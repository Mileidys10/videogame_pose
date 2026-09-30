"""Pruebas unitarias para modelos y backend de vision."""

import unittest
from src.vision.backend import Keypoint, PosePlayer
from src.vision.synthetic_adapter import SyntheticPoseBackend


class TestVisionBackend(unittest.TestCase):
    """Verifica modelos de datos de puntos clave y adaptador sintetico."""

    def test_keypoint_distance(self):
        kp1 = Keypoint(x=0.0, y=0.0, confidence=1.0)
        kp2 = Keypoint(x=3.0, y=4.0, confidence=1.0)
        self.assertAlmostEqual(kp1.distance_to(kp2), 5.0)

    def test_pose_player_properties(self):
        kpts = {
            "left_shoulder": Keypoint(x=0.4, y=0.3, confidence=0.9),
            "right_shoulder": Keypoint(x=0.6, y=0.3, confidence=0.9),
            "left_hip": Keypoint(x=0.4, y=0.7, confidence=0.9),
            "right_hip": Keypoint(x=0.6, y=0.7, confidence=0.9),
        }
        player = PosePlayer(player_id=1, bbox=(0.3, 0.2, 0.7, 0.8), keypoints=kpts)
        self.assertAlmostEqual(player.shoulder_width, 0.2)
        cx, cy = player.torso_center
        self.assertAlmostEqual(cx, 0.5)
        self.assertAlmostEqual(cy, 0.5)

    def test_synthetic_backend_players(self):
        backend = SyntheticPoseBackend(num_players=2)
        players = backend.process_frame()
        self.assertEqual(len(players), 2)
        self.assertEqual(players[0].player_id, 1)
        self.assertEqual(players[1].player_id, 2)
        self.assertIn("nose", players[0].keypoints)
        self.assertIn("left_wrist", players[0].keypoints)


if __name__ == "__main__":
    unittest.main()
