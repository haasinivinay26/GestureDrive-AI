"""
Core Game Engine for GestureDrive AI.
Integrates Road rendering, Player vehicle physics, Traffic AI, Collision detection,
Audio modulation, Hand Tracking inputs, and Keyboard fallback.
"""

import time
import pygame
from typing import Optional, Tuple

from config import (
    WINDOW_WIDTH, WINDOW_HEIGHT, SETTINGS,
    COLOR_NEON_GREEN, COLOR_NEON_RED, COLOR_NEON_CYAN,
    COLOR_TEXT_WHITE
)
from camera.camera_manager import CameraManager
from camera.gesture_recognizer import GestureState
from game.road import TrackManager
from game.car import PlayerCar
from game.obstacles import TrafficManager
from game.collision import CollisionSystem
from game.scoring import ScoringSystem
from utils.audio import AUDIO
from utils.helpers import render_text_with_shadow


class EngineState:
    COUNTDOWN = "COUNTDOWN"
    RACING = "RACING"
    PAUSED = "PAUSED"
    GAME_OVER = "GAME_OVER"


class GameEngine:
    """Orchestrates real-time gameplay simulation, input mapping, and 3D rendering."""

    def __init__(self, camera_mgr: CameraManager):
        self.camera_mgr = camera_mgr
        self.state = EngineState.COUNTDOWN
        self.countdown_timer = 3.6  # 3, 2, 1, GO
        self.last_beep_second = 4

        # Subsystems
        self.track = TrackManager()
        self.car = PlayerCar()
        self.traffic = TrafficManager(self.track.track_length, self.track.total_world_length)
        self.collision = CollisionSystem()
        self.scoring = ScoringSystem()

        # Fonts
        self.font_countdown = pygame.font.SysFont("Impact", 84)
        self.font_overlay = pygame.font.SysFont("Verdana", 28, bold=True)

        # Health / Collisions
        self.lives = 3
        self.is_race_finished = False

    def start_new_race(self):
        """Prepare fresh state for a new race."""
        self.state = EngineState.COUNTDOWN
        self.countdown_timer = 3.6
        self.last_beep_second = 4
        self.lives = 3
        self.is_race_finished = False

        self.car.reset()
        self.collision.reset()
        self.scoring.reset()
        self.traffic.populate_traffic()

        AUDIO.start_engine()

    def update(self, dt: float) -> Optional[str]:
        """
        Advance game simulation.
        Returns:
            "RESULTS" if race completed or game over.
            None to continue.
        """
        if self.state == EngineState.PAUSED:
            return None

        # Handle Countdown State
        if self.state == EngineState.COUNTDOWN:
            self.countdown_timer -= dt
            sec = int(self.countdown_timer)
            if sec != self.last_beep_second and sec in (3, 2, 1):
                AUDIO.play("beep", volume=0.8)
                self.last_beep_second = sec
            elif self.countdown_timer <= 0.0 and self.last_beep_second != 0:
                AUDIO.play("go", volume=1.0)
                self.last_beep_second = 0
                self.state = EngineState.RACING
            return None

        if self.state != EngineState.RACING:
            return None

        # 1. Retrieve Hand Gesture Telemetry
        gesture_state: GestureState = self.camera_mgr.get_state()
        steer_input = gesture_state.steer_angle
        is_accel = gesture_state.is_accelerating
        is_brake = gesture_state.is_braking

        # 2. Keyboard Fallback (if enabled or camera disconnected)
        if SETTINGS.keyboard_fallback_enabled or not self.camera_mgr.is_connected:
            keys = pygame.key.get_pressed()
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                steer_input = -1.0 * SETTINGS.steering_sensitivity
            elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                steer_input = 1.0 * SETTINGS.steering_sensitivity

            if keys[pygame.K_UP] or keys[pygame.K_w]:
                is_accel = True
            if keys[pygame.K_DOWN] or keys[pygame.K_s] or keys[pygame.K_SPACE]:
                is_brake = True

        # Priority Check: Braking strictly overrides acceleration
        if is_brake:
            is_accel = False

        # 3. Update Car Physics
        current_segment = self.track.get_segment(self.car.z)
        self.car.update(dt, steer_input, is_accel, is_brake, current_segment.curve)

        # 4. Update Traffic AI
        self.traffic.update(dt)

        # 5. Collision and Near-Miss Detection
        has_collided, is_near_miss = self.collision.check_collisions(
            self.car, self.traffic, self.track.total_world_length
        )
        if is_near_miss:
            self.scoring.add_near_miss()

        if has_collided:
            self.scoring.on_crash()
            self.lives -= 1
            if self.lives <= 0:
                # Race finished
                self.state = EngineState.GAME_OVER
                self.scoring.finalize_race()
                AUDIO.stop_engine()
                return "RESULTS"

        # 6. Update Scoring and Distance
        self.scoring.update(dt, self.car.speed)

        # 7. Update Audio Engine Pitch
        AUDIO.update_engine(self.car.speed / self.car.max_speed)
        AUDIO.set_brake_sound(is_brake and self.car.speed > 40.0)

        return None

    def render(self, surface: pygame.Surface):
        """Render 3D racing world and entities."""
        # 1. Update screen shake and sparks
        dt = 1.0 / 60.0  # nominal dt for visual shake
        shake_x, shake_y = self.collision.update(dt)

        # Apply screen shake offset to a rendering canvas if shaking
        if shake_x != 0 or shake_y != 0:
            render_surf = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        else:
            render_surf = surface

        # 2. Render Road and Roadside Scenery
        current_seg = self.track.get_segment(self.car.z)
        self.track.render(render_surf, self.car.x, self.car.z, current_seg.world_y)

        # 3. Render Projected Traffic and Hazards
        self._render_traffic_entities(render_surf)

        # 4. Render Player Sports Car
        gesture_state = self.camera_mgr.get_state()
        is_brake = gesture_state.is_braking or (
            SETTINGS.keyboard_fallback_enabled and (
                pygame.key.get_pressed()[pygame.K_DOWN] or
                pygame.key.get_pressed()[pygame.K_s] or
                pygame.key.get_pressed()[pygame.K_SPACE]
            )
        )
        is_accel = gesture_state.is_accelerating or (
            SETTINGS.keyboard_fallback_enabled and (
                pygame.key.get_pressed()[pygame.K_UP] or
                pygame.key.get_pressed()[pygame.K_w]
            )
        )
        if is_brake:
            is_accel = False

        self.car.draw(render_surf, is_brake, is_accel)

        # 5. Render Collision Sparks
        self.collision.draw(render_surf)

        # Blit shaken canvas to target surface if active
        if shake_x != 0 or shake_y != 0:
            surface.fill((0, 0, 0))
            surface.blit(render_surf, (shake_x, shake_y))

        # 6. Countdown Overlay
        if self.state == EngineState.COUNTDOWN:
            self._render_countdown_overlay(surface)

        # 7. Near Miss Notification Banner
        if self.collision.near_miss_timer > 0:
            banner = render_text_with_shadow(
                self.font_overlay, self.collision.last_near_miss_text,
                COLOR_NEON_GREEN, (0, 0, 0), (2, 2)
            )
            surface.blit(banner, (WINDOW_WIDTH // 2 - banner.get_width() // 2, 220))

    def _render_traffic_entities(self, surface: pygame.Surface):
        """Project and draw opponent cars and static hazards."""
        player_z = self.car.z
        total_len = self.track.total_world_length

        # Collect entities situated in front of camera
        to_draw = []

        for car in self.traffic.cars:
            dz = car.z - player_z
            if dz < 0:
                dz += total_len
            if 0 < dz < 18000:  # Within view distance
                seg = self.track.get_segment(car.z)
                to_draw.append((dz, "car", car, seg))

        for obs in self.traffic.obstacles:
            dz = obs.z - player_z
            if dz < 0:
                dz += total_len
            if 0 < dz < 18000:
                seg = self.track.get_segment(obs.z)
                to_draw.append((dz, "obstacle", obs, seg))

        # Sort back-to-front (largest dz first)
        to_draw.sort(key=lambda item: item[0], reverse=True)

        for dz, kind, entity, seg in to_draw:
            # Calculate screen projection
            scale = 0.84 / dz
            sx = (WINDOW_WIDTH * 0.5) + (scale * (entity.x - self.car.x) * 2000.0 * (WINDOW_WIDTH * 0.5))
            sy = (WINDOW_HEIGHT * 0.5) - (scale * (seg.world_y - (1000 + self.track.get_segment(player_z).world_y)) * (WINDOW_HEIGHT * 0.5))

            if kind == "car":
                entity.draw(surface, sx, sy, scale)
            else:
                entity.draw(surface, sx, sy, scale)

    def _render_countdown_overlay(self, surface: pygame.Surface):
        """Draw 3-2-1-GO! countdown display."""
        sec = int(self.countdown_timer)
        text = str(sec) if sec > 0 else "GO!"
        color = COLOR_NEON_GREEN if text == "GO!" else COLOR_NEON_CYAN

        surf = render_text_with_shadow(self.font_countdown, text, color, (0, 0, 0), (4, 4))
        surface.blit(surf, (WINDOW_WIDTH // 2 - surf.get_width() // 2, WINDOW_HEIGHT // 2 - 120))
