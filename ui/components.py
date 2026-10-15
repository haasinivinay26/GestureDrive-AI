"""
Reusable UI Components for GestureDrive AI.
Provides animated buttons, toggle switches, and horizontal sliders.
"""

import pygame
from typing import Callable, Optional, Tuple
from config import (
    COLOR_PANEL_BG, COLOR_PANEL_BORDER,
    COLOR_NEON_CYAN, COLOR_NEON_GREEN, COLOR_TEXT_WHITE, COLOR_TEXT_MUTED
)
from utils.helpers import draw_rounded_rect, draw_glow_rect, clamp
from utils.audio import AUDIO


class UIButton:
    """Interactive button with hover animation, neon glow, shortcut pill, and click audio."""

    def __init__(
        self,
        rect: pygame.Rect,
        text: str,
        font: pygame.font.Font,
        on_click: Optional[Callable] = None,
        primary: bool = False,
        accent_color=COLOR_NEON_CYAN,
        shortcut: Optional[str] = None
    ):
        self.rect = rect
        self.text = text
        self.font = font
        self.on_click = on_click
        self.primary = primary
        self.accent_color = accent_color
        self.shortcut = shortcut
        self.is_hovered = False
        self.hover_progress = 0.0
        self.pulse_timer = 0.0
        self.font_badge = pygame.font.SysFont("Verdana", 11, bold=True)

    def update(self, dt: float, mouse_pos: Tuple[int, int]):
        """Update hover transition state and breathing pulse."""
        self.is_hovered = self.rect.collidepoint(mouse_pos)
        target = 1.0 if self.is_hovered else 0.0
        self.hover_progress += (target - self.hover_progress) * dt * 14.0
        self.pulse_timer += dt * 3.0

    def handle_event(self, event: pygame.event.Event) -> bool:
        """Process mouse clicks."""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.is_hovered:
                AUDIO.play("click", volume=0.8)
                if self.on_click:
                    self.on_click()
                return True
        return False

    def draw(self, surface: pygame.Surface):
        """Render button with modern glass styling and neon hover glow."""
        # Visual expansion on hover
        h_ratio = clamp(self.hover_progress, 0.0, 1.0)

        if self.is_hovered:
            border_c = self.accent_color
            bg_c = (int(22 + 15 * h_ratio), int(28 + 20 * h_ratio), int(46 + 30 * h_ratio))
            glow_spread = int(2 + 3 * h_ratio)
            draw_glow_rect(surface, self.rect, bg_c, border_c, radius=8, glow_spread=glow_spread)
        elif self.primary:
            # Subtle breathing glow for primary CTA
            import math
            pulse = 0.5 + 0.5 * math.sin(self.pulse_timer)
            glow_c = (
                int(self.accent_color[0] * (0.7 + 0.3 * pulse)),
                int(self.accent_color[1] * (0.7 + 0.3 * pulse)),
                int(self.accent_color[2] * (0.7 + 0.3 * pulse))
            )
            bg_c = (24, 30, 48)
            draw_glow_rect(surface, self.rect, bg_c, glow_c, radius=8, glow_spread=2)
        else:
            bg_c = (18, 22, 34)
            draw_rounded_rect(surface, self.rect, bg_c, radius=8, border_color=COLOR_PANEL_BORDER, border_width=1)

        # Label text
        txt_color = self.accent_color if self.is_hovered else (COLOR_TEXT_WHITE if not self.primary else COLOR_TEXT_WHITE)
        surf = self.font.render(self.text, True, txt_color)
        surface.blit(surf, (self.rect.centerx - surf.get_width() // 2, self.rect.centery - surf.get_height() // 2))

        # Optional Shortcut Badge in top right corner
        if self.shortcut:
            badge_surf = self.font_badge.render(self.shortcut, True, self.accent_color if self.is_hovered else COLOR_TEXT_MUTED)
            badge_w = badge_surf.get_width() + 10
            badge_h = 16
            badge_rect = pygame.Rect(self.rect.right - badge_w - 6, self.rect.top + 5, badge_w, badge_h)
            draw_rounded_rect(surface, badge_rect, (28, 34, 52), radius=4, border_color=self.accent_color if self.is_hovered else (45, 55, 80), border_width=1)
            surface.blit(badge_surf, (badge_rect.centerx - badge_surf.get_width() // 2, badge_rect.centery - badge_surf.get_height() // 2))



class UISlider:
    """Horizontal slider with continuous value adjustment."""

    def __init__(self, rect: pygame.Rect, min_val: float, max_val: float, current_val: float, label: str, font: pygame.font.Font, on_change=None):
        self.rect = rect
        self.min_val = min_val
        self.max_val = max_val
        self.value = current_val
        self.label = label
        self.font = font
        self.on_change = on_change
        self.is_dragging = False

    def handle_event(self, event: pygame.event.Event) -> bool:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.is_dragging = True
                self._update_val_from_mouse(event.pos[0])
                return True
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.is_dragging = False
        elif event.type == pygame.MOUSEMOTION and self.is_dragging:
            self._update_val_from_mouse(event.pos[0])
            return True
        return False

    def _update_val_from_mouse(self, mouse_x: int):
        norm = clamp((mouse_x - self.rect.left) / max(1, self.rect.width), 0.0, 1.0)
        self.value = self.min_val + norm * (self.max_val - self.min_val)
        if self.on_change:
            self.on_change(self.value)

    def draw(self, surface: pygame.Surface):
        # Draw label and value
        lbl_surf = self.font.render(f"{self.label}: {self.value:.2f}", True, COLOR_TEXT_WHITE)
        surface.blit(lbl_surf, (self.rect.left, self.rect.top - 24))

        # Slider background track
        draw_rounded_rect(surface, self.rect, (25, 30, 44), radius=4, border_color=COLOR_PANEL_BORDER, border_width=1)

        # Active filled track
        norm = clamp((self.value - self.min_val) / max(0.001, self.max_val - self.min_val), 0.0, 1.0)
        fill_w = int(self.rect.width * norm)
        if fill_w > 0:
            fill_rect = pygame.Rect(self.rect.left, self.rect.top, fill_w, self.rect.height)
            draw_rounded_rect(surface, fill_rect, COLOR_NEON_CYAN, radius=4)

        # Handle Knob
        knob_x = self.rect.left + fill_w
        pygame.draw.circle(surface, (255, 255, 255), (knob_x, self.rect.centery), 9)
        pygame.draw.circle(surface, COLOR_NEON_CYAN, (knob_x, self.rect.centery), 6)


class UIToggle:
    """Binary ON/OFF toggle switch."""

    def __init__(self, rect: pygame.Rect, state: bool, label: str, font: pygame.font.Font, on_toggle=None):
        self.rect = rect
        self.state = state
        self.label = label
        self.font = font
        self.on_toggle = on_toggle

    def handle_event(self, event: pygame.event.Event) -> bool:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.state = not self.state
                AUDIO.play("click", volume=0.8)
                if self.on_toggle:
                    self.on_toggle(self.state)
                return True
        return False

    def draw(self, surface: pygame.Surface):
        # Label
        lbl_surf = self.font.render(self.label, True, COLOR_TEXT_WHITE)
        surface.blit(lbl_surf, (self.rect.left, self.rect.centery - lbl_surf.get_height() // 2))

        # Switch pill on the right
        switch_w, switch_h = 56, 28
        switch_rect = pygame.Rect(self.rect.right - switch_w, self.rect.centery - switch_h // 2, switch_w, switch_h)

        bg_color = COLOR_NEON_GREEN if self.state else (40, 45, 60)
        draw_rounded_rect(surface, switch_rect, bg_color, radius=14)

        # Moving thumb circle
        thumb_x = switch_rect.right - 14 if self.state else switch_rect.left + 14
        pygame.draw.circle(surface, (255, 255, 255), (thumb_x, switch_rect.centery), 10)
