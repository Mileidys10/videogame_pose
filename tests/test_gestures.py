"""Pruebas unitarias para clasificacion y debounce de gestos de combate."""

import unittest
from src.gestures.recognizer import CombatGesture, GestureRecognizer
from src.vision.synthetic_adapter import SyntheticPoseBackend


class TestGestureRecognizer(unittest.TestCase):
    """Verifica reconocimiento de Kamehameha, Escudo y Carga de Ki."""

    def setUp(self):
        self.recognizer = GestureRecognizer(debounce_frames=3)
        self.backend = SyntheticPoseBackend(num_players=2)

    def test_classify_kamehameha(self):
        self.backend.set_player_pose(1, "KAMEHAMEHA")
        players = self.backend.process_frame()
        player1 = players[0]

        gesture = self.recognizer.classify_instant(player1)
        self.assertEqual(gesture, CombatGesture.KAMEHAMEHA)

    def test_classify_shield(self):
        self.backend.set_player_pose(2, "SHIELD")
        players = self.backend.process_frame()
        player2 = players[1]

        gesture = self.recognizer.classify_instant(player2)
        self.assertEqual(gesture, CombatGesture.SHIELD)

    def test_classify_charge_ki(self):
        self.backend.set_player_pose(1, "CHARGE_KI")
        players = self.backend.process_frame()
        player1 = players[0]

        gesture = self.recognizer.classify_instant(player1)
        self.assertEqual(gesture, CombatGesture.CHARGE_KI)

    def test_classify_idle(self):
        self.backend.set_player_pose(1, "IDLE")
        players = self.backend.process_frame()
        player1 = players[0]

        gesture = self.recognizer.classify_instant(player1)
        self.assertEqual(gesture, CombatGesture.IDLE)

    def test_debounce_stabilization(self):
        self.backend.set_player_pose(1, "KAMEHAMEHA")
        players = self.backend.process_frame()
        player1 = players[0]

        # Enviar 3 frames consecutivos de Kamehameha
        for _ in range(3):
            consolidated = self.recognizer.update_and_get_gesture(player1)

        self.assertEqual(consolidated, CombatGesture.KAMEHAMEHA)



    def test_classify_uppercut(self):
        self.backend.set_player_pose(1, "UPPERCUT")
        players = self.backend.process_frame()
        gesture = self.recognizer.classify_instant(players[0])
        self.assertEqual(gesture, CombatGesture.UPPERCUT)

    def test_classify_sixty_seven(self):
        self.backend.set_player_pose(1, "SIXTY_SEVEN")
        players = self.backend.process_frame()
        gesture = self.recognizer.classify_instant(players[0])
        self.assertEqual(gesture, CombatGesture.SIXTY_SEVEN)

    def test_classify_hadoken(self):
        self.backend.set_player_pose(1, "HADOKEN")
        players = self.backend.process_frame()
        gesture = self.recognizer.classify_instant(players[0])
        self.assertEqual(gesture, CombatGesture.HADOKEN)

    def test_classify_spirit_bomb(self):
        self.backend.set_player_pose(1, "SPIRIT_BOMB")
        players = self.backend.process_frame()
        gesture = self.recognizer.classify_instant(players[0])
        self.assertEqual(gesture, CombatGesture.SPIRIT_BOMB)

    def test_classify_dodge_roll(self):
        self.backend.set_player_pose(1, "DODGE_ROLL")
        players = self.backend.process_frame()
        gesture = self.recognizer.classify_instant(players[0])
        self.assertEqual(gesture, CombatGesture.DODGE_ROLL)

    def test_classify_taunt_cross(self):
        self.backend.set_player_pose(1, "TAUNT_CROSS")
        players = self.backend.process_frame()
        gesture = self.recognizer.classify_instant(players[0])
        self.assertEqual(gesture, CombatGesture.TAUNT_CROSS)

if __name__ == "__main__":
    unittest.main()
