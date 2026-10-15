"""
In-Game Dashboard and Real-Time HUD Overlay for GestureDrive AI.
Features high-performance peripheral gauge clusters, non-obstructive road view,
integrated live webcam PIP with MediaPipe skeleton, dynamic gesture status badges,
stealth steering chevrons, and interactive pause menu modal.
"""

import math
import pygame
from typing import Optional, Callable

from config import (
    WINDOW_WIDTH, WINDOW_HEIGHT, SETTINGS,
    COLOR_PANEL_BG, COLOR_PANEL_BORDER,
    COLOR_NEON_CYAN, COLOR_NEON_GREEN, COLOR_NEON_RED, COLOR_NEON_AMBER,
    COLOR_TEXT_WHITE, COLOR_TEXT_MUTED,
    CAMERA_PIP_WIDTH, CAMERA_PIP_HEIGHT
)
from camera.gesture_recognizer import GestureState
from ui.components import UIButton
from utils.helpers import (
    draw_rounded_rect, draw_glow_rect, draw_glass_rect, draw_arc,
    render_text_with_shadow, clamp
)


class Dashboard:
    """Manages HUD rendering, gauges, live camera preview, stealth steering, and pause menu."""

    def __init__(self, on_pause_action: Optional[Callable[[str], None]] = None):
        self.on_pause_action = on_pause_action
        self.anim_timer = 0.0

        # Fonts
        self.font_speed = pygame.font.SysFont("Impact", 46)
        self.font_unit = pygame.font.SysFont("Verdana", 13, bold=True)
        self.font_label = pygame.font.SysFont("Verdana", 11, bold=True)
        self.font_value = pygame.font.SysFont("Verdana", 17, bold=True)
        self.font_gear = pygame.font.SysFont("Impact", 28)
        self.font_gesture = pygame.font.SysFont("Verdana", 13, bold=True)
        self.font_gesture_sub = pygame.font.SysFont("Verdana", 11)
        self.font_pause_title = pygame.font.SysFont("Impact", 56)
        self.font_pause_btn = pygame.font.SysFont("Verdana", 15, bold=True)
        self.font_pip_status = pygame.font.SysFont("Verdana", 11, bold=True)

        # In-game Pause Button (Top-Right, beside camera PIP)
        self.btn_pause_toggle = UIButton(
            pygame.Rect(WINDOW_WIDTH - 110, 15, 90, 32),
            "⏸ PAUSE", self.font_label,
            lambda: self._trigger_pause("TOGGLE_PAUSE"),
            accent_color=COLOR_NEON_CYAN
        )

        # Pause Modal Buttons
        modal_w = 300
        cx = WINDOW_WIDTH // 2 - modal_w // 2
        modal_y = 230
        gap = 52

        self.pause_buttons = [
            UIButton(pygame.Rect(cx, modal_y, modal_w, 44), "RESUME RACE", self.font_pause_btn, lambda: self._trigger_pause("RESUME"), primary=True, shortcut="[ESC]"),
            UIButton(pygame.Rect(cx, modal_y + gap, modal_w, 44), "RESTART RACE", self.font_pause_btn, lambda: self._trigger_pause("RESTART"), shortcut="[R]"),
            UIButton(pygame.Rect(cx, modal_y + gap * 2, modal_w, 44), "HOW TO PLAY", self.font_pause_btn, lambda: self._trigger_pause("HOW_TO_PLAY"), shortcut="[H]"),
            UIButton(pygame.Rect(cx, modal_y + gap * 3, modal_w, 44), "SETTINGS", self.font_pause_btn, lambda: self._trigger_pause("SETTINGS"), shortcut="[S]"),
            UIButton(pygame.Rect(cx, modal_y + gap * 4, modal_w, 44), "MAIN MENU", self.font_pause_btn, lambda: self._trigger_pause("MENU"), accent_color=COLOR_NEON_RED, shortcut="[Q]"),
        ]

    def _trigger_pause(self, action: str):
        if self.on_pause_action:
            self.on_pause_action(action)

    def handle_event(self, event: pygame.event.Event, is_paused: bool) -> bool:
        """Handle HUD and Pause modal interactions."""
        if is_paused:
            for btn in self.pause_buttons:
                if btn.handle_event(event):
                    return True
        else:
            if self.btn_pause_toggle.handle_event(event):
                return True
        return False

    def update(self, dt: float, is_paused: bool):
        """Update animations and button hover states."""
        self.anim_timer += dt
        mouse_pos = pygame.mouse.get_pos()

        if is_paused:
            for btn in self.pause_buttons:
                btn.update(dt, mouse_pos)
        else:
            self.btn_pause_toggle.update(dt, mouse_pos)

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
        """Render complete in-game dashboard with clear central road view."""
        self.update(1.0 / 60.0, is_paused)

        # 1. Top-Left Speedometer & Telemetry Cluster
        self._render_speed_cluster(surface, speed_kmh, score, high_score, gesture_state)

        # 2. Stealth Steering Chevron Indicator (Leaves horizon road clear!)
        self._render_stealth_steering(surface, gesture_state)

        # 3. Top-Right Live Camera PIP with Hand Landmark Skeleton
        if SETTINGS.camera_preview_enabled:
            self._render_camera_pip(surface, camera_surface, is_camera_connected, gesture_state)

        # 4. Top-Right Pause Button
        self.btn_pause_toggle.draw(surface)

        # 5. Bottom-Left Distance and Multiplier Banner
        self._render_bottom_banner(surface, distance_str, race_time_str, multiplier, lives)

        # 6. Interactive Pause Modal Overlay if paused
        if is_paused:
            self._render_pause_overlay(surface)

    def _render_speed_cluster(self, surface: pygame.Surface, speed_kmh: float, score: int, high_score: int, gesture_state: GestureState):
        """Draw circular tachometer arc, large digital speed readout, gear, and score."""
        panel_w, panel_h = 310, 118
        panel_rect = pygame.Rect(20, 15, panel_w, panel_h)
        draw_glass_rect(surface, panel_rect, bg_rgba=(14, 18, 28, 220), border_color=(35, 48, 72), radius=10)

        # Tachometer Circular Arc Gauge
        dial_cx = panel_rect.left + 62
        dial_cy = panel_rect.top + 60
        dial_radius = 44

        # Background track arc (from 140 deg to 400 deg -> 260 deg sweep)
        draw_arc(surface, (28, 35, 50), (dial_cx, dial_cy), dial_radius, 140.0, 400.0, width=7)

        # Active speed fill arc
        speed_ratio = clamp(speed_kmh / 220.0, 0.0, 1.0)
        active_sweep = speed_ratio * 260.0
        if active_sweep > 1.0:
            if speed_ratio < 0.65:
                arc_color = COLOR_NEON_CYAN
            elif speed_ratio < 0.88:
                arc_color = COLOR_NEON_AMBER
            else:
                arc_color = COLOR_NEON_RED
            draw_arc(surface, arc_color, (dial_cx, dial_cy), dial_radius, 140.0, 140.0 + active_sweep, width=7)

        # Large Digital Speed readout
        spd_text = self.font_speed.render(f"{int(speed_kmh)}", True, COLOR_TEXT_WHITE)
        surface.blit(spd_text, (dial_cx - spd_text.get_width() // 2, dial_cy - 22))

        kmh_text = self.font_unit.render("KM/H", True, COLOR_NEON_CYAN)
        surface.blit(kmh_text, (dial_cx - kmh_text.get_width() // 2, dial_cy + 18))

        # Right Telemetry: Gear & Driving Mode, Score, Record
        telem_x = panel_rect.left + 130

        # Gear calculation
        if speed_kmh < 5:
            gear_str = "N"
            mode_str = "IDLE"
            mode_color = COLOR_TEXT_MUTED
        elif speed_kmh < 45:
            gear_str = "1"
            mode_str = "DRIVE"
            mode_color = COLOR_NEON_CYAN
        elif speed_kmh < 85:
            gear_str = "2"
            mode_str = "DRIVE"
            mode_color = COLOR_NEON_CYAN
        elif speed_kmh < 130:
            gear_str = "3"
            mode_str = "DRIVE"
            mode_color = COLOR_NEON_CYAN
        elif speed_kmh < 175:
            gear_str = "4"
            mode_str = "TURBO"
            mode_color = COLOR_NEON_AMBER
        else:
            gear_str = "5"
            mode_str = "HYPER"
            mode_color = COLOR_NEON_RED

        # Gear Badge
        gear_badge = pygame.Rect(telem_x, panel_rect.top + 12, 44, 30)
        draw_rounded_rect(surface, gear_badge, (22, 28, 44), radius=4, border_color=(0, 200, 255), border_width=1)
        g_val = self.font_gear.render(gear_str, True, COLOR_NEON_CYAN)
        surface.blit(g_val, (gear_badge.centerx - g_val.get_width() // 2, gear_badge.centery - g_val.get_height() // 2 - 1))

        # Mode Badge
        mode_badge = pygame.Rect(telem_x + 52, panel_rect.top + 14, 62, 26)
        draw_rounded_rect(surface, mode_badge, (18, 24, 38), radius=4, border_color=mode_color, border_width=1)
        m_txt = self.font_label.render(mode_str, True, mode_color)
        surface.blit(m_txt, (mode_badge.centerx - m_txt.get_width() // 2, mode_badge.centery - m_txt.get_height() // 2))

        # Score & High Score Record
        score_lbl = self.font_label.render("SCORE", True, COLOR_TEXT_MUTED)
        surface.blit(score_lbl, (telem_x, panel_rect.top + 50))
        score_val = self.font_value.render(f"{score:,}", True, COLOR_NEON_GREEN)
        surface.blit(score_val, (telem_x, panel_rect.top + 65))

        hi_lbl = self.font_label.render("RECORD", True, COLOR_TEXT_MUTED)
        surface.blit(hi_lbl, (telem_x + 95, panel_rect.top + 50))
        hi_val = self.font_value.render(f"{high_score:,}", True, COLOR_NEON_AMBER)
        surface.blit(hi_val, (telem_x + 95, panel_rect.top + 65))

    def _render_stealth_steering(self, surface: pygame.Surface, state: GestureState):
        """
        Draw a sleek, non-intrusive horizon steering indicator.
        Leaves central vanishing point clear, while giving unmistakable turn feedback.
        """
        cx = WINDOW_WIDTH // 2
        cy = 30

        angle = state.steer_angle
        direction = state.steer_direction

        # Stealth pill container
        stealth_w, stealth_h = 240, 28
        stealth_rect = pygame.Rect(cx - stealth_w // 2, cy, stealth_w, stealth_h)
        draw_glass_rect(surface, stealth_rect, bg_rgba=(14, 18, 28, 170), border_color=(35, 45, 65), radius=14)

        # Center zero tick
        pygame.draw.line(surface, (70, 85, 115), (cx, cy + 4), (cx, cy + stealth_h - 4), 1)

        # Active Steering Position Dot
        steer_px = int(cx + angle * (stealth_w * 0.42))
        dot_color = COLOR_NEON_CYAN if abs(angle) > 0.05 else (80, 110, 140)
        pygame.draw.circle(surface, dot_color, (steer_px, cy + stealth_h // 2), 6)

        # Subtle directional animated arrows
        pulse = 0.5 + 0.5 * math.sin(self.anim_timer * 6.0)
        if direction == "LEFT":
            arrow_c = (int(0 + 40 * pulse), int(220 + 35 * pulse), 255)
            arrow_surf = self.font_label.render("«« STEER LEFT", True, arrow_c)
            surface.blit(arrow_surf, (cx - 105, cy + stealth_h // 2 - arrow_surf.get_height() // 2))
        elif direction == "RIGHT":
            arrow_c = (int(0 + 40 * pulse), int(220 + 35 * pulse), 255)
            arrow_surf = self.font_label.render("STEER RIGHT »»", True, arrow_c)
            surface.blit(arrow_surf, (cx + 105 - arrow_surf.get_width(), cy + stealth_h // 2 - arrow_surf.get_height() // 2))
        else:
            center_surf = self.font_label.render("CENTER", True, (70, 90, 120))
            surface.blit(center_surf, (cx - center_surf.get_width() // 2, cy + stealth_h // 2 - center_surf.get_height() // 2))

    def _render_camera_pip(
        self,
        surface: pygame.Surface,
        camera_surface: Optional[pygame.Surface],
        is_camera_connected: bool,
        state: GestureState
    ):
        """Draw compact live webcam PIP in top-right with integrated gesture status badges."""
        pip_w = 220
        pip_h = 165
        pip_x = WINDOW_WIDTH - pip_w - 20
        pip_y = 55

        pip_rect = pygame.Rect(pip_x, pip_y, pip_w, pip_h)

        if camera_surface and is_camera_connected:
            # Scale preview to fit cleanly
            scaled_cam = pygame.transform.smoothscale(camera_surface, (pip_w, pip_h))
            surface.blit(scaled_cam, (pip_x, pip_y))
            # Neon border with glowing frame
            pygame.draw.rect(surface, COLOR_NEON_CYAN, pip_rect, width=2, border_radius=6)
        else:
            # Standby / Camera off display
            draw_glass_rect(surface, pip_rect, bg_rgba=(20, 24, 36, 230), border_color=COLOR_PANEL_BORDER, radius=6)
            msg1 = self.font_gesture.render("WEBCAM OFFLINE", True, COLOR_NEON_AMBER)
            msg2 = self.font_pip_status.render("KEYBOARD FALLBACK ACTIVE", True, COLOR_TEXT_MUTED)
            surface.blit(msg1, (pip_rect.centerx - msg1.get_width() // 2, pip_rect.centery - 12))
            surface.blit(msg2, (pip_rect.centerx - msg2.get_width() // 2, pip_rect.centery + 8))

        # Top PIP Header: Connection Dot & Hand Count
        top_bar = pygame.Rect(pip_x, pip_y - 22, pip_w, 20)
        draw_glass_rect(surface, top_bar, bg_rgba=(14, 18, 28, 200), border_color=(35, 45, 65), radius=4)

        dot_c = COLOR_NEON_GREEN if is_camera_connected else COLOR_NEON_AMBER
        pygame.draw.circle(surface, dot_c, (pip_x + 10, top_bar.centery), 4)

        cam_txt = "WEBCAM ONLINE" if is_camera_connected else "FALLBACK"
        c_surf = self.font_pip_status.render(cam_txt, True, COLOR_TEXT_WHITE)
        surface.blit(c_surf, (pip_x + 18, top_bar.centery - c_surf.get_height() // 2))

        hands_cnt = state.hands_detected
        hands_txt = f"{hands_cnt} HAND{'S' if hands_cnt != 1 else ''}"
        h_color = COLOR_NEON_CYAN if hands_cnt >= 2 else (COLOR_NEON_AMBER if hands_cnt == 1 else COLOR_TEXT_MUTED)
        h_surf = self.font_pip_status.render(hands_txt, True, h_color)
        surface.blit(h_surf, (top_bar.right - h_surf.get_width() - 8, top_bar.centery - h_surf.get_height() // 2))

        # Bottom PIP Telemetry Card: Active Recognized Gesture
        badge_h = 36
        badge_rect = pygame.Rect(pip_x, pip_y + pip_h + 4, pip_w, badge_h)

        if state.is_braking:
            b_border = COLOR_NEON_RED
            b_txt = "✋ EMERGENCY BRAKE"
            b_color = COLOR_NEON_RED
            sub_txt = "Vehicle rapidly stopping"
        elif state.is_accelerating:
            b_border = COLOR_NEON_GREEN
            b_txt = "👍 ACCELERATING"
            b_color = COLOR_NEON_GREEN
            sub_txt = "Throttle engaged"
        elif state.hands_detected >= 2:
            b_border = COLOR_NEON_CYAN
            b_txt = f"🖐️ STEERING [{state.steer_direction}]"
            b_color = COLOR_NEON_CYAN
            sub_txt = f"Wheel tilt: {state.steer_angle:+.2f}"
        else:
            b_border = (40, 50, 70)
            b_txt = "NEUTRAL / COASTING"
            b_color = COLOR_TEXT_MUTED
            sub_txt = "Hold hands up to drive"

        draw_glass_rect(surface, badge_rect, bg_rgba=(14, 18, 28, 220), border_color=b_border, radius=6)
        g_s = self.font_gesture.render(b_txt, True, b_color)
        surface.blit(g_s, (badge_rect.centerx - g_s.get_width() // 2, badge_rect.top + 3))

        sub_s = self.font_gesture_sub.render(sub_txt, True, COLOR_TEXT_MUTED)
        surface.blit(sub_s, (badge_rect.centerx - sub_s.get_width() // 2, badge_rect.top + 19))

    def _render_bottom_banner(self, surface: pygame.Surface, distance_str: str, race_time_str: str, multiplier: float, lives: int):
        """Draw distance traveled, race timer, combo multiplier badge, and vehicle shields."""
        bar_w, bar_h = 420, 44
        bar_x = 20
        bar_y = WINDOW_HEIGHT - bar_h - 15

        rect = pygame.Rect(bar_x, bar_y, bar_w, bar_h)
        draw_glass_rect(surface, rect, bg_rgba=(14, 18, 28, 220), border_color=(35, 48, 72), radius=8)

        # Distance
        dist_lbl = self.font_label.render("DISTANCE", True, COLOR_TEXT_MUTED)
        surface.blit(dist_lbl, (rect.left + 14, rect.top + 4))
        dist_val = self.font_value.render(distance_str, True, COLOR_TEXT_WHITE)
        surface.blit(dist_val, (rect.left + 14, rect.top + 18))

        # Time
        time_lbl = self.font_label.render("TIME", True, COLOR_TEXT_MUTED)
        surface.blit(time_lbl, (rect.left + 120, rect.top + 4))
        time_val = self.font_value.render(race_time_str, True, COLOR_NEON_CYAN)
        surface.blit(time_val, (rect.left + 120, rect.top + 18))

        # Combo Multiplier
        mult_badge = pygame.Rect(rect.left + 225, rect.top + 8, 76, 28)
        badge_c = COLOR_NEON_AMBER if multiplier > 1.5 else COLOR_NEON_GREEN
        draw_rounded_rect(surface, mult_badge, (22, 28, 44), radius=4, border_color=badge_c, border_width=1)
        m_txt = self.font_label.render(f"{multiplier:.1f}x MULT", True, badge_c)
        surface.blit(m_txt, (mult_badge.centerx - m_txt.get_width() // 2, mult_badge.centery - m_txt.get_height() // 2))

        # Lives / Vehicle Shields
        shield_x = rect.left + 320
        sh_lbl = self.font_label.render("SHIELDS", True, COLOR_TEXT_MUTED)
        surface.blit(sh_lbl, (shield_x, rect.top + 4))

        for i in range(3):
            sx = shield_x + i * 26
            sy = rect.top + 21
            color = COLOR_NEON_CYAN if (i < lives) else (40, 48, 65)
            pygame.draw.rect(surface, color, (sx, sy, 20, 14), border_radius=3)
            if i < lives:
                pygame.draw.rect(surface, (255, 255, 255), (sx + 2, sy + 2, 4, 10), border_radius=1)

    def _render_pause_overlay(self, surface: pygame.Surface):
        """Draw modern glassmorphic pause screen with interactive menu buttons."""
        # Darkening backdrop
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill((8, 10, 16, 215))
        surface.blit(overlay, (0, 0))

        # Modal Card
        card_w, card_h = 420, 420
        card_x = WINDOW_WIDTH // 2 - card_w // 2
        card_y = 120
        card_rect = pygame.Rect(card_x, card_y, card_w, card_h)

        draw_glass_rect(surface, card_rect, bg_rgba=(18, 22, 36, 240), border_color=(0, 200, 255), radius=14, border_width=2)

        # Title
        title = render_text_with_shadow(self.font_pause_title, "GAME PAUSED", COLOR_NEON_CYAN, (0, 0, 0), (3, 3))
        surface.blit(title, (WINDOW_WIDTH // 2 - title.get_width() // 2, card_y + 24))

        sub_msg = self.font_label.render("RACE IS CURRENTLY SUSPENDED", True, COLOR_TEXT_MUTED)
        surface.blit(sub_msg, (WINDOW_WIDTH // 2 - sub_msg.get_width() // 2, card_y + 86))

        # Draw Pause Menu Buttons
        for btn in self.pause_buttons:
            btn.draw(surface)
