/* Meine Köpfe (seit 23.11.2026): EINE Wahrheit, was in welchem Kopf sitzt – die Spulen mit Kopf-Zuordnung aus
   Material → Mein Lager (localStorage druckwerk_spulen). Daraus:
   - Ampel im Teil und im Projekt: passt der Auftrag zu meinen Köpfen?
   - „An meine Köpfe anpassen“: Kopf, Material und Farbe je Druckfarbe wählen, die App lässt den Auftrag neu slicen
     (eingang/<id>/auftrag.json {art:"anpassen"} → werkzeug/eingang.py → druck.py --wie: alle übrigen Einstellungen bleiben). */
const SP = "druckwerk_spulen";
const ls = (k, d) => { try { const v = JSON.parse(localStorage.getItem(k)); return v ?? d; } catch (e) { return d; } };
const nf = f => String(f || "").toLowerCase().trim().replace(/ß/g, "ss").replace(/ä/g, "ae").replace(/ö/g, "oe").replace(/ü/g, "ue").replace(/\s+/g, "");
const nm = m => String(m || "").toUpperCase().trim();
const gramme = a => String(a.gramm).split(",").map(x => parseFloat(x) || 0);

export function meine(){
  const K = {};
  for (const s of ls(SP, [])) if (s.kopf >= 1 && s.kopf <= 4) K[s.kopf] = {material: nm(s.material), farbe: s.farbe || "", id: s.id};
  return K;
}
// Köpfe, die das Teil wirklich benutzt (Gramm > 0)
export const benutzt = a => { const g = gramme(a); return (a.slots || []).filter((s, i) => g[i] > 0 || (a.slots.length === 1)); };
export const anpassbar = a => a.drucker === "c5pro" && !a.bemalt && !a.duesen_mm && !!a.projekt && (a.teile || []).length > 0;

// je benutztem Kopf: ok | material | farbe | leer | unbekannt (noch keine Köpfe eingetragen)
export function vergleich(a, K = meine()){
  const keine = !Object.keys(K).length;
  return benutzt(a).map(s => { const m = K[s.slot];
    const status = keine ? "unbekannt" : !m ? "leer" : nm(m.material) !== nm(s.material) ? "material" : nf(m.farbe) !== nf(s.farbe) ? "farbe" : "ok";
    return {slot: s.slot, soll: s, ist: m || null, status}; });
}
// Vorschlag: jede Druckfarbe auf den Kopf legen, in dem diese Farbe bei mir sitzt (gleicher Kopf bevorzugt), mit meinem Material
export function vorschlag(sollListe, K = meine(), mats = []){
  const frei = new Set([1, 2, 3, 4]), plan = [];
  const gueltig = m => !mats.length || mats.includes(m);
  const nimm = (s, k, quelle) => { frei.delete(k); const m = K[k];
    plan.push({von: s.slot, soll: s, kopf: k, material: m && gueltig(m.material) ? m.material : nm(s.material), farbe: s.farbe, quelle}); };
  const offen = [];
  for (const s of sollListe) { const m = K[s.slot]; if (m && nf(m.farbe) === nf(s.farbe) && frei.has(s.slot)) nimm(s, s.slot, "gleich"); else offen.push(s); }
  const offen2 = [];
  for (const s of offen) { const k = [1, 2, 3, 4].find(k => frei.has(k) && K[k] && nf(K[k].farbe) === nf(s.farbe)); if (k) nimm(s, k, "farbe"); else offen2.push(s); }
  for (const s of offen2) { const k = frei.has(s.slot) ? s.slot : [...frei][0]; frei.delete(k);
    plan.push({von: s.slot, soll: s, kopf: k, material: nm(s.material), farbe: s.farbe, quelle: "bleibt"}); }
  return plan.sort((x, y) => x.von - y.von);
}
const geaendert = p => p.some(x => x.kopf !== x.von || nm(x.material) !== nm(x.soll.material) || nf(x.farbe) !== nf(x.soll.farbe));

