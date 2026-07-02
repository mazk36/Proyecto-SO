"""Dispatcher (despachador): modulo separado del planificador.

El planificador DECIDE que proceso sigue; el dispatcher EJECUTA el cambio de
contexto: guarda el estado del proceso saliente en su PCB (PC incluido), carga el
del entrante y cobra un costo en ticks (las "rafagas de cambio de contexto"), que
el World representa congelando la CPU ese numero de ticks.
"""
from typing import Optional

from .pcb import PCB


class Dispatcher:
    def __init__(self, costo_cambio: int = 0) -> None:
        # Costo del cambio de contexto en ticks (configurable, default 0 para no
        # alterar las trazas base; en el demo se usa 1).
        self.costo_cambio = max(0, costo_cambio)
        self.total_cambios = 0        # cuantos cambios de contexto han ocurrido
        self.pc_cargado = 0           # PC del proceso actualmente en CPU (para la UI)

    def cambio_de_contexto(self, saliente: Optional[PCB], entrante: PCB) -> int:
        """Realiza el cambio de contexto saliente->entrante y devuelve el costo
        en ticks que el World debe 'congelar' la CPU."""
        # Guardar contexto del saliente ya esta en su PCB (pc, cpu_consumido, etc.).
        # Cargar contexto del entrante: el PC del CPU pasa a ser el del proceso.
        self.pc_cargado = entrante.pc
        # Solo se cobra costo si realmente habia un proceso distinto antes (no en
        # el primer despacho desde CPU ociosa cuando costo aplica igual segun teoria;
        # aqui se cobra en todo despacho para reflejar la carga del PCB).
        self.total_cambios += 1
        return self.costo_cambio
