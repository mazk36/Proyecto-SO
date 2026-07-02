"""PCB: Bloque de Control de Proceso, y los planes declarativos de memoria/E-S."""
from dataclasses import dataclass, field
from typing import List, Optional

from .enums import Estado
from .memory.page_table import PageTable


@dataclass
class AccesoMem:
    """Acceso a memoria (VIRTUAL, modulo PLUS) programado: ocurre cuando el proceso
    lleva `en_cpu` unidades de CPU consumidas (antes de ejecutar esa unidad)."""
    en_cpu: int
    va: int


@dataclass
class PeticionIO:
    """Peticion de E/S: cuando el proceso alcanza `en_cpu` unidades de CPU,
    se bloquea durante `duracion` ticks en `dispositivo`."""
    en_cpu: int
    dispositivo: str
    duracion: int


@dataclass
class PCB:
    # --- identidad / configuracion (no cambia durante la corrida) ---
    pid: int
    nombre: str
    llegada: int
    rafaga_total: int
    prioridad: int = 0                 # menor numero = mayor prioridad
    nivel_mlq: str = "ALTA"            # "ALTA" | "BAJA"
    color: str = "#888888"

    # --- memoria fisica (Modulo 2 obligatorio): tamano del proceso en KB ---
    tam_ejecutable: int = 100          # KB del codigo ejecutable
    tam_datos: int = 0                 # KB del segmento de datos (estatico)
    tam_dinamica: int = 0             # KB de memoria dinamica (heap+stack en ejecucion)
    tam_total: int = 0                 # se calcula en __post_init__ (suma de los 3)

    # --- planes declarativos ---
    plan_mem: List[AccesoMem] = field(default_factory=list)   # accesos VIRTUALES (PLUS)
    plan_io: List[PeticionIO] = field(default_factory=list)
    modo_interrupciones: str = "declarativo"   # "declarativo" | "aleatorio"

    # --- estado dinamico ---
    estado: Estado = Estado.NUEVO
    rafaga_restante: int = -1          # se inicializa a rafaga_total en __post_init__
    cpu_consumido: int = 0
    pc: int = 0                        # Program Counter (avanza cada tick ejecutado)
    quantum_restante: Optional[int] = None
    idx_mem: int = 0
    idx_io: int = 0
    tabla: PageTable = field(default_factory=PageTable)

    # --- memoria fisica asignada ---
    direccion_inicial: Optional[int] = None    # direccion fisica del 1er bloque (KB)
    bloques: List[int] = field(default_factory=list)   # indices de bloque ocupados

    # --- error ---
    codigo_error: Optional[str] = None

    # --- metricas ---
    t_primer_despacho: Optional[int] = None
    t_fin: Optional[int] = None
    espera_acumulada: int = 0          # ticks que el proceso paso en LISTO

    def __post_init__(self) -> None:
        if self.rafaga_restante < 0:
            self.rafaga_restante = self.rafaga_total
        if self.tam_total <= 0:
            self.tam_total = self.tam_ejecutable + self.tam_datos + self.tam_dinamica

    def cambiar_estado(self, nuevo: Estado) -> Estado:
        anterior = self.estado
        self.estado = nuevo
        return anterior

    # Accesos pendientes segun el cursor actual ------------------------------
    def acceso_mem_pendiente(self) -> Optional[AccesoMem]:
        if self.idx_mem < len(self.plan_mem):
            return self.plan_mem[self.idx_mem]
        return None

    def peticion_io_pendiente(self) -> Optional[PeticionIO]:
        if self.idx_io < len(self.plan_io):
            return self.plan_io[self.idx_io]
        return None
