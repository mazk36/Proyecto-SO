"""Enumeraciones del nucleo. Heredan de str para serializar directo a JSON."""
from enum import Enum


class Estado(str, Enum):
    NUEVO = "NUEVO"
    LISTO = "LISTO"
    EJECUTANDO = "EJECUTANDO"
    BLOQUEADO = "BLOQUEADO"
    TERMINADO = "TERMINADO"
    ERROR = "ERROR"           # el proceso aborto por un error (ver tasa_error)


# Diagrama de transicion de estados (5 estados + ERROR). El motor solo produce
# estas transiciones; `transicion_valida()` permite verificarlo (usado en tests y
# documentado en el informe). No se aplica en caliente para no abortar la demo.
TRANSICIONES_VALIDAS = {
    (Estado.NUEVO, Estado.LISTO),          # d) admision (largo plazo)
    (Estado.LISTO, Estado.EJECUTANDO),     # despacho
    (Estado.EJECUTANDO, Estado.LISTO),     # b) apropiacion / fin de quantum (timer)
    (Estado.EJECUTANDO, Estado.BLOQUEADO),  # a) solicitud de E/S
    (Estado.EJECUTANDO, Estado.TERMINADO),  # e) fin de rafaga
    (Estado.EJECUTANDO, Estado.ERROR),     # abort por error
    (Estado.BLOQUEADO, Estado.LISTO),      # c) fin de E/S (interrupcion de dispositivo)
}


def transicion_valida(origen: Estado, destino: Estado) -> bool:
    return (origen, destino) in TRANSICIONES_VALIDAS


class SchedAlgo(str, Enum):
    # Los 4 algoritmos obligatorios del curso...
    FCFS = "fcfs"
    SJF = "sjf"                 # no apropiativo
    PRIORIDAD_AP = "prioridad_ap"   # prioridad expulsiva (obligatorio)
    RR = "rr"
    # ...y 3 adicionales (bonus) que reutilizan el mismo patron Strategy.
    SRTF = "srtf"
    PRIORIDAD_NP = "prioridad_np"
    MLQ = "mlq"


class EstrategiaMem(str, Enum):
    """Estrategias de asignacion de memoria FISICA contigua (Modulo 2 obligatorio)."""
    FIRST_FIT = "first_fit"
    BEST_FIT = "best_fit"
    WORST_FIT = "worst_fit"


class ReplaceAlgo(str, Enum):
    """Reemplazo de paginas del modulo PLUS de memoria virtual."""
    FIFO = "fifo"
    LRU = "lru"
    OPTIMO = "optimo"
    RELOJ = "reloj"


class TipoDispositivo(str, Enum):
    TECLADO = "teclado"
    DISCO = "disco"
    IMPRESORA = "impresora"
    MOUSE = "mouse"
    RED = "red"


class TipoEvento(str, Enum):
    ADMISION = "admision"
    DESPACHO = "despacho"
    CAMBIO_CONTEXTO = "cambio_contexto"     # trabajo del dispatcher (costo en ticks)
    APROPIACION = "apropiacion"
    FIN_QUANTUM = "fin_quantum"             # interrupcion de reloj (timer)
    PAGE_FAULT = "page_fault"
    PAGE_HIT = "page_hit"
    BLOQUEO_IO = "bloqueo_io"               # interrupcion de E/S
    INTERRUPCION_IO = "interrupcion_io"     # interrupcion de fin de E/S
    CARGA_MEMORIA = "carga_memoria"         # el proceso se carga en memoria fisica
    LIBERA_MEMORIA = "libera_memoria"
    TERMINACION = "terminacion"
    ABORT_ERROR = "abort_error"             # el proceso termino con error
    TECLADO_SENAL = "teclado_senal"         # el teclado pide decision al usuario
    TECLADO_CANCELA = "teclado_cancela"
    TECLADO_CONTINUA = "teclado_continua"
    CAMBIO_SCHED = "cambio_sched"
    CAMBIO_REPLACE = "cambio_replace"
    CAMBIO_MEM = "cambio_mem"               # cambio de estrategia de memoria en caliente
    RESET = "reset"
    IDLE = "idle"


# Nombres legibles en espanol para la interfaz.
NOMBRE_SCHED = {
    SchedAlgo.FCFS: "FCFS (primero en llegar)",
    SchedAlgo.SJF: "SJF (trabajo mas corto, no apropiativo)",
    SchedAlgo.PRIORIDAD_AP: "Prioridad (apropiativa)",
    SchedAlgo.RR: "Round Robin (quantum)",
    SchedAlgo.SRTF: "SRTF (menor tiempo restante, apropiativo)",
    SchedAlgo.PRIORIDAD_NP: "Prioridad (no apropiativa)",
    SchedAlgo.MLQ: "MLQ (multinivel: alta=RR, baja=FCFS)",
}

# Los 4 algoritmos obligatorios que la comparativa evalua con el demo de 20.
SCHED_OBLIGATORIOS = [SchedAlgo.FCFS, SchedAlgo.SJF, SchedAlgo.PRIORIDAD_AP, SchedAlgo.RR]

NOMBRE_ESTRATEGIA = {
    EstrategiaMem.FIRST_FIT: "First-Fit (primer hueco)",
    EstrategiaMem.BEST_FIT: "Best-Fit (mejor ajuste)",
    EstrategiaMem.WORST_FIT: "Worst-Fit (peor ajuste)",
}

NOMBRE_REPLACE = {
    ReplaceAlgo.FIFO: "FIFO",
    ReplaceAlgo.LRU: "LRU",
    ReplaceAlgo.OPTIMO: "Optimo (Belady)",
    ReplaceAlgo.RELOJ: "Segunda oportunidad / Reloj",
}
