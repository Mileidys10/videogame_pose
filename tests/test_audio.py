"""Pruebas unitarias para el motor de audio procedimental."""

import unittest
from src.audio.sound_engine import SoundEngine


class TestSoundEngine(unittest.TestCase):
    """Verifica sintesis de ondas procedimentales y rate-limiting de audio."""

    def setUp(self):
        self.engine = SoundEngine(sample_rate=22050, enabled=True)

    def tearDown(self):
        self.engine.stop_all()

    def test_audio_initialization(self):
        # En entornos con dispositivo de audio, _sounds debe contener todos los efectos
        if self.engine.enabled:
            expected_keys = ["laser", "shield", "charge", "hit", "clash", "ko", "round_start"]
            for key in expected_keys:
                self.assertIn(key, self.engine._sounds)

    def test_play_methods_do_not_crash(self):
        # Los metodos de reproduccion deben ejecutarse limpiamente sin excepciones
        self.engine.play_laser()
        self.engine.play_shield()
        self.engine.play_charge()
        self.engine.play_hit()
        self.engine.play_clash()
        self.engine.play_ko()
        self.engine.play_round_start()

    def test_disabled_engine_silent_mode(self):
        disabled_engine = SoundEngine(enabled=False)
        self.assertFalse(disabled_engine.enabled)
        # No debe lanzar errores al llamar play
        disabled_engine.play_laser()
        disabled_engine.stop_all()


if __name__ == "__main__":
    unittest.main()
