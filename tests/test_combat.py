"""Pruebas unitarias para el motor de combate, proyectiles, choque de rayos y asaltos."""

import unittest
from src.game.combat import BeamProjectile, CombatEngine
from src.gestures.recognizer import CombatGesture
from src.vision.synthetic_adapter import SyntheticPoseBackend


class TestCombatEngine(unittest.TestCase):
    """Verifica reglas de juego, daño de rayo laser, escudos, choque de rayos, melee y asaltos."""

    def setUp(self):
        self.engine = CombatEngine(num_players=2)
        self.backend = SyntheticPoseBackend(num_players=2)

    def test_initial_state(self):
        self.assertEqual(len(self.engine.fighters), 2)
        p1 = self.engine.fighters[1]
        p2 = self.engine.fighters[2]
        self.assertEqual(p1.hp, 100.0)
        self.assertEqual(p2.hp, 100.0)
        self.assertEqual(self.engine.round_number, 1)
        self.assertEqual(self.engine.round_state, "FIGHTING")

    def test_kamehameha_firing_and_ki_consumption(self):
        p1 = self.engine.fighters[1]
        p1.ki = 50.0

        gestures = {1: CombatGesture.KAMEHAMEHA, 2: CombatGesture.IDLE}
        poses = {p.player_id: p for p in self.backend.process_frame()}

        self.engine.update_gestures(gestures, poses)
        self.assertTrue(p1.is_firing_beam)
        self.assertEqual(len(self.engine.active_beams), 1)

        initial_ki = p1.ki
        self.engine.update_physics(0.5)
        self.assertLess(p1.ki, initial_ki)

    def test_shield_blocking_reduces_damage(self):
        p1 = self.engine.fighters[1]
        p2 = self.engine.fighters[2]
        p1.ki = 80.0

        gestures = {1: CombatGesture.KAMEHAMEHA, 2: CombatGesture.SHIELD}
        poses = {p.player_id: p for p in self.backend.process_frame()}
        self.engine.update_gestures(gestures, poses)

        self.assertTrue(p2.is_blocking)
        shield = self.engine.shields[2]
        self.assertTrue(shield.active)

        beam = self.engine.active_beams[0]
        beam.head_x = p2.screen_x
        beam.head_y = p2.screen_y

        initial_hp = p2.hp
        self.engine.update_physics(0.1)

        damage_taken = initial_hp - p2.hp
        self.assertGreater(damage_taken, 0.0)
        self.assertLess(damage_taken, 2.0)

    def test_melee_punch_at_close_range(self):
        p1 = self.engine.fighters[1]
        p2 = self.engine.fighters[2]
        # Acercar los luchadores a distancia cuerpo a cuerpo
        p1.screen_x = 0.45
        p1.facing_direction = 1.0
        p2.screen_x = 0.55

        initial_hp = p2.hp
        initial_x = p2.screen_x

        # P1 lanza un golpe melee (PUNCH)
        gestures = {1: CombatGesture.PUNCH, 2: CombatGesture.IDLE}
        poses = {p.player_id: p for p in self.backend.process_frame()}

        self.engine.update_gestures(gestures, poses)

        # Verificar daño y retroceso (knockback)
        self.assertLess(p2.hp, initial_hp)
        self.assertGreater(p2.screen_x, initial_x)
        self.assertGreater(p1.melee_cooldown, 0.0)

    def test_beam_struggle_clash(self):
        p1 = self.engine.fighters[1]
        p2 = self.engine.fighters[2]
        p1.ki = 80.0
        p2.ki = 40.0

        # Ambos jugadores disparan Kamehameha
        gestures = {1: CombatGesture.KAMEHAMEHA, 2: CombatGesture.KAMEHAMEHA}
        poses = {p.player_id: p for p in self.backend.process_frame()}
        self.engine.update_gestures(gestures, poses)

        self.assertEqual(len(self.engine.active_beams), 2)
        beam1 = self.engine.active_beams[0]
        beam2 = self.engine.active_beams[1]

        # Forzar que los haces se encuentren en el medio
        beam1.head_x = 0.52
        beam2.head_x = 0.48

        self.engine.update_physics(0.1)

        # Debe activarse el choque de rayos
        self.assertTrue(self.engine.beam_struggle_active)
        self.assertIsNotNone(self.engine.clash_point)
        # Como P1 tiene 80 de Ki y P2 tiene 40 de Ki, P1 empuja el choque hacia la derecha (> 0.50)
        self.assertGreater(self.engine.clash_point[0], 0.49)

    def test_round_timer_expiration_and_scoring(self):
        p1 = self.engine.fighters[1]
        p2 = self.engine.fighters[2]
        p1.hp = 80.0
        p2.hp = 40.0

        # Forzar temporizador a punto de vencer
        self.engine.round_timer = 0.05
        self.engine.update_physics(0.1)

        # Al vencer el tiempo, el de mayor HP gana el asalto
        self.assertEqual(self.engine.round_state, "ROUND_OVER")
        self.assertEqual(self.engine.round_winner_id, 1)
        self.assertEqual(p1.rounds_won, 1)

    def test_match_victory_best_of_three(self):
        p1 = self.engine.fighters[1]
        p1.rounds_won = 1

        # P2 cae en KO en el segundo asalto
        p2 = self.engine.fighters[2]
        p2.hp = 10.0
        p2.take_damage(20.0, blocked=False)
        self.assertTrue(p2.is_knocked_out)

        self.engine._end_round_by_ko()
        self.assertEqual(p1.rounds_won, 2)

        # Avanzar el tiempo post-asalto para gatillar decision de torneo
        self.engine.update_physics(2.6)
        self.assertEqual(self.engine.round_state, "MATCH_OVER")
        self.assertEqual(self.engine.winner_id, 1)



    def test_uppercut_breaks_shield(self):
        p1 = self.engine.fighters[1]
        p2 = self.engine.fighters[2]
        p1.screen_x = 0.45
        p1.facing_direction = 1.0
        p2.screen_x = 0.52

        # P2 esta bloqueando con escudo
        p2.is_blocking = True
        shield = self.engine.shields[2]
        shield.active = True
        initial_hp = p2.hp

        # P1 lanza UPPERCUT
        gestures = {1: CombatGesture.UPPERCUT, 2: CombatGesture.SHIELD}
        poses = {p.player_id: p for p in self.backend.process_frame()}
        self.engine.update_gestures(gestures, poses)

        # El escudo debe ser ROTO
        self.assertFalse(p2.is_blocking)
        self.assertFalse(shield.active)
        self.assertLess(p2.hp, initial_hp)
        self.assertGreater(p2.hit_stun, 0.0)

    def test_sixty_seven_taunt_confusion(self):
        p1 = self.engine.fighters[1]
        p2 = self.engine.fighters[2]

        gestures = {1: CombatGesture.SIXTY_SEVEN, 2: CombatGesture.IDLE}
        poses = {p.player_id: p for p in self.backend.process_frame()}
        self.engine.update_gestures(gestures, poses)

        # El rival queda confundido/paralizado temporalmente
        self.assertGreaterEqual(p2.hit_stun, 1.5)
        self.assertGreater(len(self.engine.particles), 0)

    def test_hadoken_projectile_damage(self):
        p1 = self.engine.fighters[1]
        p2 = self.engine.fighters[2]
        p1.ki = 60.0
        p1.screen_x = 0.2
        p1.facing_direction = 1.0
        p2.screen_x = 0.8
        initial_hp = p2.hp

        gestures = {1: CombatGesture.HADOKEN, 2: CombatGesture.IDLE}
        poses = {p.player_id: p for p in self.backend.process_frame()}
        self.engine.update_gestures(gestures, poses)

        self.assertEqual(len(self.engine.active_energy_balls), 1)
        ball = self.engine.active_energy_balls[0]
        self.assertLess(p1.ki, 60.0)

        # Forzar que la bola alcance al rival
        ball.x = p2.screen_x
        ball.y = p2.screen_y
        self.engine.update_physics(0.01)

        self.assertLess(p2.hp, initial_hp)
        self.assertEqual(len(self.engine.active_energy_balls), 0)

    def test_dodge_roll_evades_damage(self):
        p1 = self.engine.fighters[1]
        p2 = self.engine.fighters[2]
        p1.screen_x = 0.45
        p1.facing_direction = 1.0
        p2.screen_x = 0.50
        initial_hp = p2.hp

        # P2 realiza evasion acrobatica (DODGE_ROLL)
        gestures_dodge = {1: CombatGesture.IDLE, 2: CombatGesture.DODGE_ROLL}
        poses = {p.player_id: p for p in self.backend.process_frame()}
        self.engine.update_gestures(gestures_dodge, poses)
        self.assertTrue(p2.is_dodging)
        self.assertGreater(p2.dodge_timer, 0.0)

        # P1 intenta golpear cuerpo a cuerpo durante la evasion
        gestures_punch = {1: CombatGesture.PUNCH, 2: CombatGesture.IDLE}
        self.engine.update_gestures(gestures_punch, poses)

        # P2 no recibe ningun dano debido a la invulnerabilidad de dodge
        self.assertEqual(p2.hp, initial_hp)

    def test_spirit_bomb_charge_and_impact(self):
        p1 = self.engine.fighters[1]
        p2 = self.engine.fighters[2]
        p1.ki = 80.0
        p1.screen_x = 0.20
        p2.screen_x = 0.80
        initial_hp = p2.hp

        # Cargar Spirit Bomb
        gestures_charge = {1: CombatGesture.SPIRIT_BOMB, 2: CombatGesture.IDLE}
        poses = {p.player_id: p for p in self.backend.process_frame()}
        for _ in range(12):
            self.engine.update_gestures(gestures_charge, poses)

        self.assertGreater(len(self.engine.active_spirit_bombs), 0)
        bomb = self.engine.active_spirit_bombs[0]
        self.assertGreater(p1.spirit_bomb_charge_time, 0.4)

        # Soltar la bomba (cambiar a IDLE)
        gestures_release = {1: CombatGesture.IDLE, 2: CombatGesture.IDLE}
        self.engine.update_gestures(gestures_release, poses)
        self.assertEqual(bomb.state, "FALLING")

        # Simular impacto de la Genkidama sobre P2
        bomb.x = p2.screen_x
        bomb.y = 0.52
        self.engine.update_physics(0.05)

        self.assertLess(p2.hp, initial_hp)
        self.assertGreater(self.engine.screen_trauma, 0.0)

    def test_taunt_cross_damage_boost(self):
        p1 = self.engine.fighters[1]
        p2 = self.engine.fighters[2]
        p1.screen_x = 0.45
        p1.facing_direction = 1.0
        p2.screen_x = 0.50
        initial_hp = p2.hp

        # P1 ejecuta TAUNT_CROSS
        gestures_taunt = {1: CombatGesture.TAUNT_CROSS, 2: CombatGesture.IDLE}
        self.engine.update_gestures(gestures_taunt, {})
        self.assertGreater(p1.damage_boost_timer, 0.0)

        # P1 lanza un PUNCH con buff de dano (+30%)
        gestures_punch = {1: CombatGesture.PUNCH, 2: CombatGesture.IDLE}
        self.engine.update_gestures(gestures_punch, {})

        # Dano normal es 18.0; con +30% es 23.4
        damage_taken = initial_hp - p2.hp
        self.assertAlmostEqual(damage_taken, 23.4, delta=0.5)

if __name__ == "__main__":
    unittest.main()