// Hinweise bei gemischtem Material
export function mischHinweise(mats){
  const M = [...new Set(mats.map(nm))], hat = v => M.some(m => m.startsWith(v)), H = [];
  if (M.length < 2) return H;
  if (hat("PLA") && hat("PETG")) H.push("PLA und PETG haften kaum aneinander. Eingelegte Zahlen oder Linien können sich lösen, wenn das Modell sie nicht verankert (beim Drehteller sind sie verankert). Das Bett wird für beide auf 65 °C gestellt, Tür offen lassen.");
  if (hat("TPU")) H.push("TPU zusammen mit hartem Material: langsam, zieht Fäden – hält nur bei großer Kontaktfläche.");
  if ((hat("ABS") || hat("ASA")) && (hat("PLA") || hat("PETG"))) H.push("ABS/ASA brauchen die heiße, geschlossene Kammer – PLA und PETG vertragen sie nicht. Besser nicht mischen.");
  if (!H.length) H.push("Unterschiedliche Materialien in einem Druck – Haftung zwischen den Materialien prüfen.");
  return H;
}

const TXT = {ok: "passt", material: "anderes Material", farbe: "andere Farbe", leer: "Kopf leer", unbekannt: "–"};
const FARB = {ok: "var(--green)", material: "var(--orange)", farbe: "var(--orange)", leer: "var(--red)", unbekannt: "var(--sub)"};

/* ---------- Ampel im Teil ---------- */
export function ampel(el, a, C){
  if (!el || a.drucker !== "c5pro") return;
  const K = meine(), V = vergleich(a, K), keine = !Object.keys(K).length, alleOk = V.every(v => v.status === "ok");
  const kann = anpassbar(a);
  el.innerHTML = `<h2>Meine Köpfe</h2>` + (keine
    ? `<div class="card"><div class="row"><div class="grow">Noch nicht eingetragen, was in deinen Köpfen sitzt.<div class="small">Einmal eintragen – dann prüft Druckwerk jedes Teil und passt es auf Wunsch an.</div></div></div></div>
       <button class="btn grey" id="kEin">Meine Köpfe eintragen</button>`
    : `<div class="card">${V.map(v => `<div class="row"><span class="dot" style="background:${C.farbe(v.ist ? v.ist.farbe : "")};width:22px;height:22px;${v.ist ? "" : "border:1.5px dashed var(--sub);background:transparent"}"></span>
        <div class="grow"><div>Kopf ${v.slot}: ${v.ist ? `<b>${C.esc(v.ist.material)}</b> ${C.esc(v.ist.farbe)}` : "leer"}</div>
          ${v.status === "ok" ? "" : `<div class="small">das Teil erwartet ${C.esc(v.soll.material)} ${C.esc(v.soll.farbe)}</div>`}</div>
        <span class="val" style="color:${FARB[v.status]}">${TXT[v.status]}</span></div>`).join("")}</div>
       ${alleOk ? `<p class="hint" style="color:var(--green)">Passt zu deinen Köpfen – so drucken.</p>` : ""}`)
    + (kann ? `<button class="btn ${alleOk || keine ? "grey" : ""}" id="kAnp">${alleOk || keine ? "Köpfe für diesen Druck selbst wählen" : "An meine Köpfe anpassen"}</button>
       ${alleOk || keine ? "" : `<p class="hint">Rechnet dieses Teil mit deinem Material und deinen Köpfen neu (1–3 Minuten). Alle anderen Einstellungen bleiben.</p>`}`
      : `<p class="hint">Dieses Teil lässt sich nur im Chat mit Claude umstellen${a.bemalt ? " (bemaltes Modell)" : a.duesen_mm ? " (gemischte Düsen)" : ""}.</p>`)
    + (a.angepasst ? `<p class="hint">Zuletzt angepasst am ${C.esc(String(a.angepasst.datum).split("-").reverse().join("."))}.</p>` : "");
  const e = el.querySelector("#kEin"); if (e) e.onclick = () => lagerOeffnen(C);
  const b = el.querySelector("#kAnp"); if (b) b.onclick = () => blatt(C, [a], a.titel || C.schoen(a.name), "auftrag:" + a.ordner);
}
async function lagerOeffnen(C){ try { (await import("./wissen.js")).oeffnen("lager", C); } catch (e) { C.go("material"); } }

