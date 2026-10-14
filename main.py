"""
GestureDrive AI — Camera-Controlled Car Racing Game Using Hand Gestures.
Main entry point and application state coordinator.
Tagline: "Your Hands. Your Road. Your Race."
"""

import sys
import os
import pygame

from config import (
    GAME_TITLE, WINDOW_WIDTH, WINDOW_HEIGHT, TARGET_FPS,
    SETTINGS
)
from camera.camera_manager import CameraManager
from game.game_engine import GameEngine, EngineState
from ui.dashboard import Dashboard
from ui.main_menu import MainMenu
from ui.camera_test import CameraTestScreen
from ui.calibration_screen import CalibrationScreen
from ui.how_to_play import HowToPlayScreen
from ui.settings_screen import SettingsScreen
from ui.results_screen import ResultsScreen
from utils.audio import AUDIO


class AppState:
    MAIN_MENU = "MAIN_MENU"
    RACING = "RACING"
    CAMERA_TEST = "CAMERA_TEST"
    CALIBRATION = "CALIBRATION"
    HOW_TO_PLAY = "HOW_TO_PLAY"
    SETTINGS = "SETTINGS"
    RESULTS = "RESULTS"


class GestureDriveApp:
    """Primary application controller for GestureDrive AI."""

    def __init__(self):
        # 1. Initialize Pygame Video & Audio
        pygame.init()
        pygame.display.set_caption(f"{GAME_TITLE} — Camera-Controlled Car Racing")

        flags = pygame.FULLSCREEN if SETTINGS.fullscreen else pygame.RESIZABLE
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), flags)
        self.clock = pygame.time.Clock()
        self.running = True
        self.state = AppState.MAIN_MENU

        # 2. Initialize Camera & Vision Manager
        self.camera_mgr = CameraManager(SETTINGS.camera_index)
        cam_started = self.camera_mgr.start()
        if not cam_started:
            print("[App] Warning: Camera not available on launch. Keyboard fallback enabled.")

        # 3. Initialize Game Engine & UI Screens
        self.engine = GameEngine(self.camera_mgr)
        self.dashboard = Dashboard()

        self.main_menu = MainMenu(on_action=self._handle_menu_action)
        self.camera_test = CameraTestScreen(self.camera_mgr, on_back=lambda: self._set_state(AppState.MAIN_MENU))
        self.calibration = CalibrationScreen(
            self.camera_mgr,
            on_finish=self._start_race_from_calibration,
            on_back=lambda: self._set_state(AppState.MAIN_MENU)
        )
        self.how_to_play = HowToPlayScreen(
            on_back=lambda: self._set_state(AppState.MAIN_MENU),
            on_test_cam=lambda: self._set_state(AppState.CAMERA_TEST)
        )
        self.settings_screen = SettingsScreen(
            on_back=lambda: self._set_state(AppState.MAIN_MENU),
            on_toggle_fullscreen=self._toggle_fullscreen
        )
        self.results_screen = ResultsScreen(
            on_restart=self._start_race,
            on_menu=lambda: self._set_state(AppState.MAIN_MENU)
        )

        self.top_speed_achieved = 0.0

    def _set_state(self, new_state: str):
        """Transition between application screens."""
        self.state = new_state
        if new_state == AppState.CALIBRATION:
            self.calibration.reset()

    def _handle_menu_action(self, action: str):
        """Dispatch main menu actions."""
        if action == "START_RACE":
            self._start_race()
        elif action == "CAMERA_TEST":
            self._set_state(AppState.CAMERA_TEST)
        elif action == "CALIBRATION":
            self._set_state(AppState.CALIBRATION)
        elif action == "HOW_TO_PLAY":
            self._set_state(AppState.HOW_TO_PLAY)
        elif action == "SETTINGS":
            self._set_state(AppState.SETTINGS)
        elif action == "EXIT":
            self.running = False

    def _start_race(self):
        """Initiate racing session."""
        self.top_speed_achieved = 0.0
        self.engine.start_new_race()
        self._set_state(AppState.RACING)

    def _start_race_from_calibration(self):
        """Launch race directly after finishing calibration."""
        self._start_race()

    def _toggle_fullscreen(self, is_fs: bool):
        """Toggle between windowed and fullscreen display."""
        flags = pygame.FULLSCREEN if is_fs else pygame.RESIZABLE
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), flags)

    def run(self):
        """Main application game loop running at 60 FPS."""
        while self.running:
            dt = self.clock.tick(TARGET_FPS) / 1000.0
            dt = min(dt, 0.1)  # Cap large spikes

            # 1. Event Handling
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    break

                # Global Hotkeys
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_F11:
                        SETTINGS.fullscreen = not SETTINGS.fullscreen
                        self._toggle_fullscreen(SETTINGS.fullscreen)
                        SETTINGS.save()

                    # Fast menu number select
                    if self.state == AppState.MAIN_MENU:
                        if event.key == pygame.K_1:
                            self._handle_menu_action("START_RACE")
                        elif event.key == pygame.K_2:
                            self._handle_menu_action("CAMERA_TEST")
                        elif event.key == pygame.K_3:
                            self._handle_menu_action("CALIBRATION")
                        elif event.key == pygame.K_4:
                            self._handle_menu_action("HOW_TO_PLAY")
                        elif event.key == pygame.K_5:
                            self._handle_menu_action("SETTINGS")
                        elif event.key == pygame.K_6:
                            self._handle_menu_action("EXIT")

                    # In-race controls
                    elif self.state == AppState.RACING:
                        if event.key in (pygame.K_ESCAPE, pygame.K_p):
                            # Toggle Pause
                            if self.engine.state == EngineState.RACING:
                                self.engine.state = EngineState.PAUSED
                                AUDIO.stop_engine()
                            elif self.engine.state == EngineState.PAUSED:
                                self.engine.state = EngineState.RACING
                                AUDIO.start_engine()
                        elif event.key == pygame.K_r:
                            # Quick restart for expo
                            self._start_race()
                        elif event.key == pygame.K_q and self.engine.state == EngineState.PAUSED:
                            AUDIO.stop_engine()
                            self._set_state(AppState.MAIN_MENU)

                # Pass events to current screen
                if self.state == AppState.MAIN_MENU:
                    self.main_menu.handle_event(event)
                elif self.state == AppState.CAMERA_TEST:
                    self.camera_test.handle_event(event)
                elif self.state == AppState.CALIBRATION:
                    self.calibration.handle_event(event)
                elif self.state == AppState.HOW_TO_PLAY:
                    self.how_to_play.handle_event(event)
                elif self.state == AppState.SETTINGS:
                    self.settings_screen.handle_event(event)
                elif self.state == AppState.RESULTS:
                    self.results_screen.handle_event(event)

            # 2. State Update
            if self.state == AppState.MAIN_MENU:
                self.main_menu.update(dt)
            elif self.state == AppState.CAMERA_TEST:
                self.camera_test.update(dt)
            elif self.state == AppState.CALIBRATION:
                self.calibration.update(dt)
            elif self.state == AppState.HOW_TO_PLAY:
                self.how_to_play.update(dt)
            elif self.state == AppState.SETTINGS:
                self.settings_screen.update(dt)
            elif self.state == AppState.RESULTS:
                self.results_screen.update(dt)
            elif self.state == AppState.RACING:
                res = self.engine.update(dt)
                if self.engine.car.speed > self.top_speed_achieved:
                    self.top_speed_achieved = self.engine.car.speed
                if res == "RESULTS":
                    self._set_state(AppState.RESULTS)

            # 3. State Rendering
            if self.state == AppState.MAIN_MENU:
                self.main_menu.draw(self.screen, self.camera_mgr.is_connected)
            elif self.state == AppState.CAMERA_TEST:
                self.camera_test.draw(self.screen)
            elif self.state == AppState.CALIBRATION:
                self.calibration.draw(self.screen)
            elif self.state == AppState.HOW_TO_PLAY:
                self.how_to_play.draw(self.screen)
            elif self.state == AppState.SETTINGS:
                self.settings_screen.draw(self.screen)
            elif self.state == AppState.RESULTS:
                self.results_screen.draw(self.screen, self.engine.scoring, self.top_speed_achieved)
            elif self.state == AppState.RACING:
                # Render 3D world
                self.engine.render(self.screen)
                # Render HUD dashboard overlay
                gesture_state = self.camera_mgr.get_state()
                preview_surf = self.camera_mgr.get_preview_surface()
                self.dashboard.draw(
                    surface=self.screen,
                    speed_kmh=self.engine.car.speed,
                    score=self.engine.scoring.score,
                    high_score=self.engine.scoring.high_score,
                    distance_str=self.engine.scoring.get_formatted_distance(),
                    race_time_str=self.engine.scoring.get_formatted_time(),
                    multiplier=self.engine.scoring.speed_multiplier,
                    lives=self.engine.lives,
                    gesture_state=gesture_state,
                    camera_surface=preview_surf,
                    is_camera_connected=self.camera_mgr.is_connected,
                    is_paused=(self.engine.state == EngineState.PAUSED)
                )

            pygame.display.flip()

        # Clean Exit
        self._cleanup()

    def _cleanup(self):
        """Release camera and audio resources gracefully."""
        print("[App] Shutting down GestureDrive AI...")
        AUDIO.stop_engine()
        self.camera_mgr.release()
        pygame.quit()
        sys.exit(0)


def main():
    """Application launcher."""
    app = GestureDriveApp()
    app.run()


if __name__ == "__main__":
    main()
