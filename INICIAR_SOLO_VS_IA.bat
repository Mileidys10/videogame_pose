@echo off
setlocal
title VideoGame Pose Combat - 1 Jugador vs IA
cd /d "%~dp0"

if exist ".venv\Scripts\python.exe" (
    set "PY_CMD=.venv\Scripts\python.exe"
) else if exist "C:\Users\POWER\Documents\GitHub\pose_active_break\.venv\Scripts\python.exe" (
    set "PY_CMD=C:\Users\POWER\Documents\GitHub\pose_active_break\.venv\Scripts\python.exe"
) else (
    set "PY_CMD=python"
)

echo Iniciando combate individual contra la Inteligencia Artificial (Modo Dificil)...
%PY_CMD% main.py --mode single --difficulty hard --backend yolo
if %errorlevel% neq 0 (
    %PY_CMD% main.py --mode single --difficulty hard --backend mock
)
pause
