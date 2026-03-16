"""
External PFC - Windows Edition v2
זיהוי תלת-מימדי מדויק של נגיעה בשיער.
- 3D distance (X,Y + weighted Z)
- בדיקת תנוחת אצבעות (אחיזה/תלישה vs יד פתוחה)
- אזור Y מוחלט: רק מעל קו העיניים = שיער
- מתעלם מאכילה/שתייה/גירוד אף
- Auto-restart + auto-update
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
HAIR_THRESHOLD = 0.13  # סף מרחק 3D לאזור שיער
COOLDOWN = 0.8
BORDER_WIDTH = 40
HISTORY_SIZE = 5
Z_WEIGHT = 0.5  # משקל ציר Z (פחות אמין מ-X,Y ב-MediaPipe)
LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pfc_log.csv")

# --- Face Mesh landmarks ---
# אזור שיער: מצח, רקות, קודקוד
HAIR_ZONE_LANDMARKS = [
    10,   # קודקוד
    151,  # מצח מרכז
    70,   # גבה שמאל חיצוני
    300,  # גבה ימין חיצוני
    234,  # רקה שמאל
    454,  # רקה ימין
    21,   # מצח שמאל
    251,  # מצח ימין
    71,   # מצח שמאל תחתון
    301,  # מצח ימין תחתון
    109,  # רקה שמאל עליונה
    338,  # רקה ימין עליונה
]

# אזור פה/אף - אכילה/שתייה/גירוד
MOUTH_LANDMARKS = [
    13,   # שפה עליונה
    14,   # שפה תחתונה
    0,    # חוד האף
    152,  # סנטר
    17,   # שפה תחתונה מרכז
    61,   # זווית פה שמאל
    291,  # זווית פה ימין
]

# קו העיניים - Y reference (מה שמתחת = לא שיער)
EYE_TOP_LANDMARKS = [159, 386]  # גבה שמאל מרכז, גבה ימין מרכז

# אצבעות - קצוות ומפרקים
FINGERTIP_IDS = [4, 8, 12, 16, 20]       # קצות
FINGER_MCP_IDS = [2, 5, 9, 13, 17]       # בסיס אצבעות
FINGER_PIP_IDS = [3, 6, 10, 14, 18]      # מפרק אמצעי


def init_log():
    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, "w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow(["timestamp", "date", "hour", "distance", "smoothed", "zone"])


def log_event(dist, smooth_dist, zone="hair"):
    now = datetime.now()
    with open(LOG_FILE, "a", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow([
            now.isoformat(), now.strftime("%Y-%m-%d"), now.strftime("%H:%M"),
            f"{dist:.4f}", f"{smooth_dist:.4f}", zone
        ])


def show_red_frame():
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


def dist_3d(p1, p2):
    """מרחק 3D משוקלל - Z עם משקל מופחת"""
    return np.sqrt(
        (p1.x - p2.x) ** 2 +
        (p1.y - p2.y) ** 2 +
        (Z_WEIGHT * (p1.z - p2.z)) ** 2
    )


def min_dist_to_zone(finger, face_landmarks, zone_ids):
    """מרחק מינימלי 3D מאצבע לאזור"""
    return min(dist_3d(finger, face_landmarks[lid]) for lid in zone_ids)


def get_eye_line_y(face_landmarks):
    """מחזיר Y ממוצע של קו הגבות - מה שמעל = אזור שיער"""
    return np.mean([face_landmarks[lid].y for lid in EYE_TOP_LANDMARKS])


def is_pinch_or_pull_pose(hand_landmarks):
    """
    בודק אם היד בתנוחת תלישה/צביטה:
    - אצבעות מכופפות (קצה קרוב לבסיס)
    - או אגודל+מורה קרובים (צביטה)
    מחזיר ציון 0-1 (1 = תנוחת תלישה ברורה)
    """
    tips = [hand_landmarks[i] for i in FINGERTIP_IDS]
    mcps = [hand_landmarks[i] for i in FINGER_MCP_IDS]
    pips = [hand_landmarks[i] for i in FINGER_PIP_IDS]

    # בדיקת כיפוף: כמה אצבעות מכופפות (tip קרוב ל-pip יותר מ-tip ל-mcp)
    curled = 0
    for i in range(1, 5):  # אצבעות 1-4 (בלי אגודל)
        tip_to_mcp = dist_3d(tips[i], mcps[i])
        pip_to_mcp = dist_3d(pips[i], mcps[i])
        if tip_to_mcp < pip_to_mcp * 1.2:
            curled += 1

    # בדיקת צביטה: אגודל-מורה קרובים
    thumb_index_dist = dist_3d(tips[0], tips[1])
    pinch = 1.0 if thumb_index_dist < 0.06 else 0.0

    # ציון: צביטה או לפחות 2 אצבעות מכופפות
    curl_score = curled / 4.0
    return max(pinch, curl_score)


def is_hand_in_hair_zone(hand_landmarks, face_landmarks):
    """
    בדיקה מדויקת: יד באזור שיער?
    שלבים:
    1. מרחק 3D לאזור שיער
    2. האצבע מעל קו העיניים (Y)
    3. רחוק מאזור פה
    4. תנוחת יד תואמת תלישה
    """
    eye_y = get_eye_line_y(face_landmarks)
    min_hair_dist = 999
    best_zone = ""

    for tip_id in FINGERTIP_IDS:
        finger = hand_landmarks[tip_id]

        hair_dist = min_dist_to_zone(finger, face_landmarks, HAIR_ZONE_LANDMARKS)
        mouth_dist = min_dist_to_zone(finger, face_landmarks, MOUTH_LANDMARKS)

        if hair_dist < min_hair_dist:
            min_hair_dist = hair_dist

        # תנאי 1: קרוב לאזור שיער
        if hair_dist >= HAIR_THRESHOLD:
            continue

        # תנאי 2: רק מעל קו השיער (מצח עליון ומעלה + רקות מעל האוזן)
        hairline_y = face_landmarks[10].y  # קו שיער = קודקוד (הנקודה הגבוהה ביותר)
        forehead_mid_y = face_landmarks[151].y  # מצח מרכז
        # קו השיער = בין קודקוד למצח מרכז
        hair_line = hairline_y + (forehead_mid_y - hairline_y) * 0.4

        is_above_hairline = finger.y < hair_line
        # רקות: בגובה שמעל העיניים ומחוץ לפנים
        is_at_temples = finger.y < eye_y and (
            finger.x < face_landmarks[234].x or
            finger.x > face_landmarks[454].x
        )

        if not (is_above_hairline or is_at_temples):
            continue

        # תנאי 3: רחוק מהפה (לא אוכל/שותה)
        if mouth_dist < hair_dist * 1.2:
            continue

        # זיהוי אזור ספציפי
        forehead_dist = min_dist_to_zone(finger, face_landmarks, [10, 151, 21, 251])
        temple_dist = min_dist_to_zone(finger, face_landmarks, [234, 454, 109, 338])
        if temple_dist < forehead_dist:
            best_zone = "temple"
        else:
            best_zone = "forehead"

        return True, min_hair_dist, best_zone

    return False, min_hair_dist, ""


def auto_update_check():
    try:
        updater = os.path.join(os.path.dirname(os.path.abspath(__file__)), "auto_update.py")
        if os.path.exists(updater):
            subprocess.Popen(
                [sys.executable, updater],
                creationflags=0x08000000 if sys.platform == "win32" else 0
            )
    except Exception:
        pass


def run_monitor():
    hands = mp.solutions.hands.Hands(max_num_hands=2, min_detection_confidence=0.7)
    face_mesh = mp.solutions.face_mesh.FaceMesh(
        min_detection_confidence=0.7,
        min_tracking_confidence=0.5
    )
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        return False

    last_alert = 0
    dist_history = []
    pose_history = []

    try:
        while True:
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
                zone = ""

                for hand_lms in h_res.multi_hand_landmarks:
                    in_hair, hair_dist, detected_zone = is_hand_in_hair_zone(
                        hand_lms.landmark, face_lms
                    )
                    if hair_dist < best_dist:
                        best_dist = hair_dist
                    if in_hair:
                        # בדיקת תנוחת יד - ציון תלישה
                        pull_score = is_pinch_or_pull_pose(hand_lms.landmark)
                        pose_history.append(pull_score)
                        if len(pose_history) > HISTORY_SIZE:
                            pose_history.pop(0)

                        # מפעיל רק אם תנוחת היד מרמזת על תלישה
                        # או אם היד פשוט נוגעת בשיער (גם בלי צביטה)
                        avg_pose = sum(pose_history) / len(pose_history)
                        if avg_pose > 0.2 or hair_dist < HAIR_THRESHOLD * 0.7:
                            triggered = True
                            zone = detected_zone

                dist_history.append(best_dist)
                if len(dist_history) > HISTORY_SIZE:
                    dist_history.pop(0)
                smooth_dist = sum(dist_history) / len(dist_history)

                if triggered and smooth_dist < HAIR_THRESHOLD and (time.time() - last_alert) > COOLDOWN:
                    show_red_frame()
                    log_event(best_dist, smooth_dist, zone)
                    last_alert = time.time()
            else:
                dist_history.clear()
                pose_history.clear()

            time.sleep(0.03)

    except Exception:
        pass
    finally:
        cap.release()

    return True


def main():
    init_log()
    threading.Thread(target=auto_update_check, daemon=True).start()

    while True:
        try:
            should_restart = run_monitor()
            if not should_restart:
                time.sleep(30)
            else:
                time.sleep(5)
        except Exception:
            time.sleep(5)


if __name__ == "__main__":
    main()
