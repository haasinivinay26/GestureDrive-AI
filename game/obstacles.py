"""
Opponent Vehicles and Road Obstacles Engine for GestureDrive AI.
Manages AI traffic cars, hazard obstacles (traffic cones, road barriers, oil slicks),
and dynamic pseudo-3D scaling and rendering.
"""

import math
import random
from typing import List, Dict, Any, Optional
import pygame

from config import (
    ROAD_WIDTH, SEGMENT_LENGTH, WINDOW_WIDTH, WINDOW_HEIGHT
)
from utils.helpers import clamp


OPPONENT_COLORS = [
    {"body": (210, 35, 45), "stripe": (255, 255, 255), "name": "Ferrari Red"},
    {"body": (220, 180, 20), "stripe": (20, 20, 20), "name": "Viper Yellow"},
    {"body": (35, 180, 80), "stripe": (240, 240, 240), "name": "Lime Racer"},
    {"body": (140, 45, 210), "stripe": (0, 240, 255), "name": "Cyber Purple"},
    {"body": (40, 45, 55), "stripe": (255, 45, 85), "name": "Midnight Stealth"},
]


class OpponentCar:
    """An AI-controlled rival vehicle driving along the track."""

    def __init__(self, z: float, x: float, speed_kmh: float, color_idx: int = 0):
        self.z = z                        # World Z coordinate along track
        self.x = x                        # Lateral position (-0.8 to 0.8)
        self.speed = speed_kmh            # Speed in km/h
        self.color = OPPONENT_COLORS[color_idx % len(OPPONENT_COLORS)]
        self.target_x = x
        self.weave_timer = random.uniform(0, 10)
        self.width_ratio = 0.35           # Collision width ratio relative to road

    def update(self, dt: float, total_track_len: float):
        """Move vehicle forward and periodically adjust lane."""
        world_speed = (self.speed / 3.6) * 12.0
        self.z += world_speed * dt
        self.z %= total_track_len

        # Gentle lane drifting behavior
        self.weave_timer += dt * 0.8
        drift = math.sin(self.weave_timer) * 0.15
        self.x = clamp(self.target_x + drift, -0.85, 0.85)

    def draw(self, surface: pygame.Surface, screen_x: float, screen_y: float, scale: float):
        """Render scaled 3D opponent car."""
        car_w = int(scale * 1200.0)
        car_h = int(car_w * 0.52)

        if car_w < 6 or car_w > 500 or screen_y < 0 or screen_y > WINDOW_HEIGHT:
            return

        cx, cy = int(screen_x), int(screen_y)

        # 1. Shadow underneath
        shadow_rect = pygame.Rect(cx - car_w // 2, cy - car_h // 4, car_w, car_h // 3)
        pygame.draw.ellipse(surface, (10, 12, 18), shadow_rect)

        # 2. Dual Tires
        tire_w = max(2, int(car_w * 0.16))
        tire_h = max(3, int(car_h * 0.55))
        pygame.draw.rect(surface, (20, 22, 28), (cx - car_w // 2, cy - tire_h // 2, tire_w, tire_h), border_radius=2)
        pygame.draw.rect(surface, (20, 22, 28), (cx + car_w // 2 - tire_w, cy - tire_h // 2, tire_w, tire_h), border_radius=2)

        # 3. Main Body
        body_rect = pygame.Rect(cx - car_w // 2 + tire_w // 2, cy - car_h, car_w - tire_w, car_h)
        pygame.draw.rect(surface, self.color["body"], body_rect, border_radius=max(2, car_w // 15))

        # 4. Roof / Windshield
        roof_w = int(body_rect.width * 0.7)
        roof_h = int(car_h * 0.45)
        roof_rect = pygame.Rect(cx - roof_w // 2, cy - car_h - roof_h // 2, roof_w, roof_h)
        pygame.draw.rect(surface, (25, 30, 45), roof_rect, border_radius=2)

        # 5. Racing Stripe
        stripe_w = max(1, int(car_w * 0.08))
        pygame.draw.rect(surface, self.color["stripe"], (cx - stripe_w // 2, cy - car_h - roof_h // 2, stripe_w, car_h + roof_h // 2))

        # 6. Taillights (Red)
        light_w = max(2, int(car_w * 0.18))
        light_h = max(2, int(car_h * 0.20))
        pygame.draw.rect(surface, (240, 25, 45), (cx - car_w // 2 + tire_w, cy - light_h - 2, light_w, light_h), border_radius=1)
        pygame.draw.rect(surface, (240, 25, 45), (cx + car_w // 2 - tire_w - light_w, cy - light_h - 2, light_w, light_h), border_radius=1)


class RoadObstacle:
    """A static hazard on the race track: cone, barrier, or oil slick."""

    def __init__(self, z: float, x: float, kind: str = "cone"):
        self.z = z
        self.x = x
        self.kind = kind  # "cone", "barrier", "oil"
        self.width_ratio = 0.20 if kind == "cone" else (0.45 if kind == "barrier" else 0.35)

    def draw(self, surface: pygame.Surface, screen_x: float, screen_y: float, scale: float):
        """Render scaled obstacle sprite."""
        cx, cy = int(screen_x), int(screen_y)

        if self.kind == "cone":
            # Orange traffic cone
            cone_w = max(4, int(scale * 380.0))
            cone_h = max(6, int(cone_w * 1.5))
            if cone_w < 3 or cone_w > 250:
                return
            pts = [(cx, cy - cone_h), (cx - cone_w // 2, cy), (cx + cone_w // 2, cy)]
            pygame.draw.polygon(surface, (255, 110, 10), pts)
            # White reflective band
            band_y1 = cy - int(cone_h * 0.55)
            band_y2 = cy - int(cone_h * 0.35)
            band_w = int(cone_w * 0.5)
            pygame.draw.polygon(surface, (255, 255, 255), [
                (cx - band_w // 3, band_y1), (cx + band_w // 3, band_y1),
                (cx + band_w // 2, band_y2), (cx - band_w // 2, band_y2)
            ])

        elif self.kind == "barrier":
            # Construction hazard barrier (striped red and white)
            bar_w = max(8, int(scale * 750.0))
            bar_h = max(4, int(bar_w * 0.38))
            if bar_w < 4 or bar_w > 400:
                return
            rect = pygame.Rect(cx - bar_w // 2, cy - bar_h, bar_w, bar_h)
            pygame.draw.rect(surface, (230, 230, 230), rect, border_radius=2)
            # Diagonal warning stripes
            stripe_step = max(4, bar_w // 6)
            for sx in range(rect.left, rect.right, stripe_step * 2):
                pts = [(sx, rect.bottom), (sx + stripe_step, rect.bottom),
                       (sx + stripe_step * 2, rect.top), (sx + stripe_step, rect.top)]
                pygame.draw.polygon(surface, (230, 35, 45), pts)
            pygame.draw.rect(surface, (40, 45, 55), rect, width=1, border_radius=2)

        elif self.kind == "oil":
            # Dark iridescent oil slick on asphalt
            oil_w = max(8, int(scale * 600.0))
            oil_h = max(3, int(oil_w * 0.35))
            if oil_w < 4 or oil_w > 350:
                return
            rect = pygame.Rect(cx - oil_w // 2, cy - oil_h // 2, oil_w, oil_h)
            pygame.draw.ellipse(surface, (25, 20, 35), rect)
            pygame.draw.ellipse(surface, (60, 40, 80), rect.inflate(-oil_w // 4, -oil_h // 4))


class TrafficManager:
    """Manages active cars and obstacles on the track."""

    def __init__(self, track_length: int, total_world_len: float):
        self.track_length = track_length
        self.total_world_len = total_world_len
        self.cars: List[OpponentCar] = []
        self.obstacles: List[RoadObstacle] = []
        self.populate_traffic()

    def populate_traffic(self, count_cars: int = 14, count_obstacles: int = 12):
        """Distribute AI cars and hazards across track."""
        self.cars.clear()
        self.obstacles.clear()

        # Distribute opponent cars
        lanes = [-0.65, 0.0, 0.65]
        spacing = self.total_world_len / (count_cars + 2)

        for i in range(count_cars):
            z = (i + 1) * spacing + random.uniform(-100, 100)
            lane = lanes[i % len(lanes)]
            speed = random.uniform(80.0, 140.0)
            self.cars.append(OpponentCar(z=z, x=lane, speed_kmh=speed, color_idx=i))

        # Distribute road obstacles
        obs_spacing = self.total_world_len / (count_obstacles + 2)
        for i in range(count_obstacles):
            z = (i + 0.5) * obs_spacing + random.uniform(-150, 150)
            lane = random.choice([-0.7, -0.35, 0.0, 0.35, 0.7])
            kind = random.choice(["cone", "barrier", "oil"])
            self.obstacles.append(RoadObstacle(z=z, x=lane, kind=kind))

    def update(self, dt: float):
        """Update traffic movements."""
        for car in self.cars:
            car.update(dt, self.total_world_len)
