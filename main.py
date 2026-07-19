"""
main.py
-------
Gesture Controller with hover-menu mode select.

Settings (camera size, gesture thresholds, zone widths) live in
config.json, next to this file -- edit that instead of this code
to tune sensitivity.

Menu (hold index fingertip on a button for 2s to select):
  G -> Gestures: window control
       fist               -> minimize (or confirm app switcher if it's open)
       open palm           -> opens app switcher and holds it open
       move hand left/right while palm open -> step through apps one at a time
  R -> Remote: hand position = arrow keys (for games)
  V -> Volume (right-hand pinch)
  B -> Brightness (right-hand pinch)
  X -> Exit

Press 'm' anytime to return to the menu. Press 'q' anytime to quit.
"""

import cv2
import json
import os
import numpy as np

from hand_tracking_module import HandDetector
from gesture_menu import MenuButton, HoverMenu
import system_control as sysctl

CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")

DEFAULTS = {
    "camera": {"width": 480, "height": 360},
    "gesture_thresholds": {"min_dist": 25, "max_dist": 200},
    "menu": {"dwell_seconds": 2.0},
    "gestures_mode": {"left_zone_frac": 0.38, "right_zone_frac": 0.62},
}


def load_config():
    cfg = {k: v.copy() for k, v in DEFAULTS.items()}
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH) as f:
                user_cfg = json.load(f)
            for key, value in user_cfg.items():
                if key in cfg and isinstance(value, dict):
                    cfg[key].update(value)
                else:
                    cfg[key] = value
        except Exception as e:
            print(f"Warning: could not read config.json ({e}); using defaults.")
    return cfg


CONFIG = load_config()
CAM_WIDTH = CONFIG["camera"]["width"]
CAM_HEIGHT = CONFIG["camera"]["height"]
MIN_DIST = CONFIG["gesture_thresholds"]["min_dist"]
MAX_DIST = CONFIG["gesture_thresholds"]["max_dist"]
DWELL_SECONDS = CONFIG["menu"]["dwell_seconds"]
LEFT_ZONE_FRAC = CONFIG["gestures_mode"]["left_zone_frac"]
RIGHT_ZONE_FRAC = CONFIG["gestures_mode"]["right_zone_frac"]

STATE_MENU = "menu"
STATE_GESTURES = "gestures"
STATE_REMOTE = "remote"
STATE_VOLUME = "volume"
STATE_BRIGHTNESS = "brightness"


def make_menu_buttons():
    return [
        MenuButton("G", (100, 380)),
        MenuButton("R", (220, 130)),
        MenuButton("V", (320, 90)),
        MenuButton("B", (420, 130)),
        MenuButton("X", (540, 380)),
    ]


def main():
    cap = cv2.VideoCapture(0)
    cap.set(3, CAM_WIDTH)
    cap.set(4, CAM_HEIGHT)

    detector = HandDetector(max_hands=1, detection_con=0.75)
    menu = HoverMenu(make_menu_buttons(), dwell_seconds=DWELL_SECONDS)

    state = STATE_MENU
    zone_state = "center"
    vol_percent = sysctl.get_volume()
    bright_percent = sysctl.get_brightness()
    last_arrow_zone = None

    while True:
        success, img = cap.read()
        if not success:
            print("Could not read from webcam.")
            break

        img = cv2.flip(img, 1)
        img = detector.find_hands(img)
        lm_list = detector.find_position(img, hand_no=0, draw=False)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        if key == ord('m'):
            if sysctl.switcher_is_active():
                sysctl.confirm_app_switcher()
            state = STATE_MENU

        if state == STATE_MENU:
            fingertip = (lm_list[8][1], lm_list[8][2]) if len(lm_list) > 8 else None
            selected = menu.update(fingertip)
            menu.draw(img)
            if selected == "G":
                state = STATE_GESTURES
            elif selected == "R":
                state = STATE_REMOTE
            elif selected == "V":
                state = STATE_VOLUME
            elif selected == "B":
                state = STATE_BRIGHTNESS
            elif selected == "X":
                break

        elif state == STATE_GESTURES:
            h, w = img.shape[:2]
            cv2.line(img, (int(w * LEFT_ZONE_FRAC), 0), (int(w * LEFT_ZONE_FRAC), h), (100, 100, 255), 1)
            cv2.line(img, (int(w * RIGHT_ZONE_FRAC), 0), (int(w * RIGHT_ZONE_FRAC), h), (100, 100, 255), 1)

            if len(lm_list) > 0:
                fingers = detector.fingers_up()
                wrist_x = lm_list[0][1]

                if sum(fingers) == 0:
                    if sysctl.switcher_is_active():
                        sysctl.confirm_app_switcher()
                        zone_state = "center"
                    else:
                        sysctl.minimize_window()

                elif sum(fingers) == 5:
                    if not sysctl.switcher_is_active():
                        sysctl.open_app_switcher()
                        zone_state = "center"

                    if wrist_x < w * LEFT_ZONE_FRAC:
                        zone = "left"
                    elif wrist_x > w * RIGHT_ZONE_FRAC:
                        zone = "right"
                    else:
                        zone = "center"

                    if zone != zone_state:
                        if zone == "left" and zone_state == "center":
                            sysctl.switcher_step("prev")
                        elif zone == "right" and zone_state == "center":
                            sysctl.switcher_step("next")
                        zone_state = zone

            status = "switcher OPEN - move left/right to step, fist to confirm" \
                if sysctl.switcher_is_active() else "fist=minimize | open palm=open switcher"
            cv2.putText(img, f"GESTURES: {status}",
                        (10, 460), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (200, 200, 200), 1)

        elif state == STATE_REMOTE:
            if len(lm_list) > 0:
                x = lm_list[0][1]
                y = lm_list[0][2]
                h, w = img.shape[:2]
                zone = None
                if x < w * 0.3:
                    zone = "left"
                elif x > w * 0.7:
                    zone = "right"
                elif y < h * 0.3:
                    zone = "up"
                elif y > h * 0.7:
                    zone = "down"

                if zone and zone != last_arrow_zone:
                    sysctl.press_arrow(zone)
                last_arrow_zone = zone

            cv2.putText(img, "REMOTE: move hand to screen edges for arrow keys",
                        (10, 460), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)

        elif state in (STATE_VOLUME, STATE_BRIGHTNESS):
            if len(lm_list) > 8:
                x1, y1 = lm_list[4][1], lm_list[4][2]
                x2, y2 = lm_list[8][1], lm_list[8][2]
                length, img, line_info = HandDetector.find_distance((x1, y1), (x2, y2), img)
                percent = int(np.clip(np.interp(length, [MIN_DIST, MAX_DIST], [0, 100]), 0, 100))

                if state == STATE_VOLUME:
                    vol_percent = percent
                    sysctl.set_volume(vol_percent)
                    cv2.putText(img, f'Vol: {vol_percent}%', (10, 460),
                                cv2.FONT_HERSHEY_COMPLEX, 0.7, (255, 0, 0), 2)
                else:
                    bright_percent = percent
                    sysctl.set_brightness(bright_percent)
                    cv2.putText(img, f'Bri: {bright_percent}%', (10, 460),
                                cv2.FONT_HERSHEY_COMPLEX, 0.7, (0, 165, 255), 2)

        cv2.putText(img, f"Mode: {state}  (m: menu, q: quit)", (10, 30),
                    cv2.FONT_HERSHEY_COMPLEX, 0.6, (0, 255, 0), 2)

        cv2.imshow("Gesture Controller", img)

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
