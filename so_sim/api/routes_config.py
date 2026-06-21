"""Configuracion en caliente: planificador, reemplazo, escenario y presets."""
from fastapi import APIRouter, HTTPException, Request

from ..core import MundoConfig
from ..scenarios import presets
from .schemas import ReplacerBody, ScenarioBody, SchedulerBody

router = APIRouter(prefix="/api", tags=["config"])


def _mgr(request: Request):
    return request.app.state.manager


@router.post("/config/scheduler")
async def cambiar_scheduler(body: SchedulerBody, request: Request):
    try:
        await _mgr(request).set_scheduler(body.algoritmo, body.quantum)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"ok": True}


@router.post("/config/replacer")
async def cambiar_replacer(body: ReplacerBody, request: Request):
    try:
        await _mgr(request).set_replacer(body.algoritmo)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"ok": True}


@router.post("/config/scenario")
async def cargar_escenario(body: ScenarioBody, request: Request):
    try:
        cfg = MundoConfig.from_dict(body.model_dump())
        await _mgr(request).load_config(cfg)
    except (ValueError, KeyError) as e:
        raise HTTPException(status_code=400, detail=f"Configuracion invalida: {e}")
    return {"ok": True}


@router.get("/config/actual")
async def config_actual(request: Request):
    """Devuelve el escenario actual (para precargar el editor de procesos)."""
    return _mgr(request).cfg.to_dict()


@router.get("/presets")
async def listar_presets():
    return presets.listar()


@router.post("/presets/{nombre}")
async def cargar_preset(nombre: str, request: Request):
    try:
        cfg = presets.cargar(nombre)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Preset desconocido: {nombre}")
    await _mgr(request).load_config(cfg)
    return {"ok": True}
