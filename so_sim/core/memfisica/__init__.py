"""Subsistema de memoria FISICA contigua (Modulo 2 obligatorio del curso).

Direccionamiento fisico directo, SIN MMU: un proceso se carga en su totalidad en
bloques contiguos de tamano fijo. Administracion por mapa de bits y tres estrategias
de asignacion (First/Best/Worst-Fit).
"""
from .estrategias import Estrategia, get_estrategia
from .memoria import MemoriaFisica

__all__ = ["MemoriaFisica", "Estrategia", "get_estrategia"]
