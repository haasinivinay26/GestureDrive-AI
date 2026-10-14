"""
Audio management and procedural sound generation for GestureDrive AI.
Generates retro-futuristic arcade sound effects using NumPy and plays them via Pygame Mixer.
Runs silently and safely if sound hardware is missing.
"""

import os
import wave
import struct
import numpy as np
import pygame
from config import SOUNDS_DIR, SETTINGS


class AudioManager:
    """Manages sound effects, engine modulation, and procedural audio synthesis."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AudioManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self.sounds = {}
        self.engine_channel = None
        self.brake_channel = None
        self.is_sound_available = False

        self._init_mixer()
        self._generate_default_sounds()
        self._load_sounds()

    def _init_mixer(self):
        """Initialize pygame.mixer safely."""
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=1024)
            self.is_sound_available = True
            # Reserve specific channels for engine and tire screech
            pygame.mixer.set_num_channels(16)
            self.engine_channel = pygame.mixer.Channel(0)
            self.brake_channel = pygame.mixer.Channel(1)
        except Exception as e:
            print(f"[Audio] Warning: Mixer initialization failed: {e}. Audio disabled.")
            self.is_sound_available = False

    def _generate_default_sounds(self):
        """Synthesize arcade sounds if WAV files don't exist."""
        os.makedirs(SOUNDS_DIR, exist_ok=True)
        sample_rate = 44100

        # 1. Engine Loop (continuous multi-harmonic rumble)
        engine_file = os.path.join(SOUNDS_DIR, "engine.wav")
        if not os.path.exists(engine_file):
            duration = 1.0  # 1-second seamless loop
            t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
            f0 = 85.0  # Base RPM frequency
            # Harmonics
            wave_data = (
                0.40 * np.sin(2 * np.pi * f0 * t) +
                0.25 * np.sin(2 * np.pi * 2 * f0 * t) +
                0.20 * np.sin(2 * np.pi * 3 * f0 * t) +
                0.15 * np.sin(2 * np.pi * 4 * f0 * t) +
                0.10 * np.random.uniform(-1, 1, len(t))
            )
            # Smooth loop boundary
            fade = int(sample_rate * 0.05)
            wave_data[:fade] *= np.linspace(0, 1, fade)
            wave_data[-fade:] *= np.linspace(1, 0, fade)
            self._save_wav(engine_file, wave_data, sample_rate)

        # 2. Brake Screech (frequency modulated friction scream)
        brake_file = os.path.join(SOUNDS_DIR, "brake.wav")
        if not os.path.exists(brake_file):
            duration = 0.8
            t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
            mod = np.sin(2 * np.pi * 18 * t) * 400.0
            freq = 2800.0 + mod
            wave_data = np.sin(2 * np.pi * freq * t) * 0.4 + 0.3 * np.random.uniform(-1, 1, len(t))
            # Envelope: fast rise, steady, fade out
            env = np.ones_like(t)
            ramp_up = int(sample_rate * 0.05)
            ramp_down = int(sample_rate * 0.25)
            env[:ramp_up] = np.linspace(0, 1, ramp_up)
            env[-ramp_down:] = np.linspace(1, 0, ramp_down)
            wave_data = wave_data * env * 0.55
            self._save_wav(brake_file, wave_data, sample_rate)

        # 3. Crash Crunch (explosive transient + sub-bass boom)
        crash_file = os.path.join(SOUNDS_DIR, "crash.wav")
        if not os.path.exists(crash_file):
            duration = 1.2
            t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
            noise = np.random.uniform(-1, 1, len(t)) * np.exp(-4.5 * t)
            sub_bass = np.sin(2 * np.pi * 65 * np.exp(-2.0 * t) * t) * np.exp(-3.0 * t)
            wave_data = (noise * 0.7 + sub_bass * 0.8) * 0.7
            self._save_wav(crash_file, wave_data, sample_rate)

        # 4. Button Click (crisp UI tick)
        click_file = os.path.join(SOUNDS_DIR, "click.wav")
        if not os.path.exists(click_file):
            duration = 0.06
            t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
            wave_data = np.sin(2 * np.pi * 750 * t) * np.exp(-35 * t) * 0.45
            self._save_wav(click_file, wave_data, sample_rate)

        # 5. Beep High (race countdown start)
        beep_file = os.path.join(SOUNDS_DIR, "beep.wav")
        if not os.path.exists(beep_file):
            duration = 0.18
            t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
            wave_data = np.sin(2 * np.pi * 920 * t) * np.exp(-10 * t) * 0.5
            self._save_wav(beep_file, wave_data, sample_rate)

        # 6. Countdown Go Beep (higher pitch)
        go_file = os.path.join(SOUNDS_DIR, "go.wav")
        if not os.path.exists(go_file):
            duration = 0.35
            t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
            wave_data = np.sin(2 * np.pi * 1450 * t) * np.exp(-6 * t) * 0.6
            self._save_wav(go_file, wave_data, sample_rate)

    def _save_wav(self, filepath: str, data: np.ndarray, sample_rate: int):
        """Save a normalized numpy array as 16-bit PCM WAV."""
        try:
            norm = np.clip(data, -1.0, 1.0)
            int_data = (norm * 32767).astype(np.int16)
            with wave.open(filepath, "w") as wf:
                wf.setnchannels(1)  # Mono
                wf.setsampwidth(2)   # 16-bit
                wf.setframerate(sample_rate)
                wf.writeframes(int_data.tobytes())
        except Exception as e:
            print(f"[Audio] Error writing WAV {filepath}: {e}")

    def _load_sounds(self):
        """Load synthesized WAV files into Pygame Sound objects."""
        if not self.is_sound_available:
            return
        sound_names = ["engine", "brake", "crash", "click", "beep", "go"]
        for name in sound_names:
            path = os.path.join(SOUNDS_DIR, f"{name}.wav")
            if os.path.exists(path):
                try:
                    snd = pygame.mixer.Sound(path)
                    self.sounds[name] = snd
                except Exception as e:
                    print(f"[Audio] Failed to load sound {name}: {e}")

    def play(self, name: str, volume: float = 1.0):
        """Play a single one-shot sound effect if sound is enabled."""
        if not (self.is_sound_available and SETTINGS.sound_enabled):
            return
        snd = self.sounds.get(name)
        if snd:
            try:
                snd.set_volume(volume)
                snd.play()
            except Exception:
                pass

    def start_engine(self):
        """Start looped engine sound."""
        if not (self.is_sound_available and SETTINGS.sound_enabled):
            return
        snd = self.sounds.get("engine")
        if snd and self.engine_channel:
            if not self.engine_channel.get_busy():
                self.engine_channel.play(snd, loops=-1)
                self.engine_channel.set_volume(0.25)

    def update_engine(self, speed_ratio: float):
        """Dynamically adjust engine volume based on speed (0.0 to 1.0)."""
        if not (self.is_sound_available and SETTINGS.sound_enabled):
            return
        if self.engine_channel and self.engine_channel.get_busy():
            # Adjust volume according to speed
            vol = 0.2 + 0.5 * speed_ratio
            self.engine_channel.set_volume(vol)

    def stop_engine(self):
        """Stop engine sound loop."""
        if self.engine_channel:
            self.engine_channel.stop()

    def set_brake_sound(self, active: bool):
        """Trigger or stop tire screech loop when braking at speed."""
        if not (self.is_sound_available and SETTINGS.sound_enabled):
            return
        if self.brake_channel:
            if active:
                if not self.brake_channel.get_busy():
                    snd = self.sounds.get("brake")
                    if snd:
                        self.brake_channel.play(snd, loops=-1)
                        self.brake_channel.set_volume(0.4)
            else:
                if self.brake_channel.get_busy():
                    self.brake_channel.stop()


# Global audio manager instance
AUDIO = AudioManager()
