"""MMU: traduce direcciones virtuales a fisicas y resuelve page faults."""
from typing import Optional

from .frames import PhysicalMemory
from .replacement import Replacer


class MMU:
    def __init__(self, memoria: PhysicalMemory, offset_bits: int) -> None:
        self.memoria = memoria
        self.offset_bits = offset_bits
        self.tam_pagina = 1 << offset_bits
        self.replacer: Optional[Replacer] = None   # lo asigna el World
        self.aciertos = 0
        self.fallos = 0
        self.por_pid = {}                           # pid -> {"aciertos", "fallos"}
        self.ultimo_evento = None                   # ultimo acceso traducido

    def _contador(self, pid: int) -> dict:
        c = self.por_pid.get(pid)
        if c is None:
            c = {"aciertos": 0, "fallos": 0}
            self.por_pid[pid] = c
        return c

    def access(self, pcb, va: int, tick: int, world) -> dict:
        """Traduce `va` para el proceso `pcb`. Devuelve y guarda el evento."""
        vpn = va >> self.offset_bits
        offset = va & (self.tam_pagina - 1)
        pte = pcb.tabla.get(vpn)
        cont = self._contador(pcb.pid)
        victima = None

        if pte.presente:
            # ----- ACIERTO -----
            self.aciertos += 1
            cont["aciertos"] += 1
            pte.ref = True
            pte.ultimo_uso = tick
            marco = self.memoria.marcos[pte.marco]
            if marco is not None:
                marco.ref = True
                marco.ultimo_uso = tick
            pa = (pte.marco << self.offset_bits) | offset
            resultado = "HIT"
        else:
            # ----- FALLO DE PAGINA -----
            self.fallos += 1
            cont["fallos"] += 1
            idx = self.memoria.marco_libre()
            if idx is None:
                # memoria llena: el algoritmo de reemplazo elige victima
                idx = self.replacer.elegir_victima(self.memoria, world, pcb.pid, vpn)
                vmarco = self.memoria.marcos[idx]
                vpcb = world.pcb.get(vmarco.pid)
                if vpcb is not None:
                    vpcb.tabla.invalidar(vmarco.vpn)
                victima = {"pid": vmarco.pid, "vpn": vmarco.vpn}
            self.memoria.cargar(idx, pcb.pid, vpn, tick)
            pte.presente = True
            pte.marco = idx
            pte.ref = True
            pte.cargada_en = tick
            pte.ultimo_uso = tick
            pa = (idx << self.offset_bits) | offset
            resultado = "FAULT"

        self.ultimo_evento = {
            "pid": pcb.pid, "va": va, "vpn": vpn, "offset": offset,
            "resultado": resultado, "pa": pa, "marco": pte.marco, "victima": victima,
        }
        return self.ultimo_evento

    def reset_contadores(self) -> None:
        self.aciertos = 0
        self.fallos = 0
        self.por_pid = {}
        self.ultimo_evento = None
