"""Modulo de vision y estimacion de posturas."""

from .backend import Keypoint, PoseEstimationBackend, PosePlayer
from .yolo_adapter import YOLOv8PoseBackend
from .mediapipe_adapter import MediaPipePoseBackend
from .synthetic_adapter import SyntheticPoseBackend

__all__ = [
    "Keypoint",
    "PoseEstimationBackend",
    "PosePlayer",
    "YOLOv8PoseBackend",
    "MediaPipePoseBackend",
    "SyntheticPoseBackend",
]
