"""Protocolo de comunicacion y serializacion para multijugador LAN."""

from dataclasses import asdict, dataclass, field
from enum import Enum
import json
import time
from typing import Any, Dict, List, Optional, Tuple


class PacketType(str, Enum):
    JOIN = "JOIN"
    JOIN_ACK = "JOIN_ACK"
    INPUT = "INPUT"
    STATE = "STATE"
    HEARTBEAT = "HEARTBEAT"
    LEAVE = "LEAVE"


@dataclass
class PlayerInputPacket:
    player_id: int
    gesture: str
    timestamp: float = field(default_factory=time.time)
    seq: int = 0
    keypoints: Optional[Dict[str, Tuple[float, float]]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": PacketType.INPUT.value,
            "player_id": self.player_id,
            "gesture": self.gesture,
            "timestamp": self.timestamp,
            "seq": self.seq,
            "keypoints": self.keypoints,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PlayerInputPacket":
        return cls(
            player_id=int(data["player_id"]),
            gesture=str(data["gesture"]),
            timestamp=float(data.get("timestamp", time.time())),
            seq=int(data.get("seq", 0)),
            keypoints=data.get("keypoints"),
        )


@dataclass
class GameStatePacket:
    round_number: int
    round_timer: float
    round_state: str
    winner_id: Optional[int]
    fighters: Dict[int, Dict[str, Any]]
    beams: List[Dict[str, Any]]
    beam_struggle_active: bool
    clash_point: Optional[Tuple[float, float]]
    timestamp: float = field(default_factory=time.time)
    seq: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": PacketType.STATE.value,
            "round_number": self.round_number,
            "round_timer": self.round_timer,
            "round_state": self.round_state,
            "winner_id": self.winner_id,
            "fighters": {str(k): v for k, v in self.fighters.items()},
            "beams": self.beams,
            "beam_struggle_active": self.beam_struggle_active,
            "clash_point": list(self.clash_point) if self.clash_point else None,
            "timestamp": self.timestamp,
            "seq": self.seq,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GameStatePacket":
        raw_fighters = data.get("fighters", {})
        fighters = {int(k): v for k, v in raw_fighters.items()}
        clash = data.get("clash_point")
        clash_tuple = tuple(clash) if clash else None
        return cls(
            round_number=int(data.get("round_number", 1)),
            round_timer=float(data.get("round_timer", 60.0)),
            round_state=str(data.get("round_state", "FIGHTING")),
            winner_id=data.get("winner_id"),
            fighters=fighters,
            beams=list(data.get("beams", [])),
            beam_struggle_active=bool(data.get("beam_struggle_active", False)),
            clash_point=clash_tuple,
            timestamp=float(data.get("timestamp", time.time())),
            seq=int(data.get("seq", 0)),
        )


def encode_packet(data: Dict[str, Any]) -> bytes:
    return json.dumps(data, separators=(",", ":")).encode("utf-8")


def decode_packet(raw: bytes) -> Optional[Dict[str, Any]]:
    try:
        return json.loads(raw.decode("utf-8"))
    except Exception:
        return None