/* ---------- Ampel im Projekt ---------- */
export function projektAmpel(el, p, C){
  if (!el) return;
  const teile = p.teile.filter(t => t.drucker === "c5pro"); if (!teile.length) return;
  const K = meine(), keine = !Object.keys(K).length;
  const nicht = teile.filter(t => vergleich(t, K).some(v => v.status !== "ok"));
  const kann = teile.filter(anpassbar);
  el.innerHTML = keine
    ? `<p class="hint">Tipp: Trag unter Wissen → Material → Mein Lager ein, was in deinen Köpfen sitzt – dann zeigt Druckwerk hier, ob alles passt.</p>
       <button class="btn grey" id="pkEin">Meine Köpfe eintragen</button>`
    : !nicht.length ? `<p class="hint" style="color:var(--green)">Alle Teile passen zu deinen Köpfen.</p>`
    : `<div class="warn">${teile.length === 1 ? "Das Teil passt nicht" : nicht.length === teile.length ? "Kein Teil passt" : `${nicht.length} von ${teile.length} Teilen passen nicht`} zu deinen Köpfen (${[...new Set(nicht.flatMap(t => vergleich(t, K).filter(v => v.status !== "ok").map(v => `Kopf ${v.slot}: ${TXT[v.status]}`)))].join(", ")}).</div>
       ${kann.length ? `<button class="btn" id="pkAnp">Projekt an meine Köpfe anpassen</button>
       <p class="hint">Rechnet die betroffenen Teile mit deinem Material neu. Alle anderen Einstellungen bleiben.</p>` : ""}`;
  const e = el.querySelector("#pkEin"); if (e) e.onclick = () => lagerOeffnen(C);
  const b = el.querySelector("#pkAnp"); if (b) b.onclick = () => blatt(C, kann, p.titel, "projekt:" + p.id);
}

