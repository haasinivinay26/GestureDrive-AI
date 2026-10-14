"""
Utility and helper functions for GestureDrive AI.
Provides math utilities, color blending, drawing primitives, and surface manipulation.
"""

import math
import pygame


def clamp(val: float, min_v: float, max_v: float) -> float:
    """Clamp a value between min_v and max_v."""
    return max(min_v, min(max_v, val))


def lerp(a: float, b: float, t: float) -> float:
    """Linear interpolation between a and b by factor t."""
    return a + (b - a) * t


def map_range(val: float, in_min: float, in_max: float, out_min: float, out_max: float) -> float:
    """Map val from input range to output range, clamped."""
    if in_max == in_min:
        return out_min
    norm = clamp((val - in_min) / (in_max - in_min), 0.0, 1.0)
    return out_min + norm * (out_max - out_min)


def ease_out_quad(t: float) -> float:
    """Easing function for smooth UI animations."""
    return 1 - (1 - t) * (1 - t)


def draw_rounded_rect(surface: pygame.Surface, rect: pygame.Rect, color, radius: int = 8, border_color=None, border_width: int = 1):
    """Draw a rounded rectangle with optional border."""
    pygame.draw.rect(surface, color, rect, border_radius=radius)
    if border_color and border_width > 0:
        pygame.draw.rect(surface, border_color, rect, width=border_width, border_radius=radius)


def draw_glow_rect(surface: pygame.Surface, rect: pygame.Rect, color, glow_color, radius: int = 8, glow_spread: int = 4):
    """Draw a rectangle with a soft neon glow around its border."""
    # Outer glow layer
    glow_rect = rect.inflate(glow_spread * 2, glow_spread * 2)
    glow_surf = pygame.Surface((glow_rect.width, glow_rect.height), pygame.SRCALPHA)
    glow_rgba = (*glow_color[:3], 60)
    pygame.draw.rect(glow_surf, glow_rgba, glow_surf.get_rect(), border_radius=radius + glow_spread)
    surface.blit(glow_surf, glow_rect.topleft)
    # Inner solid rect
    pygame.draw.rect(surface, color, rect, border_radius=radius)
    pygame.draw.rect(surface, glow_color, rect, width=2, border_radius=radius)


def render_text_with_shadow(font: pygame.font.Font, text: str, color, shadow_color=(0, 0, 0), offset=(2, 2)) -> pygame.Surface:
    """Render text with a drop shadow."""
    text_surf = font.render(text, True, color)
    shadow_surf = font.render(text, True, shadow_color)
    w = text_surf.get_width() + abs(offset[0])
    h = text_surf.get_height() + abs(offset[1])
    combined = pygame.Surface((w, h), pygame.SRCALPHA)
    combined.blit(shadow_surf, (max(0, offset[0]), max(0, offset[1])))
    combined.blit(text_surf, (max(0, -offset[0]), max(0, -offset[1])))
    return combined
