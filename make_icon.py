# -*- coding: utf-8 -*-
"""
مولّد أيقونة تطبيق منبه الصلاة.

يرسم قوس المحراب الذهبي مع ساعة على خلفية عنابية متدرجة، ويصدّر
المقاسات التي تحتاجها أجهزة أندرويد و iOS.

الاستخدام:  python make_icon.py
            python make_icon.py صورتي.png     (لاستخدام صورة جاهزة)
"""
import sys
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).parent
SIZES = [192, 512]
SS = 4  # مضاعف لتنعيم الحواف

GOLD = (246, 221, 149, 255)
STOPS = [(0.00, (208, 30, 40)), (0.45, (142, 16, 25)), (1.00, (58, 7, 12))]


def lerp(a, b, t):
    return tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))


def grad_color(t):
    t = max(0.0, min(1.0, t))
    for i in range(len(STOPS) - 1):
        p0, c0 = STOPS[i]
        p1, c1 = STOPS[i + 1]
        if p0 <= t <= p1:
            return lerp(c0, c1, (t - p0) / (p1 - p0))
    return STOPS[-1][1]


def bezier(p0, p1, p2, p3, steps=140):
    pts = []
    for i in range(steps + 1):
        t = i / steps
        u = 1 - t
        x = u**3*p0[0] + 3*u*u*t*p1[0] + 3*u*t*t*p2[0] + t**3*p3[0]
        y = u**3*p0[1] + 3*u*u*t*p1[1] + 3*u*t*t*p2[1] + t**3*p3[1]
        pts.append((x, y))
    return pts


def stamp_path(d, pts, width, fill):
    """رسم مسار سميك بختم دوائر متلاصقة — يعطي حافة ملساء بلا تعرّجات."""
    r = width / 2.0
    def dot(x, y):
        d.ellipse([x - r, y - r, x + r, y + r], fill=fill)
    prev = pts[0]
    dot(*prev)
    for p in pts[1:]:
        dx, dy = p[0] - prev[0], p[1] - prev[1]
        dist = (dx * dx + dy * dy) ** 0.5
        n = max(1, int(dist))
        for i in range(1, n + 1):
            dot(prev[0] + dx * i / n, prev[1] + dy * i / n)
        prev = p


def mihrab_points(s):
    """نقاط قوس المحراب على لوحة 512 مضروبة في المعامل s."""
    def P(x, y):
        return (x * s, y * s)

    pts = [P(160, 396), P(160, 236)]
    pts += bezier(P(160, 236), P(160, 208), P(182, 198), P(210, 182))
    pts += bezier(P(210, 182), P(238, 166), P(250, 150), P(256, 126))
    pts += bezier(P(256, 126), P(262, 150), P(274, 166), P(302, 182))
    pts += bezier(P(302, 182), P(330, 198), P(352, 208), P(352, 236))
    pts += [P(352, 396), P(160, 396)]   # إغلاق الشكل بخط القاعدة
    return pts


def draw_icon(size):
    n = size * SS
    img = Image.new("RGBA", (n, n), STOPS[-1][1] + (255,))
    d = ImageDraw.Draw(img)

    # خلفية متدرجة من نقطة أعلى الوسط
    cx, cy = 0.5 * n, 0.30 * n
    rmax = int(((max(cx, n - cx)) ** 2 + (max(cy, n - cy)) ** 2) ** 0.5) + 2
    for r in range(rmax, 0, -2):
        d.ellipse([cx - r, cy - r, cx + r, cy + r],
                  fill=grad_color(r / rmax) + (255,))

    s = n / 512.0
    # قوس المحراب
    stamp_path(d, mihrab_points(s), 17 * s, GOLD)

    # الساعة داخل القوس
    ccx, ccy, rr = 256 * s, 292 * s, 56 * s
    d.ellipse([ccx - rr, ccy - rr, ccx + rr, ccy + rr], outline=GOLD,
              width=max(2, round(13 * s)))
    stamp_path(d, [(ccx, ccy), (ccx, ccy - 36 * s)], 12 * s, GOLD)
    stamp_path(d, [(ccx, ccy), (ccx + 30 * s, ccy + 16 * s)], 12 * s, GOLD)
    dot = 8 * s
    d.ellipse([ccx - dot, ccy - dot, ccx + dot, ccy + dot], fill=GOLD)

    return img.resize((size, size), Image.LANCZOS)


def from_photo(path):
    """قصّ صورة المستخدم مربعاً وتصديرها بكل المقاسات."""
    src = Image.open(path).convert("RGBA")
    w, h = src.size
    side = min(w, h)
    src = src.crop(((w - side) // 2, (h - side) // 2,
                    (w - side) // 2 + side, (h - side) // 2 + side))
    for s in SIZES:
        src.resize((s, s), Image.LANCZOS).save(ROOT / f"icon-{s}.png")
    print(f"تم إنشاء الأيقونات من {Path(path).name}")


def main():
    if len(sys.argv) > 1:
        from_photo(sys.argv[1])
        return
    for s in SIZES:
        draw_icon(s).save(ROOT / f"icon-{s}.png")
        print(f"icon-{s}.png ✓")


if __name__ == "__main__":
    main()
