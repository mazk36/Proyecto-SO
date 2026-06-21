"""Control del bucle de simulacion: play / pause / step / reset / speed."""
from fastapi import APIRouter, Request

from .schemas import SpeedBody

router = APIRouter(prefix="/api/control", tags=["control"])


def _mgr(request: Request):
    return request.app.state.manager


@router.post("/play")
async def play(request: Request):
    await _mgr(request).play()
    return {"ok": True}


@router.post("/pause")
async def pause(request: Request):
    await _mgr(request).pause()
    return {"ok": True}


@router.post("/step")
async def step(request: Request):
    await _mgr(request).step()
    return {"ok": True}


@router.post("/reset")
async def reset(request: Request):
    await _mgr(request).reset()
    return {"ok": True}


@router.post("/speed")
async def speed(body: SpeedBody, request: Request):
    await _mgr(request).set_speed(body.velocidad_ms)
    return {"ok": True}
