"""
Interactive Gesture Calibration Screen for GestureDrive AI.
Guides the player through a 5-step visual calibration wizard to align neutral steering,
test turn limits, and verify accelerator and brake gestures.
"""

import pygame
from typing import Callable

from config import (
    WINDOW_WIDTH, WINDOW_HEIGHT,
    COLOR_NEON_CYAN, COLOR_NEON_GREEN, COLOR_NEON_RED, COLOR_NEON_AMBER,
    COLOR_PANEL_BG, COLOR_PANEL_BORDER, COLOR_TEXT_WHITE, COLOR_TEXT_MUTED
)
from camera.camera_manager import CameraManager
from camera.calibration import CalibrationManager, CalibrationStep
from ui.components import UIButton
from utils.helpers import draw_rounded_rect, draw_glow_rect, render_text_with_shadow, clamp


class CalibrationScreen:
    """Renders the step-by-step calibration wizard."""

    def __init__(self, camera_mgr: CameraManager, on_finish: Callable[[], None], on_back: Callable[[], None]):
        self.camera_mgr = camera_mgr
        self.on_finish = on_finish
        self.on_back = on_back
        self.calib_mgr = CalibrationManager()

        # Fonts
        self.font_title = pygame.font.SysFont("Impact", 42)
        self.font_step = pygame.font.SysFont("Verdana", 24, bold=True)
        self.font_desc = pygame.font.SysFont("Verdana", 17)
        self.font_hint = pygame.font.SysFont("Verdana", 14)
        self.font_btn = pygame.font.SysFont("Verdana", 16, bold=True)

        # Buttons
        btn_y = WINDOW_HEIGHT - 65
        self.btn_back = UIButton(pygame.Rect(40, btn_y, 160, 45), "CANCEL", self.font_btn, self.on_back)
        self.btn_calib_center = UIButton(pygame.Rect(220, btn_y, 220, 45), "CALIBRATE CENTER", self.font_btn, self._calibrate_center)
        self.btn_done = UIButton(pygame.Rect(WINDOW_WIDTH - 240, btn_y, 200, 45), "START RACE", self.font_btn, self.on_finish, primary=True)
        self.calib_feedback_timer = 0.0

    def _calibrate_center(self):
        """Zero the neutral steering position directly."""
        success = self.camera_mgr.calibrate_center()
        if success:
            self.calib_feedback_timer = 2.0

    def reset(self):
        """Reset calibration session."""
        self.calib_mgr.reset()
        self.calib_feedback_timer = 0.0

    def handle_event(self, event: pygame.event.Event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.on_back()
            return
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_c:
            self._calibrate_center()
            return
        self.btn_back.handle_event(event)
        self.btn_calib_center.handle_event(event)
        if self.calib_mgr.is_finished:
            self.btn_done.handle_event(event)

    def update(self, dt: float):
        mouse_pos = pygame.mouse.get_pos()
        self.btn_back.update(dt, mouse_pos)
        self.btn_calib_center.update(dt, mouse_pos)
        if self.calib_mgr.is_finished:
            self.btn_done.update(dt, mouse_pos)

        if self.calib_feedback_timer > 0:
            self.calib_feedback_timer -= dt

        # Advance calibration state machine with latest camera gestures
        state = self.camera_mgr.get_state()
        self.step_progress = self.calib_mgr.update(dt, state)

    def draw(self, surface: pygame.Surface):
        surface.fill((14, 16, 24))

        # Title
        title_surf = render_text_with_shadow(self.font_title, "GESTURE CALIBRATION WIZARD", COLOR_NEON_CYAN, (0, 0, 0), (2, 2))
        surface.blit(title_surf, (40, 25))

        step_info = self.calib_mgr.get_step_info()

        # 1. Main Step Instruction Card
        card_w, card_h = 700, 420
        card_x, card_y = 40, 100
        card_rect = pygame.Rect(card_x, card_y, card_w, card_h)
        draw_glow_rect(surface, card_rect, (20, 24, 36), COLOR_PANEL_BORDER, radius=10, glow_spread=2)

        # Step Title
        s_title = self.font_step.render(step_info["title"], True, COLOR_NEON_GREEN if self.calib_mgr.is_finished else COLOR_NEON_CYAN)
        surface.blit(s_title, (card_x + 30, card_y + 25))

        # Progress Indicator (Step X of 5)
        if not self.calib_mgr.is_finished:
            step_num = self.calib_mgr.current_step + 1
            num_surf = self.font_desc.render(f"Step {step_num} of 5", True, COLOR_TEXT_MUTED)
            surface.blit(num_surf, (card_right := card_x + card_w - num_surf.get_width() - 30, card_y + 30))

        # Main Instruction Text
        inst_surf = self.font_desc.render(step_info["instruction"], True, COLOR_TEXT_WHITE)
        surface.blit(inst_surf, (card_x + 30, card_y + 85))

        # Target Criteria
        target_surf = self.font_desc.render(f"Target: {step_info['target']}", True, COLOR_NEON_AMBER)
        surface.blit(target_surf, (card_x + 30, card_y + 125))

        # Hint
        hint_surf = self.font_hint.render(f"Tip: {step_info['hint']}", True, COLOR_TEXT_MUTED)
        surface.blit(hint_surf, (card_x + 30, card_y + 165))

        # Progress Bar for Current Step
        p_bar_w = card_w - 60
        p_bar_h = 24
        p_bar_x = card_x + 30
        p_bar_y = card_y + 230

        # Bar background
        draw_rounded_rect(surface, pygame.Rect(p_bar_x, p_bar_y, p_bar_w, p_bar_h), (30, 36, 50), radius=6)

        # Bar filled
        fill_w = int(p_bar_w * self.step_progress)
        if fill_w > 0:
            fill_c = COLOR_NEON_GREEN if self.step_progress >= 1.0 else COLOR_NEON_CYAN
            draw_rounded_rect(surface, pygame.Rect(p_bar_x, p_bar_y, fill_w, p_bar_h), fill_c, radius=6)

        # Bar percentage text
        pct_txt = self.font_hint.render(f"{int(self.step_progress * 100)}%", True, COLOR_TEXT_WHITE)
        surface.blit(pct_txt, (p_bar_x + p_bar_w // 2 - pct_txt.get_width() // 2, p_bar_y + 3))

        # 2. Camera Live Preview PIP (Right Side)
        pip_w, pip_h = 440, 330
        pip_x = WINDOW_WIDTH - pip_w - 40
        pip_y = 100
        pip_rect = pygame.Rect(pip_x, pip_y, pip_w, pip_h)

        cam_surf = self.camera_mgr.get_preview_surface()
        if cam_surf and self.camera_mgr.is_connected:
            scaled_cam = pygame.transform.scale(cam_surf, (pip_w, pip_h))
            surface.blit(scaled_cam, (pip_x, pip_y))
            pygame.draw.rect(surface, COLOR_NEON_CYAN, pip_rect, width=2, border_radius=8)
        else:
            draw_rounded_rect(surface, pip_rect, (20, 24, 36), radius=8, border_color=COLOR_PANEL_BORDER, border_width=1)
            msg = self.font_desc.render("Camera preview offline", True, COLOR_TEXT_MUTED)
            surface.blit(msg, (pip_rect.centerx - msg.get_width() // 2, pip_rect.centery))

        # Live Steering Angle Readout under PIP
        state = self.camera_mgr.get_state()
        meter_rect = pygame.Rect(pip_x, pip_y + pip_h + 15, pip_w, 42)
        draw_rounded_rect(surface, meter_rect, (20, 24, 36), radius=6, border_color=COLOR_PANEL_BORDER, border_width=1)
        st_text = self.font_desc.render(f"Wheel Angle: {state.wheel_tilt_degrees:+.1f} deg  |  Gesture: {state.active_gesture}", True, COLOR_NEON_CYAN)
        surface.blit(st_text, (meter_rect.centerx - st_text.get_width() // 2, meter_rect.centery - st_text.get_height() // 2))

        # Buttons
        self.btn_back.draw(surface)
        self.btn_calib_center.draw(surface)
        if self.calib_mgr.is_finished:
            self.btn_done.draw(surface)

        if self.calib_feedback_timer > 0:
            fb_rect = pygame.Rect(460, WINDOW_HEIGHT - 65, 230, 45)
            draw_glow_rect(surface, fb_rect, (20, 40, 30), COLOR_NEON_GREEN, radius=6, glow_spread=2)
            fb_txt = self.font_btn.render("CENTER CALIBRATED! ✓", True, COLOR_NEON_GREEN)
            surface.blit(fb_txt, (fb_rect.centerx - fb_txt.get_width() // 2, fb_rect.centery - fb_txt.get_height() // 2))
