"""
hand_tracking_module.py
------------------------
Uses MediaPipe's Tasks API (HandLandmarker) in VIDEO mode.

Why VIDEO mode instead of IMAGE mode: IMAGE mode re-detects the hand
from scratch on every frame with no memory of previous frames, which
causes visible jitter/flicker in the landmark overlay. VIDEO mode tracks
the hand across frames (using each frame's timestamp), giving smoother,
more stable results.
"""

import os
import time
import urllib.request
import cv2
import math
import mediapipe as mp
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision as mp_vision

MODEL_URL = "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task"
MODEL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hand_landmarker.task")


def _ensure_model():
    if not os.path.exists(MODEL_PATH):
        print("Downloading hand-tracking model (one-time, ~8MB)...")
        urllib.request.urlretrieve(MODEL_URL, MODEL_PATH)
        print("Model downloaded.")


HAND_CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 4),
    (0, 5), (5, 6), (6, 7), (7, 8),
    (5, 9), (9, 10), (10, 11), (11, 12),
    (9, 13), (13, 14), (14, 15), (15, 16),
    (13, 17), (17, 18), (18, 19), (19, 20),
    (0, 17),
]


class HandDetector:
    def __init__(self, mode=False, max_hands=2, detection_con=0.7, track_con=0.7):
        _ensure_model()
        base_options = mp_python.BaseOptions(model_asset_path=MODEL_PATH)
        options = mp_vision.HandLandmarkerOptions(
            base_options=base_options,
            num_hands=max_hands,
            min_hand_detection_confidence=detection_con,
            min_tracking_confidence=track_con,
            running_mode=mp_vision.RunningMode.VIDEO,
        )
        self.detector = mp_vision.HandLandmarker.create_from_options(options)

        self.tip_ids = [4, 8, 12, 16, 20]
        self.result = None
        self.landmark_list = []
        self._start_time = time.time()

    def find_hands(self, img, draw=True):
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=img_rgb)
        timestamp_ms = int((time.time() - self._start_time) * 1000)
        self.result = self.detector.detect_for_video(mp_image, timestamp_ms)

        if draw and self.result and self.result.hand_landmarks:
            h, w, _ = img.shape
            for hand_landmarks in self.result.hand_landmarks:
                points = [(int(lm.x * w), int(lm.y * h)) for lm in hand_landmarks]
                for start, end in HAND_CONNECTIONS:
                    cv2.line(img, points[start], points[end], (0, 255, 0), 2)
                for (x, y) in points:
                    cv2.circle(img, (x, y), 4, (255, 0, 255), cv2.FILLED)
        return img

    def find_position(self, img, hand_no=0, draw=True):
        self.landmark_list = []
        if self.result and self.result.hand_landmarks:
            if hand_no < len(self.result.hand_landmarks):
                hand_landmarks = self.result.hand_landmarks[hand_no]
                h, w, _ = img.shape
                for idx, lm in enumerate(hand_landmarks):
                    cx, cy = int(lm.x * w), int(lm.y * h)
                    self.landmark_list.append([idx, cx, cy])
        return self.landmark_list

    def get_handedness(self, hand_no=0):
        if self.result and self.result.handedness:
            if hand_no < len(self.result.handedness):
                return self.result.handedness[hand_no][0].category_name
        return None

    def num_hands_detected(self):
        if self.result and self.result.hand_landmarks:
            return len(self.result.hand_landmarks)
        return 0

    def fingers_up(self):
        fingers = []
        if not self.landmark_list:
            return [0, 0, 0, 0, 0]

        if self.landmark_list[self.tip_ids[0]][1] > self.landmark_list[self.tip_ids[0] - 1][1]:
            fingers.append(1)
        else:
            fingers.append(0)

        for id in range(1, 5):
            if self.landmark_list[self.tip_ids[id]][2] < self.landmark_list[self.tip_ids[id] - 2][2]:
                fingers.append(1)
            else:
                fingers.append(0)

        return fingers

    @staticmethod
    def find_distance(p1, p2, img=None, draw=True):
        x1, y1 = p1
        x2, y2 = p2
        cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
        length = math.hypot(x2 - x1, y2 - y1)

        if img is not None and draw:
            cv2.circle(img, (x1, y1), 8, (255, 0, 255), cv2.FILLED)
            cv2.circle(img, (x2, y2), 8, (255, 0, 255), cv2.FILLED)
            cv2.line(img, (x1, y1), (x2, y2), (255, 0, 255), 2)
            cv2.circle(img, (cx, cy), 8, (255, 0, 255), cv2.FILLED)

        return length, img, [x1, y1, x2, y2, cx, cy]
