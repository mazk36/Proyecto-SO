"""Calculo centralizado de metricas de planificacion.

Convencion de tiempo: el tick `t` cubre el intervalo [t, t+1). Un proceso que
termina durante el tick `t_fin` completa en `t_fin + 1`.
  - retorno   = (t_fin + 1) - llegada
  - respuesta = t_primer_despacho - llegada
  - espera    = ticks que el proceso paso en estado LISTO (espera_acumulada)
La espera se mide directamente (no se deriva), por lo que es exacta aun con E/S
de por medio.
"""
from typing import List, Optional

from .pcb import PCB


def retorno(p: PCB) -> Optional[int]:
    if p.t_fin is None:
        return None
    return (p.t_fin + 1) - p.llegada


def respuesta(p: PCB) -> Optional[int]:
    if p.t_primer_despacho is None:
        return None
    return p.t_primer_despacho - p.llegada


def espera(p: PCB) -> int:
    return p.espera_acumulada


def metricas_proceso(p: PCB) -> dict:
    return {"espera": espera(p), "retorno": retorno(p), "respuesta": respuesta(p)}


def promedios(procesos: List[PCB]) -> dict:
    terminados = [p for p in procesos if p.t_fin is not None]
    if not terminados:
        return {"espera": None, "retorno": None, "respuesta": None,
                "terminados": 0, "total": len(procesos)}
    n = len(terminados)
    prom_esp = sum(espera(p) for p in terminados) / n
    prom_ret = sum(retorno(p) for p in terminados) / n
    resp = [respuesta(p) for p in terminados if respuesta(p) is not None]
    prom_resp = sum(resp) / len(resp) if resp else None
    return {
        "espera": round(prom_esp, 2),
        "retorno": round(prom_ret, 2),
        "respuesta": round(prom_resp, 2) if prom_resp is not None else None,
        "terminados": n, "total": len(procesos),
    }
