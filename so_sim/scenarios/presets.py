"""Escenarios precargados (demos de un clic) en espanol.

Cada preset es un dict que `MundoConfig.from_dict` sabe leer. Las direcciones
virtuales usan va = vpn << 12 (offset_bits=12), asi VPN = va >> 12.
"""
from ..core.config import MundoConfig


def _va(vpn: int) -> int:
    return vpn << 12


# --- 1) Mezcla basica de procesos con algo de memoria y E/S ------------------
BASICO = {
    "descripcion": "Mezcla basica: 3 procesos con accesos a memoria y una E/S. Ideal para empezar.",
    "scheduler": "fcfs", "replacer": "fifo", "num_marcos": 4, "quantum": 3,
    "procesos": [
        {"pid": 1, "nombre": "Editor", "llegada": 0, "rafaga": 6, "prioridad": 2,
         "accesos": [{"en_cpu": 0, "va": _va(0)}, {"en_cpu": 1, "va": _va(1)},
                     {"en_cpu": 4, "va": _va(2)}],
         "io": [{"en_cpu": 3, "dispositivo": "Disco", "duracion": 3}]},
        {"pid": 2, "nombre": "Compilador", "llegada": 1, "rafaga": 4, "prioridad": 1,
         "accesos": [{"en_cpu": 0, "va": _va(0)}, {"en_cpu": 2, "va": _va(3)}]},
        {"pid": 3, "nombre": "Navegador", "llegada": 2, "rafaga": 5, "prioridad": 3,
         "accesos": [{"en_cpu": 0, "va": _va(4)}, {"en_cpu": 1, "va": _va(1)}],
         "io": [{"en_cpu": 2, "dispositivo": "Impresora", "duracion": 2}]},
    ],
}

# --- 2) Cadena de referencia clasica para demostrar page faults --------------
# Cadena clasica de Belady: 7 0 1 2 0 3 0 4 2 3 0 3 2 con 3 marcos.
_CADENA = [7, 0, 1, 2, 0, 3, 0, 4, 2, 3, 0, 3, 2]
PAGE_FAULTS = {
    "descripcion": ("Un proceso con la cadena de referencia clasica (7 0 1 2 0 3 0 4 2 3 0 3 2) "
                    "y solo 3 marcos. Cambia el algoritmo de reemplazo y compara los fallos."),
    "scheduler": "fcfs", "replacer": "fifo", "num_marcos": 3, "quantum": 3,
    "procesos": [
        {"pid": 1, "nombre": "Demo-Paginas", "llegada": 0, "rafaga": len(_CADENA),
         "accesos": [{"en_cpu": i, "va": _va(vpn)} for i, vpn in enumerate(_CADENA)]},
    ],
}

# --- 3) MLQ: dos procesos de alta (RR) y uno de baja (FCFS) ------------------
MLQ_DEMO = {
    "descripcion": "MLQ: 2 procesos de ALTA prioridad (Round Robin) y 1 de BAJA (FCFS).",
    "scheduler": "mlq", "replacer": "fifo", "num_marcos": 4, "quantum": 2,
    "procesos": [
        {"pid": 1, "nombre": "Sistema-A", "llegada": 0, "rafaga": 4, "nivel_mlq": "ALTA"},
        {"pid": 2, "nombre": "Sistema-B", "llegada": 0, "rafaga": 4, "nivel_mlq": "ALTA"},
        {"pid": 3, "nombre": "Lote", "llegada": 0, "rafaga": 6, "nivel_mlq": "BAJA"},
    ],
}

# --- 4) Round Robin con quantum ----------------------------------------------
ROUND_ROBIN = {
    "descripcion": "Round Robin con quantum=2: observa el reparto por turnos en el Gantt.",
    "scheduler": "rr", "replacer": "fifo", "num_marcos": 4, "quantum": 2,
    "procesos": [
        {"pid": 1, "nombre": "T1", "llegada": 0, "rafaga": 5},
        {"pid": 2, "nombre": "T2", "llegada": 0, "rafaga": 3},
        {"pid": 3, "nombre": "T3", "llegada": 1, "rafaga": 6},
    ],
}

# --- 5) Solapamiento CPU / E-S (modelo DMA) ----------------------------------
IO_OVERLAP = {
    "descripcion": ("Solapamiento CPU/E-S: P1 se bloquea en una E/S larga y la CPU "
                    "sigue trabajando con P2 mientras tanto (modelo DMA)."),
    "scheduler": "fcfs", "replacer": "fifo", "num_marcos": 4, "quantum": 3,
    "procesos": [
        {"pid": 1, "nombre": "LeeDisco", "llegada": 0, "rafaga": 6,
         "io": [{"en_cpu": 2, "dispositivo": "Disco", "duracion": 4}]},
        {"pid": 2, "nombre": "Calcula", "llegada": 1, "rafaga": 4},
    ],
}

PRESETS = {
    "basico": BASICO,
    "page_faults": PAGE_FAULTS,
    "mlq": MLQ_DEMO,
    "round_robin": ROUND_ROBIN,
    "io_overlap": IO_OVERLAP,
}

PRESET_DEFECTO = "basico"


def listar() -> list:
    return [{"nombre": k, "descripcion": v["descripcion"]} for k, v in PRESETS.items()]


def cargar(nombre: str) -> MundoConfig:
    if nombre not in PRESETS:
        raise KeyError(f"Preset desconocido: {nombre}")
    return MundoConfig.from_dict(PRESETS[nombre])


def config_por_defecto() -> MundoConfig:
    return cargar(PRESET_DEFECTO)
