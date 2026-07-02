"""Generacion pseudoaleatoria REPRODUCIBLE (todo con una semilla fija).

Centraliza las formulas matematicas que exige el informe:

  * Cantidad de interrupciones de un proceso  (rango [5, 20]):
        N_int = 5 + ((burst + tam_KB // 128 + r) mod 16)      con r = rand(0,15)
  * Duracion de cada interrupcion (rango [5, 20]):
        Dur  = 5 + ((burst + r) mod 16)                        con r = rand(0,15)
  * Tasa de error (0.5% = 5 de cada 1000):
        el proceso aborta con error  <=>  rand_uniforme() < tasa_error   (0.005)
  * Generacion de parametros de un proceso aleatorio:
        burst in [3,15], tam_ejecutable in {64,128,256,512} KB, prioridad in [0,9]

Usar la misma semilla produce SIEMPRE la misma corrida (determinismo del motor).
"""
import random
from typing import Dict, List

TAM_DIVISOR = 128        # KB; escala del tamano en la formula de interrupciones


class Generador:
    def __init__(self, seed: int = 12345) -> None:
        self.seed = seed
        self.rng = random.Random(seed)

    def reset(self) -> None:
        self.rng = random.Random(self.seed)

    # --- formulas de interrupciones -----------------------------------------
    def cantidad_interrupciones(self, burst: int, tam_kb: int) -> int:
        r = self.rng.randint(0, 15)
        return 5 + ((burst + tam_kb // TAM_DIVISOR + r) % 16)

    def duracion_interrupcion(self, burst: int) -> int:
        r = self.rng.randint(0, 15)
        return 5 + ((burst + r) % 16)

    # --- tasa de error -------------------------------------------------------
    def marca_error(self, tasa: float) -> bool:
        return self.rng.random() < tasa

    def codigo_error(self) -> str:
        codigos = ["SIGSEGV (acceso invalido)", "DIV_ZERO (division por cero)",
                   "STACK_OVERFLOW", "SIGILL (instruccion ilegal)", "OOM (sin memoria)"]
        return self.rng.choice(codigos)

    # --- generacion de procesos aleatorios ----------------------------------
    def generar_procesos(self, n: int, dispositivos: List[str],
                         llegada_max: int = 8) -> List[Dict]:
        procesos = []
        tam_opciones = [64, 128, 256, 512]
        for i in range(n):
            pid = i + 1
            burst = self.rng.randint(3, 15)
            tam_ejec = self.rng.choice(tam_opciones)
            prioridad = self.rng.randint(0, 9)
            llegada = self.rng.randint(0, llegada_max)
            io = self._io_aleatoria(burst, tam_ejec, dispositivos)
            procesos.append({
                "pid": pid, "nombre": f"Proc-{pid}", "llegada": llegada,
                "rafaga": burst, "prioridad": prioridad,
                "tam_ejecutable": tam_ejec,
                "tam_datos": tam_ejec // 2, "tam_dinamica": tam_ejec // 4,
                "modo_interrupciones": "aleatorio", "io": io,
            })
        return procesos

    def _io_aleatoria(self, burst: int, tam_kb: int, dispositivos: List[str]) -> List[Dict]:
        """Genera peticiones de E/S para un proceso segun las formulas. Se limita
        a que las peticiones ocurran dentro de la rafaga del proceso."""
        if not dispositivos or burst < 2:
            return []
        # cantidad de interrupciones, acotada a lo que cabe en la rafaga
        cantidad = min(self.cantidad_interrupciones(burst, tam_kb), max(0, burst - 1))
        instantes = sorted(self.rng.sample(range(1, burst), min(cantidad, burst - 1))) \
            if burst > 1 else []
        io = []
        for en_cpu in instantes:
            io.append({
                "en_cpu": en_cpu,
                "dispositivo": self.rng.choice(dispositivos),
                "duracion": self.duracion_interrupcion(burst),
            })
        return io


def generar_io_para(pcb, dispositivos: List[str], gen: Generador) -> List[dict]:
    """Genera el plan de E/S aleatorio de un proceso ya construido (modo aleatorio)."""
    return gen._io_aleatoria(pcb.rafaga_total, pcb.tam_total, dispositivos)
