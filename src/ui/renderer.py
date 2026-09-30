"""Renderizador multimedia de combate, HUD, VFX, choque de rayos, temporizador y camara con Pygame-CE."""

from collections import deque
import math
import random
from typing import Deque, Dict, List, Optional, Tuple
import cv2
import numpy as np
import pygame

from ..game.combat import BeamProjectile, CombatEngine, FighterState, Particle, ShieldEffect
from ..gestures.recognizer import CombatGesture
from ..vision.backend import PosePlayer

# Conexiones anatomicas para dibujar el esqueleto energetico
SKELETON_CONNECTIONS = [
    ("left_shoulder", "right_shoulder"),
    ("left_shoulder", "left_elbow"),
    ("left_elbow", "left_wrist"),
    ("right_shoulder", "right_elbow"),
    ("right_elbow", "right_wrist"),
    ("left_shoulder", "left_hip"),
    ("right_shoulder", "right_hip"),
    ("left_hip", "right_hip"),
    ("left_hip", "left_knee"),
    ("left_knee", "left_ankle"),
    ("right_hip", "right_knee"),
    ("right_knee", "right_ankle"),
]

# Paletas de color estilizadas por jugador (P1-P4)
FIGHTER_PALETTES = {
    1: {"primary": (0, 230, 255), "secondary": (255, 255, 255), "accent": (0, 160, 255), "name": "NEON CYAN"},
    2: {"primary": (255, 60, 80), "secondary": (255, 215, 0), "accent": (200, 20, 40), "name": "SOLAR CRIMSON"},
    3: {"primary": (40, 230, 130), "secondary": (200, 255, 220), "accent": (20, 160, 90), "name": "EMERALD CYBER"},
    4: {"primary": (190, 70, 255), "secondary": (255, 140, 255), "accent": (130, 30, 210), "name": "ULTRAVIOLET VOID"},
}


