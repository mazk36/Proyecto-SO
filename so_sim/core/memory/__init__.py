"""Subsistema de memoria virtual / paginacion."""
from ..enums import ReplaceAlgo
from .replacement import (FIFOReplacer, LRUReplacer, OptimoReplacer,
                          RelojReplacer, Replacer)

REPLACERS = {
    ReplaceAlgo.FIFO.value: FIFOReplacer,
    ReplaceAlgo.LRU.value: LRUReplacer,
    ReplaceAlgo.OPTIMO.value: OptimoReplacer,
    ReplaceAlgo.RELOJ.value: RelojReplacer,
}


def get_replacer(nombre) -> Replacer:
    clave = nombre.value if isinstance(nombre, ReplaceAlgo) else str(nombre)
    if clave not in REPLACERS:
        raise ValueError(f"Algoritmo de reemplazo desconocido: {nombre}")
    return REPLACERS[clave]()
