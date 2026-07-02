"""Control del bucle de simulacion: play / pause / step / reset / speed."""
from fastapi import APIRouter, HTTPException, Request

from .schemas import SpeedBody, TecladoBody

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


@router.post("/teclado/senal")
async def teclado_senal(request: Request):
    """Dispara una interrupcion de teclado sobre el proceso en CPU (boton ⌨️)."""
    await _mgr(request).senal_teclado()
    return {"ok": True}


@router.post("/teclado/resolver")
async def teclado_resolver(body: TecladoBody, request: Request):
    if body.accion not in ("cancelar", "continuar"):
        raise HTTPException(status_code=400, detail="Accion debe ser 'cancelar' o 'continuar'.")
    await _mgr(request).resolver_teclado(body.accion)
    return {"ok": True}
