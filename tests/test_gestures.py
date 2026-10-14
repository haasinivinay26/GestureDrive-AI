"""
Unit tests for GestureRecognizer and Hand Data structures.
Tests synthetic hand landmark sets for:
- Two-hand steering calculation
- Thumbs-up acceleration recognition
- Open-palm braking recognition
- Priority rule (Braking strictly overrides acceleration)
- Missing hand decay
"""

import math
import pytest
from camera.hand_tracker import HandData
from camera.gesture_recognizer import GestureRecognizer, GestureState


def create_synthetic_hand(wrist=(0.5, 0.7, 0.0), is_thumbs_up=False, is_open_palm=False, is_left=False) -> HandData:
    """Create a 21-landmark synthetic hand."""
    wx, wy, wz = wrist
    landmarks = [(wx, wy, wz)] * 21

    if is_thumbs_up:
        # Thumb pointing up (y decreases upwards)
        landmarks[1] = (wx - 0.03, wy - 0.05, 0.0)  # CMC
        landmarks[2] = (wx - 0.04, wy - 0.10, 0.0)  # MCP
        landmarks[3] = (wx - 0.03, wy - 0.16, 0.0)  # IP
        landmarks[4] = (wx - 0.02, wy - 0.22, 0.0)  # TIP (high up)

        # Other 4 fingers curled into fist (tips close to wrist/below PIP)
        for base, tip in [(5, 8), (9, 12), (13, 16), (17, 20)]:
            landmarks[base] = (wx + 0.02 * (base // 4), wy - 0.08, 0.0)     # MCP
            landmarks[base + 1] = (wx + 0.02 * (base // 4), wy - 0.09, 0.0) # PIP
            landmarks[base + 2] = (wx + 0.02 * (base // 4), wy - 0.07, 0.0) # DIP
            landmarks[tip] = (wx + 0.02 * (base // 4), wy - 0.05, 0.0)      # TIP curled near wrist

    elif is_open_palm:
        # All fingers extended upward away from wrist
        # Thumb
        landmarks[1] = (wx - 0.05, wy - 0.06, 0.0)
        landmarks[2] = (wx - 0.08, wy - 0.11, 0.0)
        landmarks[3] = (wx - 0.10, wy - 0.16, 0.0)
        landmarks[4] = (wx - 0.12, wy - 0.22, 0.0)

        # Index, Middle, Ring, Pinky extended
        for i, (base, tip) in enumerate([(5, 8), (9, 12), (13, 16), (17, 20)]):
            x_offset = (i - 1.5) * 0.04
            landmarks[base] = (wx + x_offset, wy - 0.08, 0.0)
            landmarks[base + 1] = (wx + x_offset, wy - 0.14, 0.0)
            landmarks[base + 2] = (wx + x_offset, wy - 0.20, 0.0)
            landmarks[tip] = (wx + x_offset, wy - 0.26, 0.0)  # Extended high

    else:
        # Neutral resting hand
        for i in range(1, 21):
            landmarks[i] = (wx, wy - 0.01 * i, 0.0)

    label = "Left" if is_left else "Right"
    return HandData(label=label, landmarks=landmarks, raw_landmarks=None)


def test_steering_neutral():
    """Two level hands should produce roughly neutral steering (near 0.0)."""
    recognizer = GestureRecognizer()
    # Left hand at x=0.35, y=0.5; Right hand at x=0.65, y=0.5
    h_left = create_synthetic_hand(wrist=(0.35, 0.5, 0.0), is_left=True)
    h_right = create_synthetic_hand(wrist=(0.65, 0.5, 0.0), is_left=False)

    # Feed multiple frames to settle EMA smoothing
    for _ in range(10):
        state = recognizer.process([h_left, h_right])

    assert abs(state.steer_angle) < 0.15
    assert state.hands_detected == 2


def test_steering_left():
    """Left hand lower / right hand higher rotates wheel left (steer < 0)."""
    recognizer = GestureRecognizer()
    # Turning left: left hand down (y increases), right hand up (y decreases)
    h_left = create_synthetic_hand(wrist=(0.30, 0.65, 0.0), is_left=True)
    h_right = create_synthetic_hand(wrist=(0.60, 0.35, 0.0), is_left=False)

    for _ in range(15):
        state = recognizer.process([h_left, h_right])

    assert state.steer_angle < -0.30
    assert state.wheel_tilt_degrees < -10.0


def test_steering_right():
    """Right hand lower / left hand higher rotates wheel right (steer > 0)."""
    recognizer = GestureRecognizer()
    # Turning right: right hand down (y increases), left hand up (y decreases)
    h_left = create_synthetic_hand(wrist=(0.35, 0.35, 0.0), is_left=True)
    h_right = create_synthetic_hand(wrist=(0.65, 0.65, 0.0), is_left=False)

    for _ in range(15):
        state = recognizer.process([h_left, h_right])

    assert state.steer_angle > 0.30
    assert state.wheel_tilt_degrees > 10.0


def test_thumbs_up_acceleration():
    """A thumbs-up hand triggers acceleration."""
    recognizer = GestureRecognizer()
    h_thumbs = create_synthetic_hand(wrist=(0.5, 0.6, 0.0), is_thumbs_up=True)

    for _ in range(5):
        state = recognizer.process([h_thumbs])

    assert state.is_accelerating is True
    assert state.is_braking is False
    assert "ACCEL" in state.active_gesture


def test_open_palm_braking():
    """An open-palm hand triggers braking."""
    recognizer = GestureRecognizer()
    h_palm = create_synthetic_hand(wrist=(0.5, 0.6, 0.0), is_open_palm=True)

    for _ in range(5):
        state = recognizer.process([h_palm])

    assert state.is_braking is True
    assert state.is_accelerating is False
    assert "BRAKE" in state.active_gesture


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


def test_missing_hands_returns_to_neutral():
    """When tracking is lost, steering angle smoothly returns to 0 and accel/brake cease."""
    recognizer = GestureRecognizer()
    h_left = create_synthetic_hand(wrist=(0.3, 0.7, 0.0), is_left=True)
    h_right = create_synthetic_hand(wrist=(0.6, 0.3, 0.0), is_left=False)
    for _ in range(10):
        recognizer.process([h_left, h_right])

    # Lose hands
    for _ in range(25):
        state = recognizer.process([])

    assert abs(state.steer_angle) < 0.05
    assert state.is_accelerating is False
    assert state.is_braking is False
    assert state.hands_detected == 0
