# Simulador de Sistema Operativo

Simulador interactivo, con interfaz web, de los tres mecanismos centrales de un
sistema operativo trabajando de forma integrada sobre un mismo reloj lógico:

- **Planificación de procesos** — estados del PCB y siete algoritmos de CPU.
- **Memoria virtual / paginación** — tabla de páginas por proceso, marcos físicos
  limitados, traducción de dirección virtual a física, fallos de página y cuatro
  algoritmos de reemplazo.
- **Dispositivos de E/S** — bloquean y desbloquean procesos liberando la CPU.

El mundo avanza por *ticks* y puede ejecutarse paso a paso o en modo automático
(reproducir / pausar / velocidad), con todo actualizándose en vivo: tabla de
procesos, diagrama de Gantt, marcos de memoria, colas de dispositivos, métricas y
una bitácora de eventos.

La lógica del simulador (`so_sim/core/`) está escrita en Python puro, sin
dependencias del servidor, de modo que puede probarse de forma aislada. Encima va
una capa delgada con **FastAPI** que la expone por HTTP, y un frontend de
**HTML + CSS + JavaScript** servido tal cual, sin ningún paso de compilación.

---

## Requisitos

- Python 3.10 o superior.
- No usa Node, ni base de datos, ni compilación de assets.

## Cómo ejecutarlo

**Atajo (Windows):** doble clic en `run.bat`. Crea el entorno virtual, instala las
dependencias, abre el navegador y arranca el servidor.

**A mano**, desde la carpeta del proyecto:

```bash
python -m venv .venv
# Windows:  .\.venv\Scripts\activate
# Linux/Mac: source .venv/bin/activate
pip install -r requirements.txt
python -m uvicorn so_sim.app:app
```

Luego abrir `http://127.0.0.1:8000`.

## Uso de la interfaz

La barra superior controla la simulación:

- **Reproducir / Pausa / Paso / Reiniciar** y un **deslizador de velocidad**.
- **Planificador** y **Reemplazo**: se pueden cambiar *en caliente*; el cambio se
  aplica en el siguiente tick sin perder el estado. El campo **Quantum** solo
  aparece para Round Robin y MLQ.
- **Escenario**: carga ejemplos predefinidos de un clic.
- **Crear / editar procesos**: abre un editor donde se definen procesos a mano
  (ver más abajo).

Los paneles muestran: procesos (PCB) y colas, la CPU actual, el diagrama de Gantt,
la memoria (marcos, contadores de aciertos/fallos, último acceso traducido y
tablas de páginas), los dispositivos de E/S, las métricas y la bitácora.

### Crear y editar procesos

El botón **Crear / editar procesos** abre un formulario que parte del escenario
actual. Por cada proceso se define PID, nombre, instante de llegada, ráfaga de
CPU, prioridad y nivel (alta/baja, para MLQ). Además, por proceso se pueden añadir:

- **Accesos a memoria**: a qué *página (VPN)* accede el proceso cuando lleva *N*
  unidades de CPU consumidas.
- **Peticiones de E/S**: en qué instante de CPU se bloquea, en qué dispositivo y
  por cuántos ticks.

También se ajustan los parámetros globales (planificador, quantum, reemplazo,
número de marcos, bits de offset y lista de dispositivos). Al confirmar, el
escenario se valida y se carga.

### Escenarios predefinidos

| Escenario | Qué muestra |
|---|---|
| `basico` | Tres procesos con accesos a memoria y una E/S. Punto de partida. |
| `page_faults` | Cadena de referencia clásica `7 0 1 2 0 3 0 4 2 3 0 3 2` con 3 marcos: cambia el reemplazo y compara los fallos. |
| `mlq` | Dos procesos de alta prioridad (Round Robin) y uno de baja (FCFS). |
| `round_robin` | Reparto por turnos (quantum = 2) visible en el Gantt. |
| `io_overlap` | La CPU sigue trabajando con otro proceso mientras uno está bloqueado en E/S. |

## Algoritmos

- **Planificación de CPU:** FCFS, SJF, SRTF (apropiativo), Round Robin (con
  quantum), Prioridad (apropiativa y no apropiativa) y MLQ (multinivel: cola alta
  por Round Robin, cola baja por FCFS, con prioridad estricta entre niveles).
- **Reemplazo de páginas:** FIFO, LRU, Óptimo (usa la traza de accesos declarada
  para mirar el futuro) y Segunda Oportunidad / Reloj (bit de referencia con
  puntero circular).

## Estructura del proyecto

```
so_sim/
  app.py            FastAPI: sirve estáticos, la página y registra las rutas.
  manager.py        Gestiona el mundo, el bucle de reproducción (asyncio) y el stream a la UI.
  api/              Rutas: control, estado (con stream), configuración; y los esquemas de validación.
  core/             Lógica pura del simulador (sin FastAPI):
    world.py        tick(): orquesta los tres subsistemas en un orden de fases fijo.
    pcb.py  config.py  enums.py  events.py  metrics.py  serialize.py
    scheduler/      Los siete planificadores + una fábrica.
    memory/         MMU, tabla de páginas, marcos y algoritmos de reemplazo.
    io/             Dispositivos de E/S (cola + servicio por ticks).
  scenarios/        Escenarios predefinidos.
  static/           index.html + css + js (módulos nativos, sin empaquetador).
tests/              Pruebas del núcleo con casos conocidos y de determinismo.
```

### Cómo avanza un tick

Cada `tick` ejecuta siempre el mismo orden de fases y suma uno al reloj:

```
admisión → planificar/apropiar → acceso a memoria → ejecutar ráfaga
        → fin de ráfaga o E/S → avanzar dispositivos → contabilidad
```

Los accesos a memoria y las peticiones de E/S se declaran en función de la CPU ya
consumida por cada proceso, no del reloj global. Gracias a esto, una misma
configuración produce siempre la misma traza (y el algoritmo Óptimo puede conocer
los accesos futuros).

## Comunicación en tiempo real

El servidor conduce el reloj y empuja el estado del mundo a la interfaz mediante
**Server-Sent Events**; los comandos van por POST. Si el stream se bloquea (por
ejemplo, detrás de un proxy o antivirus), el cliente recurre a consultar el estado
por *polling* de forma automática.

## Pruebas

```bash
pip install pytest
python -m pytest
```

Cubren cada planificador con casos verificables a mano, la traducción de
direcciones, los cuatro algoritmos de reemplazo sobre la cadena clásica, el
bloqueo y desbloqueo por E/S, y el determinismo del motor.

## Notas de diseño

- El núcleo no importa FastAPI, por lo que es testeable y se puede modificar sin
  tocar la interfaz.
- La E/S se modela por conteo de ticks (no por hilos reales): conserva el
  comportamiento asíncrono sin condiciones de carrera y mantiene el estado
  reproducible y serializable.
- Planificadores y reemplazos siguen el patrón Strategy con una fábrica, y se
  intercambian entre ticks bajo un único candado, sin tocar los PCB ni las tablas.
```
