"""Tests del modulo de memoria FISICA: asignacion contigua, fragmentacion interna,
reserva del SO y diferencia entre First/Best/Worst-Fit."""
from so_sim.core.memfisica import MemoriaFisica
from so_sim.core.pcb import PCB


def _p(pid: int, tam: int) -> PCB:
    return PCB(pid=pid, nombre=f"P{pid}", llegada=0, rafaga_total=1, tam_ejecutable=tam)


def test_asignacion_contigua_y_direccion():
    m = MemoriaFisica(1000, 0, 100, "first_fit")   # 10 bloques de 100 KB
    p = _p(1, 250)                                  # necesita 3 bloques
    assert m.asignar(p) is True
    assert p.bloques == [0, 1, 2]
    assert p.direccion_inicial == 0
    assert m.bloques_libres() == 7


def test_fragmentacion_interna():
    m = MemoriaFisica(1000, 0, 100, "first_fit")
    m.asignar(_p(1, 250))          # 3 bloques = 300 KB reservados, 250 reales -> 50 KB
    assert m.fragmentacion_interna() == 50


def test_reserva_del_so():
    m = MemoriaFisica(1000, 200, 100, "first_fit")   # 2 bloques reservados al SO
    assert m.bloques_so == 2
    p = _p(1, 100)
    m.asignar(p)
    assert p.bloques == [2]          # se coloca despues de la franja del SO


def _con_dos_huecos(est: str) -> MemoriaFisica:
    # Deja un hueco de 4 bloques en [0..3] y otro de 6 en [5..10].
    m = MemoriaFisica(1100, 0, 100, est)
    m.asignar(_p(1, 400)); m.asignar(_p(2, 100)); m.asignar(_p(3, 600))
    m.liberar(1); m.liberar(3)
    return m


def test_first_best_worst_eligen_distinto_hueco():
    # Peticion de 3 bloques (300 KB): huecos disponibles de 4 y 6 bloques.
    mf = _con_dos_huecos("first_fit"); pf = _p(4, 300); mf.asignar(pf)
    mb = _con_dos_huecos("best_fit"); pb = _p(4, 300); mb.asignar(pb)
    mw = _con_dos_huecos("worst_fit"); pw = _p(4, 300); mw.asignar(pw)
    assert pf.bloques[0] == 0    # First-Fit: primer hueco que cabe (el de 4)
    assert pb.bloques[0] == 0    # Best-Fit: el menor que cabe (el de 4)
    assert pw.bloques[0] == 5    # Worst-Fit: el mayor (el de 6)


def test_worst_fit_falla_por_fragmentacion_externa():
    # Tras colocar 3 bloques, pedir 6: worst-fit se queda sin hueco contiguo.
    mw = _con_dos_huecos("worst_fit")
    mw.asignar(_p(4, 300))               # ocupa parte del hueco grande
    assert mw.cabe(600) is False         # ya no hay 6 bloques contiguos
    mf = _con_dos_huecos("first_fit")
    mf.asignar(_p(4, 300))               # deja intacto el hueco grande
    assert mf.cabe(600) is True
