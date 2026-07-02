"""Estrategias de asignacion de memoria fisica contigua (patron Strategy).

Cada estrategia recibe la lista de HUECOS libres (agujeros de bloques contiguos)
y la cantidad de bloques que necesita el proceso, y elige en cual hueco colocarlo.
Devuelve el indice del bloque inicial, o None si no cabe en ningun hueco.

Un hueco se representa como (inicio, longitud): `inicio` es el indice del primer
bloque libre del tramo y `longitud` cuantos bloques contiguos libres tiene.
"""
from typing import List, Optional, Tuple

from ..enums import EstrategiaMem

Hueco = Tuple[int, int]   # (inicio, longitud)


class Estrategia:
    nombre = "base"

    def elegir(self, huecos: List[Hueco], necesarios: int) -> Optional[int]:
        raise NotImplementedError


class FirstFit(Estrategia):
    """Primer hueco (en orden de direccion) donde quepa el proceso. Rapido."""
    nombre = EstrategiaMem.FIRST_FIT.value

    def elegir(self, huecos, necesarios):
        for inicio, longitud in huecos:          # huecos vienen ordenados por direccion
            if longitud >= necesarios:
                return inicio
        return None


class BestFit(Estrategia):
    """Hueco mas pequeno donde quepa (deja el menor sobrante). Minimiza el
    desperdicio inmediato pero tiende a generar muchos huecos diminutos."""
    nombre = EstrategiaMem.BEST_FIT.value

    def elegir(self, huecos, necesarios):
        candidatos = [(longitud, inicio) for inicio, longitud in huecos
                      if longitud >= necesarios]
        if not candidatos:
            return None
        # menor longitud; empate -> menor direccion (reproducible)
        _, inicio = min(candidatos, key=lambda x: (x[0], x[1]))
        return inicio


class WorstFit(Estrategia):
    """Hueco mas grande donde quepa (deja el mayor sobrante utilizable)."""
    nombre = EstrategiaMem.WORST_FIT.value

    def elegir(self, huecos, necesarios):
        candidatos = [(longitud, inicio) for inicio, longitud in huecos
                      if longitud >= necesarios]
        if not candidatos:
            return None
        # mayor longitud; empate -> menor direccion (reproducible)
        _, inicio = max(candidatos, key=lambda x: (x[0], -x[1]))
        return inicio


_ESTRATEGIAS = {
    EstrategiaMem.FIRST_FIT.value: FirstFit,
    EstrategiaMem.BEST_FIT.value: BestFit,
    EstrategiaMem.WORST_FIT.value: WorstFit,
}


def get_estrategia(nombre) -> Estrategia:
    clave = nombre.value if isinstance(nombre, EstrategiaMem) else str(nombre)
    if clave not in _ESTRATEGIAS:
        raise ValueError(f"Estrategia de memoria desconocida: {nombre}")
    return _ESTRATEGIAS[clave]()
