"""
Calibration workflow for GestureDrive AI.
Guides the player through a 5-step interactive calibration routine:
1. Neutral Steering Position (zeros center offset)
2. Left Wheel Turn
3. Right Wheel Turn
4. Thumbs-Up Accelerator Test
5. Open Palm Brake Test
"""

import time
from typing import Dict, Any, Optional
from config import SETTINGS
from camera.gesture_recognizer import GestureState


class CalibrationStep:
    NEUTRAL = 0
    TURN_LEFT = 1
    TURN_RIGHT = 2
    TEST_ACCEL = 3
    TEST_BRAKE = 4
    COMPLETED = 5


class CalibrationManager:
    """Manages the calibration wizard state machine and validation timers."""

    STEP_DESCRIPTIONS = [
        {
            "title": "STEP 1: NEUTRAL STEERING",
            "instruction": "Hold both hands level in front of your webcam like a steering wheel.",
            "target": "Hold steady for 2 seconds",
            "hint": "Keep your hands roughly 30-40 cm apart."
        },
        {
            "title": "STEP 2: STEER LEFT",
            "instruction": "Rotate your imaginary wheel to the LEFT (left hand down, right hand up).",
            "target": "Turn left past 15 degrees",
            "hint": "Feel the steering needle move left."
        },
        {
            "title": "STEP 3: STEER RIGHT",
            "instruction": "Rotate your imaginary wheel to the RIGHT (right hand down, left hand up).",
            "target": "Turn right past 15 degrees",
            "hint": "Feel the steering needle move right."
        },
        {
            "title": "STEP 4: ACCELERATOR TEST",
            "instruction": "Make a clear THUMBS-UP with either hand to test acceleration.",
            "target": "Hold thumbs-up for 1.5 seconds",
            "hint": "Keep your other four fingers curled into a fist."
        },
        {
            "title": "STEP 5: BRAKE TEST",
            "instruction": "Show an OPEN PALM with all fingers spread to test braking.",
            "target": "Hold open palm for 1.5 seconds",
            "hint": "All 5 fingers should be spread open towards the camera."
        },
        {
            "title": "CALIBRATION COMPLETE!",
            "instruction": "Your gestures are calibrated and ready for the race track!",
            "target": "Press SPACE or START RACE to enter the game.",
            "hint": "You can re-run calibration anytime from the main menu."
        }
    ]

    def __init__(self):
        self.current_step = CalibrationStep.NEUTRAL
        self.step_hold_timer = 0.0
        self.required_hold_duration = 1.5
        self.is_finished = False

        # Captured calibration values
        self.neutral_tilt_sum = 0.0
        self.neutral_samples = 0
        self.max_left_tilt = 0.0
        self.max_right_tilt = 0.0

    def reset(self):
        """Reset calibration session."""
        self.current_step = CalibrationStep.NEUTRAL
        self.step_hold_timer = 0.0
        self.is_finished = False
        self.neutral_tilt_sum = 0.0
        self.neutral_samples = 0
        self.max_left_tilt = 0.0
        self.max_right_tilt = 0.0

    def update(self, dt: float, state: GestureState) -> float:
        """
        Process current frame state against current step requirements.
        Returns step progress from 0.0 to 1.0.
        """
        if self.is_finished:
            return 1.0

        step_satisfied = False

        if self.current_step == CalibrationStep.NEUTRAL:
            if state.hands_detected >= 2 and abs(state.steer_angle) < 0.25:
                step_satisfied = True
                self.neutral_tilt_sum += state.wheel_tilt_degrees
                self.neutral_samples += 1

        elif self.current_step == CalibrationStep.TURN_LEFT:
            if state.steer_angle < -0.35:
                step_satisfied = True
                self.max_left_tilt = min(self.max_left_tilt, state.wheel_tilt_degrees)

        elif self.current_step == CalibrationStep.TURN_RIGHT:
            if state.steer_angle > 0.35:
                step_satisfied = True
                self.max_right_tilt = max(self.max_right_tilt, state.wheel_tilt_degrees)

        elif self.current_step == CalibrationStep.TEST_ACCEL:
            if state.is_accelerating:
                step_satisfied = True

        elif self.current_step == CalibrationStep.TEST_BRAKE:
            if state.is_braking:
                step_satisfied = True

        # Accumulate hold timer if satisfied
        if step_satisfied:
            self.step_hold_timer += dt
            if self.step_hold_timer >= self.required_hold_duration:
                self._advance_step()
                self.step_hold_timer = 0.0
        else:
            self.step_hold_timer = max(0.0, self.step_hold_timer - dt * 1.5)

        progress = min(1.0, self.step_hold_timer / self.required_hold_duration)
        return progress

    def _advance_step(self):
        """Proceed to next calibration stage."""
        self.current_step += 1
        if self.current_step >= CalibrationStep.COMPLETED:
            self.is_finished = True
            self._save_calibration()

    def _save_calibration(self):
        """Save calibrated profile to settings."""
        if self.neutral_samples > 0:
            avg_neutral = self.neutral_tilt_sum / self.neutral_samples
            SETTINGS.neutral_tilt_deg = round(avg_neutral, 2)
            SETTINGS.calibration_offset_x = round(avg_neutral, 2)
        SETTINGS.save()
        print(f"[Calibration] Calibrated neutral settings saved: tilt={SETTINGS.neutral_tilt_deg} deg.")

    def get_step_info(self) -> Dict[str, Any]:
        """Return information for current calibration step."""
        step_idx = min(self.current_step, len(self.STEP_DESCRIPTIONS) - 1)
        return self.STEP_DESCRIPTIONS[step_idx]
