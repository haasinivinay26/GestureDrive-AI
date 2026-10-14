"""
Hand tracking module using MediaPipe.
Detects up to 2 hands, extracts 21 3D landmarks per hand, and renders neon HUD annotations.
"""

from typing import List, Optional, Tuple, Dict, Any
import cv2
import mediapipe as mp
import numpy as np


class HandData:
    """Encapsulates detected hand information."""
    def __init__(self, label: str, landmarks: List[Tuple[float, float, float]], raw_landmarks):
        self.label = label  # 'Left' or 'Right'
        self.landmarks = landmarks  # List of 21 (x, y, z) normalized coords
        self.raw_landmarks = raw_landmarks

    @property
    def wrist(self) -> Tuple[float, float, float]:
        return self.landmarks[0]

    @property
    def thumb_tip(self) -> Tuple[float, float, float]:
        return self.landmarks[4]

    @property
    def index_tip(self) -> Tuple[float, float, float]:
        return self.landmarks[8]

    @property
    def middle_tip(self) -> Tuple[float, float, float]:
        return self.landmarks[12]

    @property
    def ring_tip(self) -> Tuple[float, float, float]:
        return self.landmarks[16]

    @property
    def pinky_tip(self) -> Tuple[float, float, float]:
        return self.landmarks[20]


# Connections between landmarks for bone rendering
HAND_CONNECTIONS = [
    # Thumb
    (0, 1), (1, 2), (2, 3), (3, 4),
    # Index
    (0, 5), (5, 6), (6, 7), (7, 8),
    # Middle
    (5, 9), (9, 10), (10, 11), (11, 12),
    # Ring
    (9, 13), (13, 14), (14, 15), (15, 16),
    # Pinky
    (13, 17), (17, 18), (18, 19), (19, 20),
    # Palm base
    (0, 17)
]


class HandTracker:
    """MediaPipe Hands wrapper with custom racing-themed HUD visualization."""

    def __init__(self, max_num_hands: int = 2, min_detection_confidence: float = 0.6, min_tracking_confidence: float = 0.5):
        self.max_num_hands = max_num_hands
        self.min_detection_confidence = min_detection_confidence
        self.min_tracking_confidence = min_tracking_confidence

        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=max_num_hands,
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence
        )

    def process_frame(self, frame_bgr: np.ndarray) -> Tuple[List[HandData], np.ndarray]:
        """
        Process a BGR webcam frame.
        Returns:
            hands_data: list of HandData objects
            annotated_frame: RGB frame with cyber HUD overlays for PIP display
        """
        h, w, _ = frame_bgr.shape
        # Convert BGR to RGB for MediaPipe
        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        # Performance optimization: writeable=False during inference
        frame_rgb.flags.writeable = False
        results = self.hands.process(frame_rgb)
        frame_rgb.flags.writeable = True

        hands_data: List[HandData] = []
        annotated = frame_rgb.copy()

        if results.multi_hand_landmarks:
            # Determine handedness labels
            handedness_list = []
            if results.multi_handedness:
                for classification in results.multi_handedness:
                    handedness_list.append(classification.classification[0].label)
            else:
                handedness_list = ["Hand"] * len(results.multi_hand_landmarks)

            for i, hand_lms in enumerate(results.multi_hand_landmarks):
                label = handedness_list[i] if i < len(handedness_list) else "Hand"
                pts = [(lm.x, lm.y, lm.z) for lm in hand_lms.landmark]
                hands_data.append(HandData(label=label, landmarks=pts, raw_landmarks=hand_lms))

                # Draw high-tech HUD skeleton
                self._draw_neon_skeleton(annotated, pts, w, h, label)

        return hands_data, annotated

    def _draw_neon_skeleton(self, img: np.ndarray, pts: List[Tuple[float, float, float]], w: int, h: int, label: str):
        """Draw cyber neon joints and bones on the frame."""
        # Convert normalized coords to pixel points
        pixel_pts = [(int(p[0] * w), int(p[1] * h)) for p in pts]

        # Draw bones (neon cyan)
        bone_color = (0, 220, 255)
        for start_idx, end_idx in HAND_CONNECTIONS:
            pt1 = pixel_pts[start_idx]
            pt2 = pixel_pts[end_idx]
            cv2.line(img, pt1, pt2, bone_color, 2, cv2.LINE_AA)

        # Draw joints (outer cyan circle, inner bright white dot)
        for i, pt in enumerate(pixel_pts):
            if i in (4, 8, 12, 16, 20):  # Fingertips: electric lime green
                cv2.circle(img, pt, 5, (50, 255, 120), -1, cv2.LINE_AA)
                cv2.circle(img, pt, 7, (0, 180, 80), 1, cv2.LINE_AA)
            elif i == 0:  # Wrist: neon purple
                cv2.circle(img, pt, 7, (220, 80, 255), -1, cv2.LINE_AA)
            else:  # Knuckles
                cv2.circle(img, pt, 3, (255, 255, 255), -1, cv2.LINE_AA)
                cv2.circle(img, pt, 4, (0, 180, 220), 1, cv2.LINE_AA)

        # Draw small label near wrist
        wrist_pt = pixel_pts[0]
        cv2.putText(img, label[:1], (wrist_pt[0] - 6, wrist_pt[1] + 18),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1, cv2.LINE_AA)

    def close(self):
        """Release MediaPipe resources."""
        if hasattr(self, "hands") and self.hands:
            self.hands.close()
