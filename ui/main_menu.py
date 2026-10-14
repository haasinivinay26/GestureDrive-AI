"""
Main Menu Screen for GestureDrive AI.
Features high-impact cyber typography, animated perspective grid background,
sound-responsive interactive buttons, and tech expo demonstration branding.
"""

import math
import pygame
from typing import Optional, Callable

from config import (
    WINDOW_WIDTH, WINDOW_HEIGHT, GAME_TITLE, TAGLINE,
    COLOR_NEON_CYAN, COLOR_NEON_GREEN, COLOR_NEON_RED,
    COLOR_TEXT_WHITE, COLOR_TEXT_MUTED
)
from ui.components import UIButton
from utils.helpers import render_text_with_shadow, draw_glow_rect


class MainMenu:
    """Manages the main menu screen, animations, and user navigation."""

    def __init__(self, on_action: Callable[[str], None]):
        self.on_action = on_action
        self.anim_timer = 0.0

        # Fonts
        self.font_title = pygame.font.SysFont("Impact", 78)
        self.font_tagline = pygame.font.SysFont("Verdana", 20, bold=True)
        self.font_button = pygame.font.SysFont("Verdana", 17, bold=True)
        self.font_footer = pygame.font.SysFont("Verdana", 13)

        # Buttons configuration
        btn_w, btn_h = 320, 50
        start_y = 250
        gap = 62
        cx = WINDOW_WIDTH // 2 - btn_w // 2

        self.buttons = [
            UIButton(pygame.Rect(cx, start_y + 0 * gap, btn_w, btn_h), "1. START RACE", self.font_button, lambda: self.on_action("START_RACE"), primary=True),
            UIButton(pygame.Rect(cx, start_y + 1 * gap, btn_w, btn_h), "2. CAMERA TEST", self.font_button, lambda: self.on_action("CAMERA_TEST")),
            UIButton(pygame.Rect(cx, start_y + 2 * gap, btn_w, btn_h), "3. GESTURE CALIBRATION", self.font_button, lambda: self.on_action("CALIBRATION")),
            UIButton(pygame.Rect(cx, start_y + 3 * gap, btn_w, btn_h), "4. HOW TO PLAY", self.font_button, lambda: self.on_action("HOW_TO_PLAY")),
            UIButton(pygame.Rect(cx, start_y + 4 * gap, btn_w, btn_h), "5. SETTINGS", self.font_button, lambda: self.on_action("SETTINGS")),
            UIButton(pygame.Rect(cx, start_y + 5 * gap, btn_w, btn_h), "6. EXIT GAME", self.font_button, lambda: self.on_action("EXIT")),
        ]

    def handle_event(self, event: pygame.event.Event):
        """Process input events."""
        for btn in self.buttons:
            if btn.handle_event(event):
                break

    def update(self, dt: float):
        """Update animation and button hover effects."""
        self.anim_timer += dt
        mouse_pos = pygame.mouse.get_pos()
        for btn in self.buttons:
            btn.update(dt, mouse_pos)

    def draw(self, surface: pygame.Surface, is_camera_connected: bool):
        """Draw main menu interface."""
        # 1. Animated Cyber Horizon and Grid
        self._render_cyber_grid(surface)

        # 2. Glowing Title and Tagline
        title_y = 75
        # Soft glowing title shadow
        pulse = 0.5 + 0.5 * math.sin(self.anim_timer * 3.0)
        glow_color = (int(0 + 40 * pulse), int(220 + 35 * pulse), 255)

        title_surf = render_text_with_shadow(self.font_title, GAME_TITLE, glow_color, (0, 0, 0), (4, 4))
        surface.blit(title_surf, (WINDOW_WIDTH // 2 - title_surf.get_width() // 2, title_y))

        tag_surf = self.font_tagline.render(TAGLINE, True, COLOR_TEXT_WHITE)
        surface.blit(tag_surf, (WINDOW_WIDTH // 2 - tag_surf.get_width() // 2, title_y + 92))

        # 3. Expo Badge
        expo_text = self.font_footer.render("COLLEGE TECH EXPO EDITION  |  PYTHON + MEDIAPIPE + OPENCV", True, COLOR_NEON_GREEN)
        surface.blit(expo_text, (WINDOW_WIDTH // 2 - expo_text.get_width() // 2, title_y + 125))

        # 4. Camera Status Indicator (Top Right)
        status_x = WINDOW_WIDTH - 240
        status_rect = pygame.Rect(status_x, 20, 220, 32)
        draw_glow_rect(surface, status_rect, (18, 22, 34), (45, 55, 80), radius=6, glow_spread=1)
        dot_c = COLOR_NEON_GREEN if is_camera_connected else COLOR_NEON_AMBER
        pygame.draw.circle(surface, dot_c, (status_x + 16, 36), 6)
        status_msg = "WEBCAM ONLINE" if is_camera_connected else "KEYBOARD FALLBACK"
        msg_surf = self.font_footer.render(status_msg, True, COLOR_TEXT_WHITE)
        surface.blit(msg_surf, (status_x + 28, 28))

        # 5. Buttons
        for btn in self.buttons:
            btn.draw(surface)

        # 6. Footer Controls Hint
        hint = self.font_footer.render("Use mouse to select  |  Press 1-6 keys for fast select  |  ESC to go back", True, COLOR_TEXT_MUTED)
        surface.blit(hint, (WINDOW_WIDTH // 2 - hint.get_width() // 2, WINDOW_HEIGHT - 32))

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
