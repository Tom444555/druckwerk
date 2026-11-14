// wissen.js – Material (Filamente · Lager · Zubehör), Drucker (Creator 5 Pro), Workflow (Idee → Modell)
// Inhalte stehen in wissen/*.json (dort pflegen, Feld "stand" mitziehen). Eigene Daten liegen nur im Gerät (localStorage).
const $ = (s, r = document) => r.querySelector(s);
const $$ = (s, r = document) => [...r.querySelectorAll(s)];
let D = null, C = null;
const U = { mat: "filamente", gruppe: "Alle", ziel: "", zub: "alle", dr: "ueberblick", wf: "weg", weg: "technik" };
const ls = (k, d) => { try { const v = JSON.parse(localStorage.getItem(k)); return v ?? d; } catch (e) { return d; } };
const lsSet = (k, v) => { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) {} };
const zahl = v => { const n = parseFloat(String(v ?? "").replace(",", ".")); return isFinite(n) ? n : 0; };
const heute = () => new Date().toISOString().slice(0, 10);
const de = iso => iso ? iso.split("-").reverse().join(".") : "";

async function daten(){
  if (D) return D;
  const l = async n => (await fetch(`wissen/${n}.json`, {cache: "no-store"})).json();
  const [f, z, c, w] = await Promise.all([l("filamente"), l("zubehoer"), l("c5pro"), l("workflow")]);
  return D = {f, z, c, w};
}
const seg = (k, opts) => `<div class="seg">${opts.map(([v, l]) => `<button data-u="${k}" data-v="${v}" class="${U[k] === v ? "on" : ""}">${l}</button>`).join("")}</div>`;
const chips = (k, opts) => `<div class="chips">${opts.map(([v, l]) => `<button class="chip ${U[k] === v ? "on" : ""}" data-u="${k}" data-v="${v}">${C.esc(l)}</button>`).join("")}</div>`;
const liste = a => `<div class="card"><ul class="liste">${a.map(x => `<li>${C.esc(x)}</li>`).join("")}</ul></div>`;
const quellen = (q, stand) => `<h2>Quellen · Stand ${C.esc(stand)}</h2><div class="card">${q.map(x =>
  `<a class="row chev" href="${C.esc(x.url)}" target="_blank" rel="noopener" style="color:inherit;text-decoration:none"><div class="grow small">${C.esc(x.titel)}</div></a>`).join("")}</div><div style="height:20px"></div>`;
function binden(app, neu){
  $$("[data-u]", app).forEach(b => b.onclick = () => { const k = b.dataset.u, v = b.dataset.v;
    U[k] = (b.classList.contains("chip") && k === "ziel" && U[k] === v) ? "" : v; neu(); });
}

export async function seite(app, ctx, welche){
  C = ctx;
  if (!D) app.innerHTML = `<h1>${{material: "Material", drucker: "Drucker", workflow: "Workflow"}[welche]}</h1><div class="empty">Wird geladen …</div>`;
  await daten();
  ({material, drucker, workflow})[welche](app);
}