/* ---------- Blatt: Köpfe für diesen Druck wählen und neu slicen lassen ---------- */
function blatt(C, teile, titel, ziel){
  const K = meine(), mats = Object.keys(((C.DRUCKER || {}).c5pro || {}).filamente || {PLA: 1, PETG: 1});
  // jede Kombination Kopf|Material|Farbe über alle Teile einmal
  const komb = new Map();
  for (const t of teile) for (const s of benutzt(t)) { const k = `${s.slot}|${nm(s.material)}|${nf(s.farbe)}`; if (!komb.has(k)) komb.set(k, {...s, n: 0}); komb.get(k).n++; }
  const soll = [...komb.values()].sort((x, y) => x.slot - y.slot);
  // Vorschlag je Kopf-Nummer eindeutig halten: Kombinationen mit gleichem Kopf (uneinheitliches Projekt) bekommen denselben Zielkopf
  const proKopf = [...new Map(soll.map(s => [s.slot, s])).values()];
  const basis = vorschlag(proKopf, K, mats), P = soll.map(s => { const b = basis.find(x => x.von === s.slot);
    const gleicheFarbe = nf(b.soll.farbe) === nf(s.farbe);
    return {von: s.slot, soll: s, kopf: b.kopf, material: gleicheFarbe ? b.material : (K[b.kopf] && mats.includes(K[b.kopf].material) ? K[b.kopf].material : nm(s.material)), farbe: s.farbe}; });
  const d = C.sheet(`<h3>Köpfe für „${C.esc(titel)}“</h3><div id="kbInhalt"></div>`), box = d.querySelector("#kbInhalt");
  const mal = () => {
    const doppelt = (() => { const m = new Map(); for (const x of P) { const k = x.kopf; if (!m.has(k)) m.set(k, new Set()); m.get(k).add(x.von); } return [...m.values()].some(s => s.size > 1); })();
    const betroffen = teile.filter(t => teilPlan(t).aendert);
    const H = mischHinweise(P.map(x => x.material)), alt = teile.filter(t => t.geaendert);
    box.innerHTML = `<p>Je Farbe des Drucks: in welchem Kopf sie sitzt und welches Material. Vorbelegt aus „Mein Lager“.</p>
      <div class="card">${P.map((x, i) => `<div class="row" style="flex-wrap:wrap;row-gap:6px"><span class="dot" style="background:${C.farbe(x.soll.farbe)};width:22px;height:22px"></span>
        <div class="grow" style="min-width:120px"><b>${C.esc(x.soll.farbe || "Farbe")}</b><div class="small">bisher Kopf ${x.von} · ${C.esc(x.soll.material)}${teile.length > 1 ? ` · ${x.soll.n} ${x.soll.n === 1 ? "Teil" : "Teile"}` : ""}</div></div>
        <select data-kk="${i}" aria-label="Kopf">${[1, 2, 3, 4].map(k => `<option value="${k}" ${k === x.kopf ? "selected" : ""}>Kopf ${k}${K[k] ? " · " + C.esc(K[k].farbe || K[k].material) : ""}</option>`).join("")}</select>
        <select data-km="${i}" aria-label="Material">${[...new Set([...mats, x.material])].map(m => `<option ${m === x.material ? "selected" : ""}>${C.esc(m)}</option>`).join("")}</select>
        ${K[x.kopf] && nf(K[x.kopf].farbe) !== nf(x.soll.farbe) ? `<div class="small" style="flex-basis:100%;color:var(--orange)">In Kopf ${x.kopf} sitzt bei dir ${C.esc(K[x.kopf].farbe || K[x.kopf].material)} – Spule wechseln, sonst druckt es in dieser Farbe.</div>` : !K[x.kopf] && Object.keys(K).length ? `<div class="small" style="flex-basis:100%;color:var(--orange)">Kopf ${x.kopf} ist bei dir leer – ${C.esc(x.soll.farbe)} einlegen.</div>` : ""}</div>`).join("")}</div>
      ${doppelt ? `<div class="warn">Zwei Farben liegen auf demselben Kopf – jede Farbe braucht ihren eigenen.</div>` : ""}
      ${H.map(h => `<div class="warn">⚠ ${C.esc(h)}</div>`).join("")}
      ${alt.length ? `<div class="warn">${alt.length === 1 ? "Ein Teil hast" : alt.length + " Teile hast"} du selbst in Flash Studio geändert – die neue Fassung ersetzt deine.</div>` : ""}
      <p class="hint">${betroffen.length ? (teile.length > 1 ? `${betroffen.length} von ${teile.length} Teilen werden neu gerechnet.` : "Das Teil wird neu gerechnet, das Modell bleibt gleich.") + " Danach sind Druckdatei, Zeiten und Gramm neu." : "So ist nichts zu ändern – das passt schon."}</p>
      <button class="btn" id="kbLos" ${doppelt || !betroffen.length ? "disabled style=\"opacity:.45\"" : ""}>Neu slicen (${betroffen.length > 1 ? "einige Minuten" : "1–3 Min."})</button>
      <button class="btn grey" id="kbZu">Abbrechen</button>`;
    box.querySelectorAll("[data-kk]").forEach(s => s.onchange = () => { const x = P[+s.dataset.kk]; x.kopf = +s.value;
      P.forEach(y => { if (y !== x && y.von === x.von) y.kopf = x.kopf; });
      const m = K[x.kopf]; if (m && mats.includes(m.material)) x.material = m.material; mal(); });
    box.querySelectorAll("[data-km]").forEach(s => s.onchange = () => { P[+s.dataset.km].material = s.value; mal(); });
    box.querySelector("#kbZu").onclick = () => d.remove();
    box.querySelector("#kbLos").onclick = async () => { if (doppelt || !betroffen.length) return;
      const liste = betroffen.map(t => ({ordner: t.ordner, koepfe: teilPlan(t).koepfe}));
      d.remove();
      const W = await import("./werkstatt.js");
      W.auftragSenden(C, liste.length === 1 ? {art: "anpassen", ...liste[0]} : {art: "anpassen", liste}, {
        titel: liste.length === 1 ? "Teil wird angepasst" : `${liste.length} Teile werden angepasst`, name: titel, ziel,
        pruef: (l, id) => liste.every(e => { const a = l.find(x => x.ordner === e.ordner); return a && a.angepasst && a.angepasst.id === id; })});
    };
  };
  const teilPlan = t => { const koepfe = benutzt(t).map(s => { const x = P.find(p => p.von === s.slot && nm(p.soll.material) === nm(s.material) && nf(p.soll.farbe) === nf(s.farbe)) || P.find(p => p.von === s.slot);
      return {von: s.slot, kopf: x.kopf, material: x.material, farbe: x.farbe || s.farbe, _alt: s}; });
    const aendert = koepfe.some(k => k.kopf !== k.von || nm(k.material) !== nm(k._alt.material) || nf(k.farbe) !== nf(k._alt.farbe));
    return {aendert, koepfe: koepfe.map(({_alt, ...k}) => k)}; };
  mal();
}

// für Tests
export const _test = {vorschlag, vergleich, mischHinweise, geaendert, nf};
