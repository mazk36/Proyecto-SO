"""MLQ multinivel: cola ALTA = Round Robin(quantum), cola BAJA = FCFS.
Prioridad estricta entre niveles (ALTA siempre antes que BAJA)."""
from typing import List, Optional

from ..pcb import PCB
from .base import Scheduler


class MLQ(Scheduler):
    nombre = "mlq"
    apropiativo = True

    def __init__(self, quantum: int = 3) -> None:
        super().__init__(quantum=max(1, quantum or 3))
        self.alta: List[PCB] = []
        self.baja: List[PCB] = []

    def agregar(self, pcb: PCB) -> None:
        cola = self.alta if pcb.nivel_mlq == "ALTA" else self.baja
        if not any(x.pid == pcb.pid for x in cola):
            cola.append(pcb)

    def quitar(self, pcb: PCB) -> None:
        self.alta = [x for x in self.alta if x.pid != pcb.pid]
        self.baja = [x for x in self.baja if x.pid != pcb.pid]

    def listos(self) -> List[PCB]:
        return self.alta + self.baja

    def vaciar(self) -> None:
        self.alta.clear()
        self.baja.clear()

    def seleccionar(self) -> Optional[PCB]:
        if self.alta:
            return self.alta.pop(0)
        if self.baja:
            return self.baja.pop(0)
        return None

    def on_despachar(self, pcb: PCB) -> None:
        # Solo la cola de alta usa quantum (RR); la baja es FCFS.
        pcb.quantum_restante = self.quantum if pcb.nivel_mlq == "ALTA" else None

    def debe_expropiar(self, en_cpu: PCB) -> bool:
        # Un proceso de BAJA es expropiado si llega/queda uno en ALTA.
        if en_cpu.nivel_mlq == "BAJA" and self.alta:
            return True
        # En ALTA se aplica el quantum de Round Robin.
        if en_cpu.nivel_mlq == "ALTA":
            return en_cpu.quantum_restante is not None and en_cpu.quantum_restante <= 0
        return False
