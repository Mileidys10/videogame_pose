"""Motor de combate, gestion de proyectiles, choque de rayos, escudos y sistema de asaltos."""

from dataclasses import dataclass, field
import random
from typing import Dict, List, Optional, Tuple

from ..gestures.recognizer import CombatGesture
from ..vision.backend import PosePlayer


@dataclass
class Particle:
    """Particula visual energetica para chispas, auras y explosiones."""
    x: float
    y: float
    vx: float
    vy: float
    life: float
    max_life: float
    color: Tuple[int, int, int]
    radius: float


@dataclass
class BeamProjectile:
    """Rayo laser continuo / Kamehameha proyectado horizontalmente entre jugadores."""
    owner_id: int
    start_x: float
    start_y: float
    head_x: float
    head_y: float
    direction: float  # +1.0 hacia la derecha, -1.0 hacia la izquierda
    speed: float = 1.6
    damage_per_sec: float = 40.0
    color: Tuple[int, int, int] = (60, 220, 255)
    core_color: Tuple[int, int, int] = (255, 255, 255)
    thickness: float = 0.05
    active: bool = True
    collided: bool = False

    def update(self, dt: float) -> None:
        if not self.active:
            return
        self.head_x += self.direction * self.speed * dt
        if self.head_x > 1.15 or self.head_x < -0.15:
            self.active = False


@dataclass
class SpiritBombProjectile:
    """Esfera colosal de energia concentrada (Genkidama / Spirit Bomb)."""
    owner_id: int
    x: float
    y: float
    target_x: float
    radius: float = 0.06
    charge_progress: float = 0.0
    state: str = "CHARGING"  # "CHARGING", "FALLING", "EXPLODED"
    damage: float = 45.0
    active: bool = True
    color: Tuple[int, int, int] = (100, 230, 255)

    def update(self, dt: float) -> None:
        if self.state == "FALLING":
            # Desciende diagonalmente hacia target_x
            dx = self.target_x - self.x
            self.x += (dx * 2.0) * dt
            self.y += 0.40 * dt
            if self.y >= 0.55:
                self.state = "EXPLODED"
                self.active = False


@dataclass
class EnergyBallProjectile:
    """Proyectil balistico esferico rapido (Hadoken / Plasma Ball)."""
    owner_id: int
    x: float
    y: float
    vx: float
    radius: float = 0.035
    damage: float = 24.0
    active: bool = True
    color: Tuple[int, int, int] = (0, 230, 255)

    def update(self, dt: float) -> None:
        self.x += self.vx * dt
        if self.x < -0.15 or self.x > 1.15:
            self.active = False


@dataclass
class ShieldEffect:
    """Escudo energetico de absorcion de dano."""
    owner_id: int
    center_x: float
    center_y: float
    radius: float = 0.12
    active: bool = False
    color: Tuple[int, int, int] = (255, 215, 0)


@dataclass
class FighterStats:
    """Metricas de rendimiento y estadisticas acumuladas por combatiente."""
    damage_dealt: float = 0.0
    damage_taken: float = 0.0
    attacks_thrown: int = 0
    hits_landed: int = 0
    blocks_successful: int = 0
    dodges_executed: int = 0
    taunts_performed: int = 0

    @property
    def accuracy(self) -> float:
        if self.attacks_thrown <= 0:
            return 0.0
        return min(100.0, (self.hits_landed / self.attacks_thrown) * 100.0)


