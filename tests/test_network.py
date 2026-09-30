"""Pruebas unitarias para el modulo de red y optimizaciones de vision."""

import time
import unittest

from src.game.combat import CombatEngine
from src.gestures.recognizer import CombatGesture
from src.network.client import GameClient
from src.network.protocol import (
    GameStatePacket,
    PacketType,
    PlayerInputPacket,
    decode_packet,
    encode_packet,
)
from src.network.server import GameServer
from src.vision.backend import Keypoint, PosePlayer
from src.vision.smoother import KeypointSmoother
from src.vision.synthetic_adapter import SyntheticPoseBackend
from src.vision.threaded_backend import ThreadedPoseBackend


class TestNetworkModule(unittest.TestCase):
    def test_packet_serialization_roundtrip(self):
        # 1. PlayerInputPacket
        input_packet = PlayerInputPacket(
            player_id=2,
            gesture="KAMEHAMEHA",
            timestamp=123456.78,
            seq=42,
            keypoints={"wrist_r": (0.45, 0.55)},
        )
        raw_bytes = encode_packet(input_packet.to_dict())
        decoded_dict = decode_packet(raw_bytes)
        self.assertIsNotNone(decoded_dict)
        reconstructed_input = PlayerInputPacket.from_dict(decoded_dict)
        self.assertEqual(reconstructed_input.player_id, 2)
        self.assertEqual(reconstructed_input.gesture, "KAMEHAMEHA")
        self.assertEqual(reconstructed_input.seq, 42)

        # 2. GameStatePacket
        state_packet = GameStatePacket(
            round_number=2,
            round_timer=45.5,
            round_state="FIGHTING",
            winner_id=None,
            fighters={
                1: {"hp": 85.0, "ki": 40.0, "gesture": "SHIELD", "rounds_won": 1},
                2: {"hp": 60.0, "ki": 90.0, "gesture": "CHARGE_KI", "rounds_won": 0},
            },
            beams=[{"owner_id": 1, "head_x": 0.5, "head_y": 0.5, "direction": 1.0, "active": True}],
            beam_struggle_active=True,
            clash_point=(0.52, 0.48),
        )
        raw_state_bytes = encode_packet(state_packet.to_dict())
        decoded_state_dict = decode_packet(raw_state_bytes)
        self.assertIsNotNone(decoded_state_dict)
        reconstructed_state = GameStatePacket.from_dict(decoded_state_dict)
        self.assertEqual(reconstructed_state.round_number, 2)
        self.assertAlmostEqual(reconstructed_state.round_timer, 45.5)
        self.assertTrue(reconstructed_state.beam_struggle_active)
        self.assertEqual(reconstructed_state.clash_point, (0.52, 0.48))
        self.assertEqual(len(reconstructed_state.fighters), 2)
        self.assertEqual(reconstructed_state.fighters[1]["hp"], 85.0)

    def test_server_and_client_udp_exchange(self):
        port = 19998
        server = GameServer(host="127.0.0.1", port=port)
        server.start()

        client = GameClient(host="127.0.0.1", port=port)
        connected = client.start(timeout=1.5)
        self.assertTrue(connected, "El cliente deberia conectarse exitosamente al servidor UDP")
        self.assertEqual(client.assigned_player_id, 2)

        # Enviar input desde cliente
        client.send_input(gesture="CHARGE_KI")
        time.sleep(0.1)

        remote_inp = server.get_remote_input(player_id=2)
        self.assertIsNotNone(remote_inp)
        self.assertEqual(remote_inp.gesture, "CHARGE_KI")

        # Broadcast de estado desde servidor
        state = GameStatePacket(
            round_number=1,
            round_timer=58.2,
            round_state="FIGHTING",
            winner_id=None,
            fighters={1: {"hp": 100.0}, 2: {"hp": 90.0}},
            beams=[],
            beam_struggle_active=False,
            clash_point=None,
        )
        server.broadcast_state(state)
        time.sleep(0.1)

        latest_client_state = client.get_latest_state()
        self.assertIsNotNone(latest_client_state)
        self.assertAlmostEqual(latest_client_state.round_timer, 58.2)

        client.close()
        server.close()

    def test_threaded_vision_backend(self):
        inner_backend = SyntheticPoseBackend(num_players=2)
        threaded = ThreadedPoseBackend(inner_backend)

        # Primera consulta (puede retornar lista inicial o vacia sin bloquear)
        poses = threaded.process_frame(None)
        self.assertIsInstance(poses, list)

        # Enviar frame dummy
        import numpy as np
        dummy_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        threaded.process_frame(dummy_frame)
        time.sleep(0.1)

        poses_after = threaded.process_frame(dummy_frame)
        self.assertEqual(len(poses_after), 2)
        threaded.close()

    def test_keypoint_smoother(self):
        smoother = KeypointSmoother(alpha=0.5, snap_threshold=0.3)
        kp_raw = {"nose": Keypoint(x=0.5, y=0.5, confidence=0.9)}
        p1 = PosePlayer(player_id=1, bbox=(0.4, 0.4, 0.2, 0.2), keypoints=kp_raw, confidence=0.9)

        # Primer frame: sin suavizado previo
        smoothed_1 = smoother.smooth([p1])
        self.assertAlmostEqual(smoothed_1[0].keypoints["nose"].x, 0.5)

        # Segundo frame: movimiento leve (0.5 -> 0.6). Con alpha=0.5, promedio = 0.55
        p2 = PosePlayer(
            player_id=1,
            bbox=(0.4, 0.4, 0.2, 0.2),
            keypoints={"nose": Keypoint(x=0.6, y=0.5, confidence=0.9)},
            confidence=0.9,
        )
        smoothed_2 = smoother.smooth([p2])
        self.assertAlmostEqual(smoothed_2[0].keypoints["nose"].x, 0.55)

        # Tercer frame: teletransporte brusco (0.55 -> 0.95, delta=0.4 > snap_threshold=0.3)
        p3 = PosePlayer(
            player_id=1,
            bbox=(0.8, 0.4, 0.2, 0.2),
            keypoints={"nose": Keypoint(x=0.95, y=0.5, confidence=0.9)},
            confidence=0.9,
        )
        smoothed_3 = smoother.smooth([p3])
        # Snap directo
        self.assertAlmostEqual(smoothed_3[0].keypoints["nose"].x, 0.95)

    def test_combat_engine_state_packet_roundtrip(self):
        from src.game.combat import BeamProjectile
        engine1 = CombatEngine(num_players=2)
        engine1.fighters[1].hp = 64.0
        engine1.fighters[1].ki = 88.0
        engine1.fighters[1].current_gesture = CombatGesture.KAMEHAMEHA
        engine1.active_beams.append(
            BeamProjectile(
                owner_id=1,
                start_x=0.2,
                start_y=0.55,
                head_x=0.45,
                head_y=0.55,
                direction=1.0,
                active=True,
            )
        )

        packet = engine1.to_game_state_packet()
        self.assertEqual(packet.fighters[1]["hp"], 64.0)
        self.assertEqual(len(packet.beams), 1)

        engine2 = CombatEngine(num_players=2)
        engine2.apply_game_state_packet(packet)
        self.assertEqual(engine2.fighters[1].hp, 64.0)
        self.assertEqual(engine2.fighters[1].ki, 88.0)
        self.assertEqual(engine2.fighters[1].current_gesture, CombatGesture.KAMEHAMEHA)
        self.assertEqual(len(engine2.active_beams), 1)


if __name__ == "__main__":
    unittest.main()
