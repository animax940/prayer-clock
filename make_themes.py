# -*- coding: utf-8 -*-
"""
تجهيز خلفيات الثيمات.

المصادر في _bg_src/:
  - صور طولية منفردة بدقة عالية
  - صفحة مجمّعة (سبرايت شيت) فيها 8 بلاطات، أربع منها مكررة مع المنفردات
  - صور واجهة جاهزة تُتجاهل تماماً (مرجع ألوان فقط)

التكرار حُدّد بالفحص البصري لا بالتخمين، والاختيار مثبّت أدناه.

الاستخدام:  python make_themes.py
"""
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).parent
SRC = ROOT / "_bg_src"
OUT = ROOT / "themes"
SHEET = "bg1.png"

FULL_W, THUMB_W = 900, 160

# صور منفردة عالية الدقة: الملف -> اسم الثيم
SINGLES = {
    "bg6.png": "night",     # ليل وهلال
    "bg5.png": "sky",       # سماء زرقاء
    "bg7.png": "mist",      # صفاء فاتح
    "bg4.png": "sand",      # رمال فاتحة
    "bg3.png": "garden",    # أوراق خضراء
    "bg2.png": "violet",    # بنفسجي
}
# بلاطات فريدة من الصفحة المجمّعة: رقم البلاطة (1..8) -> اسم الثيم
SHEET_TILES = {
    2: "lake",              # ليل وبحيرة
    4: "sunset",            # غروب صحراوي
    7: "mihrab",            # محراب ذهبي
    8: "twilight",          # شفق وردي
}


def bands(length, probe):
    out, start = [], None
    for i in range(length):
        if probe(i) and start is None:
            start = i
        elif not probe(i) and start is not None:
            out.append((start, i)); start = None
    if start is not None:
        out.append((start, length))
    return out


def split_sheet(img):
    """قصّ بلاطات الصفحة المجمّعة بترتيب: صف علوي ثم سفلي، يميناً لليسار."""
    w, h = img.size
    px = img.convert("RGB").load()
    bg = px[2, 2]
    def is_bg(x, y):
        p = px[x, y]
        return abs(p[0]-bg[0]) + abs(p[1]-bg[1]) + abs(p[2]-bg[2]) < 40

    cols = [c for c in bands(w, lambda x: sum(0 if is_bg(x, y) else 1
                                              for y in range(0, h, 7)) > 3)
            if (c[1] - c[0]) >= w * 0.04]
    rowfill = [sum(0 if is_bg(x, y) else 1 for x in range(0, w, 7))
               for y in range(h)]
    content = bands(h, lambda y: rowfill[y] > 2)
    top, bottom = content[0][0], content[-1][1]
    mid = min(range(int(h*0.42), int(h*0.58)), key=lambda y: rowfill[y])
    rows = [(top, mid), (mid, bottom)]

    def trim(t):
        tp = t.convert("RGB").load(); tw, th = t.size
        near = lambda p: abs(p[0]-bg[0])+abs(p[1]-bg[1])+abs(p[2]-bg[2]) < 40
        a, b, c, d = 0, th-1, 0, tw-1
        while a < b and all(near(tp[x, a]) for x in range(0, tw, 5)): a += 1
        while b > a and all(near(tp[x, b]) for x in range(0, tw, 5)): b -= 1
        while c < d and all(near(tp[c, y]) for y in range(0, th, 5)): c += 1
        while d > c and all(near(tp[d, y]) for y in range(0, th, 5)): d -= 1
        return t.crop((c, a, d+1, b+1))

    return [trim(img.crop((x0, y0, x1, y1)))
            for y0, y1 in rows for x0, x1 in cols]


def fit(img, width):
    return img.resize((width, round(img.height * width / img.width)),
                      Image.LANCZOS)


def export(im, name):
    w = min(FULL_W, im.width * 3)
    fit(im, w).save(OUT / f"{name}.jpg", "JPEG", quality=84,
                    optimize=True, progressive=True)
    fit(im, THUMB_W).save(OUT / f"{name}-t.jpg", "JPEG", quality=78,
                          optimize=True)
    kb = (OUT / f"{name}.jpg").stat().st_size // 1024
    tkb = (OUT / f"{name}-t.jpg").stat().st_size // 1024
    print(f"{name}: {im.width}x{im.height} → {w}px، {kb}KB + {tkb}KB")
    return kb + tkb


def main():
    OUT.mkdir(exist_ok=True)
    total = 0
    for f, name in SINGLES.items():
        p = SRC / f
        if not p.exists():
            print(f"{f} ✗ غير موجود"); continue
        total += export(Image.open(p).convert("RGB"), name)

    sheet = SRC / SHEET
    if sheet.exists():
        tiles = split_sheet(Image.open(sheet).convert("RGB"))
        print(f"الصفحة المجمّعة: {len(tiles)} بلاطة، الفريد منها "
              f"{len(SHEET_TILES)}")
        for idx, name in SHEET_TILES.items():
            if idx <= len(tiles):
                total += export(tiles[idx-1], name)
    print(f"المجموع: {total}KB — {len(SINGLES)+len(SHEET_TILES)} ثيم")


if __name__ == "__main__":
    main()
