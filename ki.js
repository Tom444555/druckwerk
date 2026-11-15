// ki.js – „Aus Foto erzeugen (KI)“: Fotos → GitHub (eingang/<id>/ki.json) → Action generieren.yml (fal.ai oder Hugging Face)
//   → ki/<id>/ (STL, GLB, Vorschau) → automatisch in „Meine Modelle“ übernehmen und in der Werkstatt öffnen.
// Der fal-Schlüssel liegt nur als Secret FAL_KEY im GitHub-Lager; die App braucht nur den vorhandenen GitHub-Zugang (Slicen).
const REPO = "Tom444555/druckwerk", TOK = "druckwerk_token";
const KI = "druckwerk_ki";            // Merkzettel der laufenden Erzeugung {id, name, dienst, kosten, start} – übersteht Neuladen
const KI_EIN = "druckwerk_ki_ein";    // Nutzer hat bestätigt: Secret FAL_KEY ist eingetragen
const KI_WAHL = "druckwerk_ki_wahl";  // zuletzt gewählter Dienst, Qualität, Größe
const ls = { get: k => { try { return localStorage.getItem(k); } catch (e) { return null; } },
  set: (k, v) => { try { v == null ? localStorage.removeItem(k) : localStorage.setItem(k, v); } catch (e) {} },
  json: (k, d) => { try { return JSON.parse(localStorage.getItem(k)) ?? d; } catch (e) { return d; } } };
let C = null;

// Preise je Lauf laut fal-Doku (Stand 15.11.2026) – gleiche Tabelle wie werkzeug/generieren.py
export const DIENSTE = [
  {id: "trellis2", name: "TRELLIS.2", preis: {schnell: .25, standard: .30, hoch: .35}, bilder: 1,
   stufen: ["512", "1024", "1536"], text: "Bester Allrounder fürs Geld: viel Detail, scharfe Kanten. Ein Foto."},
  {id: "rodin", name: "Hyper3D Rodin Gen‑2.5", preis: {schnell: .40, standard: .40, hoch: .40}, bilder: 5,
   stufen: ["Medium", "High", "Extreme-High"], text: "Spitzenqualität für Figuren und Deko. Bis 5 Fotos aus verschiedenen Richtungen, Beschreibung möglich."},
  {id: "hunyuan", name: "Hunyuan3D 3.1 Pro", preis: {schnell: .375, standard: .375, hoch: .375}, mehr: .15, bilder: 4,
   ansichten: ["vorne", "hinten", "links", "rechts"], text: "Sehr feine, dichte Netze. Foto 2–4 = hinten / links / rechts (+0,15 $)."},
  {id: "hf-trellis2", name: "TRELLIS.2 gratis (Hugging Face)", preis: {schnell: 0, standard: 0, hoch: 0}, bilder: 1,
   stufen: ["512", "1024", "1536"], text: "Kostenlos, aber experimentell: wenige Läufe am Tag, kann ausfallen. Secret HF_TOKEN empfohlen."},
];
export const kosten = (d, q, n) => { const x = DIENSTE.find(y => y.id === d) || DIENSTE[0]; return (x.preis[q] ?? x.preis.standard) + (x.mehr && n > 1 ? x.mehr : 0); };
export const preisText = p => p ? "ca. " + p.toFixed(3).replace(/0$/, "").replace(".", ",") + " $" : "gratis";

