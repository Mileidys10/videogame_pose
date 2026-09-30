"""Pruebas unitarias para el modulo de Inteligencia Artificial (FighterAI)."""

import unittest
from src.ai.simple_ai import FighterAI
from src.game.combat import BeamProjectile, CombatEngine
from src.gestures.recognizer import CombatGesture


class TestFighterAI(unittest.TestCase):
    """Verifica las reglas heurísticas y niveles de dificultad de la IA."""

    def setUp(self):
        self.engine = CombatEngine(num_players=2)

    def test_ai_initialization_difficulties(self):
        ai_easy = FighterAI(player_id=2, difficulty="EASY")
        self.assertEqual(ai_easy.difficulty, "EASY")

        ai_norm = FighterAI(player_id=2, difficulty="normal")
        self.assertEqual(ai_norm.difficulty, "NORMAL")

        ai_hard = FighterAI(player_id=2, difficulty="HARD")
        self.assertEqual(ai_hard.difficulty, "HARD")

        ai_fallback = FighterAI(player_id=2, difficulty="IMPOSSIBLE")
        self.assertEqual(ai_fallback.difficulty, "NORMAL")

    def test_ai_normal_defends_against_incoming_beam(self):
        ai = FighterAI(player_id=2, difficulty="NORMAL")
        # Simular rayo que se aproxima disparado por P1
        beam = BeamProjectile(
            owner_id=1,
            start_x=0.2,
            start_y=0.55,
            head_x=0.6,
            head_y=0.55,
            direction=1.0,
        )
        self.engine.active_beams.append(beam)

        # Forzar actualizacion inmediata
        ai._decision_timer = 0.0
        decision = ai.update(0.1, self.engine)

        # Debe responder con escudo o evasion acrobatica
        self.assertIn(decision, (CombatGesture.SHIELD, CombatGesture.DODGE_ROLL))

    def test_ai_hard_counters_shield_with_uppercut(self):
        ai = FighterAI(player_id=2, difficulty="HARD")
        p1 = self.engine.fighters[1]
        p2 = self.engine.fighters[2]

        # P1 esta bloqueando con escudo cerca de P2
        p1.screen_x = 0.48
        p2.screen_x = 0.52
        p1.is_blocking = True

        ai._decision_timer = 0.0
        decision = ai.update(0.1, self.engine)

        # La IA en nivel Hard debe contraatacar rompiendo escudo con UPPERCUT
        self.assertEqual(decision, CombatGesture.UPPERCUT)

    def test_ai_charges_ki_when_empty(self):
        ai = FighterAI(player_id=2, difficulty="NORMAL")
        p2 = self.engine.fighters[2]
        p2.ki = 5.0  # Ki agotado
        p1 = self.engine.fighters[1]
        p1.screen_x = 0.1
        p2.screen_x = 0.9  # Distancia segura

        ai._decision_timer = 0.0
        decision = ai.update(0.1, self.engine)

        self.assertEqual(decision, CombatGesture.CHARGE_KI)


if __name__ == "__main__":
    unittest.main()
