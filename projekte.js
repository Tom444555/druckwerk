// projekte.js – Startseite „Projekte“: ein Projekt = alle Teile, die zusammengehören (Feld gruppe in auftrag.json).
// Projektseite mit Teilen in Druck-Reihenfolge, Köpfen, und „Alles für den USB-Stick“ (ZIP mit Ordner + LIESMICH.txt).
const $ = (s, r = document) => r.querySelector(s);
let C = null;
const dez = (x, n = 1) => (+x || 0).toFixed(n).replace(".", ",");
const gid = a => a.gruppe || a.ordner;
export const teilTitel = (a, c = C) => a.titel || c.schoen(a.name);
const gramme = a => String(a.gramm).split(",").map(x => parseFloat(x) || 0);
const dauer = min => { const h = Math.floor(min / 60), m = min % 60; return h ? `${h} h ${m} min` : `${m} min`; };

// Aufträge → Projekte (offene zuerst, dann neueste)
export function gruppen(A, c = C){
  const M = new Map();
  for (const a of A) { const k = gid(a); if (!M.has(k)) M.set(k, []); M.get(k).push(a); }
  const G = c.gedruckt();
  const P = [...M.entries()].map(([id, teile]) => {
    teile.sort((x, y) => (x.nr || 99) - (y.nr || 99) || x.ordner.localeCompare(y.ordner));
    const haupt = teile.reduce((b, t) => c.summeGramm(t) > c.summeGramm(b) ? t : b, teile[0]);
    return { id, teile, haupt, titel: teile[0].gruppe_titel || c.schoen(teile[0].name), datum: teile.map(t => t.datum).sort().pop(),
      fertig: teile.filter(t => G[t.ordner]).length, min: teile.reduce((s, t) => s + c.minuten(t.zeit), 0), gramm: teile.reduce((s, t) => s + c.summeGramm(t), 0) };
  });
  P.sort((x, y) => (x.fertig === x.teile.length) - (y.fertig === y.teile.length) || y.datum.localeCompare(x.datum) || x.titel.localeCompare(y.titel));
  return P;
}
// Köpfe über alle Teile: je Kopf Material/Farbe und Gramm; einheitlich = jeder Kopf überall gleich bestückt
function koepfe(p){
  const K = {};
  p.teile.forEach(t => { const g = gramme(t); t.slots.forEach((s, i) => { if (!(g[i] > 0)) return;
    const k = K[s.slot] = K[s.slot] || {slot: s.slot, was: new Set(), gramm: 0, farbe: s.farbe}; k.was.add(`${s.material} ${s.farbe}`.trim()); k.gramm += g[i]; }); });
  const liste = Object.values(K).sort((a, b) => a.slot - b.slot);
  const duesen = [...new Set(p.teile.map(t => String(t.duese_mm || "0.4")))];
  return { liste, einheitlich: liste.every(k => k.was.size === 1), duesen };
}
const punkte = (t, c = C) => { const g = gramme(t); return `<div class="dots">${t.slots.filter((s, i) => g[i] > 0).map(s => `<span class="dot" style="background:${c.farbe(s.farbe)}"></span>`).join("")}</div>`; };

