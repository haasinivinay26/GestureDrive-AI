"""
Configuration and constants for GestureDrive AI.
Manages game settings, color themes, display resolution, physics, and persistent storage.
"""

import os
import json
from dataclasses import dataclass, field, asdict

# Base directory paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
SOUNDS_DIR = os.path.join(ASSETS_DIR, "sounds")
IMAGES_DIR = os.path.join(ASSETS_DIR, "images")
FONTS_DIR = os.path.join(ASSETS_DIR, "fonts")
SETTINGS_FILE = os.path.join(BASE_DIR, "settings.json")

# Display and Window Configuration
GAME_TITLE = "GestureDrive AI"
TAGLINE = "Your Hands. Your Controls. Your Race."
WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720
TARGET_FPS = 60

# Camera and Vision Configuration
CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480
CAMERA_FPS = 30
CAMERA_PIP_WIDTH = 260
CAMERA_PIP_HEIGHT = 195

# Color Palette (High-contrast Cyberpunk / Modern Racing Theme)
COLOR_BACKGROUND = (14, 16, 24)
COLOR_PANEL_BG = (22, 26, 38)
COLOR_PANEL_BORDER = (45, 55, 80)
COLOR_NEON_CYAN = (0, 240, 255)
COLOR_NEON_GREEN = (50, 255, 120)
COLOR_NEON_RED = (255, 45, 85)
COLOR_NEON_AMBER = (255, 175, 20)
COLOR_NEON_PURPLE = (180, 80, 255)
COLOR_TEXT_WHITE = (245, 248, 255)
COLOR_TEXT_MUTED = (140, 155, 180)
COLOR_DARK_OVERLAY = (0, 0, 0, 160)

# Road 3D Projection Colors (Dark Cyber Racing Theme)
ROAD_COLORS = {
    "light": {
        "road": (44, 48, 62),
        "grass": (14, 18, 28),
        "rumble": (0, 230, 255),       # Neon Cyan curb
        "lane": (240, 250, 255),       # Crisp luminous white dash
    },
    "dark": {
        "road": (36, 40, 52),
        "grass": (10, 13, 22),
        "rumble": (255, 35, 65),       # Laser Crimson curb
        "lane": (36, 40, 52),          # Hidden on dark segments
    },
}

# Road Physics & Projection Parameters
ROAD_WIDTH = 2000
SEGMENT_LENGTH = 200
RUMBLE_LENGTH = 3
LANES = 3
CAMERA_HEIGHT = 1000
CAMERA_DEPTH = 0.84  # 1 / tan(fov/2)
DRAW_DISTANCE = 160  # Segments rendered ahead
TRACK_LENGTH = 1500  # Total segments in a loop

# Car Physics & Simulation Parameters
MAX_SPEED_KMH = 220.0
ACCELERATION_RATE = 50.0   # km/h per second when throttle active
BRAKE_RATE = 110.0         # km/h per second when brake active
NATURAL_DECEL = 20.0       # km/h per second coasting friction
OFFROAD_DECEL = 70.0       # km/h per second when off tarmac
MAX_OFFROAD_SPEED = 60.0   # km/h maximum offroad speed
CAR_STEER_RATE = 2.4       # Lateral movement sensitivity

# Gesture Recognition Settings
STEERING_DEADZONE = 0.08
STEERING_SMOOTHING_ALPHA = 0.22
GESTURE_CONFIRM_FRAMES = 3


@dataclass
class GameSettings:
    """Persistent player and hardware settings."""
    camera_index: int = 0
    camera_preview_enabled: bool = True
    steering_sensitivity: float = 1.0     # 0.4 to 2.5
    gesture_sensitivity: float = 0.7      # 0.4 to 1.0 (confidence threshold)
    sound_enabled: bool = True
    fullscreen: bool = False
    keyboard_fallback_enabled: bool = True
    visual_effects: bool = True           # High-speed motion streaks, particles, road glow
    difficulty: str = "Normal"            # Easy, Normal, Hard
    high_score: int = 0
    calibration_offset_x: float = 0.0
    calibration_offset_y: float = 0.0
    calibration_scale_angle: float = 1.0
    neutral_tilt_deg: float = 0.0         # Calibrated neutral steering wheel tilt in degrees
    neutral_mid_x: float = 0.5            # Calibrated horizontal midpoint between hands (0.0 to 1.0)
    steering_deadzone: float = 0.08       # Center deadzone to prevent drift

    @classmethod
    def load(cls) -> "GameSettings":
        """Load settings from JSON file or return defaults."""
        if os.path.exists(SETTINGS_FILE):
            try:
                with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
            except Exception as e:
                print(f"[Settings] Error loading {SETTINGS_FILE}: {e}. Using defaults.")
        return cls()

    def save(self):
        """Save settings to JSON file."""
        try:
            with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump(asdict(self), f, indent=4)
        except Exception as e:
            print(f"[Settings] Error saving {SETTINGS_FILE}: {e}")


# Global settings singleton
SETTINGS = GameSettings.load()
