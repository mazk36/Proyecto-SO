"""SimulationManager: unico punto que toca asyncio/FastAPI.

Posee el World, gestiona el bucle de play con un asyncio.Lock unico (el loop de
play y el step manual nunca ejecutan tick() a la vez) y publica snapshots a las
colas de los suscriptores SSE.
"""
import asyncio
from typing import List, Optional

from .core import MundoConfig, World, to_dict


class SimulationManager:
    def __init__(self, cfg: MundoConfig) -> None:
        self.cfg = cfg
        self.world = World(cfg)
        self.lock = asyncio.Lock()
        self.subscribers: List[asyncio.Queue] = []
        self.velocidad_ms = 600
        self.corriendo = False
        self._task: Optional[asyncio.Task] = None

    # --------------------------------------------------------------- snapshots
    def snapshot(self) -> dict:
        return to_dict(self.world, corriendo=self.corriendo,
                       velocidad_ms=self.velocidad_ms)

    async def _publish(self) -> None:
        snap = self.snapshot()
        for q in list(self.subscribers):
            try:
                q.put_nowait(snap)
            except asyncio.QueueFull:
                pass

    async def subscribe(self) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue(maxsize=64)
        self.subscribers.append(q)
        await q.put(self.snapshot())
        return q

    def unsubscribe(self, q: asyncio.Queue) -> None:
        if q in self.subscribers:
            self.subscribers.remove(q)

    # ----------------------------------------------------------------- control
    async def play(self) -> None:
        if self.corriendo or self.world.terminado:
            return
        self.corriendo = True
        self._task = asyncio.create_task(self._loop())
        await self._publish()

    async def _loop(self) -> None:
        try:
            while self.corriendo and not self.world.terminado:
                await asyncio.sleep(self.velocidad_ms / 1000)
                if not self.corriendo:
                    break
                async with self.lock:
                    if self.world.terminado:
                        break
                    self.world.tick()
                await self._publish()
        except asyncio.CancelledError:
            pass
        finally:
            self.corriendo = False
            await self._publish()

    async def _detener_task(self) -> None:
        self.corriendo = False
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except (asyncio.CancelledError, Exception):
                pass
            self._task = None

    async def pause(self) -> None:
        await self._detener_task()
        await self._publish()

    async def step(self) -> None:
        await self._detener_task()
        async with self.lock:
            if not self.world.terminado:
                self.world.tick()
        await self._publish()

    async def set_speed(self, ms: int) -> None:
        self.velocidad_ms = max(50, min(5000, int(ms)))
        await self._publish()

    async def reset(self) -> None:
        await self._detener_task()
        async with self.lock:
            self.world.reset()
        await self._publish()

    async def set_scheduler(self, algo: str, quantum: Optional[int] = None) -> None:
        async with self.lock:
            self.world.set_scheduler(algo, quantum)
        await self._publish()

    async def set_replacer(self, algo: str) -> None:
        async with self.lock:
            self.world.set_replacer(algo)
        await self._publish()

    async def load_config(self, cfg: MundoConfig) -> None:
        cfg.validar()
        await self._detener_task()
        async with self.lock:
            self.cfg = cfg
            self.world = World(cfg)
        await self._publish()

    async def shutdown(self) -> None:
        await self._detener_task()
