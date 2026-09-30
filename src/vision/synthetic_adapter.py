"""Adaptador sintetico de estimacion de posturas para pruebas automatizadas y simulacion."""

from typing import Dict, List, Optional
import numpy as np

from .backend import Keypoint, PoseEstimationBackend, PosePlayer


class SyntheticPoseBackend(PoseEstimationBackend):
    """Generador sintetico determinista de posturas corporales para pruebas y simulacion."""

    def __init__(self, num_players: int = 2):
        self.num_players = num_players
        self._forced_states: Dict[int, str] = {i + 1: "IDLE" for i in range(num_players)}

    def set_player_pose(self, player_id: int, pose_name: str) -> None:
        """Configura la postura sintetica para un jugador."""
        self._forced_states[player_id] = pose_name.upper()

    def process_frame(self, frame: Optional[np.ndarray] = None) -> List[PosePlayer]:
        """Genera jugadores con coordenadas vectoriales correspondientes a sus estados configurados."""
        players: List[PosePlayer] = []

        spacing = 1.0 / (self.num_players + 1)
        for p_idx in range(self.num_players):
            pid = p_idx + 1
            center_x = (p_idx + 1) * spacing
            state = self._forced_states.get(pid, "IDLE")

            sw = 0.16
            shoulder_y = 0.35
            hip_y = 0.65
            ls_x = center_x - sw / 2.0
            rs_x = center_x + sw / 2.0

            keypoints: Dict[str, Keypoint] = {
                "nose": Keypoint(x=center_x, y=0.22, confidence=0.95),
                "left_eye": Keypoint(x=center_x - 0.03, y=0.20, confidence=0.95),
                "right_eye": Keypoint(x=center_x + 0.03, y=0.20, confidence=0.95),
                "left_ear": Keypoint(x=center_x - 0.06, y=0.21, confidence=0.95),
                "right_ear": Keypoint(x=center_x + 0.06, y=0.21, confidence=0.95),
                "left_shoulder": Keypoint(x=ls_x, y=shoulder_y, confidence=0.95),
                "right_shoulder": Keypoint(x=rs_x, y=shoulder_y, confidence=0.95),
                "left_hip": Keypoint(x=ls_x + 0.02, y=hip_y, confidence=0.95),
                "right_hip": Keypoint(x=rs_x - 0.02, y=hip_y, confidence=0.95),
                "left_knee": Keypoint(x=ls_x + 0.02, y=0.82, confidence=0.95),
                "right_knee": Keypoint(x=rs_x - 0.02, y=0.82, confidence=0.95),
                "left_ankle": Keypoint(x=ls_x + 0.02, y=0.95, confidence=0.95),
                "right_ankle": Keypoint(x=rs_x - 0.02, y=0.95, confidence=0.95),
            }

            if state == "KAMEHAMEHA":
                aim_dir = 1.0 if pid == 1 else -1.0
                target_wrist_x = center_x + (aim_dir * 0.22)
                wrist_y = shoulder_y + 0.05
                elbow_x = center_x + (aim_dir * 0.11)

                keypoints["left_elbow"] = Keypoint(x=elbow_x, y=wrist_y + 0.02, confidence=0.95)
                keypoints["right_elbow"] = Keypoint(x=elbow_x, y=wrist_y - 0.02, confidence=0.95)
                keypoints["left_wrist"] = Keypoint(x=target_wrist_x, y=wrist_y - 0.01, confidence=0.95)
                keypoints["right_wrist"] = Keypoint(x=target_wrist_x + 0.01, y=wrist_y + 0.01, confidence=0.95)

            elif state == "SHIELD":
                keypoints["left_elbow"] = Keypoint(x=ls_x - 0.03, y=shoulder_y + 0.10, confidence=0.95)
                keypoints["right_elbow"] = Keypoint(x=rs_x + 0.03, y=shoulder_y + 0.10, confidence=0.95)
                keypoints["left_wrist"] = Keypoint(x=center_x - 0.03, y=shoulder_y + 0.04, confidence=0.95)
                keypoints["right_wrist"] = Keypoint(x=center_x + 0.03, y=shoulder_y + 0.04, confidence=0.95)

            elif state == "CHARGE_KI":
                keypoints["left_elbow"] = Keypoint(x=ls_x - 0.12, y=shoulder_y + 0.16, confidence=0.95)
                keypoints["right_elbow"] = Keypoint(x=rs_x + 0.12, y=shoulder_y + 0.16, confidence=0.95)
                keypoints["left_wrist"] = Keypoint(x=ls_x + 0.01, y=hip_y - 0.02, confidence=0.95)
                keypoints["right_wrist"] = Keypoint(x=rs_x - 0.01, y=hip_y - 0.02, confidence=0.95)

            elif state == "PUNCH":
                aim_dir = 1.0 if pid == 1 else -1.0
                keypoints["left_elbow"] = Keypoint(x=ls_x - 0.02, y=shoulder_y + 0.15, confidence=0.95)
                keypoints["left_wrist"] = Keypoint(x=ls_x - 0.02, y=shoulder_y + 0.20, confidence=0.95)
                keypoints["right_elbow"] = Keypoint(x=rs_x + aim_dir * 0.10, y=shoulder_y, confidence=0.95)
                keypoints["right_wrist"] = Keypoint(x=rs_x + aim_dir * 0.22, y=shoulder_y, confidence=0.95)

            elif state == "UPPERCUT":
                # Gancho derecho vertical por encima de la nariz
                keypoints["left_elbow"] = Keypoint(x=ls_x, y=shoulder_y + 0.12, confidence=0.95)
                keypoints["left_wrist"] = Keypoint(x=center_x - 0.02, y=shoulder_y + 0.08, confidence=0.95)
                keypoints["right_elbow"] = Keypoint(x=center_x + 0.02, y=shoulder_y - 0.04, confidence=0.95)
                keypoints["right_wrist"] = Keypoint(x=center_x + 0.02, y=0.14, confidence=0.95)

            elif state == "SIXTY_SEVEN":
                # Mano izquierda alta (0.16) y mano derecha baja (0.50) con buena apertura
                keypoints["left_elbow"] = Keypoint(x=ls_x - 0.04, y=shoulder_y - 0.06, confidence=0.95)
                keypoints["left_wrist"] = Keypoint(x=ls_x - 0.03, y=0.16, confidence=0.95)
                keypoints["right_elbow"] = Keypoint(x=rs_x + 0.04, y=shoulder_y + 0.08, confidence=0.95)
                keypoints["right_wrist"] = Keypoint(x=rs_x + 0.03, y=0.50, confidence=0.95)

            elif state == "HADOKEN":
                # Ambas manos proyectadas al frente a nivel del pecho
                aim_dir = 1.0 if pid == 1 else -1.0
                target_x = center_x + (aim_dir * 0.20)
                keypoints["left_elbow"] = Keypoint(x=ls_x + aim_dir * 0.08, y=shoulder_y + 0.04, confidence=0.95)
                keypoints["right_elbow"] = Keypoint(x=rs_x + aim_dir * 0.08, y=shoulder_y + 0.04, confidence=0.95)
                keypoints["left_wrist"] = Keypoint(x=target_x - 0.02, y=shoulder_y + 0.04, confidence=0.95)
                keypoints["right_wrist"] = Keypoint(x=target_x + 0.03, y=shoulder_y + 0.04, confidence=0.95)

            elif state == "SPIRIT_BOMB":
                # Manos levantadas al cielo sobre la cabeza
                keypoints["left_elbow"] = Keypoint(x=ls_x - 0.04, y=0.22, confidence=0.95)
                keypoints["right_elbow"] = Keypoint(x=rs_x + 0.04, y=0.22, confidence=0.95)
                keypoints["left_wrist"] = Keypoint(x=ls_x - 0.05, y=0.10, confidence=0.95)
                keypoints["right_wrist"] = Keypoint(x=rs_x + 0.05, y=0.10, confidence=0.95)

            elif state == "DODGE_ROLL":
                # Inclinacion lateral acentuada de hombros > 25 grados
                keypoints["left_shoulder"] = Keypoint(x=ls_x, y=shoulder_y - 0.05, confidence=0.95)
                keypoints["right_shoulder"] = Keypoint(x=rs_x, y=shoulder_y + 0.05, confidence=0.95)
                keypoints["left_wrist"] = Keypoint(x=ls_x - 0.02, y=shoulder_y + 0.15, confidence=0.95)
                keypoints["right_wrist"] = Keypoint(x=rs_x + 0.02, y=shoulder_y + 0.25, confidence=0.95)

            elif state == "TAUNT_CROSS":
                # Brazos cruzados sobre el pecho hacia los hombros contrarios
                keypoints["left_elbow"] = Keypoint(x=ls_x - 0.02, y=shoulder_y + 0.10, confidence=0.95)
                keypoints["right_elbow"] = Keypoint(x=rs_x + 0.02, y=shoulder_y + 0.10, confidence=0.95)
                keypoints["left_wrist"] = Keypoint(x=center_x + 0.06, y=shoulder_y + 0.05, confidence=0.95)
                keypoints["right_wrist"] = Keypoint(x=center_x - 0.06, y=shoulder_y + 0.05, confidence=0.95)

            else:  # IDLE
                keypoints["left_elbow"] = Keypoint(x=ls_x - 0.02, y=shoulder_y + 0.15, confidence=0.95)
                keypoints["right_elbow"] = Keypoint(x=rs_x + 0.02, y=shoulder_y + 0.15, confidence=0.95)
                keypoints["left_wrist"] = Keypoint(x=ls_x - 0.02, y=shoulder_y + 0.32, confidence=0.95)
                keypoints["right_wrist"] = Keypoint(x=rs_x + 0.02, y=shoulder_y + 0.32, confidence=0.95)

            bbox = (center_x - sw, 0.15, center_x + sw, 0.98)
            players.append(
                PosePlayer(
                    player_id=pid,
                    bbox=bbox,
                    keypoints=keypoints,
                    confidence=0.98,
                )
            )

        return players

    def close(self) -> None:
        pass
