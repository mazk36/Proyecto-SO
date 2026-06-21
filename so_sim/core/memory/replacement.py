"""Algoritmos de reemplazo de paginas (patron Strategy).

Solo se invocan cuando la memoria fisica esta llena (no hay marco libre).
Todos rompen empates de forma explicita (menor pid, luego menor vpn) para que
las corridas sean 100% reproducibles.
"""
from .frames import PhysicalMemory

INF = 10 ** 9


class Replacer:
    nombre = "base"

    def elegir_victima(self, memoria: PhysicalMemory, world,
                       pid_entrante: int, vpn_entrante: int) -> int:
        raise NotImplementedError


class FIFOReplacer(Replacer):
    """Reemplaza la pagina cargada hace mas tiempo (orden de carga)."""
    nombre = "fifo"

    def elegir_victima(self, memoria, world, pid_entrante, vpn_entrante):
        return min(memoria.ocupados(),
                   key=lambda i: (memoria.marcos[i].cargada_en,
                                  memoria.marcos[i].pid,
                                  memoria.marcos[i].vpn))


class LRUReplacer(Replacer):
    """Reemplaza la pagina usada hace mas tiempo (menor ultimo_uso)."""
    nombre = "lru"

    def elegir_victima(self, memoria, world, pid_entrante, vpn_entrante):
        return min(memoria.ocupados(),
                   key=lambda i: (memoria.marcos[i].ultimo_uso,
                                  memoria.marcos[i].pid,
                                  memoria.marcos[i].vpn))


class OptimoReplacer(Replacer):
    """Optimo de Belady: reemplaza la pagina cuyo proximo uso esta mas lejano
    (o que no vuelve a usarse). Solo es posible porque los accesos son
    declarativos (plan_mem); se documenta como cota teorica no realizable en un
    SO real. La distancia se mide en unidades de CPU del proceso dueno."""
    nombre = "optimo"

    def elegir_victima(self, memoria, world, pid_entrante, vpn_entrante):
        return max(memoria.ocupados(),
                   key=lambda i: (world.distancia_proximo_uso(memoria.marcos[i].pid,
                                                              memoria.marcos[i].vpn),
                                  -memoria.marcos[i].pid,
                                  -memoria.marcos[i].vpn))


class RelojReplacer(Replacer):
    """Segunda oportunidad / Reloj: puntero circular sobre los marcos. Si el
    marco apuntado tiene ref=1 se pone a 0 y se avanza (segunda oportunidad); el
    primero con ref=0 es la victima."""
    nombre = "reloj"

    def elegir_victima(self, memoria, world, pid_entrante, vpn_entrante):
        n = memoria.num_marcos
        for _ in range(2 * n + 1):
            i = memoria.puntero_reloj
            m = memoria.marcos[i]
            memoria.puntero_reloj = (i + 1) % n
            if m is None:
                continue
            if m.ref:
                m.ref = False
            else:
                return i
        return memoria.ocupados()[0]
