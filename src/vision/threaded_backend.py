"""Inferencia de vision desacoplada en hilo secundario (ThreadedPoseBackend)."""

import threading
import time
from typing import List, Optional
import numpy as np

from .backend import PoseEstimationBackend, PosePlayer


class ThreadedPoseBackend(PoseEstimationBackend):
    """Envuelve un backend de pose en un hilo daemon para no bloquear los 60 FPS del juego."""

    def __init__(self, backend: PoseEstimationBackend):
        self.inner_backend = backend
        self.latest_frame: Optional[np.ndarray] = None
        self.latest_poses: List[PosePlayer] = []
        self.running = True
        self.has_new_frame = threading.Event()
        self.lock = threading.Lock()
        self.worker = threading.Thread(target=self._inference_loop, daemon=True)
        self.worker.start()

    def _inference_loop(self) -> None:
        while self.running:
            self.has_new_frame.wait(timeout=0.05)
            if not self.running:
                break
            with self.lock:
                frame = self.latest_frame
                self.has_new_frame.clear()

            if frame is not None:
                poses = self.inner_backend.process_frame(frame)
                with self.lock:
                    self.latest_poses = poses

    def process_frame(self, frame: Optional[np.ndarray]) -> List[PosePlayer]:
        if frame is not None:
            with self.lock:
                self.latest_frame = frame
                self.has_new_frame.set()
        with self.lock:
            return list(self.latest_poses)

    def close(self) -> None:
        self.running = False
        self.has_new_frame.set()
        if self.worker.is_alive():
            self.worker.join(timeout=0.5)
        self.inner_backend.close()