/* ================= Material ================= */
function material(app){
  const kopf = `<h1>Material</h1>${seg("mat", [["filamente", "Filamente"], ["lager", "Mein Lager"], ["zubehoer", "Zubehör"]])}`;
  if (U.mat === "lager") return lager(app, kopf);
  if (U.mat === "zubehoer") return zubehoer(app, kopf);
  const f = D.f;
  const zeigen = f.materialien.filter(m => (U.gruppe === "Alle" || m.gruppe === U.gruppe) && (!U.ziel || m.eignung.includes(U.ziel)));
  app.innerHTML = kopf + `
  <h2>Was soll das Teil können?</h2>${chips("ziel", f.finder.map(x => [x.id, x.name]))}
  <h2>Gruppe</h2>${chips("gruppe", [["Alle", "Alle"], ...f.gruppen.map(g => [g, g])])}
  <h2>${zeigen.length} ${zeigen.length === 1 ? "Material" : "Materialien"} für den Creator 5 Pro</h2>
  ${zeigen.length ? `<div class="card">${zeigen.map(m => `
    <div class="row chev" data-m="${m.id}" style="cursor:pointer"><div class="grow"><div><b>${C.esc(m.name)}</b></div>
      <div class="small">${C.esc(m.kurz)}</div>
      <div class="werte"><span>Düse ${C.esc(m.duese)}</span><span>Bett ${C.esc(m.bett)}</span><span>Kammer ${C.esc(m.kammer)}</span></div></div></div>`).join("")}</div>`
    : `<div class="empty">Keine Übereinstimmung – Auswahl oben lockern.</div>`}
  <p class="hint">${C.esc(f.hinweis)}</p>
  <h2>Mischen in einem Druck</h2>${liste(f.mischen)}
  <h2>Grundausstattung</h2><div class="card">${f.starter.map(s => `<div class="row"><div class="grow"><b>${C.esc(s.name)}</b><div class="small">${C.esc(s.wozu)}</div></div></div>`).join("")}</div>
  <p class="hint">${C.esc(f.spulen)}</p>
  ${quellen(f.quellen, f.stand)}`;
  binden(app, () => material(app));
  $$("[data-m]", app).forEach(r => r.onclick = () => filamentBlatt(f.materialien.find(m => m.id === r.dataset.m)));
}
function filamentBlatt(m){
  const z = (l, k) => m[k] ? `<div class="row"><div class="grow">${l}</div><span class="val">${C.esc(m[k])}${m.herkunft && m.herkunft[k] ? ` <span class="pill">${m.herkunft[k]}</span>` : ""}</span></div>` : "";
  const d = C.sheet(`<h3>${C.esc(m.name)}</h3><p>${C.esc(m.kurz)}</p>
    <div class="card">${z("Düse (°C)", "duese")}${z("Bett (°C)", "bett")}${z("Kammer (°C)", "kammer")}${z("Lüfter", "luefter")}${z("Trocknen", "trocknen")}${z("Durchfluss (mm³/s)", "flow")}</div>
    <h2>Wofür</h2><div class="card"><div class="row"><div class="grow" style="font-size:15px">${C.esc(m.wofuer)}</div></div></div>
    <h2>Achtung</h2><div class="card"><div class="row"><div class="grow" style="font-size:15px">${C.esc(m.achtung)}</div></div></div>
    <p class="hint">${m.druckwerk.length ? "In druckwerk wählbar als: " + m.druckwerk.join(", ") : "Noch nicht in druckwerk hinterlegt – auf Wunsch ergänzt Claude das Profil."}</p>
    <div style="height:12px"></div>
    ${m.druckwerk.length ? `<button class="btn" id="fAuf">Auftrag mit ${C.esc(m.druckwerk[0])} beginnen</button>` : ""}
    <button class="btn grey" id="fZu">Schließen</button>`);
  d.querySelector("#fZu").onclick = () => d.remove();
  const a = d.querySelector("#fAuf"); if (a) a.onclick = () => { d.remove(); C.neuStart("", "", m.druckwerk[0]); };
}

