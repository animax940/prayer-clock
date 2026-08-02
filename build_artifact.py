# -*- coding: utf-8 -*-
"""
بناء نسخة مستقلة بملف واحد (للاستضافة على claude.ai).

يدمج جداول الأوقات وأصوات الأذان وصور الثيمات داخل الصفحة نفسها،
لأن تلك الاستضافة لا تسمح بتحميل أي ملف خارجي.

الاستخدام:  python build_artifact.py <ملف الإخراج>
"""
import base64
import io
import re
import sys
from pathlib import Path

ROOT = Path(__file__).parent
OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "standalone.html"

src = io.open(ROOT / "index.html", encoding="utf-8").read()
style = re.search(r"<style>.*?</style>", src, re.S).group(0)
body = re.search(r"<body>\s*(.*?)\s*</body>", src, re.S).group(1)


def b64(path, mime):
    return "data:%s;base64,%s" % (
        mime, base64.b64encode(path.read_bytes()).decode())


# جداول الأوقات المضغوطة بدل الملف الخارجي
pack = io.open(ROOT / "times_pack.js", encoding="utf-8").read()
body = body.replace('<script src="times_data.js"></script>',
                    "<script>\n%s</script>" % pack)

# أصوات الأذان
for i in (1, 2):
    body = body.replace('file:"sounds/adhan%d.mp3"' % i,
                        'file:"%s"' % b64(ROOT / "sounds" / ("adhan%d.mp3" % i),
                                          "audio/mpeg"))

# صور الثيمات (الخلفية والمصغّرة)
themes = {}
for f in sorted((ROOT / "themes").glob("*.jpg")):
    themes[f.stem] = b64(f, "image/jpeg")
inject = "<script>window.THEME_DATA=%s;</script>" % (
    "{" + ",".join('"%s":"%s"' % (k, v) for k, v in themes.items()) + "}")
body = inject + "\n" + body

# الإعدادات المركزية من الموقع المنشور
body = body.replace('const CONFIG_URL = "config.json";',
                    'const CONFIG_URL = '
                    '"https://animax940.github.io/prayer-clock/config.json";')

# ملفات الأذكار كبيرة (22-31 ميغابايت) — تُجلب من الموقع المباشر بدل
# دمجها كـ base64، حفاظاً على حجم معقول للنسخة المستضافة على claude.ai
PAGES_BASE = "https://animax940.github.io/prayer-clock/"
for rel in ("sounds/azkar_morning.mp3", "sounds/azkar_evening.mp3"):
    body = body.replace('"%s"' % rel, '"%s%s"' % (PAGES_BASE, rel))

html = "<title>منبه الصلاة</title>\n%s\n%s" % (style, body)
html = html.replace('"Cairo","Segoe UI"', '"Segoe UI"')
io.open(OUT, "w", encoding="utf-8", newline="").write(html)

print("%s: %.2f ميغابايت، %d ثيم مدمج"
      % (OUT.name, OUT.stat().st_size / 1048576, len(themes) // 2))
