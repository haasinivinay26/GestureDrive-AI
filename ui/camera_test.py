"""
Dedicated Camera Test and Diagnostic Screen for GestureDrive AI.
Provides full-resolution webcam preview with live skeleton overlays,
real-time gesture diagnostics, steering wheel angle meters, Calibrate Center button,
and device selector.
"""

import cv2
import pygame
from typing import Callable, Optional

from config import (
    WINDOW_WIDTH, WINDOW_HEIGHT, SETTINGS,
    COLOR_NEON_CYAN, COLOR_NEON_GREEN, COLOR_NEON_RED, COLOR_NEON_AMBER,
    COLOR_PANEL_BG, COLOR_PANEL_BORDER, COLOR_TEXT_WHITE, COLOR_TEXT_MUTED
)
from camera.camera_manager import CameraManager
from camera.gesture_recognizer import GestureState
from ui.components import UIButton
from utils.helpers import draw_rounded_rect, draw_glow_rect, render_text_with_shadow


class CameraTestScreen:
    """Diagnostic screen for testing webcam, steering calibration, and gesture response."""

    def __init__(self, camera_mgr: CameraManager, on_back: Callable[[], None]):
        self.camera_mgr = camera_mgr
        self.on_back = on_back
        self.calib_feedback_timer = 0.0

        # Fonts
        self.font_title = pygame.font.SysFont("Impact", 42)
        self.font_header = pygame.font.SysFont("Verdana", 17, bold=True)
        self.font_body = pygame.font.SysFont("Verdana", 13)
        self.font_big = pygame.font.SysFont("Verdana", 20, bold=True)

        # Buttons
        btn_y = WINDOW_HEIGHT - 65
        self.btn_back = UIButton(pygame.Rect(40, btn_y, 160, 45), "BACK TO MENU", self.font_header, self.on_back)
        self.btn_calib = UIButton(pygame.Rect(220, btn_y, 220, 45), "CALIBRATE CENTER", self.font_header, self._calibrate_center, primary=True)
        self.btn_switch_cam = UIButton(
            pygame.Rect(WINDOW_WIDTH - 240, btn_y, 200, 45),
            f"CAMERA #{SETTINGS.camera_index} (NEXT)",
            self.font_header,
            self._cycle_camera
        )

    def _calibrate_center(self):
        """Zero out the steering orientation based on current hand positions."""
        success = self.camera_mgr.calibrate_center()
        if success:
            self.calib_feedback_timer = 2.0
            print("[CameraTest] Calibrated center successfully.")
        else:
            print("[CameraTest] Calibration failed: no hands detected.")

    def _cycle_camera(self):
        """Switch to next camera device index (0 -> 1 -> 2 -> 0)."""
        next_idx = (SETTINGS.camera_index + 1) % 3
        print(f"[CameraTest] Switching to camera index {next_idx}...")
        self.camera_mgr.restart(new_index=next_idx)
        self.btn_switch_cam.text = f"CAMERA #{SETTINGS.camera_index} (NEXT)"

    def handle_event(self, event: pygame.event.Event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.on_back()
            return
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_c:
            self._calibrate_center()
            return

        self.btn_back.handle_event(event)
        self.btn_calib.handle_event(event)
        self.btn_switch_cam.handle_event(event)

    def update(self, dt: float):
        mouse_pos = pygame.mouse.get_pos()
        self.btn_back.update(dt, mouse_pos)
        self.btn_calib.update(dt, mouse_pos)
        self.btn_switch_cam.update(dt, mouse_pos)

        if self.calib_feedback_timer > 0:
            self.calib_feedback_timer -= dt

    def draw(self, surface: pygame.Surface):
        surface.fill((14, 16, 24))

        # Title
        title_surf = render_text_with_shadow(self.font_title, "WEBCAM & GESTURE DIAGNOSTICS", COLOR_NEON_CYAN, (0, 0, 0), (2, 2))
        surface.blit(title_surf, (40, 20))

        sub = self.font_body.render("Hold hands in neutral position and click 'CALIBRATE CENTER' (or press C) to eliminate steering drift.", True, COLOR_TEXT_MUTED)
        surface.blit(sub, (40, 68))

        # Retrieve camera data
        state: GestureState = self.camera_mgr.get_state()
        raw_frame = self.camera_mgr.latest_raw_frame

        # 1. Main Camera Viewport (Left Side)
        cam_w, cam_h = 620, 465
        cam_x, cam_y = 40, 95
        cam_rect = pygame.Rect(cam_x, cam_y, cam_w, cam_h)

        if raw_frame is not None and self.camera_mgr.is_connected:
            resized = cv2.resize(raw_frame, (cam_w, cam_h))
            rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
            cam_surface = pygame.image.frombuffer(rgb.tobytes(), (cam_w, cam_h), "RGB")
            surface.blit(cam_surface, (cam_x, cam_y))
            pygame.draw.rect(surface, COLOR_NEON_CYAN, cam_rect, width=2, border_radius=8)
        else:
            draw_rounded_rect(surface, cam_rect, (20, 24, 34), radius=8, border_color=COLOR_PANEL_BORDER, border_width=2)
            err_text = self.camera_mgr.error_message or "Webcam offline. Check connection or privacy settings."
            err_surf = self.font_header.render("CAMERA OFFLINE", True, COLOR_NEON_RED)
            surface.blit(err_surf, (cam_rect.centerx - err_surf.get_width() // 2, cam_rect.centery - 20))
            desc_surf = self.font_body.render(err_text[:50], True, COLOR_TEXT_MUTED)
            surface.blit(desc_surf, (cam_rect.centerx - desc_surf.get_width() // 2, cam_rect.centery + 12))

        # 2. Real-Time Telemetry & Diagnostics Card (Right Side)
        diag_x = cam_x + cam_w + 25
        diag_w = WINDOW_WIDTH - diag_x - 40
        diag_rect = pygame.Rect(diag_x, cam_y, diag_w, cam_h)
        draw_glow_rect(surface, diag_rect, (20, 24, 36), COLOR_PANEL_BORDER, radius=8, glow_spread=2)

        # Header
        h_surf = self.font_header.render("TELEMETRY & SENSOR STATUS", True, COLOR_NEON_CYAN)
        surface.blit(h_surf, (diag_x + 20, cam_y + 14))

        cur_y = cam_y + 44
        gap = 48

        # A. Hand Count & Vision FPS
        fps_str = f"{state.hands_detected} HAND(S)  |  {self.camera_mgr.measured_fps:.1f} FPS"
        self._render_diag_row(surface, diag_x + 20, cur_y, "HAND TRACKING", fps_str,
                             COLOR_NEON_GREEN if state.hands_detected >= 2 else (COLOR_NEON_AMBER if state.hands_detected == 1 else COLOR_TEXT_MUTED))
        cur_y += gap

        # B. Steering Direction and Numeric Value
        dir_color = COLOR_NEON_CYAN if state.steer_direction == "CENTER" else (COLOR_NEON_AMBER if state.steer_direction == "LEFT" else COLOR_NEON_GREEN)
        steer_str = f"[{state.steer_direction}]  ({state.steer_angle:+.2f})  |  Tilt: {state.wheel_tilt_degrees:+.1f}°"
        self._render_diag_row(surface, diag_x + 20, cur_y, "STEERING ORIENTATION", steer_str, dir_color)

        # Visual horizontal steering needle
        bar_w = diag_w - 40
        bar_rect = pygame.Rect(diag_x + 20, cur_y + 24, bar_w, 12)
        draw_rounded_rect(surface, bar_rect, (30, 36, 50), radius=3)
        pygame.draw.line(surface, (100, 110, 130), (bar_rect.centerx, bar_rect.top), (bar_rect.centerx, bar_rect.bottom), 1)
        dot_px = int(bar_rect.centerx + state.steer_angle * (bar_w * 0.45))
        pygame.draw.circle(surface, dir_color, (dot_px, bar_rect.centery), 6)
        cur_y += gap + 10

        # C. Calibrated Reference Zero
        calib_str = f"Neutral Tilt: {state.calibrated_tilt:+.1f}°  |  Neutral Mid X: {state.calibrated_mid_x:.2f}"
        self._render_diag_row(surface, diag_x + 20, cur_y, "CALIBRATED ZERO REFERENCE", calib_str, COLOR_TEXT_WHITE)
        cur_y += gap - 4

        # D. Accelerator Status
        accel_c = COLOR_NEON_GREEN if state.is_accelerating else (COLOR_NEON_AMBER if "DETECTED" in state.accel_status else COLOR_TEXT_MUTED)
        self._render_status_pill(surface, diag_x + 20, cur_y, diag_w - 40, "ACCELERATOR", state.accel_status, accel_c)
        cur_y += gap - 4

        # E. Brake Status
        brake_c = COLOR_NEON_RED if state.is_braking else COLOR_TEXT_MUTED
        self._render_status_pill(surface, diag_x + 20, cur_y, diag_w - 40, "BRAKE", state.brake_status, brake_c)
        cur_y += gap - 4

        # F. Start Gesture Status
        start_c = COLOR_NEON_GREEN if state.start_status == "ACCEPTED" else (COLOR_NEON_AMBER if state.is_start_gesture else COLOR_TEXT_MUTED)
        self._render_status_pill(surface, diag_x + 20, cur_y, diag_w - 40, "START GESTURE", f"{state.start_status} (✌️)", start_c)

        # Calibration Feedback Notification
        if self.calib_feedback_timer > 0:
            fb_rect = pygame.Rect(450, WINDOW_HEIGHT - 65, 240, 45)
            draw_glow_rect(surface, fb_rect, (20, 40, 30), COLOR_NEON_GREEN, radius=6, glow_spread=2)
            fb_txt = self.font_header.render("CENTER CALIBRATED! ✓", True, COLOR_NEON_GREEN)
            surface.blit(fb_txt, (fb_rect.centerx - fb_txt.get_width() // 2, fb_rect.centery - fb_txt.get_height() // 2))

        # Bottom Buttons
        self.btn_back.draw(surface)
        self.btn_calib.draw(surface)
        self.btn_switch_cam.draw(surface)

    def _render_diag_row(self, surface: pygame.Surface, x: int, y: int, label: str, val: str, val_color):
        lbl_surf = self.font_body.render(label, True, COLOR_TEXT_MUTED)
        surface.blit(lbl_surf, (x, y))
        v_surf = self.font_big.render(val, True, val_color)
        surface.blit(v_surf, (x, y + 16))

    def _render_status_pill(self, surface: pygame.Surface, x: int, y: int, w: int, label: str, status_text: str, color):
        rect = pygame.Rect(x, y, w, 32)
        active = (color != COLOR_TEXT_MUTED)
        bg = (color[0] // 5, color[1] // 5, color[2] // 5) if active else (22, 26, 38)
        draw_glow_rect(surface, rect, bg, color if active else COLOR_PANEL_BORDER, radius=5, glow_spread=1 if active else 0)
        txt = f"{label}: {status_text}"
        txt_surf = self.font_header.render(txt, True, color if active else COLOR_TEXT_MUTED)
        surface.blit(txt_surf, (rect.centerx - txt_surf.get_width() // 2, rect.centery - txt_surf.get_height() // 2))
