"""
Main Menu & Showcase Landing Screen for GestureDrive AI.
Features high-impact cyber racing typography, a procedural showcase supercar
parked on an asphalt track with neon reflections, animated atmospheric particles,
prominent navigation buttons, live webcam status, and an interactive Start Gesture HUD.
"""

import math
import random
import pygame
from typing import Optional, Callable, List

from config import (
    WINDOW_WIDTH, WINDOW_HEIGHT,
    COLOR_NEON_CYAN, COLOR_NEON_GREEN, COLOR_NEON_RED, COLOR_NEON_AMBER,
    COLOR_TEXT_WHITE, COLOR_TEXT_MUTED, COLOR_PANEL_BORDER
)
from ui.components import UIButton
from utils.helpers import render_text_with_shadow, draw_glow_rect, draw_rounded_rect, draw_glass_rect, clamp


class AtmosphericParticle:
    """Subtle floating cyber light motes for background ambiance."""
    def __init__(self):
        self.x = random.uniform(0, WINDOW_WIDTH)
        self.y = random.uniform(0, WINDOW_HEIGHT)
        self.vx = random.uniform(-15, 15)
        self.vy = random.uniform(-25, -5)
        self.radius = random.uniform(1.2, 2.8)
        self.alpha = random.uniform(40, 140)
        self.color = random.choice([(0, 240, 255), (0, 140, 255), (255, 180, 50)])

    def update(self, dt: float):
        self.x += self.vx * dt
        self.y += self.vy * dt
        if self.y < 0:
            self.y = WINDOW_HEIGHT
            self.x = random.uniform(0, WINDOW_WIDTH)
        if self.x < 0:
            self.x = WINDOW_WIDTH
        elif self.x > WINDOW_WIDTH:
            self.x = 0

    def draw(self, surface: pygame.Surface):
        glow_surf = pygame.Surface((int(self.radius * 4), int(self.radius * 4)), pygame.SRCALPHA)
        color_rgba = (*self.color, int(self.alpha))
        pygame.draw.circle(glow_surf, color_rgba, (int(self.radius * 2), int(self.radius * 2)), int(self.radius))
        surface.blit(glow_surf, (int(self.x - self.radius * 2), int(self.y - self.radius * 2)))


