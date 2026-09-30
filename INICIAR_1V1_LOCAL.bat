@echo off
chcp 65001 > nul
title VideoGame Pose Combat - MODO 1V1 LOCAL (MISMA PANTALLA)

echo ======================================================================
echo    VIDEOGAME POSE COMBAT - MODO 1V1 LOCAL (2 JUGADORES EN 1 PC)
echo ======================================================================
echo.
echo Posicionamiento recomendado para jugar con CAMARA:
echo.
echo      [ JUGADOR 1 ]                     [ JUGADOR 2 ]
echo       (Izquierda)                       (Derecha)
echo          \                                 /
echo           \                               /
echo            ========= [ WEBCAM ] =========
echo.
echo * Distancia a la camara: 1.8 a 2.5 metros
echo * Ambos jugadores visibles de cintura hacia arriba
echo.
echo ======================================================================
echo Selecciona el modo de ejecucion:
echo ======================================================================
echo [1] 1v1 Local con Camara Web (Recomendado: YOLOv8 multi-persona)
echo [2] 1v1 Local con Camara Web (MediaPipe: Division espacial ROI)
echo [3] 1v1 Local con Simulador de Teclado (Sin camara / Pruebas)
echo [4] Salir
echo.

set /p opcion="Elige una opcion [1-4]: "

if "%opcion%"=="1" (
    echo.
    echo [*] Iniciando combate 1v1 Local con motor YOLOv8-Pose...
    python main.py --mode local --players 2 --backend yolo
    goto fin
)

if "%opcion%"=="2" (
    echo.
    echo [*] Iniciando combate 1v1 Local con motor MediaPipe...
    python main.py --mode local --players 2 --backend mediapipe
    goto fin
)

if "%opcion%"=="3" (
    echo.
    echo [*] Iniciando combate 1v1 Local con Simulador de Teclado en misma pantalla...
    echo.
    echo Controles P1 (Izquierda): 1=Kame, 2=Escudo, 3=Ki, 5=Golpe, 6=Upper, 7=Meme67, U=Hadoken, I=Genkidama, O=Dodge, P=Buff
    echo Controles P2 (Derecha):   8=Kame, 9=Escudo, 0=Ki, ==Golpe, [=Upper, ]=Meme67, J=Hadoken, K=Genkidama, L=Dodge, ;=Buff
    echo                           (Tambien puedes usar el Teclado Numerico: KP1 a KP9)
    echo.
    python main.py --mode local --players 2 --backend mock
    goto fin
)

:fin
pause