/* ---------- Mein Lager (Spulen, nur auf diesem Gerät) ---------- */
const SP = "druckwerk_spulen";
const SORTEN = ["PLA", "PLA matt", "PLA Silk", "PLA-CF", "PETG", "PETG-CF", "TPU", "ABS", "ASA", "ASA-CF", "PA-CF", "PVA", "Sonstiges"];
const spulen = () => ls(SP, []);
const spName = s => `${s.material} ${s.farbe || ""}`.trim();
function lager(app, kopf){
  const L = spulen();
  const rest = L.reduce((s, x) => s + zahl(x.rest), 0);
  const wert = L.reduce((s, x) => s + (zahl(x.start) ? zahl(x.preis) * zahl(x.rest) / zahl(x.start) : 0), 0);
  let h = kopf + `<div class="stats">
    <div class="stat"><span class="small">Spulen</span><b>${L.length}</b></div>
    <div class="stat"><span class="small">Vorrat</span><b>${(rest / 1000).toFixed(2).replace(".", ",")} kg</b></div>
    <div class="stat"><span class="small">Wert</span><b>${wert.toFixed(0)} €</b></div></div>
  <h2>Köpfe am Creator 5 Pro</h2><div class="card">${[1, 2, 3, 4].map(k => { const s = L.find(x => x.kopf === k);
    return `<div class="row"><span class="dot" style="background:${s ? C.farbe(s.farbe) : "transparent"};width:22px;height:22px"></span>
      <div class="grow">Kopf ${k}</div><span class="val">${s ? C.esc(spName(s)) + " · " + zahl(s.rest).toFixed(0) + " g" : "leer"}</span></div>`; }).join("")}</div>
  <h2>Spulen</h2>`;
  if (!L.length) h += `<div class="empty">Noch keine Spulen eingetragen.<br>Trag deine Spulen ein – dann kannst du nach jedem Auftrag den Verbrauch abbuchen und siehst, was noch reicht.</div>`;
  else h += `<div class="card">${L.map(s => { const p = zahl(s.start) ? Math.max(0, Math.min(100, 100 * zahl(s.rest) / zahl(s.start))) : 0;
    return `<div class="row chev" data-s="${s.id}" style="cursor:pointer"><span class="dot" style="background:${C.farbe(s.farbe)};width:22px;height:22px"></span>
      <div class="grow"><div><b>${C.esc(spName(s))}</b>${s.kopf ? ` <span class="pill">Kopf ${s.kopf}</span>` : ""}</div>
        <div class="small">${zahl(s.rest).toFixed(0)} g von ${zahl(s.start).toFixed(0)} g${s.marke ? " · " + C.esc(s.marke) : ""}</div>
        <div class="balken" style="margin-top:6px"><i style="width:${p}%;background:${p < 15 ? "var(--red)" : p < 35 ? "var(--orange)" : "var(--green)"}"></i></div></div></div>`; }).join("")}</div>`;
  h += `<div style="height:16px"></div><button class="btn" id="spNeu">Spule hinzufügen</button>
    <p class="hint">Das Lager liegt nur in diesem Gerät. Verbrauch buchst du im Auftrag über „Verbrauch vom Filamentlager abbuchen“.</p><div style="height:20px"></div>`;
  app.innerHTML = h;
  binden(app, () => material(app));
  $("#spNeu").onclick = () => spuleBlatt(null, () => material(app));
  $$("[data-s]", app).forEach(r => r.onclick = () => spuleBlatt(spulen().find(x => x.id === r.dataset.s), () => material(app)));
}
function spuleBlatt(s, fertig){
  const neu = !s; s = s || {id: "s" + Date.now().toString(36), material: "PLA", farbe: "", marke: "", start: 1000, rest: 1000, preis: "", kopf: 0};
  const feld = (l, id, v, ph = "", mode = "text") => `<div class="row"><div class="grow">${l}</div><input type="text" inputmode="${mode}" id="${id}" value="${C.esc(v)}" placeholder="${ph}" style="flex:1"></div>`;
  const d = C.sheet(`<h3>${neu ? "Neue Spule" : C.esc(spName(s))}</h3><p>${neu ? "Was auf der Spule steht, reicht." : "Werte anpassen oder Verbrauch abziehen."}</p>
    <div class="card">
      <div class="row"><div class="grow">Material</div><select id="sMat">${SORTEN.map(x => `<option ${x === s.material ? "selected" : ""}>${x}</option>`).join("")}</select></div>
      ${feld("Farbe", "sFar", s.farbe, "z. B. schwarz")}${feld("Marke", "sMar", s.marke, "optional")}
      ${feld("Gewicht neu (g)", "sSta", s.start, "1000", "decimal")}${feld("Rest (g)", "sRes", s.rest, "1000", "decimal")}${feld("Preis (€)", "sPre", s.preis, "optional", "decimal")}
      <div class="row"><div class="grow">Sitzt in Kopf</div><select id="sKop">${[0, 1, 2, 3, 4].map(k => `<option value="${k}" ${k === (s.kopf || 0) ? "selected" : ""}>${k ? "Kopf " + k : "keiner"}</option>`).join("")}</select></div>
    </div>
    ${neu ? "" : `<h2>Verbrauch abziehen</h2><div class="card"><div class="row"><div class="grow">Gramm</div><input type="text" inputmode="decimal" id="sAb" placeholder="z. B. 42" style="flex:1"></div></div>`}
    <div style="height:14px"></div><button class="btn" id="sOk">Sichern</button>
    ${neu ? "" : `<button class="btn rot" id="sWeg">Spule löschen</button>`}<button class="btn grey" id="sZu">Abbrechen</button>`);
  const q = id => d.querySelector(id);
  q("#sZu").onclick = () => d.remove();
  q("#sOk").onclick = () => {
    let L = spulen().filter(x => x.id !== s.id);
    const n = {id: s.id, material: q("#sMat").value, farbe: q("#sFar").value.trim(), marke: q("#sMar").value.trim(),
      start: zahl(q("#sSta").value) || 1000, rest: zahl(q("#sRes").value), preis: q("#sPre").value.trim(), kopf: +q("#sKop").value};
    if (!neu && q("#sAb").value.trim()) n.rest = Math.max(0, n.rest - zahl(q("#sAb").value));
    if (n.rest > n.start) n.start = n.rest;
    if (n.kopf) L.forEach(x => { if (x.kopf === n.kopf) x.kopf = 0; });   // ein Kopf trägt nur eine Spule
    L.push(n); L.sort((a, b) => spName(a).localeCompare(spName(b), "de"));
    lsSet(SP, L); d.remove(); C.toast("Gespeichert"); fertig();
  };
  const w = q("#sWeg"); if (w) w.onclick = () => { lsSet(SP, spulen().filter(x => x.id !== s.id)); d.remove(); C.toast("Gelöscht"); fertig(); };
}
// Aus dem Auftrag: Gramm je Kopf von den passenden Spulen abziehen
export function abbuchen(a, ctx){
  C = ctx;
  const L = spulen(), gr = String(a.gramm).split(",").map(zahl), schon = ls("druckwerk_gebucht", {})[a.ordner];
  if (!L.length) {
    const d = C.sheet(`<h3>Noch kein Filamentlager</h3><p>Trag zuerst deine Spulen ein (Material → Mein Lager). Danach kannst du hier den Verbrauch abbuchen.</p>
      <button class="btn" id="bL">Zum Lager</button><button class="btn grey" id="bZ">Abbrechen</button>`);
    d.querySelector("#bZ").onclick = () => d.remove();
    d.querySelector("#bL").onclick = () => { d.remove(); U.mat = "lager"; C.go("material"); };
    return;
  }
  const gleich = (x, y) => (x || "").toLowerCase().replace(/ß/g, "ss").trim() === (y || "").toLowerCase().replace(/ß/g, "ss").trim();
  const vor = s => (L.find(x => x.kopf === s.slot && x.material.toUpperCase().startsWith(String(s.material).split("-")[0].toUpperCase()))
    || L.find(x => gleich(x.farbe, s.farbe) && x.material.toUpperCase().startsWith(String(s.material).split("-")[0].toUpperCase())) || {}).id || "";
  const d = C.sheet(`<h3>Verbrauch abbuchen</h3><p>${C.esc(a.name)}${schon ? `<br><b>Schon abgebucht am ${de(schon)}</b> – nur noch einmal buchen, wenn du erneut gedruckt hast.` : ""}</p>
    <div class="card">${a.slots.map((s, i) => { const v = vor(s);
      return `<div class="row"><span class="dot" style="background:${C.farbe(s.farbe)};width:22px;height:22px"></span>
        <div class="grow"><div>Kopf ${s.slot}: ${gr[i].toFixed(1)} g</div><div class="small">${C.esc(s.material)} ${C.esc(s.farbe)}</div></div>
        <select data-b="${i}"><option value="">nicht buchen</option>${L.map(x => `<option value="${x.id}" ${x.id === v ? "selected" : ""}>${C.esc(spName(x))} (${zahl(x.rest).toFixed(0)} g)</option>`).join("")}</select></div>`; }).join("")}</div>
    <div id="bWarn"></div><div style="height:14px"></div>
    <button class="btn" id="bOk">Abbuchen</button><button class="btn grey" id="bZu">Abbrechen</button>`);
  const pruefen = () => {
    const bedarf = {}; d.querySelectorAll("[data-b]").forEach(e => { if (e.value) bedarf[e.value] = (bedarf[e.value] || 0) + gr[+e.dataset.b]; });
    const eng = Object.entries(bedarf).map(([id, g]) => [L.find(x => x.id === id), g]).filter(([x, g]) => zahl(x.rest) < g);
    d.querySelector("#bWarn").innerHTML = eng.map(([x, g]) => `<div class="warn">⚠ ${C.esc(spName(x))}: es fehlen ${(g - zahl(x.rest)).toFixed(0)} g.</div>`).join("");
    return bedarf;
  };
  d.querySelectorAll("[data-b]").forEach(e => e.onchange = pruefen); pruefen();
  d.querySelector("#bZu").onclick = () => d.remove();
  d.querySelector("#bOk").onclick = () => {
    const bedarf = pruefen(); if (!Object.keys(bedarf).length) return C.toast("Keine Spule gewählt");
    for (const [id, g] of Object.entries(bedarf)) { const x = L.find(y => y.id === id); x.rest = Math.max(0, +(zahl(x.rest) - g).toFixed(1)); }
    lsSet(SP, L); const G = ls("druckwerk_gebucht", {}); G[a.ordner] = heute(); lsSet("druckwerk_gebucht", G);
    d.remove(); C.toast("Abgebucht");
  };
}

