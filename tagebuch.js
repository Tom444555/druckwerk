// tagebuch.js – Druck-Tagebuch: Ergebnis je Auftrag (Sterne, Mängel, Notiz, Foto)
// Texte in localStorage „druckwerk_tagebuch“, Fotos (JPEG, max. 1000 px) in IndexedDB „druckwerk_fotos“ – alles nur im Gerät.
const TB = "druckwerk_tagebuch";
export const MAENGEL = ["Haftung", "Fäden", "Farbversatz", "Verzug", "Details fehlen", "Maße stimmen nicht", "Oberfläche"];
let C = null;
const ls = (k, d) => { try { const v = JSON.parse(localStorage.getItem(k)); return v ?? d; } catch (e) { return d; } };
const lsSet = (k, v) => { try { localStorage.setItem(k, JSON.stringify(v)); return true; } catch (e) { return false; } };
export const eintraege = () => ls(TB, []);
const de = iso => iso ? iso.slice(0, 10).split("-").reverse().join(".") : "";
const sterne = n => "★".repeat(n) + "☆".repeat(5 - n);
const uniq = v => [...new Set(String(v ?? "").split(",").map(x => x.trim()))].join(" / ");

/* ---------- Fotos in IndexedDB ---------- */
let _db = null;
function db(){
  if (_db) return _db;
  return _db = new Promise((ok, fehler) => {
    try { const r = indexedDB.open("druckwerk_fotos", 1);
      r.onupgradeneeded = () => r.result.createObjectStore("fotos");
      r.onsuccess = () => ok(r.result); r.onerror = () => fehler(r.error);
    } catch (e) { fehler(e); }
  });
}
async function fotoTun(modus, fn){ const d = await db(); return new Promise((ok, fehler) => {
  const t = d.transaction("fotos", modus), st = t.objectStore("fotos"); const r = fn(st);
  t.oncomplete = () => ok(r && r.result); t.onerror = () => fehler(t.error); }); }
const fotoSichern = (id, blob) => fotoTun("readwrite", st => st.put(blob, id));
const fotoLaden = id => fotoTun("readonly", st => st.get(id)).catch(() => null);
const fotoLoeschen = id => fotoTun("readwrite", st => st.delete(id)).catch(() => null);

// Bild im Browser auf max. 1000 px Kante als JPEG verkleinern
function verkleinern(datei, max = 1000){
  return new Promise((ok, fehler) => {
    const url = URL.createObjectURL(datei), img = new Image();
    img.onload = () => { const f = Math.min(1, max / Math.max(img.naturalWidth, img.naturalHeight));
      const c = document.createElement("canvas"); c.width = Math.round(img.naturalWidth * f); c.height = Math.round(img.naturalHeight * f);
      c.getContext("2d").drawImage(img, 0, 0, c.width, c.height); URL.revokeObjectURL(url);
      c.toBlob(b => b ? ok(b) : fehler(new Error("kein Bild")), "image/jpeg", 0.85); };
    img.onerror = () => { URL.revokeObjectURL(url); fehler(new Error("Bild nicht lesbar")); };
    img.src = url;
  });
}
// Miniaturen nachladen: <img data-foto="id">
async function fotosEinsetzen(root){
  for (const el of root.querySelectorAll("img[data-foto]")) {
    const b = await fotoLaden(el.dataset.foto); if (b) { el.src = URL.createObjectURL(b); el.style.visibility = "visible"; }
  }
}

