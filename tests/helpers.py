"""Utilidades comunes para los tests del nucleo."""
from so_sim.core import MundoConfig, World


def correr(world: World, max_ticks: int = 3000) -> World:
    pasos = 0
    while not world.terminado and pasos < max_ticks:
        world.tick()
        pasos += 1
    return world


def mundo(dic: dict) -> World:
    return World(MundoConfig.from_dict(dic))


def hist(world: World):
    return list(world.cpu_historial)


def proc(world: World, pid: int):
    return world.pcb[pid]
