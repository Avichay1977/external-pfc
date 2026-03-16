# External PFC - Executive Function Prosthetic

Real-time hair-touch detection system for trichotillomania awareness.
Pure Edge AI — no cloud, no server, no data leaving the device.

## How It Works

Uses MediaPipe Face Mesh + Hands to detect when a hand moves toward the hairline zone.
3D distance calculation with pinch/pull pose recognition. Alerts only for hair area (above hairline + temples), ignores eating/drinking.

## Platforms

| Platform | Alert Type | How It Runs |
|----------|-----------|-------------|
| **Windows** | Red border flash | Silent background process, auto-starts with Windows |
| **Android** | Haptic vibration | Pydroid 3 script, auto-restarts |
| **iPad** | Visual + audio beep | Safari PWA, Add to Home Screen |

---

## Installation

### Windows

1. Download or clone this repo
2. Run `install_windows.bat`
3. Done — PFC starts automatically with Windows

**Requirements:** Python 3.8+, webcam

### Android

1. Install [Pydroid 3](https://play.google.com/store/apps/details?id=ru.iiec.pydroid3) from Play Store
2. Copy `pfc_android.py` to the device
3. Open in Pydroid 3 and tap Run
4. First run auto-installs dependencies

### iPad

1. Send `pfc_ipad.html` to the iPad (AirDrop / WhatsApp / Email)
2. Open in Safari
3. Tap Share → **Add to Home Screen**
4. Launch from home screen — runs as full-screen app
5. Tap "התחל" (Start) and allow camera access

---

## CSV Logging

All alerts are logged with timestamp, date, hour, and distance values.
- **Windows/Android:** `pfc_log.csv` in the script folder
- **iPad:** Double-tap the HUD bar to download CSV

Use `analyze_log.py` to view hourly patterns and trends.

## Auto-Update (Windows)

The Windows version checks GitHub for updates on startup and applies them automatically.

---

Built with Claude Code.
