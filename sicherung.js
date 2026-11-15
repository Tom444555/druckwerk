// sicherung.js – alle Gerätedaten als eine Datei sichern und wiederherstellen
// localStorage: alle Schlüssel „druckwerk_*“ (GitHub-Zugang nur auf Wunsch)
// IndexedDB: „druckwerk“/modelle (eigene Modelle, STL als ArrayBuffer) und „druckwerk_fotos“/fotos (Tagebuch-Fotos als Blob)
let C = null;
const DBS = [{name: "druckwerk", store: "modelle", key: {keyPath: "id"}}, {name: "druckwerk_fotos", store: "fotos", key: undefined}];

// gleiche Version + gleicher Speicher wie werkstatt.js / tagebuch.js – sonst fehlt dort später der Speicher
function dbOeffnen(x){
  return new Promise((ok, fehler) => { try {
    const r = indexedDB.open(x.name, 1);
    r.onupgradeneeded = () => { if (!r.result.objectStoreNames.contains(x.store)) r.result.createObjectStore(x.store, x.key); };
    r.onsuccess = () => ok(r.result); r.onerror = () => fehler(r.error);
  } catch (e) { fehler(e); } });
}
async function alleLesen(x){
  const d = await dbOeffnen(x);
  return new Promise((ok, fehler) => { const t = d.transaction(x.store, "readonly"), st = t.objectStore(x.store), w = st.getAll(), k = st.getAllKeys();
    t.oncomplete = () => { d.close(); ok(k.result.map((key, i) => [key, w.result[i]])); }; t.onerror = () => { d.close(); fehler(t.error); }; });
}
async function schreiben(x, paare){
  const d = await dbOeffnen(x);
  return new Promise((ok, fehler) => { const t = d.transaction(x.store, "readwrite"), st = t.objectStore(x.store);
    for (const [key, v] of paare) x.key ? st.put(v) : st.put(v, key);
    t.oncomplete = () => { d.close(); ok(); }; t.onerror = () => { d.close(); fehler(t.error); }; });
}
const zuB64 = buf => { const u = new Uint8Array(buf); let s = ""; for (let i = 0; i < u.length; i += 32768) s += String.fromCharCode.apply(null, u.subarray(i, i + 32768)); return btoa(s); };
const ausB64 = b => { const s = atob(b), u = new Uint8Array(s.length); for (let i = 0; i < s.length; i++) u[i] = s.charCodeAt(i); return u.buffer; };
// Werte JSON-fähig machen: ArrayBuffer / Blob → {$buf}/{$blob}
async function packen(v){
  if (v instanceof ArrayBuffer) return {$buf: zuB64(v)};
  if (ArrayBuffer.isView(v)) return {$buf: zuB64(v.buffer.slice(v.byteOffset, v.byteOffset + v.byteLength))};
  if (typeof Blob !== "undefined" && v instanceof Blob) return {$blob: zuB64(await v.arrayBuffer()), typ: v.type};
  if (Array.isArray(v)) return Promise.all(v.map(packen));
  if (v && typeof v === "object") { const o = {}; for (const [k, x] of Object.entries(v)) o[k] = await packen(x); return o; }
  return v;
}
function auspacken(v){
  if (Array.isArray(v)) return v.map(auspacken);
  if (v && typeof v === "object") {
    if (typeof v.$buf === "string") return ausB64(v.$buf);
    if (typeof v.$blob === "string") return new Blob([ausB64(v.$blob)], {type: v.typ || ""});
    const o = {}; for (const [k, x] of Object.entries(v)) o[k] = auspacken(x); return o;
  }
  return v;
}
const lokal = mitToken => { const o = {}; try { for (let i = 0; i < localStorage.length; i++) { const k = localStorage.key(i);
  if (k.startsWith("druckwerk_") && (mitToken || k !== "druckwerk_token")) o[k] = localStorage.getItem(k); } } catch (e) {} return o; };
const anzahl = (L, k) => { try { const v = JSON.parse(L[k] || "null"); return Array.isArray(v) ? v.length : v ? Object.keys(v).length : 0; } catch (e) { return 0; } };
const kb = n => n > 1048576 ? (n / 1048576).toFixed(1).replace(".", ",") + " MB" : Math.max(1, Math.round(n / 1024)) + " KB";

