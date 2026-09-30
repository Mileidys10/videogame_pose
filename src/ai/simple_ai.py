"""Modulo de Inteligencia Artificial para oponente virtual (1v1 vs IA)."""

import random
from typing import Optional

from ..game.combat import CombatEngine, FighterState
from ..gestures.recognizer import CombatGesture


class FighterAI:
    """Controlador de IA heuristica reactiva con 3 niveles de dificultad."""

    def __init__(self, player_id: int = 2, difficulty: str = "NORMAL"):
        self.player_id = player_id
        self.difficulty = difficulty.upper()
        if self.difficulty not in ("EASY", "NORMAL", "HARD"):
            self.difficulty = "NORMAL"

        self.current_gesture: CombatGesture = CombatGesture.IDLE
        self._decision_timer: float = 0.0

        # Tiempos de reaccion segun dificultad
        self._delay_map = {
            "EASY": 1.2,
            "NORMAL": 0.5,
            "HARD": 0.18,
        }

    def update(self, dt: float, engine: CombatEngine) -> CombatGesture:
        """Evalua la situacion del combate y retorna la accion decidida por la IA."""
        self._decision_timer -= dt
        if self._decision_timer > 0.0:
            return self.current_gesture

        # Reiniciar temporizador de reaccion
        base_delay = self._delay_map.get(self.difficulty, 0.5)
        self._decision_timer = random.uniform(base_delay * 0.8, base_delay * 1.2)

        ai_fighter = engine.fighters.get(self.player_id)
        if not ai_fighter or ai_fighter.is_knocked_out or ai_fighter.hit_stun > 0.0:
            self.current_gesture = CombatGesture.IDLE
            return CombatGesture.IDLE

        # Identificar rival directo
        opponents = [f for f in engine.fighters.values() if f.player_id != self.player_id and not f.is_knocked_out]
        if not opponents:
            self.current_gesture = CombatGesture.IDLE
            return CombatGesture.IDLE

        opp = opponents[0]
        dist = abs(opp.screen_x - ai_fighter.screen_x)

        # 1. MODO EASY (Comportamiento relajado, 40% aleatorio, recarga Ki lento)
        if self.difficulty == "EASY":
            if random.random() < 0.35:
                # Accion aleatoria o reposo
                self.current_gesture = random.choice([CombatGesture.IDLE, CombatGesture.CHARGE_KI, CombatGesture.PUNCH])
            elif opp.is_firing_beam and random.random() < 0.60:
                self.current_gesture = CombatGesture.SHIELD
            elif dist <= 0.22:
                self.current_gesture = CombatGesture.PUNCH
            elif ai_fighter.ki < 30.0:
                self.current_gesture = CombatGesture.CHARGE_KI
            else:
                self.current_gesture = CombatGesture.HADOKEN if random.random() < 0.5 else CombatGesture.IDLE
            return self.current_gesture

        # 2. MODO NORMAL (Reacciones logicas equilibradas)
        if self.difficulty == "NORMAL":
            # Si el oponente lanza rayo continuo o Hadoken, defenderse
            incoming_beam = any(b.active and b.owner_id != self.player_id for b in engine.active_beams)
            incoming_ball = any(b.active and b.owner_id != self.player_id for b in engine.active_energy_balls)

            if incoming_beam or incoming_ball:
                if random.random() < 0.75:
                    self.current_gesture = CombatGesture.SHIELD
                else:
                    self.current_gesture = CombatGesture.DODGE_ROLL if ai_fighter.dodge_cooldown <= 0.0 else CombatGesture.SHIELD
                return self.current_gesture

            # Combate cuerpo a cuerpo
            if dist <= 0.24:
                if opp.is_blocking and ai_fighter.uppercut_cooldown <= 0.0:
                    self.current_gesture = CombatGesture.UPPERCUT
                elif ai_fighter.melee_cooldown <= 0.0:
                    self.current_gesture = CombatGesture.PUNCH
                else:
                    self.current_gesture = CombatGesture.SHIELD
                return self.current_gesture

            # Gestion de Ki a media y larga distancia
            if ai_fighter.ki < 25.0:
                self.current_gesture = CombatGesture.CHARGE_KI
            elif ai_fighter.ki >= 60.0 and random.random() < 0.65:
                self.current_gesture = CombatGesture.KAMEHAMEHA
            elif ai_fighter.ki >= 25.0 and ai_fighter.hadoken_cooldown <= 0.0:
                self.current_gesture = CombatGesture.HADOKEN
            else:
                self.current_gesture = CombatGesture.CHARGE_KI if ai_fighter.ki < 70.0 else CombatGesture.IDLE

            return self.current_gesture

        # 3. MODO HARD (Tactico, castiga escudos con Uppercut, esquiva proyectiles con Dodge Roll, activa Taunt Cross)
        # Contraataque de evasion inmediata
        incoming_threat = any(b.active and b.owner_id != self.player_id for b in engine.active_beams) or                           any(b.active and b.owner_id != self.player_id for b in engine.active_energy_balls)

        if incoming_threat:
            if ai_fighter.dodge_cooldown <= 0.0:
                self.current_gesture = CombatGesture.DODGE_ROLL
                return self.current_gesture
            else:
                self.current_gesture = CombatGesture.SHIELD
                return self.current_gesture

        # Si el rival esta bloqueando, castigo garantizado con UPPERCUT
        if dist <= 0.28 and opp.is_blocking and ai_fighter.uppercut_cooldown <= 0.0:
            self.current_gesture = CombatGesture.UPPERCUT
            return self.current_gesture

        # Si el rival esta aturdido o en hit-stun, aprovechar para activar bufo o Genkidama
        if opp.hit_stun > 0.5:
            if ai_fighter.damage_boost_timer <= 0.0 and ai_fighter.taunt_cross_cooldown <= 0.0:
                self.current_gesture = CombatGesture.TAUNT_CROSS
                return self.current_gesture
            elif ai_fighter.ki >= 40.0 and ai_fighter.spirit_bomb_cooldown <= 0.0:
                self.current_gesture = CombatGesture.SPIRIT_BOMB
                return self.current_gesture

        # Si estamos cerca, castigar con Melee rapido
        if dist <= 0.22 and ai_fighter.melee_cooldown <= 0.0:
            self.current_gesture = CombatGesture.PUNCH
            return self.current_gesture

        # Larga distancia
        if ai_fighter.ki >= 70.0 and random.random() < 0.70:
            self.current_gesture = CombatGesture.KAMEHAMEHA
        elif ai_fighter.ki >= 25.0 and ai_fighter.hadoken_cooldown <= 0.0:
            self.current_gesture = CombatGesture.HADOKEN
        elif ai_fighter.ki < 50.0:
            self.current_gesture = CombatGesture.CHARGE_KI
        elif ai_fighter.taunt_cooldown <= 0.0 and random.random() < 0.20:
            # Provocacion 67 estrategica
            self.current_gesture = CombatGesture.SIXTY_SEVEN
        else:
            self.current_gesture = CombatGesture.CHARGE_KI

        return self.current_gesture
