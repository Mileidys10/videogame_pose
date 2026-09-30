"""Prueba de integracion LAN: comunicacion cliente-servidor para partida multijugador."""

import time
import unittest

from src.game.combat import CombatEngine
from src.gestures.recognizer import CombatGesture
from src.network.client import GameClient
from src.network.server import GameServer


class TestLanIntegration(unittest.TestCase):
    """Verifica el flujo completo de partida en red local (Host + Client UDP)."""

    def setUp(self):
        self.port = 19995
        self.server = GameServer(host="127.0.0.1", port=self.port)
        self.server.start()
        time.sleep(0.05)

        self.client = GameClient(host="127.0.0.1", port=self.port)
        self.client.start(timeout=1.5)
        time.sleep(0.05)

    def tearDown(self):
        if self.client:
            self.client.close()
        if self.server:
            self.server.close()
        time.sleep(0.05)

    def test_full_lan_combat_cycle(self):
        # 1. Verificar asignacion de ID al conectarse
        self.assertEqual(self.client.assigned_player_id, 2)
        self.assertIn(2, self.server.assigned_players.values())

        # 2. Cliente P2 envia accion de combate
        self.client.send_input(gesture="KAMEHAMEHA")
        time.sleep(0.05)

        remote_input = self.server.get_remote_input(player_id=2)
        self.assertIsNotNone(remote_input)
        self.assertEqual(remote_input.gesture, "KAMEHAMEHA")

        # 3. Servidor orquesta combate y genera Beam Struggle
        engine = CombatEngine(num_players=2)
        engine.fighters[1].ki = 80.0
        engine.fighters[2].ki = 60.0

        gestures = {
            1: CombatGesture.KAMEHAMEHA,
            2: CombatGesture(remote_input.gesture),
        }
        engine.update_gestures(gestures, {})
        self.assertEqual(len(engine.active_beams), 2)

        # Hacer colisionar los rayos en el servidor
        b1, b2 = engine.active_beams[0], engine.active_beams[1]
        b1.head_x = 0.55
        b2.head_x = 0.45
        engine.update_physics(0.02)
        self.assertTrue(engine.beam_struggle_active)

        # 4. Servidor transmite estado sincronizado al cliente
        state_pkt = engine.to_game_state_packet()
        self.server.broadcast_state(state_pkt)
        time.sleep(0.05)

        # 5. Cliente recibe y valida el estado autoritativo
        client_state = self.client.get_latest_state()
        self.assertIsNotNone(client_state)
        self.assertTrue(client_state.beam_struggle_active)
        self.assertEqual(len(client_state.fighters), 2)
        self.assertEqual(client_state.round_number, 1)


if __name__ == "__main__":
    unittest.main()
