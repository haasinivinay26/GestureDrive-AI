"""
Gesture recognition engine for GestureDrive AI.
Recognizes:
- Steering wheel angle and lateral shift with neutral center calibration and deadzone.
- Scale-invariant thumbs-up gesture for smooth acceleration.
- Scale-invariant open-palm gesture for immediate braking (Priority: Brake > Accel).
- Victory / Peace sign (✌️) and Dual-Hand Wheel Ready gesture to start the race.
Provides detailed debug states, consecutive frame debouncing, and direction telemetry.
"""

import math
from collections import deque
from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Dict, Any
from config import SETTINGS, STEERING_DEADZONE, STEERING_SMOOTHING_ALPHA, GESTURE_CONFIRM_FRAMES
from utils.helpers import clamp


@dataclass
class GestureState:
    """Consolidated state emitted by gesture recognizer."""
    steer_angle: float = 0.0              # Normalized -1.0 (full left) to +1.0 (full right)
    raw_steer: float = 0.0                # Unsmoothed steer angle
    steer_direction: str = "CENTER"       # "LEFT", "CENTER", "RIGHT"
    is_accelerating: bool = False         # True if Thumbs-Up recognized and confirmed
    accel_status: str = "NO ACCELERATION" # "THUMBS UP DETECTED", "ACCELERATING", "NO ACCELERATION"
    is_braking: bool = False              # True if Open-Palm recognized and confirmed
    brake_status: str = "OFF"             # "OPEN PALM DETECTED", "BRAKING", "OFF"
    is_start_gesture: bool = False        # True if Starting Gesture (Victory ✌️ or Wheel Ready) detected
    start_status: str = "NOT DETECTED"    # "START READY", "HOLDING", "ACCEPTED", "NOT DETECTED"
    active_gesture: str = "NEUTRAL"       # Human-readable tag
    confidence: float = 0.0               # Estimated detection confidence
    hands_detected: int = 0               # Count of hands currently tracked
    wheel_tilt_degrees: float = 0.0       # Physical wheel tilt angle in degrees
    calibrated_tilt: float = 0.0          # Calibrated neutral tilt angle
    calibrated_mid_x: float = 0.5         # Calibrated neutral midpoint X
    debug_info: Dict[str, Any] = field(default_factory=dict) # Diagnostic metrics for telemetry UI


