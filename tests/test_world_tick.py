"""Tests de integracion y determinismo del motor de ticks."""
from so_sim.core import World, to_dict
from so_sim.scenarios import presets
from tests.helpers import correr, hist


def _firma(w: World):
    return (hist(w),
            {p.pid: (p.t_fin, p.espera_acumulada, p.t_primer_despacho) for p in w.procesos},
            w.mmu.fallos, w.mmu.aciertos)


def test_determinismo_misma_config_misma_traza():
    a = correr(World(presets.cargar("basico")))
    b = correr(World(presets.cargar("basico")))
    assert _firma(a) == _firma(b)


def test_reset_reproduce_la_corrida():
    w = correr(World(presets.cargar("page_faults")))
    firma1 = _firma(w)
    w.reset()
    correr(w)
    assert _firma(w) == firma1


def test_todos_los_presets_terminan_y_serializan():
    for nombre in presets.PRESETS:
        w = correr(World(presets.cargar(nombre)))
        assert w.terminado, f"{nombre} no termino"
        assert all(p.estado.value == "TERMINADO" for p in w.procesos)
        snap = to_dict(w, corriendo=False, velocidad_ms=500)
        # El snapshot debe ser serializable y tener las claves del contrato.
        for clave in ("tick", "cpu", "procesos", "colas", "memoria", "io", "gantt", "metricas"):
            assert clave in snap


def test_gantt_cubre_todos_los_ticks():
    w = correr(World(presets.cargar("round_robin")))
    snap = to_dict(w)
    # Los segmentos del Gantt deben cubrir exactamente [0, tick) sin huecos.
    fin_esperado = 0
    for seg in snap["gantt"]:
        assert seg["inicio"] == fin_esperado
        fin_esperado = seg["fin"]
    assert fin_esperado == w.tick_actual
