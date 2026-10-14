"""
Scoring, Race Metrics, and High Score Engine for GestureDrive AI.
Tracks distance, speed multipliers, overtakes, near-misses, and dynamic difficulty scaling.
"""

from typing import Dict, Any
from config import SETTINGS


class ScoringSystem:
    """Manages player score, distance counters, combo multipliers, and records."""

    def __init__(self):
        self.score = 0
        self.distance_meters = 0.0
        self.race_time = 0.0
        self.overtakes = 0
        self.near_misses = 0
        self.speed_multiplier = 1.0
        self.high_score = SETTINGS.high_score
        self.is_new_high_score = False

    def reset(self):
        """Reset counters for a new race."""
        self.score = 0
        self.distance_meters = 0.0
        self.race_time = 0.0
        self.overtakes = 0
        self.near_misses = 0
        self.speed_multiplier = 1.0
        self.is_new_high_score = False
        self.high_score = SETTINGS.high_score

    def update(self, dt: float, speed_kmh: float):
        """Update distance and points based on speed and multiplier."""
        self.race_time += dt

        # Distance calculation: speed in m/s * dt
        speed_mps = (speed_kmh / 3.6)
        self.distance_meters += speed_mps * dt

        # Dynamic combo multiplier based on speed bracket
        if speed_kmh > 180.0:
            self.speed_multiplier = 2.5
        elif speed_kmh > 130.0:
            self.speed_multiplier = 1.8
        elif speed_kmh > 70.0:
            self.speed_multiplier = 1.2
        else:
            self.speed_multiplier = 1.0

        # Points accumulation
        earned = speed_mps * self.speed_multiplier * dt * 4.0
        self.score += int(earned)

        # High score tracking
        if self.score > self.high_score:
            self.high_score = self.score
            self.is_new_high_score = True

    def add_near_miss(self):
        """Award points for close dodge."""
        bonus = int(250 * self.speed_multiplier)
        self.score += bonus
        self.near_misses += 1
        if self.score > self.high_score:
            self.high_score = self.score
            self.is_new_high_score = True

    def add_overtake(self):
        """Award points for passing a rival vehicle."""
        bonus = int(100 * self.speed_multiplier)
        self.score += bonus
        self.overtakes += 1
        if self.score > self.high_score:
            self.high_score = self.score
            self.is_new_high_score = True

    def on_crash(self):
        """Reset multiplier on collision."""
        self.speed_multiplier = 1.0

    def finalize_race(self):
        """Persist high score if surpassed."""
        if self.score > SETTINGS.high_score:
            SETTINGS.high_score = self.score
            SETTINGS.save()

    def get_formatted_distance(self) -> str:
        """Format distance into human-readable string."""
        if self.distance_meters >= 1000.0:
            return f"{self.distance_meters / 1000.0:.2f} km"
        return f"{int(self.distance_meters)} m"

    def get_formatted_time(self) -> str:
        """Format elapsed race time as MM:SS.ms."""
        total_secs = int(self.race_time)
        mins = total_secs // 60
        secs = total_secs % 60
        ms = int((self.race_time - total_secs) * 10)
        return f"{mins:02d}:{secs:02d}.{ms:01d}"

    def get_difficulty_factor(self) -> float:
        """Difficulty scales smoothly with distance traveled."""
        # Returns a factor from 1.0 (start) to 2.2 (after 5 km)
        return min(2.2, 1.0 + (self.distance_meters / 3000.0))
