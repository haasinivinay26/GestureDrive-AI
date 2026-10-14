"""
Collision Detection and Impact Feedback Engine for GestureDrive AI.
Handles precise bounding-box collision detection between player car and track entities,
near-miss dodge bonuses, screen shake, and spark/smoke particle bursts.
"""

import math
import random
from typing import List, Tuple, Optional
import pygame

from config import WINDOW_WIDTH, WINDOW_HEIGHT
from utils.audio import AUDIO


class SparkParticle:
    """High-velocity metallic spark emitted during collisions."""
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(120, 380)
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        self.color = random.choice([(255, 255, 100), (255, 180, 40), (255, 60, 40)])
        self.life = random.uniform(0.2, 0.5)
        self.max_life = self.life

    def update(self, dt: float) -> bool:
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.life -= dt
        return self.life > 0

    def draw(self, surface: pygame.Surface):
        alpha = max(0.0, self.life / self.max_life)
        size = max(1, int(4 * alpha))
        pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), size)


class CollisionSystem:
    """Detects collisions, computes near misses, and manages visual feedback."""

    def __init__(self):
        self.screen_shake_time = 0.0
        self.screen_shake_mag = 0.0
        self.sparks: List[SparkParticle] = []
        self.last_near_miss_text = ""
        self.near_miss_timer = 0.0

    def reset(self):
        """Reset collision state."""
        self.screen_shake_time = 0.0
        self.screen_shake_mag = 0.0
        self.sparks.clear()
        self.last_near_miss_text = ""
        self.near_miss_timer = 0.0

    def update(self, dt: float) -> Tuple[int, int]:
        """Update particles and compute screen shake camera offset."""
        # Update shake
        shake_x, shake_y = 0, 0
        if self.screen_shake_time > 0:
            self.screen_shake_time -= dt
            mag = self.screen_shake_mag * (self.screen_shake_time / 0.4)
            shake_x = int(random.uniform(-mag, mag))
            shake_y = int(random.uniform(-mag, mag))

        # Update sparks
        self.sparks = [s for s in self.sparks if s.update(dt)]

        # Near miss banner timer
        if self.near_miss_timer > 0:
            self.near_miss_timer -= dt

        return shake_x, shake_y

    def check_collisions(self, player_car, traffic_manager, total_track_len: float) -> Tuple[bool, bool]:
        """
        Check collision with opponent cars and static hazards.
        Returns: (has_collided, is_near_miss)
        """
        has_collided = False
        is_near_miss = False

        player_z = player_car.z % total_track_len
        player_x = player_car.x

        # 1. Check Opponent Cars
        for car in traffic_manager.cars:
            car_z = car.z % total_track_len
            dz = abs(car_z - player_z)
            # Handle track wrap around
            dz = min(dz, total_track_len - dz)

            if dz < 140.0:  # Longitudinal collision zone
                dx = abs(player_x - car.x)
                if dx < 0.32:  # Direct impact
                    has_collided = True
                    self._trigger_crash(player_car, car.x)
                    break
                elif dx < 0.50 and player_car.speed > 80.0:
                    is_near_miss = True

        # 2. Check Static Obstacles
        if not has_collided:
            for obs in traffic_manager.obstacles:
                obs_z = obs.z % total_track_len
                dz = abs(obs_z - player_z)
                dz = min(dz, total_track_len - dz)

                if dz < 120.0:
                    dx = abs(player_x - obs.x)
                    if dx < obs.width_ratio:
                        has_collided = True
                        if obs.kind == "oil":
                            # Oil spin out
                            self._trigger_oil_spin(player_car)
                        else:
                            self._trigger_crash(player_car, obs.x)
                        break
                    elif dx < obs.width_ratio + 0.18 and player_car.speed > 80.0:
                        is_near_miss = True

        if is_near_miss and not has_collided and self.near_miss_timer <= 0:
            self.last_near_miss_text = "NEAR MISS! +250"
            self.near_miss_timer = 1.2
            AUDIO.play("beep", volume=0.6)

        return has_collided, is_near_miss

    def _trigger_crash(self, player_car, target_x: float):
        """Execute physical and visual collision effects."""
        # Dramatic speed drop penalty
        player_car.speed = max(25.0, player_car.speed * 0.35)

        # Lateral bounce away from impacted vehicle
        bounce_dir = 1.0 if player_car.x > target_x else -1.0
        player_car.x += bounce_dir * 0.25

        # Screen shake
        self.screen_shake_time = 0.45
        self.screen_shake_mag = 14.0

        # Spawn burst of sparks
        cx = WINDOW_WIDTH // 2
        cy = WINDOW_HEIGHT - 90
        for _ in range(25):
            self.sparks.append(SparkParticle(cx + random.uniform(-40, 40), cy + random.uniform(-20, 20)))

        # Audio crash effect
        AUDIO.play("crash", volume=0.85)

    def _trigger_oil_spin(self, player_car):
        """Oil slick spin reaction."""
        player_car.speed *= 0.65
        player_car.visual_tilt = random.choice([-25.0, 25.0])
        self.screen_shake_time = 0.25
        self.screen_shake_mag = 8.0
        AUDIO.play("brake", volume=0.7)

    def draw(self, surface: pygame.Surface):
        """Render spark particles."""
        for s in self.sparks:
            s.draw(surface)
