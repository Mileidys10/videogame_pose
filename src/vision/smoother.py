"""Suavizador de keypoints con interpolacion temporal Lerp/EMA para eliminar jitter."""

from typing import Dict, List, Optional, Tuple
from .backend import Keypoint, PosePlayer


class KeypointSmoother:
    """Filtro de suavizado temporal para keypoints corporales."""

    def __init__(self, alpha: float = 0.65, snap_threshold: float = 0.25):
        self.alpha = alpha
        self.snap_threshold = snap_threshold
        self.history: Dict[int, Dict[str, Tuple[float, float]]] = {}

    def smooth(self, players: List[PosePlayer]) -> List[PosePlayer]:
        smoothed_players: List[PosePlayer] = []
        for player in players:
            pid = player.player_id
            if pid not in self.history:
                self.history[pid] = {}

            smoothed_keypoints: Dict[str, Keypoint] = {}
            for name, kp in player.keypoints.items():
                if kp.confidence < 0.2:
                    smoothed_keypoints[name] = kp
                    continue

                if name in self.history[pid]:
                    prev_x, prev_y = self.history[pid][name]
                    dist_sq = (kp.x - prev_x) ** 2 + (kp.y - prev_y) ** 2
                    if dist_sq > self.snap_threshold ** 2:
                        new_x, new_y = kp.x, kp.y
                    else:
                        new_x = self.alpha * kp.x + (1.0 - self.alpha) * prev_x
                        new_y = self.alpha * kp.y + (1.0 - self.alpha) * prev_y
                else:
                    new_x, new_y = kp.x, kp.y

                self.history[pid][name] = (new_x, new_y)
                smoothed_keypoints[name] = Keypoint(
                    x=new_x,
                    y=new_y,
                    confidence=kp.confidence,
                )

            smoothed_players.append(
                PosePlayer(
                    player_id=player.player_id,
                    bbox=player.bbox,
                    keypoints=smoothed_keypoints,
                    confidence=player.confidence,
                )
            )
        return smoothed_players

    def reset(self) -> None:
        self.history.clear()
