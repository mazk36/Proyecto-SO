"""MemoriaFisica: RAM dividida en bloques de tamano fijo, administrada por MAPA DE
BITS (se eligio mapa de bits sobre lista encadenada por su simplicidad y por ser
directo de visualizar bloque a bloque en la UI).

Unidades: todo en KB. Sin MMU: la direccion fisica de un proceso es el KB donde
empieza su primer bloque (direccion_inicial = bloque_inicial * tam_bloque).
"""
from typing import Dict, List, Optional, Tuple

from .estrategias import Estrategia, Hueco, get_estrategia

SO = -1   # marcador de bloque reservado por el Sistema Operativo


class MemoriaFisica:
    def __init__(self, ram_total: int, ram_so: int, tam_bloque: int,
                 estrategia: str = "first_fit") -> None:
        self.ram_total = ram_total
        self.ram_so = ram_so
        self.tam_bloque = tam_bloque
        self.num_bloques = ram_total // tam_bloque
        # Mapa de bits: cada celda es None (libre), SO (reservado) o un pid (int).
        self.duenos: List[Optional[int]] = [None] * self.num_bloques
        self.tam_real: Dict[int, int] = {}          # pid -> tam_total real (para fragmentacion)
        self.estrategia: Estrategia = get_estrategia(estrategia)

        # Reserva la franja del SO al inicio (bloques 0..bloques_so-1).
        self.bloques_so = self._ceil_div(ram_so, tam_bloque)
        for i in range(min(self.bloques_so, self.num_bloques)):
            self.duenos[i] = SO

    # ------------------------------------------------------------- utilidades
    @staticmethod
    def _ceil_div(a: int, b: int) -> int:
        return (a + b - 1) // b if b else 0

    def bloques_necesarios(self, tam: int) -> int:
        return max(1, self._ceil_div(tam, self.tam_bloque))

    def huecos_libres(self) -> List[Hueco]:
        """Lista de (inicio, longitud) de tramos contiguos de bloques libres."""
        huecos: List[Hueco] = []
        inicio = None
        for i, d in enumerate(self.duenos):
            if d is None:
                if inicio is None:
                    inicio = i
            else:
                if inicio is not None:
                    huecos.append((inicio, i - inicio))
                    inicio = None
        if inicio is not None:
            huecos.append((inicio, self.num_bloques - inicio))
        return huecos

    # ------------------------------------------------------- asignar / liberar
    def asignar(self, pcb) -> bool:
        """Carga el proceso COMPLETO en bloques contiguos segun la estrategia.
        Actualiza pcb.bloques y pcb.direccion_inicial. Devuelve False si no cabe."""
        necesarios = self.bloques_necesarios(pcb.tam_total)
        inicio = self.estrategia.elegir(self.huecos_libres(), necesarios)
        if inicio is None:
            return False
        for i in range(inicio, inicio + necesarios):
            self.duenos[i] = pcb.pid
        pcb.bloques = list(range(inicio, inicio + necesarios))
        pcb.direccion_inicial = inicio * self.tam_bloque
        self.tam_real[pcb.pid] = pcb.tam_total
        return True

    def liberar(self, pid: int) -> int:
        """Libera todos los bloques del proceso. Devuelve cuantos libero."""
        n = 0
        for i, d in enumerate(self.duenos):
            if d == pid:
                self.duenos[i] = None
                n += 1
        self.tam_real.pop(pid, None)
        return n

    def set_estrategia(self, nombre) -> None:
        self.estrategia = get_estrategia(nombre)

    def cabe(self, tam_total: int) -> bool:
        necesarios = self.bloques_necesarios(tam_total)
        return self.estrategia.elegir(self.huecos_libres(), necesarios) is not None

    # ------------------------------------------------------------- metricas
    def bloques_libres(self) -> int:
        return sum(1 for d in self.duenos if d is None)

    def bloques_ocupados_procesos(self) -> int:
        return sum(1 for d in self.duenos if d not in (None, SO))

    def ram_libre(self) -> int:
        return self.bloques_libres() * self.tam_bloque

    def ram_usada_procesos(self) -> int:
        return self.bloques_ocupados_procesos() * self.tam_bloque

    def fragmentacion_interna(self) -> int:
        """Desperdicio = suma por proceso de (bloques*tam_bloque - tam_real).
        Es memoria reservada pero no aprovechada dentro del ultimo bloque."""
        total = 0
        # cuenta bloques por pid
        conteo: Dict[int, int] = {}
        for d in self.duenos:
            if d not in (None, SO):
                conteo[d] = conteo.get(d, 0) + 1
        for pid, nbloques in conteo.items():
            reservado = nbloques * self.tam_bloque
            real = self.tam_real.get(pid, reservado)
            total += max(0, reservado - real)
        return total

    def mapa(self) -> List[Optional[int]]:
        """Devuelve el mapa de bits crudo (None libre, SO reservado, pid ocupado)."""
        return list(self.duenos)
