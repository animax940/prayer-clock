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


def fill_rounded_corners(img, white_thr=205):
    """
    كثير من الأيقونات الجاهزة تأتي بزوايا بيضاء خارج المربع المستدير.

    نحدّد المنطقة البيضاء المتصلة بالزوايا فقط (حتى لا نمسّ العناصر الفاتحة
    داخل التصميم)، ثم نملؤها بامتداد ألوان الحافة المجاورة لتبدو طبيعية.
    """
    from collections import deque

    px = img.load()
    n = img.size[0]
    is_white = lambda p: p[0] >= white_thr and p[1] >= white_thr and p[2] >= white_thr

    # 1) تحديد البياض المتصل بالزوايا
    outside = bytearray(n * n)
    q = deque()
    for sx, sy in ((0, 0), (n-1, 0), (0, n-1), (n-1, n-1)):
        if is_white(px[sx, sy]) and not outside[sy*n + sx]:
            outside[sy*n + sx] = 1
            q.append((sx, sy))
    while q:
        x, y = q.popleft()
        for nx, ny in ((x+1, y), (x-1, y), (x, y+1), (x, y-1)):
            if 0 <= nx < n and 0 <= ny < n and not outside[ny*n + nx] \
                    and is_white(px[nx, ny]):
                outside[ny*n + nx] = 1
                q.append((nx, ny))
    total = sum(outside)
    if not total:
        return 0

    # 2) تعبئة تدريجية من الحافة إلى الداخل بلون الجار السليم
    q = deque()
    for i in range(n * n):
        if not outside[i]:
            continue
        x, y = i % n, i // n
        for nx, ny in ((x+1, y), (x-1, y), (x, y+1), (x, y-1)):
            if 0 <= nx < n and 0 <= ny < n and not outside[ny*n + nx]:
                q.append((x, y, nx, ny))
                break
    while q:
        x, y, sx, sy = q.popleft()
        if not outside[y*n + x]:
            continue
        px[x, y] = px[sx, sy]
        outside[y*n + x] = 0
        for nx, ny in ((x+1, y), (x-1, y), (x, y+1), (x, y-1)):
            if 0 <= nx < n and 0 <= ny < n and outside[ny*n + nx]:
                q.append((nx, ny, x, y))
    return total


def from_photo(path):
    """تحويل صورة جاهزة إلى أيقونات التطبيق بكل المقاسات."""
    src = Image.open(path).convert("RGBA")
    w, h = src.size
    side = min(w, h)
    src = src.crop(((w - side) // 2, (h - side) // 2,
                    (w - side) // 2 + side, (h - side) // 2 + side))

    # الزوايا الشفافة مطلوبة في الأيقونات، فلا نعالجها إلا إن كانت بيضاء صلبة
    if src.getpixel((1, 1))[3] > 250:
        fixed = fill_rounded_corners(src)
        print(f"معالجة الزوايا البيضاء: {fixed} بكسل")
    else:
        print("الزوايا شفافة أصلاً — تُركت كما هي")

    # لون الخلفية للنسخة المحمية من القص (من منتصف الحافة العليا)
    base = src.getpixel((side // 2, int(side * 0.02)))[:3]

    for s in SIZES:
        src.resize((s, s), Image.LANCZOS).save(ROOT / f"icon-{s}.png")
        # نسخة أندرويد القابلة للقص: المحتوى داخل 78% حتى لا يُقصّ الإطار
        m = Image.new("RGBA", (s, s), base + (255,))
        inner = round(s * 0.78)
        small = src.resize((inner, inner), Image.LANCZOS)
        # نمرر الصورة كقناع حتى تُدمج الزوايا الشفافة مع الخلفية بدل أن تُنسخ
        m.paste(small, ((s - inner) // 2, (s - inner) // 2), small)
        m.save(ROOT / f"icon-maskable-{s}.png")
        print(f"icon-{s}.png + icon-maskable-{s}.png ✓")
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
