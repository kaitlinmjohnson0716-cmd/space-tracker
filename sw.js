/* Online: data files come from the network (and are saved).
   Offline: the app shell and the last saved data files are served. */
const CACHE = "space-tracker-v1";
const SHELL = ["./", "index.html", "browse.html", "trends.html", "style.css", "common.js",
  "vendor/chart.umd.min.js", "manifest.webmanifest", "icon-192.png", "icon-512.png",
  "data/history.csv", "data/status.json"];

self.addEventListener("install", e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(SHELL)).then(() => self.skipWaiting()));
});
self.addEventListener("activate", e => {
  e.waitUntil(caches.keys().then(keys => Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k))))
    .then(() => self.clients.claim()));
});
self.addEventListener("fetch", e => {
  if (e.request.method !== "GET") return;
  const url = new URL(e.request.url);
  if (url.origin !== location.origin) return;
  const networkFirst = url.pathname.includes("/data/") || e.request.mode === "navigate" ||
    /\.(html|js|css)$/.test(url.pathname);
  if (networkFirst) {
    e.respondWith(fetch(e.request).then(resp => {
      const copy = resp.clone();
      caches.open(CACHE).then(c => c.put(e.request, copy));
      return resp;
    }).catch(() => caches.match(e.request).then(r => r || caches.match("index.html"))));
  } else {
    e.respondWith(caches.match(e.request).then(r => r || fetch(e.request)));
  }
});