/* ---------- Zubehör (Haken nur auf diesem Gerät) ---------- */
function zubehoer(app, kopf){
  const z = D.z, habe = ls("druckwerk_habe", {}), alle = z.gruppen.flatMap(g => g.teile);
  const pc = {Muss: "p1", Sinnvoll: "p2", "Später": "p3"};
  const passt = t => U.zub === "alle" || (U.zub === "fehlt" && !habe[t.id]) || (U.zub === "muss" && t.prio === "Muss");
  app.innerHTML = kopf + `<div class="stats">
    <div class="stat"><span class="small">Teile</span><b>${alle.length}</b></div>
    <div class="stat"><span class="small">Vorhanden</span><b>${alle.filter(t => habe[t.id]).length}</b></div>
    <div class="stat"><span class="small">Muss offen</span><b>${alle.filter(t => t.prio === "Muss" && !habe[t.id]).length}</b></div></div>
  <div style="height:12px"></div>${seg("zub", [["alle", "Alle"], ["fehlt", "Fehlt noch"], ["muss", "Muss"]])}
  ${z.gruppen.map(g => { const t = g.teile.filter(passt); if (!t.length) return "";
    return `<h2>${C.esc(g.name)}</h2><div class="card">${t.map(x => `
      <div class="row oben"><button class="haken ${habe[x.id] ? "on" : ""}" data-h="${x.id}" aria-label="vorhanden">${habe[x.id] ? "✓" : ""}</button>
        <div class="grow"><div><b>${C.esc(x.name)}</b><span class="pr ${pc[x.prio]}">${x.prio}</span></div>
          <div class="small">${C.esc(x.wozu)}</div>
          <div class="small" style="margin-top:4px;color:var(--text)">${C.esc(x.preis || "")}${x.link ? ` · <a href="${C.esc(x.link)}" target="_blank" rel="noopener" style="color:var(--blue);text-decoration:none">Zum Shop ›</a>` : ""}</div></div></div>`).join("")}</div>
      <p class="hint">${C.esc(g.text)}</p>`; }).join("") || `<div class="empty">Alles da.</div>`}
  <p class="hint">${C.esc(z.hinweis)}</p>${quellen(z.quellen, z.stand)}`;
  binden(app, () => material(app));
  $$("[data-h]", app).forEach(b => b.onclick = () => { const H = ls("druckwerk_habe", {}); if (H[b.dataset.h]) delete H[b.dataset.h]; else H[b.dataset.h] = 1;
    lsSet("druckwerk_habe", H); const y = scrollY; material(app); scrollTo(0, y); });
}

