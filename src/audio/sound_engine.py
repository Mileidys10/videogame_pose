"""Motor de audio procedimental para sintesis de efectos de combate en tiempo real."""

import time
from typing import Optional
import numpy as np
import pygame


class SoundEngine:
    """Sintetizador matematico de audio offline con pygame.mixer y numpy."""

    def __init__(self, sample_rate: int = 22050, enabled: bool = True):
        self.sample_rate = sample_rate
        self.enabled = enabled
        self._sounds = {}
        self._last_played = {}

        if not self.enabled:
            return

        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=self.sample_rate, size=-16, channels=2, buffer=512)
            self._synthesize_all_sounds()
        except Exception as e:
            # En entornos headless sin dispositivo de audio, desactivar silenciosamente
            print(f"[INFO] Audio no disponible ({e}), operando en modo silente.")
            self.enabled = False

    def _create_stereo_sound(self, mono_wave: np.ndarray) -> pygame.mixer.Sound:
        """Convierte una onda normalizada [-1.0, 1.0] en un objeto de sonido estereo Pygame."""
        clamped = np.clip(mono_wave, -1.0, 1.0)
        audio_int16 = (clamped * 28000).astype(np.int16)
        stereo = np.column_stack((audio_int16, audio_int16))
        return pygame.sndarray.make_sound(stereo)

    def _synthesize_all_sounds(self) -> None:
        """Sintetiza todo el catalogo de efectos sonoros al arrancar."""
        sr = self.sample_rate

        # 1. Disparo de Kamehameha / Laser (0.6 segundos)
        t_laser = np.linspace(0, 0.6, int(sr * 0.6), False)
        freq_laser = 680.0 * np.exp(-3.5 * t_laser) + 180.0
        phase_laser = 2.0 * np.pi * np.cumsum(freq_laser) / sr
        env_laser = np.exp(-2.8 * t_laser)
        wave_laser = (0.7 * np.sin(phase_laser) + 0.3 * np.sin(2.0 * phase_laser)) * env_laser
        self._sounds["laser"] = self._create_stereo_sound(wave_laser)

        # 2. Escudo / Bloqueo Energetico (0.4 segundos)
        t_shield = np.linspace(0, 0.4, int(sr * 0.4), False)
        lfo_shield = 1.0 + 0.25 * np.sin(2.0 * np.pi * 18.0 * t_shield)
        wave_shield = np.sin(2.0 * np.pi * 210.0 * lfo_shield * t_shield) * np.exp(-3.0 * t_shield)
        self._sounds["shield"] = self._create_stereo_sound(wave_shield)

        # 3. Carga de Ki (0.5 segundos)
        t_charge = np.linspace(0, 0.5, int(sr * 0.5), False)
        freq_charge = 120.0 + 400.0 * (t_charge / 0.5) ** 1.5
        phase_charge = 2.0 * np.pi * np.cumsum(freq_charge) / sr
        tremolo = 0.8 + 0.2 * np.sin(2.0 * np.pi * 24.0 * t_charge)
        wave_charge = np.sin(phase_charge) * tremolo * np.linspace(0.1, 1.0, len(t_charge))
        self._sounds["charge"] = self._create_stereo_sound(wave_charge)

        # 4. Golpe / Impacto Melee (0.2 segundos)
        t_hit = np.linspace(0, 0.2, int(sr * 0.2), False)
        thud = np.sin(2.0 * np.pi * 85.0 * t_hit) * np.exp(-14.0 * t_hit)
        noise = (np.random.uniform(-1.0, 1.0, len(t_hit))) * np.exp(-22.0 * t_hit)
        wave_hit = 0.6 * thud + 0.4 * noise
        self._sounds["hit"] = self._create_stereo_sound(wave_hit)

        # 5. Choque de Rayos (Beam Struggle Buzz) (0.3 segundos, loopeable)
        t_clash = np.linspace(0, 0.3, int(sr * 0.3), False)
        buzz1 = np.sin(2.0 * np.pi * 175.0 * t_clash)
        buzz2 = np.sin(2.0 * np.pi * 182.0 * t_clash)
        crackle = np.random.uniform(-0.15, 0.15, len(t_clash))
        wave_clash = 0.45 * buzz1 + 0.45 * buzz2 + crackle
        self._sounds["clash"] = self._create_stereo_sound(wave_clash)

        # 6. K.O. y Caida (0.8 segundos)
        t_ko = np.linspace(0, 0.8, int(sr * 0.8), False)
        freq_ko = 90.0 * np.exp(-2.0 * t_ko) + 35.0
        phase_ko = 2.0 * np.pi * np.cumsum(freq_ko) / sr
        wave_ko = np.sin(phase_ko) * np.exp(-2.2 * t_ko)
        self._sounds["ko"] = self._create_stereo_sound(wave_ko)

        # 7. Inicio de Asalto / Campana (0.5 segundos)
        t_bell = np.linspace(0, 0.5, int(sr * 0.5), False)
        bell1 = np.sin(2.0 * np.pi * 880.0 * t_bell) * np.exp(-4.0 * t_bell)
        bell2 = np.sin(2.0 * np.pi * 1320.0 * t_bell) * np.exp(-5.0 * t_bell)
        self._sounds["round_start"] = self._create_stereo_sound(0.6 * bell1 + 0.4 * bell2)

    def play(self, sound_name: str, min_interval: float = 0.12) -> None:
        """Reproduce un efecto con limite de tasa (rate-limiting) para prevenir solapamientos caoticos."""
        if not self.enabled or sound_name not in self._sounds:
            return

        now = time.time()
        last = self._last_played.get(sound_name, 0.0)
        if (now - last) >= min_interval:
            self._last_played[sound_name] = now
            self._sounds[sound_name].play()

    def play_laser(self) -> None:
        self.play("laser", min_interval=0.25)

    def play_shield(self) -> None:
        self.play("shield", min_interval=0.20)

    def play_charge(self) -> None:
        self.play("charge", min_interval=0.30)

    def play_hit(self) -> None:
        self.play("hit", min_interval=0.10)

    def play_clash(self) -> None:
        self.play("clash", min_interval=0.15)

    def play_ko(self) -> None:
        self.play("ko", min_interval=0.50)

    def play_round_start(self) -> None:
        self.play("round_start", min_interval=0.50)

    def stop_all(self) -> None:
        if self.enabled:
            pygame.mixer.stop()
