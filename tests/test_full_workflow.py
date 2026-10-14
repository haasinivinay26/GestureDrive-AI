"""
Integration lifecycle test for complete GestureDrive AI session:
Verifies:
1. Starting gesture triggers race transition exactly once
2. Holding starting gesture does not repeatedly restart or retrigger
3. Returning to menu resets start detection properly
4. Thumbs-up activates acceleration in race
5. Releasing thumbs-up returns to coasting
6. Open-palm braking overrides acceleration
7. Calibrated neutral steering produces zero lateral movement (no drift)
8. Left and right steering work in correct directions
9. Lost tracking safely returns steering to zero and releases stuck controls
"""

import os
os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'

import pygame
import pytest
from main import GestureDriveApp, AppState
from camera.gesture_recognizer import GestureState
from tests.test_gestures import create_synthetic_hand


def test_full_gesture_lifecycle_workflow():
    app = GestureDriveApp()
    assert app.state == AppState.MAIN_MENU

    # --- 1. Test Starting Gesture Triggers Race Exactly Once ---
    h_victory = create_synthetic_hand(wrist=(0.5, 0.6, 0.0), is_victory=True)

    # Feed victory gesture into recognizer
    for _ in range(5):
        st = app.camera_mgr.recognizer.process([h_victory])
    assert st.is_start_gesture is True

    # Advance main menu update loop until hold timer completes
    triggered = False
    for _ in range(25):
        if app.main_menu.update(0.05, is_start_gesture_active=True):
            triggered = True
            break

    assert triggered is True
    assert app.state == AppState.RACING

    # --- 2. Hold Starting Gesture: verify race does NOT retrigger or restart ---
    race_start_time = app.engine.scoring.race_time
    for _ in range(30):
        # Even if victory gesture remains active, menu update won't fire because state is RACING and consumed=True
        app.main_menu.update(0.05, is_start_gesture_active=True)
    assert app.state == AppState.RACING

    # --- 3. Return to Menu and re-arm Start Gesture ---
    app._set_state(AppState.MAIN_MENU)
    assert app.state == AppState.MAIN_MENU
    assert app.start_gesture_consumed is False
    assert app.main_menu.start_triggered is False

    # Start race again via gesture
    triggered_again = False
    for _ in range(25):
        if app.main_menu.update(0.05, is_start_gesture_active=True):
            triggered_again = True
            break
    assert triggered_again is True
    assert app.state == AppState.RACING

    # Switch engine state to RACING (past countdown)
    app.engine.state = "RACING"

    # --- 4. Test Thumbs-up Acceleration in active gameplay ---
    initial_speed = app.engine.car.speed
    h_thumbs = create_synthetic_hand(wrist=(0.5, 0.6, 0.0), is_thumbs_up=True)

    # Simulate camera manager reading thumbs up
    for _ in range(10):
        g_st = app.camera_mgr.recognizer.process([h_thumbs])
        app.camera_mgr.current_state = g_st

    # Run engine updates with active throttle
    for _ in range(10):
        app.engine.update(0.1)

    assert app.engine.car.speed > initial_speed
    accel_speed = app.engine.car.speed

    # --- 5. Release Thumbs-up: verify natural coasting / deceleration ---
    h_neutral = create_synthetic_hand(wrist=(0.5, 0.6, 0.0))
    for _ in range(10):
        g_st = app.camera_mgr.recognizer.process([h_neutral])
        app.camera_mgr.current_state = g_st

    for _ in range(10):
        app.engine.update(0.1)

    assert app.engine.car.speed < accel_speed

    # --- 6. Open Palm Braking Overrides Acceleration ---
    h_palm = create_synthetic_hand(wrist=(0.5, 0.6, 0.0), is_open_palm=True)
    # Simulate both hands: one thumbs up, one open palm
    for _ in range(10):
        g_st = app.camera_mgr.recognizer.process([h_thumbs, h_palm])
        app.camera_mgr.current_state = g_st

    assert g_st.is_braking is True
    assert g_st.is_accelerating is False

    speed_before_brake = app.engine.car.speed
    for _ in range(5):
        app.engine.update(0.1)
    assert app.engine.car.speed < speed_before_brake

    # --- 7. Neutral Steering Calibration & Zero Lateral Drift ---
    h_left = create_synthetic_hand(wrist=(0.35, 0.50, 0.0), is_left=True)
    h_right = create_synthetic_hand(wrist=(0.65, 0.50, 0.0), is_left=False)

    app.camera_mgr.recognizer.calibrate_center([h_left, h_right])
    for _ in range(15):
        g_st = app.camera_mgr.recognizer.process([h_left, h_right])
        app.camera_mgr.current_state = g_st

    assert abs(g_st.steer_angle) < 0.015
    assert g_st.steer_direction == "CENTER"

    # Car lateral position must not drift over time
    app.engine.car.x = 0.0
    app.engine.car.speed = 100.0
    for _ in range(20):
        app.engine.update(0.1)
    assert app.engine.car.x == 0.0

    # --- 8. Steer Left & Right in Correct Directions ---
    # Left turn
    h_l_down = create_synthetic_hand(wrist=(0.30, 0.65, 0.0), is_left=True)
    h_r_up = create_synthetic_hand(wrist=(0.60, 0.35, 0.0), is_left=False)
    for _ in range(15):
        g_st = app.camera_mgr.recognizer.process([h_l_down, h_r_up])
        app.camera_mgr.current_state = g_st

    assert g_st.steer_angle < -0.20
    assert g_st.steer_direction == "LEFT"

    for _ in range(5):
        app.engine.update(0.1)
    assert app.engine.car.x < 0.0

    # Right turn
    h_l_up = create_synthetic_hand(wrist=(0.35, 0.35, 0.0), is_left=True)
    h_r_down = create_synthetic_hand(wrist=(0.65, 0.65, 0.0), is_left=False)
    for _ in range(15):
        g_st = app.camera_mgr.recognizer.process([h_l_up, h_r_down])
        app.camera_mgr.current_state = g_st

    assert g_st.steer_angle > 0.20
    assert g_st.steer_direction == "RIGHT"

    for _ in range(15):
        app.engine.update(0.1)
    assert app.engine.car.x > 0.0

    # --- 9. Missing Hands Safe Behavior ---
    for _ in range(20):
        g_st = app.camera_mgr.recognizer.process([])
        app.camera_mgr.current_state = g_st

    assert abs(g_st.steer_angle) < 0.015
    assert g_st.is_accelerating is False
    assert g_st.is_braking is False

    # Cleanup
    app.camera_mgr.release()
    pygame.quit()
