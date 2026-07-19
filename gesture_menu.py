"""
gesture_menu.py
---------------
Hover-to-select circular menu, matching the "hold your finger over a
button for ~2 seconds" interaction style.
"""

import time
import cv2

class MenuButton:
    def __init__(self, label, center, radius=45, color=(235, 175, 80)):
        self.label = label
        self.center = center
        self.radius = radius
        self.color = color

    def contains(self, point):
        px, py = point
        cx, cy = self.center
        return (px - cx) ** 2 + (py - cy) ** 2 <= self.radius ** 2

    def draw(self, img, hover_progress=0.0):
        cx, cy = self.center
        cv2.circle(img, (cx, cy), self.radius, self.color, cv2.FILLED)
        cv2.circle(img, (cx, cy), self.radius, (255, 255, 255), 2)
        cv2.putText(img, self.label, (cx - 12, cy + 10),
                    cv2.FONT_HERSHEY_COMPLEX, 1.0, (255, 255, 255), 2)

        if hover_progress > 0:
            angle = int(360 * hover_progress)
            cv2.ellipse(img, (cx, cy), (self.radius + 8, self.radius + 8),
                        -90, 0, angle, (0, 255, 0), 4)


class HoverMenu:
    def __init__(self, buttons, dwell_seconds=2.0):
        self.buttons = buttons
        self.dwell_seconds = dwell_seconds
        self.hover_start = None
        self.hover_button = None

    def update(self, fingertip_pos):
        if fingertip_pos is None:
            self.hover_start = None
            self.hover_button = None
            return None

        hit = None
        for btn in self.buttons:
            if btn.contains(fingertip_pos):
                hit = btn
                break

        if hit is None:
            self.hover_start = None
            self.hover_button = None
            return None

        if hit is not self.hover_button:
            self.hover_button = hit
            self.hover_start = time.time()
            return None

        elapsed = time.time() - self.hover_start
        if elapsed >= self.dwell_seconds:
            self.hover_start = None
            self.hover_button = None
            return hit.label

        return None

    def hover_progress(self):
        if self.hover_button is None or self.hover_start is None:
            return None, 0.0
        elapsed = time.time() - self.hover_start
        return self.hover_button, min(elapsed / self.dwell_seconds, 1.0)

    def draw(self, img):
        hover_btn, progress = self.hover_progress()
        for btn in self.buttons:
            btn.draw(img, hover_progress=progress if btn is hover_btn else 0.0)
