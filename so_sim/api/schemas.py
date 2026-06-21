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
    accesos: List[AccesoBody] = []
    io: List[IoBody] = []


class DispositivoBody(BaseModel):
    nombre: str
    tipo: str = "disco"


class ScenarioBody(BaseModel):
    procesos: List[ProcesoBody]
    num_marcos: int = Field(default=4, ge=1, le=64)
    offset_bits: int = Field(default=12, ge=4, le=20)
    dispositivos: Optional[List[DispositivoBody]] = None
    scheduler: str = "fcfs"
    quantum: int = Field(default=3, ge=1, le=50)
    replacer: str = "fifo"
    costo_fault: int = Field(default=0, ge=0, le=10)
    descripcion: str = ""
