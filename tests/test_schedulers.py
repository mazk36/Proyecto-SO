"""Tests deterministas de cada algoritmo de planificacion (casos de pizarra)."""
from tests.helpers import correr, hist, mundo, proc


def test_fcfs_orden_y_metricas():
    w = correr(mundo({
        "scheduler": "fcfs",
        "procesos": [
            {"pid": 1, "rafaga": 3, "llegada": 0},
            {"pid": 2, "rafaga": 2, "llegada": 0},
        ],
    }))
    assert hist(w) == [1, 1, 1, 2, 2]
    p1, p2 = proc(w, 1), proc(w, 2)
    assert p1.t_fin == 2 and p2.t_fin == 4
    # retorno = (t_fin + 1) - llegada
    assert (p1.t_fin + 1) == 3
    assert (p2.t_fin + 1) == 5
    assert p1.espera_acumulada == 0
    assert p2.espera_acumulada == 3
    assert p1.t_primer_despacho == 0 and p2.t_primer_despacho == 3


def test_round_robin_quantum():
    w = correr(mundo({
        "scheduler": "rr", "quantum": 2,
        "procesos": [
            {"pid": 1, "rafaga": 5, "llegada": 0},
            {"pid": 2, "rafaga": 3, "llegada": 0},
        ],
    }))
    assert hist(w) == [1, 1, 2, 2, 1, 1, 2, 1]
    assert proc(w, 1).t_fin == 7
    assert proc(w, 2).t_fin == 6


def test_sjf_no_apropiativo():
    # P1 corre completo; luego el mas corto (P3) antes que P2.
    w = correr(mundo({
        "scheduler": "sjf",
        "procesos": [
            {"pid": 1, "rafaga": 4, "llegada": 0},
            {"pid": 2, "rafaga": 2, "llegada": 1},
            {"pid": 3, "rafaga": 1, "llegada": 2},
        ],
    }))
    assert hist(w) == [1, 1, 1, 1, 3, 2, 2]


def test_srtf_apropiativo():
    # La llegada de P2 (mas corto) expropia a P1.
    w = correr(mundo({
        "scheduler": "srtf",
        "procesos": [
            {"pid": 1, "rafaga": 5, "llegada": 0},
            {"pid": 2, "rafaga": 2, "llegada": 1},
        ],
    }))
    assert hist(w) == [1, 2, 2, 1, 1, 1, 1]
    assert proc(w, 2).t_fin == 2


def test_prioridad_apropiativa():
    w = correr(mundo({
        "scheduler": "prioridad_ap",
        "procesos": [
            {"pid": 1, "rafaga": 4, "llegada": 0, "prioridad": 3},
            {"pid": 2, "rafaga": 2, "llegada": 2, "prioridad": 1},
        ],
    }))
    assert hist(w) == [1, 1, 2, 2, 1, 1]


def test_mlq_alta_antes_que_baja():
    w = correr(mundo({
        "scheduler": "mlq", "quantum": 2,
        "procesos": [
            {"pid": 1, "rafaga": 4, "llegada": 0, "nivel_mlq": "ALTA"},
            {"pid": 2, "rafaga": 4, "llegada": 0, "nivel_mlq": "ALTA"},
            {"pid": 3, "rafaga": 6, "llegada": 0, "nivel_mlq": "BAJA"},
        ],
    }))
    assert hist(w) == [1, 1, 2, 2, 1, 1, 2, 2, 3, 3, 3, 3, 3, 3]
    # El proceso de baja prioridad solo arranca cuando los de alta terminan.
    assert hist(w).index(3) == 8


def test_cambio_scheduler_en_caliente():
    # Empieza en FCFS, pasa a SRTF tras 1 tick; el cambio no rompe el estado.
    w = mundo({
        "scheduler": "fcfs",
        "procesos": [
            {"pid": 1, "rafaga": 6, "llegada": 0},
            {"pid": 2, "rafaga": 2, "llegada": 0},
        ],
    })
    w.tick()  # P1 despachado bajo FCFS
    w.set_scheduler("srtf")
    correr(w)
    # Ambos terminan y P2 (mas corto) acaba antes que P1.
    assert proc(w, 1).t_fin is not None
    assert proc(w, 2).t_fin is not None
    assert proc(w, 2).t_fin < proc(w, 1).t_fin
