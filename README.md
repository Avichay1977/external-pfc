# External PFC — Hair Touch Monitor

> *Between rockets and shelters, inspiration finds its way in.*

Real-time Trichotillomania intervention system. Detects when a hand moves toward the hairline and interrupts the impulse before it lands. Runs locally — no cloud, no server, no data leaving the device.

---

## Installation

### 🖥️ Windows

1. Download [External-PFC.zip](https://github.com/Avichay1977/external-pfc/raw/master/External-PFC.zip)
2. Extract the folder
3. Double-click `install_windows.bat`

That's it. The monitor runs silently in the background and starts automatically with Windows.

---

### 📱 Android (Pydroid 3)

1. Install [Pydroid 3](https://play.google.com/store/apps/details?id=ru.iiec.pydroid3) from Google Play
2. Download [pfc_android.py](https://raw.githubusercontent.com/Avichay1977/external-pfc/master/pfc_android.py)
3. Open the file in Pydroid 3 and tap **Run**
4. On first run it installs all dependencies automatically

---

### 🍎 iPad / iPhone (Safari)

1. Download [pfc_ipad.html](https://raw.githubusercontent.com/Avichay1977/external-pfc/master/pfc_ipad.html)
2. Open in Safari
3. Tap **Share → Add to Home Screen**
4. Open from your home screen and tap **Start**

---

## How it works

- Tracks hand and face position at 30fps using MediaPipe
- Detects movement toward the hairline only (forehead, temples, crown)
- Ignores eating, drinking, scratching nose
- Recognizes pinch/grasp posture — only deliberate pulling movements trigger an alert
- Logs every event to CSV for weekly pattern analysis

---

## License

MIT — free to use, modify, and share.