/* ---------- GitHub ---------- */
async function gh(pfad, opt = {}){
  return fetch(`https://api.github.com/repos/${REPO}${pfad}`, {...opt, cache: "no-store",
    headers: {Authorization: "Bearer " + ls.get(TOK), Accept: opt.roh ? "application/vnd.github.raw+json" : "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}});
}
function b64(buf){ const u = new Uint8Array(buf); let s = ""; for (let i = 0; i < u.length; i += 32768) s += String.fromCharCode.apply(null, u.subarray(i, i + 32768)); return btoa(s); }
const ablegen = async (pfad, inhalt, text) => { const r = await gh("/contents/" + pfad, {method: "PUT", body: JSON.stringify({message: text, content: inhalt})});
  if (!r.ok) throw new Error(r.status === 401 || r.status === 403 ? "GitHub-Zugang abgelaufen oder ohne Schreibrecht – unter Start → Gerät & Daten neu einrichten." : "Hochladen fehlgeschlagen (" + r.status + ")"); };

/* ---------- Einstieg ---------- */
export function oeffnen(ctx){
  C = ctx;
  const o = ls.json(KI, null);
  if (o && Date.now() - o.start < 2 * 3600e3 && ls.get(TOK)) return fortschritt(o);
  if (!ls.get(TOK) || !ls.get(KI_EIN)) return hilfe(ctx, () => formular());
  formular();
}

/* ---------- Einrichtung (für Nicht-Programmierer) ---------- */
export function hilfe(ctx, weiter){
  C = ctx || C;
  const tok = !!ls.get(TOK), ein = !!ls.get(KI_EIN);
  const a = (u, t) => `<a href="${u}" target="_blank" rel="noopener" style="color:var(--blue)">${t}</a>`;
  const d = C.sheet(`<h3>Einrichtung: 3D-Modell aus Foto</h3>
    <p>Einmalig, etwa 10 Minuten. Gerechnet wird bei fal.ai, bezahlt von deinem eigenen Guthaben (je Modell 0,25–0,53 $).</p>
    <h2>1 · GitHub-Zugang der App</h2><div class="card"><div class="row">
      <span class="haken ${tok ? "on" : ""}" aria-hidden="true">${tok ? "✓" : ""}</span>
      <div class="grow">${tok ? "Eingerichtet – der Zugang fürs Slicen genügt, du brauchst keinen neuen." : "Fehlt noch. Derselbe Zugang wie beim Slicen aus der Werkstatt."}</div>
      ${tok ? "" : `<button class="wb klein" id="hTok">Einrichten</button>`}</div></div>
    <h2>2 · fal.ai-Konto und Guthaben</h2><div class="card"><ol class="steps">
      <li>${a("https://fal.ai/login", "fal.ai öffnen")} → anmelden (z. B. mit deinem GitHub- oder Google-Konto).</li>
      <li>${a("https://fal.ai/dashboard/billing", "Billing")} → Guthaben aufladen, z. B. 5 $ (reicht für etwa 10–20 Modelle).</li></ol></div>
    <h2>3 · Schlüssel erzeugen</h2><div class="card"><ol class="steps">
      <li>${a("https://fal.ai/dashboard/keys", "Keys")} → „Add key“, Name <b>druckwerk</b>, Scope <b>API</b>.</li>
      <li>Schlüssel kopieren – er wird nur einmal angezeigt.</li></ol></div>
    <h2>4 · Schlüssel ins GitHub-Lager</h2><div class="card"><ol class="steps">
      <li>${a(`https://github.com/${REPO}/settings/secrets/actions`, "GitHub → druckwerk → Settings → Secrets and variables → Actions")} öffnen.</li>
      <li>„New repository secret“ antippen.</li>
      <li>Name: <b>FAL_KEY</b> (genau so) · Secret: Schlüssel einfügen → „Add secret“.</li></ol></div>
    <p class="hint">Der Schlüssel liegt nur bei GitHub – nicht in der App, nicht auf dem Gerät. Fehlt er oder ist das Guthaben leer, meldet die App das nach dem Versuch.</p>
    <h2>Gratis-Weg (optional, experimentell)</h2><div class="card"><ol class="steps">
      <li>${a("https://huggingface.co/settings/tokens", "huggingface.co → Access Tokens")} → „Create new token“, Typ <b>Read</b>.</li>
      <li>Wie in Schritt 4 als Secret <b>HF_TOKEN</b> eintragen. Dann im Formular „TRELLIS.2 gratis“ wählen.</li></ol></div>
    <div style="height:14px"></div>
    <button class="btn" id="hOk" ${tok ? "" : "disabled style='opacity:.4'"}>${ein ? "Weiter" : "FAL_KEY ist eingetragen – weiter"}</button>
    <button class="btn grey" id="hZu">Später</button>`);
  d.querySelector("#hZu").onclick = () => d.remove();
  const t = d.querySelector("#hTok");
  if (t) t.onclick = async () => { d.remove(); try { (await import("./werkstatt.js")).zugangEinrichten(C, () => hilfe(C, weiter)); } catch (e) { C.toast("Konnte nicht geladen werden"); } };
  d.querySelector("#hOk").onclick = () => { if (!ls.get(TOK)) return; ls.set(KI_EIN, "1"); d.remove(); if (weiter) weiter(); };
}

/* ---------- Formular ---------- */
const S = {fotos: [], name: "", mm: 100, dienst: "trellis2", qualitaet: "standard", text: ""};
function formular(){
  Object.assign(S, {...ls.json(KI_WAHL, {}), fotos: S.fotos});
  const d = C.sheet(""), box = d.firstElementChild;
  const mal = () => {
    const y = box.scrollTop, D = DIENSTE.find(x => x.id === S.dienst) || DIENSTE[0];
    const n = Math.min(S.fotos.length, D.bilder), p = kosten(D.id, S.qualitaet, n);
    box.innerHTML = `<h3>Aus Foto erzeugen (KI)</h3><p>Ein Foto wird per KI zum 3D-Modell. Fertig nach meist 2–6 Minuten, dann liegt es unter „Meine Modelle“.</p>
    <h2>Fotos (${S.fotos.length}/${D.bilder})</h2>
    ${S.fotos.length ? `<div class="kifotos">${S.fotos.map((f, i) => `<div class="kifoto${i >= D.bilder ? " aus" : ""}"><img src="${f.mini}" alt="Foto ${i + 1}">
      <span>${i >= D.bilder ? "wird nicht genutzt" : D.ansichten ? D.ansichten[i] : i + 1}</span><button data-weg="${i}" aria-label="Foto ${i + 1} entfernen">×</button></div>`).join("")}</div><div style="height:10px"></div>` : ""}
    <label class="btn grey">${S.fotos.length ? "Weiteres Foto" : "Foto aufnehmen oder wählen"}<input type="file" id="kFoto" accept="image/*" multiple hidden></label>
    <div class="card" style="margin-top:10px"><div class="row chev" id="kTipps" style="cursor:pointer" role="button" tabindex="0"><div class="grow">Tipps für gute Fotos</div></div></div>
    <h2>Modell</h2><div class="card">
      <div class="row"><div class="grow">Name</div><input type="text" id="kName" value="${C.esc(S.name)}" placeholder="z. B. Hund Bello" style="max-width:60%"></div>
      <div class="row"><div class="grow">Größe (längste Kante)</div><input type="text" inputmode="numeric" id="kMm" value="${C.esc(S.mm)}" style="max-width:70px"><span class="small">mm</span></div></div>
    <h2>Dienst</h2><div class="card">${DIENSTE.map(x => `<div class="row oben" data-d="${x.id}" style="cursor:pointer" role="button" tabindex="0">
      <span class="haken ${x.id === D.id ? "on" : ""}" aria-hidden="true">${x.id === D.id ? "✓" : ""}</span>
      <div class="grow"><div><b>${C.esc(x.name)}</b> <span class="pill${x.preis.standard ? "" : " gruen"}">${x.preis.standard ? (x.id === "trellis2" ? "0,25–0,35 $" : preisText(x.preis.standard)) : "gratis"}</span></div>
        <div class="small">${C.esc(x.text)}</div></div></div>`).join("")}</div>
    ${D.stufen ? `<h2>Qualität</h2><div class="seg">${[["schnell", "Schnell"], ["standard", "Standard"], ["hoch", "Hoch"]].map(([v, l], i) =>
      `<button data-q="${v}" class="${S.qualitaet === v ? "on" : ""}">${l} · ${D.stufen[i]}</button>`).join("")}</div>` : ""}
    ${D.id === "rodin" ? `<h2>Beschreibung (optional)</h2><div class="card"><textarea id="kText" placeholder="z. B. sitzender Hund, glatte Oberfläche">${C.esc(S.text)}</textarea></div>` : ""}
    <div class="warn">KI-Modelle sind <b>nicht maßhaltig</b>: gut für Figuren und Deko. Technische Teile (Halter, Passungen) besser über <a href="#" id="kNeu" style="color:var(--blue)">„Neu“</a>.</div>
    <p class="hint">Nur eigene oder freie Motive. Das Foto wird in dein GitHub-Lager hochgeladen (ist es öffentlich, kann es jeder sehen; es bleibt in der Versionsgeschichte) und an ${D.id === "hf-trellis2" ? "Hugging Face" : "fal.ai"} übertragen.</p>
    <div style="height:14px"></div>
    <button class="btn" id="kLos" ${S.fotos.length ? "" : "disabled style='opacity:.4'"}>Erzeugen · ${preisText(p)}</button>
    <button class="btn grey" id="kZu">Abbrechen</button>
    <p class="hint" style="text-align:center"><a href="#" id="kHilfe" style="color:var(--sub)">Einrichtung &amp; Hilfe</a></p>`;
    box.scrollTop = y;
    const merk = () => ls.set(KI_WAHL, JSON.stringify({dienst: S.dienst, qualitaet: S.qualitaet, mm: S.mm}));
    box.querySelector("#kFoto").onchange = async e => {
      const fs = [...e.target.files]; e.target.value = ""; if (!fs.length) return;
      for (const f of fs.slice(0, 8 - S.fotos.length)) { try { S.fotos.push(await verkleinern(f)); } catch (x) { C.toast("Foto konnte nicht gelesen werden"); } }
      mal(); };
    box.querySelectorAll("[data-weg]").forEach(b => b.onclick = () => { S.fotos.splice(+b.dataset.weg, 1); mal(); });
    box.querySelector("#kName").oninput = e => { S.name = e.target.value; };
    box.querySelector("#kMm").oninput = e => { S.mm = e.target.value; };
    box.querySelector("#kMm").onchange = () => { merk(); };
    box.querySelectorAll("[data-d]").forEach(r => r.onclick = r.onkeydown = e => { if (e.type === "keydown" && e.key !== "Enter") return; S.dienst = r.dataset.d; merk(); mal(); });
    box.querySelectorAll("[data-q]").forEach(b => b.onclick = () => { S.qualitaet = b.dataset.q; merk(); mal(); });
    const tx = box.querySelector("#kText"); if (tx) tx.oninput = e => { S.text = e.target.value; };
    box.querySelector("#kTipps").onclick = box.querySelector("#kTipps").onkeydown = e => { if (e.type === "keydown" && e.key !== "Enter") return; tipps(); };
    box.querySelector("#kNeu").onclick = e => { e.preventDefault(); d.remove(); C.go("neu"); };
    box.querySelector("#kHilfe").onclick = e => { e.preventDefault(); d.remove(); hilfe(C, () => formular()); };
    box.querySelector("#kZu").onclick = () => d.remove();
    box.querySelector("#kLos").onclick = () => {
      if (!S.fotos.length) return C.toast("Erst ein Foto wählen");
      const mm = Math.round(parseFloat(String(S.mm).replace(",", ".")));
      if (!(mm >= 10 && mm <= 256)) return C.toast("Größe: 10 bis 256 mm");
      S.mm = mm; merk(); bestaetigen(d, D, n, p);
    };
  };
  mal();
}

function tipps(){
  const d = C.sheet(`<h3>Tipps für gute Fotos</h3><div class="card"><ol class="steps">
    <li><b>Ein Objekt</b>, das mehr als die Hälfte des Bildes füllt.</li>
    <li><b>Ruhiger, einfarbiger Hintergrund</b> (Wand, Tuch) – oder vorher freistellen (iPhone: Motiv lange drücken → „Kopieren“ / „Sticker“).</li>
    <li><b>Gleichmäßiges Licht</b>, keine harten Schatten, kein Blitz-Glanz.</li>
    <li>Leicht <b>von schräg oben</b> und ganz im Bild – nichts abgeschnitten.</li>
    <li>Bei Rodin und Hunyuan: <b>weitere Fotos</b> von hinten und von der Seite machen die Rückseite deutlich besser.</li>
    <li>Dünne Teile (Finger, Antennen, Haare) werden oft zu fein – lieber kompakte Motive.</li></ol></div>
    <div style="height:12px"></div><button class="btn grey" id="tZu">Fertig</button>`);
  d.querySelector("#tZu").onclick = () => d.remove();
}

async function verkleinern(file){                    // auf max. 1536 px, JPEG – spart Upload und passt für alle Dienste
  const url = URL.createObjectURL(file);
  try {
    const img = await new Promise((ok, err) => { const i = new Image(); i.onload = () => ok(i); i.onerror = err; i.src = url; });
    const w = img.naturalWidth, h = img.naturalHeight, s = Math.min(1, 1536 / Math.max(w, h));
    const c = document.createElement("canvas"); c.width = Math.max(1, Math.round(w * s)); c.height = Math.max(1, Math.round(h * s));
    const g = c.getContext("2d"); g.fillStyle = "#fff"; g.fillRect(0, 0, c.width, c.height); g.drawImage(img, 0, 0, c.width, c.height);
    const blob = await new Promise((ok, err) => c.toBlob(b => b ? ok(b) : err(new Error("toBlob")), "image/jpeg", .9));
    const k = document.createElement("canvas"), ks = 200 / Math.max(c.width, c.height);
    k.width = Math.round(c.width * ks); k.height = Math.round(c.height * ks); k.getContext("2d").drawImage(c, 0, 0, k.width, k.height);
    return {blob, mini: k.toDataURL("image/jpeg", .7), b: c.width, h: c.height};
  } finally { URL.revokeObjectURL(url); }
}

function bestaetigen(form, D, n, p){
  const d = C.sheet(`<h3>${p ? `Kostet ${preisText(p)}` : "Kostenlos erzeugen"}</h3>
    <p>${p ? `${preisText(p).replace("ca. ", "Ca. ")} werden von deinem <b>fal-Guthaben</b> abgebucht` : "Läuft über Hugging Face (Gratis-Kontingent)"} · ${C.esc(D.name)} · ${n} Foto${n > 1 ? "s" : ""} · ${C.esc(S.mm)} mm</p>
    ${p ? `<div class="warn">Auch ein misslungener Versuch (z. B. ungeeignetes Foto) kann Guthaben kosten.</div>` : `<div class="warn">Experimentell: kann am Tageskontingent oder an Änderungen des Space scheitern.</div>`}
    <div style="height:14px"></div>
    <button class="btn" id="bJa">${p ? `Ja, für ${preisText(p)} erzeugen` : "Ja, gratis erzeugen"}</button><button class="btn grey" id="bNein">Abbrechen</button>`);
  d.querySelector("#bNein").onclick = () => d.remove();
  d.querySelector("#bJa").onclick = () => { d.remove(); form.remove(); losschicken(D, n, p); };
}

/* ---------- Abschicken, Warten, Übernehmen ---------- */
let LAUF = null;                                      // {id, versprechen, d (Fortschritts-Blatt), zeige}
async function losschicken(D, n, p){
  const id = "k" + Date.now().toString(36), name = String(S.name || "").trim() || "KI-Modell";
  const o = {id, name, dienst: D.id, kosten: p, start: Date.now()};
  const {d, sag} = blatt(o, "Fotos werden hochgeladen …");
  try {
    const fotos = S.fotos.slice(0, n), namen = [];
    for (const [i, f] of fotos.entries()) {
      sag(`Foto ${i + 1} von ${fotos.length} wird hochgeladen …`, 3 + 12 * i / fotos.length);
      await ablegen(`eingang/${id}/${i + 1}.jpg`, b64(await f.blob.arrayBuffer()), `App: Foto ${i + 1} für ${name}`); namen.push(`${i + 1}.jpg`);
    }
    const job = {name, dienst: D.id, bild: namen, ziel_mm: S.mm, qualitaet: D.stufen ? S.qualitaet : "standard", ...(D.id === "rodin" && S.text.trim() ? {text: S.text.trim()} : {})};
    sag("Auftrag wird abgeschickt …", 16);
    await ablegen(`eingang/${id}/ki.json`, btoa(unescape(encodeURIComponent(JSON.stringify(job)))), `App: KI-Modell ${name}`);
    ls.set(KI, JSON.stringify(o)); S.fotos = []; S.name = ""; S.text = "";
  } catch (e) { console.error(e); sag("Fehler: " + (e.message || e), 0); const b = d.querySelector("#kfZu"); if (b) b.textContent = "Schließen"; return; }
  verfolgen(o, d, sag);
}

function blatt(o, text){                             // Fortschritts-Blatt
  const d = C.sheet(`<h3>„${C.esc(o.name)}“ wird erzeugt</h3><p id="kfText">${C.esc(text)}</p><div class="balken"><i id="kfBalken"></i></div>
    <p class="small" style="margin-top:10px;text-align:center">Meist 2–6 Minuten. Du kannst die App schließen – beim nächsten Öffnen geht es hier weiter.</p>
    <button class="btn grey" id="kfZu">Im Hintergrund weiter</button>`);
  d.onclick = null; d.querySelector("#kfZu").onclick = () => d.remove();
  const sag = (t, p) => { const e = d.querySelector("#kfText"); if (e) { e.textContent = t; d.querySelector("#kfBalken").style.width = p + "%"; } };
  return {d, sag};
}

function fortschritt(o){ const {d, sag} = blatt(o, "KI rechnet …"); verfolgen(o, d, sag); }

function verfolgen(o, d, sag){
  if (LAUF && LAUF.id === o.id) { LAUF.d = d; LAUF.zeige = sag; return LAUF.versprechen; }
  LAUF = {id: o.id, d, zeige: sag};
  const L = LAUF;
  L.versprechen = warten(o, (t, p) => L.zeige && L.zeige(t, p)).then(mid => abschluss(o, L, mid, null), e => abschluss(o, L, null, e));
  return L.versprechen;
}

function abschluss(o, L, mid, fehler){
  if (LAUF === L) LAUF = null;
  const offen = L.d && document.body.contains(L.d);
  if (mid) {
    import("./kiweg.js").then(K => { if (K.modellFertig(mid)) C.toast("Danach im KI-Ablauf: Schritt 5 · Modell prüfen"); }).catch(() => {});
    if (offen) L.d.remove();
    if (offen) { C.go("werkstatt:e:" + mid); C.toast("KI-Modell ist fertig"); return; }
    const d = C.sheet(`<h3>KI-Modell „${C.esc(o.name)}“ ist fertig</h3><p>Es liegt jetzt unter Bibliothek → Meine Modelle.</p>
      <button class="btn" id="fOk">In der Werkstatt öffnen</button><button class="btn grey" id="fZu">Später</button>`);
    d.querySelector("#fOk").onclick = () => { d.remove(); C.go("werkstatt:e:" + mid); };
    d.querySelector("#fZu").onclick = () => d.remove();
    return;
  }
  const t = String((fehler && fehler.message) || fehler || "Unbekannter Fehler"), einr = /Schlüssel|FAL_KEY|HF_TOKEN|Guthaben|GitHub-Zugang/.test(t);
  if (offen) L.d.remove();
  const d = C.sheet(`<h3>Erzeugen hat nicht geklappt</h3><p>„${C.esc(o.name)}“</p><div class="warn">${C.esc(t)}</div><div style="height:14px"></div>
    ${einr ? `<button class="btn" id="eHi">Einrichtung öffnen</button>` : ""}<button class="btn grey" id="eZu">Schließen</button>`);
  d.querySelector("#eZu").onclick = () => d.remove();
  const h = d.querySelector("#eHi"); if (h) h.onclick = () => { d.remove(); hilfe(C, () => formular()); };
}

// wartet auf status/<id>.json (von generieren.py), lädt die STL und legt sie unter „Meine Modelle“ ab → Modell-ID
async function warten(o, sag){
  const pause = ms => new Promise(r => setTimeout(r, ms));
  let st = null;
  for (let i = 0; !st; i++) {
    const min = (Date.now() - o.start) / 60000;
    if (min > 40) { ls.set(KI, null); throw new Error("Keine Antwort nach 40 Minuten. Auf GitHub unter Actions → Generieren nachsehen."); }
    sag(`KI rechnet … ${min < 1 ? "gerade gestartet" : `seit ${Math.round(min)} Min.`}`, Math.min(18 + min * 12, 90));
    if (i) await pause(10000);
    try { const r = await gh(`/contents/status/${o.id}.json`, {roh: true}); if (r.ok) st = await r.json(); } catch (e) {}
  }
  ls.set(KI, null);
  if (!st.ok) throw new Error(st.fehler || "Unbekannter Fehler");
  sag("Fertig – Modell wird geladen …", 94);
  const r = await gh("/contents/" + st.stl.split("/").map(encodeURIComponent).join("/"), {roh: true});
  if (!r.ok) throw new Error("Modell liegt im Lager (" + st.ordner + "), konnte aber nicht geladen werden (" + r.status + ").");
  const buf = await r.arrayBuffer();
  let bild = "";
  try { const v = await gh(`/contents/${st.ordner}/vorschau.png`, {roh: true});
    if (v.ok) bild = await new Promise(ok => { const f = new FileReader(); f.onload = () => ok(f.result); f.onerror = () => ok(""); v.blob().then(b => f.readAsDataURL(b)); }); } catch (e) {}
  const W = await import("./werkstatt.js");
  return W.kiUebernehmen({name: st.name || o.name, stl: buf, bild, info: {...(st.info || {}), ordner: st.ordner}});
}

// beim App-Start: läuft noch eine Erzeugung von vorhin?
export function offenePruefen(ctx){
  C = ctx; const o = ls.json(KI, null);
  if (!o || !ls.get(TOK)) return;
  if (Date.now() - o.start > 2 * 3600e3) return ls.set(KI, null);
  C.toast(`„${o.name}“ wird noch erzeugt …`);
  verfolgen(o, null, null);
}
export const laeuft = () => { const o = ls.json(KI, null); return o && Date.now() - o.start < 2 * 3600e3 ? o : null; };
