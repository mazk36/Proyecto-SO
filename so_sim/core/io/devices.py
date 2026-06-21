"""Dispositivos de E/S modelados por TICKS (no por hilos).

Reinterpreta el DMA-con-Thread del codigo base Java como un DMA-de-N-ticks
determinista: conserva el comportamiento asincrono observable (la CPU sigue
trabajando mientras el dispositivo transfiere) sin condiciones de carrera.
"""
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple


@dataclass
class EnServicio:
    pid: int
    ticks_restantes: int
    duracion_total: int


class Device:
    def __init__(self, nombre: str, tipo: str) -> None:
        self.nombre = nombre
        self.tipo = tipo
        self.cola: List[Tuple[int, int]] = []      # [(pid, duracion), ...] FIFO
        self.en_servicio: Optional[EnServicio] = None

    def encolar(self, pid: int, duracion: int) -> None:
        self.cola.append((pid, duracion))

    def ocupado(self) -> bool:
        return self.en_servicio is not None or bool(self.cola)


class IoSubsystem:
    def __init__(self) -> None:
        self.dispositivos: Dict[str, Device] = {}

    def agregar(self, device: Device) -> None:
        self.dispositivos[device.nombre] = device

    def encolar(self, nombre: str, pid: int, duracion: int) -> None:
        if nombre not in self.dispositivos:
            raise ValueError(f"Dispositivo inexistente: {nombre}")
        self.dispositivos[nombre].encolar(pid, duracion)

    def hay_actividad(self) -> bool:
        return any(d.ocupado() for d in self.dispositivos.values())

    def tick(self) -> List[Tuple[int, str]]:
        """Avanza todos los dispositivos un tick. Un proceso recien encolado
        empieza a servirse este tick pero NO descuenta hasta el proximo (cuenta
        a partir del tick siguiente). Devuelve [(pid, nombre_dispositivo), ...]
        de las E/S completadas (interrupciones)."""
        interrupciones: List[Tuple[int, str]] = []
        for dev in self.dispositivos.values():
            if dev.en_servicio is not None:
                dev.en_servicio.ticks_restantes -= 1
                if dev.en_servicio.ticks_restantes <= 0:
                    interrupciones.append((dev.en_servicio.pid, dev.nombre))
                    dev.en_servicio = None
            if dev.en_servicio is None and dev.cola:
                pid, dur = dev.cola.pop(0)
                dev.en_servicio = EnServicio(pid=pid, ticks_restantes=dur,
                                             duracion_total=dur)
        return interrupciones
