"""Tests del subsistema de E/S: bloqueo, solapamiento CPU/E-S e interrupcion."""
from so_sim.core import World
from so_sim.core.enums import TipoEvento
from so_sim.core.io import Device, IoSubsystem
from so_sim.scenarios import presets
from tests.helpers import correr, hist, proc


def test_dispositivo_sirve_n_ticks_y_cuenta_desde_el_siguiente():
    io = IoSubsystem()
    io.agregar(Device("Disco", "disco"))
    io.encolar("Disco", pid=7, duracion=3)
    # El tick en que se encola lo pone en servicio pero NO descuenta aun.
    assert io.tick() == []                       # arranca servicio
    assert io.tick() == []                       # 3 -> 2
    assert io.tick() == []                       # 2 -> 1
    assert io.tick() == [(7, "Disco")]           # 1 -> 0: interrupcion


def test_io_bloquea_y_libera_la_cpu():
    w = correr(World(presets.cargar("io_overlap")))
    # P1 se bloquea por E/S y P2 ocupa la CPU mientras tanto.
    assert hist(w) == [1, 1, 2, 2, 2, 2, 1, 1, 1, 1]
    assert proc(w, 1).t_fin == 9
    assert proc(w, 2).t_fin == 5
    tipos = {e["tipo"] for e in w.log.ultimos(1000)}
    assert TipoEvento.BLOQUEO_IO.value in tipos
    assert TipoEvento.INTERRUPCION_IO.value in tipos


def test_proceso_vuelve_a_listo_tras_io():
    w = World(presets.cargar("io_overlap"))
    # Avanza hasta que P1 este bloqueado.
    bloqueado = False
    for _ in range(20):
        w.tick()
        if proc(w, 1).estado.value == "BLOQUEADO":
            bloqueado = True
            break
    assert bloqueado, "P1 deberia bloquearse por E/S"
    correr(w)
    assert proc(w, 1).estado.value == "TERMINADO"
