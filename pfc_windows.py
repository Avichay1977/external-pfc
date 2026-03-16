"""
External PFC - Windows Edition
רץ ברקע בשקט. מסגרת אדומה מהבהבת רק כשיד נוגעת באזור השיער.
מתעלם מאכילה/שתייה (אזור הפה והסנטר).
"""

import cv2
import mediapipe as mp
import numpy as np
import tkinter as tk
import threading
import time
import csv
import os
import sys
import subprocess
from datetime import datetime

# --- הגדרות ---
HAIR_THRESHOLD = 0.12  # סף מרחק לאזור שיער
COOLDOWN = 0.8         # שניות בין התראות
BORDER_WIDTH = 40      # עובי מסגרת אדומה
HISTORY_SIZE = 5       # פריימים לממוצע נע (סינון רעידות)
LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pfc_log.csv")

# נקודות פנים של MediaPipe Face Mesh
# אזור שיער: מצח, רקות, קודקוד
HAIR_ZONE_LANDMARKS = [
    10,   # מצח עליון (קודקוד)
    151,  # מצח מרכז
    70,   # גבה שמאל חיצוני
    300,  # גבה ימין חיצוני
    234,  # רקה שמאל
    454,  # רקה ימין
    21,   # מצח שמאל
    251,  # מצח ימין
]

# אזור פה - אם היד קרובה לפה = אכילה/שתייה, מתעלמים
MOUTH_LANDMARKS = [
    13,   # שפה עליונה
    14,   # שפה תחתונה
    0,    # חוד האף (שתייה מכוס)
    152,  # סנטר
]

# אצבעות - בודקים כמה אצבעות (לא רק אצבע מורה)
FINGERTIP_LANDMARKS = [4, 8, 12, 16, 20]  # אגודל, מורה, אמצע, קמיצה, זרת


def init_log():
    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["timestamp", "date", "hour", "distance", "smoothed_distance"])


def log_event(dist, smooth_dist):
    now = datetime.now()
    with open(LOG_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            now.isoformat(),
            now.strftime("%Y-%m-%d"),
            now.strftime("%H:%M"),
            f"{dist:.4f}",
            f"{smooth_dist:.4f}"
        ])


def show_red_frame():
    """מסגרת אדומה מהבהבת על כל המסך - 3 הבהובים"""
    def create_ui():
        for _ in range(3):
            root = tk.Tk()
            w, h = root.winfo_screenwidth(), root.winfo_screenheight()
            root.geometry(f"{w}x{h}+0+0")
            root.overrideredirect(True)
            root.attributes("-topmost", True)
            root.attributes("-transparentcolor", "white")
            root.configure(background="white")

            canvas = tk.Canvas(root, width=w, height=h, bg="white", highlightthickness=0)
            canvas.pack()
            canvas.create_rectangle(0, 0, w, h, outline="red", width=BORDER_WIDTH)

            root.after(200, root.destroy)
            root.mainloop()
            time.sleep(0.1)

    threading.Thread(target=create_ui, daemon=True).start()


def dist_to_zone(finger, face_landmarks, zone_ids):
    """מרחק מינימלי מאצבע לאזור מסוים בפנים"""
    min_d = 999
    for lid in zone_ids:
        lm = face_landmarks[lid]
        d = np.sqrt((finger.x - lm.x) ** 2 + (finger.y - lm.y) ** 2)
        if d < min_d:
            min_d = d
    return min_d


def is_hand_in_hair_zone(hand_landmarks, face_landmarks):
    """
    בודק אם יד נמצאת באזור השיער ולא באזור הפה.
    מחזיר (True/False, מרחק_מינימלי_לשיער)
    """
    min_hair_dist = 999

    for tip_id in FINGERTIP_LANDMARKS:
        finger = hand_landmarks[tip_id]

        # מרחק לאזור שיער
        hair_dist = dist_to_zone(finger, face_landmarks, HAIR_ZONE_LANDMARKS)
        # מרחק לאזור פה
        mouth_dist = dist_to_zone(finger, face_landmarks, MOUTH_LANDMARKS)

        if hair_dist < min_hair_dist:
            min_hair_dist = hair_dist

        # אם האצבע קרובה לשיער וגם רחוקה מהפה = נגיעה בשיער
        if hair_dist < HAIR_THRESHOLD and mouth_dist > hair_dist * 1.3:
            return True, min_hair_dist

    return False, min_hair_dist


def auto_update_check():
    """בודק עדכונים מ-GitHub ברקע"""
    try:
        updater = os.path.join(os.path.dirname(os.path.abspath(__file__)), "auto_update.py")
        if os.path.exists(updater):
            subprocess.Popen(
                [sys.executable, updater],
                creationflags=0x08000000 if sys.platform == "win32" else 0  # CREATE_NO_WINDOW
            )
    except Exception:
        pass


def main():
    init_log()
    # בדיקת עדכון ברקע
    threading.Thread(target=auto_update_check, daemon=True).start()

    mp_hands = mp.solutions.hands
    mp_face = mp.solutions.face_mesh
    hands = mp_hands.Hands(max_num_hands=2, min_detection_confidence=0.7)
    face_mesh = mp_face.FaceMesh(min_detection_confidence=0.7)
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        sys.exit(1)

    last_alert = 0
    dist_history = []
    event_count = 0

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                time.sleep(1)
                continue

            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h_res = hands.process(rgb_frame)
            f_res = face_mesh.process(rgb_frame)

            if h_res.multi_hand_landmarks and f_res.multi_face_landmarks:
                face_lms = f_res.multi_face_landmarks[0].landmark
                triggered = False
                best_dist = 999

                # בודק כל יד שמזוהה
                for hand_lms in h_res.multi_hand_landmarks:
                    in_hair, hair_dist = is_hand_in_hair_zone(
                        hand_lms.landmark, face_lms
                    )
                    if hair_dist < best_dist:
                        best_dist = hair_dist
                    if in_hair:
                        triggered = True

                # Low-pass filter
                dist_history.append(best_dist)
                if len(dist_history) > HISTORY_SIZE:
                    dist_history.pop(0)
                smooth_dist = sum(dist_history) / len(dist_history)

                if triggered and smooth_dist < HAIR_THRESHOLD and (time.time() - last_alert) > COOLDOWN:
                    show_red_frame()
                    log_event(best_dist, smooth_dist)
                    event_count += 1
                    last_alert = time.time()
            else:
                dist_history.clear()

            time.sleep(0.03)

    except KeyboardInterrupt:
        pass
    finally:
        cap.release()


if __name__ == "__main__":
    main()
