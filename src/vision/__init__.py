"""Modulo de vision y estimacion de posturas."""

from .backend import Keypoint, PoseEstimationBackend, PosePlayer
from .synthetic_adapter import SyntheticPoseBackend

try:
    from .yolo_adapter import YOLOv8PoseBackend
except ImportError:
    YOLOv8PoseBackend = None

try:
    from .mediapipe_adapter import MediaPipePoseBackend
except ImportError:
    MediaPipePoseBackend = None

__all__ = [
    "Keypoint",
    "PoseEstimationBackend",
    "PosePlayer",
    "YOLOv8PoseBackend",
    "MediaPipePoseBackend",
    "SyntheticPoseBackend",
]