@dataclass
class FighterState:
    """Estado y atributos de combate de un jugador."""
    player_id: int
    name: str
    max_hp: float = 100.0
    hp: float = 100.0
    max_ki: float = 100.0
    ki: float = 50.0
    current_gesture: CombatGesture = CombatGesture.IDLE
    is_blocking: bool = False
    is_charging: bool = False
    is_firing_beam: bool = False
    is_knocked_out: bool = False
    facing_direction: float = 1.0
    screen_x: float = 0.2
    screen_y: float = 0.55
    hit_stun: float = 0.0
    melee_cooldown: float = 0.0
    uppercut_cooldown: float = 0.0
    taunt_cooldown: float = 0.0
    hadoken_cooldown: float = 0.0
    spirit_bomb_cooldown: float = 0.0
    spirit_bomb_charge_time: float = 0.0
    dodge_cooldown: float = 0.0
    dodge_timer: float = 0.0
    is_dodging: bool = False
    taunt_cross_cooldown: float = 0.0
    damage_boost_timer: float = 0.0
    rounds_won: int = 0
    color_theme: Tuple[int, int, int] = (255, 100, 30)

    def take_damage(self, amount: float, blocked: bool = False) -> float:
        if self.is_dodging:
            # Evasion perfecta: dano cero durante ventana de dodge
            return 0.0
        effective_damage = amount * 0.15 if blocked else amount
        self.hp = max(0.0, self.hp - effective_damage)
        if self.hp <= 0.0:
            self.is_knocked_out = True
        if not blocked:
            self.hit_stun = 0.18
        return effective_damage

    def charge_ki(self, amount: float) -> None:
        if not self.is_knocked_out:
            self.ki = min(self.max_ki, self.ki + amount)

    def consume_ki(self, amount: float) -> bool:
        if self.ki >= amount:
            self.ki -= amount
            return True
        return False


