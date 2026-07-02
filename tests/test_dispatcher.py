"""Tests del dispatcher: el costo de cambio de contexto agrega ticks y se contabiliza."""
from so_sim.core import MundoConfig, World


def _correr(costo: int) -> World:
    cfg = MundoConfig.from_dict({
        "scheduler": "rr", "quantum": 2, "costo_cambio": costo,
        "procesos": [{"pid": 1, "rafaga": 3}, {"pid": 2, "rafaga": 3}],
    })
    w = World(cfg)
    pasos = 0
    while not w.terminado and pasos < 500:
        w.tick(); pasos += 1
    return w


def test_costo_cambio_agrega_ticks():
    w0 = _correr(0)
    w1 = _correr(1)
    assert w1.tick_actual > w0.tick_actual        # los cambios de contexto cuestan ticks
    assert w1.dispatcher.total_cambios >= 2


def test_sin_costo_no_penaliza():
    w0 = _correr(0)
    # Sin costo, la CPU no queda congelada por el dispatcher.
    assert w0.dispatcher.costo_cambio == 0
    assert all(p.estado.value == "TERMINADO" for p in w0.procesos)
