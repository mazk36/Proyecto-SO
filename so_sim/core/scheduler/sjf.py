"""SJF: trabajo mas corto primero. No apropiativo (elige al despachar)."""
from typing import Optional

from ..pcb import PCB
from .base import Scheduler


class SJF(Scheduler):
    nombre = "sjf"
    apropiativo = False

    def seleccionar(self) -> Optional[PCB]:
        if not self.cola:
            return None
        p = min(self.cola, key=lambda x: (x.rafaga_restante, x.llegada, x.pid))
        self.cola.remove(p)
        return p
