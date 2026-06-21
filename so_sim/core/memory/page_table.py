"""Tabla de paginas por proceso. Modulo independiente (no importa nada del nucleo)."""
from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class PTE:
    """Entrada de la tabla de paginas (Page Table Entry)."""
    presente: bool = False
    marco: Optional[int] = None     # indice de marco fisico si presente
    ref: bool = False               # bit de referencia (para Reloj/LRU)
    cargada_en: int = -1            # tick en que se cargo (para FIFO)
    ultimo_uso: int = -1            # tick del ultimo acceso (para LRU)


class PageTable:
    """Mapea VPN -> PTE. Crea entradas perezosamente."""

    def __init__(self) -> None:
        self.entradas: Dict[int, PTE] = {}

    def get(self, vpn: int) -> PTE:
        pte = self.entradas.get(vpn)
        if pte is None:
            pte = PTE()
            self.entradas[vpn] = pte
        return pte

    def invalidar(self, vpn: int) -> None:
        pte = self.entradas.get(vpn)
        if pte is not None:
            pte.presente = False
            pte.marco = None
            pte.ref = False