/* ================= Drucker ================= */
function drucker(app){
  const c = D.c, neu = () => drucker(app);
  let h = `<h1>Creator 5 Pro</h1>${seg("dr", [["ueberblick", "Überblick"], ["einrichten", "Einrichten"], ["wartung", "Wartung"], ["hilfe", "Hilfe"]])}`;
  if (U.dr === "ueberblick") {
    const k = C.DRUCKER.kobrax;
    h += `<h2>Steckbrief</h2><div class="card">${c.steckbrief.map(([a, b]) => `<div class="row"><div class="grow">${C.esc(a)}</div><span class="val" style="max-width:62%">${C.esc(b)}</span></div>`).join("")}</div>
    <h2>Stärken</h2>${liste(c.staerken)}<h2>Grenzen</h2>${liste(c.grenzen)}
    <h2>Programme</h2>${liste(c.software)}<h2>Stand in druckwerk</h2>${liste(c.druckwerk)}
    <h2>Per USB drucken (iPhone / iPad)</h2><div class="card"><ol class="steps">${c.usb.map(x => `<li>${C.esc(x)}</li>`).join("")}</ol></div>
    ${k ? `<h2>Früher: ${C.esc(k.name)}</h2><div class="card"><div class="row"><div class="grow small">Offen, vier Farben über eine Düse, Bauraum ${k.bauraum_mm.join(" × ")} mm. Alte Aufträge mit „Kobra X“ laufen nicht auf dem Creator 5 Pro – sie müssen neu gesliced werden.</div></div></div>` : ""}
    <p class="hint">${C.esc(c.hinweis)}</p>${quellen(c.quellen, c.stand)}`;
  } else if (U.dr === "einrichten") {
    const E = ls("druckwerk_c5_ein", {}), n = c.einrichten.filter(x => E[x.id]).length;
    h += `<h2>Erste Einrichtung · ${n} von ${c.einrichten.length} erledigt</h2>
    <div class="balken" style="margin:0 2px 10px"><i style="width:${100 * n / c.einrichten.length}%;background:var(--green)"></i></div>
    <div class="card">${c.einrichten.map(x => `<div class="row oben"><button class="haken ${E[x.id] ? "on" : ""}" data-e="${x.id}" aria-label="erledigt">${E[x.id] ? "✓" : ""}</button>
      <div class="grow"><div><b>${C.esc(x.t)}</b></div><div class="small">${C.esc(x.d)}</div></div></div>`).join("")}</div>
    <h2>Vor jedem Druck</h2>${liste(c.vorDruck)}<h2>Zeit und Material sparen</h2>${liste(c.zeitSparen)}<div style="height:20px"></div>`;
  } else if (U.dr === "wartung") {
    const W = ls("druckwerk_c5_wartung", {}), jetzt = Date.now();
    h += `<h2>Wartungsplan</h2><div class="card">${c.wartung.map(x => { const l = W[x.id], alt = l ? Math.floor((jetzt - new Date(l)) / 864e5) : null;
      const faellig = x.tage > 0 && (alt === null || alt >= x.tage);
      return `<div class="row oben"><div class="grow"><div><b>${C.esc(x.t)}</b>${faellig ? `<span class="pr p2">fällig</span>` : ""}</div>
        <div class="small">${C.esc(x.i)}</div>${x.tage > 0 ? `<div class="small">Zuletzt: ${l ? de(l) + (alt ? ` (vor ${alt} Tagen)` : " (heute)") : "noch nicht eingetragen"}</div>` : ""}</div>
        ${x.tage > 0 ? `<button class="wb klein" data-w="${x.id}">Erledigt</button>` : ""}</div>`; }).join("")}</div>
    <p class="hint">„Erledigt“ merkt sich das heutige Datum in diesem Gerät. Die Abstände sind Richtwerte; nur die 1500 Druckstunden fürs Fetten stammen aus dem Flashforge-Wiki.</p>
    <h2>Firmware-Verlauf</h2><div class="card">${c.firmware.map(([v, d, t]) => `<div class="row oben"><div style="flex:none;width:62px"><b>${v}</b><div class="small">${C.esc(d)}</div></div><div class="grow small" style="color:var(--text)">${C.esc(t)}</div></div>`).join("")}</div><div style="height:20px"></div>`;
  } else {
    h += `<div style="height:12px"></div><div class="card"><div class="row"><input type="text" id="pSuch" placeholder="Problem oder Fehlercode suchen" style="flex:1"></div></div>
    <h2>Probleme und Lösungen</h2><div id="pListe">${c.probleme.map(p => `<div class="card pk" style="margin-bottom:10px"><div class="row"><div class="grow"><div><b>${C.esc(p.t)}</b></div>
      <div class="small" style="margin-top:4px"><b>Ursache:</b> ${C.esc(p.u)}</div><div style="font-size:15px;margin-top:4px"><b>Lösung:</b> ${C.esc(p.l)}</div></div></div></div>`).join("")}</div>
    <p class="hint">Kommst du nicht weiter: Foto oder Fehlercode an Claude schicken („druckwerk: Problem …“). Offizielle Hilfe: wiki.flashforge.com.</p><div style="height:20px"></div>`;
  }
  app.innerHTML = h;
  binden(app, neu);
  $$("[data-e]", app).forEach(b => b.onclick = () => { const E = ls("druckwerk_c5_ein", {}); if (E[b.dataset.e]) delete E[b.dataset.e]; else E[b.dataset.e] = heute();
    lsSet("druckwerk_c5_ein", E); const y = scrollY; neu(); scrollTo(0, y); });
  $$("[data-w]", app).forEach(b => b.onclick = () => { const W = ls("druckwerk_c5_wartung", {}); W[b.dataset.w] = heute(); lsSet("druckwerk_c5_wartung", W);
    const y = scrollY; neu(); scrollTo(0, y); C.toast("Eingetragen"); });
  const s = $("#pSuch"); if (s) s.oninput = () => { const q = s.value.toLowerCase().trim();
    $$(".pk", app).forEach(k => k.style.display = !q || k.textContent.toLowerCase().includes(q) ? "" : "none"); };
}

