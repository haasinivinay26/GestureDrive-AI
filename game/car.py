"""
Player Car Physics and Dynamic 2D/3D Procedural Renderer for GestureDrive AI.
Renders an aerodynamic sports car with tilting chassis, exhaust fire particles,
and high-intensity LED brake lights.
"""

import math
import random
from typing import List, Tuple
import pygame

from config import (
    MAX_SPEED_KMH, ACCELERATION_RATE, BRAKE_RATE,
    NATURAL_DECEL, OFFROAD_DECEL, MAX_OFFROAD_SPEED,
    CAR_STEER_RATE, COLOR_NEON_RED, COLOR_NEON_CYAN,
    WINDOW_WIDTH, WINDOW_HEIGHT, SETTINGS
)
from utils.helpers import clamp, lerp


class ExhaustParticle:
    """Sparks and flame particles emitted from exhaust pipes during acceleration."""
    def __init__(self, x: float, y: float, vx: float, vy: float, color, life: float = 0.3):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.color = color
        self.life = life
        self.max_life = life

    def update(self, dt: float) -> bool:
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.life -= dt
        return self.life > 0

    def draw(self, surface: pygame.Surface):
        alpha = max(0.0, min(1.0, self.life / self.max_life))
        radius = max(1, int(4 * alpha))
        c = self.color
        pygame.draw.circle(surface, c, (int(self.x), int(self.y)), radius)


