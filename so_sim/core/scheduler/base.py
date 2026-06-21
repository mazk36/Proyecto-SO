"""Interfaz comun de planificadores (Strategy)."""
from typing import List, Optional

from ..pcb import PCB


class Scheduler:
    nombre = "base"
    apropiativo = False

    def __init__(self, quantum: Optional[int] = None) -> None:
        self.cola: List[PCB] = []
        self.quantum = quantum

    def es_apropiativo(self) -> bool:
        return self.apropiativo

    def agregar(self, pcb: PCB) -> None:
        if not any(x.pid == pcb.pid for x in self.cola):
            self.cola.append(pcb)

    def quitar(self, pcb: PCB) -> None:
        self.cola = [x for x in self.cola if x.pid != pcb.pid]

    def listos(self) -> List[PCB]:
        return list(self.cola)

    def vaciar(self) -> None:
        self.cola.clear()

    # A implementar por cada algoritmo -------------------------------------
    def seleccionar(self) -> Optional[PCB]:
        raise NotImplementedError

    def debe_expropiar(self, en_cpu: PCB) -> bool:
        return False

    def on_despachar(self, pcb: PCB) -> None:
        # Por defecto los algoritmos sin quantum no usan quantum_restante.
        pcb.quantum_restante = None
