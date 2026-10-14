"""
In-Game Dashboard and Real-Time HUD Overlay for GestureDrive AI.
Renders speedometer, gear, distance, score, high score, health/lives,
steering wheel angle dial, gesture indicator badges, live webcam PIP, and pause overlay.
"""

import math
import pygame
from typing import Optional

from config import (
    WINDOW_WIDTH, WINDOW_HEIGHT, SETTINGS,
    COLOR_PANEL_BG, COLOR_PANEL_BORDER,
    COLOR_NEON_CYAN, COLOR_NEON_GREEN, COLOR_NEON_RED, COLOR_NEON_AMBER,
    COLOR_TEXT_WHITE, COLOR_TEXT_MUTED,
    CAMERA_PIP_WIDTH, CAMERA_PIP_HEIGHT
)
from camera.gesture_recognizer import GestureState
from utils.helpers import draw_rounded_rect, draw_glow_rect, render_text_with_shadow, clamp


class Dashboard:
    """Manages HUD rendering, gauges, live camera preview, and telemetry displays."""

    def __init__(self):
        # Fonts
        self.font_speed = pygame.font.SysFont("Impact", 44)
        self.font_unit = pygame.font.SysFont("Verdana", 14, bold=True)
        self.font_label = pygame.font.SysFont("Verdana", 12, bold=True)
        self.font_value = pygame.font.SysFont("Verdana", 18, bold=True)
        self.font_gesture = pygame.font.SysFont("Verdana", 15, bold=True)
        self.font_pause_title = pygame.font.SysFont("Impact", 64)
        self.font_pause_body = pygame.font.SysFont("Verdana", 20)

    def draw(
        self,
        surface: pygame.Surface,
        speed_kmh: float,
        score: int,
        high_score: int,
        distance_str: str,
        race_time_str: str,
        multiplier: float,
        lives: int,
        gesture_state: GestureState,
        camera_surface: Optional[pygame.Surface],
        is_camera_connected: bool,
        is_paused: bool
    ):
        """Render complete in-game dashboard."""

        # 1. Top-Left Speedometer & Telemetry Cluster
        self._render_speed_cluster(surface, speed_kmh, score, high_score)

        # 2. Top-Center Steering Wheel Dial and Gesture Badges
        self._render_steering_and_gestures(surface, gesture_state)

        # 3. Top-Right Live Camera PIP with Hand Landmark Skeleton
        if SETTINGS.camera_preview_enabled:
            self._render_camera_pip(surface, camera_surface, is_camera_connected, race_time_str)

        # 4. Bottom-Left Distance and Multiplier Banner
        self._render_bottom_banner(surface, distance_str, multiplier, lives)

        # 5. Pause Modal Overlay if paused
        if is_paused:
            self._render_pause_overlay(surface)

    def _render_speed_cluster(self, surface: pygame.Surface, speed_kmh: float, score: int, high_score: int):
        """Draw speedometer dial, digital readout, current gear, and score."""
        panel_w, panel_h = 290, 115
        panel_rect = pygame.Rect(20, 15, panel_w, panel_h)
        draw_glow_rect(surface, panel_rect, (18, 22, 34), COLOR_PANEL_BORDER, radius=10, glow_spread=2)

        # Speedometer Circular Dial
        dial_cx = panel_rect.left + 55
        dial_cy = panel_rect.top + 55
        dial_radius = 42

        # Background track
        pygame.draw.circle(surface, (30, 36, 52), (dial_cx, dial_cy), dial_radius, width=6)

        # Active speed arc (cyan to amber to red)
        speed_ratio = clamp(speed_kmh / 220.0, 0.0, 1.0)
        arc_angle_deg = speed_ratio * 240.0  # 240 degrees sweep
        start_rad = math.radians(150.0)
        end_rad = math.radians(150.0 + arc_angle_deg)

        arc_color = COLOR_NEON_CYAN if speed_ratio < 0.65 else (COLOR_NEON_AMBER if speed_ratio < 0.88 else COLOR_NEON_RED)
        # Approximate arc by drawing segmented lines
        steps = max(2, int(arc_angle_deg / 10.0))
        pts = []
        for i in range(steps + 1):
            ang = start_rad + (end_rad - start_rad) * (i / steps)
            px = dial_cx + math.cos(ang) * (dial_radius - 3)
            py = dial_cy + math.sin(ang) * (dial_radius - 3)
            pts.append((px, py))
        if len(pts) >= 2:
            pygame.draw.lines(surface, arc_color, False, pts, width=6)

        # Digital Speed Number
        spd_text = self.font_speed.render(f"{int(speed_kmh)}", True, COLOR_TEXT_WHITE)
        surface.blit(spd_text, (dial_cx - spd_text.get_width() // 2, dial_cy - 20))

        kmh_text = self.font_unit.render("KM/H", True, COLOR_NEON_CYAN)
        surface.blit(kmh_text, (dial_cx - kmh_text.get_width() // 2, dial_cy + 16))

        # Right Telemetry: Gear, Score, High Score
        telem_x = panel_rect.left + 120

        # Gear calculation
        if speed_kmh < 5:
            gear_str = "N"
        elif speed_kmh < 45:
            gear_str = "1"
        elif speed_kmh < 85:
            gear_str = "2"
        elif speed_kmh < 130:
            gear_str = "3"
        elif speed_kmh < 175:
            gear_str = "4"
        else:
            gear_str = "5"

        gear_badge = pygame.Rect(telem_x, panel_rect.top + 12, 42, 26)
        draw_rounded_rect(surface, gear_badge, (30, 36, 52), radius=4, border_color=COLOR_NEON_CYAN, border_width=1)
        g_lbl = self.font_label.render("GEAR", True, COLOR_TEXT_MUTED)
        surface.blit(g_lbl, (gear_badge.right + 6, gear_badge.top + 1))
        g_val = self.font_value.render(gear_str, True, COLOR_NEON_CYAN)
        surface.blit(g_val, (gear_badge.centerx - g_val.get_width() // 2, gear_badge.centery - g_val.get_height() // 2))

        # Score
        score_lbl = self.font_label.render("SCORE", True, COLOR_TEXT_MUTED)
        surface.blit(score_lbl, (telem_x, panel_rect.top + 45))
        score_val = self.font_value.render(f"{score:,}", True, COLOR_NEON_GREEN)
        surface.blit(score_val, (telem_x, panel_rect.top + 60))

        # High Score
        hi_lbl = self.font_label.render("RECORD", True, COLOR_TEXT_MUTED)
        surface.blit(hi_lbl, (telem_x + 95, panel_rect.top + 45))
        hi_val = self.font_value.render(f"{high_score:,}", True, COLOR_NEON_AMBER)
        surface.blit(hi_val, (telem_x + 95, panel_rect.top + 60))

    def _render_steering_and_gestures(self, surface: pygame.Surface, state: GestureState):
        """Draw interactive steering wheel icon and gesture indicator pills."""
        center_x = WINDOW_WIDTH // 2
        top_y = 15

        # Gesture Status Banner Panel
        banner_w, banner_h = 440, 50
        banner_rect = pygame.Rect(center_x - banner_w // 2, top_y, banner_w, banner_h)

        if state.is_braking:
            border_c = COLOR_NEON_RED
            glow_c = COLOR_NEON_RED
            txt_c = COLOR_NEON_RED
        elif state.is_accelerating:
            border_c = COLOR_NEON_GREEN
            glow_c = COLOR_NEON_GREEN
            txt_c = COLOR_NEON_GREEN
        elif state.hands_detected >= 2:
            border_c = COLOR_NEON_CYAN
            glow_c = COLOR_NEON_CYAN
            txt_c = COLOR_NEON_CYAN
        else:
            border_c = COLOR_PANEL_BORDER
            glow_c = COLOR_PANEL_BORDER
            txt_c = COLOR_TEXT_MUTED

        draw_glow_rect(surface, banner_rect, (18, 22, 34), border_c, radius=8, glow_spread=2)

        # Active Gesture Icon & Name
        gest_surf = self.font_gesture.render(state.active_gesture, True, txt_c)
        surface.blit(gest_surf, (banner_rect.centerx - gest_surf.get_width() // 2, banner_rect.top + 8))

        # Secondary telemetry line: Steering Direction & Accel status
        sub_info = f"STEER: [{state.steer_direction}] ({state.steer_angle:+.2f})  |  ACCEL: {state.accel_status}"
        sub_surf = self.font_label.render(sub_info, True, COLOR_TEXT_MUTED)
        surface.blit(sub_surf, (banner_rect.centerx - sub_surf.get_width() // 2, banner_rect.top + 28))

        # Steering Wheel Angle Dial
        wheel_dial_w, wheel_dial_h = 280, 36
        wheel_rect = pygame.Rect(center_x - wheel_dial_w // 2, top_y + banner_h + 8, wheel_dial_w, wheel_dial_h)
        draw_rounded_rect(surface, wheel_rect, (18, 22, 34), radius=6, border_color=COLOR_PANEL_BORDER, border_width=1)

        # Center tick
        mid_x = wheel_rect.centerx
        mid_y = wheel_rect.centery
        pygame.draw.line(surface, (100, 110, 130), (mid_x, wheel_rect.top + 4), (mid_x, wheel_rect.bottom - 4), width=1)

        # Steering position indicator dot
        steer_px = int(mid_x + state.steer_angle * (wheel_dial_w * 0.44))
        pygame.draw.circle(surface, border_c, (steer_px, mid_y), 7)
        pygame.draw.circle(surface, (255, 255, 255), (steer_px, mid_y), 9, width=1)

        # Left / Center / Right Labels
        lbl_l = self.font_label.render("LEFT", True, COLOR_TEXT_MUTED)
        lbl_c = self.font_label.render("CENTER", True, COLOR_NEON_CYAN if state.steer_direction == "CENTER" else (70, 80, 100))
        lbl_r = self.font_label.render("RIGHT", True, COLOR_TEXT_MUTED)
        surface.blit(lbl_l, (wheel_rect.left + 8, mid_y - lbl_l.get_height() // 2))
        surface.blit(lbl_c, (wheel_rect.centerx - lbl_c.get_width() // 2, wheel_rect.top - 14))
        surface.blit(lbl_r, (wheel_rect.right - 8 - lbl_r.get_width(), mid_y - lbl_r.get_height() // 2))

    def _render_camera_pip(
        self,
        surface: pygame.Surface,
        camera_surface: Optional[pygame.Surface],
        is_camera_connected: bool,
        race_time_str: str
    ):
        """Draw live webcam PIP with neon frame, camera connection status, and race timer."""
        pip_w, pip_h = CAMERA_PIP_WIDTH, CAMERA_PIP_HEIGHT
        pip_x = WINDOW_WIDTH - pip_w - 20
        pip_y = 15

        container_rect = pygame.Rect(pip_x, pip_y, pip_w, pip_h)

        if camera_surface and is_camera_connected:
            surface.blit(camera_surface, (pip_x, pip_y))
            # Neon border around PIP
            pygame.draw.rect(surface, COLOR_NEON_CYAN, container_rect, width=2, border_radius=6)
        else:
            # Standby / Camera off display
            draw_rounded_rect(surface, container_rect, (22, 26, 38), radius=6, border_color=COLOR_PANEL_BORDER, border_width=1)
            msg1 = self.font_label.render("WEBCAM INACTIVE", True, COLOR_NEON_AMBER)
            msg2 = self.font_label.render("KEYBOARD FALLBACK ON", True, COLOR_TEXT_MUTED)
            surface.blit(msg1, (container_rect.centerx - msg1.get_width() // 2, container_rect.centery - 14))
            surface.blit(msg2, (container_rect.centerx - msg2.get_width() // 2, container_rect.centery + 6))

        # Bottom Bar under PIP: Race Timer and Cam Status
        bar_rect = pygame.Rect(pip_x, pip_y + pip_h + 6, pip_w, 28)
        draw_rounded_rect(surface, bar_rect, (18, 22, 34), radius=4, border_color=COLOR_PANEL_BORDER, border_width=1)

        # Camera connection dot
        dot_color = COLOR_NEON_GREEN if is_camera_connected else COLOR_NEON_AMBER
        pygame.draw.circle(surface, dot_color, (pip_x + 14, bar_rect.centery), 5)
        cam_lbl = self.font_label.render("CAM" if is_camera_connected else "KEY", True, COLOR_TEXT_WHITE)
        surface.blit(cam_lbl, (pip_x + 24, bar_rect.centery - cam_lbl.get_height() // 2))

        # Timer
        time_lbl = self.font_value.render(race_time_str, True, COLOR_NEON_CYAN)
        surface.blit(time_lbl, (bar_rect.right - time_lbl.get_width() - 8, bar_rect.centery - time_lbl.get_height() // 2))

    def _render_bottom_banner(self, surface: pygame.Surface, distance_str: str, multiplier: float, lives: int):
        """Draw distance traveled, combo multiplier badge, and vehicle integrity shields."""
        bar_w, bar_h = 380, 42
        bar_x = 20
        bar_y = WINDOW_HEIGHT - bar_h - 15

        rect = pygame.Rect(bar_x, bar_y, bar_w, bar_h)
        draw_glow_rect(surface, rect, (18, 22, 34), COLOR_PANEL_BORDER, radius=6, glow_spread=2)

        # Distance
        dist_lbl = self.font_label.render("DISTANCE", True, COLOR_TEXT_MUTED)
        surface.blit(dist_lbl, (rect.left + 12, rect.top + 4))
        dist_val = self.font_value.render(distance_str, True, COLOR_TEXT_WHITE)
        surface.blit(dist_val, (rect.left + 12, rect.top + 18))

        # Combo Multiplier
        mult_badge = pygame.Rect(rect.left + 140, rect.top + 8, 70, 26)
        badge_c = COLOR_NEON_AMBER if multiplier > 1.5 else COLOR_NEON_GREEN
        draw_rounded_rect(surface, mult_badge, (30, 36, 52), radius=4, border_color=badge_c, border_width=1)
        m_txt = self.font_label.render(f"{multiplier:.1f}x MULT", True, badge_c)
        surface.blit(m_txt, (mult_badge.centerx - m_txt.get_width() // 2, mult_badge.centery - m_txt.get_height() // 2))

        # Lives / Shields
        shield_x = rect.left + 235
        sh_lbl = self.font_label.render("SHIELDS", True, COLOR_TEXT_MUTED)
        surface.blit(sh_lbl, (shield_x, rect.top + 4))

        for i in range(3):
            sx = shield_x + i * 22
            sy = rect.top + 22
            color = COLOR_NEON_CYAN if (i < lives) else (50, 55, 70)
            pygame.draw.rect(surface, color, (sx, sy, 16, 12), border_radius=2)

    def _render_pause_overlay(self, surface: pygame.Surface):
        """Draw transparent pause screen."""
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill((10, 14, 22, 200))
        surface.blit(overlay, (0, 0))

        title = render_text_with_shadow(self.font_pause_title, "GAME PAUSED", COLOR_NEON_CYAN, (0, 0, 0), (3, 3))
        surface.blit(title, (WINDOW_WIDTH // 2 - title.get_width() // 2, WINDOW_HEIGHT // 2 - 80))

        sub = self.font_pause_body.render("Press 'P' or ESC to Resume  |  'R' to Restart  |  'Q' for Menu", True, COLOR_TEXT_WHITE)
        surface.blit(sub, (WINDOW_WIDTH // 2 - sub.get_width() // 2, WINDOW_HEIGHT // 2 + 10))
