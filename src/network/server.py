"""Servidor UDP Host no-bloqueante para partidas LAN."""

import socket
import threading
import time
from typing import Dict, Optional, Tuple

from .protocol import (
    GameStatePacket,
    PacketType,
    PlayerInputPacket,
    decode_packet,
    encode_packet,
)


class GameServer:
    def __init__(self, host: str = "0.0.0.0", port: int = 9999):
        self.host = host
        self.port = port
        self.sock: Optional[socket.socket] = None
        self.running = False
        self.clients: Dict[Tuple[str, int], float] = {}
        self.assigned_players: Dict[Tuple[str, int], int] = {}
        self.remote_inputs: Dict[int, PlayerInputPacket] = {}
        self.lock = threading.Lock()
        self.thread: Optional[threading.Thread] = None
        self.seq = 0

    def start(self) -> None:
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((self.host, self.port))
        self.sock.settimeout(0.05)
        self.running = True
        self.thread = threading.Thread(target=self._listen_loop, daemon=True)
        self.thread.start()
        print(f"[NETWORK] Servidor UDP escuchando en {self.host}:{self.port}")

    def _listen_loop(self) -> None:
        while self.running and self.sock:
            try:
                data, addr = self.sock.recvfrom(4096)
            except socket.timeout:
                continue
            except OSError:
                break

            packet_data = decode_packet(data)
            if not packet_data:
                continue

            ptype = packet_data.get("type")
            now = time.time()

            with self.lock:
                self.clients[addr] = now

                if ptype == PacketType.JOIN.value:
                    if addr not in self.assigned_players:
                        pid = 2 if 2 not in self.assigned_players.values() else len(self.assigned_players) + 2
                        self.assigned_players[addr] = pid
                    else:
                        pid = self.assigned_players[addr]

                    ack = {
                        "type": PacketType.JOIN_ACK.value,
                        "player_id": pid,
                        "server_time": now,
                    }
                    try:
                        self.sock.sendto(encode_packet(ack), addr)
                    except OSError:
                        pass
                    print(f"[NETWORK] Cliente conectado desde {addr}, asignado como Jugador {pid}")

                elif ptype == PacketType.INPUT.value:
                    inp = PlayerInputPacket.from_dict(packet_data)
                    if addr in self.assigned_players:
                        inp.player_id = self.assigned_players[addr]
                    self.remote_inputs[inp.player_id] = inp

                elif ptype == PacketType.HEARTBEAT.value:
                    pass

                elif ptype == PacketType.LEAVE.value:
                    self.clients.pop(addr, None)
                    pid = self.assigned_players.pop(addr, None)
                    if pid:
                        self.remote_inputs.pop(pid, None)
                        print(f"[NETWORK] Cliente P{pid} ({addr}) desconectado")

    def broadcast_state(self, state: GameStatePacket) -> None:
        if not self.running or not self.sock:
            return
        self.seq += 1
        state.seq = self.seq
        packet_bytes = encode_packet(state.to_dict())

        with self.lock:
            now = time.time()
            dead_clients = [addr for addr, last_seen in self.clients.items() if now - last_seen > 8.0]
            for addr in dead_clients:
                self.clients.pop(addr, None)
                pid = self.assigned_players.pop(addr, None)
                if pid:
                    self.remote_inputs.pop(pid, None)
                    print(f"[NETWORK] Cliente P{pid} desconectado por timeout")

            for addr in list(self.clients.keys()):
                try:
                    self.sock.sendto(packet_bytes, addr)
                except OSError:
                    pass

    def get_remote_input(self, player_id: int) -> Optional[PlayerInputPacket]:
        with self.lock:
            return self.remote_inputs.get(player_id)

    def has_connected_clients(self) -> bool:
        with self.lock:
            return len(self.clients) > 0

    def close(self) -> None:
        self.running = False
        if self.sock:
            try:
                self.sock.close()
            except OSError:
                pass
            self.sock = None
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=0.5)
