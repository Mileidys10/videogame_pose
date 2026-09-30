@echo off
setlocal enabledelayedexpansion
title Instalador de Dependencias - VideoGame Pose Combat
echo ========================================================
echo    Instalando Dependencias de VideoGame Pose Combat
echo ========================================================
echo.
cd /d "%~dp0"

echo [1/3] Verificando instalacion de Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] No se encontro Python en tu sistema.
    echo Por favor descarga e instala Python 3.10 o superior desde https://www.python.org/
    echo Asegurate de marcar la casilla "Add python.exe to PATH" durante la instalacion.
    pause
    exit /b 1
)

echo [2/3] Creando entorno virtual local (.venv)...
if not exist ".venv" (
    python -m venv .venv
)
if exist ".venv\Scripts\pip.exe" (
    echo [OK] Entorno virtual activo.
    set "PIP_CMD=.venv\Scripts\pip.exe"
) else (
    echo [ALERTA] Usando instalador pip de Python global.
    set "PIP_CMD=python -m pip"
)

echo [3/3] Instalando librerias requeridas (pygame-ce, opencv, ultralytics, numpy)...
%PIP_CMD% install --upgrade pip
%PIP_CMD% install -r requirements.txt

echo.
echo ========================================================
echo    Instalacion completada con exito!
echo.
echo    Accesos directos listos:
echo    - INICIAR_HOST.bat       (Si tu creas la partida como P1)
echo    - INICIAR_CLIENTE.bat    (Si te unes al PC de un amigo como P2)
echo    - INICIAR_SOLO_VS_IA.bat (Para jugar solo contra la computadora)
echo ========================================================
pause
