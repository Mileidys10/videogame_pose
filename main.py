"""Punto de entrada principal para el videojuego VideoGame Pose Combat."""

import argparse
import sys
import time
from typing import Dict, Optional
import cv2
import numpy as np
import pygame

from src.audio.sound_engine import SoundEngine
from src.game.combat import CombatEngine
from src.ai.simple_ai import FighterAI
from src.gestures.recognizer import CombatGesture, GestureRecognizer
from src.network.client import GameClient
from src.network.server import GameServer
from src.ui.renderer import PygameRenderer
from src.vision.backend import PoseEstimationBackend, PosePlayer
from src.vision.mediapipe_adapter import MediaPipePoseBackend
from src.vision.smoother import KeypointSmoother
from src.vision.synthetic_adapter import SyntheticPoseBackend
from src.vision.threaded_backend import ThreadedPoseBackend
from src.vision.yolo_adapter import YOLOv8PoseBackend


def parse_arguments() -> argparse.Namespace:
    """Configura y analiza los argumentos de linea de comandos."""
    parser = argparse.ArgumentParser(
        description="VideoGame Pose Combat: Combate de poses corporales para 2 a 4 jugadores."
    )
    parser.add_argument(
        "--mode",
        choices=["local", "host", "client", "single"],
        default="local",
        help="Modo de operacion: 'local' (2P local), 'host' (servidor LAN P1), 'client' (cliente LAN P2), 'single' (1P vs IA).",
    )
    parser.add_argument(
        "--difficulty",
        choices=["easy", "normal", "hard"],
        default="normal",
        help="Nivel de dificultad de la IA en modo 'single' (easy, normal, hard).",
    )
    parser.add_argument(
        "--host",
        type=str,
        default="127.0.0.1",
        help="Direccion IP del host para conectarse en modo client (default: 127.0.0.1).",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=9999,
        help="Puerto UDP para comunicacion LAN (default: 9999).",
    )
    parser.add_argument(
        "--backend",
        choices=["yolo", "mediapipe", "mock"],
        default="yolo",
        help="Motor de estimacion de posturas a utilizar (yolo, mediapipe, mock).",
    )
    parser.add_argument(
        "--camera",
        type=int,
        default=0,
        help="Indice del dispositivo de captura de video (default: 0).",
    )
    parser.add_argument(
        "--players",
        type=int,
        default=2,
        choices=[2, 3, 4],
        help="Cantidad de combatientes simultaneos (2 a 4).",
    )
    parser.add_argument(
        "--width",
        type=int,
        default=1280,
        help="Ancho del lienzo de la ventana (default: 1280).",
    )
    parser.add_argument(
        "--height",
        type=int,
        default=720,
        help="Alto del lienzo de la ventana (default: 720).",
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Ejecuta en modo sin pantalla para pruebas automatizadas.",
    )
    parser.add_argument(
        "--no-sound",
        action="store_true",
        help="Desactiva los efectos de audio sintetizados.",
    )
    parser.add_argument(
        "--threaded-vision",
        action="store_true",
        help="Ejecuta la inferencia de vision en hilo desacoplado para garantizar 60 FPS fijos.",
    )
    parser.add_argument(
        "--no-smooth",
        action="store_true",
        help="Desactiva el filtro de suavizado temporal Lerp en los keypoints.",
    )
    parser.add_argument(
        "--demo-seconds",
        type=float,
        default=0.0,
        help="Duracion maxima en segundos para ejecucion de prueba (0 = infinito).",
    )
    return parser.parse_args()


def initialize_backend(name: str, num_players: int) -> PoseEstimationBackend:
    """Fabrica e inicializa el backend de vision seleccionado."""
    if name == "yolo":
        print("[INFO] Inicializando backend Ultralytics YOLOv8-Pose...")
        return YOLOv8PoseBackend(model_path="yolov8n-pose.pt", min_confidence=0.35)
    elif name == "mediapipe":
        print("[INFO] Inicializando backend Google MediaPipe Tasks...")
        return MediaPipePoseBackend(num_players=num_players, min_confidence=0.35)
    elif name == "mock":
        print("[INFO] Inicializando backend sintetico determinista...")
        return SyntheticPoseBackend(num_players=num_players)
    else:
        raise ValueError(f"Backend no reconocido: {name}")


