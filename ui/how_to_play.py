"""
How to Play & College Expo Presentation Screen for GestureDrive AI.
Features interactive visual gesture cards and academic technology architecture explanations.
"""

import pygame
from typing import Callable

from config import (
    WINDOW_WIDTH, WINDOW_HEIGHT,
    COLOR_NEON_CYAN, COLOR_NEON_GREEN, COLOR_NEON_RED, COLOR_NEON_AMBER,
    COLOR_PANEL_BG, COLOR_PANEL_BORDER, COLOR_TEXT_WHITE, COLOR_TEXT_MUTED
)
from ui.components import UIButton
from utils.helpers import draw_rounded_rect, draw_glow_rect, render_text_with_shadow


class HowToPlayScreen:
    """Displays visitor instructions and technology exposition diagrams."""

    def __init__(self, on_back: Callable[[], None], on_test_cam: Callable[[], None]):
        self.on_back = on_back
        self.on_test_cam = on_test_cam
        self.active_tab = 0  # 0: How to Play, 1: Technology Architecture

        # Fonts
        self.font_title = pygame.font.SysFont("Impact", 42)
        self.font_tab = pygame.font.SysFont("Verdana", 16, bold=True)
        self.font_card_title = pygame.font.SysFont("Verdana", 17, bold=True)
        self.font_body = pygame.font.SysFont("Verdana", 13)
        self.font_hint = pygame.font.SysFont("Verdana", 12)

        # Tab Buttons
        self.btn_tab_play = UIButton(pygame.Rect(40, 90, 240, 40), "1. HOW TO PLAY", self.font_tab, lambda: self._set_tab(0), primary=True)
        self.btn_tab_tech = UIButton(pygame.Rect(300, 90, 280, 40), "2. TECH EXPO ARCHITECTURE", self.font_tab, lambda: self._set_tab(1))

        # Action Buttons
        self.btn_back = UIButton(pygame.Rect(40, WINDOW_HEIGHT - 65, 160, 45), "BACK TO MENU", self.font_tab, self.on_back)
        self.btn_cam = UIButton(pygame.Rect(WINDOW_WIDTH - 240, WINDOW_HEIGHT - 65, 200, 45), "TEST CAMERA NOW", self.font_tab, self.on_test_cam, primary=True)

    def _set_tab(self, idx: int):
        self.active_tab = idx
        self.btn_tab_play.primary = (idx == 0)
        self.btn_tab_tech.primary = (idx == 1)

    def handle_event(self, event: pygame.event.Event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.on_back()
            return
        self.btn_tab_play.handle_event(event)
        self.btn_tab_tech.handle_event(event)
        self.btn_back.handle_event(event)
        self.btn_cam.handle_event(event)

    def update(self, dt: float):
        mouse_pos = pygame.mouse.get_pos()
        self.btn_tab_play.update(dt, mouse_pos)
        self.btn_tab_tech.update(dt, mouse_pos)
        self.btn_back.update(dt, mouse_pos)
        self.btn_cam.update(dt, mouse_pos)

    def draw(self, surface: pygame.Surface):
        surface.fill((14, 16, 24))

        # Title
        title_surf = render_text_with_shadow(self.font_title, "HOW TO PLAY & EXPO GUIDE", COLOR_NEON_CYAN, (0, 0, 0), (2, 2))
        surface.blit(title_surf, (40, 25))

        # Tabs
        self.btn_tab_play.draw(surface)
        self.btn_tab_tech.draw(surface)

        if self.active_tab == 0:
            self._render_how_to_play(surface)
        else:
            self._render_tech_architecture(surface)

        # Bottom Buttons
        self.btn_back.draw(surface)
        self.btn_cam.draw(surface)

    def _render_how_to_play(self, surface: pygame.Surface):
        """Render 3 distinct gesture instruction cards."""
        card_w = 370
        card_h = 430
        card_y = 150
        gap = 25
        start_x = 40

        cards = [
            {
                "title": "STEERING WHEEL",
                "badge": "BOTH HANDS",
                "color": COLOR_NEON_CYAN,
                "lines": [
                    "Hold both hands up in front of the camera",
                    "like gripping an imaginary steering wheel.",
                    "",
                    "- Rotate hands LEFT (left down, right up)",
                    "  to steer the car left.",
                    "- Rotate hands RIGHT (right down, left up)",
                    "  to steer the car right.",
                    "- Returning hands level centers steering.",
                    "",
                    "Single-hand assist is also supported!"
                ]
            },
            {
                "title": "ACCELERATOR",
                "badge": "THUMBS-UP",
                "color": COLOR_NEON_GREEN,
                "lines": [
                    "Give a deliberate THUMBS-UP with",
                    "either hand to accelerate.",
                    "",
                    "- Keep your other 4 fingers curled into a fist.",
                    "- Hold thumbs-up to smoothly gain speed.",
                    "- Release the gesture to coast naturally.",
                    "",
                    "High speeds unlock 2.5x score multipliers!"
                ]
            },
            {
                "title": "BRAKE COMMAND",
                "badge": "OPEN PALM",
                "color": COLOR_NEON_RED,
                "lines": [
                    "Show an OPEN PALM with all 5 fingers",
                    "spread outward towards the camera.",
                    "",
                    "- Rapidly decelerates vehicle speed.",
                    "- Holding open-palm keeps brakes locked.",
                    "- Brakes override acceleration unconditionally!",
                    "",
                    "Essential for dodging sudden hazards."
                ]
            }
        ]

        for i, card in enumerate(cards):
            cx = start_x + i * (card_w + gap)
            rect = pygame.Rect(cx, card_y, card_w, card_h)
            draw_glow_rect(surface, rect, (20, 24, 36), card["color"], radius=10, glow_spread=2)

            # Card Header
            t_surf = self.font_card_title.render(card["title"], True, card["color"])
            surface.blit(t_surf, (cx + 20, card_y + 20))

            badge_rect = pygame.Rect(cx + card_w - 130, card_y + 18, 110, 24)
            draw_rounded_rect(surface, badge_rect, (30, 36, 52), radius=4, border_color=card["color"], border_width=1)
            b_surf = self.font_hint.render(card["badge"], True, card["color"])
            surface.blit(b_surf, (badge_rect.centerx - b_surf.get_width() // 2, badge_rect.centery - b_surf.get_height() // 2))

            # Body Lines
            line_y = card_y + 70
            for line in card["lines"]:
                l_surf = self.font_body.render(line, True, COLOR_TEXT_WHITE if line.startswith("-") else COLOR_TEXT_MUTED)
                surface.blit(l_surf, (cx + 20, line_y))
                line_y += 24

    def _render_tech_architecture(self, surface: pygame.Surface):
        """Render Academic Technology Architecture Breakdown."""
        card_w = 570
        card_h = 200
        start_x = 40
        card_y = 150
        gap_y = 25
        gap_x = 25

        modules = [
            (start_x, card_y, "1. COMPUTER VISION PIPELINE", COLOR_NEON_CYAN, [
                "Powered by OpenCV (cv2) on a dedicated asynchronous thread.",
                "Captures 30 FPS video frames, normalizes aspect ratios,",
                "and mirrors camera input for natural driving orientation."
            ]),
            (start_x + card_w + gap_x, card_y, "2. 3D HAND LANDMARK DETECTION", COLOR_NEON_GREEN, [
                "Powered by Google MediaPipe Hands framework.",
                "Extracts 21 3D coordinates (x, y, z) per hand in real-time.",
                "Renders cyber-neon skeletal overlay on live PIP feed."
            ]),
            (start_x, card_y + card_h + gap_y, "3. GESTURE RECOGNITION ENGINE", COLOR_NEON_AMBER, [
                "Trigonometric steering angle calculation via atan2(dy, dx).",
                "Knuckle joint curl heuristics for thumbs-up and open-palm.",
                "Debounce hysteresis buffer & strict brake-over-throttle priority."
            ]),
            (start_x + card_w + gap_x, card_y + card_h + gap_y, "4. PSEUDO-3D RACING SIMULATION", COLOR_NEON_PURPLE if 'COLOR_NEON_PURPLE' in globals() else COLOR_NEON_CYAN, [
                "Built natively with Pygame and NumPy.",
                "Classic OutRun scanline road projection with curves and hills.",
                "Procedural 44.1kHz audio synthesis for engine revving and tire screech."
            ]),
        ]

        for x, y, title, color, lines in modules:
            rect = pygame.Rect(x, y, card_w, card_h)
            draw_glow_rect(surface, rect, (20, 24, 36), color, radius=8, glow_spread=2)

            t_surf = self.font_card_title.render(title, True, color)
            surface.blit(t_surf, (x + 20, y + 18))

            ly = y + 55
            for l in lines:
                ls = self.font_body.render(l, True, COLOR_TEXT_WHITE)
                surface.blit(ls, (x + 20, ly))
                ly += 26
