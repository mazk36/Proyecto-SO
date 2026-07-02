"""Comparativas 'headless': corren el mismo escenario a termino variando el
algoritmo de planificacion o la estrategia de memoria, y recolectan metricas para
la tabla comparativa de la UI (y su exportacion a CSV).

No tocan la simulacion en vivo: crean World temporales y los corren hasta el final.
"""
import copy
from typing import Dict, List

from . import metrics
from .config import MundoConfig
from .enums import SCHED_OBLIGATORIOS, EstrategiaMem, NOMBRE_ESTRATEGIA, NOMBRE_SCHED
from .world import World


def _correr(cfg: MundoConfig, max_ticks: int = 20000) -> World:
    """Corre un World a termino, auto-resolviendo el teclado (Continuar) para no
    quedarse esperando decision del usuario en una corrida automatica.

    Recolecta, ademas de las metricas de planificacion:
      - frag_pico / frag_prom: fragmentacion INTERNA (desperdicio dentro de bloques).
      - huecos_pico: numero maximo de huecos libres (indicio de fragmentacion
        EXTERNA, que es donde First/Best/Worst-Fit se diferencian).
      - espera_admision: ticks totales que procesos ya llegados esperaron sin caber
        en memoria (presion de asignacion; menor es mejor).
    """
    from .enums import Estado
    w = World(cfg)
    frag_pico = frag_acum = huecos_pico = espera_admision = pasos = 0
    while not w.terminado and pasos < max_ticks:
        w.tick()
        if w.decision_teclado is not None:
            w.resolver_teclado("continuar")
        f = w.mem_fisica.fragmentacion_interna()
        frag_pico = max(frag_pico, f)
        frag_acum += f
        huecos_pico = max(huecos_pico, len(w.mem_fisica.huecos_libres()))
        espera_admision += sum(1 for p in w.procesos
                               if p.estado == Estado.NUEVO and p.llegada < w.tick_actual)
        pasos += 1
    w._frag_pico = frag_pico
    w._frag_prom = round(frag_acum / pasos, 1) if pasos else 0
    w._huecos_pico = huecos_pico
    w._espera_admision = espera_admision
    return w


def comparar_schedulers(cfg: MundoConfig) -> Dict:
    """Evalua los 4 planificadores obligatorios con el mismo conjunto de procesos."""
    filas: List[dict] = []
    for algo in SCHED_OBLIGATORIOS:
        c = copy.deepcopy(cfg)
        c.scheduler = algo.value
        w = _correr(c)
        m = metrics.promedios(w.procesos)
        filas.append({
            "algoritmo": algo.value, "nombre": NOMBRE_SCHED[algo],
            "espera": m["espera"], "retorno": m["retorno"], "respuesta": m["respuesta"],
            "con_error": m["con_error"],
        })
    return {"tipo": "schedulers", "filas": filas}


# Secuencia de asignacion/liberacion (en KB) disenada para DIFERENCIAR las tres
# estrategias. Es el ejemplo clasico de libro: se crean dos huecos de distinto
# tamano (4 y 6 bloques con bloques de 100 KB) y luego se pide primero un bloque
# pequeno y despues uno grande. Worst-Fit "malgasta" el hueco grande con la
# peticion pequena y luego no puede colocar la grande (fallo por fragmentacion
# externa), mientras First-Fit y Best-Fit si lo logran.
#
# Nota didactica: en este simulador la UBICACION fisica no afecta la planificacion
# (un proceso solo necesita CABER), por eso la diferencia entre estrategias se
# mide con este micro-benchmark de asignacion puro y no con el turnaround.
_BENCH_TAM_BLOQUE = 100
_BENCH_RAM = 1100          # 11 bloques, sin reserva de SO
_BENCH_OPS = [
    ("alloc", 1, 400),     # p1: 4 bloques  [0..3]
    ("alloc", 2, 100),     # p2: 1 bloque   [4]  (separador, no se libera)
    ("alloc", 3, 600),     # p3: 6 bloques  [5..10]
    ("free", 1, 0),        # -> hueco de 4 bloques en [0..3]
    ("free", 3, 0),        # -> hueco de 6 bloques en [5..10]
    ("alloc", 4, 300),     # peticion pequena (3 bloques)
    ("alloc", 5, 600),     # peticion grande (6 bloques)
]


def _bench_estrategia(est: str) -> dict:
    from .memfisica import MemoriaFisica
    from .pcb import PCB
    mem = MemoriaFisica(_BENCH_RAM, 0, _BENCH_TAM_BLOQUE, est)
    procesos: Dict[int, PCB] = {}
    exitosas = 0
    fallos_externos = 0
    for op, pid, tam in _BENCH_OPS:
        if op == "alloc":
            p = PCB(pid=pid, nombre=f"P{pid}", llegada=0, rafaga_total=1,
                    tam_ejecutable=tam)
            if mem.asignar(p):
                procesos[pid] = p
                exitosas += 1
            else:
                # Hay RAM total suficiente pero no contigua => fragmentacion externa.
                if mem.bloques_libres() >= mem.bloques_necesarios(tam):
                    fallos_externos += 1
        else:
            mem.liberar(pid)
            procesos.pop(pid, None)
    return {
        "estrategia": est,
        "nombre": NOMBRE_ESTRATEGIA[EstrategiaMem(est)],
        "asignaciones_ok": exitosas,
        "fallos_externos": fallos_externos,
        "fragmentacion_interna": mem.fragmentacion_interna(),
        "huecos_finales": len(mem.huecos_libres()),
    }


def comparar_estrategias(cfg: MundoConfig = None) -> Dict:
    """Compara First/Best/Worst-Fit con el micro-benchmark de asignacion clasico.
    (No depende de `cfg`; se acepta el parametro por simetria con la otra comparativa.)"""
    filas = [_bench_estrategia(est.value)
             for est in (EstrategiaMem.FIRST_FIT, EstrategiaMem.BEST_FIT, EstrategiaMem.WORST_FIT)]
    return {"tipo": "estrategias", "filas": filas}


def comparativa_completa(cfg: MundoConfig) -> Dict:
    return {
        "schedulers": comparar_schedulers(cfg)["filas"],
        "estrategias": comparar_estrategias(cfg)["filas"],
    }