/* ---------- Liste aller Projekte ---------- */
export async function liste(app, ctx){
  C = ctx;
  const P = gruppen(C.AUFTRAEGE), G = C.gedruckt();
  let O = null; try { O = await (await import("./wissen.js")).offen(); } catch (e) {}
  const offenP = P.find(p => p.fertig < p.teile.length);
  const naechst = offenP && offenP.teile.find(t => !G[t.ordner]);
  const einOffen = O && O.einGesamt && O.einErledigt < O.einGesamt;
  const karte = p => { const k = koepfe(p), fertig = p.fertig === p.teile.length;
    return `<div class="card pkarte" data-p="${C.esc(p.id)}" role="button" tabindex="0">
      ${p.haupt.vorschau ? `<img src="auftraege/${C.esc(p.haupt.ordner)}/${C.esc(p.haupt.vorschau)}" alt="" loading="lazy">` : `<div class="pleer"></div>`}
      <div class="ptext"><div><b>${C.esc(p.titel)}</b></div>
        <div class="small">${p.teile.length === 1 ? "1 Teil" : p.teile.length + " Teile"} · ${dauer(p.min)} · ${dez(p.gramm, 0)} g</div>
        <div class="pfuss">${fertig ? `<span class="pill gruen">gedruckt</span>` : `<span class="pill">${p.fertig} von ${p.teile.length} gedruckt</span>`}
          <div class="dots">${k.liste.map(x => `<span class="dot" style="background:${C.farbe(x.farbe)}"></span>`).join("")}</div></div></div></div>`; };
  app.innerHTML = `<h1>Projekte</h1>
  <div class="card"><div class="row"><input type="text" id="pSuch" placeholder="Suchen: Projekt, Material, Fehler …" aria-label="Alles durchsuchen" style="flex:1"></div></div>
  <div id="pTreffer"></div><div id="pHaupt">
  ${naechst ? `<h2>Als Nächstes drucken</h2><div class="card"><div class="row oben"><div class="grow"><div><b>${C.esc(teilTitel(naechst))}</b>${offenP.teile.length > 1 ? ` <span class="small">· ${C.esc(offenP.titel)}</span>` : ""}</div>
      <div class="small" style="margin-top:3px">${C.zeitKurz(naechst.zeit)} · ${dez(C.summeGramm(naechst))} g · Düse ${String(naechst.duese_mm || "0.4").replace(".", ",")} mm</div></div>${punkte(naechst)}</div>
    <div style="padding:0 16px 14px"><button class="btn" data-p="${C.esc(offenP.id)}">Zum Projekt</button></div></div>` : ""}
  ${einOffen ? `<div class="card"><div class="row chev" id="pEin" style="cursor:pointer" role="button" tabindex="0"><div class="grow"><b>Drucker einrichten</b>
      <div class="small">${O.einErledigt} von ${O.einGesamt} erledigt · als Nächstes: ${C.esc(O.einNaechster)}</div></div></div></div>` : ""}
  ${P.length ? `<h2>${P.length} ${P.length === 1 ? "Projekt" : "Projekte"}</h2><div class="pgitter">${P.map(karte).join("")}</div>`
    : `<div class="empty">Noch keine Projekte.<br>Unter „Neu“ beschreiben, was du drucken willst – Claude schickt die fertigen Druckdateien, sie erscheinen dann hier.</div>`}
  ${C.verborgen().length ? `<div style="height:14px"></div><button class="btn grey" id="pWeg">Ausgeblendete Teile wieder zeigen (${C.verborgen().length})</button>` : ""}
  <div style="height:20px"></div></div>`;
  const auf = el => el.onclick = el.onkeydown = e => { if (e.type === "keydown" && e.key !== "Enter") return; e.stopPropagation(); C.go("projekt:" + el.dataset.p); };
  app.querySelectorAll("[data-p]").forEach(auf);
  const pe = $("#pEin"); if (pe) pe.onclick = async () => (await import("./wissen.js")).oeffnen("einrichten", C);
  const pw = $("#pWeg"); if (pw) pw.onclick = () => C.verborgenZeigen();
  // Suche über Projekte, Teile und Wissen
  const such = $("#pSuch"), tr = $("#pTreffer"), haupt = $("#pHaupt");
  such.oninput = async () => {
    const q = such.value.trim(), t = q.toLowerCase();
    if (q.length < 2) { tr.innerHTML = ""; haupt.style.display = ""; return; }
    const R = [];
    P.forEach(p => { if (p.titel.toLowerCase().includes(t)) R.push({art: "Projekt", t: p.titel, sub: `${p.teile.length} Teile · ${dauer(p.min)}`, ziel: "projekt:" + p.id});
      p.teile.forEach(a => { if (p.teile.length > 1 && (teilTitel(a) + " " + a.name).toLowerCase().includes(t)) R.push({art: "Teil", t: `${teilTitel(a)} – ${p.titel}`, sub: C.zeitKurz(a.zeit), ziel: "auftrag:" + a.ordner}); }); });
    let K = null, w = []; try { K = await import("./wissen.js"); w = await K.suche(q); } catch (e) {}
    if (such.value.trim() !== q) return;
    R.push(...w); haupt.style.display = "none";
    tr.innerHTML = `<h2>${R.length} Treffer</h2>` + (R.length ? `<div class="card">${R.slice(0, 40).map((x, i) => `
      <div class="row chev" data-tr="${i}" style="cursor:pointer" role="button" tabindex="0"><div class="grow"><div><b>${C.esc(x.t)}</b> <span class="pill">${C.esc(x.art)}</span></div>
        <div class="small" style="overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${C.esc(x.sub || "")}</div></div></div>`).join("")}</div>` : `<div class="empty">Nichts gefunden.</div>`) + `<div style="height:20px"></div>`;
    tr.querySelectorAll("[data-tr]").forEach(r => r.onclick = r.onkeydown = e => { if (e.type === "keydown" && e.key !== "Enter") return;
      const x = R[+r.dataset.tr]; if (/^(projekt|auftrag):/.test(x.ziel)) C.go(x.ziel); else K.oeffnen(x.ziel, C, q); });
  };
}

/* ---------- Ein Projekt ---------- */
export function projekt(app, ctx, id){
  C = ctx;
  const p = gruppen(C.AUFTRAEGE).find(x => x.id === id);
  if (!p) return C.go("projekte");
  const G = C.gedruckt(), k = koepfe(p), mehr = p.teile.length > 1;
  const dz = d => String(d).replace(".", ",");
  app.innerHTML = `<button class="back" id="zur">‹ Projekte</button>
  <h1>${C.esc(p.titel)}</h1>
  ${p.haupt.vorschau ? `<img class="pbild" src="auftraege/${C.esc(p.haupt.ordner)}/${C.esc(p.haupt.vorschau)}" alt="">` : ""}
  <div class="stats">
    <div class="stat"><span class="small">Gedruckt</span><b>${p.fertig} / ${p.teile.length}</b></div>
    <div class="stat"><span class="small">Druckzeit</span><b>${dauer(p.min)}</b></div>
    <div class="stat"><span class="small">Filament</span><b>${dez(p.gramm, 0)} g</b></div>
  </div>
  <h2>Köpfe bestücken</h2>
  <div class="card">${k.liste.map(x => `<div class="row"><span class="dot" style="background:${C.farbe(x.farbe)};width:22px;height:22px"></span>
      <div class="grow">Kopf ${x.slot}: <b>${C.esc([...x.was].join(" / "))}</b></div><span class="val">${dez(x.gramm)} g</span></div>`).join("")}
    <div class="row"><div class="grow">Düse</div><span class="val">${k.duesen.length === 1 ? dz(k.duesen[0]) + " mm auf allen Köpfen" : k.duesen.map(dz).join(" und ") + " mm – je Teil verschieden"}</span></div></div>
  ${k.duesen.length > 1 ? `<div class="warn">Die Teile brauchen unterschiedliche Düsen – bei jedem Teil steht, welche.</div>` : ""}
  ${!k.einheitlich ? `<div class="warn">Ein Kopf ist je nach Teil anders bestückt – vor jedem Teil im Teil nachsehen.</div>` : ""}
  <h2>${mehr ? "Teile in Druck-Reihenfolge" : "Druckdatei"}</h2>
  <div class="card">${p.teile.map((t, i) => `<div class="row" data-o="${C.esc(t.ordner)}">
      <button class="haken ${G[t.ordner] ? "on" : ""}" data-hk="${C.esc(t.ordner)}" aria-label="${C.esc(teilTitel(t))} als gedruckt markieren">${G[t.ordner] ? "✓" : ""}</button>
      <div class="grow chevteil" data-auf="${C.esc(t.ordner)}" role="button" tabindex="0" style="cursor:pointer"><div><b>${mehr ? (i + 1) + ". " : ""}${C.esc(teilTitel(t))}</b></div>
        <div class="small">${C.zeitKurz(t.zeit)} · ${dez(C.summeGramm(t))} g${k.duesen.length > 1 ? ` · Düse ${dz(t.duese_mm || "0.4")} mm` : ""}</div></div>
      ${punkte(t)}<span class="small" data-auf="${C.esc(t.ordner)}" style="cursor:pointer;font-size:20px;padding-left:4px" aria-hidden="true">›</span></div>`).join("")}</div>
  <p class="hint">Haken = gedruckt. Teil antippen: 3D-Ansicht, Einstellungen, einzelne Datei, Ergebnis eintragen.</p>
  <h2>Auf den USB-Stick</h2>
  <button class="btn" id="usb">Alles für den USB-Stick laden</button>
  <div class="balken" id="usbB" style="display:none;margin:8px 2px"><i></i></div>
  <p class="hint">Lädt <b>${C.esc(ordnerName(p))}.zip</b>. In „Dateien“ antippen → es entsteht der Ordner <b>${C.esc(ordnerName(p))}</b> mit ${mehr ? "allen Druckdateien in Reihenfolge (1_, 2_ …)" : "der Druckdatei"} und LIESMICH.txt. Den Ordner auf den USB-Stick bewegen.</p>
  <h2>Mehr</h2>
  ${p.teile.some(t => t.projekt) ? `<button class="btn grey" id="fs">Für Flash Studio am Mac laden (3MF)</button>
  <p class="hint">Dieselben Teile als Projekt-Dateien: in Flash Studio Desktop öffnen, ansehen oder ändern und von dort per WLAN an den Drucker senden.</p>` : ""}
  <button class="btn grey" id="teilen">Auf anderes Gerät holen (Link teilen)</button>
  <h2>Verwalten</h2>
  <button class="btn rot" id="weg">Projekt ausblenden</button>
  <div style="height:20px"></div>`;
  $("#zur").onclick = () => C.go("projekte");
  app.querySelectorAll("[data-auf]").forEach(r => r.onclick = r.onkeydown = e => { if (e.type === "keydown" && e.key !== "Enter") return; C.go("auftrag:" + r.dataset.auf); });
  app.querySelectorAll("[data-hk]").forEach(b => b.onclick = () => { const an = !C.gedruckt()[b.dataset.hk]; C.gedrucktSetzen(b.dataset.hk, an);
    C.toast(an ? "Als gedruckt markiert" : "Wieder offen"); projekt(app, C, id); });
  const balken = $("#usbB"), fort = x => { balken.style.display = ""; balken.firstElementChild.style.width = Math.round(x * 100) + "%"; };
  const laden = async (knopf, art) => { if (knopf.disabled) return; const text = knopf.textContent; knopf.disabled = true; knopf.textContent = "Wird gepackt …";
    try { await paket(p, art, fort); C.toast("Fertig – in „Dateien“ unter Downloads", 4000); }
    catch (e) { console.error(e); C.toast("Konnte nicht geladen werden – Internet prüfen", 4000); }
    knopf.disabled = false; knopf.textContent = text; setTimeout(() => { balken.style.display = "none"; }, 1500); };
  $("#usb").onclick = e => laden(e.currentTarget, "gcode");
  const fs = $("#fs"); if (fs) fs.onclick = e => laden(e.currentTarget, "projekt");
  $("#teilen").onclick = async () => { const url = location.origin + location.pathname + "#projekt:" + encodeURIComponent(p.id);
    try { if (navigator.share) { await navigator.share({title: "Druckwerk: " + p.titel, url}); return; } } catch (e) { if (e && e.name === "AbortError") return; }
    try { await navigator.clipboard.writeText(url); C.toast("Link kopiert"); } catch (e) { C.sheet(`<h3>Link</h3><div class="card"><pre class="prompt">${C.esc(url)}</pre></div>`); } };
  $("#weg").onclick = () => { const d = C.sheet(`<h3>„${C.esc(p.titel)}“ ausblenden?</h3><p>Das Projekt verschwindet aus deiner Liste. Die Dateien bleiben im Lager; unter „Projekte“ ganz unten holst du es zurück.</p>
    <button class="btn rotvoll" id="jaW">Ausblenden</button><button class="btn grey" id="neinW">Abbrechen</button>`);
    d.querySelector("#neinW").onclick = () => d.remove();
    d.querySelector("#jaW").onclick = () => { d.remove(); C.verbergen(p.teile.map(t => t.ordner)); C.go("projekte"); C.toast("Ausgeblendet"); }; };
}

/* ---------- Paket für den USB-Stick: ZIP (ohne Kompression) mit Ordner, nummerierten Dateien und LIESMICH.txt ---------- */
const sauber = s => String(s).normalize("NFD").replace(/[̀-ͯ]/g, "").replace(/ß/g, "ss").replace(/[^A-Za-z0-9_-]+/g, "_").replace(/^_+|_+$/g, "");
export const ordnerName = p => sauber(p.titel) || "Projekt";
export const dateiName = (p, t, i, art) => { const e = art === "gcode" ? ".gcode" : ".3mf", basis = sauber(t.datei || String(t[art] || "").replace(/\.[^.]+$/, ""));
  return (p.teile.length > 1 ? (i + 1) + "_" : "") + basis + e; };
export function liesmich(p, c = C){
  const k = koepfe(p), dz = d => String(d).replace(".", ","), Z = [];
  Z.push(p.titel, "=".repeat(p.titel.length), "", `Drucker: ${p.teile[0].drucker_name}`, `Erstellt mit Druckwerk am ${c.deDatum(new Date().toISOString())}`, "",
    "KOEPFE BESTUECKEN", ...k.liste.map(x => `  Kopf ${x.slot}: ${[...x.was].join(" / ")}  (${dez(x.gramm)} g)`),
    `  Duese: ${k.duesen.length === 1 ? dz(k.duesen[0]) + " mm auf allen Koepfen" : "je Teil verschieden, siehe unten"}`, "",
    p.teile.length > 1 ? "TEILE IN DRUCK-REIHENFOLGE" : "DRUCKDATEI");
  p.teile.forEach((t, i) => { const g = gramme(t);
    Z.push(`  ${dateiName(p, t, i, "gcode")}`, `      ${teilTitel(t, c)} - ${c.zeitKurz(t.zeit)}, ${dez(c.summeGramm(t))} g, Duese ${dz(t.duese_mm || "0.4")} mm, Schicht ${dz(t.schicht)} mm`,
      `      Koepfe: ${t.slots.filter((s, j) => g[j] > 0).map(s => `${s.slot} ${s.material} ${s.farbe}`).join(", ")}`); });
  Z.push("", `Gesamt: ${dauer(p.min)}, ${dez(p.gramm, 0)} g`, "", "AM DRUCKER",
    "  1. Diesen Ordner auf den USB-Stick (FAT32) kopieren.", "  2. Koepfe wie oben bestuecken, Platte sauber und leer.",
    "  3. Am Bildschirm unter USB die Datei waehlen, erste Schicht beobachten.", "  4. In Druckwerk den Haken beim Teil setzen und das Ergebnis eintragen.", "");
  return Z.join("\r\n");
}
let _crcT = null;
function crc32(u8){ if (!_crcT) { _crcT = new Uint32Array(256); for (let n = 0; n < 256; n++) { let c = n; for (let k = 0; k < 8; k++) c = c & 1 ? 0xEDB88320 ^ (c >>> 1) : c >>> 1; _crcT[n] = c >>> 0; } }
  let c = 0xFFFFFFFF; for (let i = 0; i < u8.length; i++) c = _crcT[(c ^ u8[i]) & 255] ^ (c >>> 8); return (c ^ 0xFFFFFFFF) >>> 0; }
export function zip(dateien){   // [{name, daten: Uint8Array}] → Blob
  const enc = new TextEncoder(), teile = [], zentral = []; let pos = 0;
  const d = new Date(), zeit = (d.getHours() << 11) | (d.getMinutes() << 5) | (d.getSeconds() >> 1), tag = ((d.getFullYear() - 1980) << 9) | ((d.getMonth() + 1) << 5) | d.getDate();
  for (const f of dateien) {
    const n = enc.encode(f.name), crc = crc32(f.daten), gr = f.daten.length;
    const kopf = new DataView(new ArrayBuffer(30)); kopf.setUint32(0, 0x04034b50, true); kopf.setUint16(4, 20, true); kopf.setUint16(6, 0x0800, true); kopf.setUint16(8, 0, true);
    kopf.setUint16(10, zeit, true); kopf.setUint16(12, tag, true); kopf.setUint32(14, crc, true); kopf.setUint32(18, gr, true); kopf.setUint32(22, gr, true); kopf.setUint16(26, n.length, true);
    teile.push(kopf.buffer, n, f.daten);
    const z = new DataView(new ArrayBuffer(46)); z.setUint32(0, 0x02014b50, true); z.setUint16(4, 20, true); z.setUint16(6, 20, true); z.setUint16(8, 0x0800, true);
    z.setUint16(12, zeit, true); z.setUint16(14, tag, true); z.setUint32(16, crc, true); z.setUint32(20, gr, true); z.setUint32(24, gr, true); z.setUint16(28, n.length, true); z.setUint32(42, pos, true);
    zentral.push(z.buffer, n); pos += 30 + n.length + gr;
  }
  const zl = zentral.reduce((s, x) => s + x.byteLength, 0), ende = new DataView(new ArrayBuffer(22));
  ende.setUint32(0, 0x06054b50, true); ende.setUint16(8, dateien.length, true); ende.setUint16(10, dateien.length, true); ende.setUint32(12, zl, true); ende.setUint32(16, pos, true);
  return new Blob([...teile, ...zentral, ende.buffer], {type: "application/zip"});
}
async function paket(p, art, fort){
  const ordner = ordnerName(p), mit = p.teile.map((t, i) => [t, i]).filter(([t]) => t[art]), D = [];
  fort(0.03);
  for (let j = 0; j < mit.length; j++) { const [t, i] = mit[j];
    const r = await fetch(`auftraege/${t.ordner}/${encodeURIComponent(t[art])}`); if (!r.ok) throw new Error("fehlt: " + t[art]);
    D.push({name: `${ordner}/${dateiName(p, t, i, art)}`, daten: new Uint8Array(await r.arrayBuffer())}); fort((j + 1) / (mit.length + 0.5)); }
  D.push({name: `${ordner}/LIESMICH.txt`, daten: new TextEncoder().encode("﻿" + liesmich(p))});
  const url = URL.createObjectURL(zip(D)), a = document.createElement("a");
  a.href = url; a.download = ordner + (art === "gcode" ? "" : "_FlashStudio") + ".zip"; document.body.appendChild(a); a.click(); a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 60000); fort(1);
}
