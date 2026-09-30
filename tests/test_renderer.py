"""Pruebas unitarias para el renderizador multimedia en modo headless."""

import unittest
import numpy as np
from src.game.combat import CombatEngine
from src.ui.renderer import PygameRenderer
from src.vision.synthetic_adapter import SyntheticPoseBackend


class TestRendererHeadless(unittest.TestCase):
    """Verifica inicializacion y pipeline de dibujo de Pygame-CE fuera de pantalla."""

    def setUp(self):
        self.renderer = PygameRenderer(width=640, height=360, headless=True)
        self.engine = CombatEngine(num_players=2)
        self.backend = SyntheticPoseBackend(num_players=2)

    def tearDown(self):
        self.renderer.close()

    def test_render_frame_without_camera(self):
        poses = {p.player_id: p for p in self.backend.process_frame()}
        # No debe lanzar excepciones
        self.renderer.render_frame(
            camera_frame=None,
            engine=self.engine,
            poses=poses,
            fps=60.0,
            backend_name="TEST_MOCK",
        )
        self.assertIsNotNone(self.renderer.screen)

    def test_render_frame_with_dummy_camera(self):
        dummy_frame = np.zeros((360, 640, 3), dtype=np.uint8)
        poses = {p.player_id: p for p in self.backend.process_frame()}
        self.renderer.render_frame(
            camera_frame=dummy_frame,
            engine=self.engine,
            poses=poses,
            fps=59.5,
            backend_name="TEST_MOCK",
        )
        self.assertEqual(self.renderer.screen.get_width(), 640)
        self.assertEqual(self.renderer.screen.get_height(), 360)


    def test_render_with_guide_overlay(self):
        poses = {p.player_id: p for p in self.backend.process_frame()}
        self.renderer.show_guide = True
        self.renderer.render_frame(
            camera_frame=None,
            engine=self.engine,
            poses=poses,
            fps=60.0,
            backend_name="TEST_GUIDE",
        )
        self.assertTrue(self.renderer.show_guide)
        self.assertIsNotNone(self.renderer.screen)


if __name__ == "__main__":
    unittest.main()
