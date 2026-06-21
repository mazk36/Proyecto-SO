"""World: el unico 'mundo' simulado. Su metodo tick() avanza 1 unidad de tiempo
orquestando los 3 subsistemas (procesos, memoria, E/S) en un ORDEN DE FASES FIJO.

No importa FastAPI: es Python puro y testeable con pytest.
"""
from typing import List, Optional

from .config import MundoConfig, construir_pcbs
from .enums import Estado, TipoEvento
from .events import EventLog
from .io import Device, IoSubsystem
from .memory import get_replacer
from .memory.frames import PhysicalMemory
from .memory.mmu import MMU
from .pcb import PCB
from .scheduler import get_scheduler

INF = 10 ** 9


class World:
    def __init__(self, cfg: MundoConfig, limite_ticks: int = 5000) -> None:
        self.cfg = cfg
        self.limite_ticks = limite_ticks
        self._inicializar()

    # ------------------------------------------------------------------ setup
    def _inicializar(self) -> None:
        cfg = self.cfg
        self.offset_bits = cfg.offset_bits
        self.tam_pagina = 1 << cfg.offset_bits
        self.costo_fault = cfg.costo_fault

        self.procesos: List[PCB] = construir_pcbs(cfg)
        self.pcb = {p.pid: p for p in self.procesos}

        self.memoria = PhysicalMemory(cfg.num_marcos)
        self.mmu = MMU(self.memoria, cfg.offset_bits)
        self.mmu.replacer = get_replacer(cfg.replacer)

        self.io = IoSubsystem()
        for d in cfg.dispositivos:
            self.io.agregar(Device(d.nombre, d.tipo))

        self.scheduler = get_scheduler(cfg.scheduler, quantum=cfg.quantum)
        self.en_cpu: Optional[PCB] = None

        self.log = EventLog()
        self.cpu_historial: List[Optional[int]] = []   # pid o None (idle) por tick
        self.tick_actual = 0
        self.terminado = False
        self._fault_pendiente = 0   # ticks de penalizacion por page fault (costo_fault)

    def reset(self) -> None:
        self._inicializar()
        self.log.add(0, TipoEvento.RESET, "Simulacion reiniciada desde la configuracion actual.")

    # --------------------------------------------------------------- utilidades
    def _txt(self, p: PCB) -> str:
        return f"P{p.pid}({p.nombre})"

    def liberar_marcos(self, p: PCB) -> None:
        for _idx, vpn in self.memoria.liberar_de(p.pid):
            p.tabla.invalidar(vpn)

    def distancia_proximo_uso(self, pid: int, vpn: int) -> int:
        """Para OPTIMO: ticks/unidades de CPU del proceso `pid` hasta su proximo
        acceso a `vpn` (INF si no vuelve a usarse)."""
        p = self.pcb.get(pid)
        if p is None:
            return INF
        inicio = p.idx_mem
        # El proceso en CPU ya esta sirviendo su acceso actual: se omite.
        if self.en_cpu is not None and self.en_cpu.pid == pid:
            inicio = p.idx_mem + 1
        for k in range(inicio, len(p.plan_mem)):
            a = p.plan_mem[k]
            if (a.va >> self.offset_bits) == vpn:
                return max(0, a.en_cpu - p.cpu_consumido)
        return INF

    # ----------------------------------------------------- cambios en caliente
    def set_scheduler(self, algo, quantum: Optional[int] = None) -> None:
        listos = [p for p in self.procesos if p.estado == Estado.LISTO]
        self.scheduler = get_scheduler(algo, quantum=quantum or self.cfg.quantum)
        for p in sorted(listos, key=lambda x: (x.llegada, x.pid)):
            self.scheduler.agregar(p)
        if self.en_cpu is not None:
            # Reajusta el quantum del proceso en ejecucion al nuevo algoritmo.
            self.scheduler.on_despachar(self.en_cpu)
        self.cfg.scheduler = algo.value if hasattr(algo, "value") else str(algo)
        if quantum:
            self.cfg.quantum = quantum
        self.log.add(self.tick_actual, TipoEvento.CAMBIO_SCHED,
                     f"Planificador cambiado a {self.cfg.scheduler} (en caliente).")

    def set_replacer(self, algo) -> None:
        self.mmu.replacer = get_replacer(algo)
        self.cfg.replacer = algo.value if hasattr(algo, "value") else str(algo)
        self.log.add(self.tick_actual, TipoEvento.CAMBIO_REPLACE,
                     f"Algoritmo de reemplazo cambiado a {self.cfg.replacer} (en caliente).")

    # ------------------------------------------------------------------- tick
    def tick(self) -> None:
        if self.terminado:
            return
        if self.tick_actual >= self.limite_ticks:
            self.terminado = True
            return
        t = self.tick_actual

        # Penalizacion opcional por page fault: la CPU queda 'congelada' N ticks.
        if self._fault_pendiente > 0:
            self._fault_pendiente -= 1
            self.cpu_historial.append(self.en_cpu.pid if self.en_cpu else None)
            self._fase_dispositivos(t)
            self._fase_contabilidad()
            self.tick_actual += 1
            self._evaluar_terminado()
            return

        self._fase_admision(t)
        self._fase_planificar(t)
        falla = self._fase_memoria(t)
        self._fase_ejecutar(t)
        self._fase_fin_io(t)
        self._fase_dispositivos(t)
        self._fase_contabilidad()

        self.tick_actual += 1
        self._evaluar_terminado()

        # Si hubo fallo de pagina con costo, congela los proximos N ticks.
        if falla and self.costo_fault > 0:
            self._fault_pendiente = self.costo_fault

    # FASE 0 -----------------------------------------------------------------
    def _fase_admision(self, t: int) -> None:
        for p in self.procesos:
            if p.estado == Estado.NUEVO and p.llegada <= t:
                p.cambiar_estado(Estado.LISTO)
                self.scheduler.agregar(p)
                self.log.add(t, TipoEvento.ADMISION,
                             f"{self._txt(p)} llega y pasa a LISTO.")

    # FASE 1 -----------------------------------------------------------------
    def _fase_planificar(self, t: int) -> None:
        if self.en_cpu is not None and self.scheduler.debe_expropiar(self.en_cpu):
            p = self.en_cpu
            fin_quantum = p.quantum_restante is not None and p.quantum_restante <= 0
            p.cambiar_estado(Estado.LISTO)
            self.scheduler.agregar(p)
            self.en_cpu = None
            if fin_quantum:
                self.log.add(t, TipoEvento.FIN_QUANTUM,
                             f"{self._txt(p)} agota su quantum y vuelve a LISTO.")
            else:
                self.log.add(t, TipoEvento.APROPIACION,
                             f"{self._txt(p)} es apropiado y vuelve a LISTO.")

        if self.en_cpu is None:
            nxt = self.scheduler.seleccionar()
            if nxt is not None:
                nxt.cambiar_estado(Estado.EJECUTANDO)
                if nxt.t_primer_despacho is None:
                    nxt.t_primer_despacho = t
                self.scheduler.on_despachar(nxt)
                self.en_cpu = nxt
                self.log.add(t, TipoEvento.DESPACHO,
                             f"{self._txt(nxt)} es despachado a la CPU.")

    # FASE 2 -----------------------------------------------------------------
    def _fase_memoria(self, t: int) -> bool:
        if self.en_cpu is None:
            return False
        p = self.en_cpu
        acc = p.acceso_mem_pendiente()
        if acc is None or acc.en_cpu != p.cpu_consumido:
            return False
        ev = self.mmu.access(p, acc.va, t, self)
        p.idx_mem += 1
        if ev["resultado"] == "FAULT":
            extra = ""
            if ev["victima"] is not None:
                v = ev["victima"]
                extra = f" (reemplaza pagina {v['vpn']} de P{v['pid']})"
            self.log.add(t, TipoEvento.PAGE_FAULT,
                         f"{self._txt(p)} FALLO de pagina en VPN {ev['vpn']}{extra}.")
            return True
        self.log.add(t, TipoEvento.PAGE_HIT,
                     f"{self._txt(p)} acierto de pagina en VPN {ev['vpn']} (marco {ev['marco']}).")
        return False

    # FASE 3 -----------------------------------------------------------------
    def _fase_ejecutar(self, t: int) -> None:
        pid_ejecuta = None
        if self.en_cpu is not None:
            p = self.en_cpu
            p.rafaga_restante -= 1
            p.cpu_consumido += 1
            if p.quantum_restante is not None:
                p.quantum_restante -= 1
            pid_ejecuta = p.pid
        self.cpu_historial.append(pid_ejecuta)

    # FASE 4 -----------------------------------------------------------------
    def _fase_fin_io(self, t: int) -> None:
        if self.en_cpu is None:
            return
        p = self.en_cpu
        pet = p.peticion_io_pendiente()
        if pet is not None and pet.en_cpu == p.cpu_consumido and p.rafaga_restante > 0:
            p.cambiar_estado(Estado.BLOQUEADO)
            self.io.encolar(pet.dispositivo, p.pid, pet.duracion)
            p.idx_io += 1
            self.en_cpu = None
            self.log.add(t, TipoEvento.BLOQUEO_IO,
                         f"{self._txt(p)} solicita E/S en {pet.dispositivo} "
                         f"({pet.duracion} ticks) y se BLOQUEA; la CPU queda libre.")
        elif p.rafaga_restante <= 0:
            p.cambiar_estado(Estado.TERMINADO)
            p.t_fin = t
            self.liberar_marcos(p)
            self.en_cpu = None
            self.log.add(t, TipoEvento.TERMINACION,
                         f"{self._txt(p)} TERMINA (libera sus marcos de memoria).")

    # FASE 5 -----------------------------------------------------------------
    def _fase_dispositivos(self, t: int) -> None:
        for pid, dispositivo in self.io.tick():
            p = self.pcb[pid]
            p.cambiar_estado(Estado.LISTO)
            self.scheduler.agregar(p)
            self.log.add(t, TipoEvento.INTERRUPCION_IO,
                         f"Interrupcion de {dispositivo}: {self._txt(p)} "
                         f"completa su E/S y vuelve a LISTO.")

    # FASE 6 -----------------------------------------------------------------
    def _fase_contabilidad(self) -> None:
        for p in self.procesos:
            if p.estado == Estado.LISTO:
                p.espera_acumulada += 1

    def _evaluar_terminado(self) -> None:
        if all(p.estado == Estado.TERMINADO for p in self.procesos):
            self.terminado = True
