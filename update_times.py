# -*- coding: utf-8 -*-
"""
محدّث تقويم أوقات الصلاة — منبه الصلاة
يجلب جداول أوقات الصلاة السنوية (المطابقة لتقويم وزارة الأوقاف والشؤون
الدينية العُمانية) لجميع الولايات، ويحفظها في مجلد times/ بجانب التطبيق،
ثم يولّد ملف times_data.js المدمج لاستخدامه بدون خادم.

الاستخدام:  python update_times.py            (تنزيل + توليد الملفات)
           python update_times.py --pack-only (توليد الملفات من times/ فقط)
"""
import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

SOURCE = "https://almanarah.live/times"   # مرآة عامة لتقويم الوزارة
OUT_DIR = Path(__file__).parent / "times"
HEADERS = {"User-Agent": "PrayerClock/1.0 (personal prayer times app)"}


def fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()


def main() -> None:
    OUT_DIR.mkdir(exist_ok=True)

    raw = fetch(f"{SOURCE}/cities.json")
    cities = list(dict.fromkeys(json.loads(raw.decode("utf-8"))))
    (OUT_DIR / "cities.json").write_bytes(
        json.dumps(cities, ensure_ascii=False).encode("utf-8"))
    print(f"المدن: {len(cities)}")

    all_data = {}
    for i, city in enumerate(cities, 1):
        fname = f"{city}_times.json"
        url = f"{SOURCE}/{urllib.parse.quote(fname)}"
        try:
            data = fetch(url)
            table = json.loads(data.decode("utf-8"))
            (OUT_DIR / fname).write_bytes(
                json.dumps(table, ensure_ascii=False,
                           separators=(",", ":")).encode("utf-8"))
            all_data[city] = table
            print(f"[{i}/{len(cities)}] {city} ✓")
        except Exception as exc:
            print(f"[{i}/{len(cities)}] {city} ✗ ({exc})")
        time.sleep(0.15)   # مهلة مهذبة بين الطلبات

    emit(all_data)


MONTH_DAYS = [31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]


def emit(all_data: dict) -> None:
    root = Path(__file__).parent
    # ملف مدمج يعمل بدون خادم (يُحمَّل عبر <script src="times_data.js">)
    js = ("// جداول أوقات الصلاة لجميع الولايات — يُحدَّث بتشغيل update_times.py\n"
          "window.TIMES_DATA = "
          + json.dumps(all_data, ensure_ascii=False, separators=(",", ":"))
          + ";\n")
    (root / "times_data.js").write_text(js, encoding="utf-8")
    print(f"times_data.js: {len(js.encode('utf-8'))//1024} KB — {len(all_data)} ولاية")

    # حزمة مضغوطة للنسخة المستضافة: لكل ولاية سلسلة 366 يوماً × 24 رقماً
    pack = {}
    for city, table in all_data.items():
        buf, prev = [], "0000" * 6
        for m in range(1, 13):
            for d in range(1, MONTH_DAYS[m - 1] + 1):
                row = table.get(f"{d}/{m}")
                seg = "".join(t.replace(":", "") for t in row) if row else prev
                buf.append(seg)
                prev = seg
        pack[city] = "".join(buf)
    pjs = ("// حزمة مضغوطة لأوقات الصلاة (366 يوم × 24 رقم لكل ولاية)\n"
           "window.TIMES_PACK = "
           + json.dumps(pack, ensure_ascii=False, separators=(",", ":"))
           + ";\n")
    (root / "times_pack.js").write_text(pjs, encoding="utf-8")
    print(f"times_pack.js: {len(pjs.encode('utf-8'))//1024} KB")


def pack_only() -> None:
    all_data = {}
    for f in OUT_DIR.glob("*_times.json"):
        city = f.name[:-len("_times.json")]
        all_data[city] = json.loads(f.read_text(encoding="utf-8"))
    emit(all_data)


if __name__ == "__main__":
    if "--pack-only" in sys.argv:
        pack_only()
    else:
        main()
