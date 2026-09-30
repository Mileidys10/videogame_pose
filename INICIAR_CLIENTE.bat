@echo off
setlocal enabledelayedexpansion
title VideoGame Pose Combat - MODO CLIENTE (Jugador 2)
cd /d "%~dp0"

if exist ".venv\Scripts\python.exe" (
    set "PY_CMD=.venv\Scripts\python.exe"
) else if exist "C:\Users\POWER\Documents\GitHub\pose_active_break\.venv\Scripts\python.exe" (
    set "PY_CMD=C:\Users\POWER\Documents\GitHub\pose_active_break\.venv\Scripts\python.exe"
) else (
    set "PY_CMD=python"
)

echo ========================================================
echo    VIDEOGAME POSE COMBAT - MODO CLIENTE (JUGADOR 2)
echo ========================================================
echo.
set /p HOST_IP="Ingresa la direccion IP del PC Host (ej: 192.168.1.14 o 26.X.X.X): "
if "%HOST_IP%"=="" set HOST_IP=127.0.0.1

echo.
echo Conectando al Host en %HOST_IP%:9999...
echo.
%PY_CMD% main.py --mode client --host %HOST_IP% --port 9999 --backend yolo
if %errorlevel% neq 0 (
    echo.
    echo No se pudo iniciar con camara web. Probando simulador sintetico (teclado)...
    %PY_CMD% main.py --mode client --host %HOST_IP% --port 9999 --backend mock
)
pause
