"""Modelos Pydantic para validar los cuerpos de las peticiones del API.
(Solo para la frontera HTTP; el nucleo usa sus propias dataclasses.)"""
from typing import List, Optional

from pydantic import BaseModel, Field


class SpeedBody(BaseModel):
    velocidad_ms: int = Field(ge=50, le=5000)


class SchedulerBody(BaseModel):
    algoritmo: str
    quantum: Optional[int] = Field(default=None, ge=1, le=50)


class ReplacerBody(BaseModel):
    algoritmo: str


class EstrategiaBody(BaseModel):
    algoritmo: str          # first_fit | best_fit | worst_fit


class TecladoBody(BaseModel):
    accion: str             # "cancelar" | "continuar"


class GenerarBody(BaseModel):
    cantidad: int = Field(default=10, ge=1, le=50)
    seed: Optional[int] = None


class AccesoBody(BaseModel):
    en_cpu: int = Field(ge=0)
    va: int = Field(ge=0)


class IoBody(BaseModel):
    en_cpu: int = Field(ge=0)
    dispositivo: str
    duracion: int = Field(ge=1, le=100)


class ProcesoBody(BaseModel):
    pid: int = Field(ge=1)
    nombre: str = ""
    llegada: int = Field(default=0, ge=0)
    rafaga: int = Field(ge=1, le=100)
    prioridad: int = Field(default=0, ge=0, le=99)
    nivel_mlq: str = "ALTA"
    tam_ejecutable: int = Field(default=100, ge=1, le=100000)
    tam_datos: int = Field(default=0, ge=0, le=100000)
    tam_dinamica: int = Field(default=0, ge=0, le=100000)
    modo_interrupciones: str = "declarativo"
    accesos: List[AccesoBody] = []
    io: List[IoBody] = []


class DispositivoBody(BaseModel):
    nombre: str
    tipo: str = "disco"


class ScenarioBody(BaseModel):
    procesos: List[ProcesoBody]
    # memoria fisica (obligatorio)
    ram_total: int = Field(default=16384, ge=256, le=1048576)
    ram_so: int = Field(default=2048, ge=0, le=1048576)
    tam_bloque: int = Field(default=256, ge=32, le=2048)
    estrategia_mem: str = "first_fit"
    # paginacion (PLUS)
    paginacion_activa: bool = True
    num_marcos: int = Field(default=4, ge=1, le=64)
    offset_bits: int = Field(default=12, ge=4, le=20)
    replacer: str = "fifo"
    costo_fault: int = Field(default=0, ge=0, le=10)
    # planificacion / dispatcher
    scheduler: str = "fcfs"
    quantum: int = Field(default=3, ge=1, le=50)
    costo_cambio: int = Field(default=0, ge=0, le=10)
    # aleatoriedad / errores
    tasa_error: float = Field(default=0.0, ge=0.0, le=1.0)
    seed: int = Field(default=12345)
    dispositivos: Optional[List[DispositivoBody]] = None
    descripcion: str = ""
