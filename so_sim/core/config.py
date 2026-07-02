"""Configuracion del mundo (dataclasses) + constructor del World.

Mantiene FastAPI/Pydantic fuera del nucleo: aqui solo hay objetos Python puros.
"""
from dataclasses import dataclass, field
from typing import List

from .aleatorio import Generador
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
    tam_ejecutable: int = 100          # KB
    tam_datos: int = 0                 # KB
    tam_dinamica: int = 0              # KB
    modo_interrupciones: str = "declarativo"
    accesos: List[dict] = field(default_factory=list)   # [{en_cpu, va}] (PLUS: paginacion)
    io: List[dict] = field(default_factory=list)         # [{en_cpu, dispositivo, duracion}]


@dataclass
class DispositivoConfig:
    nombre: str
    tipo: str = TipoDispositivo.DISCO.value


def _dispositivos_por_defecto() -> List[DispositivoConfig]:
    # Los 5 dispositivos obligatorios del curso.
    return [
        DispositivoConfig("Teclado", TipoDispositivo.TECLADO.value),
        DispositivoConfig("Disco", TipoDispositivo.DISCO.value),
        DispositivoConfig("Impresora", TipoDispositivo.IMPRESORA.value),
        DispositivoConfig("Mouse", TipoDispositivo.MOUSE.value),
        DispositivoConfig("Red", TipoDispositivo.RED.value),
    ]


