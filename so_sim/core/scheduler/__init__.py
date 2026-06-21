"""Fabrica de planificadores."""
from typing import Optional

from ..enums import SchedAlgo
from .base import Scheduler
from .fcfs import FCFS
from .mlq import MLQ
from .priority import Priority
from .round_robin import RoundRobin
from .sjf import SJF
from .srtf import SRTF


def get_scheduler(nombre, quantum: Optional[int] = None) -> Scheduler:
    clave = nombre.value if isinstance(nombre, SchedAlgo) else str(nombre)
    if clave == SchedAlgo.FCFS.value:
        return FCFS()
    if clave == SchedAlgo.SJF.value:
        return SJF()
    if clave == SchedAlgo.SRTF.value:
        return SRTF()
    if clave == SchedAlgo.RR.value:
        return RoundRobin(quantum=quantum or 3)
    if clave == SchedAlgo.PRIORIDAD_NP.value:
        return Priority(apropiativa=False)
    if clave == SchedAlgo.PRIORIDAD_AP.value:
        return Priority(apropiativa=True)
    if clave == SchedAlgo.MLQ.value:
        return MLQ(quantum=quantum or 3)
    raise ValueError(f"Algoritmo de planificacion desconocido: {nombre}")
