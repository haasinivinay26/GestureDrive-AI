"""
How to Play & College Expo Presentation Screen for GestureDrive AI.
Features interactive visual cards for all 6 supported driving gestures:
- Steering Left, Steering Right, Straight/Neutral Hold
- Accelerate (Thumbs-up)
- Brake (Open palm)
- Starting Gesture (Victory sign ✌️ / Wheel ready)
Includes camera distance/lighting setup guide and academic architecture overview.
"""

import pygame
from typing import Callable

from config import (
    WINDOW_WIDTH, WINDOW_HEIGHT,
    COLOR_NEON_CYAN, COLOR_NEON_GREEN, COLOR_NEON_RED, COLOR_NEON_AMBER,
    COLOR_PANEL_BG, COLOR_PANEL_BORDER, COLOR_TEXT_WHITE, COLOR_TEXT_MUTED
)
from ui.components import UIButton
from utils.helpers import draw_rounded_rect, draw_glow_rect, draw_glass_rect, render_text_with_shadow


class HowToPlayScreen:
    """Displays visitor instructions and technology exposition diagrams."""

    def __init__(self, on_back: Callable[[], None], on_test_cam: Callable[[], None]):
        self.on_back = on_back
        self.on_test_cam = on_test_cam
        self.active_tab = 0  # 0: Gesture Controls, 1: Camera Setup & Tech Architecture

        # Fonts
        self.font_title = pygame.font.SysFont("Impact", 44)
        self.font_tab = pygame.font.SysFont("Verdana", 15, bold=True)
        self.font_card_title = pygame.font.SysFont("Verdana", 14, bold=True)
        self.font_body = pygame.font.SysFont("Verdana", 12)
        self.font_badge = pygame.font.SysFont("Verdana", 10, bold=True)
        self.font_tips = pygame.font.SysFont("Verdana", 12)

        # Tab Buttons
        self.btn_tab_play = UIButton(pygame.Rect(60, 85, 230, 38), "1. GESTURE CONTROLS", self.font_tab, lambda: self._set_tab(0), primary=True)
        self.btn_tab_tech = UIButton(pygame.Rect(305, 85, 270, 38), "2. CAMERA SETUP & TECH", self.font_tab, lambda: self._set_tab(1))

        # Action Buttons
        self.btn_back = UIButton(pygame.Rect(60, WINDOW_HEIGHT - 60, 160, 42), "BACK TO MENU", self.font_tab, self.on_back, shortcut="[ESC]")
        self.btn_cam = UIButton(pygame.Rect(WINDOW_WIDTH - 250, WINDOW_HEIGHT - 60, 190, 42), "TEST CAMERA NOW", self.font_tab, self.on_test_cam, primary=True)

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
        surface.fill((8, 10, 16))

        # Title
        title_surf = render_text_with_shadow(self.font_title, "HOW TO PLAY — GESTURE CONTROLS", COLOR_NEON_CYAN, (0, 0, 0), (2, 2))
        surface.blit(title_surf, (60, 22))

        # Tabs
        self.btn_tab_play.draw(surface)
        self.btn_tab_tech.draw(surface)

        if self.active_tab == 0:
            self._render_gesture_cards(surface)
        else:
            self._render_camera_and_architecture(surface)

        # Bottom Buttons
        self.btn_back.draw(surface)
        self.btn_cam.draw(surface)

    def _render_gesture_cards(self, surface: pygame.Surface):
        """Render 6 detailed gesture cards (2 rows of 3)."""
        card_w = 365
        card_h = 205
        gap_x = 24
        gap_y = 16
        start_x = 60
        start_y = 135

        cards = [
            {
                "title": "STEERING LEFT",
                "badge": "TILT WHEEL",
                "color": COLOR_NEON_CYAN,
                "icon": "◄",
                "lines": [
                    "Hold both hands up in front of the camera.",
                    "Rotate hands counter-clockwise:",
                    "• Left hand DOWN, Right hand UP",
                    "The car smoothly steers left across lanes.",
                    "Single-hand assist is also supported."
                ]
            },
            {
                "title": "STRAIGHT / NEUTRAL",
                "badge": "LEVEL HANDS",
                "color": (120, 180, 255),
                "icon": "▲",
                "lines": [
                    "Hold both hands level at equal heights.",
                    "Within the calibrated neutral deadzone,",
                    "the car drives dead straight without drift.",
                    "Even on sharp curves, zero lateral drag",
                    "keeps you locked in your current lane."
                ]
            },
            {
                "title": "STEERING RIGHT",
                "badge": "TILT WHEEL",
                "color": COLOR_NEON_CYAN,
                "icon": "►",
                "lines": [
                    "Hold both hands up in front of the camera.",
                    "Rotate hands clockwise:",
                    "• Right hand DOWN, Left hand UP",
                    "The car smoothly steers right across lanes.",
                    "Angle determines turning sharpness."
                ]
            },
            {
                "title": "ACCELERATION",
                "badge": "THUMBS-UP",
                "color": COLOR_NEON_GREEN,
                "icon": "👍",
                "lines": [
                    "Extend thumb UPWARD with other 4 fingers",
                    "curled into a fist. Works on either hand.",
                    "• Smoothly gains speed up to 220 KM/H",
                    "• High speeds unlock 2.5x score multiplier",
                    "Release gesture to coast naturally."
                ]
            },
            {
                "title": "BRAKING & STOP",
                "badge": "OPEN PALM",
                "color": COLOR_NEON_RED,
                "icon": "✋",
                "lines": [
                    "Show an OPEN PALM with all 5 fingers",
                    "spread outward facing the camera.",
                    "• Rapid deceleration down to full stop",
                    "• Strictly overrides acceleration priority",
                    "Critical for avoiding sudden traffic hazards."
                ]
            },
            {
                "title": "START RACE",
                "badge": "PEACE / 2 HANDS",
                "color": COLOR_NEON_AMBER,
                "icon": "✌️",
                "lines": [
                    "Show ✌️ Victory/Peace sign or grip wheel",
                    "with both hands on the main menu.",
                    "• Hold steady for 1 second",
                    "• On-screen progress meter confirms start",
                    "Prevents accidental starts."
                ]
            },
        ]

        for i, card in enumerate(cards):
            col = i % 3
            row = i // 3
            cx = start_x + col * (card_w + gap_x)
            cy = start_y + row * (card_h + gap_y)

            rect = pygame.Rect(cx, cy, card_w, card_h)
            draw_glass_rect(surface, rect, bg_rgba=(16, 20, 32, 220), border_color=(35, 48, 70), radius=10)

            # Left accent highlight
            accent_rect = pygame.Rect(cx + 4, cy + 8, 3, card_h - 16)
            draw_rounded_rect(surface, accent_rect, card["color"], radius=2)

            # Header & Badge
            t_surf = self.font_card_title.render(f"{card['icon']}  {card['title']}", True, card["color"])
            surface.blit(t_surf, (cx + 16, cy + 14))

            badge_surf = self.font_badge.render(card["badge"], True, card["color"])
            bw = badge_surf.get_width() + 12
            badge_rect = pygame.Rect(cx + card_w - bw - 14, cy + 12, bw, 20)
            draw_rounded_rect(surface, badge_rect, (24, 30, 48), radius=4, border_color=card["color"], border_width=1)
            surface.blit(badge_surf, (badge_rect.centerx - badge_surf.get_width() // 2, badge_rect.centery - badge_surf.get_height() // 2))

            # Body lines
            line_y = cy + 46
            for line in card["lines"]:
                is_bullet = line.startswith("•")
                color = COLOR_TEXT_WHITE if is_bullet else COLOR_TEXT_MUTED
                l_surf = self.font_body.render(line, True, color)
                surface.blit(l_surf, (cx + 16, line_y))
                line_y += 24

    def _render_camera_and_architecture(self, surface: pygame.Surface):
        """Render Camera Placement Setup Tips and Academic Technology Architecture."""
        start_x = 60
        start_y = 135

        # 1. Camera Setup Guide Card (Left side)
        guide_w = 480
        guide_h = 425
        guide_rect = pygame.Rect(start_x, start_y, guide_w, guide_h)
        draw_glass_rect(surface, guide_rect, bg_rgba=(16, 20, 32, 220), border_color=COLOR_NEON_CYAN, radius=10)

        t_cam = self.font_card_title.render("OPTIMAL CAMERA & HARDWARE SETUP", True, COLOR_NEON_CYAN)
        surface.blit(t_cam, (start_x + 20, start_y + 18))

        tips = [
            ("CAMERA DISTANCE", "Sit 1.5 to 3.0 feet (45-90 cm) directly in front of the webcam."),
            ("LIGHTING CONDITIONS", "Ensure face and hands are clearly lit from the front. Avoid harsh backlights or bright windows behind you."),
            ("HAND POSITIONING", "Keep hands within the upper center of the camera frame for fastest landmark recognition."),
            ("STEERING CALIBRATION", "Use 'Calibrate Center' on the main menu to zero out your natural resting hand angle."),
            ("KEYBOARD FALLBACK", "Arrow keys (←, →, ↑, ↓) and WASD are always ready if camera access is interrupted."),
            ("WEBCAM DIAGNOSTICS", "Click 'TEST CAMERA NOW' to view the live skeleton overlay and check your FPS."),
        ]

        ty = start_y + 55
        for heading, body in tips:
            h_s = self.font_badge.render(f"• {heading}", True, COLOR_NEON_GREEN)
            surface.blit(h_s, (start_x + 20, ty))
            b_s = self.font_body.render(body, True, COLOR_TEXT_MUTED)
            surface.blit(b_s, (start_x + 20, ty + 18))
            ty += 56

        # 2. Technology Architecture Cards (Right side)
        arch_x = start_x + guide_w + 25
        arch_w = WINDOW_WIDTH - arch_x - 60

        modules = [
            ("1. COMPUTER VISION PIPELINE", COLOR_NEON_CYAN, "Powered by OpenCV (cv2) on a dedicated background thread running at 30 FPS. Captures, normalizes aspect ratios, and mirrors video for natural steering."),
            ("2. 3D HAND LANDMARK TRACKING", COLOR_NEON_GREEN, "Powered by Google MediaPipe. Extracts 21 3D coordinates (x, y, z) per hand in real-time and renders cyber-neon skeletal overlays on the live HUD preview."),
            ("3. GESTURE RECOGNITION ENGINE", COLOR_NEON_AMBER, "Uses trigonometric steering angle math atan2(dy, dx), knuckle curl heuristics for thumbs-up and open palm, debouncing buffers, and strict brake-over-accel priority."),
            ("4. PSEUDO-3D RACING SIMULATION", (180, 80, 255), "Built natively with Pygame and NumPy. Features OutRun scanline road projection, rolling hills, responsive physics, procedural audio, and AI opponent traffic."),
        ]

        my = start_y
        for title, color, desc in modules:
            m_rect = pygame.Rect(arch_x, my, arch_w, 95)
            draw_glass_rect(surface, m_rect, bg_rgba=(16, 20, 32, 220), border_color=(35, 48, 70), radius=8)

            m_title = self.font_card_title.render(title, True, color)
            surface.blit(m_title, (arch_x + 18, my + 12))

            # Multi-line word wrap or clean split
            words = desc.split()
            lines = []
            curr = ""
            for w in words:
                if len(curr + " " + w) > 75:
                    lines.append(curr)
                    curr = w
                else:
                    curr = curr + " " + w if curr else w
            if curr:
                lines.append(curr)

            ly = my + 38
            for l in lines:
                l_s = self.font_body.render(l, True, COLOR_TEXT_MUTED)
                surface.blit(l_s, (arch_x + 18, ly))
                ly += 20

            my += 110