/* ================= Workflow ================= */
function workflow(app){
  const w = D.w, neu = () => workflow(app);
  let h = `<h1>Von der Idee zum Modell</h1>${seg("wf", [["weg", "Weg"], ["werkzeuge", "Werkzeuge"], ["vorschlaege", "Vorschläge"]])}`;
  if (U.wf === "weg") {
    const g = w.wege.find(x => x.id === U.weg) || w.wege[0];
    h += `<h2>Womit fängst du an?</h2>${chips("weg", w.wege.map(x => [x.id, x.name]))}
    <p class="hint">${C.esc(g.kurz)}</p>
    <h2>${g.schritte.length} Schritte</h2><div class="card">${g.schritte.map((s, i) => `<div class="row oben"><span class="nr">${i + 1}</span>
      <div class="grow"><div><b>${C.esc(s.t)}</b> <span class="pill">${C.esc(s.wer)}</span></div><div class="small">${C.esc(s.d)}</div></div></div>`).join("")}</div>
    <div style="height:16px"></div><button class="btn" id="wStart">Auftrag so beginnen</button>
    <p class="hint">Füllt unter „Neu“ eine Vorlage aus, die genau die Angaben abfragt, die Claude für diesen Weg braucht.</p><div style="height:20px"></div>`;
  } else if (U.wf === "werkzeuge") {
    h += w.werkzeuge.map(g => `<h2>${C.esc(g.gruppe)}</h2><div class="card">${g.liste.map(t => { const innen = `<div class="grow"><div><b>${C.esc(t.name)}</b> <span class="pill">${C.esc(t.wo)}</span></div>
        <div class="small">${C.esc(t.d)}</div>${t.preis && t.preis !== "–" ? `<div class="small" style="color:var(--text);margin-top:3px">${C.esc(t.preis)}</div>` : ""}</div>`;
      return t.url ? `<a class="row chev oben" href="${C.esc(t.url)}" target="_blank" rel="noopener" style="color:inherit;text-decoration:none">${innen}</a>` : `<div class="row oben">${innen}</div>`; }).join("")}</div>`).join("")
      + `<p class="hint">Preise sind Stand ${C.esc(w.stand)} und ändern sich. „Claude“ = erledige ich im Auftrag, du brauchst dafür nichts zu installieren.</p>` + quellen(w.quellen, w.stand);
  } else {
    const wahl = ls("druckwerk_wunsch", []);
    h += `<p class="hint" style="margin-top:14px">So würde ich druckwerk zum Komplettprogramm ausbauen. Tipp an, was du willst – unten entsteht daraus ein Auftrag an Claude.</p>
    <div class="card" style="margin-top:10px">${w.vorschlaege.map(v => `<div class="row oben"><button class="haken ${wahl.includes(v.id) ? "on" : ""}" data-v2="${v.id}" aria-label="auswählen">${wahl.includes(v.id) ? "✓" : ""}</button>
      <div class="grow"><div><b>${C.esc(v.t)}</b></div><div class="small">${C.esc(v.nutzen)}</div>
        <div class="werte"><span>Aufwand: ${C.esc(v.aufwand)}</span><span>${C.esc(v.status)}</span></div></div></div>`).join("")}</div>
    <div style="height:16px"></div>
    <button class="btn" id="vKop" ${wahl.length ? "" : "disabled style='opacity:.4'"}>Auswahl kopieren (${wahl.length})</button>
    <a class="btn grey" id="vAuf" target="_blank" ${wahl.length ? "" : "style='opacity:.4;pointer-events:none'"}>In Claude öffnen</a><div style="height:20px"></div>`;
  }
  app.innerHTML = h;
  binden(app, neu);
  const st = $("#wStart"); if (st) st.onclick = () => { const g = w.wege.find(x => x.id === U.weg) || w.wege[0]; C.neuStart(g.vorlage, g.zweck); };
  $$("[data-v2]", app).forEach(b => b.onclick = () => { let L = ls("druckwerk_wunsch", []); L = L.includes(b.dataset.v2) ? L.filter(x => x !== b.dataset.v2) : [...L, b.dataset.v2];
    lsSet("druckwerk_wunsch", L); const y = scrollY; neu(); scrollTo(0, y); });
  const text = () => "druckwerk: Bitte diese Vorschläge aus der App umsetzen:\n" + w.vorschlaege.filter(v => ls("druckwerk_wunsch", []).includes(v.id)).map(v => "- " + v.t).join("\n");
  const k = $("#vKop"); if (k) k.onclick = async () => { try { await navigator.clipboard.writeText(text()); C.toast("Kopiert"); } catch (e) { C.toast("Bitte in Claude öffnen"); } };
  const a = $("#vAuf"); if (a) a.href = "https://claude.ai/new?q=" + encodeURIComponent(text());
}
