"""Contratos e interfaces para la capa de vision y estimacion de posturas."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
import math
import numpy as np


@dataclass
class Keypoint:
    """Representa un punto clave corporal en coordenadas normalizadas [0.0, 1.0]."""
    x: float
    y: float
    confidence: float = 1.0

    def distance_to(self, other: "Keypoint") -> float:
        """Calcula la distancia euclidiana 2D normalizada hacia otro punto."""
        return math.hypot(self.x - other.x, self.y - other.y)


@dataclass
class PosePlayer:
    """Modelo canónico de un combatiente detectado en el fotograma."""
    player_id: int
    bbox: Tuple[float, float, float, float]  # (x1, y1, x2, y2) normalizado
    keypoints: Dict[str, Keypoint] = field(default_factory=dict)
    confidence: float = 1.0

    @property
    def shoulder_width(self) -> float:
        """Ancho de hombros utilizado como unidad de escala corporal."""
        ls = self.keypoints.get("left_shoulder")
        rs = self.keypoints.get("right_shoulder")
        if ls and rs and ls.confidence > 0.2 and rs.confidence > 0.2:
            dist = ls.distance_to(rs)
            return max(dist, 0.05)
        # Valor por defecto seguro si no se detectan ambos hombros
        return 0.15

    @property
    def torso_center(self) -> Tuple[float, float]:
        """Calcula el centro geometrico del torso."""
        ls = self.keypoints.get("left_shoulder")
        rs = self.keypoints.get("right_shoulder")
        lh = self.keypoints.get("left_hip")
        rh = self.keypoints.get("right_hip")

        points = [p for p in (ls, rs, lh, rh) if p and p.confidence > 0.2]
        if points:
            avg_x = sum(p.x for p in points) / len(points)
            avg_y = sum(p.y for p in points) / len(points)
            return (avg_x, avg_y)

        # Respaldo con centro de bounding box
        x1, y1, x2, y2 = self.bbox
        return ((x1 + x2) / 2.0, (y1 + y2) / 2.0)

    def get_keypoint(self, name: str) -> Optional[Keypoint]:
        """Obtiene un punto clave si cumple con un umbral minimo de confianza."""
        kp = self.keypoints.get(name)
        if kp and kp.confidence >= 0.2:
            return kp
        return None


class PoseEstimationBackend(ABC):
    """Interfaz abstracta (Estrategia) para motores de estimacion de pose."""

    @abstractmethod
    def process_frame(self, frame: np.ndarray) -> List[PosePlayer]:
        """Procesa un fotograma BGR/RGB y retorna la lista ordenada de jugadores."""
        pass

    @abstractmethod
    def close(self) -> None:
        """Libera recursos del modelo o hardware."""
        pass
