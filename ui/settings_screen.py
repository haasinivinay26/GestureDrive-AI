"""
Interactive Settings Screen for GestureDrive AI.
Allows configuring camera selection, steering sensitivity, gesture thresholds,
sound effects, fullscreen toggle, difficulty, and keyboard fallback with instant persistence.
"""

import pygame
from typing import Callable

from config import (
    WINDOW_WIDTH, WINDOW_HEIGHT, SETTINGS,
    COLOR_NEON_CYAN, COLOR_NEON_GREEN, COLOR_NEON_RED, COLOR_NEON_AMBER,
    COLOR_PANEL_BG, COLOR_PANEL_BORDER, COLOR_TEXT_WHITE, COLOR_TEXT_MUTED
)
from ui.components import UIButton, UISlider, UIToggle
from utils.helpers import draw_rounded_rect, draw_glow_rect, render_text_with_shadow


class SettingsScreen:
    """Manages application settings controls and user preferences."""

    def __init__(self, on_back: Callable[[], None], on_toggle_fullscreen: Callable[[bool], None]):
        self.on_back = on_back
        self.on_toggle_fullscreen = on_toggle_fullscreen

        # Fonts
        self.font_title = pygame.font.SysFont("Impact", 42)
        self.font_header = pygame.font.SysFont("Verdana", 17, bold=True)
        self.font_label = pygame.font.SysFont("Verdana", 14)
        self.font_btn = pygame.font.SysFont("Verdana", 15, bold=True)

        # Build Interactive Controls
        card_x = 80
        col_w = 520

        # Sliders
        self.slider_steering = UISlider(
            rect=pygame.Rect(card_x, 150, col_w, 14),
            min_val=0.4, max_val=2.5, current_val=SETTINGS.steering_sensitivity,
            label="Steering Sensitivity", font=self.font_label,
            on_change=lambda v: setattr(SETTINGS, "steering_sensitivity", v)
        )

        self.slider_gesture = UISlider(
            rect=pygame.Rect(card_x, 230, col_w, 14),
            min_val=0.4, max_val=0.95, current_val=SETTINGS.gesture_sensitivity,
            label="Gesture Detection Confidence", font=self.font_label,
            on_change=lambda v: setattr(SETTINGS, "gesture_sensitivity", v)
        )

        # Toggles
        self.toggle_preview = UIToggle(
            rect=pygame.Rect(card_x, 290, col_w, 36),
            state=SETTINGS.camera_preview_enabled, label="Live Webcam HUD Preview (PIP)", font=self.font_label,
            on_toggle=lambda s: setattr(SETTINGS, "camera_preview_enabled", s)
        )

        self.toggle_sound = UIToggle(
            rect=pygame.Rect(card_x, 345, col_w, 36),
            state=SETTINGS.sound_enabled, label="Sound Effects & Procedural Audio", font=self.font_label,
            on_toggle=lambda s: setattr(SETTINGS, "sound_enabled", s)
        )

        self.toggle_keyboard = UIToggle(
            rect=pygame.Rect(card_x, 400, col_w, 36),
            state=SETTINGS.keyboard_fallback_enabled, label="Keyboard Fallback Controls (Arrow / WASD)", font=self.font_label,
            on_toggle=lambda s: setattr(SETTINGS, "keyboard_fallback_enabled", s)
        )

        self.toggle_fullscreen = UIToggle(
            rect=pygame.Rect(card_x, 455, col_w, 36),
            state=SETTINGS.fullscreen, label="Fullscreen Display Mode", font=self.font_label,
            on_toggle=self._handle_fullscreen_toggle
        )

        # Right Column: Difficulty and Camera Selector
        right_x = card_x + col_w + 80
        right_w = 480

        self.btn_cam_0 = UIButton(pygame.Rect(right_x, 150, 140, 38), "Cam #0", self.font_btn, lambda: self._set_cam(0))
        self.btn_cam_1 = UIButton(pygame.Rect(right_x + 155, 150, 140, 38), "Cam #1", self.font_btn, lambda: self._set_cam(1))
        self.btn_cam_2 = UIButton(pygame.Rect(right_x + 310, 150, 140, 38), "Cam #2", self.font_btn, lambda: self._set_cam(2))
        self._update_cam_buttons()

        # Difficulty Buttons
        self.btn_diff_easy = UIButton(pygame.Rect(right_x, 270, 140, 38), "Easy", self.font_btn, lambda: self._set_diff("Easy"))
        self.btn_diff_norm = UIButton(pygame.Rect(right_x + 155, 270, 140, 38), "Normal", self.font_btn, lambda: self._set_diff("Normal"))
        self.btn_diff_hard = UIButton(pygame.Rect(right_x + 310, 270, 140, 38), "Hard", self.font_btn, lambda: self._set_diff("Hard"))
        self._update_diff_buttons()

        # Save & Back Button
        self.btn_save_back = UIButton(
            pygame.Rect(WINDOW_WIDTH // 2 - 120, WINDOW_HEIGHT - 65, 240, 45),
            "SAVE & RETURN", self.font_btn, self._save_and_back, primary=True
        )

    def _handle_fullscreen_toggle(self, is_fs: bool):
        SETTINGS.fullscreen = is_fs
        if self.on_toggle_fullscreen:
            self.on_toggle_fullscreen(is_fs)

    def _set_cam(self, idx: int):
        SETTINGS.camera_index = idx
        self._update_cam_buttons()

    def _update_cam_buttons(self):
        self.btn_cam_0.primary = (SETTINGS.camera_index == 0)
        self.btn_cam_1.primary = (SETTINGS.camera_index == 1)
        self.btn_cam_2.primary = (SETTINGS.camera_index == 2)

    def _set_diff(self, diff: str):
        SETTINGS.difficulty = diff
        self._update_diff_buttons()

    def _update_diff_buttons(self):
        self.btn_diff_easy.primary = (SETTINGS.difficulty == "Easy")
        self.btn_diff_norm.primary = (SETTINGS.difficulty == "Normal")
        self.btn_diff_hard.primary = (SETTINGS.difficulty == "Hard")

    def _save_and_back(self):
        SETTINGS.save()
        self.on_back()

    def handle_event(self, event: pygame.event.Event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self._save_and_back()
            return

        self.slider_steering.handle_event(event)
        self.slider_gesture.handle_event(event)
        self.toggle_preview.handle_event(event)
        self.toggle_sound.handle_event(event)
        self.toggle_keyboard.handle_event(event)
        self.toggle_fullscreen.handle_event(event)

        self.btn_cam_0.handle_event(event)
        self.btn_cam_1.handle_event(event)
        self.btn_cam_2.handle_event(event)

        self.btn_diff_easy.handle_event(event)
        self.btn_diff_norm.handle_event(event)
        self.btn_diff_hard.handle_event(event)

        self.btn_save_back.handle_event(event)

    def update(self, dt: float):
        mouse_pos = pygame.mouse.get_pos()
        self.btn_cam_0.update(dt, mouse_pos)
        self.btn_cam_1.update(dt, mouse_pos)
        self.btn_cam_2.update(dt, mouse_pos)
        self.btn_diff_easy.update(dt, mouse_pos)
        self.btn_diff_norm.update(dt, mouse_pos)
        self.btn_diff_hard.update(dt, mouse_pos)
        self.btn_save_back.update(dt, mouse_pos)

    def draw(self, surface: pygame.Surface):
        surface.fill((14, 16, 24))

        # Title
        title_surf = render_text_with_shadow(self.font_title, "SYSTEM SETTINGS", COLOR_NEON_CYAN, (0, 0, 0), (2, 2))
        surface.blit(title_surf, (80, 25))

        # Left Column: Sensitivity & Toggles
        self.slider_steering.draw(surface)
        self.slider_gesture.draw(surface)
        self.toggle_preview.draw(surface)
        self.toggle_sound.draw(surface)
        self.toggle_keyboard.draw(surface)
        self.toggle_fullscreen.draw(surface)

        # Right Column Header
        right_x = 80 + 520 + 80
        cam_lbl = self.font_header.render("CAMERA HARDWARE DEVICE", True, COLOR_NEON_CYAN)
        surface.blit(cam_lbl, (right_x, 115))
        self.btn_cam_0.draw(surface)
        self.btn_cam_1.draw(surface)
        self.btn_cam_2.draw(surface)

        diff_lbl = self.font_header.render("AI TRAFFIC DIFFICULTY", True, COLOR_NEON_CYAN)
        surface.blit(diff_lbl, (right_x, 230))
        self.btn_diff_easy.draw(surface)
        self.btn_diff_norm.draw(surface)
        self.btn_diff_hard.draw(surface)

        # Bottom
        self.btn_save_back.draw(surface)
