"""Contrato JSON unico con el frontend: to_dict(world) -> dict serializable.

Aisla el formato de presentacion del modelo interno; el frontend re-renderiza de
forma idempotente desde este unico objeto.
"""
from typing import List, Optional

from . import metrics
from .enums import (NOMBRE_REPLACE, NOMBRE_SCHED, ReplaceAlgo, SchedAlgo,
                    Estado)
from .scheduler.mlq import MLQ

MAX_EVENTOS = 14


def _color(world, pid: Optional[int]) -> Optional[str]:
    if pid is None:
        return None
    p = world.pcb.get(pid)
    return p.color if p else None


def _gantt(world) -> List[dict]:
    seg: List[dict] = []
    for i, pid in enumerate(world.cpu_historial):
        if seg and seg[-1]["pid"] == pid:
            seg[-1]["fin"] = i + 1
        else:
            seg.append({"pid": pid, "inicio": i, "fin": i + 1, "color": _color(world, pid)})
    return seg


def _pids(procesos, estado) -> List[int]:
    return [p.pid for p in procesos if p.estado == estado]


def _nombre_sched(clave: str) -> str:
    try:
        return NOMBRE_SCHED[SchedAlgo(clave)]
    except ValueError:
        return clave


def _nombre_replace(clave: str) -> str:
    try:
        return NOMBRE_REPLACE[ReplaceAlgo(clave)]
    except ValueError:
        return clave


def to_dict(world, corriendo: bool = False, velocidad_ms: int = 500) -> dict:
    sched = world.scheduler
    mmu = world.mmu
    procesos = world.procesos

    # --- procesos ---
    proc_json = [{
        "pid": p.pid, "nombre": p.nombre, "estado": p.estado.value,
        "prioridad": p.prioridad, "nivel_mlq": p.nivel_mlq,
        "llegada": p.llegada, "rafaga_total": p.rafaga_total,
        "rafaga_restante": p.rafaga_restante, "cpu_consumido": p.cpu_consumido,
        "quantum_restante": p.quantum_restante, "color": p.color,
        "metricas": metrics.metricas_proceso(p),
    } for p in procesos]

    # --- colas ---
    colas = {
        "nuevos": sorted(_pids(procesos, Estado.NUEVO)),
        "listos": [p.pid for p in sched.listos()],
        "bloqueados": sorted(_pids(procesos, Estado.BLOQUEADO)),
        "terminados": [p.pid for p in sorted(
            (x for x in procesos if x.estado == Estado.TERMINADO),
            key=lambda x: (x.t_fin if x.t_fin is not None else 0, x.pid))],
    }
    if isinstance(sched, MLQ):
        colas["mlq"] = {"alta": [p.pid for p in sched.alta],
                        "baja": [p.pid for p in sched.baja]}

    # --- memoria ---
    marcos = []
    for idx, m in enumerate(world.memoria.marcos):
        if m is None:
            marcos.append({"idx": idx, "pid": None, "vpn": None, "color": None, "ref": False})
        else:
            marcos.append({"idx": idx, "pid": m.pid, "vpn": m.vpn,
                           "color": _color(world, m.pid), "ref": m.ref})
    tablas = {}
    for p in procesos:
        if p.tabla.entradas:
            tablas[str(p.pid)] = [{
                "vpn": vpn, "presente": e.presente, "marco": e.marco, "ref": e.ref,
            } for vpn, e in sorted(p.tabla.entradas.items())]
    total = mmu.aciertos + mmu.fallos
    memoria = {
        "tam_pagina": world.tam_pagina, "offset_bits": world.offset_bits,
        "num_marcos": world.memoria.num_marcos,
        "algoritmo": world.cfg.replacer, "algoritmo_nombre": _nombre_replace(world.cfg.replacer),
        "puntero_reloj": world.memoria.puntero_reloj,
        "marcos": marcos, "tablas": tablas,
        "contadores": {
            "aciertos": mmu.aciertos, "fallos": mmu.fallos,
            "tasa_fallos": round(mmu.fallos / total, 3) if total else 0.0,
        },
        "ultimo_evento_va": mmu.ultimo_evento,
    }

    # --- E/S ---
    dispositivos = []
    for dev in world.io.dispositivos.values():
        es = None
        if dev.en_servicio is not None:
            srv = dev.en_servicio
            prog = 1 - (srv.ticks_restantes / srv.duracion_total) if srv.duracion_total else 1
            es = {"pid": srv.pid, "ticks_restantes": srv.ticks_restantes,
                  "duracion_total": srv.duracion_total, "progreso": round(prog, 2),
                  "color": _color(world, srv.pid)}
        dispositivos.append({
            "nombre": dev.nombre, "tipo": dev.tipo, "en_servicio": es,
            "cola": [{"pid": pid, "color": _color(world, pid)} for pid, _ in dev.cola],
        })

    # --- CPU ---
    cpu = {
        "algoritmo": world.cfg.scheduler, "algoritmo_nombre": _nombre_sched(world.cfg.scheduler),
        "quantum": getattr(sched, "quantum", None),
        "pid_ejecutando": world.en_cpu.pid if world.en_cpu else None,
        "quantum_restante": world.en_cpu.quantum_restante if world.en_cpu else None,
    }

    return {
        "tick": world.tick_actual,
        "corriendo": corriendo,
        "velocidad_ms": velocidad_ms,
        "terminado": world.terminado,
        "cpu": cpu,
        "procesos": proc_json,
        "colas": colas,
        "memoria": memoria,
        "io": {"dispositivos": dispositivos},
        "gantt": _gantt(world),
        "metricas": metrics.promedios(procesos),
        "eventos": world.log.ultimos(MAX_EVENTOS),
    }
