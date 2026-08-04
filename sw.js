/* منبه الصلاة — Service Worker: عمل كامل بدون إنترنت بعد أول تحميل */
const CACHE = "prayer-clock-v11";
const ASSETS = [
  "./",
  "index.html",
  "times_data.js",
  "manifest.webmanifest",
  "icon-192.png",
  "icon-512.png",
  "icon-maskable-192.png",
  "icon-maskable-512.png",
  "themes/night-t.jpg", "themes/lake-t.jpg", "themes/mihrab-t.jpg",
  "themes/sunset-t.jpg", "themes/sky-t.jpg", "themes/mist-t.jpg",
  "themes/sand-t.jpg", "themes/garden-t.jpg", "themes/violet-t.jpg",
  "themes/twilight-t.jpg",
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
  /* الإعدادات المركزية دائماً من الشبكة حتى تصل تغييرات المشرف فوراً */
  const path = new URL(e.request.url).pathname;
  const isPage = e.request.mode === "navigate" ||
                 e.request.destination === "document" ||
                 path.endsWith(".html") ||
                 path.endsWith("config.json");

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

/* إشعار الأذان: يصل من خادم الدفع حتى والتطبيق مغلق تماماً.
   أيقونة التطبيق (بحواف دائرية عبر نسخة القص الآمنة)، نص عربي بمحاذاة
   صحيحة، اهتزاز نابض، وزر إغلاق صريح. */
self.addEventListener("push", event => {
  let data = {};
  try{ data = event.data ? event.data.json() : {}; }
  catch(e){ data = { body: event.data ? event.data.text() : "" }; }

  const title = data.title || "🕌 منبه الصلاة";
  event.waitUntil(
    self.registration.showNotification(title, {
      body: data.body || "",
      icon: "icon-maskable-512.png",
      badge: "icon-192.png",
      dir: "rtl",
      lang: "ar",
      tag: "adhan-alert",
      renotify: true,
      vibrate: [300, 150, 300, 150, 300, 150, 500],
      actions: [{ action: "close", title: "إغلاق" }]
    })
  );
});

self.addEventListener("notificationclick", event => {
  event.notification.close();
  if(event.action === "close") return;   /* المستخدم ضغط إغلاق فقط */
  event.waitUntil(
    self.clients.matchAll({ type: "window", includeUncontrolled: true }).then(list => {
      for(const c of list) if("focus" in c) return c.focus();
      if(self.clients.openWindow) return self.clients.openWindow("./");
    })
  );
});
