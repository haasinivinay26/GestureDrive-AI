"""
Comprehensive UI/UX Regression and Rendering Test Suite for GestureDrive AI.
Verifies that all redesigned screens, HUD overlays, showcase supercar,
glassmorphic components, and pause modals instantiate and render without errors.
"""

import os
os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'

import pygame
import pytest
from config import WINDOW_WIDTH, WINDOW_HEIGHT, SETTINGS
from ui.components import UIButton, UISlider, UIToggle
from ui.main_menu import MainMenu
from ui.dashboard import Dashboard
from ui.how_to_play import HowToPlayScreen
from ui.settings_screen import SettingsScreen
from ui.results_screen import ResultsScreen
from camera.gesture_recognizer import GestureState
from game.scoring import ScoringSystem
from game.car import PlayerCar
from game.road import TrackManager


@pytest.fixture(scope="module", autouse=True)
def init_pygame():
    pygame.init()
    yield
    pygame.quit()


def test_ui_components_render():
    """Verify UIButton, UISlider, and UIToggle render properly onto a surface."""
    surface = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
    font = pygame.font.SysFont("Verdana", 14)

    btn = UIButton(pygame.Rect(50, 50, 200, 40), "TEST BUTTON", font, primary=True, shortcut="[1]")
    slider = UISlider(pygame.Rect(50, 120, 200, 12), 0.0, 10.0, 5.0, "Volume", font)
    toggle = UIToggle(pygame.Rect(50, 160, 200, 30), True, "Audio", font)

    btn.update(0.016, (60, 60))
    slider.draw(surface)
    toggle.draw(surface)
    btn.draw(surface)

    # Verify click handling
    clicked = []
    btn.on_click = lambda: clicked.append(True)
    btn.is_hovered = True
    ev = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(60, 60))
    assert btn.handle_event(ev) is True
    assert len(clicked) == 1


def test_main_menu_render():
    """Verify MainMenu with showcase supercar, start gesture card, and particles renders cleanly."""
    surface = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
    actions = []
    menu = MainMenu(on_action=lambda a: actions.append(a))

    # Update frame
    menu.update(0.016, is_start_gesture_active=False)

    # Draw frame
    g_state = GestureState(hands_detected=2, is_start_gesture=False, active_gesture="WHEEL READY")
    menu.draw(surface, is_camera_connected=True, gesture_state=g_state)

    # Test start gesture progression
    assert menu.start_triggered is False
    for _ in range(25):
        menu.update(0.05, is_start_gesture_active=True)
    assert menu.start_triggered is True
    assert "START_RACE" in actions

    menu.reset_start_gesture()
    assert menu.start_triggered is False


def test_dashboard_hud_render():
    """Verify in-game HUD Dashboard, stealth steering, camera PIP, and pause modal."""
    surface = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
    pause_actions = []
    dash = Dashboard(on_pause_action=lambda a: pause_actions.append(a))

    g_state = GestureState(
        steer_angle=0.35,
        steer_direction="RIGHT",
        is_accelerating=True,
        accel_status="ACCELERATING",
        is_braking=False,
        hands_detected=2
    )

    cam_mock = pygame.Surface((220, 165))

    # Active racing HUD
    dash.draw(
        surface=surface,
        speed_kmh=165.0,
        score=2450,
        high_score=8000,
        distance_str="1,240 M",
        race_time_str="01:14.2",
        multiplier=2.0,
        lives=3,
        gesture_state=g_state,
        camera_surface=cam_mock,
        is_camera_connected=True,
        is_paused=False
    )

    # Paused HUD modal
    dash.draw(
        surface=surface,
        speed_kmh=165.0,
        score=2450,
        high_score=8000,
        distance_str="1,240 M",
        race_time_str="01:14.2",
        multiplier=2.0,
        lives=3,
        gesture_state=g_state,
        camera_surface=cam_mock,
        is_camera_connected=True,
        is_paused=True
    )

    # Pause action trigger
    dash._trigger_pause("RESUME")
    assert "RESUME" in pause_actions


def test_how_to_play_screen():
    """Verify HowToPlay tutorial screen with 6 cards and architecture tab."""
    surface = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
    nav = []
    screen = HowToPlayScreen(on_back=lambda: nav.append("BACK"), on_test_cam=lambda: nav.append("CAM"))

    screen.update(0.016)
    screen.draw(surface)

    # Switch to architecture tab
    screen._set_tab(1)
    screen.draw(surface)
    assert screen.active_tab == 1


def test_settings_screen():
    """Verify Settings screen sliders, toggles, and persistence."""
    surface = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
    nav = []
    screen = SettingsScreen(on_back=lambda: nav.append("BACK"), on_toggle_fullscreen=lambda fs: None)

    screen.update(0.016)
    screen.draw(surface)

    # Toggle visual effects
    vfx_before = SETTINGS.visual_effects
    screen.toggle_vfx.state = not vfx_before
    screen.toggle_vfx.on_toggle(not vfx_before)
    assert SETTINGS.visual_effects != vfx_before
    # Restore
    SETTINGS.visual_effects = vfx_before


def test_results_screen():
    """Verify ResultsScreen with score recap and rank grading."""
    surface = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
    nav = []
    screen = ResultsScreen(on_restart=lambda: nav.append("RESTART"), on_menu=lambda: nav.append("MENU"))

    scoring = ScoringSystem()
    scoring.score = 5200
    scoring.distance_meters = 3500.0
    scoring.race_time = 145.0
    scoring.near_misses = 8
    scoring.is_new_high_score = True

    screen.update(0.016)
    screen.draw(surface, scoring, top_speed=218.0)


def test_player_car_visuals_and_streaks():
    """Verify enhanced player car with speed streaks and lightbar renders without crash."""
    surface = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
    car = PlayerCar()
    car.speed = 180.0
    car.steer_angle = 0.5
    car.update(0.016, 0.5, is_accel=True, is_brake=False, road_curve=0.0)
    car.draw(surface, is_braking=False, is_accel=True)

    # Braking draw
    car.draw(surface, is_braking=True, is_accel=False)