@dataclass
class MundoConfig:
    procesos: List[ProcesoConfig]
    # --- memoria FISICA (Modulo 2 obligatorio), todo en KB ---
    ram_total: int = 16384             # 16 MB
    ram_so: int = 2048                 # 2 MB reservados para el SO
    tam_bloque: int = 256              # tamano de bloque (potencia de 2, 32..2048 KB)
    estrategia_mem: str = "first_fit"
    # --- memoria VIRTUAL / paginacion (Modulo PLUS) ---
    paginacion_activa: bool = True
    num_marcos: int = 4
    offset_bits: int = 12
    replacer: str = "fifo"
    costo_fault: int = 0
    # --- planificacion / dispatcher ---
    scheduler: str = "fcfs"
    quantum: int = 3
    costo_cambio: int = 0              # costo del cambio de contexto (ticks)
    # --- E/S y aleatoriedad ---
    dispositivos: List[DispositivoConfig] = field(default_factory=_dispositivos_por_defecto)
    tasa_error: float = 0.0            # 0.005 = 0.5% (5 de cada 1000)
    seed: int = 12345
    descripcion: str = ""

    def to_dict(self) -> dict:
        """Serializa la config a la forma que entiende `from_dict` / el editor."""
        return {
            "descripcion": self.descripcion,
            "ram_total": self.ram_total, "ram_so": self.ram_so,
            "tam_bloque": self.tam_bloque, "estrategia_mem": self.estrategia_mem,
            "paginacion_activa": self.paginacion_activa,
            "num_marcos": self.num_marcos, "offset_bits": self.offset_bits,
            "replacer": self.replacer, "costo_fault": self.costo_fault,
            "scheduler": self.scheduler, "quantum": self.quantum,
            "costo_cambio": self.costo_cambio,
            "tasa_error": self.tasa_error, "seed": self.seed,
            "dispositivos": [{"nombre": d.nombre, "tipo": d.tipo} for d in self.dispositivos],
            "procesos": [{
                "pid": p.pid, "nombre": p.nombre, "llegada": p.llegada,
                "rafaga": p.rafaga, "prioridad": p.prioridad, "nivel_mlq": p.nivel_mlq,
                "tam_ejecutable": p.tam_ejecutable, "tam_datos": p.tam_datos,
                "tam_dinamica": p.tam_dinamica, "modo_interrupciones": p.modo_interrupciones,
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
        # --- memoria fisica ---
        if self.tam_bloque < 32 or self.tam_bloque > 2048:
            raise ValueError("El tamano de bloque debe estar entre 32 y 2048 KB.")
        if self.tam_bloque & (self.tam_bloque - 1) != 0:
            raise ValueError("El tamano de bloque debe ser potencia de 2.")
        if self.ram_so >= self.ram_total:
            raise ValueError("La RAM del SO debe ser menor que la RAM total.")
        ram_disponible = self.ram_total - self.ram_so
        for p in self.procesos:
            tam = p.tam_ejecutable + p.tam_datos + p.tam_dinamica
            if tam > ram_disponible:
                raise ValueError(
                    f"P{p.pid} necesita {tam} KB pero solo hay {ram_disponible} KB "
                    "disponibles para procesos.")
        # --- paginacion (PLUS) ---
        if self.num_marcos < 1:
            raise ValueError("Debe haber al menos 1 marco de memoria.")
        # --- planificacion ---
        if self.quantum < 1:
            raise ValueError("El quantum debe ser >= 1.")
        if not (0.0 <= self.tasa_error <= 1.0):
            raise ValueError("La tasa de error debe estar entre 0 y 1.")
        # --- procesos / E/S ---
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
            tam_ejecutable=int(p.get("tam_ejecutable", 100)),
            tam_datos=int(p.get("tam_datos", 0)),
            tam_dinamica=int(p.get("tam_dinamica", 0)),
            modo_interrupciones=str(p.get("modo_interrupciones", "declarativo")),
            accesos=list(p.get("accesos", [])),
            io=list(p.get("io", [])),
        ) for p in d["procesos"]]
        disp = d.get("dispositivos")
        dispositivos = ([DispositivoConfig(x["nombre"], x.get("tipo", "disco")) for x in disp]
                        if disp else _dispositivos_por_defecto())
        return MundoConfig(
            procesos=procesos,
            ram_total=int(d.get("ram_total", 16384)),
            ram_so=int(d.get("ram_so", 2048)),
            tam_bloque=int(d.get("tam_bloque", 256)),
            estrategia_mem=str(d.get("estrategia_mem", "first_fit")),
            paginacion_activa=bool(d.get("paginacion_activa", True)),
            num_marcos=int(d.get("num_marcos", 4)),
            offset_bits=int(d.get("offset_bits", 12)),
            replacer=str(d.get("replacer", "fifo")),
            costo_fault=int(d.get("costo_fault", 0)),
            scheduler=str(d.get("scheduler", "fcfs")),
            quantum=int(d.get("quantum", 3)),
            costo_cambio=int(d.get("costo_cambio", 0)),
            dispositivos=dispositivos,
            tasa_error=float(d.get("tasa_error", 0.0)),
            seed=int(d.get("seed", 12345)),
            descripcion=str(d.get("descripcion", "")),
        )


def construir_pcbs(cfg: MundoConfig) -> List[PCB]:
    gen = Generador(cfg.seed)
    nombres_disp = [d.nombre for d in cfg.dispositivos]
    pcbs = []
    for pc in cfg.procesos:
        plan_mem = [AccesoMem(en_cpu=int(a["en_cpu"]), va=int(a["va"])) for a in pc.accesos]
        plan_mem.sort(key=lambda a: a.en_cpu)
        # Modo de interrupciones: declarativo (usa pc.io) o aleatorio (se generan).
        io_src = pc.io
        if pc.modo_interrupciones == "aleatorio" and not pc.io:
            tam_total = pc.tam_ejecutable + pc.tam_datos + pc.tam_dinamica
            gen_p = Generador(cfg.seed + pc.pid)   # sub-semilla estable por proceso
            io_src = gen_p._io_aleatoria(pc.rafaga, tam_total, nombres_disp)
        plan_io = [PeticionIO(en_cpu=int(x["en_cpu"]), dispositivo=str(x["dispositivo"]),
                              duracion=int(x["duracion"])) for x in io_src]
        plan_io.sort(key=lambda x: x.en_cpu)
        pcbs.append(PCB(
            pid=pc.pid, nombre=pc.nombre, llegada=pc.llegada,
            rafaga_total=pc.rafaga, prioridad=pc.prioridad,
            nivel_mlq=pc.nivel_mlq, color=color_para(pc.pid),
            tam_ejecutable=pc.tam_ejecutable, tam_datos=pc.tam_datos,
            tam_dinamica=pc.tam_dinamica, modo_interrupciones=pc.modo_interrupciones,
            plan_mem=plan_mem, plan_io=plan_io,
        ))
    pcbs.sort(key=lambda p: (p.llegada, p.pid))
    return pcbs


def build_world_from_config(cfg: MundoConfig):
    from .world import World
    return World(cfg)
