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

## Estado del proyecto y cómo retomarlo

### Estado actual

El simulador está **funcional**: un núcleo en Python puro (sin dependencias de FastAPI) que integra tres subsistemas (planificación, memoria virtual con paginación y E/S) sobre un único reloj lógico, expuesto mediante una API FastAPI y una interfaz web en vivo vía Server-Sent Events (SSE).

Lo que ya está hecho y funcionando:

- **Núcleo del simulador completo**: `World` orquesta el `tick()` con fases en orden fijo; PCB con planes declarativos de memoria e I/O para garantizar reproducibilidad.
- **7 algoritmos de planificación**: FCFS, SJF, SRTF, Round Robin (quantum configurable), Prioridad no apropiativa, Prioridad apropiativa y MLQ (multinivel), bajo patrón Strategy.
- **Memoria virtual**: MMU con traducción VA→FA, page faults/hits y **4 algoritmos de reemplazo** (FIFO, LRU, Óptimo/Belady, Reloj), todos cambiables en caliente.
- **E/S por ticks** (sin hilos): cola FIFO por dispositivo, bloqueo/desbloqueo de procesos y 4 tipos predefinidos (disco, impresora, teclado, red), con simulación DMA determinista.
- **API FastAPI completa**: control (play/pause/step/reset/speed), configuración en caliente (scheduler/replacer), carga de escenarios y estado vía `GET /api/state` + `GET /api/stream` (SSE con fallback a polling).
- **5 escenarios predefinidos**: `basico`, `page_faults` (cadena clásica de Belady), `mlq`, `round_robin`, `io_overlap`.
- **Interfaz web** HTML+CSS+JS sin frameworks ni empaquetador: paneles de procesos, CPU, Gantt (canvas), memoria (marcos + tablas de páginas), dispositivos E/S, métricas (espera/retorno/respuesta) y bitácora de eventos, además de un editor interactivo de procesos.
- **Reproducibilidad total**: todas las corridas son 100% deterministas (misma configuración → misma traza).

**Pruebas: 17 tests en verde** (17 funciones de test en 4 archivos) que cubren scheduling, memoria, E/S y determinismo.

### Cómo retomar el trabajo

Desde una sesión nueva, en la carpeta del proyecto:

**Windows (PowerShell):**

```powershell
# 1. Crear y activar el entorno virtual
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Correr los tests (deben pasar los 17)
pip install pytest
python -m pytest

# 4. Levantar el servidor
python -m uvicorn so_sim.app:app
```

> Atajo en Windows: en lugar de los pasos manuales puedes ejecutar `run.bat` (doble clic o `run.bat` en PowerShell).

**Linux / macOS:**

```bash
# 1. Entorno virtual
python3 -m venv .venv
source .venv/bin/activate

# 2. Dependencias y tests
pip install -r requirements.txt
pip install pytest
python3 -m pytest

# 3. Servidor
python3 -m uvicorn so_sim.app:app
```

Por último, abrir el navegador en:

```
http://127.0.0.1:8000
```

### Mapa rápido del código

La estructura separa núcleo (Python puro, testeable), API delgada (FastAPI) y UI (vanilla JS):

- **`so_sim/core/world.py`** — `World`: el corazón del simulador. Su `tick()` ejecuta las fases en orden fijo: **admisión → planificar/apropiar → acceso_mem → ejecutar_ráfaga → fin_io → avanzar_dispositivos → contabilidad**. Empieza por aquí para entender el ciclo. El `costo_fault` (congelar CPU N ticks ante un fallo) está alrededor de `world.py:112`.
- **`so_sim/core/pcb.py`** — PCB y declarativas (`AccesoMem`, `PeticionIO`): los accesos a memoria y E/S se definen en `plan_mem` / `plan_io` y ocurren cuando `cpu_consumido` alcanza el valor declarado (esto es lo que hace todo reproducible, e incluso permite que Óptimo "vea el futuro").
- **Planificadores** — `so_sim/core/scheduler/`: clase base en `base.py`, una implementación por archivo (`fcfs.py`, `sjf.py`, `srtf.py`, `round_robin.py`, `priority.py`, `mlq.py`) y la fábrica `get_scheduler()` en `__init__.py`.
- **Memoria** — `so_sim/core/memory/`: `mmu.py` (traducción y manejo de fallos), `page_table.py` (VPN→marco, bits de validez/referencia/timestamps), `frames.py` (marcos físicos), `replacement.py` (FIFO/LRU/Óptimo/Reloj) con la fábrica `get_replacer()` en `__init__.py`.
- **E/S** — `so_sim/core/io/devices.py`: `Device` e `IoSubsystem`, modelado por ticks.
- **`so_sim/core/serialize.py`** — `to_dict()`: contrato único JSON con el frontend (procesos, memoria, I/O, Gantt, eventos, métricas). Serializa sin importar FastAPI.
- **`so_sim/manager.py`** — `SimulationManager`: gestiona el `World`, el bucle de reproducción (`asyncio.Lock`), genera snapshots y los publica a los suscriptores SSE.
- **`so_sim/app.py`** + **`so_sim/api/`** — capa FastAPI: `routes_control.py`, `routes_state.py`, `routes_config.py` y los modelos Pydantic en `schemas.py`.
- **Frontend** — `so_sim/static/`: `index.html`, `css/` y `js/` (lógica cliente con `fetch`/SSE). La validación vive en backend (`MundoConfig.validar()`) y cliente (`validarCliente()` en JS).
- **Tests** — `tests/`: `test_schedulers.py` (7), `test_memory.py` (3), `test_io.py` (3), `test_world_tick.py` (4); utilidades en `helpers.py`.

### Pendientes y posibles mejoras

- **Exponer `costo_fault` en el editor** (dificultad: **baja**) — ya existe en `config.py`/`world.py` pero `js/editor.js` lo fija a 0; falta añadir el campo en HTML y enviarlo en el POST.
- **Exponer el tipo de dispositivo en el editor** (dificultad: **baja**) — hoy se crea hardcodeado como `disco`; permitir elegir entre disco/impresora/teclado/red por dispositivo.
- **Duplicar proceso en el editor** (dificultad: **baja**) — copiar un proceso existente (PID+N, nombre, ráfaga, accesos, E/S) para crear variantes rápido.
- **Exportar/guardar escenarios a JSON** (dificultad: **baja**) — botón de descarga que serialice la configuración actual para compartir o archivar.
- **Validación avanzada en el editor** (dificultad: **baja**) — validar VPN antes de enviar (no cargar la misma página dos veces, avisar de accesos fuera del rango de `offset_bits`), sugerir nombres.
- **Paginación de la bitácora** (dificultad: **media**) — hoy `MAX_EVENTOS=14` solo muestra los últimos; añadir scroll/paginación para escenarios largos.
- **Métricas ampliadas** (dificultad: **media**) — añadir context switches, % de CPU idle y tabla por proceso (no solo promedios).
- **Más algoritmos** (dificultad: **media**) — Feedback (FB), AGING para prioridad, Clock-Pro para memoria; el patrón Strategy facilita la extensión.
- **Lazy allocation / swapping** (dificultad: **alta**) — cargar marcos solo al primer acceso, o swap a disco con penalización de acceso.
- **Comparativa visual entre algoritmos** (dificultad: **alta**) — correr el mismo escenario con distintos planificadores/reemplazos lado a lado y mostrar tabla comparativa.
```
