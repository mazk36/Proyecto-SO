"""SRTF: menor tiempo restante primero. Apropiativo (reevalua cada tick)."""
from typing import Optional

from ..pcb import PCB
from .base import Scheduler


class SRTF(Scheduler):
    nombre = "srtf"
    apropiativo = True

    def seleccionar(self) -> Optional[PCB]:
        if not self.cola:
            return None
        p = min(self.cola, key=lambda x: (x.rafaga_restante, x.llegada, x.pid))
        self.cola.remove(p)
        return p

    def debe_expropiar(self, en_cpu: PCB) -> bool:
        if not self.cola:
            return False
        mejor = min(self.cola, key=lambda x: (x.rafaga_restante, x.llegada, x.pid))
        return mejor.rafaga_restante < en_cpu.rafaga_restante
