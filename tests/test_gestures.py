"""
Unit tests for GestureRecognizer and Hand Data structures.
Tests synthetic hand landmark sets for:
- Two-hand steering calculation (left, right, neutral)
- Neutral center calibration and deadzone straight driving
- Thumbs-up acceleration activation and prompt release
- Fist and pointing non-activation (no false positives)
- Open-palm braking recognition
- Priority rule (Braking strictly overrides acceleration)
- Starting gesture detection (✌️ Victory sign & wheel ready)
- Missing hand decay
"""

import math
import pytest
from camera.hand_tracker import HandData
from camera.gesture_recognizer import GestureRecognizer, GestureState
from config import SETTINGS


def create_synthetic_hand(
    wrist=(0.5, 0.7, 0.0),
    is_thumbs_up=False,
    is_open_palm=False,
    is_victory=False,
    is_fist=False,
    is_pointing=False,
    is_left=False
) -> HandData:
    """Create an anatomically scaled 21-landmark synthetic hand."""
    wx, wy, wz = wrist
    landmarks = [(wx, wy, wz)] * 21
    # Middle MCP (landmark 9) establishes palm scale: hand_scale ~ 0.20
    landmarks[9] = (wx, wy - 0.20, wz)

    if is_thumbs_up:
        # Thumb pointing up (y decreases upwards)
        landmarks[1] = (wx - 0.04, wy - 0.05, 0.0)  # CMC
        landmarks[2] = (wx - 0.06, wy - 0.10, 0.0)  # MCP
        landmarks[3] = (wx - 0.05, wy - 0.17, 0.0)  # IP
        landmarks[4] = (wx - 0.04, wy - 0.25, 0.0)  # TIP (high up above index MCP)

        # Other 4 fingers curled into fist (tips close to wrist/below MCP)
        for base, tip in [(5, 8), (9, 12), (13, 16), (17, 20)]:
            x_off = (base // 4 - 2) * 0.03
            landmarks[base] = (wx + x_off, wy - 0.16, 0.0)     # MCP
            landmarks[base + 1] = (wx + x_off, wy - 0.12, 0.0) # PIP
            landmarks[base + 2] = (wx + x_off, wy - 0.08, 0.0) # DIP
            landmarks[tip] = (wx + x_off, wy - 0.05, 0.0)      # TIP curled near wrist

    elif is_open_palm:
        # Thumb
        landmarks[1] = (wx - 0.05, wy - 0.06, 0.0)
        landmarks[2] = (wx - 0.09, wy - 0.12, 0.0)
        landmarks[3] = (wx - 0.12, wy - 0.18, 0.0)
        landmarks[4] = (wx - 0.15, wy - 0.24, 0.0)

        # Index, Middle, Ring, Pinky extended high
        for i, (base, tip) in enumerate([(5, 8), (9, 12), (13, 16), (17, 20)]):
            x_offset = (i - 1.5) * 0.04
            landmarks[base] = (wx + x_offset, wy - 0.14, 0.0)
            landmarks[base + 1] = (wx + x_offset, wy - 0.20, 0.0)
            landmarks[base + 2] = (wx + x_offset, wy - 0.26, 0.0)
            landmarks[tip] = (wx + x_offset, wy - 0.32, 0.0)

    elif is_victory:
        # Index and Middle extended in V
        # Thumb folded
        landmarks[2] = (wx - 0.05, wy - 0.08, 0.0)
        landmarks[4] = (wx - 0.02, wy - 0.10, 0.0)  # Thumb tip folded

        # Index extended left
        landmarks[5] = (wx - 0.04, wy - 0.14, 0.0)
        landmarks[6] = (wx - 0.05, wy - 0.20, 0.0)
        landmarks[8] = (wx - 0.06, wy - 0.32, 0.0)

        # Middle extended right
        landmarks[9] = (wx + 0.02, wy - 0.14, 0.0)
        landmarks[10] = (wx + 0.03, wy - 0.20, 0.0)
        landmarks[12] = (wx + 0.04, wy - 0.32, 0.0)

        # Ring & Pinky curled
        landmarks[13] = (wx + 0.06, wy - 0.13, 0.0)
        landmarks[14] = (wx + 0.06, wy - 0.10, 0.0)
        landmarks[16] = (wx + 0.06, wy - 0.05, 0.0)

        landmarks[17] = (wx + 0.09, wy - 0.12, 0.0)
        landmarks[18] = (wx + 0.09, wy - 0.09, 0.0)
        landmarks[20] = (wx + 0.09, wy - 0.05, 0.0)

    elif is_pointing:
        # Index extended, but thumb and other fingers folded
        landmarks[4] = (wx - 0.02, wy - 0.08, 0.0)  # Thumb folded
        landmarks[5] = (wx, wy - 0.14, 0.0)
        landmarks[6] = (wx, wy - 0.20, 0.0)
        landmarks[8] = (wx, wy - 0.32, 0.0)  # Index extended

        for base, tip in [(9, 12), (13, 16), (17, 20)]:
            landmarks[base] = (wx + 0.04, wy - 0.14, 0.0)
            landmarks[base + 1] = (wx + 0.04, wy - 0.10, 0.0)
            landmarks[tip] = (wx + 0.04, wy - 0.05, 0.0)

    elif is_fist:
        # All fingers folded including thumb
        landmarks[4] = (wx - 0.02, wy - 0.08, 0.0)  # Thumb folded
        for base, tip in [(5, 8), (9, 12), (13, 16), (17, 20)]:
            landmarks[base] = (wx + 0.03, wy - 0.14, 0.0)
            landmarks[base + 1] = (wx + 0.03, wy - 0.10, 0.0)
            landmarks[tip] = (wx + 0.03, wy - 0.05, 0.0)

    else:
        # Neutral resting hand
        for i in range(1, 21):
            landmarks[i] = (wx, wy - 0.01 * i, 0.0)

    label = "Left" if is_left else "Right"
    return HandData(label=label, landmarks=landmarks, raw_landmarks=None)


def test_steering_neutral_with_calibration():
    """Calibrating center zeros out any natural posture asymmetry."""
    recognizer = GestureRecognizer()
    SETTINGS.neutral_tilt_deg = 0.0
    SETTINGS.neutral_mid_x = 0.50

    # User sits slightly off-center (mid_x = 0.54, tilt = 2.5 deg)
    h_left = create_synthetic_hand(wrist=(0.38, 0.51, 0.0), is_left=True)
    h_right = create_synthetic_hand(wrist=(0.70, 0.49, 0.0), is_left=False)

    # Calibrate center
    success = recognizer.calibrate_center([h_left, h_right])
    assert success is True
    assert SETTINGS.neutral_mid_x > 0.50

    # Now evaluate steering with calibrated center
    for _ in range(15):
        state = recognizer.process([h_left, h_right])

    assert abs(state.steer_angle) < 0.03
    assert state.steer_direction == "CENTER"


def test_steering_left():
    """Left hand lower / right hand higher rotates wheel left (steer < 0)."""
    recognizer = GestureRecognizer()
    SETTINGS.neutral_tilt_deg = 0.0
    SETTINGS.neutral_mid_x = 0.50

    h_left = create_synthetic_hand(wrist=(0.30, 0.65, 0.0), is_left=True)
    h_right = create_synthetic_hand(wrist=(0.60, 0.35, 0.0), is_left=False)

    for _ in range(15):
        state = recognizer.process([h_left, h_right])

    assert state.steer_angle < -0.30
    assert state.steer_direction == "LEFT"


def test_steering_right():
    """Right hand lower / left hand higher rotates wheel right (steer > 0)."""
    recognizer = GestureRecognizer()
    SETTINGS.neutral_tilt_deg = 0.0
    SETTINGS.neutral_mid_x = 0.50

    h_left = create_synthetic_hand(wrist=(0.35, 0.35, 0.0), is_left=True)
    h_right = create_synthetic_hand(wrist=(0.65, 0.65, 0.0), is_left=False)

    for _ in range(15):
        state = recognizer.process([h_left, h_right])

    assert state.steer_angle > 0.30
    assert state.steer_direction == "RIGHT"


def test_thumbs_up_acceleration_and_release():
    """Thumbs up triggers acceleration, releasing deactivates promptly."""
    recognizer = GestureRecognizer()
    h_thumbs = create_synthetic_hand(wrist=(0.5, 0.6, 0.0), is_thumbs_up=True)

    # Show thumbs-up
    for _ in range(5):
        state = recognizer.process([h_thumbs])

    assert state.is_accelerating is True
    assert "ACCEL" in state.active_gesture
    assert state.accel_status == "ACCELERATING"

    # Release thumbs-up (neutral hand)
    h_neutral = create_synthetic_hand(wrist=(0.5, 0.6, 0.0))
    for _ in range(5):
        state = recognizer.process([h_neutral])

    assert state.is_accelerating is False
    assert state.accel_status == "NO ACCELERATION"


def test_fist_and_pointing_do_not_accelerate():
    """A closed fist or pointing gesture must NOT trigger acceleration."""
    recognizer = GestureRecognizer()

    # Closed fist
    h_fist = create_synthetic_hand(wrist=(0.5, 0.6, 0.0), is_fist=True)
    for _ in range(5):
        state = recognizer.process([h_fist])
    assert state.is_accelerating is False

    # Pointing finger
    h_point = create_synthetic_hand(wrist=(0.5, 0.6, 0.0), is_pointing=True)
    for _ in range(5):
        state = recognizer.process([h_point])
    assert state.is_accelerating is False


def test_open_palm_braking():
    """An open-palm hand triggers braking."""
    recognizer = GestureRecognizer()
    h_palm = create_synthetic_hand(wrist=(0.5, 0.6, 0.0), is_open_palm=True)

    for _ in range(5):
        state = recognizer.process([h_palm])

    assert state.is_braking is True
    assert state.is_accelerating is False
    assert state.brake_status == "BRAKING"


def test_braking_overrides_acceleration():
    """If one hand shows open-palm and one shows thumbs-up, BRAKE MUST WIN!"""
    recognizer = GestureRecognizer()
    h_thumbs = create_synthetic_hand(wrist=(0.3, 0.6, 0.0), is_thumbs_up=True, is_left=True)
    h_palm = create_synthetic_hand(wrist=(0.7, 0.6, 0.0), is_open_palm=True, is_left=False)

    for _ in range(5):
        state = recognizer.process([h_thumbs, h_palm])

    assert state.is_braking is True
    assert state.is_accelerating is False
    assert "BRAKE" in state.active_gesture


def test_victory_starting_gesture():
    """Victory sign (✌️) activates starting gesture without triggering accelerator."""
    recognizer = GestureRecognizer()
    h_victory = create_synthetic_hand(wrist=(0.5, 0.6, 0.0), is_victory=True)

    for _ in range(5):
        state = recognizer.process([h_victory])

    assert state.is_start_gesture is True
    assert state.is_accelerating is False  # Must NOT accelerate!
    assert state.is_braking is False

    # Hold for 20 frames to achieve accepted status
    for _ in range(20):
        state = recognizer.process([h_victory])

    assert state.start_status == "ACCEPTED"


def test_missing_hands_returns_to_neutral():
    """When tracking is lost, steering angle smoothly returns to 0 and accel/brake cease."""
    recognizer = GestureRecognizer()
    h_left = create_synthetic_hand(wrist=(0.3, 0.7, 0.0), is_left=True)
    h_right = create_synthetic_hand(wrist=(0.6, 0.3, 0.0), is_left=False)
    for _ in range(10):
        recognizer.process([h_left, h_right])

    # Lose hands
    for _ in range(20):
        state = recognizer.process([])

    assert abs(state.steer_angle) < 0.01
    assert state.steer_direction == "CENTER"
    assert state.is_accelerating is False
    assert state.is_braking is False
    assert state.hands_detected == 0
