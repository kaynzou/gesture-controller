# Gesture Controller (macOS)

Control your Mac's **volume** and **screen brightness** using hand gestures,
tracked live through your webcam with OpenCV + MediaPipe.

- **Right hand**, pinch thumb + index finger → controls **volume**
- **Left hand**, pinch thumb + index finger → controls **brightness**
- Distance between fingers maps to 0–100%

This is a macOS-adapted version of the classic "gesture volume control"
project. The original tutorials you'll find online use `pycaw`, which is
**Windows-only** — this version uses `osascript` (built into macOS) for
volume, so it works natively without extra system dependencies.

## Setup

1. Make sure you have Python 3.9+ installed:
   ```bash
   python3 --version
   ```

2. (Recommended) Create a virtual environment:
   ```bash
   cd gesture-controller
   python3 -m venv venv
   source venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Run it:
   ```bash
   python3 main.py
   ```

5. **Grant camera permission** the first time macOS prompts you
   (System Settings → Privacy & Security → Camera → allow your terminal/IDE).

6. Press `q` in the video window to quit.

## Known macOS caveats

- **Brightness control**: `screen_brightness_control` works reliably on
  Intel Macs and most external displays. On some Apple Silicon MacBooks,
  macOS restricts programmatic control of the *internal* display's
  brightness — if you see no effect, try it with an external monitor
  connected, or skip brightness and just keep the volume gesture.
- **Camera permission**: if the video window doesn't open, check
  System Settings → Privacy & Security → Camera and allow your terminal
  app (Terminal, iTerm, VS Code, etc).

## How it works

1. `hand_tracking_module.py` wraps MediaPipe Hands — detects 21 landmarks
   per hand and tells you which fingers are up and how far apart any two
   points are.
2. `system_control.py` translates a 0–100 percentage into an actual
   macOS volume/brightness change.
3. `main.py` ties it together: reads webcam frames, tracks both hands,
   measures thumb–index distance per hand, maps that distance to a
   percentage, and applies it.

## Ideas to extend it

- Add a **fist gesture to mute/unmute** instantly.
- Add **face detection** (MediaPipe Face Mesh) to only activate control
  when your face is visible — mirrors the "face + hand recognition"
  combo from the original post.
- Swap `pyautogui`/`pynput` in to control **media playback** (play/pause,
  skip track) with a swipe gesture.
- Save a short screen recording of it working (like the demo GIF in the
  post) using QuickTime's built-in screen recorder.

## Configuration (config.json)

All tunable numbers live in `config.json` — edit values there instead of the code:

```json
{
  "camera": { "width": 480, "height": 360 },
  "gesture_thresholds": { "min_dist": 25, "max_dist": 200 },
  "menu": { "dwell_seconds": 2.0 },
  "gestures_mode": { "left_zone_frac": 0.38, "right_zone_frac": 0.62 }
}
```

- `camera.width/height` — lower = faster tracking, less lag; higher = clearer image.
- `gesture_thresholds.min_dist/max_dist` — pixel distance range mapped to 0-100% for volume/brightness pinch.
- `menu.dwell_seconds` — how long to hover on a menu button before it selects.
- `gestures_mode.left_zone_frac/right_zone_frac` — how far from center your hand must move to step through the app switcher. Narrower gap (values closer together) = shorter, quicker movements needed.

If `config.json` is missing or has a typo, the app falls back to built-in defaults and prints a warning instead of crashing.

## Full Gesture List

- **Menu**: hover index fingertip over G / R / V / B / X for 2s to select a mode.
- **Gestures (G)**: fist = minimize window. Open palm = open app switcher (holds Cmd). While switcher is open, move hand left/right past the blue guide lines to step through apps. Fist again = confirm.
- **Remote (R)**: move whole hand to screen edges (left/right/up/down) for arrow key presses. Good for turn-based browser games like 2048.
- **Volume (V)** / **Brightness (B)**: pinch thumb + index finger together/apart.
- Press `m` anytime to return to the menu, `q` to quit.
