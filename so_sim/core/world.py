"""World: el unico 'mundo' simulado. Su metodo tick() avanza 1 unidad de tiempo
orquestando los subsistemas (procesos, memoria fisica, paginacion PLUS, E/S) en un
ORDEN DE FASES FIJO.

No importa FastAPI: es Python puro y testeable con pytest.

Orden de fases de cada tick:
  admision+carga_memoria -> dispatcher/cambio_contexto -> planificar/apropiar ->
  memoria(paginacion PLUS) -> PC++/ejecutar -> fin_rafaga/error/E-S ->
  avanzar_dispositivos -> contabilidad
"""
from typing import List, Optional

from .aleatorio import Generador
from .config import MundoConfig, construir_pcbs
from .dispatcher import Dispatcher
from .enums import Estado, TipoDispositivo, TipoEvento
from .events import EventLog
from .io import Device, IoSubsystem
from .memfisica import MemoriaFisica
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
        # --- memoria fisica (Modulo 2 obligatorio) ---
        self.mem_fisica = MemoriaFisica(cfg.ram_total, cfg.ram_so, cfg.tam_bloque,
                                        cfg.estrategia_mem)
        # --- paginacion virtual (Modulo PLUS) ---
        self.paginacion_activa = cfg.paginacion_activa
        self.offset_bits = cfg.offset_bits
        self.tam_pagina = 1 << cfg.offset_bits
        self.costo_fault = cfg.costo_fault
        self.memoria = PhysicalMemory(cfg.num_marcos)      # marcos de paginacion
        self.mmu = MMU(self.memoria, cfg.offset_bits)
        self.mmu.replacer = get_replacer(cfg.replacer)

        # --- procesos ---
        self.procesos: List[PCB] = construir_pcbs(cfg)
        self.pcb = {p.pid: p for p in self.procesos}

        # --- E/S ---
        self.io = IoSubsystem()
        for d in cfg.dispositivos:
            self.io.agregar(Device(d.nombre, d.tipo))

        # --- planificador + dispatcher ---
        self.scheduler = get_scheduler(cfg.scheduler, quantum=cfg.quantum)
        self.dispatcher = Dispatcher(cfg.costo_cambio)
        self.costo_cambio = cfg.costo_cambio
        self.en_cpu: Optional[PCB] = None

        # --- errores (RNG dedicado, reproducible) ---
        self.tasa_error = cfg.tasa_error
        self.gen_error = Generador(cfg.seed ^ 0x5AA5)

        # --- teclado interactivo (decision pendiente Cancelar/Continuar) ---
        self.decision_teclado: Optional[dict] = None

        # --- bitacora / contadores ---
        self.log = EventLog()
        self.cpu_historial: List[Optional[int]] = []   # pid o None (idle) por tick
        self.tick_actual = 0
        self.terminado = False
        self._fault_pendiente = 0   # ticks de penalizacion por page fault
        self._cc_pendiente = 0      # ticks de penalizacion por cambio de contexto

    def reset(self) -> None:
        self._inicializar()
        self.log.add(0, TipoEvento.RESET, "Simulacion reiniciada desde la configuracion actual.")

    # --------------------------------------------------------------- utilidades
    def _txt(self, p: PCB) -> str:
        return f"P{p.pid}({p.nombre})"

    def _liberar_todo(self, p: PCB) -> None:
        """Libera la memoria del proceso (fisica y, si aplica, sus marcos de paginacion)."""
        if self.paginacion_activa:
            self.liberar_marcos(p)
        n = self.mem_fisica.liberar(p.pid)
        if n:
            self.log.add(self.tick_actual, TipoEvento.LIBERA_MEMORIA,
                         f"{self._txt(p)} libera {n} bloque(s) de memoria fisica.")

    def liberar_marcos(self, p: PCB) -> None:
        for _idx, vpn in self.memoria.liberar_de(p.pid):
            p.tabla.invalidar(vpn)

    def distancia_proximo_uso(self, pid: int, vpn: int) -> int:
        """Para OPTIMO: unidades de CPU del proceso `pid` hasta su proximo acceso a
        `vpn` (INF si no vuelve a usarse)."""
        p = self.pcb.get(pid)
        if p is None:
            return INF
        inicio = p.idx_mem
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

    def set_estrategia_mem(self, algo) -> None:
        self.mem_fisica.set_estrategia(algo)
        self.cfg.estrategia_mem = algo.value if hasattr(algo, "value") else str(algo)
        self.log.add(self.tick_actual, TipoEvento.CAMBIO_MEM,
                     f"Estrategia de memoria cambiada a {self.cfg.estrategia_mem} (en caliente).")

    # ---------------------------------------------------- teclado interactivo
    def senal_teclado_manual(self) -> bool:
        """Dispara manualmente una interrupcion de teclado sobre el proceso en CPU
        (boton '⌨️ Senal' de la UI). Devuelve True si se genero la decision."""
        if self.decision_teclado is not None or self.en_cpu is None:
            return False
        p = self.en_cpu
        p.cambiar_estado(Estado.BLOQUEADO)
        self.en_cpu = None
        self.decision_teclado = {"pid": p.pid, "nombre": p.nombre, "dispositivo": "Teclado"}
        self.log.add(self.tick_actual, TipoEvento.TECLADO_SENAL,
                     f"Senal de teclado sobre {self._txt(p)}: el usuario debe Cancelar o Continuar.")
        return True

    def resolver_teclado(self, accion: str) -> None:
        """Resuelve la decision pendiente del teclado: 'cancelar' o 'continuar'."""
        if self.decision_teclado is None:
            return
        pid = self.decision_teclado["pid"]
        p = self.pcb.get(pid)
        if p is not None:
            if accion == "cancelar":
                p.codigo_error = "Cancelado desde el teclado"
                p.cambiar_estado(Estado.ERROR)
                p.t_fin = self.tick_actual
                self._liberar_todo(p)
                self.log.add(self.tick_actual, TipoEvento.TECLADO_CANCELA,
                             f"{self._txt(p)} fue CANCELADO desde el teclado.")
            else:
                p.cambiar_estado(Estado.LISTO)
                self.scheduler.agregar(p)
                self.log.add(self.tick_actual, TipoEvento.TECLADO_CONTINUA,
                             f"{self._txt(p)} CONTINUA tras la senal de teclado y vuelve a LISTO.")
        self.decision_teclado = None
        self._evaluar_terminado()

    # ------------------------------------------------------------------- tick
    def tick(self) -> None:
        if self.terminado:
            return
        if self.tick_actual >= self.limite_ticks:
            self.terminado = True
            return
        t = self.tick_actual

        # Penalizacion por page fault: la CPU queda 'congelada' N ticks.
        if self._fault_pendiente > 0:
            self._fault_pendiente -= 1
            self.cpu_historial.append(self.en_cpu.pid if self.en_cpu else None)
            self._fase_dispositivos(t)
            self._fase_contabilidad()
            self.tick_actual += 1
            self._evaluar_terminado()
            return

        # Penalizacion por cambio de contexto (trabajo del dispatcher): CPU sin
        # progreso util durante N ticks.
        if self._cc_pendiente > 0:
            self._cc_pendiente -= 1
            self.log.add(t, TipoEvento.CAMBIO_CONTEXTO,
                         "Dispatcher: cambio de contexto en curso (guardando/cargando PCB).")
            self.cpu_historial.append(None)
            self._fase_dispositivos(t)
            self._fase_contabilidad()
            self.tick_actual += 1
            self._evaluar_terminado()
            return

        self._fase_admision(t)
        despacho = self._fase_planificar(t)
        # Si hubo despacho y hay costo de cambio de contexto, congela la CPU.
        if despacho and self.costo_cambio > 0:
            self._cc_pendiente = self.costo_cambio
            self.cpu_historial.append(None)
            self.log.add(t, TipoEvento.CAMBIO_CONTEXTO,
                         "Dispatcher: inicia cambio de contexto.")
            self._fase_dispositivos(t)
            self._fase_contabilidad()
            self.tick_actual += 1
            self._evaluar_terminado()
            return

        falla = self._fase_memoria(t)
        self._fase_ejecutar(t)
        self._fase_fin_io(t)
        self._fase_dispositivos(t)
        self._fase_contabilidad()

        self.tick_actual += 1
        self._evaluar_terminado()

        if falla and self.costo_fault > 0:
            self._fault_pendiente = self.costo_fault

    # FASE 0: admision + carga en memoria fisica (planificador de LARGO plazo) ---
    def _fase_admision(self, t: int) -> None:
        for p in self.procesos:
            if p.estado == Estado.NUEVO and p.llegada <= t:
                # Carga COMPLETA en memoria fisica (direccionamiento fisico, sin MMU).
                if self.mem_fisica.asignar(p):
                    p.cambiar_estado(Estado.LISTO)
                    self.scheduler.agregar(p)
                    self.log.add(t, TipoEvento.ADMISION,
                                 f"{self._txt(p)} llega, se carga en memoria (dir {p.direccion_inicial} KB, "
                                 f"{len(p.bloques)} bloque(s)) y pasa a LISTO.")
                # Si no cabe, el proceso espera (mediano plazo) y se reintenta luego.

    # FASE 1: planificar / apropiar + dispatcher --------------------------------
    def _fase_planificar(self, t: int) -> bool:
        """Devuelve True si se despacho un nuevo proceso a la CPU (hubo cambio de
        contexto). Cubre los 5 eventos del planificador (ver informe)."""
        saliente = None
        if self.en_cpu is not None and self.scheduler.debe_expropiar(self.en_cpu):
            p = self.en_cpu
            fin_quantum = p.quantum_restante is not None and p.quantum_restante <= 0
            p.cambiar_estado(Estado.LISTO)
            self.scheduler.agregar(p)
            saliente = p
            self.en_cpu = None
            if fin_quantum:
                self.log.add(t, TipoEvento.FIN_QUANTUM,
                             f"{self._txt(p)} agota su quantum (interrupcion de reloj) y vuelve a LISTO.")
            else:
                self.log.add(t, TipoEvento.APROPIACION,
                             f"{self._txt(p)} es apropiado y vuelve a LISTO.")

        despacho = False
        if self.en_cpu is None:
            nxt = self.scheduler.seleccionar()
            if nxt is not None:
                nxt.cambiar_estado(Estado.EJECUTANDO)
                if nxt.t_primer_despacho is None:
                    nxt.t_primer_despacho = t
                self.scheduler.on_despachar(nxt)
                self.dispatcher.cambio_de_contexto(saliente, nxt)   # carga PCB / PC
                self.en_cpu = nxt
                despacho = True
                self.log.add(t, TipoEvento.DESPACHO,
                             f"{self._txt(nxt)} es despachado a la CPU (PC={nxt.pc}).")
        return despacho

    # FASE 2: memoria virtual / paginacion (Modulo PLUS) ------------------------
    def _fase_memoria(self, t: int) -> bool:
        if not self.paginacion_activa or self.en_cpu is None:
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

    # FASE 3: ejecutar rafaga (avanza el Program Counter) -----------------------
    def _fase_ejecutar(self, t: int) -> None:
        pid_ejecuta = None
        if self.en_cpu is not None:
            p = self.en_cpu
            p.rafaga_restante -= 1
            p.cpu_consumido += 1
            p.pc += 1                          # el Program Counter avanza cada tick
            if p.quantum_restante is not None:
                p.quantum_restante -= 1
            self.dispatcher.pc_cargado = p.pc
            pid_ejecuta = p.pid
        self.cpu_historial.append(pid_ejecuta)

    # FASE 4: fin de rafaga (error/terminacion) o bloqueo por E/S ---------------
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
            # Fin de rafaga: decide error (tasa_error) o terminacion normal.
            if self.gen_error.marca_error(self.tasa_error):
                p.codigo_error = self.gen_error.codigo_error()
                p.cambiar_estado(Estado.ERROR)
                p.t_fin = t
                self._liberar_todo(p)
                self.en_cpu = None
                self.log.add(t, TipoEvento.ABORT_ERROR,
                             f"{self._txt(p)} ABORTA con error: {p.codigo_error}.")
            else:
                p.cambiar_estado(Estado.TERMINADO)
                p.t_fin = t
                self._liberar_todo(p)
                self.en_cpu = None
                self.log.add(t, TipoEvento.TERMINACION,
                             f"{self._txt(p)} TERMINA (libera su memoria).")

    # FASE 5: avanzar dispositivos (interrupciones de fin de E/S) ---------------
    def _fase_dispositivos(self, t: int) -> None:
        for pid, dispositivo in self.io.tick():
            p = self.pcb[pid]
            dev = self.io.dispositivos.get(dispositivo)
            es_teclado = dev is not None and dev.tipo == TipoDispositivo.TECLADO.value
            if es_teclado and self.decision_teclado is None:
                # El teclado exige decision del usuario: el proceso sigue BLOQUEADO.
                self.decision_teclado = {"pid": pid, "nombre": p.nombre,
                                         "dispositivo": dispositivo}
                self.log.add(t, TipoEvento.TECLADO_SENAL,
                             f"Interrupcion de teclado: {self._txt(p)} espera decision "
                             "(Cancelar / Continuar).")
                continue
            p.cambiar_estado(Estado.LISTO)
            self.scheduler.agregar(p)
            self.log.add(t, TipoEvento.INTERRUPCION_IO,
                         f"Interrupcion de {dispositivo}: {self._txt(p)} "
                         f"completa su E/S y vuelve a LISTO.")

    # FASE 6: contabilidad (tiempo de espera) -----------------------------------
    def _fase_contabilidad(self) -> None:
        for p in self.procesos:
            if p.estado == Estado.LISTO:
                p.espera_acumulada += 1

    def _evaluar_terminado(self) -> None:
        if all(p.estado in (Estado.TERMINADO, Estado.ERROR) for p in self.procesos):
            self.terminado = True
