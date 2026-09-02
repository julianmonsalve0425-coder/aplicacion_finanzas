@echo off
title Finanzas - Servidor FastAPI
echo ===================================================
echo   Iniciando Finanzas - Servidor Backend FastAPI
echo ===================================================
echo.

if exist "venv\Scripts\python.exe" (
    echo [*] Usando entorno virtual del proyecto (venv)...
    set PYTHON_CMD=venv\Scripts\python.exe
) else (
    echo [*] Usando Python global del sistema...
    set PYTHON_CMD=python
)

cd "API Backend RESTful (FastAPI)"
echo [*] Arrancando Uvicorn en http://127.0.0.1:8000 ...
echo [*] Abre tu navegador en: http://127.0.0.1:8000
echo.
..\venv\Scripts\uvicorn.exe main:app --reload --host 127.0.0.1 --port 8000

pause