/* ---------- Neuer Eintrag (aus dem Auftrag) ---------- */
export function eintragen(a, ctx, fertig){
  C = ctx;
  const E = {note: 0, maengel: [], blob: null};
  const d = C.sheet(`<h3>Ergebnis eintragen</h3><p>${C.esc(a.name)}</p>
    <h2>Wie ist der Druck geworden?</h2>
    <div class="seg" id="tNote">${[1, 2, 3, 4, 5].map(n => `<button data-n="${n}" style="font-size:20px;color:var(--orange)">☆</button>`).join("")}</div>
    <p class="hint" style="text-align:left;margin:6px 4px 0">1 Stern = misslungen, 5 Sterne = perfekt</p>
    <h2>Mängel</h2><div class="chips">${MAENGEL.map(m => `<button class="chip" data-mg="${C.esc(m)}">${C.esc(m)}</button>`).join("")}</div>
    <h2>Notiz</h2><div class="card"><textarea id="tText" placeholder="z. B. Gold-Adern oben abgerissen, Unterseite sauber"></textarea></div>
    <h2>Foto</h2><div class="card"><div class="row">
      <img id="tVor" alt="" style="width:56px;height:56px;border-radius:8px;object-fit:cover;display:none">
      <label class="grow" style="color:var(--blue);cursor:pointer">Foto aufnehmen oder wählen
        <input type="file" accept="image/*" capture="environment" id="tFoto" style="display:none"></label></div></div>
    <div style="height:14px"></div><button class="btn" id="tOk">Sichern</button><button class="btn grey" id="tZu">Abbrechen</button>`);
  const q = s => d.querySelector(s);
  const noteZeigen = () => d.querySelectorAll("[data-n]").forEach(b => b.textContent = +b.dataset.n <= E.note ? "★" : "☆");
  d.querySelectorAll("[data-n]").forEach(b => b.onclick = () => { E.note = +b.dataset.n; noteZeigen(); });
  d.querySelectorAll("[data-mg]").forEach(b => b.onclick = () => { const m = b.dataset.mg;
    E.maengel = E.maengel.includes(m) ? E.maengel.filter(x => x !== m) : [...E.maengel, m]; b.classList.toggle("on", E.maengel.includes(m)); });
  q("#tFoto").onchange = async e => { const f = e.target.files && e.target.files[0]; if (!f) return;
    try { E.blob = await verkleinern(f); const v = q("#tVor"); v.src = URL.createObjectURL(E.blob); v.style.display = "block"; }
    catch (err) { C.toast("Foto nicht lesbar"); } };
  q("#tZu").onclick = () => d.remove();
  q("#tOk").onclick = async () => {
    if (!E.note) return C.toast("Bitte Sterne vergeben");
    const id = "t" + Date.now().toString(36);
    let foto = false;
    if (E.blob) { try { await fotoSichern(id, E.blob); foto = true; } catch (e) { C.toast("Foto konnte nicht gespeichert werden"); } }
    const n = {id, ordner: a.ordner, name: a.name, datum: new Date().toISOString().slice(0, 16), note: E.note, maengel: E.maengel,
      text: q("#tText").value.trim(), foto,
      auftrag: {drucker: a.drucker, drucker_name: a.drucker_name, slots: a.slots, gramm: a.gramm, schicht: a.schicht, stufe: a.stufe,
        infill: a.infill, waende: a.waende, stuetzen: a.stuetzen, duese: a.duese, bett: a.bett}};
    if (!lsSet(TB, [n, ...eintraege()])) return C.toast("Speicher voll – nicht gesichert");
    d.remove(); C.toast("Eingetragen"); if (fertig) fertig();
  };
}

/* ---------- Kurzliste im Auftrag ---------- */
export function imAuftrag(el, a, ctx){
  C = ctx;
  const L = eintraege().filter(x => x.ordner === a.ordner);
  el.innerHTML = `<h2>Druck-Tagebuch</h2>${L.length ? `<div class="card">${L.map(zeile).join("")}</div><div style="height:10px"></div>` : ""}
    <button class="btn grey" id="tNeu">Ergebnis eintragen</button>`;
  el.querySelector("#tNeu").onclick = () => eintragen(a, ctx, () => imAuftrag(el, a, ctx));
  el.querySelectorAll("[data-t]").forEach(r => r.onclick = () => blatt(eintraege().find(x => x.id === r.dataset.t), () => imAuftrag(el, a, ctx)));
  fotosEinsetzen(el);
}
const zeile = t => `<div class="row chev" data-t="${t.id}" style="cursor:pointer">
  ${t.foto ? `<img data-foto="${t.id}" alt="" style="width:48px;height:48px;border-radius:8px;object-fit:cover;flex:none;visibility:hidden;background:var(--fill)">` : ""}
  <div class="grow"><div><b>${C.esc(t.name)}</b></div>
    <div class="small"><span style="color:var(--orange)">${sterne(t.note)}</span> · ${de(t.datum)}</div>
    ${t.maengel.length ? `<div class="werte">${t.maengel.map(m => `<span>${C.esc(m)}</span>`).join("")}</div>` : ""}</div></div>`;

/* ---------- Tab Drucker → Tagebuch ---------- */
export function liste(el, ctx, neu){
  C = ctx;
  const L = eintraege().sort((x, y) => y.datum.localeCompare(x.datum));
  const schnitt = L.length ? L.reduce((s, x) => s + x.note, 0) / L.length : 0;
  el.innerHTML = `<div class="stats">
    <div class="stat"><span class="small">Einträge</span><b>${L.length}</b></div>
    <div class="stat"><span class="small">Schnitt</span><b>${L.length ? schnitt.toFixed(1).replace(".", ",") + " ★" : "–"}</b></div>
    <div class="stat"><span class="small">Mit Mängeln</span><b>${L.filter(x => x.maengel.length).length}</b></div></div>
    ${L.length ? `<h2>Neueste zuerst</h2><div class="card">${L.map(zeile).join("")}</div>`
      : `<div class="empty">Noch keine Einträge.<br>Nach einem Druck im Auftrag auf „Ergebnis eintragen“ tippen – Sterne, Mängel und Foto helfen Claude, die Einstellungen für deinen Drucker zu verbessern.</div>`}
    <p class="hint">Das Tagebuch liegt nur in diesem Gerät, Fotos inklusive.</p><div style="height:20px"></div>`;
  el.querySelectorAll("[data-t]").forEach(r => r.onclick = () => blatt(eintraege().find(x => x.id === r.dataset.t), neu));
  fotosEinsetzen(el);
}

