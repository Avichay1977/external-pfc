"""
External PFC - Android Edition (Pydroid 3)
רטט רק כשיד נוגעת באזור השיער. מתעלם מאכילה/שתייה.
"""

import cv2
import mediapipe as mp
import numpy as np
import time
import csv
import os
from datetime import datetime

try:
    from plyer import vibrator
    HAS_VIBRATOR = True
except ImportError:
    HAS_VIBRATOR = False
    print("plyer לא מותקן - רטט לא יעבוד. התקן: pip install plyer")

# --- הגדרות ---
HAIR_THRESHOLD = 0.12
COOLDOWN = 0.8
HISTORY_SIZE = 5
VIBRATE_MS = 0.3

LOG_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(LOG_DIR, "pfc_log.csv")

# אזור שיער: מצח, רקות, קודקוד
HAIR_ZONE_LANDMARKS = [10, 151, 70, 300, 234, 454, 21, 251]
# אזור פה - אכילה/שתייה
MOUTH_LANDMARKS = [13, 14, 0, 152]
# כל האצבעות
FINGERTIP_LANDMARKS = [4, 8, 12, 16, 20]


def init_log():
    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, "w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow(["timestamp", "date", "hour", "distance", "smoothed_distance"])


def log_event(dist, smooth_dist):
    now = datetime.now()
    with open(LOG_FILE, "a", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow([
            now.isoformat(), now.strftime("%Y-%m-%d"), now.strftime("%H:%M"),
            f"{dist:.4f}", f"{smooth_dist:.4f}"
        ])


def do_vibrate():
    if HAS_VIBRATOR:
        try:
            vibrator.vibrate(time=VIBRATE_MS)
        except Exception:
            pass


def dist_to_zone(finger, face_landmarks, zone_ids):
    min_d = 999
    for lid in zone_ids:
        lm = face_landmarks[lid]
        d = np.sqrt((finger.x - lm.x) ** 2 + (finger.y - lm.y) ** 2)
        if d < min_d:
            min_d = d
    return min_d


def is_hand_in_hair_zone(hand_landmarks, face_landmarks):
    min_hair_dist = 999
    for tip_id in FINGERTIP_LANDMARKS:
        finger = hand_landmarks[tip_id]
        hair_dist = dist_to_zone(finger, face_landmarks, HAIR_ZONE_LANDMARKS)
        mouth_dist = dist_to_zone(finger, face_landmarks, MOUTH_LANDMARKS)
        if hair_dist < min_hair_dist:
            min_hair_dist = hair_dist
        if hair_dist < HAIR_THRESHOLD and mouth_dist > hair_dist * 1.3:
            return True, min_hair_dist
    return False, min_hair_dist


def main():
    init_log()
    print("External PFC (Android) - מופעל")
    print(f"לוג: {LOG_FILE}")

    hands = mp.solutions.hands.Hands(max_num_hands=2, min_detection_confidence=0.7)
    face_mesh = mp.solutions.face_mesh.FaceMesh(min_detection_confidence=0.7)

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        cap = cv2.VideoCapture(1)
    if not cap.isOpened():
        print("שגיאה: לא ניתן לפתוח מצלמה")
        return

    last_alert = 0
    dist_history = []
    event_count = 0

    try:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                time.sleep(1)
                continue

            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h_res = hands.process(rgb)
            f_res = face_mesh.process(rgb)

            if h_res.multi_hand_landmarks and f_res.multi_face_landmarks:
                face_lms = f_res.multi_face_landmarks[0].landmark
                triggered = False
                best_dist = 999

                for hand_lms in h_res.multi_hand_landmarks:
                    in_hair, hair_dist = is_hand_in_hair_zone(hand_lms.landmark, face_lms)
                    if hair_dist < best_dist:
                        best_dist = hair_dist
                    if in_hair:
                        triggered = True

                dist_history.append(best_dist)
                if len(dist_history) > HISTORY_SIZE:
                    dist_history.pop(0)
                smooth_dist = sum(dist_history) / len(dist_history)

                if triggered and smooth_dist < HAIR_THRESHOLD and (time.time() - last_alert) > COOLDOWN:
                    do_vibrate()
                    log_event(best_dist, smooth_dist)
                    event_count += 1
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] התראה #{event_count}")
                    last_alert = time.time()
            else:
                dist_history.clear()

            time.sleep(0.01)

    except KeyboardInterrupt:
        pass
    finally:
        cap.release()
        print(f"\nסה\"כ {event_count} התראות. לוג: {LOG_FILE}")


if __name__ == "__main__":
    main()
