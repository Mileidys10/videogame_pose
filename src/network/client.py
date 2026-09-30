"""Cliente UDP para conexion a host LAN en VideoGame Pose Combat."""

import socket
import threading
import time
from typing import Any, Dict, Optional, Tuple

from .protocol import (
    GameStatePacket,
    PacketType,
    PlayerInputPacket,
    decode_packet,
    encode_packet,
)


class GameClient:
    def __init__(self, host: str, port: int = 9999):
        self.host = host
        self.port = port
        self.server_addr = (host, port)
        self.sock: Optional[socket.socket] = None
        self.running = False
        self.connected = False
        self.assigned_player_id: Optional[int] = None
        self.latest_state: Optional[GameStatePacket] = None
        self.last_packet_time = 0.0
        self.seq = 0
        self.lock = threading.Lock()
        self.thread: Optional[threading.Thread] = None

    def start(self, timeout: float = 3.0) -> bool:
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.settimeout(0.05)
        self.running = True
        self.thread = threading.Thread(target=self._listen_loop, daemon=True)
        self.thread.start()

        join_bytes = encode_packet({"type": PacketType.JOIN.value, "timestamp": time.time()})
        start_attempt = time.time()
        while time.time() - start_attempt < timeout and not self.connected:
            try:
                self.sock.sendto(join_bytes, self.server_addr)
            except OSError:
                pass
            time.sleep(0.1)

        return self.connected

    def _listen_loop(self) -> None:
        while self.running and self.sock:
            try:
                data, addr = self.sock.recvfrom(4096)
            except socket.timeout:
                continue
            except OSError:
                break

            packet = decode_packet(data)
            if not packet:
                continue

            ptype = packet.get("type")
            now = time.time()

            with self.lock:
                self.last_packet_time = now

                if ptype == PacketType.JOIN_ACK.value:
                    self.connected = True
                    self.assigned_player_id = int(packet.get("player_id", 2))
                    print(f"[NETWORK] Conectado exitosamente como Jugador {self.assigned_player_id}")

                elif ptype == PacketType.STATE.value:
                    self.latest_state = GameStatePacket.from_dict(packet)
                    if not self.connected:
                        self.connected = True

    def send_input(self, gesture: str, keypoints: Optional[Dict[str, Tuple[float, float]]] = None) -> None:
        if not self.running or not self.sock:
            return
        self.seq += 1
        pid = self.assigned_player_id if self.assigned_player_id is not None else 2
        packet = PlayerInputPacket(
            player_id=pid,
            gesture=gesture,
            timestamp=time.time(),
            seq=self.seq,
            keypoints=keypoints,
        )
        try:
            self.sock.sendto(encode_packet(packet.to_dict()), self.server_addr)
        except OSError:
            pass

    def get_latest_state(self) -> Optional[GameStatePacket]:
        with self.lock:
            return self.latest_state

    def is_server_alive(self) -> bool:
        with self.lock:
            return self.connected and (time.time() - self.last_packet_time < 5.0)

    def close(self) -> None:
        self.running = False
        if self.sock:
            try:
                leave_packet = encode_packet({
                    "type": PacketType.LEAVE.value,
                    "player_id": self.assigned_player_id,
                })
                self.sock.sendto(leave_packet, self.server_addr)
                self.sock.close()
            except OSError:
                pass
            self.sock = None
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=0.5)
