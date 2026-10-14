"""
Gesture recognition engine for GestureDrive AI.
Recognizes:
- Steering wheel angle and horizontal lateral shift using two hands (or single-hand assist).
- Thumbs-up gesture for smooth acceleration.
- Open-palm gesture for immediate braking.
Enforces priority (Braking > Acceleration), debounce smoothing, and confidence thresholds.
"""

import math
from collections import deque
from dataclasses import dataclass
from typing import List, Tuple, Optional
from config import SETTINGS, STEERING_DEADZONE, STEERING_SMOOTHING_ALPHA, GESTURE_CONFIRM_FRAMES
from utils.helpers import clamp


@dataclass
class GestureState:
    """Consolidated state emitted by gesture recognizer."""
    steer_angle: float = 0.0          # Normalized -1.0 (full left) to +1.0 (full right)
    raw_steer: float = 0.0            # Unsmoothed steer angle
    is_accelerating: bool = False     # True if Thumbs-Up recognized
    is_braking: bool = False          # True if Open-Palm recognized
    active_gesture: str = "NEUTRAL"   # "NEUTRAL", "STEERING", "THUMBS_UP", "OPEN_PALM"
    confidence: float = 0.0           # Estimated detection confidence
    hands_detected: int = 0           # Count of hands currently tracked
    wheel_tilt_degrees: float = 0.0   # Physical wheel tilt angle in degrees for UI gauge


