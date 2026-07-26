/* منبه الصلاة — Service Worker: عمل كامل بدون إنترنت بعد أول تحميل */
const CACHE = "prayer-clock-v5";
const ASSETS = [
  "./",
  "index.html",
  "times_data.js",
  "manifest.webmanifest",
  "icon.svg",
  "sounds/adhan1.mp3",
  "sounds/adhan2.mp3"
];

self.addEventListener("install", e => {
  e.waitUntil(
    caches.open(CACHE).then(c => c.addAll(ASSETS)).then(() => self.skipWaiting())
  );
});

self.addEventListener("activate", e => {
  e.waitUntil(
    caches.keys()
      .then(ks => Promise.all(ks.filter(k => k !== CACHE).map(k => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

/* الصفحة نفسها: الشبكة أولاً حتى تصل التحديثات، والذاكرة عند انقطاع الإنترنت.
   بقية الملفات (الأصوات والجداول): الذاكرة أولاً للسرعة. */
self.addEventListener("fetch", e => {
  if (e.request.method !== "GET") return;
  /* الطلبات الخارجية (مثل خدمة العناوين) تذهب للشبكة مباشرة — تخزينها
     يخلط النتائج لأن التخزين هنا يتجاهل معاملات الرابط. */
  if (new URL(e.request.url).origin !== self.location.origin) return;
  const isPage = e.request.mode === "navigate" ||
                 e.request.destination === "document" ||
                 new URL(e.request.url).pathname.endsWith(".html");

  if (isPage) {
    e.respondWith(
      fetch(e.request).then(res => {
        const clone = res.clone();
        caches.open(CACHE).then(c => c.put(e.request, clone));
        return res;
      }).catch(() =>
        caches.match(e.request, { ignoreSearch: true })
          .then(hit => hit || caches.match("index.html"))
      )
    );
    return;
  }

  e.respondWith(
    caches.match(e.request, { ignoreSearch: true }).then(hit =>
      hit ||
      fetch(e.request).then(res => {
        const clone = res.clone();
        caches.open(CACHE).then(c => c.put(e.request, clone));
        return res;
      }).catch(() => hit)
    )
  );
});
