"""
Main Menu Screen for GestureDrive AI.
Features high-impact cyber typography, animated perspective grid background,
sound-responsive interactive buttons, and an interactive Start Gesture detection HUD.
"""

import math
import pygame
from typing import Optional, Callable

from config import (
    WINDOW_WIDTH, WINDOW_HEIGHT, GAME_TITLE, TAGLINE,
    COLOR_NEON_CYAN, COLOR_NEON_GREEN, COLOR_NEON_RED, COLOR_NEON_AMBER,
    COLOR_TEXT_WHITE, COLOR_TEXT_MUTED
)
from ui.components import UIButton
from utils.helpers import render_text_with_shadow, draw_glow_rect, draw_rounded_rect


class MainMenu:
    """Manages the main menu screen, animations, and starting gesture listener."""

    def __init__(self, on_action: Callable[[str], None]):
        self.on_action = on_action
        self.anim_timer = 0.0
        self.start_hold_timer = 0.0
        self.start_required_duration = 1.0  # Hold for 1 second to start
        self.start_triggered = False

        # Fonts
        self.font_title = pygame.font.SysFont("Impact", 74)
        self.font_tagline = pygame.font.SysFont("Verdana", 19, bold=True)
        self.font_button = pygame.font.SysFont("Verdana", 17, bold=True)
        self.font_footer = pygame.font.SysFont("Verdana", 13)
        self.font_gesture_title = pygame.font.SysFont("Verdana", 15, bold=True)
        self.font_gesture_sub = pygame.font.SysFont("Verdana", 13)

        # Buttons configuration
        btn_w, btn_h = 320, 48
        start_y = 265
        gap = 58
        cx = WINDOW_WIDTH // 2 - btn_w // 2

        self.buttons = [
            UIButton(pygame.Rect(cx, start_y + 0 * gap, btn_w, btn_h), "1. START RACE", self.font_button, lambda: self.on_action("START_RACE"), primary=True),
            UIButton(pygame.Rect(cx, start_y + 1 * gap, btn_w, btn_h), "2. CAMERA TEST", self.font_button, lambda: self.on_action("CAMERA_TEST")),
            UIButton(pygame.Rect(cx, start_y + 2 * gap, btn_w, btn_h), "3. GESTURE CALIBRATION", self.font_button, lambda: self.on_action("CALIBRATION")),
            UIButton(pygame.Rect(cx, start_y + 3 * gap, btn_w, btn_h), "4. HOW TO PLAY", self.font_button, lambda: self.on_action("HOW_TO_PLAY")),
            UIButton(pygame.Rect(cx, start_y + 4 * gap, btn_w, btn_h), "5. SETTINGS", self.font_button, lambda: self.on_action("SETTINGS")),
            UIButton(pygame.Rect(cx, start_y + 5 * gap, btn_w, btn_h), "6. EXIT GAME", self.font_button, lambda: self.on_action("EXIT")),
        ]

    def reset_start_gesture(self):
        """Reset the starting gesture state when returning to the main menu."""
        self.start_hold_timer = 0.0
        self.start_triggered = False

    def handle_event(self, event: pygame.event.Event):
        """Process input events."""
        for btn in self.buttons:
            if btn.handle_event(event):
                break

    def update(self, dt: float, is_start_gesture_active: bool = False) -> bool:
        """
        Update animation and handle start gesture trigger.
        Returns True if the race was triggered by gesture.
        """
        self.anim_timer += dt
        mouse_pos = pygame.mouse.get_pos()
        for btn in self.buttons:
            btn.update(dt, mouse_pos)

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
        """Draw main menu interface with interactive start-ready HUD."""
        # 1. Animated Cyber Horizon and Grid
        self._render_cyber_grid(surface)

        # 2. Glowing Title and Tagline
        title_y = 65
        pulse = 0.5 + 0.5 * math.sin(self.anim_timer * 3.0)
        glow_color = (int(0 + 40 * pulse), int(220 + 35 * pulse), 255)

        title_surf = render_text_with_shadow(self.font_title, GAME_TITLE, glow_color, (0, 0, 0), (4, 4))
        surface.blit(title_surf, (WINDOW_WIDTH // 2 - title_surf.get_width() // 2, title_y))

        tag_surf = self.font_tagline.render(TAGLINE, True, COLOR_TEXT_WHITE)
        surface.blit(tag_surf, (WINDOW_WIDTH // 2 - tag_surf.get_width() // 2, title_y + 88))

        # 3. Expo Badge
        expo_text = self.font_footer.render("COLLEGE TECH EXPO EDITION  |  PYTHON + MEDIAPIPE + OPENCV", True, COLOR_NEON_GREEN)
        surface.blit(expo_text, (WINDOW_WIDTH // 2 - expo_text.get_width() // 2, title_y + 118))

        # 4. Camera Status Indicator (Top Right)
        status_x = WINDOW_WIDTH - 240
        status_rect = pygame.Rect(status_x, 20, 220, 32)
        draw_glow_rect(surface, status_rect, (18, 22, 34), (45, 55, 80), radius=6, glow_spread=1)
        dot_c = COLOR_NEON_GREEN if is_camera_connected else COLOR_NEON_AMBER
        pygame.draw.circle(surface, dot_c, (status_x + 16, 36), 6)
        status_msg = "WEBCAM ONLINE" if is_camera_connected else "KEYBOARD FALLBACK"
        msg_surf = self.font_footer.render(status_msg, True, COLOR_TEXT_WHITE)
        surface.blit(msg_surf, (status_x + 28, 28))

        # 5. START READY / GESTURE STATUS BANNER (Center)
        self._render_start_gesture_card(surface, gesture_state)

        # 6. Menu Buttons
        for btn in self.buttons:
            btn.draw(surface)

        # 7. Footer Controls Hint
        hint = self.font_footer.render("Use mouse or press 1-6 keys  |  Show ✌️ Victory Sign to Start  |  ESC to go back", True, COLOR_TEXT_MUTED)
        surface.blit(hint, (WINDOW_WIDTH // 2 - hint.get_width() // 2, WINDOW_HEIGHT - 28))

    def _render_start_gesture_card(self, surface: pygame.Surface, gesture_state):
        """Render prominent START READY gesture prompt and hold progress."""
        card_w, card_h = 620, 62
        card_x = WINDOW_WIDTH // 2 - card_w // 2
        card_y = 180
        rect = pygame.Rect(card_x, card_y, card_w, card_h)

        is_start_active = getattr(gesture_state, "is_start_gesture", False) if gesture_state else False
        active_gesture_name = getattr(gesture_state, "active_gesture", "NEUTRAL") if gesture_state else "NEUTRAL"
        progress = min(1.0, self.start_hold_timer / max(0.1, self.start_required_duration))

        if self.start_triggered:
            glow_c = COLOR_NEON_GREEN
            status_text = "START ACCEPTED! LAUNCHING RACE..."
            sub_text = "Get ready to drive!"
        elif is_start_active:
            glow_c = COLOR_NEON_GREEN if progress > 0.5 else COLOR_NEON_AMBER
            status_text = f"START READY: [START GESTURE DETECTED] - HOLDING ({int(progress * 100)}%)"
            sub_text = "Hold steady for 1 second to start race..."
        else:
            glow_c = COLOR_NEON_CYAN
            status_text = "START READY: SHOW ✌️ VICTORY SIGN TO START RACE"
            sub_text = f"Or hold both hands on wheel  |  Camera: {active_gesture_name}"

        draw_glow_rect(surface, rect, (20, 24, 36), glow_c, radius=8, glow_spread=2 if is_start_active else 1)

        t_surf = self.font_gesture_title.render(status_text, True, glow_c)
        surface.blit(t_surf, (card_x + 20, card_y + 10))

        s_surf = self.font_gesture_sub.render(sub_text, True, COLOR_TEXT_MUTED)
        surface.blit(s_surf, (card_x + 20, card_y + 34))

        # Progress bar at bottom of card
        if is_start_active and progress > 0:
            bar_w = int((card_w - 40) * progress)
            bar_rect = pygame.Rect(card_x + 20, card_y + card_h - 8, bar_w, 4)
            draw_rounded_rect(surface, bar_rect, glow_c, radius=2)

    def _render_cyber_grid(self, surface: pygame.Surface):
        """Draw retro-futuristic horizon with moving ground lines."""
        surface.fill((12, 14, 22))
        w, h = WINDOW_WIDTH, WINDOW_HEIGHT
        horizon_y = int(h * 0.42)

        # Sky
        pygame.draw.rect(surface, (15, 18, 30), (0, 0, w, horizon_y))

        # Moving road / ground perspective
        ground_rect = pygame.Rect(0, horizon_y, w, h - horizon_y)
        pygame.draw.rect(surface, (18, 22, 36), ground_rect)

        # Moving horizontal lines
        line_offset = (self.anim_timer * 120.0) % 60.0
        y = horizon_y
        while y < h:
            norm = (y - horizon_y) / max(1, (h - horizon_y))
            spacing = 15.0 + norm * 85.0
            y += spacing
            draw_y = int(y - line_offset * norm)
            if horizon_y < draw_y < h:
                color = (30 + int(30 * norm), 45 + int(50 * norm), 80 + int(80 * norm))
                pygame.draw.line(surface, color, (0, draw_y), (w, draw_y), 1)

        # Vanishing point radial grid lines
        center_x = w // 2
        for x in range(0, w + 1, 140):
            pygame.draw.line(surface, (30, 40, 65), (center_x, horizon_y), (x, h), 1)
