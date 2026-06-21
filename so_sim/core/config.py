"""Configuracion del mundo (dataclasses) + constructor del World.

Mantiene FastAPI/Pydantic fuera del nucleo: aqui solo hay objetos Python puros.
"""
from dataclasses import dataclass, field
from typing import List

from .enums import TipoDispositivo
from .pcb import PCB, AccesoMem, PeticionIO


def color_para(pid: int) -> str:
    """Color HSL estable y distinguible por pid (angulo aureo)."""
    return f"hsl({(pid * 137 + 40) % 360}, 65%, 55%)"


@dataclass
class ProcesoConfig:
    pid: int
    nombre: str
    llegada: int
    rafaga: int
    prioridad: int = 0
    nivel_mlq: str = "ALTA"
    accesos: List[dict] = field(default_factory=list)   # [{en_cpu, va}]
    io: List[dict] = field(default_factory=list)         # [{en_cpu, dispositivo, duracion}]


@dataclass
class DispositivoConfig:
    nombre: str
    tipo: str = TipoDispositivo.DISCO.value


def _dispositivos_por_defecto() -> List[DispositivoConfig]:
    return [
        DispositivoConfig("Disco", TipoDispositivo.DISCO.value),
        DispositivoConfig("Impresora", TipoDispositivo.IMPRESORA.value),
    ]


@dataclass
class MundoConfig:
    procesos: List[ProcesoConfig]
    num_marcos: int = 4
    offset_bits: int = 12
    dispositivos: List[DispositivoConfig] = field(default_factory=_dispositivos_por_defecto)
    scheduler: str = "fcfs"
    quantum: int = 3
    replacer: str = "fifo"
    costo_fault: int = 0
    descripcion: str = ""

    def to_dict(self) -> dict:
        """Serializa la config a la forma que entiende `from_dict` / el editor."""
        return {
            "descripcion": self.descripcion,
            "scheduler": self.scheduler, "quantum": self.quantum,
            "replacer": self.replacer, "num_marcos": self.num_marcos,
            "offset_bits": self.offset_bits, "costo_fault": self.costo_fault,
            "dispositivos": [{"nombre": d.nombre, "tipo": d.tipo} for d in self.dispositivos],
            "procesos": [{
                "pid": p.pid, "nombre": p.nombre, "llegada": p.llegada,
                "rafaga": p.rafaga, "prioridad": p.prioridad, "nivel_mlq": p.nivel_mlq,
                "accesos": list(p.accesos), "io": list(p.io),
            } for p in self.procesos],
        }

    def validar(self) -> None:
        """Valida la coherencia del escenario; lanza ValueError con mensaje en
        espanol si algo esta mal (para devolver un 400 claro al frontend)."""
        if not self.procesos:
            raise ValueError("El escenario no tiene procesos.")
        pids = [p.pid for p in self.procesos]
        if len(pids) != len(set(pids)):
            raise ValueError("Hay PIDs repetidos entre los procesos.")
        if self.num_marcos < 1:
            raise ValueError("Debe haber al menos 1 marco de memoria.")
        nombres_disp = {d.nombre for d in self.dispositivos}
        for p in self.procesos:
            if p.rafaga < 1:
                raise ValueError(f"P{p.pid}: la rafaga debe ser >= 1.")
            for x in p.io:
                if x["dispositivo"] not in nombres_disp:
                    raise ValueError(
                        f"P{p.pid} pide E/S en '{x['dispositivo']}', que no existe.")

    @staticmethod
    def from_dict(d: dict) -> "MundoConfig":
        procesos = [ProcesoConfig(
            pid=int(p["pid"]),
            nombre=str(p.get("nombre") or f"P{p['pid']}"),
            llegada=int(p.get("llegada", 0)),
            rafaga=int(p["rafaga"]),
            prioridad=int(p.get("prioridad", 0)),
            nivel_mlq=str(p.get("nivel_mlq", "ALTA")).upper(),
            accesos=list(p.get("accesos", [])),
            io=list(p.get("io", [])),
        ) for p in d["procesos"]]
        disp = d.get("dispositivos")
        dispositivos = ([DispositivoConfig(x["nombre"], x.get("tipo", "disco")) for x in disp]
                        if disp else _dispositivos_por_defecto())
        return MundoConfig(
            procesos=procesos,
            num_marcos=int(d.get("num_marcos", 4)),
            offset_bits=int(d.get("offset_bits", 12)),
            dispositivos=dispositivos,
            scheduler=str(d.get("scheduler", "fcfs")),
            quantum=int(d.get("quantum", 3)),
            replacer=str(d.get("replacer", "fifo")),
            costo_fault=int(d.get("costo_fault", 0)),
            descripcion=str(d.get("descripcion", "")),
        )


def construir_pcbs(cfg: MundoConfig) -> List[PCB]:
    pcbs = []
    for pc in cfg.procesos:
        plan_mem = [AccesoMem(en_cpu=int(a["en_cpu"]), va=int(a["va"])) for a in pc.accesos]
        plan_mem.sort(key=lambda a: a.en_cpu)
        plan_io = [PeticionIO(en_cpu=int(x["en_cpu"]), dispositivo=str(x["dispositivo"]),
                              duracion=int(x["duracion"])) for x in pc.io]
        plan_io.sort(key=lambda x: x.en_cpu)
        pcbs.append(PCB(
            pid=pc.pid, nombre=pc.nombre, llegada=pc.llegada,
            rafaga_total=pc.rafaga, prioridad=pc.prioridad,
            nivel_mlq=pc.nivel_mlq, color=color_para(pc.pid),
            plan_mem=plan_mem, plan_io=plan_io,
        ))
    pcbs.sort(key=lambda p: (p.llegada, p.pid))
    return pcbs


def build_world_from_config(cfg: MundoConfig):
    from .world import World
    return World(cfg)
