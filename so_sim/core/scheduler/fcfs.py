"""FCFS: primero en llegar, primero en ser servido. No apropiativo."""
from typing import Optional

from ..pcb import PCB
from .base import Scheduler


class FCFS(Scheduler):
    nombre = "fcfs"
    apropiativo = False

    def seleccionar(self) -> Optional[PCB]:
        return self.cola.pop(0) if self.cola else None
