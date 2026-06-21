"""Simulador educativo de Sistema Operativo (procesos + memoria virtual + E/S).

El paquete `so_sim.core` es el nucleo puro de simulacion: NO importa FastAPI y se
puede probar con pytest sin levantar el servidor. FastAPI solo aparece en
`so_sim.app`, `so_sim.api` y `so_sim.manager`.
"""

__version__ = "1.0.0"
