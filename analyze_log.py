"""
External PFC - Log Analyzer
ניתוח לוג CSV למציאת דפוסים וקורלציות לשעות עבודה
"""

import csv
import os
from collections import defaultdict
from datetime import datetime

LOG_FILE = os.path.join(os.path.dirname(__file__), "pfc_log.csv")


def analyze():
    if not os.path.exists(LOG_FILE):
        print("אין קובץ לוג עדיין. הפעל את PFC קודם.")
        return

    events = []
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            events.append(row)

    if not events:
        print("הלוג ריק.")
        return

    total = len(events)
    print(f"=== ניתוח PFC Log ===")
    print(f"סה\"כ אירועים: {total}")
    print()

    # התפלגות לפי שעות
    by_hour = defaultdict(int)
    for e in events:
        hour = e["hour"].split(":")[0]
        by_hour[hour] += 1

    print("התפלגות לפי שעות:")
    for hour in sorted(by_hour.keys()):
        count = by_hour[hour]
        bar = "█" * count
        print(f"  {hour}:00  {bar} ({count})")
    print()

    # התפלגות לפי ימים
    by_date = defaultdict(int)
    for e in events:
        by_date[e["date"]] += 1

    print("התפלגות לפי ימים:")
    for date in sorted(by_date.keys()):
        count = by_date[date]
        bar = "█" * min(count, 50)
        print(f"  {date}  {bar} ({count})")
    print()

    # שעות שיא
    if by_hour:
        peak_hour = max(by_hour, key=by_hour.get)
        print(f"שעת שיא: {peak_hour}:00 ({by_hour[peak_hour]} אירועים)")

    # ממוצע יומי
    if by_date:
        avg_daily = total / len(by_date)
        print(f"ממוצע יומי: {avg_daily:.1f} אירועים")

    # מגמה - 3 ימים אחרונים vs 3 ימים ראשונים
    dates = sorted(by_date.keys())
    if len(dates) >= 6:
        first3 = sum(by_date[d] for d in dates[:3]) / 3
        last3 = sum(by_date[d] for d in dates[-3:]) / 3
        change = ((last3 - first3) / first3) * 100 if first3 > 0 else 0
        direction = "ירידה" if change < 0 else "עלייה"
        print(f"מגמה: {direction} של {abs(change):.0f}% (3 ימים אחרונים vs ראשונים)")


if __name__ == "__main__":
    analyze()