def main() -> int:
    """Bucle principal de orquestacion del videojuego."""
    args = parse_arguments()

    # 1. Inicializar Motor de Audio Procedimental
    sound_engine = SoundEngine(enabled=(not args.headless and not args.no_sound))

    # 2. Inicializar Componentes de Red (Host o Client)
    server: Optional[GameServer] = None
    client: Optional[GameClient] = None
    assigned_player_id: int = 1

    if args.mode == "host":
        print(f"[NETWORK] Iniciando en Modo HOST (Servidor LAN en puerto {args.port})...")
        server = GameServer(host="0.0.0.0", port=args.port)
        server.start()
        assigned_player_id = 1
    elif args.mode == "client":
        print(f"[NETWORK] Iniciando en Modo CLIENT (Conectando a {args.host}:{args.port})...")
        client = GameClient(host=args.host, port=args.port)
        client.start(timeout=2.0)
        assigned_player_id = client.assigned_player_id if client.assigned_player_id is not None else 2

    # En modo host o client, la camara local solo necesita detectar a 1 jugador
    detection_players = 1 if args.mode in ("host", "client", "single") else args.players

    # 3. Inicializar Backend de Vision
    try:
        raw_backend = initialize_backend(args.backend, detection_players)
    except Exception as e:
        print(f"[ALERTA] Error al iniciar backend {args.backend}: {e}")
        print("[INFO] Activando respaldo con backend sintetico (mock)...")
        raw_backend = SyntheticPoseBackend(num_players=detection_players)
        args.backend = "mock"

    if args.threaded_vision:
        print("[INFO] Activando inferencia de vision desacoplada (ThreadedPoseBackend).")
        backend: PoseEstimationBackend = ThreadedPoseBackend(raw_backend)
    else:
        backend = raw_backend

    smoother: Optional[KeypointSmoother] = None if args.no_smooth else KeypointSmoother(alpha=0.65)

    # 4. Inicializar Camara si no es mock
    cap: Optional[cv2.VideoCapture] = None
    if args.backend != "mock":
        cap = cv2.VideoCapture(args.camera)
        if not cap.isOpened():
            print(f"[ALERTA] No se pudo abrir la camara {args.camera}. Cambiando a modo de simulacion sintetica.")
            backend.close()
            backend = SyntheticPoseBackend(num_players=detection_players)
            args.backend = "mock"
            cap = None
        else:
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    # 5. Inicializar Componentes de Combate y UI
    engine = CombatEngine(num_players=args.players, sound_engine=sound_engine)
    ai_opponent: Optional[FighterAI] = None
    if args.mode == "single":
        print(f"[AI] Iniciando Inteligencia Artificial como Jugador 2 (Dificultad: {args.difficulty.upper()})...")
        ai_opponent = FighterAI(player_id=2, difficulty=args.difficulty)
    recognizer = GestureRecognizer(debounce_frames=3)
    renderer = PygameRenderer(
        width=args.width,
        height=args.height,
        headless=args.headless,
        title=f"VideoGame Pose Combat [{args.mode.upper()}] ({args.backend.upper()})",
    )

    print("\n========================================================")
    print(f" VideoGame Pose Combat - Motor Iniciado [{args.mode.upper()}]")
    print(f" - Modo: {args.mode.upper()} | Backend: {args.backend.upper()}")
    print(f" - Jugador Local Asignado: P{assigned_player_id}")
    print(f" - Audio Procedimental: {'ACTIVO' if sound_engine.enabled else 'DESACTIVADO'}")
    print(f" - Suavizado Lerp: {'ACTIVO' if smoother is not None else 'DESACTIVADO'}")
    print(f" - Inferencia en Hilo: {'ACTIVA' if args.threaded_vision else 'SINCRONA'}")
    print(" - Controles de teclado:")
    print("   * 'H' o 'TAB': Abrir/cerrar Guia de Movimientos en pantalla")
    print("   * 'R': Reiniciar combate / nueva partida")
    print("   * 'Q' o 'ESC': Salir del juego")
    print("   * Manual completo disponible en: docs/GUIA_DE_MOVIMIENTOS.md")
    if args.backend == "mock":
        print("   * Simulador: '1' Kamehameha | '2' Escudo | '3' Carga Ki | '4' Idle | '5' Melee")
    print("========================================================\n")

    last_time = time.time()
    start_time = time.time()
    running = True

    try:
        while running:
            current_time = time.time()
            dt = max(0.001, min(0.1, current_time - last_time))
            last_time = current_time

            if args.demo_seconds > 0.0 and (current_time - start_time) >= args.demo_seconds:
                print(f"[INFO] Tiempo de prueba ({args.demo_seconds}s) alcanzado. Finalizando bucle limpiamente.")
                break

            # 1. Gestion de Eventos de Ventana y Teclado
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_ESCAPE, pygame.K_q):
                        running = False
                    elif event.key == pygame.K_r:
                        if args.mode != "client":
                            engine.reset_match()
                    elif event.key in (pygame.K_h, pygame.K_TAB):
                        renderer.show_guide = not renderer.show_guide

                    # Controles de simulacion en tiempo real para modo mock
                    elif isinstance(raw_backend, SyntheticPoseBackend):
                        target_p = assigned_player_id if args.mode in ("host", "client") else 1
                        if event.key == pygame.K_1:
                            raw_backend.set_player_pose(target_p, "KAMEHAMEHA")
                        elif event.key == pygame.K_2:
                            raw_backend.set_player_pose(target_p, "SHIELD")
                        elif event.key == pygame.K_3:
                            raw_backend.set_player_pose(target_p, "CHARGE_KI")
                        elif event.key == pygame.K_4:
                            raw_backend.set_player_pose(target_p, "IDLE")
                        elif event.key == pygame.K_5:
                            raw_backend.set_player_pose(target_p, "PUNCH")
                        elif event.key == pygame.K_6:
                            raw_backend.set_player_pose(target_p, "UPPERCUT")
                        elif event.key == pygame.K_7:
                            raw_backend.set_player_pose(target_p, "SIXTY_SEVEN")
                        elif event.key == pygame.K_u:
                            raw_backend.set_player_pose(target_p, "HADOKEN")
                        elif event.key == pygame.K_i:
                            raw_backend.set_player_pose(target_p, "SPIRIT_BOMB")
                        elif event.key == pygame.K_o:
                            raw_backend.set_player_pose(target_p, "DODGE_ROLL")
                        elif event.key == pygame.K_p:
                            raw_backend.set_player_pose(target_p, "TAUNT_CROSS")

                        # En modo local 2 jugadores, los numeros 8, 9, 0, -, = controlan P2
                        if args.mode == "local" and args.players >= 2:
                            if event.key == pygame.K_8:
                                raw_backend.set_player_pose(2, "KAMEHAMEHA")
                            elif event.key == pygame.K_9:
                                raw_backend.set_player_pose(2, "SHIELD")
                            elif event.key == pygame.K_0:
                                raw_backend.set_player_pose(2, "CHARGE_KI")
                            elif event.key == pygame.K_MINUS:
                                raw_backend.set_player_pose(2, "IDLE")
                            elif event.key == pygame.K_EQUALS:
                                raw_backend.set_player_pose(2, "PUNCH")

            # 2. Captura de Fotograma Local
            frame: Optional[np.ndarray] = None
            if cap is not None and cap.isOpened():
                ret, raw_frame = cap.read()
                if ret and raw_frame is not None:
                    frame = raw_frame

            # 3. Inferencia de Posturas Local
            detected_players = backend.process_frame(frame)
            if smoother is not None:
                detected_players = smoother.smooth(detected_players)

            # Reasignar player_id si estamos en modo host/client
            if args.mode in ("host", "client") and detected_players:
                detected_players[0].player_id = assigned_player_id

            poses_by_id: Dict[int, PosePlayer] = {p.player_id: p for p in detected_players}

            # 4. Clasificacion de Gestos Locales
            current_gestures: Dict[int, CombatGesture] = {}
            for p in detected_players:
                gesture = recognizer.update_and_get_gesture(p)
                current_gestures[p.player_id] = gesture

            # 5. Gestion de Red segun Modo
            if args.mode == "host" and server is not None:
                # Recoger inputs remotos de P2
                remote_input = server.get_remote_input(player_id=2)
                if remote_input:
                    try:
                        current_gestures[2] = CombatGesture(remote_input.gesture)
                    except Exception:
                        current_gestures[2] = CombatGesture.IDLE

                # Actualizar motor fisico de combate
                engine.update_gestures(current_gestures, poses_by_id)
                engine.update_physics(dt)

                # Broadcast autoritativo del estado a clientes
                server.broadcast_state(engine.to_game_state_packet())

            elif args.mode == "client" and client is not None:
                # Enviar input local de P2 al Host
                local_gesture = current_gestures.get(assigned_player_id, CombatGesture.IDLE)
                client.send_input(gesture=local_gesture.value)

                # Recibir y aplicar el estado autoritativo del Host
                remote_state = client.get_latest_state()
                if remote_state:
                    engine.apply_game_state_packet(remote_state)

            else:
                # Modo Local / Single Player
                if ai_opponent is not None:
                    current_gestures[2] = ai_opponent.update(dt, engine)

                engine.update_gestures(current_gestures, poses_by_id)
                engine.update_physics(dt)

            # 6. Renderizado de Graficos
            fps = 1.0 / dt if dt > 0 else 60.0
            renderer.render_frame(
                camera_frame=frame,
                engine=engine,
                poses=poses_by_id,
                fps=fps,
                backend_name=f"{args.backend.upper()}:{args.mode.upper()}",
            )

            # Control de refresco
            if not args.headless:
                renderer.clock.tick(60)

    except KeyboardInterrupt:
        print("\n[INFO] Interrupcion de teclado detectada.")
    finally:
        if server:
            server.close()
        if client:
            client.close()
        if cap is not None:
            cap.release()
        sound_engine.stop_all()
        backend.close()
        renderer.close()
        print("[INFO] Recursos multimedia y modelos liberados correctamente.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
