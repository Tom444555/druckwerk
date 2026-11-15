// start.js – Startansicht: nächster Schritt, Suche über alles, Schnellzugriffe, Gerät & Daten
// Liest nur, was schon im Gerät liegt (localStorage) und wissen/*.json über wissen.js.
const $ = (s, r = document) => r.querySelector(s);
const ls = (k, d) => { try { const v = JSON.parse(localStorage.getItem(k)); return v ?? d; } catch (e) { return d; } };
const zahl = v => { const n = parseFloat(String(v ?? "").replace(",", ".")); return isFinite(n) ? n : 0; };
let C = null;

export async function start(app, ctx){
  C = ctx;
  try { if (navigator.storage && navigator.storage.persist) navigator.storage.persist(); } catch (e) {}   // Safari soll Gerätedaten nicht wegräumen
  const K = await import("./wissen.js");
  let O = {einErledigt: 0, einGesamt: 0, einNaechster: "", faellig: [], leer: [], spulen: 0, wartungNie: true};
  try { O = await K.offen(); } catch (e) {}
  const A = C.AUFTRAEGE, G = C.gedruckt(), TB = ls("druckwerk_tagebuch", []);
  const offenA = A.filter(a => !G[a.ordner]);
  const ohneErgebnis = A.filter(a => G[a.ordner] && !TB.some(t => t.ordner === a.ordner));
  const neuVonClaude = C.LAGER.filter(x => !A.some(a => a.ordner === x.ordner));
  const punkte = a => `<span class="dots" style="display:inline-flex;vertical-align:-2px">${a.slots.map(s => `<span class="dot" style="background:${C.farbe(s.farbe)}"></span>`).join("")}</span>`;

  // Schritte in Reihenfolge der Wichtigkeit: [Titel, Text, Ziel, Knopftext]
  const S = [];
  const einOffen = O.einGesamt && O.einErledigt < O.einGesamt;
  const einSchritt = ["Drucker einrichten", `${O.einErledigt} von ${O.einGesamt} erledigt · als Nächstes: ${O.einNaechster}`, "w:einrichten", O.einErledigt ? "Einrichtung fortsetzen" : "Einrichtung beginnen"];
  if (einOffen && !Object.keys(G).length) S.push(einSchritt);
  ohneErgebnis.slice(0, 3).forEach(a => S.push([`Ergebnis melden: ${C.schoen(a.name)}`, `Gedruckt am ${C.deDatum(G[a.ordner])} – Sterne, Mängel, Foto. So lernt die App deinen Drucker.`, "auftrag:" + a.ordner, "Ergebnis eintragen"]));
  offenA.slice(0, 3).forEach(a => S.push([`Drucken: ${C.schoen(a.name)}`, `${C.zeitKurz(a.zeit)} · ${a.slots.length} ${a.slots.length === 1 ? "Kopf" : "Köpfe"} ${punkte(a)}`, "auftrag:" + a.ordner, "Druckdatei holen"]));
  if (offenA.length > 3) S.push([offenA.length === 4 ? "1 weiterer Auftrag noch nicht gedruckt" : `${offenA.length - 3} weitere Aufträge noch nicht gedruckt`, "Liste „Noch drucken“ öffnen", "liste:offen", "Liste öffnen"]);
  if (einOffen && Object.keys(G).length) S.push(einSchritt);
  O.faellig.forEach(w => S.push([`Wartung fällig: ${w.t}`, w.i, "w:wartung", "Zur Wartung"]));
  O.leer.forEach(s => S.push([`Spule fast leer: ${`${s.material} ${s.farbe || ""}`.trim()}`, `noch ${zahl(s.rest).toFixed(0)} g${s.kopf ? ` · sitzt in Kopf ${s.kopf}` : ""} – Nachschub besorgen`, "w:lager", "Zum Lager"]));
  if (neuVonClaude.length) S.push([`${neuVonClaude.length} ${neuVonClaude.length === 1 ? "Auftrag" : "Aufträge"} von Claude noch nicht gespeichert`, neuVonClaude.slice(0, 3).map(a => C.schoen(a.name)).join(", ") + (neuVonClaude.length > 3 ? " …" : ""), "liste:claude", "Ansehen"]);
  if (A.length && !O.spulen) S.push(["Spulen eintragen", "Dann zeigt jeder Auftrag, ob das Filament reicht und was der Druck kostet.", "w:lager", "Spulen eintragen"]);
  if (!A.length && !neuVonClaude.length) S.push(["Ersten Auftrag beginnen", "Unter „Neu“ beschreiben, was du brauchst – Claude schickt die fertige Druckdatei.", "neu", "Neuer Auftrag"]);

  const [erst, ...rest] = S;
  const heute = new Date().toLocaleDateString("de-DE", {weekday: "long", day: "numeric", month: "long"});
  app.innerHTML = `<h1>Druckwerk</h1>
  <div class="card"><div class="row"><input type="text" id="stSuch" placeholder="Suchen: Auftrag, Material, Fehler …" aria-label="Alles durchsuchen" style="flex:1"></div></div>
  <div id="stTreffer"></div>
  <div id="stHaupt">
  <h2>Nächster Schritt · ${C.esc(heute)}</h2>
  ${erst ? `<div class="card"><div class="row oben"><div class="grow"><div><b>${C.esc(erst[0])}</b></div><div class="small" style="margin-top:3px">${erst[1].includes("<span") ? erst[1] : C.esc(erst[1])}</div></div></div>
    <div style="padding:0 16px 14px"><button class="btn" data-ziel="${C.esc(erst[2])}">${C.esc(erst[3])}</button></div></div>`
    : `<div class="card"><div class="row"><span class="haken on" aria-hidden="true">✓</span><div class="grow"><b>Alles erledigt</b><div class="small">Keine offenen Drucke, nichts fällig.</div></div></div></div>`}
  ${rest.length ? `<h2>Danach</h2><div class="card">${rest.map(x => `<div class="row chev" data-ziel="${C.esc(x[2])}" style="cursor:pointer" role="button" tabindex="0">
    <div class="grow"><div><b>${C.esc(x[0])}</b></div><div class="small">${x[1].includes("<span") ? x[1] : C.esc(x[1])}</div></div></div>`).join("")}</div>` : ""}
  <h2>Schnell</h2>
  <div class="kacheln">
    <button class="kachel" data-ziel="neu"><span aria-hidden="true">＋</span>Neuer Auftrag</button>
    <button class="kachel" data-ziel="bibliothek"><span aria-hidden="true">⬆︎</span>Datei öffnen</button>
    <button class="kachel" data-ziel="w:hilfe"><span aria-hidden="true">?</span>Problem lösen</button>
    <button class="kachel" data-ziel="w:lager"><span aria-hidden="true">◎</span>Meine Spulen</button>
  </div>
  <h2>So geht's</h2>
  <div class="card"><ol class="steps">
    <li><b>Neu</b>: beschreiben, was du brauchst → „In Claude öffnen“.</li>
    <li>Claude schickt die <b>.gcode</b> und einen Link – Link antippen speichert den Auftrag hier.</li>
    <li>Im Auftrag „.gcode laden“ → auf den USB-Stick → am Drucker starten.</li>
    <li>Danach „Als gedruckt markieren“ und das <b>Ergebnis eintragen</b>.</li></ol>
    <div class="row chev" data-ziel="workflow" style="cursor:pointer" role="button" tabindex="0"><div class="grow">Alle Wege, Werkzeuge und Ideen</div></div></div>
  <h2>Gerät &amp; Daten</h2>
  <div class="card">
    <div class="row chev" id="stSich" style="cursor:pointer" role="button" tabindex="0"><div class="grow">Sicherung erstellen<div class="small">Aufträge, Spulen, Tagebuch mit Fotos, eigene Modelle – als eine Datei${ls("druckwerk_gesichert", "") ? ` · zuletzt am ${C.deDatum(ls("druckwerk_gesichert", ""))}` : ""}</div></div></div>
    <label class="row chev" style="cursor:pointer"><div class="grow">Sicherung wiederherstellen<div class="small">Datei wählen (auch vom anderen Gerät)</div></div>
      <input type="file" id="stWieder" accept=".json,application/json" hidden></label>
    <div class="row chev" id="stHome" style="cursor:pointer" role="button" tabindex="0"><div class="grow">Als App auf den Home-Bildschirm<div class="small">${standalone() ? "läuft bereits als App ✓" : "eigenes Symbol, startet ohne Safari-Leiste, geht auch offline"}</div></div></div>
    <div class="row"><div class="grow">GitHub-Zugang (Slicen aus der App)</div><span class="val">${tokenDa() ? "eingerichtet" : "nicht eingerichtet"}</span>
      ${tokenDa() ? `<button class="back" id="stTok" style="color:var(--red)">entfernen</button>` : ""}</div>
  </div>
  <p class="hint">Alle eigenen Daten liegen nur in diesem Gerät. Eine Sicherung ab und zu schützt vor Verlust (z. B. wenn Safari Website-Daten löscht).</p>
  <div style="height:20px"></div></div>`;

  const geh = ziel => { const [art, x] = ziel.split(":");
    if (art === "w") return x === "hilfe" ? K.oeffnen("problem", C, "") : K.oeffnen(x, C);
    if (art === "liste") { C.liste(x); return; }
    C.go(ziel); };
  app.querySelectorAll("[data-ziel]").forEach(b => b.onclick = b.onkeydown = e => { if (e.type === "keydown" && e.key !== "Enter") return; geh(b.dataset.ziel); });
  $("#stSich").onclick = async () => (await import("./sicherung.js")).sichern(C);
  $("#stWieder").onchange = async e => { const f = e.target.files && e.target.files[0]; e.target.value = ""; if (f) (await import("./sicherung.js")).wiederherstellen(f, C); };
  $("#stHome").onclick = () => { const d = C.sheet(`<h3>Als App installieren</h3><p>${standalone() ? "Druckwerk läuft schon als App." : "Einmal einrichten – danach startet Druckwerk wie eine App."}</p>
    <div class="card"><ol class="steps"><li>In <b>Safari</b> öffnen: tom444555.github.io/druckwerk</li><li>Unten (iPad: oben) das <b>Teilen-Symbol</b> antippen</li>
      <li><b>„Zum Home-Bildschirm“</b> wählen → „Hinzufügen“</li></ol></div>
    <p class="hint">Achtung: Die App auf dem Home-Bildschirm hat ihren eigenen Speicher. Aufträge, Spulen und Tagebuch aus Safari vorher mit „Sicherung erstellen“ sichern und in der App wiederherstellen.</p>
    <div style="height:12px"></div><button class="btn grey" id="hZu">Fertig</button>`); d.querySelector("#hZu").onclick = () => d.remove(); };
  const tk = $("#stTok"); if (tk) tk.onclick = () => { try { localStorage.removeItem("druckwerk_token"); } catch (e) {} C.toast("Zugang entfernt"); start(app, C); };

  // Suche über alles: eigene Aufträge, Aufträge von Claude, Wissen
  const such = $("#stSuch"), tr = $("#stTreffer"), haupt = $("#stHaupt");
  such.oninput = async () => {
    const q = such.value.trim(), t = q.toLowerCase();
    if (q.length < 2) { tr.innerHTML = ""; haupt.style.display = ""; return; }
    const eigen = A.filter(a => (a.name + " " + a.ordner).toLowerCase().includes(t)).map(a => ({art: "Auftrag", t: C.schoen(a.name), sub: `${C.deDatum(a.datum)} · ${C.zeitKurz(a.zeit)}`, ziel: "auftrag:" + a.ordner}));
    const lager = neuVonClaude.filter(a => (a.name + " " + a.ordner).toLowerCase().includes(t)).map(a => ({art: "Von Claude", t: C.schoen(a.name), sub: "noch nicht gespeichert – antippen speichert", ziel: "hinzu:" + a.ordner}));
    let w = []; try { w = await K.suche(q); } catch (e) {}
    if (such.value.trim() !== q) return;
    const R = [...eigen, ...lager, ...w];
    haupt.style.display = "none";
    tr.innerHTML = `<h2>${R.length} ${R.length === 1 ? "Treffer" : "Treffer"}</h2>` + (R.length ? `<div class="card">${R.slice(0, 40).map((x, i) => `
      <div class="row chev" data-tr="${i}" style="cursor:pointer" role="button" tabindex="0"><div class="grow"><div><b>${C.esc(x.t)}</b> <span class="pill">${C.esc(x.art)}</span></div>
        <div class="small" style="overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${C.esc(x.sub || "")}</div></div></div>`).join("")}</div>`
      : `<div class="empty">Nichts gefunden.</div>`) + `<div style="height:20px"></div>`;
    tr.querySelectorAll("[data-tr]").forEach(r => r.onclick = r.onkeydown = e => { if (e.type === "keydown" && e.key !== "Enter") return;
      const x = R[+r.dataset.tr];
      if (x.ziel.startsWith("hinzu:")) { const a = C.LAGER.find(y => y.ordner === x.ziel.slice(6)); C.hinzufuegen([a]); C.toast("Auftrag gespeichert"); C.go("auftrag:" + a.ordner); }
      else if (x.ziel.startsWith("auftrag:")) C.go(x.ziel);
      else K.oeffnen(x.ziel, C, q); });
  };
}
const standalone = () => { try { return matchMedia("(display-mode: standalone)").matches || navigator.standalone === true; } catch (e) { return false; } };
const tokenDa = () => { try { return !!localStorage.getItem("druckwerk_token"); } catch (e) { return false; } };
