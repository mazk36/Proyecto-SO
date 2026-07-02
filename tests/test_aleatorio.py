"""Tests del generador aleatorio: rangos de las formulas, determinismo por semilla
y tasa de error aproximada."""
from so_sim.core.aleatorio import Generador


def test_rangos_interrupciones():
    g = Generador(1)
    for _ in range(1000):
        assert 5 <= g.cantidad_interrupciones(10, 256) <= 20
        assert 5 <= g.duracion_interrupcion(10) <= 20


def test_determinismo_misma_semilla():
    a = Generador(42)
    b = Generador(42)
    sa = [a.cantidad_interrupciones(7, 128) for _ in range(30)]
    sb = [b.cantidad_interrupciones(7, 128) for _ in range(30)]
    assert sa == sb


def test_tasa_error_aproximada():
    # 0.5% sobre 10000 -> ~50 (margen amplio para no ser fragil).
    g = Generador(3)
    hits = sum(1 for _ in range(10000) if g.marca_error(0.005))
    assert 20 <= hits <= 90


def test_generar_procesos_reproducible():
    a = Generador(9).generar_procesos(15, ["Disco", "Red"])
    b = Generador(9).generar_procesos(15, ["Disco", "Red"])
    assert a == b
    assert len(a) == 15
    for p in a:
        assert p["rafaga"] >= 1
        assert p["tam_ejecutable"] > 0
