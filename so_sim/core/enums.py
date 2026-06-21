"""Enumeraciones del nucleo. Heredan de str para serializar directo a JSON."""
from enum import Enum


class Estado(str, Enum):
    NUEVO = "NUEVO"
    LISTO = "LISTO"
    EJECUTANDO = "EJECUTANDO"
    BLOQUEADO = "BLOQUEADO"
    TERMINADO = "TERMINADO"


class SchedAlgo(str, Enum):
    FCFS = "fcfs"
    SJF = "sjf"
    SRTF = "srtf"
    RR = "rr"
    PRIORIDAD_NP = "prioridad_np"
    PRIORIDAD_AP = "prioridad_ap"
    MLQ = "mlq"


class ReplaceAlgo(str, Enum):
    FIFO = "fifo"
    LRU = "lru"
    OPTIMO = "optimo"
    RELOJ = "reloj"


class TipoDispositivo(str, Enum):
    DISCO = "disco"
    IMPRESORA = "impresora"
    TECLADO = "teclado"
    RED = "red"


class TipoEvento(str, Enum):
    ADMISION = "admision"
    DESPACHO = "despacho"
    APROPIACION = "apropiacion"
    FIN_QUANTUM = "fin_quantum"
    PAGE_FAULT = "page_fault"
    PAGE_HIT = "page_hit"
    BLOQUEO_IO = "bloqueo_io"
    INTERRUPCION_IO = "interrupcion_io"
    TERMINACION = "terminacion"
    CAMBIO_SCHED = "cambio_sched"
    CAMBIO_REPLACE = "cambio_replace"
    RESET = "reset"
    IDLE = "idle"


# Nombres legibles en espanol para la interfaz.
NOMBRE_SCHED = {
    SchedAlgo.FCFS: "FCFS (primero en llegar)",
    SchedAlgo.SJF: "SJF (trabajo mas corto)",
    SchedAlgo.SRTF: "SRTF (menor tiempo restante, apropiativo)",
    SchedAlgo.RR: "Round Robin (quantum)",
    SchedAlgo.PRIORIDAD_NP: "Prioridad (no apropiativa)",
    SchedAlgo.PRIORIDAD_AP: "Prioridad (apropiativa)",
    SchedAlgo.MLQ: "MLQ (multinivel: alta=RR, baja=FCFS)",
}

NOMBRE_REPLACE = {
    ReplaceAlgo.FIFO: "FIFO",
    ReplaceAlgo.LRU: "LRU",
    ReplaceAlgo.OPTIMO: "Optimo (Belady)",
    ReplaceAlgo.RELOJ: "Segunda oportunidad / Reloj",
}