class GestureRecognizer:
    """Processes tracked hand landmarks into high-fidelity driving commands."""

    def __init__(self):
        self.smoothed_steer = 0.0
        self.last_gesture_history = deque(maxlen=GESTURE_CONFIRM_FRAMES)
        self.consecutive_frames_lost = 0

    def reset(self):
        """Reset internal smoothing states."""
        self.smoothed_steer = 0.0
        self.last_gesture_history.clear()
        self.consecutive_frames_lost = 0

    def process(self, hands_data: list) -> GestureState:
        """
        Evaluate hand landmarks and return a GestureState.
        hands_data: list of HandData objects.
        """
        num_hands = len(hands_data)

        if num_hands == 0:
            self.consecutive_frames_lost += 1
            # Return smoothly to center when hands are lost
            self.smoothed_steer *= 0.85
            if abs(self.smoothed_steer) < 0.01:
                self.smoothed_steer = 0.0
            self.last_gesture_history.append("NEUTRAL")
            return GestureState(
                steer_angle=self.smoothed_steer,
                raw_steer=0.0,
                is_accelerating=False,
                is_braking=False,
                active_gesture="NO HANDS",
                confidence=0.0,
                hands_detected=0,
                wheel_tilt_degrees=0.0
            )

        self.consecutive_frames_lost = 0

        # 1. Analyze Steering (Two Hands or One Hand)
        raw_steer, tilt_deg = self._compute_steering(hands_data)

        # Apply deadzone
        if abs(raw_steer) < STEERING_DEADZONE:
            raw_steer = 0.0

        # Apply sensitivity setting
        raw_steer = clamp(raw_steer * SETTINGS.steering_sensitivity, -1.0, 1.0)

        # Exponential moving average smoothing
        alpha = STEERING_SMOOTHING_ALPHA
        self.smoothed_steer = alpha * raw_steer + (1.0 - alpha) * self.smoothed_steer
        steer_value = clamp(self.smoothed_steer, -1.0, 1.0)

        # 2. Analyze Discrete Gestures: Thumbs-Up (Accel) and Open-Palm (Brake)
        has_brake = any(self._is_open_palm(h.landmarks) for h in hands_data)
        has_accel = any(self._is_thumbs_up(h.landmarks) for h in hands_data)

        # Priority Rule: BRAKE OVERRIDES ACCELERATE unconditionally
        current_raw_gesture = "NEUTRAL"
        if has_brake:
            current_raw_gesture = "OPEN_PALM"
        elif has_accel:
            current_raw_gesture = "THUMBS_UP"
        elif num_hands >= 2:
            current_raw_gesture = "STEERING"
        elif num_hands == 1:
            current_raw_gesture = "ASSIST_STEER"

        # Multi-frame confirmation (hysteresis debouncing)
        self.last_gesture_history.append(current_raw_gesture)
        confirmed_gesture = self._get_debounced_gesture(current_raw_gesture)

        is_braking = (confirmed_gesture == "OPEN_PALM")
        # Brake strictly cancels acceleration
        is_accelerating = (confirmed_gesture == "THUMBS_UP") and not is_braking

        # Formulate human-readable status banner
        if is_braking:
            display_gesture = "OPEN PALM [BRAKE]"
        elif is_accelerating:
            display_gesture = "THUMBS UP [ACCEL]"
        elif num_hands >= 2:
            display_gesture = "STEERING WHEEL"
        else:
            display_gesture = "1-HAND ASSIST"

        confidence = 0.90 if (has_brake or has_accel) else (0.80 if num_hands >= 2 else 0.65)

        return GestureState(
            steer_angle=steer_value,
            raw_steer=raw_steer,
            is_accelerating=is_accelerating,
            is_braking=is_braking,
            active_gesture=display_gesture,
            confidence=confidence,
            hands_detected=num_hands,
            wheel_tilt_degrees=tilt_deg
        )

    def _compute_steering(self, hands_data: list) -> Tuple[float, float]:
        """Compute steering from hands orientation."""
        if len(hands_data) >= 2:
            # Sort hands left-to-right by wrist X coordinate
            h1, h2 = hands_data[0], hands_data[1]
            if h1.landmarks[0][0] < h2.landmarks[0][0]:
                left_hand, right_hand = h1, h2
            else:
                left_hand, right_hand = h2, h1

            # Left and right palm centers (landmark 9: Middle MCP)
            p_left = left_hand.landmarks[9]
            p_right = right_hand.landmarks[9]

            dx = p_right[0] - p_left[0]
            dy = p_right[1] - p_left[1]

            # In image coords, y increases downwards.
            # When tilting wheel left: left hand goes down (dy decreases) or right hand goes up.
            # Angle in radians:
            angle_rad = math.atan2(dy, max(0.01, dx))
            tilt_deg = math.degrees(angle_rad)

            # Max steering tilt: ~35 degrees
            max_tilt_rad = math.radians(35.0)
            steer_tilt = clamp(angle_rad / max_tilt_rad, -1.0, 1.0)

            # Midpoint lateral shift (moving both hands across screen)
            mid_x = (p_left[0] + p_right[0]) * 0.5
            steer_shift = clamp((mid_x - 0.5) / 0.22, -1.0, 1.0)

            # Blend tilt (primary 75%) and shift (secondary 25%)
            raw_steer = 0.75 * steer_tilt + 0.25 * steer_shift
            return clamp(raw_steer, -1.0, 1.0), tilt_deg

        else:
            # Single-hand fallback
            hand = hands_data[0]
            palm_x = hand.landmarks[9][0]
            steer = clamp((palm_x - 0.5) / 0.25, -1.0, 1.0)
            return steer, steer * 30.0

    def _is_thumbs_up(self, lms: List[Tuple[float, float, float]]) -> bool:
        """
        Check if hand is forming a Thumbs-Up gesture.
        Condition:
        1. Thumb is pointing UP (tip significantly above thumb MCP and wrist).
        2. Four fingers (Index, Middle, Ring, Pinky) are curled closed into fist.
        """
        wrist = lms[0]
        thumb_tip = lms[4]
        thumb_ip = lms[3]
        thumb_mcp = lms[2]

        # Thumb pointing up in image space (y decreases upwards)
        thumb_is_up = (thumb_tip[1] < thumb_ip[1] < thumb_mcp[1]) and (wrist[1] - thumb_tip[1] > 0.12)
        # Thumb shouldn't be tilted too far horizontally
        thumb_vertical = abs(thumb_tip[0] - thumb_mcp[0]) < 1.3 * abs(thumb_mcp[1] - thumb_tip[1])

        if not (thumb_is_up and thumb_vertical):
            return False

        # Check that other 4 fingers are curled
        curled_count = 0
        finger_indices = [
            (8, 6),    # Index (tip, pip)
            (12, 10),  # Middle
            (16, 14),  # Ring
            (20, 18)   # Pinky
        ]

        for tip_idx, pip_idx in finger_indices:
            tip = lms[tip_idx]
            pip = lms[pip_idx]
            # Finger is curled if tip is below or near its pip joint
            dist_wrist_tip = math.dist((wrist[0], wrist[1]), (tip[0], tip[1]))
            dist_wrist_pip = math.dist((wrist[0], wrist[1]), (pip[0], pip[1]))
            if (tip[1] >= pip[1] - 0.02) or (dist_wrist_tip < 1.15 * dist_wrist_pip):
                curled_count += 1

        return curled_count >= 3

    def _is_open_palm(self, lms: List[Tuple[float, float, float]]) -> bool:
        """
        Check if hand is displaying an Open Palm gesture (Brake command).
        Condition:
        All 5 fingers extended outward, tips far from wrist.
        """
        wrist = lms[0]
        palm_center = lms[9]

        extended_count = 0
        finger_indices = [
            (8, 6),    # Index
            (12, 10),  # Middle
            (16, 14),  # Ring
            (20, 18)   # Pinky
        ]

        for tip_idx, pip_idx in finger_indices:
            tip = lms[tip_idx]
            pip = lms[pip_idx]
            dist_wrist_tip = math.dist((wrist[0], wrist[1]), (tip[0], tip[1]))
            dist_wrist_pip = math.dist((wrist[0], wrist[1]), (pip[0], pip[1]))
            # In an extended finger, tip must be distinctly further from wrist than pip
            if dist_wrist_tip > 1.28 * dist_wrist_pip and (tip[1] < pip[1] + 0.04):
                extended_count += 1

        # Check thumb extension
        thumb_tip = lms[4]
        thumb_mcp = lms[2]
        dist_wrist_thumb = math.dist((wrist[0], wrist[1]), (thumb_tip[0], thumb_tip[1]))
        dist_wrist_mcp = math.dist((wrist[0], wrist[1]), (thumb_mcp[0], thumb_mcp[1]))
        thumb_extended = dist_wrist_thumb > 1.20 * dist_wrist_mcp

        return (extended_count >= 4) and thumb_extended

    def _get_debounced_gesture(self, current: str) -> str:
        """Apply majority voting across the recent frames buffer."""
        if not self.last_gesture_history:
            return current
        counts = {}
        for g in self.last_gesture_history:
            counts[g] = counts.get(g, 0) + 1
        most_common = max(counts, key=counts.get)
        # If the most common gesture appears in at least half of the buffer, accept it
        if counts[most_common] >= len(self.last_gesture_history) // 2:
            return most_common
        return current
