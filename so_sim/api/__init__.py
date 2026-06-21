"""Routers de la API (capa delgada sobre el SimulationManager)."""
from . import routes_config, routes_control, routes_state

__all__ = ["routes_control", "routes_state", "routes_config"]