class PlayerCar:
    """Simulates player vehicle physics, steering response, and visual rendering."""

    def __init__(self):
        self.x = 0.0             # Lateral position: -1.0 (left curb) to +1.0 (right curb)
        self.z = 0.0             # Longitudinal track distance in world units
        self.speed = 0.0         # Current speed in km/h
        self.max_speed = MAX_SPEED_KMH
        self.steer_angle = 0.0   # Current normalized steering -1.0 to 1.0
        self.visual_tilt = 0.0   # Visual body roll angle in degrees
        self.particles: List[ExhaustParticle] = []
        self.bounce_timer = 0.0  # Road rumble vibration

    def reset(self):
        """Reset car state for a new race."""
        self.x = 0.0
        self.z = 0.0
        self.speed = 0.0
        self.steer_angle = 0.0
        self.visual_tilt = 0.0
        self.particles.clear()

    def update(self, dt: float, steer_input: float, is_accel: bool, is_brake: bool, road_curve: float):
        """
        Advance vehicle physics by delta time dt.
        Braking strictly overrides acceleration.
        """
        self.steer_angle = steer_input

        # 1. Acceleration and Braking Physics
        is_offroad = abs(self.x) > 1.0

        if is_brake:
            self.speed = max(0.0, self.speed - BRAKE_RATE * dt)
        elif is_accel:
            # When on grass/offroad, top speed is capped at MAX_OFFROAD_SPEED
            effective_max = MAX_OFFROAD_SPEED if is_offroad else self.max_speed
            if self.speed < effective_max:
                self.speed = min(effective_max, self.speed + ACCELERATION_RATE * dt)
        else:
            # Coasting deceleration
            self.speed = max(0.0, self.speed - NATURAL_DECEL * dt)

        # 2. Off-road grass penalty
        if is_offroad and self.speed > MAX_OFFROAD_SPEED:
            self.speed = max(MAX_OFFROAD_SPEED, self.speed - OFFROAD_DECEL * 1.5 * dt)

        # 3. Lateral movement across track (only turns when moving)
        speed_factor = self.speed / self.max_speed
        lateral_speed = speed_factor * CAR_STEER_RATE

        # Neutral steering lock: if steer_angle is zero or negligible, strictly keep moving straight
        if abs(self.steer_angle) < 0.015:
            self.steer_angle = 0.0
        else:
            self.x += self.steer_angle * lateral_speed * dt

        self.x = clamp(self.x, -1.8, 1.8)

        # 4. Advance distance along track
        # Scale km/h into world distance units
        world_speed = (self.speed / 3.6) * 12.0
        self.z += world_speed * dt

        # 5. Visual Body Roll Tilt
        target_tilt = self.steer_angle * 10.0
        self.visual_tilt = lerp(self.visual_tilt, target_tilt, dt * 10.0)

        # 6. Road vibration rumble when driving at speed
        if self.speed > 30.0:
            self.bounce_timer += dt * (self.speed * 0.15)
        else:
            self.bounce_timer = 0.0

        # 7. Exhaust particle simulation
        self._update_particles(dt, is_accel)

    def _update_particles(self, dt: float, is_accel: bool):
        """Spawn and update exhaust flame and smoke particles."""
        # Spawn particles when accelerating
        if is_accel and self.speed > 20.0:
            for _ in range(2):
                color = random.choice([(255, 120, 20), (255, 220, 50), (0, 240, 255)])
                # Left and right pipe positions (screen coords around bottom center)
                car_cx = WINDOW_WIDTH // 2
                car_cy = WINDOW_HEIGHT - 65
                vx_l = random.uniform(-15, -5)
                vx_r = random.uniform(5, 15)
                vy = random.uniform(30, 80)
                self.particles.append(ExhaustParticle(car_cx - 32, car_cy, vx_l, vy, color, life=random.uniform(0.15, 0.35)))
                self.particles.append(ExhaustParticle(car_cx + 32, car_cy, vx_r, vy, color, life=random.uniform(0.15, 0.35)))

        # Update existing particles
        self.particles = [p for p in self.particles if p.update(dt)]

    def draw(self, surface: pygame.Surface, is_braking: bool, is_accel: bool):
        """Draw player sports car near bottom of screen with aerodynamic body roll and visual telemetry."""
        # 1. High-speed motion wind streaks when driving over 130 km/h
        if self.speed > 130.0 and getattr(SETTINGS, "visual_effects", True):
            speed_ratio = (self.speed - 130.0) / (self.max_speed - 130.0)
            num_streaks = int(3 + 8 * speed_ratio)
            for _ in range(num_streaks):
                sx = random.randint(40, WINDOW_WIDTH - 40)
                sy = random.randint(WINDOW_HEIGHT // 2, WINDOW_HEIGHT)
                slen = random.randint(30, int(60 + 100 * speed_ratio))
                alpha = random.randint(40, int(80 + 120 * speed_ratio))
                s_surf = pygame.Surface((2, slen), pygame.SRCALPHA)
                pygame.draw.line(s_surf, (200, 240, 255, alpha), (1, 0), (1, slen), 2)
                surface.blit(s_surf, (sx, sy))

        # 2. Draw exhaust particles behind the car
        for p in self.particles:
            p.draw(surface)

        cx = WINDOW_WIDTH // 2
        cy = WINDOW_HEIGHT - 95

        # Slight vertical bounce when driving
        bounce_y = int(math.sin(self.bounce_timer) * 1.5) if self.speed > 40.0 else 0
        cy += bounce_y

        car_w = 160
        car_h = 80

        # Create rotated/tilted car surface for body roll
        car_surf = pygame.Surface((car_w + 50, car_h + 40), pygame.SRCALPHA)
        local_cx = (car_w + 50) // 2
        local_cy = (car_h + 40) // 2

        # 3. Soft Underglow reflection on tarmac (Cyan normally, Red when braking)
        glow_color = (255, 30, 60, 90) if is_braking else (0, 220, 255, 75)
        underglow_rect = pygame.Rect(local_cx - car_w // 2, local_cy + 16, car_w, 20)
        pygame.draw.ellipse(car_surf, glow_color, underglow_rect)

        # 4. Shadow underneath car
        shadow_rect = pygame.Rect(local_cx - car_w // 2 + 8, local_cy + 18, car_w - 16, 15)
        pygame.draw.ellipse(car_surf, (8, 10, 16, 210), shadow_rect)

        # 5. Dual Rear Tires
        tire_w, tire_h = 26, 44
        # Left tire
        pygame.draw.rect(car_surf, (20, 24, 30), (local_cx - car_w // 2 + 2, local_cy - 4, tire_w, tire_h), border_radius=4)
        pygame.draw.rect(car_surf, (45, 52, 68), (local_cx - car_w // 2 + 6, local_cy + 4, 14, 28), border_radius=2)
        # Right tire
        pygame.draw.rect(car_surf, (20, 24, 30), (local_cx + car_w // 2 - tire_w - 2, local_cy - 4, tire_w, tire_h), border_radius=4)
        pygame.draw.rect(car_surf, (45, 52, 68), (local_cx + car_w // 2 - tire_w + 4, local_cy + 4, 14, 28), border_radius=2)

        # 6. Main Body Chassis (Aggressive Sports supercar shape)
        body_points = [
            (local_cx - 60, local_cy + 26),  # Bottom left
            (local_cx - 72, local_cy + 6),   # Mid left flare
            (local_cx - 52, local_cy - 20),  # Roof left
            (local_cx + 52, local_cy - 20),  # Roof right
            (local_cx + 72, local_cy + 6),   # Mid right flare
            (local_cx + 60, local_cy + 26),  # Bottom right
        ]
        # Cyber Blue / Electric Cobalt
        pygame.draw.polygon(car_surf, (16, 65, 160), body_points)
        # Highlight contour
        pygame.draw.lines(car_surf, (50, 130, 245), True, body_points, width=2)

        # 7. Rear Windshield Glass (reflective dark glass)
        windshield_points = [
            (local_cx - 44, local_cy - 17),
            (local_cx + 44, local_cy - 17),
            (local_cx + 52, local_cy + 2),
            (local_cx - 52, local_cy + 2),
        ]
        pygame.draw.polygon(car_surf, (25, 35, 55), windshield_points)
        pygame.draw.lines(car_surf, (90, 150, 220), True, windshield_points, width=1)

        # 8. Dual Racing Stripes (Neon Cyan)
        stripe_color = (0, 240, 255)
        pygame.draw.rect(car_surf, stripe_color, (local_cx - 11, local_cy - 20, 6, 46))
        pygame.draw.rect(car_surf, stripe_color, (local_cx + 5, local_cy - 20, 6, 46))

        # 9. Rear Spoiler Wing
        spoiler_w = 124
        spoiler_y = local_cy - 25
        pygame.draw.rect(car_surf, (12, 16, 26), (local_cx - spoiler_w // 2, spoiler_y, spoiler_w, 8), border_radius=2)
        pygame.draw.rect(car_surf, (0, 240, 255), (local_cx - spoiler_w // 2, spoiler_y, spoiler_w, 2))
        # Spoiler struts
        pygame.draw.rect(car_surf, (16, 20, 32), (local_cx - 32, spoiler_y + 7, 7, 9))
        pygame.draw.rect(car_surf, (16, 20, 32), (local_cx + 25, spoiler_y + 7, 7, 9))

        # Active Steering Blinker Winglet Accents
        if self.steer_angle < -0.15:
            # Turning left -> left winglet flashes cyan
            pygame.draw.rect(car_surf, (0, 255, 255), (local_cx - spoiler_w // 2 - 2, spoiler_y - 3, 5, 14), border_radius=2)
        elif self.steer_angle > 0.15:
            # Turning right -> right winglet flashes cyan
            pygame.draw.rect(car_surf, (0, 255, 255), (local_cx + spoiler_w // 2 - 3, spoiler_y - 3, 5, 14), border_radius=2)

        # 10. Dual Exhaust Tips
        pipe_color = (255, 180, 50) if is_accel else (140, 145, 160)
        pygame.draw.circle(car_surf, pipe_color, (local_cx - 34, local_cy + 25), 5)
        pygame.draw.circle(car_surf, pipe_color, (local_cx + 34, local_cy + 25), 5)

        # 11. Continuous Hypercar LED Lightbar (Red with intense Brake Bloom)
        light_color = (255, 20, 50) if is_braking else (190, 20, 40)
        lightbar_pts = [
            (local_cx - 62, local_cy + 8),
            (local_cx - 20, local_cy + 13),
            (local_cx + 20, local_cy + 13),
            (local_cx + 62, local_cy + 8),
        ]
        pygame.draw.lines(car_surf, light_color, False, lightbar_pts, width=5 if is_braking else 3)

        # Taillight brake glow bloom
        if is_braking:
            glow_surf = pygame.Surface((car_w + 50, car_h + 40), pygame.SRCALPHA)
            pygame.draw.lines(glow_surf, (255, 50, 80, 120), False, lightbar_pts, width=12)
            car_surf.blit(glow_surf, (0, 0))

        # Rotate car surface for body roll lean
        rotated_surf = pygame.transform.rotate(car_surf, -self.visual_tilt)
        rot_rect = rotated_surf.get_rect(center=(cx, cy))
        surface.blit(rotated_surf, rot_rect)

