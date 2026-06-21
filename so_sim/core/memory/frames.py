"""Memoria fisica: conjunto finito de marcos. Lo limitado de `num_marcos` es lo
que fuerza los page faults cuando hay mas paginas activas que marcos."""
from dataclasses import dataclass
from typing import List, Optional, Tuple


@dataclass
class Marco:
    pid: int
    vpn: int
    cargada_en: int      # tick de carga (FIFO)
    ultimo_uso: int      # tick del ultimo acceso (LRU)
    ref: bool = True     # bit de referencia (Reloj)


class PhysicalMemory:
    def __init__(self, num_marcos: int) -> None:
        self.num_marcos = num_marcos
        self.marcos: List[Optional[Marco]] = [None] * num_marcos
        self.puntero_reloj = 0   # manecilla del algoritmo Reloj

    def marco_libre(self) -> Optional[int]:
        for i, m in enumerate(self.marcos):
            if m is None:
                return i
        return None

    def ocupados(self) -> List[int]:
        return [i for i, m in enumerate(self.marcos) if m is not None]

    def cargar(self, idx: int, pid: int, vpn: int, tick: int) -> None:
        self.marcos[idx] = Marco(pid=pid, vpn=vpn, cargada_en=tick,
                                 ultimo_uso=tick, ref=True)

    def liberar_de(self, pid: int) -> List[Tuple[int, int]]:
        """Libera los marcos del proceso `pid`. Devuelve [(idx, vpn), ...]."""
        liberados = []
        for i, m in enumerate(self.marcos):
            if m is not None and m.pid == pid:
                liberados.append((i, m.vpn))
                self.marcos[i] = None
        return liberados