class GestureRecognizer:
    """Processes tracked hand landmarks into high-fidelity driving commands."""

    def __init__(self):
        self.smoothed_steer = 0.0
        self.last_gesture_history = deque(maxlen=GESTURE_CONFIRM_FRAMES)
        self.start_gesture_frames = 0
        self.consecutive_frames_lost = 0

    def reset(self):
        """Reset internal smoothing states."""
        self.smoothed_steer = 0.0
        self.last_gesture_history.clear()
        self.start_gesture_frames = 0
        self.consecutive_frames_lost = 0

    def calibrate_center(self, hands_data: list) -> bool:
        """
        Record the current hand position as the calibrated neutral zero-point.
        Updates SETTINGS.neutral_tilt_deg and SETTINGS.neutral_mid_x.
        """
        if not hands_data:
            return False

        if len(hands_data) >= 2:
            h1, h2 = hands_data[0], hands_data[1]
            if h1.landmarks[0][0] < h2.landmarks[0][0]:
                left_hand, right_hand = h1, h2
            else:
                left_hand, right_hand = h2, h1

            p_left = left_hand.landmarks[9]
            p_right = right_hand.landmarks[9]

            dx = p_right[0] - p_left[0]
            dy = p_right[1] - p_left[1]
            angle_rad = math.atan2(dy, max(0.01, dx))
            tilt_deg = math.degrees(angle_rad)
            mid_x = (p_left[0] + p_right[0]) * 0.5

            SETTINGS.neutral_tilt_deg = round(tilt_deg, 2)
            SETTINGS.neutral_mid_x = round(mid_x, 3)
            SETTINGS.save()
            self.smoothed_steer = 0.0
            print(f"[Calibration] Calibrated neutral center: tilt={SETTINGS.neutral_tilt_deg} deg, mid_x={SETTINGS.neutral_mid_x}")
            return True
        elif len(hands_data) == 1:
            palm_x = hands_data[0].landmarks[9][0]
            SETTINGS.neutral_mid_x = round(palm_x, 3)
            SETTINGS.neutral_tilt_deg = 0.0
            SETTINGS.save()
            self.smoothed_steer = 0.0
            print(f"[Calibration] Calibrated 1-hand center: mid_x={SETTINGS.neutral_mid_x}")
            return True

        return False

    def process(self, hands_data: list) -> GestureState:
        """
        Evaluate hand landmarks and return a GestureState.
        hands_data: list of HandData objects.
        """
        num_hands = len(hands_data)
        calibrated_tilt = getattr(SETTINGS, "neutral_tilt_deg", 0.0)
        calibrated_mid_x = getattr(SETTINGS, "neutral_mid_x", 0.5)
        deadzone = getattr(SETTINGS, "steering_deadzone", STEERING_DEADZONE)

        if num_hands == 0:
            self.consecutive_frames_lost += 1
            # Return smoothly to center when hands are lost
            self.smoothed_steer *= 0.70
            if abs(self.smoothed_steer) < 0.01:
                self.smoothed_steer = 0.0
            self.last_gesture_history.append("NEUTRAL")
            self.start_gesture_frames = max(0, self.start_gesture_frames - 2)

            return GestureState(
                steer_angle=self.smoothed_steer,
                raw_steer=0.0,
                steer_direction="CENTER",
                is_accelerating=False,
                accel_status="NO ACCELERATION",
                is_braking=False,
                brake_status="OFF",
                is_start_gesture=False,
                start_status="NOT DETECTED",
                active_gesture="NO HANDS",
                confidence=0.0,
                hands_detected=0,
                wheel_tilt_degrees=0.0,
                calibrated_tilt=calibrated_tilt,
                calibrated_mid_x=calibrated_mid_x,
                debug_info={"hands": 0, "status": "Waiting for hands"}
            )

        self.consecutive_frames_lost = 0

        # 1. Analyze Steering relative to calibrated neutral reference
        raw_steer, tilt_deg, debug_steer = self._compute_steering(hands_data, calibrated_tilt, calibrated_mid_x)

        # Apply configurable central deadzone
        if abs(raw_steer) < deadzone:
            raw_steer = 0.0

        # Apply sensitivity setting
        raw_steer = clamp(raw_steer * SETTINGS.steering_sensitivity, -1.0, 1.0)

        # Exponential moving average smoothing
        alpha = STEERING_SMOOTHING_ALPHA
        self.smoothed_steer = alpha * raw_steer + (1.0 - alpha) * self.smoothed_steer

        # Strict zero snap when close to center to prevent persistent creeping
        if abs(self.smoothed_steer) < 0.015:
            self.smoothed_steer = 0.0

        steer_value = clamp(self.smoothed_steer, -1.0, 1.0)

        # Determine steering direction label
        if steer_value < -0.04:
            steer_dir = "LEFT"
        elif steer_value > 0.04:
            steer_dir = "RIGHT"
        else:
            steer_dir = "CENTER"

        # 2. Analyze Discrete Gestures with Scale-Invariant Heuristics
        has_brake, brake_diag = self._check_any_hand(hands_data, self._is_open_palm)
        has_accel, accel_diag = self._check_any_hand(hands_data, self._is_thumbs_up)
        has_start, start_diag = self._check_start_gesture(hands_data, raw_steer)

        # 3. Gesture Priority & Conflict Resolution
        # Strict Rule 1: BRAKE OVERRIDES ACCELERATE unconditionally
        current_raw_gesture = "NEUTRAL"
        if has_brake:
            current_raw_gesture = "OPEN_PALM"
        elif has_accel:
            current_raw_gesture = "THUMBS_UP"
        elif has_start:
            current_raw_gesture = "START_GESTURE"
        elif num_hands >= 2:
            current_raw_gesture = "STEERING"
        elif num_hands == 1:
            current_raw_gesture = "ASSIST_STEER"

        # Multi-frame confirmation (hysteresis debouncing)
        self.last_gesture_history.append(current_raw_gesture)
        confirmed_gesture = self._get_debounced_gesture(current_raw_gesture)

        is_braking = (confirmed_gesture == "OPEN_PALM")
        # Braking strictly cancels acceleration
        is_accelerating = (confirmed_gesture == "THUMBS_UP") and not is_braking

        # Starting gesture progression
        if has_start:
            self.start_gesture_frames += 1
        else:
            self.start_gesture_frames = max(0, self.start_gesture_frames - 2)

        is_start_active = (self.start_gesture_frames >= 2)
        if self.start_gesture_frames >= 18:
            start_status = "ACCEPTED"
        elif self.start_gesture_frames > 0:
            start_status = "START READY"
        else:
            start_status = "NOT DETECTED"

        # Status text banners
        if is_braking:
            brake_status = "BRAKING"
            accel_status = "NO ACCELERATION (BRAKE OVERRIDE)"
            display_gesture = "OPEN PALM [BRAKE]"
        elif is_accelerating:
            brake_status = "OFF"
            accel_status = "ACCELERATING"
            display_gesture = "THUMBS UP [ACCEL]"
        elif has_accel:
            accel_status = "THUMBS UP DETECTED"
            brake_status = "OFF"
            display_gesture = "THUMBS UP [DETECTED]"
        elif is_start_active:
            accel_status = "NO ACCELERATION"
            brake_status = "OFF"
            display_gesture = f"START GESTURE: {start_status}"
        elif num_hands >= 2:
            accel_status = "NO ACCELERATION"
            brake_status = "OFF"
            display_gesture = f"STEERING [{steer_dir}]"
        else:
            accel_status = "NO ACCELERATION"
            brake_status = "OFF"
            display_gesture = "1-HAND ASSIST"

        confidence = 0.95 if (has_brake or has_accel) else (0.85 if num_hands >= 2 else 0.70)

        # Consolidated debug telemetry
        debug_metrics = {
            "steer_dir": steer_dir,
            "raw_steer": round(raw_steer, 3),
            "smoothed_steer": round(steer_value, 3),
            "wheel_tilt": round(tilt_deg, 1),
            "calib_tilt": round(calibrated_tilt, 1),
            "calib_mid_x": round(calibrated_mid_x, 3),
            "brake_diag": brake_diag,
            "accel_diag": accel_diag,
            "start_diag": start_diag,
            "start_frames": self.start_gesture_frames,
        }
        debug_metrics.update(debug_steer)

        return GestureState(
            steer_angle=steer_value,
            raw_steer=raw_steer,
            steer_direction=steer_dir,
            is_accelerating=is_accelerating,
            accel_status=accel_status,
            is_braking=is_braking,
            brake_status=brake_status,
            is_start_gesture=is_start_active,
            start_status=start_status,
            active_gesture=display_gesture,
            confidence=confidence,
            hands_detected=num_hands,
            wheel_tilt_degrees=tilt_deg,
            calibrated_tilt=calibrated_tilt,
            calibrated_mid_x=calibrated_mid_x,
            debug_info=debug_metrics
        )

    def _compute_steering(self, hands_data: list, calib_tilt: float, calib_mid_x: float) -> Tuple[float, float, dict]:
        """Compute steering orientation relative to calibrated neutral reference."""
        if len(hands_data) >= 2:
            # Sort hands left-to-right by wrist X coordinate
            h1, h2 = hands_data[0], hands_data[1]
            if h1.landmarks[0][0] < h2.landmarks[0][0]:
                left_hand, right_hand = h1, h2
            else:
                left_hand, right_hand = h2, h1

            # Palm centers (landmark 9: Middle MCP)
            p_left = left_hand.landmarks[9]
            p_right = right_hand.landmarks[9]

            dx = p_right[0] - p_left[0]
            dy = p_right[1] - p_left[1]

            # In image coords, y increases downwards.
            # When tilting wheel left: left hand moves down, right hand moves up -> dy < 0.
            # Angle in degrees:
            angle_rad = math.atan2(dy, max(0.01, dx))
            raw_tilt_deg = math.degrees(angle_rad)

            # Subtract calibrated neutral tilt
            relative_tilt_deg = raw_tilt_deg - calib_tilt
            relative_tilt_rad = math.radians(relative_tilt_deg)

            # Max tilt scale (~32 degrees)
            max_tilt_rad = math.radians(32.0)
            steer_tilt = clamp(relative_tilt_rad / max_tilt_rad, -1.0, 1.0)

            # Midpoint lateral shift relative to calibrated mid_x
            mid_x = (p_left[0] + p_right[0]) * 0.5
            relative_mid_x = mid_x - calib_mid_x
            steer_shift = clamp(relative_mid_x / 0.20, -1.0, 1.0)

            # Blend: Tilt is primary (85%), lateral shift is secondary (15%)
            raw_steer = 0.85 * steer_tilt + 0.15 * steer_shift

            diag = {
                "p_left": (round(p_left[0], 2), round(p_left[1], 2)),
                "p_right": (round(p_right[0], 2), round(p_right[1], 2)),
                "rel_tilt_deg": round(relative_tilt_deg, 1),
                "rel_mid_x": round(relative_mid_x, 3),
            }
            return clamp(raw_steer, -1.0, 1.0), raw_tilt_deg, diag

        else:
            # Single-hand fallback relative to calibrated center
            hand = hands_data[0]
            palm_x = hand.landmarks[9][0]
            relative_x = palm_x - calib_mid_x
            steer = clamp(relative_x / 0.22, -1.0, 1.0)
            diag = {"single_hand_x": round(palm_x, 2), "rel_x": round(relative_x, 3)}
            return steer, steer * 30.0, diag

    def _get_hand_scale(self, lms: List[Tuple[float, float, float]]) -> float:
        """Calculate palm scale (distance from wrist to middle MCP) for scale invariance."""
        wrist = lms[0]
        middle_mcp = lms[9]
        scale = math.dist((wrist[0], wrist[1]), (middle_mcp[0], middle_mcp[1]))
        return max(0.05, scale)

    def _is_thumbs_up(self, lms: List[Tuple[float, float, float]]) -> Tuple[bool, dict]:
        """
        Robust Scale-Invariant Thumbs-Up Detector:
        1. Thumb is extended UP: thumb tip is significantly higher than thumb MCP and index MCP.
        2. Four fingers (Index, Middle, Ring, Pinky) are folded into a fist.
        3. Index finger MUST be folded (prevents false positive from pointing or victory signs).
        """
        wrist = lms[0]
        thumb_tip = lms[4]
        thumb_ip = lms[3]
        thumb_mcp = lms[2]
        index_mcp = lms[5]

        hand_scale = self._get_hand_scale(lms)

        # 1. Thumb is pointing upward:
        # Thumb tip is vertically above thumb MCP and index MCP
        thumb_up_mcp = (thumb_mcp[1] - thumb_tip[1]) > (0.15 * hand_scale)
        thumb_up_index = (index_mcp[1] - thumb_tip[1]) > (0.10 * hand_scale)
        thumb_extended = math.dist((wrist[0], wrist[1]), (thumb_tip[0], thumb_tip[1])) > (1.18 * math.dist((wrist[0], wrist[1]), (thumb_mcp[0], thumb_mcp[1])))

        # Thumb angle: check thumb points predominantly vertical (|dx| <= 1.5 * |dy|)
        dy_thumb = abs(thumb_mcp[1] - thumb_tip[1])
        dx_thumb = abs(thumb_tip[0] - thumb_mcp[0])
        thumb_vertical = (dy_thumb > 0.02) and (dx_thumb < 1.6 * dy_thumb)

        is_thumb_ready = thumb_up_mcp and thumb_up_index and thumb_extended and thumb_vertical

        # 2. Check that the four long fingers are folded (tips near palm/wrist):
        finger_pairs = [
            (8, 6, 5),    # Index (tip, pip, mcp)
            (12, 10, 9),  # Middle
            (16, 14, 13), # Ring
            (20, 18, 17)  # Pinky
        ]

        folded_count = 0
        index_folded = False

        for idx, (tip_i, pip_i, mcp_i) in enumerate(finger_pairs):
            tip = lms[tip_i]
            pip = lms[pip_i]
            mcp = lms[mcp_i]

            dist_tip_wrist = math.dist((wrist[0], wrist[1]), (tip[0], tip[1]))
            dist_pip_wrist = math.dist((wrist[0], wrist[1]), (pip[0], pip[1]))

            # In a curled finger, tip is not extended far beyond pip
            is_curled = (dist_tip_wrist < dist_pip_wrist * 1.20) or (tip[1] >= mcp[1] - 0.12 * hand_scale)
            if is_curled:
                folded_count += 1
                if idx == 0:
                    index_folded = True

        # Strict requirement: Thumb must be extended UP, at least 3 of 4 fingers folded, AND index must be folded
        is_thumbs_up = is_thumb_ready and (folded_count >= 3) and index_folded

        diag = {
            "thumb_ready": is_thumb_ready,
            "folded_count": folded_count,
            "index_folded": index_folded,
            "is_thumbs_up": is_thumbs_up
        }
        return is_thumbs_up, diag

    def _is_open_palm(self, lms: List[Tuple[float, float, float]]) -> Tuple[bool, dict]:
        """
        Scale-Invariant Open Palm (Brake) Detector:
        All 5 fingers extended outward away from wrist, fingers spread.
        """
        wrist = lms[0]
        hand_scale = self._get_hand_scale(lms)

        extended_count = 0
        finger_pairs = [
            (8, 6),    # Index
            (12, 10),  # Middle
            (16, 14),  # Ring
            (20, 18)   # Pinky
        ]

        for tip_i, pip_i in finger_pairs:
            tip = lms[tip_i]
            pip = lms[pip_i]
            dist_tip = math.dist((wrist[0], wrist[1]), (tip[0], tip[1]))
            dist_pip = math.dist((wrist[0], wrist[1]), (pip[0], pip[1]))
            # In an extended finger, tip is substantially further from wrist than pip
            if dist_tip > dist_pip * 1.25 and (tip[1] < pip[1] + 0.05 * hand_scale):
                extended_count += 1

        # Check thumb extension
        thumb_tip = lms[4]
        thumb_mcp = lms[2]
        thumb_dist = math.dist((wrist[0], wrist[1]), (thumb_tip[0], thumb_tip[1]))
        mcp_dist = math.dist((wrist[0], wrist[1]), (thumb_mcp[0], thumb_mcp[1]))
        thumb_extended = thumb_dist > mcp_dist * 1.20

        is_palm = (extended_count >= 4) and thumb_extended
        diag = {
            "extended_count": extended_count,
            "thumb_extended": thumb_extended,
            "is_open_palm": is_palm
        }
        return is_palm, diag

    def _is_victory_sign(self, lms: List[Tuple[float, float, float]]) -> Tuple[bool, dict]:
        """
        Detects Victory / Peace Sign (✌️) as an intentional, unmistakable START GESTURE:
        - Index (8) and Middle (12) are EXTENDED.
        - Ring (16) and Pinky (20) are FOLDED.
        - Thumb (4) is folded across palm.
        """
        wrist = lms[0]
        hand_scale = self._get_hand_scale(lms)

        # Index & Middle extended
        idx_tip, idx_pip = lms[8], lms[6]
        mid_tip, mid_pip = lms[12], lms[10]

        idx_ext = math.dist((wrist[0], wrist[1]), (idx_tip[0], idx_tip[1])) > math.dist((wrist[0], wrist[1]), (idx_pip[0], idx_pip[1])) * 1.25
        mid_ext = math.dist((wrist[0], wrist[1]), (mid_tip[0], mid_tip[1])) > math.dist((wrist[0], wrist[1]), (mid_pip[0], mid_pip[1])) * 1.25

        # Ring & Pinky folded
        rng_tip, rng_pip, rng_mcp = lms[16], lms[14], lms[13]
        pnk_tip, pnk_pip, pnk_mcp = lms[20], lms[18], lms[17]

        rng_fold = (rng_tip[1] >= rng_mcp[1] - 0.12 * hand_scale) or (math.dist((wrist[0], wrist[1]), (rng_tip[0], rng_tip[1])) < math.dist((wrist[0], wrist[1]), (rng_pip[0], rng_pip[1])) * 1.20)
        pnk_fold = (pnk_tip[1] >= pnk_mcp[1] - 0.12 * hand_scale) or (math.dist((wrist[0], wrist[1]), (pnk_tip[0], pnk_tip[1])) < math.dist((wrist[0], wrist[1]), (pnk_pip[0], pnk_pip[1])) * 1.20)

        # Thumb not pointing up like thumbs-up
        thumb_tip = lms[4]
        index_mcp = lms[5]
        thumb_down = thumb_tip[1] >= index_mcp[1] - 0.12 * hand_scale

        is_peace = idx_ext and mid_ext and rng_fold and pnk_fold and thumb_down
        diag = {
            "index_ext": idx_ext,
            "mid_ext": mid_ext,
            "rng_fold": rng_fold,
            "pnk_fold": pnk_fold,
            "thumb_down": thumb_down,
            "is_peace": is_peace
        }
        return is_peace, diag

    def _check_any_hand(self, hands_data: list, func) -> Tuple[bool, dict]:
        """Test a gesture function across all detected hands."""
        combined_diag = {}
        for i, h in enumerate(hands_data):
            matched, diag = func(h.landmarks)
            combined_diag[f"hand_{i}"] = diag
            if matched:
                return True, combined_diag
        return False, combined_diag

    def _check_start_gesture(self, hands_data: list, raw_steer: float) -> Tuple[bool, dict]:
        """Check for either Victory Sign (✌️) or Both Hands Wheel Ready position."""
        diag = {}
        # 1. Victory Sign on either hand
        for i, h in enumerate(hands_data):
            is_v, v_diag = self._is_victory_sign(h.landmarks)
            diag[f"hand_{i}_victory"] = v_diag
            if is_v:
                return True, {"type": "VICTORY_SIGN", **diag}

        # 2. Both Hands Wheel Ready (holding steering wheel steady near center)
        if len(hands_data) >= 2 and abs(raw_steer) < 0.20:
            return True, {"type": "WHEEL_READY", "steer": raw_steer}

        return False, diag

    def _get_debounced_gesture(self, current: str) -> str:
        """Apply majority voting across the recent frames buffer."""
        if not self.last_gesture_history:
            return current
        counts = {}
        for g in self.last_gesture_history:
            counts[g] = counts.get(g, 0) + 1
        most_common = max(counts, key=counts.get)
        if counts[most_common] >= len(self.last_gesture_history) // 2:
            return most_common
        return current
