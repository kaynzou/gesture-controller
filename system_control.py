"""
system_control.py
------------------
macOS-native volume + brightness control, plus window/app control
for the gesture menu.

App switcher model: open palm opens the switcher and holds it open
(Cmd held down). Moving your hand left/right steps through apps one
at a time. Closing into a fist confirms your choice (releases Cmd).
"""

import subprocess
import pyautogui

pyautogui.FAILSAFE = False

try:
    import screen_brightness_control as sbc
    BRIGHTNESS_AVAILABLE = True
except ImportError:
    BRIGHTNESS_AVAILABLE = False


def set_volume(percent: int):
    percent = max(0, min(100, int(percent)))
    subprocess.run(
        ["osascript", "-e", f"set volume output volume {percent}"],
        check=False,
    )


def get_volume() -> int:
    result = subprocess.run(
        ["osascript", "-e", "output volume of (get volume settings)"],
        capture_output=True,
        text=True,
        check=False,
    )
    try:
        return int(result.stdout.strip())
    except ValueError:
        return 50


def is_muted() -> bool:
    result = subprocess.run(
        ["osascript", "-e", "output muted of (get volume settings)"],
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout.strip() == "true"


def set_mute(muted: bool):
    state = "true" if muted else "false"
    subprocess.run(
        ["osascript", "-e", f"set volume output muted {state}"],
        check=False,
    )


def set_brightness(percent: int):
    """Kept for compatibility -- on Apple Silicon internal displays this
    is unreliable, so brightness is actually controlled via
    nudge_brightness() below using real keyboard brightness keys instead."""
    if not BRIGHTNESS_AVAILABLE:
        return
    percent = max(0, min(100, int(percent)))
    try:
        sbc.set_brightness(percent)
    except Exception:
        pass


def get_brightness() -> int:
    if not BRIGHTNESS_AVAILABLE:
        return 50
    try:
        return sbc.get_brightness()[0]
    except Exception:
        return 50


# ---- Brightness via real keyboard keys (works reliably on Apple Silicon) ----
# macOS brightness-up/down are keyboard hardware keys under the hood.
# key code 144 = brightness up, 145 = brightness down (standard Mac keyboard codes).

def nudge_brightness(direction: str):
    """direction: 'up' or 'down'. Simulates pressing the physical brightness key."""
    code = "144" if direction == "up" else "145"
    subprocess.run(
        ["osascript", "-e", f"tell application \"System Events\" to key code {code}"],
        check=False,
    )


def minimize_window():
    pyautogui.hotkey('command', 'm')


def close_window():
    pyautogui.hotkey('command', 'w')


def press_arrow(direction):
    """direction: 'left', 'right', 'up', 'down'"""
    pyautogui.press(direction)


# ---- App switcher: open + hold, step left/right, confirm with a fist ----

_switcher_active = False


def open_app_switcher():
    """Open the Cmd+Tab switcher and hold Cmd down. Call once when palm opens."""
    global _switcher_active
    if not _switcher_active:
        pyautogui.keyDown('command')
        pyautogui.press('tab')
        _switcher_active = True


def switcher_step(direction):
    """direction: 'next' (right) or 'prev' (left). Cmd must already be held."""
    if not _switcher_active:
        return
    if direction == 'next':
        pyautogui.press('tab')
    else:
        pyautogui.keyDown('shift')
        pyautogui.press('tab')
        pyautogui.keyUp('shift')


def confirm_app_switcher():
    """Release Cmd, locking in whichever app is currently highlighted."""
    global _switcher_active
    if _switcher_active:
        pyautogui.keyUp('command')
        _switcher_active = False


def switcher_is_active() -> bool:
    return _switcher_active