class MainMenu:
    """Manages the full-screen landing page, showcase car, animations, and starting gesture listener."""

    def __init__(self, on_action: Callable[[str], None]):
        self.on_action = on_action
        self.anim_timer = 0.0
        self.start_hold_timer = 0.0
        self.start_required_duration = 1.0  # Hold for 1 second to start
        self.start_triggered = False

        # Background particles
        self.particles: List[AtmosphericParticle] = [AtmosphericParticle() for _ in range(35)]

        # Fonts
        self.font_title = pygame.font.SysFont("Impact", 78)
        self.font_tagline = pygame.font.SysFont("Verdana", 17, bold=True)
        self.font_expo = pygame.font.SysFont("Verdana", 11, bold=True)
        self.font_btn_primary = pygame.font.SysFont("Verdana", 18, bold=True)
        self.font_btn = pygame.font.SysFont("Verdana", 15, bold=True)
        self.font_btn_small = pygame.font.SysFont("Verdana", 13, bold=True)
        self.font_footer = pygame.font.SysFont("Verdana", 12)
        self.font_guide_title = pygame.font.SysFont("Verdana", 13, bold=True)
        self.font_guide_body = pygame.font.SysFont("Verdana", 11)
        self.font_gesture_title = pygame.font.SysFont("Verdana", 14, bold=True)
        self.font_gesture_sub = pygame.font.SysFont("Verdana", 12)

        # Buttons configuration (Positioned cleanly on the right half to leave supercar visible)
        btn_w = 340
        btn_x = WINDOW_WIDTH - btn_w - 70
        btn_y_start = 220
        gap = 56

        self.buttons = [
            UIButton(
                pygame.Rect(btn_x, btn_y_start, btn_w, 54),
                "START RACE", self.font_btn_primary,
                lambda: self.on_action("START_RACE"),
                primary=True,
                accent_color=COLOR_NEON_CYAN,
                shortcut="[1]"
            ),
            UIButton(
                pygame.Rect(btn_x, btn_y_start + gap, btn_w, 48),
                "HOW TO PLAY", self.font_btn,
                lambda: self.on_action("HOW_TO_PLAY"),
                shortcut="[2]"
            ),
            UIButton(
                pygame.Rect(btn_x, btn_y_start + gap * 2, btn_w, 48),
                "SETTINGS", self.font_btn,
                lambda: self.on_action("SETTINGS"),
                shortcut="[3]"
            ),
        ]

        # Secondary utility buttons row
        util_w = 106
        util_gap = 10
        util_y = btn_y_start + gap * 3 + 12
        self.util_buttons = [
            UIButton(
                pygame.Rect(btn_x, util_y, util_w, 38),
                "TEST CAM", self.font_btn_small,
                lambda: self.on_action("CAMERA_TEST"),
                shortcut="[4]"
            ),
            UIButton(
                pygame.Rect(btn_x + util_w + util_gap, util_y, util_w, 38),
                "CALIBRATE", self.font_btn_small,
                lambda: self.on_action("CALIBRATION"),
                shortcut="[5]"
            ),
            UIButton(
                pygame.Rect(btn_x + (util_w + util_gap) * 2, util_y, util_w, 38),
                "EXIT", self.font_btn_small,
                lambda: self.on_action("EXIT"),
                accent_color=COLOR_NEON_RED,
                shortcut="[6]"
            ),
        ]

    def reset_start_gesture(self):
        """Reset the starting gesture state when returning to the main menu."""
        self.start_hold_timer = 0.0
        self.start_triggered = False

    def handle_event(self, event: pygame.event.Event):
        """Process input events."""
        for btn in self.buttons:
            if btn.handle_event(event):
                return
        for btn in self.util_buttons:
            if btn.handle_event(event):
                return

    def update(self, dt: float, is_start_gesture_active: bool = False) -> bool:
        """
        Update animation and handle start gesture trigger.
        Returns True if the race was triggered by gesture.
        """
        self.anim_timer += dt
        mouse_pos = pygame.mouse.get_pos()

        # Update buttons
        for btn in self.buttons:
            btn.update(dt, mouse_pos)
        for btn in self.util_buttons:
            btn.update(dt, mouse_pos)

        # Update ambient particles
        for p in self.particles:
            p.update(dt)

        # Process Start Gesture Hold Progression
        if is_start_gesture_active and not self.start_triggered:
            self.start_hold_timer += dt
            if self.start_hold_timer >= self.start_required_duration:
                self.start_triggered = True
                self.on_action("START_RACE")
                return True
        else:
            self.start_hold_timer = max(0.0, self.start_hold_timer - dt * 2.0)

        return False

    def draw(self, surface: pygame.Surface, is_camera_connected: bool, gesture_state=None):
        """Draw modern full-screen racing game landing page."""
        # 1. Dark Racing Horizon and Track Base
        self._render_background(surface)

        # 2. Draw Atmospheric Particles
        for p in self.particles:
            p.draw(surface)

        # 3. Render 3D Showcase Supercar parked on the track
        self._render_showcase_supercar(surface)

        # 4. Top Header & Title Branding
        self._render_header(surface, is_camera_connected)

        # 5. START READY / GESTURE STATUS CARD
        self._render_start_gesture_card(surface, gesture_state)

        # 6. Navigation Buttons
        for btn in self.buttons:
            btn.draw(surface)
        for btn in self.util_buttons:
            btn.draw(surface)

        # 7. Compact Gesture Control Guide (Bottom Left)
        self._render_compact_control_guide(surface)

        # 8. Footer Controls Hint
        hint = self.font_footer.render("Press 1-6 keys or click  |  Show ✌️ Victory Sign or hands on wheel to Start  |  ESC to exit", True, COLOR_TEXT_MUTED)
        surface.blit(hint, (WINDOW_WIDTH // 2 - hint.get_width() // 2, WINDOW_HEIGHT - 24))

    def _render_background(self, surface: pygame.Surface):
        """Draw ultra-dark racing atmosphere with asphalt track and neon distance grid."""
        surface.fill((8, 10, 16))
        w, h = WINDOW_WIDTH, WINDOW_HEIGHT
        horizon_y = int(h * 0.40)

        # Sky gradient: Dark cosmic navy to dusk indigo
        pygame.draw.rect(surface, (10, 12, 22), (0, 0, w, horizon_y))

        # Distant neon horizon glow line
        glow_pulse = 0.5 + 0.5 * math.sin(self.anim_timer * 2.0)
        h_color = (int(0 + 20 * glow_pulse), int(120 + 40 * glow_pulse), 200)
        pygame.draw.line(surface, h_color, (0, horizon_y), (w, horizon_y), 2)

        # Subtle distant mountain/skyline silhouette
        pts = [
            (0, horizon_y),
            (120, horizon_y - 30),
            (260, horizon_y - 15),
            (380, horizon_y - 45),
            (520, horizon_y - 20),
            (700, horizon_y - 50),
            (900, horizon_y - 25),
            (1100, horizon_y - 40),
            (w, horizon_y)
        ]
        pygame.draw.polygon(surface, (14, 18, 32), pts)

        # Asphalt Track Perspective (extends towards left/center)
        track_y = horizon_y
        track_h = h - track_y
        track_rect = pygame.Rect(0, track_y, w, track_h)
        pygame.draw.rect(surface, (15, 18, 26), track_rect)

        # Perspective asphalt lane lines (moving forward gently)
        center_vx = int(w * 0.32)
        lane_offset = (self.anim_timer * 70.0) % 50.0

        for line_y_norm in [0.15, 0.32, 0.52, 0.75, 1.0]:
            ly = track_y + int(track_h * line_y_norm)
            curb_color = (25, 30, 44)
            pygame.draw.line(surface, curb_color, (0, ly), (w, ly), 1)

        # Angled track perspective boundaries
        pygame.draw.line(surface, (0, 180, 230), (center_vx, horizon_y), (40, h), 2)
        pygame.draw.line(surface, (0, 180, 230), (center_vx, horizon_y), (int(w * 0.62), h), 2)

        # Roadside neon barrier dashes
        curb_step = 40
        for i in range(12):
            cy = horizon_y + int((i / 12.0) ** 1.8 * track_h)
            dash_c = COLOR_NEON_CYAN if (i % 2 == 0) else COLOR_NEON_RED
            p1_x = int(center_vx + (40 - center_vx) * (cy - horizon_y) / max(1, track_h))
            pygame.draw.circle(surface, dash_c, (p1_x, cy), max(2, int(i * 0.5)))

    def _render_showcase_supercar(self, surface: pygame.Surface):
        """Draw an exotic, sleek sports supercar parked on the asphalt with neon reflections."""
        cx = int(WINDOW_WIDTH * 0.33)
        cy = int(WINDOW_HEIGHT * 0.66)

        # Subtle chassis idle breathing motion
        float_y = int(math.sin(self.anim_timer * 2.5) * 2.0)
        cy += float_y

        car_w = 340
        car_h = 160

        car_surf = pygame.Surface((car_w + 80, car_h + 80), pygame.SRCALPHA)
        lcx = (car_w + 80) // 2
        lcy = (car_h + 80) // 2

        # 1. Neon Cyan Underglow Reflection on Asphalt
        glow_pulse = 0.7 + 0.3 * math.sin(self.anim_timer * 3.0)
        underglow_rect = pygame.Rect(lcx - car_w // 2 - 10, lcy + 30, car_w + 20, 36)
        underglow_c = (0, int(200 * glow_pulse), int(255 * glow_pulse), 75)
        pygame.draw.ellipse(car_surf, underglow_c, underglow_rect)

        # 2. Drop Shadow beneath tires and chassis
        shadow_rect = pygame.Rect(lcx - car_w // 2 + 15, lcy + 38, car_w - 30, 24)
        pygame.draw.ellipse(car_surf, (5, 6, 10, 220), shadow_rect)

        # 3. Wide Racing Slicks (Left & Right)
        tire_w, tire_h = 44, 76
        # Left tire
        pygame.draw.rect(car_surf, (18, 20, 26), (lcx - car_w // 2 + 10, lcy + 2, tire_w, tire_h), border_radius=8)
        pygame.draw.rect(car_surf, (35, 40, 52), (lcx - car_w // 2 + 18, lcy + 14, 20, 50), border_radius=4)
        # Cyan brake caliper
        pygame.draw.rect(car_surf, COLOR_NEON_CYAN, (lcx - car_w // 2 + 30, lcy + 26, 6, 26), border_radius=2)

        # Right tire
        pygame.draw.rect(car_surf, (18, 20, 26), (lcx + car_w // 2 - tire_w - 10, lcy + 2, tire_w, tire_h), border_radius=8)
        pygame.draw.rect(car_surf, (35, 40, 52), (lcx + car_w // 2 - tire_w + 6, lcy + 14, 20, 50), border_radius=4)
        pygame.draw.rect(car_surf, COLOR_NEON_CYAN, (lcx + car_w // 2 - tire_w + 8, lcy + 26, 6, 26), border_radius=2)

        # 4. Aerodynamic Rear Diffuser with vertical carbon fins
        diffuser_rect = pygame.Rect(lcx - 90, lcy + 42, 180, 22)
        pygame.draw.rect(car_surf, (12, 15, 22), diffuser_rect, border_radius=4)
        for fx in range(-70, 71, 35):
            pygame.draw.rect(car_surf, (25, 30, 42), (lcx + fx - 2, lcy + 42, 5, 22))

        # 5. Dual Polished Exhaust Outlets with Idle Sparks
        ex_l = (lcx - 55, lcy + 48)
        ex_r = (lcx + 55, lcy + 48)
        pygame.draw.circle(car_surf, (180, 190, 210), ex_l, 9)
        pygame.draw.circle(car_surf, (20, 24, 32), ex_l, 6)
        pygame.draw.circle(car_surf, (180, 190, 210), ex_r, 9)
        pygame.draw.circle(car_surf, (20, 24, 32), ex_r, 6)

        # Exhaust idle heat glow
        flame_pulse = 0.5 + 0.5 * math.sin(self.anim_timer * 8.0)
        flame_c = (255, int(140 * flame_pulse), 30, int(150 * flame_pulse))
        pygame.draw.circle(car_surf, flame_c, ex_l, int(5 + 3 * flame_pulse))
        pygame.draw.circle(car_surf, flame_c, ex_r, int(5 + 3 * flame_pulse))

        # 6. Main Hypercar Body Chassis (Sculptured Widebody)
        body_points = [
            (lcx - 130, lcy + 44),  # Bottom left flare
            (lcx - 150, lcy + 10),  # Mid left wheel arch
            (lcx - 120, lcy - 20),  # Upper haunch left
            (lcx - 75, lcy - 48),   # Roofline left
            (lcx + 75, lcy - 48),   # Roofline right
            (lcx + 120, lcy - 20),  # Upper haunch right
            (lcx + 150, lcy + 10),  # Mid right wheel arch
            (lcx + 130, lcy + 44),  # Bottom right flare
        ]
        # Cyber Midnight Blue body
        pygame.draw.polygon(car_surf, (14, 45, 110), body_points)
        # Metallic sheen highlight
        pygame.draw.lines(car_surf, (40, 120, 240), True, body_points, width=3)

        # 7. Tinted Aerodynamic Glass Canopy
        canopy_points = [
            (lcx - 65, lcy - 44),
            (lcx + 65, lcy - 44),
            (lcx + 85, lcy - 12),
            (lcx - 85, lcy - 12),
        ]
        pygame.draw.polygon(car_surf, (18, 26, 44), canopy_points)
        pygame.draw.lines(car_surf, (80, 150, 230), True, canopy_points, width=2)
        # Glass reflection sweep line
        pygame.draw.line(car_surf, (140, 200, 255, 180), (lcx - 40, lcy - 40), (lcx + 20, lcy - 16), 2)

        # 8. Continuous Horizon LED Lightbar (Modern Hypercar Taillight)
        # Continuous glowing LED ribbon
        lightbar_points = [
            (lcx - 125, lcy + 4),
            (lcx - 50, lcy + 14),
            (lcx + 50, lcy + 14),
            (lcx + 125, lcy + 4)
        ]
        pygame.draw.lines(car_surf, (255, 30, 60), False, lightbar_points, width=5)
        # Outer soft glow bloom
        lightbar_surf = pygame.Surface((car_w + 80, car_h + 80), pygame.SRCALPHA)
        pygame.draw.lines(lightbar_surf, (255, 60, 90, 90), False, lightbar_points, width=12)
        car_surf.blit(lightbar_surf, (0, 0))

        # 9. Carbon-Fiber GT Rear Wing & Endplates
        wing_w = 260
        wing_y = lcy - 56
        # Struts
        pygame.draw.rect(car_surf, (15, 20, 30), (lcx - 65, wing_y + 10, 10, 18))
        pygame.draw.rect(car_surf, (15, 20, 30), (lcx + 55, wing_y + 10, 10, 18))
        # Wing plank
        wing_rect = pygame.Rect(lcx - wing_w // 2, wing_y, wing_w, 12)
        pygame.draw.rect(car_surf, (10, 14, 22), wing_rect, border_radius=4)
        pygame.draw.rect(car_surf, COLOR_NEON_CYAN, (lcx - wing_w // 2, wing_y, wing_w, 2))
        # Wing endplate aero stabilizers
        pygame.draw.rect(car_surf, COLOR_NEON_CYAN, (lcx - wing_w // 2, wing_y - 6, 6, 24), border_radius=2)
        pygame.draw.rect(car_surf, COLOR_NEON_CYAN, (lcx + wing_w // 2 - 6, wing_y - 6, 6, 24), border_radius=2)

        # Blit showcase car to main surface
        surface.blit(car_surf, (cx - (car_w + 80) // 2, cy - (car_h + 80) // 2))

    def _render_header(self, surface: pygame.Surface, is_camera_connected: bool):
        """Draw game title, expo edition subtitle, and hardware status indicator."""
        # Game Title: GESTURE DRIVE
        pulse = 0.5 + 0.5 * math.sin(self.anim_timer * 2.5)
        glow_color = (int(0 + 40 * pulse), int(220 + 35 * pulse), 255)

        title_x = 70
        title_y = 35

        title_surf = render_text_with_shadow(self.font_title, "GESTURE DRIVE", glow_color, (0, 0, 0), (4, 4))
        surface.blit(title_surf, (title_x, title_y))

        # Tagline: "Your Hands. Your Controls. Your Race."
        tagline_text = "Your Hands. Your Controls. Your Race."
        tag_surf = self.font_tagline.render(tagline_text, True, COLOR_TEXT_WHITE)
        surface.blit(tag_surf, (title_x + 4, title_y + 88))

        # College Tech Expo Badge Pill
        expo_pill = pygame.Rect(title_x + 4, title_y + 120, 390, 24)
        draw_glass_rect(surface, expo_pill, bg_rgba=(15, 25, 45, 200), border_color=(0, 180, 255), radius=12)
        expo_lbl = self.font_expo.render("COLLEGE TECH EXPO 2026  •  AI COMPUTER VISION RACING", True, COLOR_NEON_CYAN)
        surface.blit(expo_lbl, (expo_pill.centerx - expo_lbl.get_width() // 2, expo_pill.centery - expo_lbl.get_height() // 2))

        # Top-Right Hardware Webcam Status Indicator Pill
        status_w, status_h = 240, 36
        status_x = WINDOW_WIDTH - status_w - 70
        status_y = 38
        status_rect = pygame.Rect(status_x, status_y, status_w, status_h)

        status_border = COLOR_NEON_GREEN if is_camera_connected else COLOR_NEON_AMBER
        draw_glass_rect(surface, status_rect, bg_rgba=(18, 24, 38, 220), border_color=status_border, radius=18)

        # Blinking green/amber dot
        dot_c = COLOR_NEON_GREEN if is_camera_connected else COLOR_NEON_AMBER
        dot_pulse = 0.6 + 0.4 * math.sin(self.anim_timer * 4.0)
        pygame.draw.circle(surface, dot_c, (status_x + 18, status_y + status_h // 2), int(5 * dot_pulse))

        status_msg = "WEBCAM ONLINE (30 FPS)" if is_camera_connected else "KEYBOARD FALLBACK ON"
        msg_surf = self.font_expo.render(status_msg, True, COLOR_TEXT_WHITE)
        surface.blit(msg_surf, (status_x + 32, status_y + status_h // 2 - msg_surf.get_height() // 2))

    def _render_start_gesture_card(self, surface: pygame.Surface, gesture_state):
        """Render prominent START READY gesture prompt and hold progress bar."""
        card_w = 340
        card_h = 60
        card_x = WINDOW_WIDTH - card_w - 70
        card_y = 145
        rect = pygame.Rect(card_x, card_y, card_w, card_h)

        is_start_active = getattr(gesture_state, "is_start_gesture", False) if gesture_state else False
        active_gesture_name = getattr(gesture_state, "active_gesture", "NEUTRAL") if gesture_state else "NEUTRAL"
        progress = min(1.0, self.start_hold_timer / max(0.1, self.start_required_duration))

        if self.start_triggered:
            glow_c = COLOR_NEON_GREEN
            status_text = "START ACCEPTED! LAUNCHING..."
            sub_text = "Get ready to drive!"
        elif is_start_active:
            glow_c = COLOR_NEON_GREEN if progress > 0.5 else COLOR_NEON_AMBER
            status_text = f"START GESTURE HELD ({int(progress * 100)}%)"
            sub_text = "Hold steady 1 second to start..."
        else:
            glow_c = COLOR_NEON_CYAN
            status_text = "SHOW ✌️ TO START RACE"
            sub_text = f"Or grip wheel  |  Camera: {active_gesture_name}"

        draw_glow_rect(surface, rect, (20, 26, 40), glow_c, radius=8, glow_spread=2 if is_start_active else 1)

        t_surf = self.font_gesture_title.render(status_text, True, glow_c)
        surface.blit(t_surf, (card_x + 16, card_y + 8))

        s_surf = self.font_gesture_sub.render(sub_text, True, COLOR_TEXT_MUTED)
        surface.blit(s_surf, (card_x + 16, card_y + 30))

        # Progress bar at bottom of card
        if is_start_active and progress > 0:
            bar_w = int((card_w - 32) * progress)
            bar_rect = pygame.Rect(card_x + 16, card_y + card_h - 7, bar_w, 4)
            draw_rounded_rect(surface, bar_rect, glow_c, radius=2)

    def _render_compact_control_guide(self, surface: pygame.Surface):
        """Render a compact 4-card gesture control guide on the lower screen."""
        guide_y = WINDOW_HEIGHT - 98
        card_w = 175
        card_h = 64
        gap = 14
        start_x = 70

        guides = [
            ("STEER WHEEL", "Tilt hands left / right", COLOR_NEON_CYAN, "🖐️"),
            ("ACCELERATE", "Thumbs-up gesture", COLOR_NEON_GREEN, "👍"),
            ("BRAKE / STOP", "Open palm (overrides accel)", COLOR_NEON_RED, "✋"),
            ("START RACE", "Hold ✌️ Peace sign 1s", COLOR_NEON_AMBER, "✌️"),
        ]

        for i, (title, desc, color, icon) in enumerate(guides):
            cx = start_x + i * (card_w + gap)
            rect = pygame.Rect(cx, guide_y, card_w, card_h)
            draw_glass_rect(surface, rect, bg_rgba=(16, 20, 32, 210), border_color=(35, 45, 68), radius=8)

            # Left color accent bar
            bar_rect = pygame.Rect(cx + 4, guide_y + 6, 3, card_h - 12)
            draw_rounded_rect(surface, bar_rect, color, radius=1)

            # Title
            t_surf = self.font_guide_title.render(f"{icon} {title}", True, color)
            surface.blit(t_surf, (cx + 14, guide_y + 10))

            # Desc
            d_surf = self.font_guide_body.render(desc, True, COLOR_TEXT_MUTED)
            surface.blit(d_surf, (cx + 14, guide_y + 34))
