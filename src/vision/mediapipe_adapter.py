"""Adaptador de estimacion de posturas con Google MediaPipe Tasks API v1.0+."""

from pathlib import Path
from typing import Dict, List, Optional
import cv2
import numpy as np

from .backend import Keypoint, PoseEstimationBackend, PosePlayer

MP_INDEX_MAP = {
    0: "nose",
    2: "left_eye",
    5: "right_eye",
    7: "left_ear",
    8: "right_ear",
    11: "left_shoulder",
    12: "right_shoulder",
    13: "left_elbow",
    14: "right_elbow",
    15: "left_wrist",
    16: "right_wrist",
    23: "left_hip",
    24: "right_hip",
    25: "left_knee",
    26: "right_knee",
    27: "left_ankle",
    28: "right_ankle",
}


class MediaPipePoseBackend(PoseEstimationBackend):
    """Motor de deteccion usando Google MediaPipe con particion espacial ROI por jugador."""

    def __init__(
        self,
        model_path: Optional[str] = None,
        min_confidence: float = 0.35,
        num_players: int = 2,
    ):
        import mediapipe as mp
        from mediapipe.tasks import python
        from mediapipe.tasks.python import vision

        if model_path is None:
            # Buscar en directorio local o en repo de cabecera
            candidates = [
                Path(__file__).resolve().parent.parent.parent / "models" / "pose_landmarker_lite.task",
                Path("C:/Users/POWER/Documents/GitHub/pose_active_break/models/pose_landmarker_lite.task"),
            ]
            for candidate in candidates:
                if candidate.exists():
                    model_path = str(candidate)
                    break

        if not model_path or not Path(model_path).exists():
            raise FileNotFoundError(
                f"No se encontro el archivo del modelo MediaPipe: {model_path}. "
                "Coloque pose_landmarker_lite.task en videogame_pose/models/."
            )

        self.model_path = str(model_path)
        self.min_confidence = min_confidence
        self.num_players = num_players
        self.mp = mp

        base_options = python.BaseOptions(model_asset_path=self.model_path)
        options = vision.PoseLandmarkerOptions(
            base_options=base_options,
            running_mode=vision.RunningMode.IMAGE,
            num_poses=1,
            min_pose_detection_confidence=self.min_confidence,
        )
        self.landmarker = vision.PoseLandmarker.create_from_options(options)

    def process_frame(self, frame: np.ndarray) -> List[PosePlayer]:
        """Divide el fotograma en columnas ROI (una por jugador) y procesa cada region de forma independiente."""
        if frame is None or frame.size == 0:
            return []

        h, w = frame.shape[:2]
        players: List[PosePlayer] = []
        slice_w = w // self.num_players

        for p_idx in range(self.num_players):
            x_start = p_idx * slice_w
            x_end = (p_idx + 1) * slice_w if p_idx < self.num_players - 1 else w
            roi = frame[:, x_start:x_end]

            rgb_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2RGB)
            mp_image = self.mp.Image(image_format=self.mp.ImageFormat.SRGB, data=rgb_roi)
            result = self.landmarker.detect(mp_image)

            if not result.pose_landmarks or len(result.pose_landmarks) == 0:
                continue

            raw_kpts = result.pose_landmarks[0]
            keypoints: Dict[str, Keypoint] = {}

            # Offset relativo de la region
            roi_fraction = (x_end - x_start) / float(w)
            roi_offset_x = x_start / float(w)

            all_xs = []
            all_ys = []

            for idx, lm in enumerate(raw_kpts):
                norm_x = roi_offset_x + (lm.x * roi_fraction)
                norm_y = float(lm.y)
                conf = float(lm.presence if hasattr(lm, "presence") else lm.visibility)

                all_xs.append(norm_x)
                all_ys.append(norm_y)

                if idx in MP_INDEX_MAP:
                    keypoints[MP_INDEX_MAP[idx]] = Keypoint(x=norm_x, y=norm_y, confidence=conf)

            # Estimar Bounding Box
            if all_xs and all_ys:
                bbox = (
                    max(0.0, min(all_xs)),
                    max(0.0, min(all_ys)),
                    min(1.0, max(all_xs)),
                    min(1.0, max(all_ys)),
                )
            else:
                bbox = (roi_offset_x, 0.0, roi_offset_x + roi_fraction, 1.0)

            players.append(
                PosePlayer(
                    player_id=p_idx + 1,
                    bbox=bbox,
                    keypoints=keypoints,
                    confidence=1.0,
                )
            )

        return players

    def close(self) -> None:
        """Cierra el detector de MediaPipe."""
        if hasattr(self, "landmarker") and self.landmarker:
            self.landmarker.close()
            self.landmarker = None
