"""
External PFC - Auto Updater
בודק עדכונים מ-GitHub אחת ליום ומעדכן בשקט
"""

import urllib.request
import os
import sys
import subprocess
import time
import hashlib

REPO = "Avichay1977/external-pfc"
BRANCH = "main"
FILES_TO_UPDATE = ["pfc_windows.py", "pfc_android.py", "pfc_ipad.html", "analyze_log.py"]
BASE_URL = f"https://raw.githubusercontent.com/{REPO}/{BRANCH}"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def file_hash(path):
    if not os.path.exists(path):
        return ""
    with open(path, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()


def check_and_update():
    updated = False
    for fname in FILES_TO_UPDATE:
        local_path = os.path.join(SCRIPT_DIR, fname)
        url = f"{BASE_URL}/{fname}"
        try:
            response = urllib.request.urlopen(url, timeout=10)
            new_content = response.read()
        except Exception:
            continue

        old_hash = file_hash(local_path)
        new_hash = hashlib.md5(new_content).hexdigest()

        if old_hash != new_hash:
            with open(local_path, "wb") as f:
                f.write(new_content)
            updated = True

    return updated


def restart_pfc():
    # Kill running PFC
    if sys.platform == "win32":
        os.system("taskkill /F /IM pythonw.exe >nul 2>&1")
        time.sleep(1)
        vbs = os.path.join(SCRIPT_DIR, "launch_pfc.vbs")
        if os.path.exists(vbs):
            subprocess.Popen(["wscript", vbs], shell=False)


if __name__ == "__main__":
    if check_and_update():
        restart_pfc()
