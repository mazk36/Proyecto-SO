"""Contrato JSON unico con el frontend: to_dict(world) -> dict serializable.

Aisla el formato de presentacion del modelo interno; el frontend re-renderiza de
forma idempotente desde este unico objeto.
"""
from typing import List, Optional

from . import metrics
from .enums import (NOMBRE_ESTRATEGIA, NOMBRE_REPLACE, NOMBRE_SCHED, EstrategiaMem,
                    Estado, ReplaceAlgo, SchedAlgo)
from .memfisica.memoria import SO
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


def _nombre_estrategia(clave: str) -> str:
    try:
        return NOMBRE_ESTRATEGIA[EstrategiaMem(clave)]
    except ValueError:
        return clave


def _memoria_fisica(world) -> dict:
    mf = world.mem_fisica
    bloques = []
    for idx, d in enumerate(mf.duenos):
        if d is None:
            bloques.append({"idx": idx, "tipo": "libre", "pid": None, "color": None})
        elif d == SO:
            bloques.append({"idx": idx, "tipo": "so", "pid": None, "color": None})
        else:
            bloques.append({"idx": idx, "tipo": "proc", "pid": d, "color": _color(world, d)})
    frag = mf.fragmentacion_interna()
    usada = mf.ram_usada_procesos()
    return {
        "ram_total": mf.ram_total, "ram_so": mf.ram_so, "tam_bloque": mf.tam_bloque,
        "num_bloques": mf.num_bloques, "bloques_so": mf.bloques_so,
        "estrategia": world.cfg.estrategia_mem,
        "estrategia_nombre": _nombre_estrategia(world.cfg.estrategia_mem),
        "bloques": bloques,
        "bloques_libres": mf.bloques_libres(),
        "bloques_ocupados": mf.bloques_ocupados_procesos(),
        "ram_usada_procesos": usada,
        "ram_libre": mf.ram_libre(),
        "fragmentacion": frag,
        "frag_pct": round(100 * frag / usada, 1) if usada else 0.0,
    }


def _paginacion(world) -> Optional[dict]:
    if not world.paginacion_activa:
        return None
    mmu = world.mmu
    marcos = []
    for idx, m in enumerate(world.memoria.marcos):
        if m is None:
            marcos.append({"idx": idx, "pid": None, "vpn": None, "color": None, "ref": False})
        else:
            marcos.append({"idx": idx, "pid": m.pid, "vpn": m.vpn,
                           "color": _color(world, m.pid), "ref": m.ref})
    tablas = {}
    for p in world.procesos:
        if p.tabla.entradas:
            tablas[str(p.pid)] = [{
                "vpn": vpn, "presente": e.presente, "marco": e.marco, "ref": e.ref,
            } for vpn, e in sorted(p.tabla.entradas.items())]
    total = mmu.aciertos + mmu.fallos
    return {
        "tam_pagina": world.tam_pagina, "offset_bits": world.offset_bits,
        "num_marcos": world.memoria.num_marcos,
        "algoritmo": world.cfg.replacer, "algoritmo_nombre": _nombre_replace(world.cfg.replacer),
        "puntero_reloj": world.memoria.puntero_reloj,
        "marcos": marcos, "tablas": tablas,
        "contadores": {
            "aciertos": mmu.aciertos, "fallos": mmu.fallos,
            "tasa_fallos": round(mmu.fallos / total, 3) if total else 0.0,
            "hit_ratio": round(mmu.aciertos / total, 3) if total else 0.0,
        },
        "ultimo_evento_va": mmu.ultimo_evento,
    }


def to_dict(world, corriendo: bool = False, velocidad_ms: int = 500) -> dict:
    sched = world.scheduler
    procesos = world.procesos

    # --- procesos ---
    proc_json = [{
        "pid": p.pid, "nombre": p.nombre, "estado": p.estado.value,
        "prioridad": p.prioridad, "nivel_mlq": p.nivel_mlq,
        "llegada": p.llegada, "rafaga_total": p.rafaga_total,
        "rafaga_restante": p.rafaga_restante, "cpu_consumido": p.cpu_consumido,
        "pc": p.pc, "quantum_restante": p.quantum_restante, "color": p.color,
        "tam_ejecutable": p.tam_ejecutable, "tam_datos": p.tam_datos,
        "tam_dinamica": p.tam_dinamica, "tam_total": p.tam_total,
        "direccion_inicial": p.direccion_inicial, "bloques": list(p.bloques),
        "codigo_error": p.codigo_error,
        "metricas": metrics.metricas_proceso(p),
    } for p in procesos]

    # --- colas (4 colas + terminados) ---
    colas = {
        "nuevos": sorted(_pids(procesos, Estado.NUEVO)),
        "listos": [p.pid for p in sched.listos()],
        "bloqueados": sorted(_pids(procesos, Estado.BLOQUEADO)),
        "terminados": [p.pid for p in sorted(
            (x for x in procesos if x.estado in (Estado.TERMINADO, Estado.ERROR)),
            key=lambda x: (x.t_fin if x.t_fin is not None else 0, x.pid))],
    }
    if isinstance(sched, MLQ):
        colas["mlq"] = {"alta": [p.pid for p in sched.alta],
                        "baja": [p.pid for p in sched.baja]}

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

    # --- CPU + PC + dispatcher ---
    cpu = {
        "algoritmo": world.cfg.scheduler, "algoritmo_nombre": _nombre_sched(world.cfg.scheduler),
        "quantum": getattr(sched, "quantum", None),
        "pid_ejecutando": world.en_cpu.pid if world.en_cpu else None,
        "nombre_ejecutando": world.en_cpu.nombre if world.en_cpu else None,
        "color_ejecutando": world.en_cpu.color if world.en_cpu else None,
        "pc": world.en_cpu.pc if world.en_cpu else world.dispatcher.pc_cargado,
        "rafaga_total": world.en_cpu.rafaga_total if world.en_cpu else None,
        "cpu_consumido": world.en_cpu.cpu_consumido if world.en_cpu else None,
        "quantum_restante": world.en_cpu.quantum_restante if world.en_cpu else None,
        "cambiando_contexto": world._cc_pendiente > 0,
    }
    dispatcher = {
        "costo_cambio": world.costo_cambio,
        "total_cambios": world.dispatcher.total_cambios,
        "cambiando": world._cc_pendiente > 0,
    }

    return {
        "tick": world.tick_actual,
        "corriendo": corriendo,
        "velocidad_ms": velocidad_ms,
        "terminado": world.terminado,
        "cpu": cpu,
        "dispatcher": dispatcher,
        "procesos": proc_json,
        "colas": colas,
        "memoria_fisica": _memoria_fisica(world),
        "memoria": _paginacion(world),        # None si la paginacion (PLUS) esta apagada
        "io": {"dispositivos": dispositivos},
        "decision_teclado": world.decision_teclado,
        "gantt": _gantt(world),
        "metricas": metrics.promedios(procesos),
        "eventos": world.log.ultimos(MAX_EVENTOS),
    }
