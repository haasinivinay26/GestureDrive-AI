"""
Threaded Camera Manager for GestureDrive AI.
Captures frames from webcam in a dedicated background thread, performs MediaPipe
hand tracking and gesture recognition without blocking the Pygame 60 FPS loop.
"""

import time
import threading
from typing import Optional, Tuple
import cv2
import numpy as np
import pygame

from config import (
    CAMERA_WIDTH, CAMERA_HEIGHT, CAMERA_FPS,
    CAMERA_PIP_WIDTH, CAMERA_PIP_HEIGHT,
    SETTINGS
)
from camera.hand_tracker import HandTracker, HandData
from camera.gesture_recognizer import GestureRecognizer, GestureState


class CameraManager:
    """Manages background webcam capture, hand tracking, and thread-safe gesture state retrieval."""

    def __init__(self, camera_index: int = 0):
        self.camera_index = camera_index
        self.running = False
        self.cap: Optional[cv2.VideoCapture] = None
        self.thread: Optional[threading.Thread] = None
        self.lock = threading.Lock()

        # Components
        self.tracker: Optional[HandTracker] = None
        self.recognizer = GestureRecognizer()

        # Shared State
        self.current_state = GestureState()
        self.latest_preview_surface: Optional[pygame.Surface] = None
        self.latest_raw_frame: Optional[np.ndarray] = None
        self.is_connected = False
        self.error_message: Optional[str] = None
        self.measured_fps = 0.0

    def start(self) -> bool:
        """Initialize camera device and spawn tracking thread."""
        if self.running:
            return True

        self.camera_index = SETTINGS.camera_index
        print(f"[Camera] Initializing camera index {self.camera_index}...")

        try:
            # Try DirectShow first on Windows for fast startup
            self.cap = cv2.VideoCapture(self.camera_index, cv2.CAP_DSHOW)
            if not self.cap or not self.cap.isOpened():
                # Fallback to standard capture API
                self.cap = cv2.VideoCapture(self.camera_index)

            if not self.cap or not self.cap.isOpened():
                self.error_message = f"Webcam #{self.camera_index} could not be opened. Using keyboard fallback."
                print(f"[Camera] Error: {self.error_message}")
                self.is_connected = False
                return False

            # Configure resolution and target frame rate
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_WIDTH)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_HEIGHT)
            self.cap.set(cv2.CAP_PROP_FPS, CAMERA_FPS)

            self.tracker = HandTracker(
                max_num_hands=2,
                min_detection_confidence=SETTINGS.gesture_sensitivity,
                min_tracking_confidence=0.5
            )

            self.running = True
            self.is_connected = True
            self.error_message = None

            self.thread = threading.Thread(target=self._worker_loop, daemon=True, name="CameraWorker")
            self.thread.start()
            print("[Camera] Tracking worker thread started successfully.")
            return True

        except Exception as e:
            self.error_message = f"Camera initialization exception: {e}"
            print(f"[Camera] Exception: {self.error_message}")
            self.is_connected = False
            self.running = False
            return False

    def _worker_loop(self):
        """Continuously capture frames and recognize gestures in the background."""
        fps_timer = time.time()
        frame_counter = 0

        while self.running and self.cap and self.cap.isOpened():
            success, frame = self.cap.read()
            if not success or frame is None:
                time.sleep(0.01)
                continue

            # Mirror frame horizontally for intuitive steering interaction
            frame = cv2.flip(frame, 1)

            # Process hand landmarks and generate annotated visualization
            try:
                hands_data, annotated_rgb = self.tracker.process_frame(frame)
                state = self.recognizer.process(hands_data)
            except Exception as e:
                # Catch any transient processing glitch
                hands_data = []
                annotated_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                state = GestureState(active_gesture=f"ERR: {str(e)[:15]}")

            # Draw active gesture banner overlay onto camera frame
            self._render_camera_hud(annotated_rgb, state)

            # Convert to Pygame Surface for Picture-in-Picture display
            pip_resized = cv2.resize(annotated_rgb, (CAMERA_PIP_WIDTH, CAMERA_PIP_HEIGHT))
            # Pygame surface requires (width, height), shape is (h, w, 3)
            # Pygame frombuffer with RGB format:
            surface = pygame.image.frombuffer(pip_resized.tobytes(), (CAMERA_PIP_WIDTH, CAMERA_PIP_HEIGHT), "RGB")

            # Calculate vision FPS
            frame_counter += 1
            now = time.time()
            if now - fps_timer >= 1.0:
                self.measured_fps = frame_counter / (now - fps_timer)
                frame_counter = 0
                fps_timer = now

            # Thread-safe state update
            with self.lock:
                self.current_state = state
                self.latest_preview_surface = surface
                self.latest_raw_frame = frame

            # Regulate capture rate to avoid CPU spinning
            time.sleep(1.0 / (CAMERA_FPS * 1.5))

    def _render_camera_hud(self, img_rgb: np.ndarray, state: GestureState):
        """Render cyberpunk HUD telemetry directly onto camera frame."""
        h, w, _ = img_rgb.shape

        # Top status bar
        if state.is_braking:
            bar_color = (255, 45, 85)     # Neon red
            text = "BRAKE ACTIVE [OPEN PALM]"
        elif state.is_accelerating:
            bar_color = (50, 255, 120)    # Neon green
            text = "ACCEL ACTIVE [THUMBS UP]"
        elif state.hands_detected >= 2:
            bar_color = (0, 240, 255)     # Neon cyan
            text = f"WHEEL: {state.wheel_tilt_degrees:+.1f} deg"
        elif state.hands_detected == 1:
            bar_color = (255, 175, 20)    # Amber
            text = "ASSIST MODE (1 HAND)"
        else:
            bar_color = (120, 130, 150)   # Muted
            text = "WAITING FOR HANDS..."

        # Semi-transparent top ribbon
        overlay = img_rgb.copy()
        cv2.rectangle(overlay, (0, 0), (w, 36), (20, 24, 32), -1)
        cv2.rectangle(overlay, (0, 32), (w, 36), bar_color, -1)
        cv2.addWeighted(overlay, 0.75, img_rgb, 0.25, 0, img_rgb)

        # Draw status text
        cv2.putText(img_rgb, text, (10, 24), cv2.FONT_HERSHEY_DUPLEX, 0.55, (255, 255, 255), 1, cv2.LINE_AA)

        # Draw steering center marker crosshair
        cx, cy = w // 2, h - 30
        cv2.line(img_rgb, (cx - 15, cy), (cx + 15, cy), (100, 110, 130), 1, cv2.LINE_AA)
        cv2.line(img_rgb, (cx, cy - 8), (cx, cy + 8), (100, 110, 130), 1, cv2.LINE_AA)

        # Steering needle
        steer_px = int(cx + state.steer_angle * (w * 0.35))
        cv2.circle(img_rgb, (steer_px, cy), 6, bar_color, -1, cv2.LINE_AA)
        cv2.circle(img_rgb, (steer_px, cy), 8, (255, 255, 255), 1, cv2.LINE_AA)

    def get_state(self) -> GestureState:
        """Retrieve the latest thread-safe gesture state."""
        with self.lock:
            return self.current_state

    def get_preview_surface(self) -> Optional[pygame.Surface]:
        """Retrieve the latest rendered camera PIP surface for Pygame."""
        with self.lock:
            return self.latest_preview_surface

    def restart(self, new_index: Optional[int] = None) -> bool:
        """Switch camera index or reconnect."""
        if new_index is not None:
            self.camera_index = new_index
            SETTINGS.camera_index = new_index
            SETTINGS.save()
        self.stop()
        return self.start()

    def stop(self):
        """Halt worker thread and free camera resources."""
        self.running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=1.5)
        if self.cap:
            try:
                self.cap.release()
            except Exception:
                pass
            self.cap = None
        if self.tracker:
            try:
                self.tracker.close()
            except Exception:
                pass
            self.tracker = None
        self.is_connected = False
        print("[Camera] Stopped and released resources.")

    def release(self):
        """Alias for stop()."""
        self.stop()
