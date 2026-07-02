"""Estado del mundo: snapshot puntual (/api/state) y stream tiempo real (SSE)."""
import asyncio
import json

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

router = APIRouter(prefix="/api", tags=["estado"])


@router.get("/state")
async def state(request: Request):
    return request.app.state.manager.snapshot()


@router.get("/comparativa")
async def comparativa(request: Request):
    """Comparativa de los 4 planificadores y las 3 estrategias de memoria."""
    return request.app.state.manager.comparativa()


@router.get("/stream")
async def stream(request: Request):
    mgr = request.app.state.manager
    cola = await mgr.subscribe()

    async def generar():
        try:
            while True:
                if await request.is_disconnected():
                    break
                try:
                    data = await asyncio.wait_for(cola.get(), timeout=15)
                    yield f"data: {json.dumps(data, ensure_ascii=False)}\n\n"
                except asyncio.TimeoutError:
                    yield ": keep-alive\n\n"   # comentario SSE para no cerrar la conexion
        finally:
            mgr.unsubscribe(cola)

    headers = {
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "X-Accel-Buffering": "no",   # evita buffering de proxys/antivirus en Windows
    }
    return StreamingResponse(generar(), media_type="text/event-stream", headers=headers)
