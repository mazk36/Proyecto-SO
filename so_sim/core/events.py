"""Bitacora de eventos en espanol (una linea por hecho relevante de cada tick)."""
from dataclasses import dataclass, asdict
from typing import List

from .enums import TipoEvento


@dataclass
class Event:
    tick: int
    tipo: TipoEvento
    texto: str

    def to_dict(self) -> dict:
        d = asdict(self)
        d["tipo"] = self.tipo.value
        return d


class EventLog:
    def __init__(self) -> None:
        self.eventos: List[Event] = []

    def add(self, tick: int, tipo: TipoEvento, texto: str) -> None:
        self.eventos.append(Event(tick, tipo, texto))

    def ultimos(self, n: int) -> List[dict]:
        return [e.to_dict() for e in self.eventos[-n:]]

    def limpiar(self) -> None:
        self.eventos.clear()
