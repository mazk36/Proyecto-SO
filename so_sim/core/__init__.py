"""Nucleo puro del simulador (sin dependencias de FastAPI)."""
from .config import MundoConfig, build_world_from_config
from .serialize import to_dict
from .world import World

__all__ = ["World", "MundoConfig", "build_world_from_config", "to_dict"]
