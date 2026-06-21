"""Round Robin: cola FIFO con quantum. Apropiativo por agotamiento de quantum."""
from typing import Optional

from ..pcb import PCB
from .base import Scheduler


class RoundRobin(Scheduler):
    nombre = "rr"
    apropiativo = True

    def __init__(self, quantum: int = 3) -> None:
        super().__init__(quantum=max(1, quantum or 3))

    def seleccionar(self) -> Optional[PCB]:
        return self.cola.pop(0) if self.cola else None

    def debe_expropiar(self, en_cpu: PCB) -> bool:
        return en_cpu.quantum_restante is not None and en_cpu.quantum_restante <= 0

    def on_despachar(self, pcb: PCB) -> None:
        pcb.quantum_restante = self.quantum
