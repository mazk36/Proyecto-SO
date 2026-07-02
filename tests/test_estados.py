"""Tests del diagrama de estados (incluye ERROR) y la inyeccion de errores."""
from so_sim.core import MundoConfig, World
from so_sim.core.enums import Estado, transicion_valida


def test_transiciones_validas_e_invalidas():
    assert transicion_valida(Estado.NUEVO, Estado.LISTO)
    assert transicion_valida(Estado.LISTO, Estado.EJECUTANDO)
    assert transicion_valida(Estado.EJECUTANDO, Estado.BLOQUEADO)
    assert transicion_valida(Estado.EJECUTANDO, Estado.ERROR)
    assert transicion_valida(Estado.BLOQUEADO, Estado.LISTO)
    # transiciones fuera del diagrama
    assert not transicion_valida(Estado.NUEVO, Estado.EJECUTANDO)
    assert not transicion_valida(Estado.TERMINADO, Estado.LISTO)
    assert not transicion_valida(Estado.BLOQUEADO, Estado.EJECUTANDO)


def test_tasa_error_total_produce_errores():
    cfg = MundoConfig.from_dict({
        "scheduler": "fcfs", "tasa_error": 1.0,
        "procesos": [{"pid": 1, "rafaga": 2}, {"pid": 2, "rafaga": 2}],
    })
    w = World(cfg)
    pasos = 0
    while not w.terminado and pasos < 500:
        w.tick(); pasos += 1
    assert all(p.estado == Estado.ERROR for p in w.procesos)
    assert all(p.codigo_error for p in w.procesos)


def test_sin_tasa_error_termina_normal():
    cfg = MundoConfig.from_dict({
        "scheduler": "fcfs", "tasa_error": 0.0,
        "procesos": [{"pid": 1, "rafaga": 2}, {"pid": 2, "rafaga": 2}],
    })
    w = World(cfg)
    pasos = 0
    while not w.terminado and pasos < 500:
        w.tick(); pasos += 1
    assert all(p.estado == Estado.TERMINADO for p in w.procesos)
