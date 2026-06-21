"""Prioridad (menor numero = mayor prioridad). Apropiativa o no, segun flag."""
from typing import Optional

from ..pcb import PCB
from .base import Scheduler


class Priority(Scheduler):
    def __init__(self, apropiativa: bool = False) -> None:
        super().__init__()
        self.apropiativo = apropiativa
        self.nombre = "prioridad_ap" if apropiativa else "prioridad_np"

    def seleccionar(self) -> Optional[PCB]:
        if not self.cola:
            return None
        p = min(self.cola, key=lambda x: (x.prioridad, x.llegada, x.pid))
        self.cola.remove(p)
        return p

    def debe_expropiar(self, en_cpu: PCB) -> bool:
        if not self.apropiativo or not self.cola:
            return False
        mejor = min(self.cola, key=lambda x: (x.prioridad, x.llegada, x.pid))
        return mejor.prioridad < en_cpu.prioridad