class PygameRenderer:
    """Motor de renderizado visual 2D sobre lienzo acelerado con efectos cinematograficos."""

    def __init__(self, width: int = 1280, height: int = 720, headless: bool = False, title: str = "VideoGame Pose Combat"):
        self.width = width
        self.height = height
        self.headless = headless
        self.title = title

        pygame.init()
        pygame.font.init()

        if self.headless:
            self.screen = pygame.Surface((self.width, self.height))
        else:
            self.screen = pygame.display.set_mode((self.width, self.height))
            pygame.display.set_caption(self.title)

        # Superficie de composicion para Screen Shake / Trauma
        self.render_canvas = pygame.Surface((self.width, self.height))

        self.clock = pygame.time.Clock()
        self.font_title = pygame.font.SysFont("Arial", 28, bold=True)
        self.font_timer = pygame.font.SysFont("Arial", 40, bold=True)
        self.font_hud = pygame.font.SysFont("Arial", 18, bold=True)
        self.font_small = pygame.font.SysFont("Arial", 14)
        self.font_banner = pygame.font.SysFont("Arial", 46, bold=True)
        self.font_subbanner = pygame.font.SysFont("Arial", 24, bold=True)

        # Buffer de rastros de movimiento (Motion Trails - 8 frames)
        self.trail_buffer: Dict[int, Deque[Tuple[Tuple[int, int], Tuple[int, int]]]] = {}
        self.show_guide: bool = False

    def handle_events(self, engine: Optional[CombatEngine] = None) -> bool:
        """Procesa eventos de teclado y ventana. Retorna False si se debe salir."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_q):
                    return False
                elif event.key == pygame.K_r and engine:
                    engine.reset_match()
                elif event.key in (pygame.K_h, pygame.K_TAB):
                    self.show_guide = not self.show_guide
        return True

    def render_frame(
        self,
        camera_frame: Optional[np.ndarray],
        engine: CombatEngine,
        poses: Dict[int, PosePlayer],
        fps: float = 60.0,
        backend_name: str = "YOLOv8-Pose",
    ) -> None:
        """Dibuja un fotograma completo con efectos visuales, auras y screen trauma shake."""
        canvas = self.render_canvas

        # 1. Fondo de camara o arena cibernetica con perspectiva reactiva
        if camera_frame is not None and camera_frame.size > 0:
            self._draw_camera_feed(canvas, camera_frame)
        else:
            self._draw_virtual_arena(canvas, engine)

        # 2. Auras energeticas pulsantes proporcionales al Ki
        self._draw_ki_auras(canvas, engine)

        # 3. Avatares estilizados de luchadores, cuerpos ciberneticos y motion trails
        for pid, fighter in engine.fighters.items():
            pose = poses.get(pid)
            self._draw_fighter_avatar(canvas, fighter, pose)

        # 4. Escudos energeticos de bloqueo
        self._draw_shields(canvas, engine.shields)

        # 5. Rayos laser / Kamehameha continuo
        self._draw_beams(canvas, engine.active_beams)

        # 6. Esferas de energia de Hadoken / Plasma Ball
        if hasattr(engine, "active_energy_balls"):
            self._draw_energy_balls(canvas, engine.active_energy_balls)

        # 7. Esferas gigantes de Spirit Bomb / Genkidama
        if hasattr(engine, "active_spirit_bombs"):
            self._draw_spirit_bombs(canvas, engine.active_spirit_bombs)

        # 8. Choque de rayos (Beam Struggle)
        if engine.beam_struggle_active and engine.clash_point:
            self._draw_beam_struggle(canvas, engine.clash_point)

        # 9. Particulas volumetricas
        self._draw_particles(canvas, engine.particles)

        # 10. HUD superior reactivo, barras de vida, Ki y cooldowns
        self._draw_hud(canvas, engine, fps, backend_name)

        # 11. Superposicion de asaltos, fin de partida o desconexion
        if engine.round_state in ("ROUND_OVER", "MATCH_OVER"):
            self._draw_round_overlay(canvas, engine)

        # 11.5. Guia interactiva de movimientos en pantalla (Toggle 'H' o 'TAB')
        if self.show_guide:
            self._draw_movement_guide(canvas)

        # 12. Aplicar Screen Shake (Trauma Shake al canvas)
        shake_x = 0
        shake_y = 0
        trauma = getattr(engine, "screen_trauma", 0.0)
        if trauma > 0.02:
            shake_amp = int((trauma ** 2) * 22)
            shake_x = random.randint(-shake_amp, shake_amp)
            shake_y = random.randint(-shake_amp, shake_amp)

        self.screen.fill((0, 0, 0))
        self.screen.blit(canvas, (shake_x, shake_y))

        if not self.headless:
            pygame.display.flip()

    def _draw_camera_feed(self, canvas: pygame.Surface, frame: np.ndarray) -> None:
        """Superpone el stream de video de OpenCV con un tinte oscuro de alto contraste."""
        mirrored = cv2.flip(frame, 1)
        rgb_frame = cv2.cvtColor(mirrored, cv2.COLOR_BGR2RGB)
        resized = cv2.resize(rgb_frame, (self.width, self.height))

        cam_surface = pygame.surfarray.make_surface(np.rot90(resized))
        canvas.blit(cam_surface, (0, 0))

        dark_overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        dark_overlay.fill((10, 15, 25, 140))
        canvas.blit(dark_overlay, (0, 0))

    def _draw_virtual_arena(self, canvas: pygame.Surface, engine: CombatEngine) -> None:
        """Lienzo cibernetico oscuro reactivo con perspectiva de suelo tipo tron."""
        # Tinte dinamico de fondo segun la intensidad del combate
        trauma = getattr(engine, "screen_trauma", 0.0)
        bg_r = int(15 + trauma * 40)
        bg_g = int(18 - trauma * 8)
        bg_b = int(30 - trauma * 10)
        canvas.fill((bg_r, bg_g, bg_b))

        ground_y = int(self.height * 0.75)
        # Linea del horizonte
        horizon_color = (60 + int(trauma * 80), 80, 130)
        pygame.draw.line(canvas, horizon_color, (0, ground_y), (self.width, ground_y), 3)

        # Cuadricula en perspectiva hacia el suelo
        grid_color = (30, 42, 65)
        for i in range(0, self.width + 120, 80):
            pt_top = (i, ground_y)
            pt_bot = (int(i * 1.35) - 200, self.height)
            pygame.draw.line(canvas, grid_color, pt_top, pt_bot, 1)

        # Lineas horizontales de profundidad
        for d in [0.80, 0.86, 0.93, 0.98]:
            y_depth = int(self.height * d)
            pygame.draw.line(canvas, (25, 35, 55), (0, y_depth), (self.width, y_depth), 1)

    def _draw_ki_auras(self, canvas: pygame.Surface, engine: CombatEngine) -> None:
        """Dibuja auras energeticas pulsantes proporcionales al Ki del luchador."""
        ticks = pygame.time.get_ticks()
        for fighter in engine.fighters.values():
            if fighter.is_knocked_out:
                continue

            cx = int(fighter.screen_x * self.width)
            cy = int(fighter.screen_y * self.height)
            palette = FIGHTER_PALETTES.get(fighter.player_id, FIGHTER_PALETTES[1])
            c_primary = palette["primary"]

            ki_ratio = fighter.ki / fighter.max_ki
            base_radius = int(45 + ki_ratio * 35)
            pulse = int(6 * math.sin(ticks * 0.012 + fighter.player_id))

            # Si esta activamente cargando o tiene bufo de dano, multiplicar aura
            if fighter.is_charging:
                base_radius += 18
                pulse = int(10 * math.sin(ticks * 0.025))

            radius = max(20, base_radius + pulse)
            aura_surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            alpha_outer = int(40 + ki_ratio * 45) if not fighter.is_charging else 110

            color_outer = (c_primary[0], c_primary[1], c_primary[2], alpha_outer)
            color_inner = (255, 255, 255, 90 if fighter.is_charging else 40)

            pygame.draw.circle(aura_surf, color_outer, (radius, radius), radius)
            pygame.draw.circle(aura_surf, color_inner, (radius, radius), max(1, radius - 12))

            # Rayos de sobrecarga energetica durante carga Ki
            if fighter.is_charging:
                for _ in range(4):
                    ang = random.uniform(0, 6.28)
                    r_spark = random.uniform(radius * 0.5, radius * 1.1)
                    sx = int(radius + math.cos(ang) * r_spark)
                    sy = int(radius + math.sin(ang) * r_spark)
                    pygame.draw.circle(aura_surf, (255, 255, 255, 200), (sx, sy), 3)

            canvas.blit(aura_surf, (cx - radius, cy - radius + 15), special_flags=pygame.BLEND_ALPHA_SDL2)

    def _draw_fighter_avatar(self, canvas: pygame.Surface, fighter: FighterState, pose: Optional[PosePlayer]) -> None:
        """Dibuja el avatar estilizado del jugador, esqueleto cinemático, motion trail y blindaje."""
        pid = fighter.player_id
        palette = FIGHTER_PALETTES.get(pid, FIGHTER_PALETTES[1])
        base_color = palette["primary"]
        sec_color = palette["secondary"]
        if fighter.is_knocked_out:
            base_color = (120, 120, 120)
            sec_color = (160, 160, 160)

        cx = int(fighter.screen_x * self.width)
        cy = int(fighter.screen_y * self.height)

        # Inicializar buffer de trails
        if pid not in self.trail_buffer:
            self.trail_buffer[pid] = deque(maxlen=8)

        # Si tenemos pose real de camara / vision
        if pose and len(pose.keypoints) >= 6 and not fighter.is_knocked_out:
            # Obtener puntos clave para el rastro de movimiento
            lw = pose.get_keypoint("left_wrist")
            rw = pose.get_keypoint("right_wrist")
            if lw and rw:
                pt_lw = (int((1.0 - lw.x) * self.width), int(lw.y * self.height))
                pt_rw = (int((1.0 - rw.x) * self.width), int(rw.y * self.height))
                self.trail_buffer[pid].append((pt_lw, pt_rw))

            # Dibujar Motion Trails (estela de movimiento de 8 frames)
            trails = list(self.trail_buffer[pid])
            for i, (tlw, trw) in enumerate(trails[:-1]):
                alpha = int((i + 1) * (180 / len(trails)))
                trail_color = (base_color[0], base_color[1], base_color[2], alpha)
                trail_surf = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
                pygame.draw.circle(trail_surf, trail_color, tlw, 6 + i)
                pygame.draw.circle(trail_surf, trail_color, trw, 6 + i)
                canvas.blit(trail_surf, (0, 0))

            # Dibujar esqueleto anatomico de combate
            for p1_name, p2_name in SKELETON_CONNECTIONS:
                kp1 = pose.get_keypoint(p1_name)
                kp2 = pose.get_keypoint(p2_name)
                if kp1 and kp2:
                    pt1 = (int((1.0 - kp1.x) * self.width), int(kp1.y * self.height))
                    pt2 = (int((1.0 - kp2.x) * self.width), int(kp2.y * self.height))
                    pygame.draw.line(canvas, base_color, pt1, pt2, 7)
                    pygame.draw.line(canvas, sec_color, pt1, pt2, 3)

            # Nodos de blindaje y visor
            for name, kp in pose.keypoints.items():
                if kp.confidence >= 0.3:
                    pt = (int((1.0 - kp.x) * self.width), int(kp.y * self.height))
                    radius = 9 if "wrist" in name or "nose" in name else 5
                    pygame.draw.circle(canvas, sec_color, pt, radius)
                    pygame.draw.circle(canvas, base_color, pt, radius + 2, 2)

        else:
            # FighterBody estilizado tipo Cyber-Warrior para modo sintetico o sin camara
            self._draw_stylized_fighter_body(canvas, fighter, cx, cy, base_color, sec_color)

        # Efecto visual de golpe Melee / Uppercut
        if fighter.current_gesture == CombatGesture.PUNCH and fighter.melee_cooldown > 0.2:
            punch_x = cx + int(fighter.facing_direction * 75)
            pygame.draw.circle(canvas, (255, 200, 80), (punch_x, cy - 5), 16, 4)
        elif fighter.current_gesture == CombatGesture.UPPERCUT and fighter.uppercut_cooldown > 0.8:
            up_x = cx + int(fighter.facing_direction * 30)
            pygame.draw.circle(canvas, (255, 240, 100), (up_x, cy - 65), 22, 4)

    def _draw_stylized_fighter_body(
        self,
        canvas: pygame.Surface,
        fighter: FighterState,
        cx: int,
        cy: int,
        primary: Tuple[int, int, int],
        secondary: Tuple[int, int, int],
    ) -> None:
        """Dibuja un cuerpo de combate estilizado con formas geometricas ciberneticas (FighterBody)."""
        head_y = cy - 60
        facing = fighter.facing_direction

        # 1. Casco Cibernetico / Cabeza
        pygame.draw.circle(canvas, primary, (cx, head_y), 19)
        pygame.draw.circle(canvas, (30, 35, 50), (cx, head_y), 16)
        # Visor brillante
        visor_x = cx + int(facing * 8)
        pygame.draw.ellipse(canvas, secondary, (visor_x - 7, head_y - 4, 14, 8))

        # 2. Coraza Toracica / Pechera Blindada
        chest_top = head_y + 16
        chest_pts = [
            (cx - 18, chest_top),
            (cx + 18, chest_top),
            (cx + 12, cy + 24),
            (cx - 12, cy + 24),
        ]
        pygame.draw.polygon(canvas, primary, chest_pts)
        pygame.draw.polygon(canvas, (20, 25, 40), [
            (cx - 14, chest_top + 3),
            (cx + 14, chest_top + 3),
            (cx + 9, cy + 21),
            (cx - 9, cy + 21),
        ])
        # Nucleo de energia Ki en el pecho
        core_color = (60, 240, 255) if fighter.ki > 20 else (255, 100, 50)
        pygame.draw.circle(canvas, core_color, (cx, chest_top + 18), 5)

        # 3. Hombreras Blindadas
        pygame.draw.circle(canvas, secondary, (cx - 20, chest_top + 4), 7)
        pygame.draw.circle(canvas, secondary, (cx + 20, chest_top + 4), 7)

        # 4. Brazos articulados segun el gesto activo
        if fighter.is_firing_beam:
            # Brazos extendidos disparando
            pygame.draw.line(canvas, primary, (cx, chest_top + 8), (cx + int(facing * 65), cy), 8)
            pygame.draw.line(canvas, secondary, (cx, chest_top + 8), (cx + int(facing * 65), cy), 3)
        elif fighter.is_blocking:
            # Guardia alta cruzada
            pygame.draw.line(canvas, (255, 215, 0), (cx - 15, chest_top + 8), (cx + int(facing * 15), head_y), 7)
            pygame.draw.line(canvas, (255, 215, 0), (cx + 15, chest_top + 8), (cx + int(facing * 15), head_y), 7)
        elif fighter.is_charging:
            # Brazos en los costados con codos hacia afuera
            pygame.draw.line(canvas, primary, (cx - 20, chest_top + 6), (cx - 32, cy + 10), 6)
            pygame.draw.line(canvas, primary, (cx - 32, cy + 10), (cx - 16, cy + 22), 6)
            pygame.draw.line(canvas, primary, (cx + 20, chest_top + 6), (cx + 32, cy + 10), 6)
            pygame.draw.line(canvas, primary, (cx + 32, cy + 10), (cx + 16, cy + 22), 6)
        elif fighter.current_gesture == CombatGesture.SPIRIT_BOMB:
            # Brazos al cielo alzando la Genkidama
            pygame.draw.line(canvas, primary, (cx - 18, chest_top + 4), (cx - 30, head_y - 25), 7)
            pygame.draw.line(canvas, primary, (cx + 18, chest_top + 4), (cx + 30, head_y - 25), 7)
            pygame.draw.circle(canvas, secondary, (cx - 30, head_y - 25), 6)
            pygame.draw.circle(canvas, secondary, (cx + 30, head_y - 25), 6)
        elif fighter.current_gesture == CombatGesture.PUNCH:
            # Estocada de puñetazo
            pygame.draw.line(canvas, (255, 100, 50), (cx, chest_top + 8), (cx + int(facing * 80), cy - 4), 9)
            pygame.draw.circle(canvas, secondary, (cx + int(facing * 80), cy - 4), 7)
        elif fighter.current_gesture == CombatGesture.UPPERCUT:
            # Gancho hacia arriba
            pygame.draw.line(canvas, (255, 220, 80), (cx, chest_top + 8), (cx + int(facing * 20), head_y - 15), 9)
            pygame.draw.circle(canvas, secondary, (cx + int(facing * 20), head_y - 15), 8)
        else:
            # Guardia normal de reposo
            pygame.draw.line(canvas, primary, (cx - 18, chest_top + 6), (cx - 24, cy + 14), 5)
            pygame.draw.line(canvas, primary, (cx + 18, chest_top + 6), (cx + 24, cy + 14), 5)

        # 5. Piernas con grebas
        leg_spread = 24
        pygame.draw.line(canvas, primary, (cx - 8, cy + 24), (cx - leg_spread, cy + 85), 7)
        pygame.draw.line(canvas, primary, (cx + 8, cy + 24), (cx + leg_spread, cy + 85), 7)
        pygame.draw.circle(canvas, secondary, (cx - leg_spread, cy + 85), 5)
        pygame.draw.circle(canvas, secondary, (cx + leg_spread, cy + 85), 5)

    def _draw_shields(self, canvas: pygame.Surface, shields: Dict[int, ShieldEffect]) -> None:
        """Dibuja cupulas energeticas de bloqueo defensivo."""
        ticks = pygame.time.get_ticks()
        for shield in shields.values():
            if shield.active:
                cx = int(shield.center_x * self.width)
                cy = int(shield.center_y * self.height)
                r = int(shield.radius * self.width)
                wobble = int(4 * math.sin(ticks * 0.02))

                shield_surf = pygame.Surface((r * 2 + 20, r * 2 + 20), pygame.SRCALPHA)
                center_pt = (r + 10, r + 10)
                pygame.draw.circle(shield_surf, (255, 215, 0, 90), center_pt, r + wobble)
                pygame.draw.circle(shield_surf, (255, 255, 200, 220), center_pt, r + wobble, 4)
                pygame.draw.circle(shield_surf, (255, 215, 0, 150), center_pt, max(1, r - 15), 2)
                canvas.blit(shield_surf, (cx - r - 10, cy - r - 10))

    def _draw_beams(self, canvas: pygame.Surface, beams: List[BeamProjectile]) -> None:
        """Dibuja rayos laser continuos / Kamehameha con nucleo blanco incandescente."""
        ticks = pygame.time.get_ticks()
        for beam in beams:
            if not beam.active:
                continue

            x1 = int(beam.start_x * self.width)
            y1 = int(beam.start_y * self.height)
            x2 = int(beam.head_x * self.width)
            y2 = int(beam.head_y * self.height)

            jitter = int(3 * math.sin(ticks * 0.04))
            outer_thick = 24 + jitter
            inner_thick = 10 + (jitter // 2)

            # Capa exterior con tinte de energia
            pygame.draw.line(canvas, beam.color, (x1, y1), (x2, y2), outer_thick)
            # Capa interior brillante
            pygame.draw.line(canvas, beam.core_color, (x1, y1), (x2, y2), inner_thick)

            # Cabeza del rayo / Esfera de plasma
            pygame.draw.circle(canvas, beam.color, (x2, y2), outer_thick)
            pygame.draw.circle(canvas, beam.core_color, (x2, y2), inner_thick)

    def _draw_energy_balls(self, canvas: pygame.Surface, balls: List[object]) -> None:
        """Dibuja las esferas de energia de Hadoken / Plasma Ball."""
        for ball in balls:
            if not getattr(ball, "active", True):
                continue
            bx = int(ball.x * self.width)
            by = int(ball.y * self.height)
            br = max(10, int(getattr(ball, "radius", 0.035) * self.width))

            surf = pygame.Surface((br * 3, br * 3), pygame.SRCALPHA)
            center = (br * 3 // 2, br * 3 // 2)
            c = getattr(ball, "color", (0, 230, 255))
            pygame.draw.circle(surf, (c[0], c[1], c[2], 120), center, br + 4)
            pygame.draw.circle(surf, (255, 255, 255, 220), center, br)
            pygame.draw.circle(surf, (c[0], c[1], c[2], 255), center, max(2, br - 4), 2)
            canvas.blit(surf, (bx - br * 3 // 2, by - br * 3 // 2))

    def _draw_spirit_bombs(self, canvas: pygame.Surface, bombs: List[object]) -> None:
        """Dibuja la esfera colosal de Genkidama / Spirit Bomb con corona y chispas."""
        ticks = pygame.time.get_ticks()
        for bomb in bombs:
            if not getattr(bomb, "active", True):
                continue
            bx = int(bomb.x * self.width)
            by = int(bomb.y * self.height)
            br = max(18, int(getattr(bomb, "radius", 0.06) * self.width))

            surf = pygame.Surface((br * 3, br * 3), pygame.SRCALPHA)
            center = (br * 3 // 2, br * 3 // 2)
            pulse = int(5 * math.sin(ticks * 0.03))

            # Corona exterior azul cielo
            pygame.draw.circle(surf, (100, 220, 255, 90), center, br + 12 + pulse)
            # Cuerpo principal
            pygame.draw.circle(surf, (160, 240, 255, 180), center, br + pulse)
            # Nucleo hiper-brillante blanco puro
            pygame.draw.circle(surf, (255, 255, 255, 240), center, max(4, br - 8))

            # Arcos de plasma alrededor de la esfera
            for i in range(3):
                ang = ticks * 0.01 + i * 2.09
                arc_r = br + 8
                ax = int(center[0] + math.cos(ang) * arc_r)
                ay = int(center[1] + math.sin(ang) * arc_r)
                pygame.draw.circle(surf, (255, 255, 255, 220), (ax, ay), 3)

            canvas.blit(surf, (bx - br * 3 // 2, by - br * 3 // 2), special_flags=pygame.BLEND_ALPHA_SDL2)

    def _draw_beam_struggle(self, canvas: pygame.Surface, clash_point: Tuple[float, float]) -> None:
        """Dibuja la colision estelar en el punto de choque de rayos."""
        ticks = pygame.time.get_ticks()
        cx = int(clash_point[0] * self.width)
        cy = int(clash_point[1] * self.height)
        pulse = int(8 * math.sin(ticks * 0.05))

        # Esfera de choque
        radius = 32 + pulse
        struggle_surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(struggle_surf, (255, 255, 255, 220), (radius, radius), radius)
        pygame.draw.circle(struggle_surf, (255, 215, 0, 160), (radius, radius), radius + 6, 4)
        canvas.blit(struggle_surf, (cx - radius, cy - radius))

        # Chispas de choque
        for _ in range(3):
            ang = random.uniform(0, 6.28)
            length = random.uniform(20, 50)
            ex = cx + int(math.cos(ang) * length)
            ey = cy + int(math.sin(ang) * length)
            pygame.draw.line(canvas, (255, 255, 200), (cx, cy), (ex, ey), 3)

    def _draw_particles(self, canvas: pygame.Surface, particles: List[Particle]) -> None:
        """Renderiza particulas energeticas de impacto y auras."""
        for p in particles:
            alpha = int(255 * (p.life / p.max_life))
            pr = max(1, int(p.radius * self.width))
            px = int(p.x * self.width)
            py = int(p.y * self.height)

            p_surf = pygame.Surface((pr * 2, pr * 2), pygame.SRCALPHA)
            color_with_alpha = (p.color[0], p.color[1], p.color[2], alpha)
            pygame.draw.circle(p_surf, color_with_alpha, (pr, pr), pr)
            canvas.blit(p_surf, (px - pr, py - pr))

    def _draw_hud(self, canvas: pygame.Surface, engine: CombatEngine, fps: float, backend_name: str) -> None:
        """Dibuja las barras de vida (HP), energia (Ki), badges de cooldown, temporizador y asaltos."""
        # Diagnostico superior
        diag_text = self.font_small.render(
            f"Motor: {backend_name} | FPS: {fps:.1f} | 'H'/'TAB': Guia de Movimientos | 'R': Reiniciar | 'Q'/'ESC': Salir",
            True,
            (180, 200, 220),
        )
        canvas.blit(diag_text, (20, 15))

        # Cronometro Central y Asalto Actual
        center_x = self.width // 2
        round_title = f"ASALTO {engine.round_number}" if engine.round_number <= 2 else "ASALTO FINAL"
        surf_round = self.font_hud.render(round_title, True, (255, 215, 0))
        rect_round = surf_round.get_rect(center=(center_x, 25))
        canvas.blit(surf_round, rect_round)

        time_val = int(engine.round_timer)
        timer_color = (255, 60, 60) if time_val <= 10 else (240, 240, 240)
        surf_timer = self.font_timer.render(f"{time_val:02d}", True, timer_color)
        rect_timer = surf_timer.get_rect(center=(center_x, 62))
        canvas.blit(surf_timer, rect_timer)

        # Paneles de Jugadores
        for pid, fighter in engine.fighters.items():
            is_left = pid == 1 or (pid % 2 != 0)
            bar_w = 340
            bar_h = 24
            bar_y = 50

            bar_x = 30 if is_left else (self.width - 30 - bar_w)

            # Barra de Vida (HP)
            pygame.draw.rect(canvas, (20, 25, 40), (bar_x - 3, bar_y - 3, bar_w + 6, bar_h + 6), border_radius=4)
            pygame.draw.rect(canvas, (60, 70, 90), (bar_x, bar_y, bar_w, bar_h), border_radius=3)

            hp_ratio = max(0.0, fighter.hp / fighter.max_hp)
            fill_w = int(bar_w * hp_ratio)
            hp_color = (60, 220, 80) if hp_ratio > 0.5 else ((240, 190, 40) if hp_ratio > 0.25 else (230, 50, 50))
            if fill_w > 0:
                pygame.draw.rect(canvas, hp_color, (bar_x, bar_y, fill_w, bar_h), border_radius=3)

            # Nombre y Marcador de Asaltos Ganados
            name_txt = self.font_hud.render(f"{fighter.name} : {int(fighter.hp)} HP", True, (255, 255, 255))
            canvas.blit(name_txt, (bar_x, bar_y - 24))

            # Esferas de asaltos ganados (Mejor de 3)
            badge_start_x = (bar_x + bar_w - 45) if is_left else (bar_x + 10)
            for r in range(engine.max_rounds_to_win):
                bx = badge_start_x + (r * 18)
                by = bar_y - 14
                if r < fighter.rounds_won:
                    pygame.draw.circle(canvas, (255, 215, 0), (bx, by), 6)
                else:
                    pygame.draw.circle(canvas, (70, 80, 100), (bx, by), 6, 2)

            # Barra de Ki
            ki_y = bar_y + bar_h + 8
            ki_h = 12
            pygame.draw.rect(canvas, (20, 25, 40), (bar_x - 2, ki_y - 2, bar_w + 4, ki_h + 4), border_radius=3)
            pygame.draw.rect(canvas, (40, 45, 60), (bar_x, ki_y, bar_w, ki_h), border_radius=2)
            ki_ratio = max(0.0, fighter.ki / fighter.max_ki)
            ki_fill_w = int(bar_w * ki_ratio)
            if ki_fill_w > 0:
                pygame.draw.rect(canvas, (60, 200, 255), (bar_x, ki_y, ki_fill_w, ki_h), border_radius=2)

            # Accion Actual
            gesture_name = fighter.current_gesture.value if hasattr(fighter.current_gesture, "value") else str(fighter.current_gesture)
            status_desc = {
                "IDLE": "LISTO",
                "KAMEHAMEHA": "KAMEHAMEHA ACTIVO!",
                "SHIELD": "ESCUDO BLOQUEANDO",
                "CHARGE_KI": "CARGANDO ENERGIA KI...",
                "PUNCH": "GOLPE MELEE!",
                "UPPERCUT": "GANCHO UPPERCUT!",
                "SIXTY_SEVEN": "PROVOCACION 67!",
                "HADOKEN": "DISPARO HADOKEN!",
                "SPIRIT_BOMB": "CONCENTRANDO GENKIDAMA!",
                "DODGE_ROLL": "EVASION ACROBATICA!",
                "TAUNT_CROSS": "BRAZOS CRUZADOS: PODER +30%!",
            }.get(gesture_name, gesture_name)

            status_color = (150, 240, 255) if "KAMEHAMEHA" in status_desc or "GENKIDAMA" in status_desc else (
                (255, 220, 80) if "ESCUDO" in status_desc or "CARGANDO" in status_desc else (200, 210, 220)
            )
            action_txt = self.font_small.render(f"Accion: {status_desc}", True, status_color)
            canvas.blit(action_txt, (bar_x, ki_y + ki_h + 6))

            # HUD de Cooldowns de Habilidades Especiales (T-12)
            self._draw_cooldown_badges(canvas, fighter, bar_x, ki_y + ki_h + 26)

    def _draw_cooldown_badges(self, canvas: pygame.Surface, fighter: FighterState, start_x: int, start_y: int) -> None:
        """Dibuja indicadores circulares de recarga de habilidades (Cooldown Badges)."""
        skills = [
            ("U", getattr(fighter, "uppercut_cooldown", 0.0), 1.2, (255, 180, 50)),
            ("H", getattr(fighter, "hadoken_cooldown", 0.0), 1.0, (0, 220, 255)),
            ("D", getattr(fighter, "dodge_cooldown", 0.0), 1.6, (140, 240, 180)),
            ("S", getattr(fighter, "spirit_bomb_cooldown", 0.0), 4.0, (100, 210, 255)),
            ("67", getattr(fighter, "taunt_cooldown", 0.0), 10.0, (255, 215, 0)),
        ]

        for i, (label, cd, max_cd, color) in enumerate(skills):
            bx = start_x + (i * 32)
            by = start_y
            is_ready = cd <= 0.0

            badge_color = color if is_ready else (70, 80, 95)
            pygame.draw.circle(canvas, (20, 25, 35), (bx + 11, by + 11), 12)
            pygame.draw.circle(canvas, badge_color, (bx + 11, by + 11), 11, 2 if is_ready else 1)

            lbl_surf = self.font_small.render(label, True, (255, 255, 255) if is_ready else (120, 130, 140))
            canvas.blit(lbl_surf, (bx + (7 if len(label) == 1 else 3), by + 3))

    def _draw_round_overlay(self, canvas: pygame.Surface, engine: CombatEngine) -> None:
        """Muestra pancartas cinematicas de final de asalto o victoria de partida."""
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        canvas.blit(overlay, (0, 0))

        if engine.round_state == "ROUND_OVER":
            if engine.round_winner_id and engine.round_winner_id > 0:
                w = engine.fighters.get(engine.round_winner_id)
                w_name = w.name if w else f"Jugador {engine.round_winner_id}"
                main_msg = f"{w_name.upper()} GANA EL ASALTO!"
                color = (255, 215, 0)
            else:
                main_msg = "EMPATE DE ASALTO!"
                color = (200, 200, 200)

            surf_main = self.font_banner.render(main_msg, True, color)
            canvas.blit(surf_main, surf_main.get_rect(center=(self.width // 2, self.height // 2 - 20)))

            surf_sub = self.font_subbanner.render("PREPARANDO SIGUIENTE ASALTO...", True, (255, 255, 255))
            canvas.blit(surf_sub, surf_sub.get_rect(center=(self.width // 2, self.height // 2 + 35)))

        elif engine.round_state == "MATCH_OVER":
            if engine.winner_id and engine.winner_id > 0:
                w = engine.fighters.get(engine.winner_id)
                w_name = w.name if w else f"Jugador {engine.winner_id}"
                main_msg = f"CAMPEON DEL TORNEO: {w_name.upper()}!"
                color = (255, 215, 0)
            else:
                main_msg = "FIN DE LA PARTIDA: COMBATE EMPATADO!"
                color = (220, 220, 220)

            surf_main = self.font_banner.render(main_msg, True, color)
            canvas.blit(surf_main, surf_main.get_rect(center=(self.width // 2, self.height // 2 - 20)))

            surf_sub = self.font_subbanner.render("Presiona 'R' para revancha | 'ESC' para salir", True, (255, 255, 255))
            canvas.blit(surf_sub, surf_sub.get_rect(center=(self.width // 2, self.height // 2 + 30)))

            # Tabla de Estadisticas Finales del Torneo (MatchStats)
            if hasattr(engine, "stats") and len(engine.stats) >= 2:
                panel_w, panel_h = 560, 150
                px = (self.width - panel_w) // 2
                py = self.height // 2 + 65
                pygame.draw.rect(canvas, (20, 25, 40), (px, py, panel_w, panel_h), border_radius=6)
                pygame.draw.rect(canvas, (255, 215, 0), (px, py, panel_w, panel_h), 2, border_radius=6)

                st1 = engine.stats.get(1)
                st2 = engine.stats.get(2)
                f1_name = engine.fighters[1].name if 1 in engine.fighters else "P1"
                f2_name = engine.fighters[2].name if 2 in engine.fighters else "P2"

                h_txt = self.font_hud.render(f"--- RESUMEN TECNICO: {f1_name} VS {f2_name} ---", True, (255, 215, 0))
                canvas.blit(h_txt, h_txt.get_rect(center=(self.width // 2, py + 22)))

                if st1 and st2:
                    row1 = self.font_small.render(
                        f"Dano Total Infligido:  {f1_name}: {int(st1.damage_dealt)} HP  |  {f2_name}: {int(st2.damage_dealt)} HP",
                        True, (220, 230, 240)
                    )
                    row2 = self.font_small.render(
                        f"Precision de Ataque:   {f1_name}: {st1.hits_landed}/{st1.attacks_thrown} ({st1.accuracy:.0f}%)  |  {f2_name}: {st2.hits_landed}/{st2.attacks_thrown} ({st2.accuracy:.0f}%)",
                        True, (220, 230, 240)
                    )
                    row3 = self.font_small.render(
                        f"Evasiones Realizadas:  {f1_name}: {st1.dodges_executed}  |  {f2_name}: {st2.dodges_executed}",
                        True, (220, 230, 240)
                    )
                    canvas.blit(row1, (px + 30, py + 52))
                    canvas.blit(row2, (px + 30, py + 80))
                    canvas.blit(row3, (px + 30, py + 108))

    def _draw_movement_guide(self, canvas: pygame.Surface) -> None:
        """Dibuja un panel translucido de referencia rapida de movimientos y poses corporales."""
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((5, 10, 20, 215))
        canvas.blit(overlay, (0, 0))

        gw, gh = 980, 600
        gx = (self.width - gw) // 2
        gy = (self.height - gh) // 2

        pygame.draw.rect(canvas, (15, 22, 38), (gx, gy, gw, gh), border_radius=10)
        pygame.draw.rect(canvas, (0, 230, 255), (gx, gy, gw, gh), 2, border_radius=10)

        # Titulo Principal
        title = self.font_title.render("--- GUIA OFICIAL DE MOVIMIENTOS Y POSES DE COMBATE ---", True, (255, 215, 0))
        canvas.blit(title, title.get_rect(center=(self.width // 2, gy + 32)))

        subtitle = self.font_small.render("Realiza las posturas frente a la camara o usa las teclas simuladas en el teclado", True, (180, 210, 230))
        canvas.blit(subtitle, subtitle.get_rect(center=(self.width // 2, gy + 60)))

        # Filas de Movimientos
        moves = [
            ("KAMEHAMEHA", "Manos juntas al frente hacia el rival", "12 Ki/s", "Rayo continuo (40 HP/s) + Choque", "'1' / '8'", (60, 220, 255)),
            ("ESCUDO (SHIELD)", "Antebrazos verticales cubriendo pecho", "0 Ki", "Mitiga 85% dano (Vulnerable a Uppercut)", "'2' / '9'", (255, 215, 0)),
            ("CARGA KI", "Codos abiertos, punos en cintura", "+15 Ki/s", "Recarga Ki rapidamente con aura", "'3' / '0'", (255, 230, 80)),
            ("MELEE (PUNCH)", "Estocada recta de un puno al frente", "0 Ki", "18 HP a corta distancia + Knockback", "'5' / '='", (255, 100, 50)),
            ("UPPERCUT", "Puno vertical ascendente sobre nariz", "0 Ki", "24 HP | ROMPE ESCUDOS + Aturdimiento", "'6' / '['", (255, 180, 50)),
            ("BALANZA 67", "Balanza: 1 mano muy alta y 1 muy baja", "0 Ki", "Provocacion: Paraliza al rival por 2.0s", "'7' / ']'", (255, 215, 0)),
            ("HADOKEN", "Ambas palmas extendidas al pecho", "20 Ki", "Esfera balistica rapida (24 HP dano)", "'U' / 'J'", (0, 230, 255)),
            ("GENKIDAMA", "Brazos alzados al cielo sobre cabeza", "25+ Ki", "Esfera colosal: 45 HP en area + Shake", "'I' / 'K'", (120, 230, 255)),
            ("DODGE ROLL", "Inclinacion lateral de hombros > 25 deg", "0 Ki", "Evasion: Inmunidad total por 0.4s", "'O' / 'L'", (140, 240, 180)),
            ("BRAZOS CRUZADOS", "Brazos cruzados en 'X' en el pecho", "0 Ki", "Bufo de Dano: Poder de ataque +30% (8s)", "'P' / ';'", (255, 80, 60)),
        ]

        # Encabezado de Columnas
        col_y = gy + 88
        h_g = self.font_hud.render("Gesto / Ataque", True, (0, 230, 255))
        h_p = self.font_hud.render("Postura Corporal", True, (0, 230, 255))
        h_k = self.font_hud.render("Costo Ki", True, (0, 230, 255))
        h_e = self.font_hud.render("Efecto Tecnico", True, (0, 230, 255))
        h_t = self.font_hud.render("Simulador", True, (0, 230, 255))

        canvas.blit(h_g, (gx + 25, col_y))
        canvas.blit(h_p, (gx + 185, col_y))
        canvas.blit(h_k, (gx + 465, col_y))
        canvas.blit(h_e, (gx + 555, col_y))
        canvas.blit(h_t, (gx + 875, col_y))
        pygame.draw.line(canvas, (40, 60, 90), (gx + 20, col_y + 22), (gx + gw - 20, col_y + 22), 1)

        row_y = col_y + 30
        for name, pose, cost, effect, key, color in moves:
            s_name = self.font_hud.render(name, True, color)
            s_pose = self.font_small.render(pose, True, (220, 230, 240))
            s_cost = self.font_small.render(cost, True, (150, 240, 255))
            s_effect = self.font_small.render(effect, True, (210, 220, 230))
            s_key = self.font_hud.render(key, True, (255, 215, 0))

            canvas.blit(s_name, (gx + 25, row_y))
            canvas.blit(s_pose, (gx + 185, row_y + 2))
            canvas.blit(s_cost, (gx + 465, row_y + 2))
            canvas.blit(s_effect, (gx + 555, row_y + 2))
            canvas.blit(s_key, (gx + 885, row_y))

            row_y += 39

        # Pie de Pagina
        footer = self.font_hud.render("Presiona 'H' o 'TAB' para cerrar esta guia y continuar el combate", True, (255, 255, 255))
        canvas.blit(footer, footer.get_rect(center=(self.width // 2, gy + gh - 22)))

    def close(self) -> None:
        """Cierra la ventana y libera los subsistemas de visualizacion."""
        try:
            pygame.quit()
        except Exception:
            pass