class CombatEngine:
    """Motor de orquestacion de combate, proyectiles, colisiones, asaltos y audio."""

    def __init__(self, num_players: int = 2, sound_engine: Optional[object] = None):
        self.num_players = num_players
        self.sound_engine = sound_engine
        self.fighters: Dict[int, FighterState] = {}
        self.active_beams: List[BeamProjectile] = []
        self.active_energy_balls: List[EnergyBallProjectile] = []
        self.active_spirit_bombs: List[SpiritBombProjectile] = []
        self.shields: Dict[int, ShieldEffect] = {}
        self.particles: List[Particle] = []
        self.screen_trauma: float = 0.0
        self.stats: Dict[int, FighterStats] = {1: FighterStats(), 2: FighterStats()}

        # Sistema de Asaltos y Cronometro
        self.round_timer: float = 60.0
        self.round_number: int = 1
        self.max_rounds_to_win: int = 2
        self.round_state: str = "FIGHTING"
        self.round_winner_id: Optional[int] = None
        self.round_over_elapsed: float = 0.0
        self.winner_id: Optional[int] = None

        # Choque de Rayos (Beam Struggle)
        self.beam_struggle_active: bool = False
        self.clash_point: Optional[Tuple[float, float]] = None

        self._init_fighters()

    def _init_fighters(self) -> None:
        self.fighters.clear()
        self.active_beams.clear()
        self.active_energy_balls.clear()
        self.active_spirit_bombs.clear()
        self.shields.clear()
        self.particles.clear()
        self.screen_trauma = 0.0
        self.stats = {i + 1: FighterStats() for i in range(self.num_players)}
        self.winner_id = None
        self.round_winner_id = None
        self.round_timer = 60.0
        self.round_state = "FIGHTING"
        self.round_over_elapsed = 0.0
        self.beam_struggle_active = False
        self.clash_point = None

        names = ["Goku (P1)", "Vegeta (P2)", "Piccolo (P3)", "Trunks (P4)"]
        colors = [
            (255, 120, 20),
            (60, 140, 255),
            (50, 205, 50),
            (186, 85, 211),
        ]

        spacing = 1.0 / (self.num_players + 1)
        for i in range(self.num_players):
            pid = i + 1
            screen_x = (i + 1) * spacing
            facing = 1.0 if screen_x < 0.5 else -1.0
            fighter = FighterState(
                player_id=pid,
                name=names[i] if i < len(names) else f"Combatiente {pid}",
                facing_direction=facing,
                screen_x=screen_x,
                screen_y=0.55,
                color_theme=colors[i % len(colors)],
            )
            self.fighters[pid] = fighter
            self.shields[pid] = ShieldEffect(
                owner_id=pid,
                center_x=screen_x,
                center_y=0.55,
            )

        if self.sound_engine and hasattr(self.sound_engine, "play_round_start"):
            self.sound_engine.play_round_start()

    def spawn_particles(
        self,
        x: float,
        y: float,
        count: int,
        color: Tuple[int, int, int],
        speed_range: Tuple[float, float] = (0.2, 0.6),
        max_life: float = 0.4,
    ) -> None:
        for _ in range(count):
            angle = random.uniform(0.0, 6.28318)
            spd = random.uniform(speed_range[0], speed_range[1])
            vx = math_cos(angle) * spd
            vy = math_sin(angle) * spd
            self.particles.append(
                Particle(
                    x=x,
                    y=y,
                    vx=vx,
                    vy=vy,
                    life=max_life,
                    max_life=max_life,
                    color=color,
                    radius=random.uniform(0.005, 0.015),
                )
            )

    def update_gestures(self, detected_gestures: Dict[int, CombatGesture], pose_players: Dict[int, PosePlayer]) -> None:
        if self.round_state != "FIGHTING":
            return

        for pid, gesture in detected_gestures.items():
            fighter = self.fighters.get(pid)
            if not fighter or fighter.is_knocked_out or fighter.hit_stun > 0.0:
                continue

            fighter.current_gesture = gesture

            pose = pose_players.get(pid)
            if pose:
                tc_x, tc_y = pose.torso_center
                fighter.screen_x = max(0.08, min(0.92, tc_x))
                fighter.screen_y = min(0.70, max(0.30, tc_y))

                opponents = [f for f in self.fighters.values() if f.player_id != pid and not f.is_knocked_out]
                if opponents:
                    opponents.sort(key=lambda opp: abs(opp.screen_x - fighter.screen_x))
                    target = opponents[0]
                    fighter.facing_direction = 1.0 if target.screen_x > fighter.screen_x else -1.0

            # 1. Escudo
            if gesture == CombatGesture.SHIELD:
                fighter.is_blocking = True
                shield = self.shields.get(pid)
                if shield:
                    shield.active = True
                    shield.center_x = fighter.screen_x + (fighter.facing_direction * 0.05)
                    shield.center_y = fighter.screen_y
                if self.sound_engine and hasattr(self.sound_engine, "play_shield"):
                    self.sound_engine.play_shield()
            else:
                fighter.is_blocking = False
                shield = self.shields.get(pid)
                if shield:
                    shield.active = False

            # 2. Carga Ki
            if gesture == CombatGesture.CHARGE_KI:
                fighter.is_charging = True
                if self.sound_engine and hasattr(self.sound_engine, "play_charge"):
                    self.sound_engine.play_charge()
            else:
                fighter.is_charging = False

            # 3. Kamehameha
            if gesture == CombatGesture.KAMEHAMEHA:
                if fighter.ki >= 15.0:
                    fighter.is_firing_beam = True
                    existing_beam = next((b for b in self.active_beams if b.owner_id == pid and b.active), None)
                    if not existing_beam:
                        beam_color = (60, 220, 255) if pid == 1 else (255, 100, 255)
                        origin_x = fighter.screen_x + (fighter.facing_direction * 0.08)
                        origin_y = fighter.screen_y
                        self.active_beams.append(
                            BeamProjectile(
                                owner_id=pid,
                                start_x=origin_x,
                                start_y=origin_y,
                                head_x=origin_x,
                                head_y=origin_y,
                                direction=fighter.facing_direction,
                                color=beam_color,
                            )
                        )
                        if self.sound_engine and hasattr(self.sound_engine, "play_laser"):
                            self.sound_engine.play_laser()
                else:
                    fighter.is_firing_beam = False
            else:
                fighter.is_firing_beam = False

            # 4. Melee y Nuevos Ataques
            if gesture == CombatGesture.PUNCH and fighter.melee_cooldown <= 0.0:
                self._handle_melee_punch(fighter)
            elif gesture == CombatGesture.UPPERCUT and fighter.uppercut_cooldown <= 0.0:
                self._handle_uppercut(fighter)
            elif gesture == CombatGesture.SIXTY_SEVEN and fighter.taunt_cooldown <= 0.0:
                self._handle_sixty_seven(fighter)
            elif gesture == CombatGesture.HADOKEN and fighter.hadoken_cooldown <= 0.0:
                self._handle_hadoken(fighter)
            elif gesture == CombatGesture.SPIRIT_BOMB and fighter.spirit_bomb_cooldown <= 0.0:
                self._handle_spirit_bomb(fighter)
            elif gesture == CombatGesture.DODGE_ROLL and fighter.dodge_cooldown <= 0.0:
                self._handle_dodge_roll(fighter)
            elif gesture == CombatGesture.TAUNT_CROSS and fighter.taunt_cross_cooldown <= 0.0:
                self._handle_taunt_cross(fighter)

            # Si dejo de hacer SPIRIT_BOMB pero estaba cargando una bomba, lanzarla
            if gesture != CombatGesture.SPIRIT_BOMB and fighter.spirit_bomb_charge_time > 0.0:
                self._release_spirit_bomb(fighter)

    def _handle_melee_punch(self, fighter: FighterState) -> None:
        fighter.melee_cooldown = 0.45
        if fighter.player_id in self.stats:
            self.stats[fighter.player_id].attacks_thrown += 1
        reach = 0.22

        for opp in self.fighters.values():
            if opp.player_id == fighter.player_id or opp.is_knocked_out:
                continue

            dx = (opp.screen_x - fighter.screen_x) * fighter.facing_direction
            if 0.0 <= dx <= reach:
                multiplier = 1.30 if fighter.damage_boost_timer > 0.0 else 1.0
                dmg = opp.take_damage(18.0 * multiplier, blocked=opp.is_blocking)
                if fighter.player_id in self.stats:
                    self.stats[fighter.player_id].hits_landed += 1
                    self.stats[fighter.player_id].damage_dealt += dmg
                if opp.player_id in self.stats:
                    self.stats[opp.player_id].damage_taken += dmg
                self.screen_trauma = min(1.0, self.screen_trauma + 0.25)
                opp.screen_x = max(0.08, min(0.92, opp.screen_x + fighter.facing_direction * 0.05))
                self.spawn_particles(opp.screen_x, opp.screen_y, count=8, color=(255, 200, 50))
                if opp.hp <= 0.0:
                    opp.is_knocked_out = True
                if self.sound_engine and hasattr(self.sound_engine, "play_hit"):
                    self.sound_engine.play_hit()

    def _handle_uppercut(self, fighter: FighterState) -> None:
        fighter.uppercut_cooldown = 1.2
        if fighter.player_id in self.stats:
            self.stats[fighter.player_id].attacks_thrown += 1
        reach = 0.25

        for opp in self.fighters.values():
            if opp.player_id == fighter.player_id or opp.is_knocked_out:
                continue

            dx = (opp.screen_x - fighter.screen_x) * fighter.facing_direction
            if 0.0 <= dx <= reach:
                if opp.is_blocking:
                    opp.is_blocking = False
                    opp.hp = max(0.0, opp.hp - 24.0)
                    opp.hit_stun = 0.45
                    shield = self.shields.get(opp.player_id)
                    if shield:
                        shield.active = False
                    self.spawn_particles(opp.screen_x, opp.screen_y, count=16, color=(255, 215, 0), speed_range=(0.4, 0.9))
                else:
                    opp.hp = max(0.0, opp.hp - 20.0)
                    opp.hit_stun = 0.35
                    opp.screen_y = max(0.25, opp.screen_y - 0.06)
                    self.spawn_particles(opp.screen_x, opp.screen_y, count=10, color=(255, 60, 60))

                opp.screen_x = max(0.08, min(0.92, opp.screen_x + fighter.facing_direction * 0.08))
                if opp.hp <= 0.0:
                    opp.is_knocked_out = True
                if self.sound_engine and hasattr(self.sound_engine, "play_hit"):
                    self.sound_engine.play_hit()

    def _handle_sixty_seven(self, fighter: FighterState) -> None:
        fighter.taunt_cooldown = 10.0
        if fighter.player_id in self.stats:
            self.stats[fighter.player_id].taunts_performed += 1
        for opp in self.fighters.values():
            if opp.player_id != fighter.player_id and not opp.is_knocked_out:
                opp.hit_stun = max(opp.hit_stun, 2.0)

        for _ in range(25):
            rx = random.uniform(0.1, 0.9)
            ry = random.uniform(0.0, 0.2)
            self.particles.append(
                Particle(
                    x=rx,
                    y=ry,
                    vx=random.uniform(-0.05, 0.05),
                    vy=random.uniform(0.3, 0.7),
                    life=0.8,
                    max_life=0.8,
                    color=(255, 215, 0),
                    radius=0.012,
                )
            )

    def _handle_hadoken(self, fighter: FighterState) -> None:
        if fighter.consume_ki(20.0):
            if fighter.player_id in self.stats:
                self.stats[fighter.player_id].attacks_thrown += 1
            fighter.hadoken_cooldown = 1.0
            direction = fighter.facing_direction
            start_x = fighter.screen_x + (direction * 0.08)
            ball = EnergyBallProjectile(
                owner_id=fighter.player_id,
                x=start_x,
                y=fighter.screen_y,
                vx=direction * 1.8,
                damage=24.0,
                color=(0, 220, 255) if fighter.player_id == 1 else (255, 80, 220),
            )
            self.active_energy_balls.append(ball)
            if self.sound_engine and hasattr(self.sound_engine, "play_laser"):
                self.sound_engine.play_laser()

    def _handle_spirit_bomb(self, fighter: FighterState) -> None:
        """Carga progresiva de la Genkidama / Spirit Bomb."""
        if fighter.ki < 25.0:
            return

        opponents = [f for f in self.fighters.values() if f.player_id != fighter.player_id and not f.is_knocked_out]
        target_x = opponents[0].screen_x if opponents else (fighter.screen_x + fighter.facing_direction * 0.4)

        bomb = next((b for b in self.active_spirit_bombs if b.owner_id == fighter.player_id and b.state == "CHARGING"), None)
        if not bomb:
            bomb = SpiritBombProjectile(
                owner_id=fighter.player_id,
                x=fighter.screen_x,
                y=fighter.screen_y - 0.22,
                target_x=target_x,
                radius=0.04,
                charge_progress=0.1,
                state="CHARGING",
            )
            self.active_spirit_bombs.append(bomb)

        fighter.spirit_bomb_charge_time += 0.05
        fighter.consume_ki(0.6)
        bomb.charge_progress = min(1.0, fighter.spirit_bomb_charge_time / 1.0)
        bomb.radius = min(0.10, 0.04 + bomb.charge_progress * 0.06)
        bomb.target_x = target_x
        self.spawn_particles(bomb.x, bomb.y, count=3, color=(120, 230, 255), speed_range=(0.1, 0.3))

        if bomb.charge_progress >= 1.0:
            self._release_spirit_bomb(fighter)

    def _release_spirit_bomb(self, fighter: FighterState) -> None:
        """Lanza la Genkidama acumulada hacia el oponente."""
        bomb = next((b for b in self.active_spirit_bombs if b.owner_id == fighter.player_id and b.state == "CHARGING"), None)
        if bomb:
            if fighter.spirit_bomb_charge_time >= 0.4:
                bomb.state = "FALLING"
                fighter.spirit_bomb_cooldown = 4.0
                if self.sound_engine and hasattr(self.sound_engine, "play_laser"):
                    self.sound_engine.play_laser()
            else:
                bomb.active = False
                self.active_spirit_bombs.remove(bomb)
        fighter.spirit_bomb_charge_time = 0.0

    def _handle_dodge_roll(self, fighter: FighterState) -> None:
        """Evasion acrobatica con invulnerabilidad temporal (0.4s)."""
        if fighter.player_id in self.stats:
            self.stats[fighter.player_id].dodges_executed += 1
        fighter.dodge_cooldown = 1.6
        fighter.dodge_timer = 0.45
        fighter.is_dodging = True
        dash_dir = -fighter.facing_direction if fighter.screen_x > 0.5 else fighter.facing_direction
        fighter.screen_x = max(0.08, min(0.92, fighter.screen_x + dash_dir * 0.06))
        self.spawn_particles(fighter.screen_x, fighter.screen_y, count=8, color=(200, 240, 255), speed_range=(0.1, 0.4))

    def _handle_taunt_cross(self, fighter: FighterState) -> None:
        """Provocacion con brazos cruzados que otorga +30% de dano por 8 segundos."""
        if fighter.player_id in self.stats:
            self.stats[fighter.player_id].taunts_performed += 1
        fighter.taunt_cross_cooldown = 10.0
        fighter.damage_boost_timer = 8.0
        self.spawn_particles(fighter.screen_x, fighter.screen_y, count=16, color=(255, 80, 50), speed_range=(0.2, 0.7))

    def update_physics(self, dt: float) -> None:
        if self.round_state == "MATCH_OVER":
            return

        if self.round_state == "ROUND_OVER":
            self.round_over_elapsed += dt
            if self.round_over_elapsed >= 2.5:
                if self.round_winner_id:
                    w = self.fighters.get(self.round_winner_id)
                    if w and w.rounds_won >= self.max_rounds_to_win:
                        self.round_state = "MATCH_OVER"
                        self.winner_id = self.round_winner_id
                        return
                self._start_next_round()
            return

        # Cooldowns y Timers de Estados Temporales
        for f in self.fighters.values():
            if f.melee_cooldown > 0.0:
                f.melee_cooldown = max(0.0, f.melee_cooldown - dt)
            if f.uppercut_cooldown > 0.0:
                f.uppercut_cooldown = max(0.0, f.uppercut_cooldown - dt)
            if f.taunt_cooldown > 0.0:
                f.taunt_cooldown = max(0.0, f.taunt_cooldown - dt)
            if f.hadoken_cooldown > 0.0:
                f.hadoken_cooldown = max(0.0, f.hadoken_cooldown - dt)
            if f.spirit_bomb_cooldown > 0.0:
                f.spirit_bomb_cooldown = max(0.0, f.spirit_bomb_cooldown - dt)
            if f.dodge_cooldown > 0.0:
                f.dodge_cooldown = max(0.0, f.dodge_cooldown - dt)
            if f.dodge_timer > 0.0:
                f.dodge_timer = max(0.0, f.dodge_timer - dt)
            f.is_dodging = (f.dodge_timer > 0.0)
            if f.taunt_cross_cooldown > 0.0:
                f.taunt_cross_cooldown = max(0.0, f.taunt_cross_cooldown - dt)
            if f.damage_boost_timer > 0.0:
                f.damage_boost_timer = max(0.0, f.damage_boost_timer - dt)

        # Decaimiento del Screen Trauma (Screen Shake)
        if self.screen_trauma > 0.0:
            self.screen_trauma = max(0.0, self.screen_trauma - dt * 1.5)

        # Cronometro
        self.round_timer = max(0.0, self.round_timer - dt)
        if self.round_timer <= 0.0:
            self._end_round_by_time()
            return

        # Hit stun, carga Ki y consumo de Ki por disparo de rayo continuo
        for f in self.fighters.values():
            if f.hit_stun > 0.0:
                f.hit_stun = max(0.0, f.hit_stun - dt)
            if f.is_charging and not f.is_knocked_out:
                f.charge_ki(15.0 * dt)
            if f.is_firing_beam and not f.is_knocked_out:
                if not f.consume_ki(12.0 * dt):
                    f.is_firing_beam = False
                    for b in self.active_beams:
                        if b.owner_id == f.player_id:
                            b.active = False

        # Rayos Laser
        for beam in self.active_beams:
            beam.update(dt)

        # Choque de rayos (Beam Struggle)
        active_fighting_beams = [b for b in self.active_beams if b.active]
        if len(active_fighting_beams) >= 2:
            b1 = active_fighting_beams[0]
            b2 = active_fighting_beams[1]
            if (b1.direction > 0 and b2.direction < 0 and b1.head_x >= b2.head_x) or (
                b2.direction > 0 and b1.direction < 0 and b2.head_x >= b1.head_x
            ):
                self.beam_struggle_active = True
                f1 = self.fighters.get(b1.owner_id)
                f2 = self.fighters.get(b2.owner_id)
                ki1 = f1.ki if f1 else 50.0
                ki2 = f2.ki if f2 else 50.0
                total_ki = max(1.0, ki1 + ki2)
                push = (ki1 - ki2) / total_ki
                clash_x = max(0.15, min(0.85, 0.50 + push * 0.15))
                self.clash_point = (clash_x, 0.55)
                b1.head_x = clash_x
                b2.head_x = clash_x
                self.spawn_particles(clash_x, 0.55, count=4, color=(255, 255, 255))
            else:
                self.beam_struggle_active = False
                self.clash_point = None
        else:
            self.beam_struggle_active = False
            self.clash_point = None

        # Colision continua de segmento de rayo contra luchadores
        if not self.beam_struggle_active:
            for beam in self.active_beams:
                if not beam.active:
                    continue

                for opp in self.fighters.values():
                    if opp.player_id == beam.owner_id or opp.is_knocked_out:
                        continue

                    # Verificar si el oponente esta dentro del segmento [start_x, head_x]
                    min_x = min(beam.start_x, beam.head_x) - 0.05
                    max_x = max(beam.start_x, beam.head_x) + 0.05
                    if min_x <= opp.screen_x <= max_x:
                        effective_dmg = opp.take_damage(beam.damage_per_sec * dt, blocked=opp.is_blocking)
                        hit_color = (255, 215, 0) if opp.is_blocking else beam.color
                        self.spawn_particles(beam.head_x, beam.head_y, count=3, color=hit_color)

                        if opp.is_knocked_out:
                            self._end_round_by_ko()
                            return

        # Hadoken Balls
        surviving_balls = []
        for ball in self.active_energy_balls:
            ball.update(dt)
            if not ball.active:
                continue

            hit = False
            for opp in self.fighters.values():
                if opp.player_id == ball.owner_id or opp.is_knocked_out:
                    continue

                if abs(opp.screen_x - ball.x) < 0.08 and abs(opp.screen_y - ball.y) < 0.12:
                    hit = True
                    opp.take_damage(ball.damage, blocked=opp.is_blocking)
                    self.spawn_particles(ball.x, ball.y, count=12, color=ball.color)
                    if opp.hp <= 0.0:
                        opp.is_knocked_out = True
                        self._end_round_by_ko()
                        return
                    break

            if not hit:
                surviving_balls.append(ball)
        self.active_energy_balls = surviving_balls

        # Spirit Bomb / Genkidama Physics & Impact
        surviving_bombs = []
        for bomb in self.active_spirit_bombs:
            if bomb.state == "FALLING":
                bomb.update(dt)
            if not bomb.active:
                continue

            if bomb.state == "EXPLODED" or (bomb.state == "FALLING" and bomb.y >= 0.50):
                bomb.active = False
                self.screen_trauma = min(1.0, self.screen_trauma + 0.65)
                self.spawn_particles(bomb.x, bomb.y, count=30, color=(100, 230, 255), speed_range=(0.4, 1.2), max_life=0.7)
                if self.sound_engine and hasattr(self.sound_engine, "play_hit"):
                    self.sound_engine.play_hit()

                # Impacto a oponentes en radio de explosion
                for opp in self.fighters.values():
                    if opp.player_id == bomb.owner_id or opp.is_knocked_out:
                        continue
                    if abs(opp.screen_x - bomb.x) <= 0.20:
                        opp.take_damage(bomb.damage, blocked=opp.is_blocking)
                        if opp.hp <= 0.0:
                            opp.is_knocked_out = True
                            self._end_round_by_ko()
                            return
            else:
                surviving_bombs.append(bomb)
        self.active_spirit_bombs = surviving_bombs

        self._update_particles(dt)

    def _end_round_by_ko(self) -> None:
        survivors = [f for f in self.fighters.values() if not f.is_knocked_out]
        if survivors:
            winner = survivors[0]
            self.round_winner_id = winner.player_id
            winner.rounds_won += 1
        else:
            self.round_winner_id = 0

        self.round_state = "ROUND_OVER"
        self.round_over_elapsed = 0.0
        if self.sound_engine and hasattr(self.sound_engine, "play_ko"):
            self.sound_engine.play_ko()

    def _end_round_by_time(self) -> None:
        active_fighters = [f for f in self.fighters.values() if not f.is_knocked_out]
        if active_fighters:
            active_fighters.sort(key=lambda f: f.hp, reverse=True)
            winner = active_fighters[0]
            self.round_winner_id = winner.player_id
            winner.rounds_won += 1
        else:
            self.round_winner_id = 0

        self.round_state = "ROUND_OVER"
        self.round_over_elapsed = 0.0
        if self.sound_engine and hasattr(self.sound_engine, "play_ko"):
            self.sound_engine.play_ko()

    def _start_next_round(self) -> None:
        self.round_number += 1
        self.round_timer = 60.0
        self.round_state = "FIGHTING"
        self.round_winner_id = None
        self.round_over_elapsed = 0.0
        self.active_beams.clear()
        self.active_energy_balls.clear()
        self.beam_struggle_active = False
        self.clash_point = None

        spacing = 1.0 / (self.num_players + 1)
        for i, fighter in enumerate(self.fighters.values()):
            fighter.hp = fighter.max_hp
            fighter.ki = 50.0
            fighter.is_knocked_out = False
            fighter.is_blocking = False
            fighter.is_charging = False
            fighter.is_firing_beam = False
            fighter.hit_stun = 0.0
            fighter.screen_x = (i + 1) * spacing
            fighter.facing_direction = 1.0 if fighter.screen_x < 0.5 else -1.0

        if self.sound_engine and hasattr(self.sound_engine, "play_round_start"):
            self.sound_engine.play_round_start()

    def _update_particles(self, dt: float) -> None:
        surviving = []
        for p in self.particles:
            p.life -= dt
            if p.life > 0.0:
                p.x += p.vx * dt
                p.y += p.vy * dt
                surviving.append(p)
        self.particles = surviving

    def reset_match(self) -> None:
        self.round_number = 1
        self._init_fighters()

    def to_game_state_packet(self):
        from ..network.protocol import GameStatePacket
        fighters_dict = {}
        for pid, f in self.fighters.items():
            fighters_dict[pid] = {
                "player_id": f.player_id,
                "name": f.name,
                "hp": f.hp,
                "max_hp": f.max_hp,
                "ki": f.ki,
                "max_ki": f.max_ki,
                "gesture": f.current_gesture.value if hasattr(f.current_gesture, "value") else str(f.current_gesture),
                "is_blocking": f.is_blocking,
                "is_charging": f.is_charging,
                "is_firing_beam": f.is_firing_beam,
                "is_knocked_out": f.is_knocked_out,
                "facing_direction": f.facing_direction,
                "screen_x": f.screen_x,
                "screen_y": f.screen_y,
                "rounds_won": f.rounds_won,
            }
        beams_list = []
        for b in self.active_beams:
            beams_list.append({
                "owner_id": b.owner_id,
                "start_x": b.start_x,
                "start_y": b.start_y,
                "head_x": b.head_x,
                "head_y": b.head_y,
                "direction": b.direction,
                "active": b.active,
            })
        return GameStatePacket(
            round_number=self.round_number,
            round_timer=self.round_timer,
            round_state=self.round_state,
            winner_id=self.winner_id,
            fighters=fighters_dict,
            beams=beams_list,
            beam_struggle_active=self.beam_struggle_active,
            clash_point=self.clash_point,
        )

    def apply_game_state_packet(self, packet) -> None:
        self.round_number = packet.round_number
        self.round_timer = packet.round_timer
        self.round_state = packet.round_state
        self.winner_id = packet.winner_id
        self.beam_struggle_active = packet.beam_struggle_active
        self.clash_point = packet.clash_point

        for pid, fdata in packet.fighters.items():
            if pid in self.fighters:
                f = self.fighters[pid]
                f.hp = float(fdata.get("hp", f.hp))
                f.ki = float(fdata.get("ki", f.ki))
                f.is_blocking = bool(fdata.get("is_blocking", False))
                f.is_charging = bool(fdata.get("is_charging", False))
                f.is_firing_beam = bool(fdata.get("is_firing_beam", False))
                f.is_knocked_out = bool(fdata.get("is_knocked_out", False))
                f.facing_direction = float(fdata.get("facing_direction", f.facing_direction))
                f.screen_x = float(fdata.get("screen_x", f.screen_x))
                f.screen_y = float(fdata.get("screen_y", f.screen_y))
                f.rounds_won = int(fdata.get("rounds_won", f.rounds_won))
                g_str = fdata.get("gesture", "IDLE")
                try:
                    f.current_gesture = CombatGesture(g_str)
                except Exception:
                    f.current_gesture = CombatGesture.IDLE

        self.active_beams.clear()
        for bdata in packet.beams:
            if bdata.get("active", True):
                self.active_beams.append(
                    BeamProjectile(
                        owner_id=int(bdata["owner_id"]),
                        start_x=float(bdata["start_x"]),
                        start_y=float(bdata["start_y"]),
                        head_x=float(bdata["head_x"]),
                        head_y=float(bdata["head_y"]),
                        direction=float(bdata["direction"]),
                        active=True,
                    )
                )


def math_cos(rad: float) -> float:
    import math
    return math.cos(rad)


def math_sin(rad: float) -> float:
    import math
    return math.sin(rad)
