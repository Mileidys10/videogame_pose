@echo off
setlocal enabledelayedexpansion
title VideoGame Pose Combat - MODO HOST (Servidor LAN P1)
cd /d "%~dp0"

if exist ".venv\Scripts\python.exe" (
    set "PY_CMD=.venv\Scripts\python.exe"
) else if exist "C:\Users\POWER\Documents\GitHub\pose_active_break\.venv\Scripts\python.exe" (
    set "PY_CMD=C:\Users\POWER\Documents\GitHub\pose_active_break\.venv\Scripts\python.exe"
) else (
    set "PY_CMD=python"
)

echo ========================================================
echo    VIDEOGAME POSE COMBAT - MODO HOST (SERVIDOR P1)
echo ========================================================
echo.
echo Tus direcciones IP detectadas para compartir con tu amigo:
echo.
powershell -Command "Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.InterfaceAlias -notlike '*Loopback*' -and $_.IPAddress -notlike '169.254*' } | ForEach-Object { Write-Host '  --> ' $_.IPAddress '  (Interfaz: ' $_.InterfaceAlias ')' -ForegroundColor Green }"
echo.
echo --------------------------------------------------------
echo INSTRUCCIONES:
echo 1. Dile a tu amigo que ejecute INICIAR_CLIENTE.bat en su PC.
echo 2. Pidele que ingrese tu direccion IP (ejemplo: 192.168.X.X o Radmin VPN).
echo 3. Puerto UDP de comunicacion: 9999
echo --------------------------------------------------------
echo.
echo Iniciando servidor y conectando camara web...
echo.
%PY_CMD% main.py --mode host --port 9999 --backend yolo
if %errorlevel% neq 0 (
    echo.
    echo No se pudo iniciar con camara web. Probando simulador sintetico (teclado)...
    %PY_CMD% main.py --mode host --port 9999 --backend mock
)
pause