export async function sichern(ctx){
  C = ctx;
  const L0 = lokal(false);
  const d = C.sheet(`<h3>Sicherung erstellen</h3><p>Eine Datei mit allen Daten dieses Geräts.</p>
    <div class="card">
      <div class="row"><div class="grow">Aufträge</div><span class="val">${anzahl(L0, "druckwerk_meine")}</span></div>
      <div class="row"><div class="grow">Spulen</div><span class="val">${anzahl(L0, "druckwerk_spulen")}</span></div>
      <div class="row"><div class="grow">Tagebuch-Einträge</div><span class="val">${anzahl(L0, "druckwerk_tagebuch")}</span></div>
      <div class="row"><div class="grow">Eigene Modelle · Fotos</div><span class="val" id="siIdb">…</span></div>
      ${"druckwerk_token" in lokal(true) ? `<div class="row"><div class="grow">GitHub-Zugang mitsichern<div class="small">nur, wenn die Datei sicher bleibt</div></div><input type="checkbox" id="siTok"></div>` : ""}
    </div>
    <div style="height:14px"></div><button class="btn" id="siOk">Sicherung speichern</button><button class="btn grey" id="siZu">Abbrechen</button>`);
  const q = s => d.querySelector(s);
  q("#siZu").onclick = () => d.remove();
  const idb = {};
  for (const x of DBS) { try { idb[x.name] = await alleLesen(x); } catch (e) { idb[x.name] = []; } }
  if (q("#siIdb")) q("#siIdb").textContent = `${idb.druckwerk.length} · ${idb.druckwerk_fotos.length}`;
  q("#siOk").onclick = async () => {
    q("#siOk").textContent = "Wird erstellt …";
    try {
      const daten = {app: "druckwerk", format: 1, erstellt: new Date().toISOString(), lokal: lokal(!!(q("#siTok") && q("#siTok").checked)), idb: {}};
      for (const x of DBS) daten.idb[x.name] = await packen(idb[x.name]);
      const text = JSON.stringify(daten), name = `druckwerk-sicherung-${new Date().toISOString().slice(0, 10)}.json`;
      const datei = new File([text], name, {type: "application/json"});
      let geteilt = false;
      try { if (navigator.canShare && navigator.canShare({files: [datei]})) { await navigator.share({files: [datei], title: "Druckwerk-Sicherung"}); geteilt = true; } }
      catch (e) { if (e && e.name === "AbortError") { q("#siOk").textContent = "Sicherung speichern"; return; } }
      if (!geteilt) { const u = URL.createObjectURL(datei), a = document.createElement("a"); a.href = u; a.download = name; document.body.appendChild(a); a.click(); a.remove(); setTimeout(() => URL.revokeObjectURL(u), 20000); }
      try { localStorage.setItem("druckwerk_gesichert", JSON.stringify(new Date().toISOString().slice(0, 10))); } catch (e) {}
      d.remove(); C.toast(`Sicherung erstellt (${kb(text.length)})`);
    } catch (e) { console.error(e); q("#siOk").textContent = "Sicherung speichern"; C.toast("Sicherung fehlgeschlagen"); }
  };
}

export async function wiederherstellen(datei, ctx){
  C = ctx;
  let D = null;
  try { D = JSON.parse(await datei.text()); if (!D || D.app !== "druckwerk" || !D.lokal) throw 0; }
  catch (e) { return C.toast("Keine Druckwerk-Sicherung"); }
  const L = D.lokal, idb = D.idb || {};
  const d = C.sheet(`<h3>Sicherung wiederherstellen?</h3><p>vom ${C.deDatum(String(D.erstellt || "").slice(0, 10))}</p>
    <div class="card">
      <div class="row"><div class="grow">Aufträge</div><span class="val">${anzahl(L, "druckwerk_meine")}</span></div>
      <div class="row"><div class="grow">Spulen</div><span class="val">${anzahl(L, "druckwerk_spulen")}</span></div>
      <div class="row"><div class="grow">Tagebuch-Einträge</div><span class="val">${anzahl(L, "druckwerk_tagebuch")}</span></div>
      <div class="row"><div class="grow">Eigene Modelle · Fotos</div><span class="val">${(idb.druckwerk || []).length} · ${(idb.druckwerk_fotos || []).length}</span></div>
    </div>
    <p class="hint">Aufträge werden mit deiner Liste zusammengeführt. Spulen, Tagebuch, Einrichtung und Wartung kommen aus der Sicherung (die Werte auf diesem Gerät werden ersetzt). Modelle und Fotos kommen dazu.</p>
    <div style="height:14px"></div><button class="btn" id="wOk">Wiederherstellen</button><button class="btn grey" id="wZu">Abbrechen</button>`);
  d.querySelector("#wZu").onclick = () => d.remove();
  d.querySelector("#wOk").onclick = async () => {
    try {
      for (const [k, v] of Object.entries(L)) {
        if (!k.startsWith("druckwerk_") || typeof v !== "string") continue;
        if (k === "druckwerk_meine") {           // zusammenführen statt überschreiben
          let alt = []; try { alt = JSON.parse(localStorage.getItem(k) || "[]"); } catch (e) {}
          const neu = JSON.parse(v); for (const a of alt) if (!neu.some(x => x.ordner === a.ordner)) neu.push(a);
          neu.sort((x, y) => (y.datum + y.ordner).localeCompare(x.datum + x.ordner));
          localStorage.setItem(k, JSON.stringify(neu));
        } else if (k === "druckwerk_gedruckt") {
          let alt = {}; try { alt = JSON.parse(localStorage.getItem(k) || "{}"); } catch (e) {}
          localStorage.setItem(k, JSON.stringify({...alt, ...JSON.parse(v)}));
        } else localStorage.setItem(k, v);
      }
      for (const x of DBS) if (Array.isArray(idb[x.name]) && idb[x.name].length) await schreiben(x, auspacken(idb[x.name]));
      d.remove(); if (C.neuLaden) C.neuLaden(); C.toast("Wiederhergestellt"); C.go("start");
    } catch (e) { console.error(e); C.toast(/Quota/i.test(String(e && e.name)) ? "Speicher voll – nicht alles wiederhergestellt" : "Wiederherstellen fehlgeschlagen"); }
  };
}