/* ---------- Detailblatt + Text für Claude ---------- */
export function claudeText(t){
  const a = t.auftrag || {}, gr = String(a.gramm ?? "").split(",");
  return `druckwerk: Druckergebnis „${t.name}“ vom ${de(t.datum)}\n` +
    `Auftrag: auftraege/${t.ordner}\n` +
    `Drucker: ${a.drucker_name || a.drucker || "–"}\n` +
    (a.slots || []).map((s, i) => `${a.drucker === "kobrax" ? "Spule" : "Kopf"} ${s.slot}: ${s.material} ${s.farbe}${gr[i] ? ` (${(parseFloat(gr[i]) || 0).toFixed(1)} g)` : ""}`).join("\n") +
    `\nSchicht: ${a.schicht ?? "–"} mm · Füllung: ${a.infill ?? "–"} % · Wände: ${a.waende ?? "Standard"}` +
    `\nDüse / Bett: ${uniq(a.duese)} °C · ${uniq(a.bett)} °C` +
    `\nBewertung: ${t.note} von 5 Sternen (5 = perfekt)` +
    `\nMängel: ${t.maengel.length ? t.maengel.join(", ") : "keine"}` +
    (t.text ? `\nNotiz: ${t.text}` : "") +
    (t.foto ? `\nDas Foto vom Druck hänge ich hier im Chat an.` : `\nFoto vom Druck hänge ich bei Bedarf im Chat an.`) +
    `\nBitte Ursachen nennen und die Einstellungen für den nächsten Druck anpassen.`;
}
function blatt(t, neu){
  if (!t) return;
  const a = t.auftrag || {};
  const d = C.sheet(`<h3>${C.esc(t.name)}</h3><p><span style="color:var(--orange);font-size:18px">${sterne(t.note)}</span><br>${de(t.datum)} · ${C.esc(a.drucker_name || "")}</p>
    ${t.foto ? `<img data-foto="${t.id}" alt="" style="width:100%;border-radius:12px;display:block;visibility:hidden;background:var(--fill);min-height:120px">` : ""}
    <h2>Mängel</h2><div class="card"><div class="row"><div class="grow" style="font-size:15px">${t.maengel.length ? C.esc(t.maengel.join(", ")) : "keine"}</div></div></div>
    ${t.text ? `<h2>Notiz</h2><div class="card"><div class="row"><div class="grow" style="font-size:15px">${C.esc(t.text)}</div></div></div>` : ""}
    <h2>Einstellungen</h2><div class="card">
      ${(a.slots || []).map(s => `<div class="row"><span class="dot" style="background:${C.farbe(s.farbe)};width:22px;height:22px"></span><div class="grow">Kopf ${s.slot}: ${C.esc(s.material)} ${C.esc(s.farbe)}</div></div>`).join("")}
      <div class="row"><div class="grow">Schicht · Füllung · Wände</div><span class="val">${C.esc(a.schicht)} mm · ${C.esc(a.infill)} % · ${C.esc(a.waende ?? "Std.")}</span></div>
      <div class="row"><div class="grow">Düse / Bett</div><span class="val">${C.esc(uniq(a.duese))} °C · ${C.esc(uniq(a.bett))} °C</span></div></div>
    <div style="height:14px"></div>
    <button class="btn" id="tCl">An Claude schicken</button>
    ${t.foto ? `<a class="btn grey" id="tDl" download="druck_${C.esc(t.ordner)}.jpg">Foto sichern (zum Anhängen)</a>` : ""}
    <button class="btn rot" id="tWeg">Eintrag löschen</button><button class="btn grey" id="tZu">Schließen</button>`);
  fotosEinsetzen(d).then(() => { const i = d.querySelector("img[data-foto]"), l = d.querySelector("#tDl"); if (i && l && i.src) l.href = i.src; });
  d.querySelector("#tZu").onclick = () => d.remove();
  d.querySelector("#tWeg").onclick = async () => {
    lsSet(TB, eintraege().filter(x => x.id !== t.id)); if (t.foto) await fotoLoeschen(t.id);
    d.remove(); C.toast("Gelöscht"); if (neu) neu(); };
  d.querySelector("#tCl").onclick = () => {
    const text = claudeText(t);
    const s = C.sheet(`<h3>An Claude schicken</h3><p>${t.foto ? "Foto bitte im Chat anhängen („Foto sichern“ legt es in deine Fotos/Dateien)." : "Text kopieren oder direkt in Claude öffnen."}</p>
      <div class="card"><pre class="prompt">${C.esc(text)}</pre></div><div style="height:14px"></div>
      <button class="btn" id="cKop">Kopieren</button><a class="btn grey" target="_blank" rel="noopener" href="https://claude.ai/new?q=${encodeURIComponent(text)}">In Claude öffnen</a>
      <button class="btn grey" id="cZu">Schließen</button>`);
    s.querySelector("#cZu").onclick = () => s.remove();
    s.querySelector("#cKop").onclick = async () => { try { await navigator.clipboard.writeText(text); C.toast("Kopiert"); } catch (e) { C.toast("Bitte markieren und kopieren"); } };
  };
}
