"""Adaptador de estimacion de posturas multi-persona con Ultralytics YOLOv8-Pose."""

from typing import Dict, List, Optional
import numpy as np

from .backend import Keypoint, PoseEstimationBackend, PosePlayer

COCO_KEYPOINT_NAMES = [
    "nose",
    "left_eye",
    "right_eye",
    "left_ear",
    "right_ear",
    "left_shoulder",
    "right_shoulder",
    "left_elbow",
    "right_elbow",
    "left_wrist",
    "right_wrist",
    "left_hip",
    "right_hip",
    "left_knee",
    "right_knee",
    "left_ankle",
    "right_ankle",
]


class YOLOv8PoseBackend(PoseEstimationBackend):
    """Motor de deteccion multi-persona en un solo pase usando YOLOv8-Pose."""

    def __init__(self, model_path: str = "yolov8n-pose.pt", min_confidence: float = 0.35, device: Optional[str] = None):
        from ultralytics import YOLO
        self.model_path = model_path
        self.min_confidence = min_confidence
        self.device = device
        self.model = YOLO(model_path)

    def process_frame(self, frame: np.ndarray) -> List[PosePlayer]:
        """Infiere todas las personas en el fotograma y las asigna a los jugadores por su posicion horizontal."""
        if frame is None or frame.size == 0:
            return []

        results = self.model(frame, verbose=False, conf=self.min_confidence, device=self.device)
        if not results or len(results) == 0:
            return []

        result = results[0]
        if result.keypoints is None or result.boxes is None or len(result.boxes) == 0:
            return []

        # Extraer keypoints normalizados y cajas delimitadoras
        kpts_data = result.keypoints.xyn.cpu().numpy()  # [N, 17, 2]
        kpts_conf = (
            result.keypoints.conf.cpu().numpy()
            if result.keypoints.conf is not None
            else np.ones((len(result.boxes), 17), dtype=np.float32)
        )
        boxes_xyxyn = result.boxes.xyxyn.cpu().numpy()  # [N, 4] (x1, y1, x2, y2)
        boxes_conf = result.boxes.conf.cpu().numpy()

        raw_detections = []
        for i in range(len(boxes_xyxyn)):
            bbox = tuple(map(float, boxes_xyxyn[i]))
            center_x = (bbox[0] + bbox[2]) / 2.0

            keypoints: Dict[str, Keypoint] = {}
            for idx, name in enumerate(COCO_KEYPOINT_NAMES):
                x = float(kpts_data[i, idx, 0])
                y = float(kpts_data[i, idx, 1])
                conf = float(kpts_conf[i, idx])
                keypoints[name] = Keypoint(x=x, y=y, confidence=conf)

            raw_detections.append({
                "center_x": center_x,
                "bbox": bbox,
                "keypoints": keypoints,
                "confidence": float(boxes_conf[i]),
            })

        # Ordenar de izquierda a derecha (Jugador 1 a la izquierda, Jugador 2 a la derecha)
        raw_detections.sort(key=lambda d: d["center_x"])

        players: List[PosePlayer] = []
        for idx, det in enumerate(raw_detections):
            players.append(
                PosePlayer(
                    player_id=idx + 1,
                    bbox=det["bbox"],
                    keypoints=det["keypoints"],
                    confidence=det["confidence"],
                )
            )

        return players

    def close(self) -> None:
        """Libera la referencia al modelo."""
        self.model = None
