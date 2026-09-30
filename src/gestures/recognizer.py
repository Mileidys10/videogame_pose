"""Reconocedor de gestos corporales de combate basados en puntos clave normalizados."""

from collections import deque
from enum import Enum
from typing import Deque, Dict, Optional
import math

from ..vision.backend import PosePlayer


class CombatGesture(str, Enum):
    """Acciones de combate reconocibles por el motor."""
    IDLE = "IDLE"
    KAMEHAMEHA = "KAMEHAMEHA"
    SHIELD = "SHIELD"
    CHARGE_KI = "CHARGE_KI"
    PUNCH = "PUNCH"
    UPPERCUT = "UPPERCUT"
    SIXTY_SEVEN = "SIXTY_SEVEN"
    HADOKEN = "HADOKEN"
    SPIRIT_BOMB = "SPIRIT_BOMB"
    DODGE_ROLL = "DODGE_ROLL"
    TAUNT_CROSS = "TAUNT_CROSS"


class GestureRecognizer:
    """Clasificador heuristico de gestos corporales con filtro de estabilizacion temporal (debounce)."""

    def __init__(self, debounce_frames: int = 3):
        self.debounce_frames = max(1, debounce_frames)
        self._history: Dict[int, Deque[CombatGesture]] = {}

    def classify_instant(self, player: PosePlayer) -> CombatGesture:
        """Determina el gesto en el fotograma actual sin filtrar temporalmente."""
        lw = player.get_keypoint("left_wrist")
        rw = player.get_keypoint("right_wrist")
        ls = player.get_keypoint("left_shoulder")
        rs = player.get_keypoint("right_shoulder")
        le = player.get_keypoint("left_elbow")
        re = player.get_keypoint("right_elbow")
        lh = player.get_keypoint("left_hip")
        rh = player.get_keypoint("right_hip")
        nose = player.get_keypoint("nose")

        if not lw or not rw:
            return CombatGesture.IDLE

        sw = player.shoulder_width
        wrist_dist = lw.distance_to(rw)

        # Referencias de altura normalizadas
        avg_wx = (lw.x + rw.x) / 2.0
        avg_wy = (lw.y + rw.y) / 2.0
        avg_sy = ((ls.y if ls else 0.35) + (rs.y if rs else 0.35)) / 2.0
        avg_hy = ((lh.y if lh else 0.65) + (rh.y if rh else 0.65)) / 2.0
        nose_y = nose.y if nose else (avg_sy - 0.15)
        torso_cx, _ = player.torso_center

        lw_to_ls = lw.distance_to(ls) if ls else 0.5 * sw
        rw_to_rs = rw.distance_to(rs) if rs else 0.5 * sw

        # 0. EVALUAR EVASION / DODGE_ROLL (Inclinacion lateral del torso/hombros > 25 grados)
        if ls and rs:
            dx_shoulders = max(0.01, abs(ls.x - rs.x))
            dy_shoulders = abs(ls.y - rs.y)
            if (dy_shoulders / dx_shoulders) >= 0.46:  # tan(24.7 deg) ~ 0.46
                return CombatGesture.DODGE_ROLL

        # 0.5. EVALUAR SPIRIT_BOMB (Genkidama: ambos brazos levantados al cielo sobre la cabeza)
        both_hands_high = (lw.y < nose_y - 0.08) and (rw.y < nose_y - 0.08)
        hands_separated = wrist_dist >= 0.35 * sw
        if both_hands_high and hands_separated:
            return CombatGesture.SPIRIT_BOMB

        # 1. EVALUAR GESTO "67" (Balanza alternada: gran desnivel en Y Y manos separadas horizontalmente)
        height_diff = abs(lw.y - rw.y)
        horizontal_spread = abs(lw.x - rw.x)
        if height_diff >= 0.20 and horizontal_spread >= 0.70 * sw:
            return CombatGesture.SIXTY_SEVEN

        # 2. EVALUAR UPPERCUT (Gancho vertical ascendente por encima de la nariz cerca del centro)
        uppercut_right = (rw.y < nose_y) and (abs(rw.x - torso_cx) <= 0.35 * sw) and (lw.y >= avg_sy - 0.05)
        uppercut_left = (lw.y < nose_y) and (abs(lw.x - torso_cx) <= 0.35 * sw) and (rw.y >= avg_sy - 0.05)
        if uppercut_right or uppercut_left:
            return CombatGesture.UPPERCUT

        # 3. EVALUAR KAMEHAMEHA / RAYO LASER (Manos muy juntas y proyectadas)
        hands_together = wrist_dist <= (0.28 * sw)
        hands_at_chest_or_forward = (nose_y - 0.05) <= avg_wy <= (avg_hy + 0.15)
        arms_projected = (lw_to_ls >= 0.45 * sw) and (rw_to_rs >= 0.45 * sw)

        if hands_together and hands_at_chest_or_forward and arms_projected:
            return CombatGesture.KAMEHAMEHA

        # 3.8. EVALUAR TAUNT_CROSS (Brazos cruzados en X sobre el pecho: muñeca izq a la der y viceversa)
        wrists_at_chest = (nose_y - 0.05) <= avg_wy <= (avg_sy + 0.35 * sw)
        wrists_crossed = (lw.x > torso_cx + 0.04 * sw) and (rw.x < torso_cx - 0.04 * sw)
        if wrists_at_chest and wrists_crossed:
            return CombatGesture.TAUNT_CROSS

        # 4. EVALUAR ESCUDO / BLOQUEO (SHIELD)
        guard_height = (nose_y - 0.10) <= avg_wy <= (avg_sy + 0.50 * sw)
        wrists_defensive = (wrist_dist <= 0.55 * sw) and (abs(avg_wx - torso_cx) <= 0.35 * sw)
        if guard_height and wrists_defensive:
            return CombatGesture.SHIELD

        # 5. EVALUAR HADOKEN (Manos proyectadas hacia adelante en direccion lateral)
        hands_hadoken = (wrist_dist <= 0.65 * sw)
        arms_pushed_forward = abs(avg_wx - torso_cx) >= 0.60 * sw
        chest_level = (avg_sy - 0.10) <= avg_wy <= (avg_hy + 0.15)
        if hands_hadoken and arms_pushed_forward and chest_level:
            return CombatGesture.HADOKEN

        # 6. EVALUAR CARGA DE KI
        wrists_low = avg_wy >= (avg_sy + 0.50 * sw)
        elbows_bent_outward = False
        if le and re:
            elbow_spread = abs(le.x - re.x)
            shoulder_spread = abs(ls.x - rs.x) if (ls and rs) else sw
            wrist_spread = abs(lw.x - rw.x)
            elbows_bent_outward = (elbow_spread > shoulder_spread * 1.05) and (wrist_spread < elbow_spread)

        if wrists_low and elbows_bent_outward:
            return CombatGesture.CHARGE_KI

        # 7. EVALUAR GOLPE MELEE (PUNCH)
        punch_left = (lw_to_ls >= 0.85 * sw) and (rw_to_rs <= 0.45 * sw)
        punch_right = (rw_to_rs >= 0.85 * sw) and (lw_to_ls <= 0.45 * sw)
        if punch_left or punch_right:
            return CombatGesture.PUNCH

        # 8. REPOSO (IDLE)
        return CombatGesture.IDLE

    def update_and_get_gesture(self, player: PosePlayer) -> CombatGesture:
        """Actualiza el historial temporal del jugador y retorna el gesto consolidado."""
        pid = player.player_id
        if pid not in self._history:
            self._history[pid] = deque(maxlen=self.debounce_frames)

        instant_gesture = self.classify_instant(player)
        self._history[pid].append(instant_gesture)

        queue = self._history[pid]
        if len(queue) == self.debounce_frames:
            votes: Dict[CombatGesture, int] = {}
            for g in queue:
                votes[g] = votes.get(g, 0) + 1
            majority_gesture, count = max(votes.items(), key=lambda item: item[1])
            if count >= math.ceil(self.debounce_frames / 2.0):
                return majority_gesture

        return instant_gesture

    def reset(self, player_id: Optional[int] = None) -> None:
        """Reinicia el buffer de suavizado temporal."""
        if player_id is not None:
            if player_id in self._history:
                self._history[player_id].clear()
        else:
            self._history.clear()
