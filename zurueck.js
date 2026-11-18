// zurueck.js – Rückweg Mac → Druckwerk: Tom ändert ein Teil in Flash Studio und legt .gcode/.3mf zurück ins Lager.
// (1) Von Hand: Knopf „Geänderte Fassung hochladen“ im Teil (jeder Browser, auch iPad).
// (2) Von selbst finden: in Chrome/Edge am Rechner einen Ordner verbinden – Druckwerk schaut beim Zurückkommen in die App nach geänderten Dateien und fragt.
// Ablage: eingang/<id>/… + auftrag.json {art:"zurueck"} → GitHub Action (werkzeug/eingang.py → zurueck) ersetzt die Dateien im Auftrag.
const REPO = "Tom444555/druckwerk", TOK = "druckwerk_token", STAND = "druckwerk_ordner_stand";
const lsg = k => { try { return localStorage.getItem(k); } catch (e) { return null; } };
const lss = (k, v) => { try { localStorage.setItem(k, v); } catch (e) {} };
const stand = () => { try { return JSON.parse(lsg(STAND) || "{}") || {}; } catch (e) { return {}; } };
const gh = (pfad, opt = {}) => fetch(`https://api.github.com/repos/${REPO}${pfad}`, {...opt, cache: "no-store",
  headers: {Authorization: "Bearer " + lsg(TOK), Accept: opt.roh ? "application/vnd.github.raw+json" : "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}});
const b64 = buf => { const u = new Uint8Array(buf); let s = ""; for (let i = 0; i < u.length; i += 32768) s += String.fromCharCode.apply(null, u.subarray(i, i + 32768)); return btoa(s); };
const ablegen = async (pfad, inhalt, text) => { const r = await gh("/contents/" + pfad, {method: "PUT", body: JSON.stringify({message: text, content: inhalt})});
  if (!r.ok) throw new Error(r.status === 401 || r.status === 403 ? "GitHub-Zugang abgelehnt – Token prüfen (Wissen → Gerät & Daten)" : r.status === 413 || r.status === 422 ? "Datei zu groß für das Lager" : "Hochladen fehlgeschlagen (" + r.status + ")"); };
const pause = ms => new Promise(r => setTimeout(r, ms));
const titel = (a, C) => a.titel || C.schoen(a.name);
const MAX = 70 * 1024 * 1024;

// lädt die Dateien hoch und wartet, bis das Lager die neue Fassung zeigt
async function senden(C, a, dat, notiz, sag){
  for (const f of [dat.gcode, dat.projekt]) if (f && f.size > MAX) throw new Error(`„${f.name}“ ist zu groß (über 70 MB)`);
  const id = "z" + Date.now().toString(36), job = {art: "zurueck", ordner: a.ordner, notiz};
  let n = 0; const alle = [["gcode", dat.gcode], ["projekt", dat.projekt]].filter(x => x[1]);
  for (const [feld, f] of alle) { const name = feld === "gcode" ? "neu.gcode" : "neu.3mf";
    sag(`Lade ${f.name} hoch … (${Math.round(f.size / 1048576 * 10) / 10} MB)`, 5 + 40 * n / alle.length); n++;
    await ablegen(`eingang/${id}/${name}`, b64(await f.arrayBuffer()), `App: geänderte Fassung für ${a.ordner}`); job[feld] = name; }
  await ablegen(`eingang/${id}/auftrag.json`, btoa(unescape(encodeURIComponent(JSON.stringify(job)))), `App: ${a.ordner} von Tom geändert`);
  let st = null;
  for (let i = 0; i < 90 && !st; i++) { sag(`Lager übernimmt die Dateien … (${Math.round(i * 8 / 60 * 10) / 10} Min.)`, Math.min(50 + i * 2, 88)); await pause(window.__p ? 50 : 8000);
    try { const r = await gh(`/contents/status/${id}.json`, {roh: true}); if (r.ok) st = await r.json(); } catch (e) {} }
  if (!st) throw new Error("Noch keine Antwort vom Lager – in ein paar Minuten unter „Projekte“ nachsehen.");
  if (!st.ok) throw new Error("Nicht übernommen: " + String(st.fehler || "").split("\n").filter(Boolean).pop());
  for (let i = 0; i < 40; i++) { sag("Übernommen – App wird aktualisiert …", 94);
    try { const l = await (await fetch("auftraege/index.json?t=" + Date.now(), {cache: "no-store"})).json();
      if (l.some(x => x.ordner === a.ordner && x.geaendert && x.geaendert.id === id)) return l; } catch (e) {}
    await pause(window.__p ? 50 : 6000); }
  return null;
}
function mitZugang(C, weiter){ if (lsg(TOK)) return weiter(); import("./werkstatt.js").then(W => W.zugangEinrichten(C, weiter)); }

/* ---------- (1) Von Hand ---------- */
export function hochladen(C, a, vor = {}){
  mitZugang(C, () => {
    const d = C.sheet(`<h3>Geänderte Fassung hochladen</h3>
      <p>„${C.esc(titel(a, C))}“ – was du in Flash Studio geändert hast, ersetzt hier die bisherige Fassung (für alle Geräte und das USB-Paket).</p>
      <div class="card">
        <label class="row" style="cursor:pointer"><div class="grow">Druckdatei (.gcode)<div class="small" id="zG">${vor.gcode ? C.esc(vor.gcode.name) : "in Flash Studio: slicen → „G-Code exportieren“"}</div></div><span class="val" style="color:var(--blue)">wählen</span>
          <input type="file" id="zGf" accept=".gcode,.g,.gx,text/plain" hidden></label>
        <label class="row" style="cursor:pointer"><div class="grow">Projekt (.3mf)<div class="small" id="zP">${vor.projekt ? C.esc(vor.projekt.name) : "in Flash Studio: „Projekt speichern“ – damit du später weitermachen kannst"}</div></div><span class="val" style="color:var(--blue)">wählen</span>
          <input type="file" id="zPf" accept=".3mf" hidden></label>
      </div>
      <div class="card"><textarea id="zN" rows="2" placeholder="Was hast du geändert? (z. B. Füllung 30 %, Stützen aus)" style="width:100%"></textarea></div>
      <p class="hint">Die Notiz liest Claude, bevor er das Teil das nächste Mal neu rechnet – sonst ginge deine Änderung verloren. Ohne .gcode bleibt die alte Druckdatei bestehen.</p>
      <div id="zLauf" style="display:none"><p id="zText" class="small"></p><div class="balken"><i id="zBalken"></i></div></div>
      <button class="btn" id="zLos">Hochladen</button><button class="btn grey" id="zZu">Abbrechen</button>`);
    d.onclick = null;
    const dat = {gcode: vor.gcode || null, projekt: vor.projekt || null}, q = s => d.querySelector(s);
    q("#zGf").onchange = e => { dat.gcode = e.target.files[0] || null; if (dat.gcode) q("#zG").textContent = dat.gcode.name; };
    q("#zPf").onchange = e => { dat.projekt = e.target.files[0] || null; if (dat.projekt) q("#zP").textContent = dat.projekt.name; };
    q("#zZu").onclick = () => d.remove();
    q("#zLos").onclick = async () => {
      if (!dat.gcode && !dat.projekt) return C.toast("Erst eine Datei wählen");
      if (dat.gcode && !/\.(gcode|g|gx)$/i.test(dat.gcode.name)) return C.toast("Die Druckdatei muss auf .gcode enden");
      if (dat.projekt && !/\.3mf$/i.test(dat.projekt.name)) return C.toast("Das Projekt muss auf .3mf enden");
      q("#zLos").style.display = "none"; q("#zZu").textContent = "Im Hintergrund weiter"; q("#zLauf").style.display = "";
      const sag = (t, p) => { if (!d.isConnected) return; q("#zText").textContent = t; q("#zBalken").style.width = p + "%"; };
      try { const l = await senden(C, a, dat, q("#zN").value.trim(), sag);
        const s = stand(); for (const f of [dat.gcode, dat.projekt]) if (f && f._key) s[f._key] = f.lastModified; lss(STAND, JSON.stringify(s));
        d.remove(); C.toast("Neue Fassung ist im Lager", 4000); if (l) C.neuLaden(); if (vor.fertig) vor.fertig(); }
      catch (e) { console.error(e); if (d.isConnected) { q("#zText").textContent = e.message; q("#zBalken").style.width = "0"; q("#zLos").style.display = ""; q("#zLos").textContent = "Noch einmal versuchen"; } else C.toast(e.message, 6000); }
    };
  });
}

/* ---------- (2) Ordner am Rechner verbinden (Chrome/Edge) ---------- */
export const ordnerMoeglich = () => typeof window.showDirectoryPicker === "function";
const db = () => new Promise((ok, nein) => { const r = indexedDB.open("druckwerk_ordner", 1); r.onupgradeneeded = () => r.result.createObjectStore("h"); r.onsuccess = () => ok(r.result); r.onerror = () => nein(r.error); });
const dbGet = async () => { try { const d = await db(); return await new Promise(ok => { const r = d.transaction("h").objectStore("h").get("flash"); r.onsuccess = () => ok(r.result || null); r.onerror = () => ok(null); }); } catch (e) { return null; } };
const dbSet = async v => { const d = await db(); return new Promise((ok, nein) => { const t = d.transaction("h", "readwrite"); v ? t.objectStore("h").put(v, "flash") : t.objectStore("h").delete("flash"); t.oncomplete = ok; t.onerror = () => nein(t.error); }); };
let _h = null;
export async function ordnerStatus(){ if (!ordnerMoeglich()) return {art: "nein"};
  _h = _h || await dbGet(); if (!_h) return {art: "aus"};
  let p = "prompt"; try { p = await _h.queryPermission({mode: "read"}); } catch (e) {}
  return {art: p === "granted" ? "an" : "fragen", name: _h.name}; }
export async function ordnerVerbinden(C){
  try { _h = await window.showDirectoryPicker({id: "druckwerk-flash", mode: "read"}); try { await dbSet(_h); } catch (e) { console.warn("Ordner nur für diese Sitzung verbunden", e); } C.toast(`Ordner „${_h.name}“ verbunden`); return true; }
  catch (e) { if (!e || e.name !== "AbortError") C.toast("Ordner konnte nicht verbunden werden"); return false; } }
export async function ordnerErlauben(C){ try { _h = _h || await dbGet(); return !!_h && (await _h.requestPermission({mode: "read"})) === "granted"; } catch (e) { return false; } }
export async function ordnerTrennen(C){ _h = null; try { await dbSet(null); } catch (e) {} lss(STAND, "{}"); C.toast("Ordner getrennt"); }

// sucht im verbundenen Ordner nach .gcode/.3mf, die zu einem Teil gehören (Dateiname beginnt mit dem Teil-Dateinamen) und neu oder geändert sind
export async function ordnerPruefen(C){
  const st = await ordnerStatus(); if (st.art !== "an") return [];
  const s = stand(), teile = C.LAGER.map(a => ({a, basis: String(a.datei || String(a.gcode || "").replace(/\.[^.]+$/, "")).toLowerCase()})).filter(x => x.basis).sort((x, y) => y.basis.length - x.basis.length);
  const F = new Map();
  try { for await (const e of _h.values()) { if (e.kind !== "file") continue;
      const m = e.name.match(/^(?:\d+_)?(.+)\.(gcode|3mf)$/i); if (!m) continue;
      const t = teile.find(x => m[1].toLowerCase().startsWith(x.basis)); if (!t) continue;
      const f = await e.getFile(); if (s[e.name] === f.lastModified) continue;
      f._key = e.name; const feld = m[2].toLowerCase() === "3mf" ? "projekt" : "gcode";
      const x = F.get(t.a.ordner) || {a: t.a}; if (!x[feld] || x[feld].lastModified < f.lastModified) x[feld] = f; F.set(t.a.ordner, x); } }
  catch (e) { console.warn(e); return []; }
  return [...F.values()];
}
export function ordnerMerken(funde){ const s = stand(); for (const x of funde) for (const f of [x.gcode, x.projekt]) if (f && f._key) s[f._key] = f.lastModified; lss(STAND, JSON.stringify(s)); }

// Liste der Funde: je Teil hochladen oder übergehen
export function fundeZeigen(C, funde, danach){
  const d = C.sheet(`<h3>Geändert in Flash Studio</h3><p>Im verbundenen Ordner liegen neue Fassungen. Antippen zum Hochladen:</p>
    <div class="card">${funde.map((x, i) => `<div class="row chev" data-f="${i}" style="cursor:pointer" role="button" tabindex="0"><div class="grow"><b>${C.esc(titel(x.a, C))}</b>${x.a.gruppe_titel ? ` <span class="small">· ${C.esc(x.a.gruppe_titel)}</span>` : ""}
      <div class="small">${[x.gcode, x.projekt].filter(Boolean).map(f => C.esc(f.name)).join(" · ")}</div></div></div>`).join("")}</div>
    <button class="btn grey" id="fIgn">Alle übergehen</button><button class="btn grey" id="fZu">Später</button>`);
  d.querySelector("#fZu").onclick = () => d.remove();
  d.querySelector("#fIgn").onclick = () => { ordnerMerken(funde); d.remove(); C.toast("Übergangen"); if (danach) danach(); };
  d.querySelectorAll("[data-f]").forEach(r => r.onclick = () => { const x = funde[+r.dataset.f]; d.remove(); hochladen(C, x.a, {gcode: x.gcode, projekt: x.projekt, fertig: danach}); });
}

// Zeile für Projektseite/Wissen: Zustand + Knöpfe; `neu` zeichnet die Seite neu
export async function ordnerZeile(C){
  const st = await ordnerStatus();
  if (st.art === "nein") return `<p class="hint">Änderungen aus Flash Studio zurückholen: im Teil „Geänderte Fassung hochladen“. In Chrome oder Edge kann Druckwerk einen Ordner selbst im Blick behalten.</p>`;
  if (st.art === "aus") return `<button class="btn grey" data-ord="verbinden">Flash-Studio-Ordner verbinden</button>
    <p class="hint">Wähle den Ordner, in den du in Flash Studio speicherst und exportierst. Kommst du danach in Druckwerk zurück, findet es geänderte Dateien selbst und fragt, ob es sie hochladen soll. Dateinamen beim Speichern beibehalten (z. B. Schecter_370_Korpus…).</p>`;
  return `<div class="card"><div class="row"><div class="grow">Flash-Studio-Ordner<div class="small">„${C.esc(st.name)}“ ${st.art === "an" ? "– wird beim Öffnen der App geprüft" : "– Zugriff für heute noch erlauben"}</div></div>
    ${st.art === "fragen" ? `<button class="back" data-ord="erlauben">erlauben</button>` : `<button class="back" data-ord="pruefen">jetzt prüfen</button>`}<button class="back" data-ord="trennen" style="color:var(--red)">trennen</button></div></div>`;
}
export function ordnerBinden(wurzel, C, neu){
  wurzel.querySelectorAll("[data-ord]").forEach(b => b.onclick = async () => { const w = b.dataset.ord;
    if (w === "verbinden") { if (!await ordnerVerbinden(C)) return; }
    else if (w === "erlauben") { if (!await ordnerErlauben(C)) return C.toast("Nicht erlaubt"); }
    else if (w === "trennen") { await ordnerTrennen(C); return neu(); }
    const f = await ordnerPruefen(C); if (f.length) fundeZeigen(C, f, neu); else if (w !== "erlauben") C.toast("Keine geänderten Dateien im Ordner"); neu(); });
}

/* ---------- Anleitung: Mac ↔ Flash Studio ↔ Druckwerk (Wissen → Hilfe, Projektseite) ---------- */
export function anleitung(C){
  const d = C.sheet(`<h3>Mac, Flash Studio und Druckwerk</h3>
    <p>So arbeiten die drei zusammen. Auf iPhone und iPad gibt es Flash Studio Desktop nicht – dort bleibt der USB-Stick.</p>
    <h2>Einmal einrichten (Mac)</h2>
    <div class="card"><ol class="steps"><li><b>Flash Studio Desktop</b> installieren, starten, Drucker verbinden.</li>
      <li>In Flash Studio unter Einstellungen einen <b>Download-Ordner</b> festlegen – ohne ihn nimmt es keine Links an.</li>
      <li>Druckwerk in <b>Chrome</b> öffnen (Safari geht auch, aber ohne Ordner-Überwachung).</li>
      <li>Im Projekt <b>„Flash-Studio-Ordner verbinden“</b> und den Ordner wählen, in den du in Flash Studio speicherst.</li>
      <li>Beim ersten Hochladen fragt Druckwerk nach dem <b>GitHub-Zugang</b> (Token, wie am iPad).</li></ol></div>
    <h2>Hin: Druckwerk → Flash Studio → Drucker</h2>
    <div class="card"><ol class="steps"><li>Projekt öffnen → unter <b>„Direkt in Flash Studio öffnen“</b> das Teil anklicken.</li>
      <li>Der Browser fragt „Flash Studio öffnen?“ → erlauben. Das Projekt lädt mit allen Einstellungen, Farben und Köpfen.</li>
      <li>In Flash Studio <b>Slicen</b> → <b>Drucken</b>: es geht per WLAN an den Drucker.</li></ol></div>
    <p class="hint">Passiert beim Klick nichts: „Für Flash Studio am Mac laden (3MF)“ nehmen und die Datei per Doppelklick öffnen.</p>
    <h2>Zurück: eigene Änderung ins Lager</h2>
    <div class="card"><ol class="steps"><li>In Flash Studio ändern und slicen.</li>
      <li><b>„G-Code exportieren“</b> und <b>„Projekt speichern“</b> – in den verbundenen Ordner, <b>Dateinamen beibehalten</b> (z. B. Schecter_370_Korpus…).</li>
      <li>Zurück zu Druckwerk wechseln: oben erscheint <b>„In Flash Studio geändert“</b> → anklicken.</li>
      <li>Kurz notieren, <b>was</b> du geändert hast → <b>Hochladen</b>. Nach ein paar Minuten ist die neue Fassung auf allen Geräten und im USB-Paket.</li></ol></div>
    <p class="hint">Ohne verbundenen Ordner (Safari, iPad): im Teil ganz unten „Geänderte Fassung hochladen“ und die Dateien selbst wählen. Die Notiz liest Claude, bevor er das Teil neu rechnet – sonst ginge deine Änderung verloren. Lädst du nur die .3mf hoch, bleibt die Druckdatei die alte.</p>
    <div style="height:12px"></div><button class="btn grey" id="anZu">Fertig</button>`);
  d.querySelector("#anZu").onclick = () => d.remove();
}
