"""
Dedicated Camera Test and Diagnostic Screen for GestureDrive AI.
Provides full-resolution webcam preview with live skeleton overlays,
real-time gesture diagnostics, steering wheel angle meters, and device selector.
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
    """Diagnostic screen for testing webcam and gesture response."""

    def __init__(self, camera_mgr: CameraManager, on_back: Callable[[], None]):
        self.camera_mgr = camera_mgr
        self.on_back = on_back

        # Fonts
        self.font_title = pygame.font.SysFont("Impact", 44)
        self.font_header = pygame.font.SysFont("Verdana", 18, bold=True)
        self.font_body = pygame.font.SysFont("Verdana", 14)
        self.font_big = pygame.font.SysFont("Verdana", 22, bold=True)

        # Buttons
        self.btn_back = UIButton(pygame.Rect(40, WINDOW_HEIGHT - 65, 180, 45), "BACK TO MENU", self.font_header, self.on_back)
        self.btn_switch_cam = UIButton(
            pygame.Rect(WINDOW_WIDTH - 240, WINDOW_HEIGHT - 65, 200, 45),
            f"CAMERA #{SETTINGS.camera_index} (NEXT)",
            self.font_header,
            self._cycle_camera
        )

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
        self.btn_back.handle_event(event)
        self.btn_switch_cam.handle_event(event)

    def update(self, dt: float):
        mouse_pos = pygame.mouse.get_pos()
        self.btn_back.update(dt, mouse_pos)
        self.btn_switch_cam.update(dt, mouse_pos)

    def draw(self, surface: pygame.Surface):
        surface.fill((14, 16, 24))

        # Title
        title_surf = render_text_with_shadow(self.font_title, "WEBCAM & GESTURE TEST", COLOR_NEON_CYAN, (0, 0, 0), (2, 2))
        surface.blit(title_surf, (40, 25))

        sub = self.font_body.render("Verify your hand detection, steering wheel tilt, thumbs-up, and open-palm braking before racing.", True, COLOR_TEXT_MUTED)
        surface.blit(sub, (40, 75))

        # Retrieve camera data
        state: GestureState = self.camera_mgr.get_state()
        raw_frame = self.camera_mgr.latest_raw_frame

        # 1. Main Camera Viewport (Left Side)
        cam_w, cam_h = 640, 480
        cam_x, cam_y = 40, 110
        cam_rect = pygame.Rect(cam_x, cam_y, cam_w, cam_h)

        if raw_frame is not None and self.camera_mgr.is_connected:
            # Resize raw annotated frame for crisp test display
            resized = cv2.resize(raw_frame, (cam_w, cam_h))
            rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
            cam_surface = pygame.image.frombuffer(rgb.tobytes(), (cam_w, cam_h), "RGB")
            surface.blit(cam_surface, (cam_x, cam_y))
            pygame.draw.rect(surface, COLOR_NEON_CYAN, cam_rect, width=2, border_radius=8)
        else:
            # Standby screen
            draw_rounded_rect(surface, cam_rect, (20, 24, 34), radius=8, border_color=COLOR_PANEL_BORDER, border_width=2)
            err_text = self.camera_mgr.error_message or "Webcam not responding. Check connection or privacy settings."
            err_surf = self.font_header.render("CAMERA OFFLINE", True, COLOR_NEON_RED)
            surface.blit(err_surf, (cam_rect.centerx - err_surf.get_width() // 2, cam_rect.centery - 20))
            desc_surf = self.font_body.render(err_text[:50], True, COLOR_TEXT_MUTED)
            surface.blit(desc_surf, (cam_rect.centerx - desc_surf.get_width() // 2, cam_rect.centery + 12))

        # 2. Real-Time Telemetry & Diagnostics Card (Right Side)
        diag_x = cam_x + cam_w + 30
        diag_w = WINDOW_WIDTH - diag_x - 40
        diag_rect = pygame.Rect(diag_x, cam_y, diag_w, cam_h)
        draw_glow_rect(surface, diag_rect, (20, 24, 36), COLOR_PANEL_BORDER, radius=8, glow_spread=2)

        # Header
        h_surf = self.font_header.render("LIVE TELEMETRY", True, COLOR_NEON_CYAN)
        surface.blit(h_surf, (diag_x + 20, cam_y + 18))

        # Diagnostics items
        cur_y = cam_y + 60
        gap = 58

        # A. Hand Count
        self._render_diag_row(surface, diag_x + 20, cur_y, "HANDS DETECTED", f"{state.hands_detected} HAND(S)",
                             COLOR_NEON_GREEN if state.hands_detected >= 2 else (COLOR_NEON_AMBER if state.hands_detected == 1 else COLOR_TEXT_MUTED))
        cur_y += gap

        # B. Steering Wheel Angle
        self._render_diag_row(surface, diag_x + 20, cur_y, "STEERING WHEEL TILT", f"{state.wheel_tilt_degrees:+.1f} deg",
                             COLOR_NEON_CYAN if abs(state.steer_angle) > 0.05 else COLOR_TEXT_WHITE)
        # Small visual horizontal meter
        bar_w = diag_w - 40
        bar_rect = pygame.Rect(diag_x + 20, cur_y + 24, bar_w, 14)
        draw_rounded_rect(surface, bar_rect, (30, 36, 50), radius=3)
        pygame.draw.line(surface, (100, 110, 130), (bar_rect.centerx, bar_rect.top), (bar_rect.centerx, bar_rect.bottom), 1)
        dot_px = int(bar_rect.centerx + state.steer_angle * (bar_w * 0.45))
        pygame.draw.circle(surface, COLOR_NEON_CYAN, (dot_px, bar_rect.centery), 6)
        cur_y += gap + 10

        # C. Accelerator (Thumbs-Up)
        accel_color = COLOR_NEON_GREEN if state.is_accelerating else (45, 55, 75)
        self._render_status_pill(surface, diag_x + 20, cur_y, diag_w - 40, "ACCELERATOR [THUMBS-UP]", state.is_accelerating, accel_color)
        cur_y += gap

        # D. Brake (Open-Palm)
        brake_color = COLOR_NEON_RED if state.is_braking else (45, 55, 75)
        self._render_status_pill(surface, diag_x + 20, cur_y, diag_w - 40, "BRAKE [OPEN PALM]", state.is_braking, brake_color)
        cur_y += gap

        # E. FPS and Latency
        fps_str = f"{self.camera_mgr.measured_fps:.1f} FPS"
        self._render_diag_row(surface, diag_x + 20, cur_y, "VISION PIPELINE SPEED", fps_str, COLOR_NEON_GREEN)

        # Buttons
        self.btn_back.draw(surface)
        self.btn_switch_cam.draw(surface)

    def _render_diag_row(self, surface: pygame.Surface, x: int, y: int, label: str, val: str, val_color):
        lbl_surf = self.font_body.render(label, True, COLOR_TEXT_MUTED)
        surface.blit(lbl_surf, (x, y))
        v_surf = self.font_big.render(val, True, val_color)
        surface.blit(v_surf, (x, y + 18))

    def _render_status_pill(self, surface: pygame.Surface, x: int, y: int, w: int, text: str, active: bool, color):
        rect = pygame.Rect(x, y, w, 38)
        bg = (color[0] // 4, color[1] // 4, color[2] // 4) if active else (22, 26, 38)
        draw_glow_rect(surface, rect, bg, color if active else COLOR_PANEL_BORDER, radius=6, glow_spread=2 if active else 0)
        status_txt = "ACTIVE" if active else "INACTIVE"
        txt_surf = self.font_header.render(f"{text}: {status_txt}", True, color if active else COLOR_TEXT_MUTED)
        surface.blit(txt_surf, (rect.centerx - txt_surf.get_width() // 2, rect.centery - txt_surf.get_height() // 2))
