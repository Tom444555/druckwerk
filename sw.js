// sw.js – Offline-Grundlage für Druckwerk (GitHub Pages unter /druckwerk/)
// Immer zuerst das Netz (Updates kommen sofort an); nur ohne Netz oder nach 5 s Funkstille aus dem Zwischenspeicher.
// Große Dateien (gcode, stl, 3mf) werden nie zwischengespeichert. three.js vom CDN (feste Version) einmal speichern.
const CACHE = "druckwerk-v5", CDN = "druckwerk-cdn-v1";
const HUELLE = ["./", "index.html", "start.js", "sicherung.js", "werkstatt.js", "ki.js", "kiweg.js", "wissen.js", "tagebuch.js", "schichten.js",
  "wissen/filamente.json", "wissen/zubehoer.json", "wissen/c5pro.json", "wissen/workflow.json", "videos/index.html", "videos/ki-stl-bastlwastl.html", "videos/foto-in-3d-bastlwastl.html",
  "drucker/c5pro.json", "drucker/kobrax.json", "auftraege/index.json", "manifest.webmanifest", "symbol-180.png", "symbol-192.png"];

self.addEventListener("install", e => {
  self.skipWaiting();
  e.waitUntil(caches.open(CACHE).then(c => Promise.all(HUELLE.map(u => c.add(new Request(u, {cache: "reload"})).catch(() => {})))));
});
self.addEventListener("activate", e => {
  e.waitUntil(caches.keys().then(k => Promise.all(k.filter(n => n !== CACHE && n !== CDN).map(n => caches.delete(n)))).then(() => self.clients.claim()));
});

const merken = p => /\/druckwerk\/?$|\.(html|js|json|webmanifest|png)$/.test(p) && !/\/(eingang|status)\//.test(p);
self.addEventListener("fetch", e => {
  const r = e.request; if (r.method !== "GET") return;
  const u = new URL(r.url);
  if (u.hostname === "cdn.jsdelivr.net" && u.pathname.startsWith("/npm/three@")) {        // feste Version → einmal laden, dann aus dem Speicher
    e.respondWith(caches.open(CDN).then(c => c.match(r).then(t => t || fetch(r).then(n => { if (n.ok) c.put(r, n.clone()); return n; }))));
    return;
  }
  if (u.origin !== location.origin) return;
  const pfad = u.pathname, klein = merken(pfad) && (!/\/auftraege\//.test(pfad) || /\/auftraege\/index\.json$|\/vorschau\.png$/.test(pfad));
  if (!klein && r.mode !== "navigate") return;                                              // große Dateien: Browser normal
  const schluessel = r.mode === "navigate" ? new Request(new URL("./", self.registration.scope)) : new Request(u.origin + u.pathname);
  e.respondWith((async () => {
    const c = await caches.open(CACHE);
    // immer beim Server nachfragen (304 ist billig) – so kommen Änderungen sofort an, auch an GitHub Pages' 10-Min.-Cache vorbei
    const frage = r.mode === "navigate" ? new Request(r.url, {cache: "no-cache", credentials: "same-origin"}) : new Request(r, {cache: r.cache === "no-store" ? "no-store" : "no-cache"});
    const netz = fetch(frage).then(n => { if (n.ok && n.type === "basic") c.put(schluessel, n.clone()); return n; });
    const alt = await c.match(schluessel);
    if (!alt) return netz;
    const warte = new Promise(ok => setTimeout(() => ok(alt), 5000));
    return Promise.race([netz.catch(() => alt), warte]);
  })());
});
