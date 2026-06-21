@echo off
REM Atajo para Windows: crea el entorno, instala dependencias y lanza el servidor.
cd /d "%~dp0"

if not exist ".venv" (
  echo Creando entorno virtual...
  py -m venv .venv
)

echo Instalando dependencias...
".venv\Scripts\python.exe" -m pip install -r requirements.txt --quiet

echo.
echo Servidor en http://127.0.0.1:8000  (Ctrl+C para detener)
start "" http://127.0.0.1:8000
".venv\Scripts\python.exe" -m uvicorn so_sim.app:app
