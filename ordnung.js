/* Lager-Ordnung (seit 23.11.2026): eine Karteikarte je Projekt – Bereich, Stand, Herkunft, Schlagworte, Archiv.
   Quelle: lager/karten.json im Lager. Toms Änderungen bleiben sofort auf dem Gerät (druckwerk_karten) und werden,
   wenn ein GitHub-Zugang hinterlegt ist, in die Datei zurückgeschrieben – so gelten sie auf allen Geräten. */
const LS = "druckwerk_karten", TOK = "druckwerk_token", REPO = "Tom444555/druckwerk", PFAD = "lager/karten.json";
const lsGet = (k, d) => { try { const v = JSON.parse(localStorage.getItem(k)); return v ?? d; } catch (e) { return d; } };
const lsSet = (k, v) => { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) {} };
let K = null;
export const F = {bereich: "alle", archiv: false};      // gewählter Filter (gilt für Projekte und Bibliothek)
const STD = [{id: "musik", name: "Gitarre & Musik"}, {id: "foto", name: "Foto & Scan"}, {id: "werkstatt", name: "Werkstatt & Ordnung"}, {id: "deko", name: "Deko & Geschenke"}, {id: "drucker", name: "Drucker & Kalibrieren"}, {id: "sonstiges", name: "Unsortiert"}];

export async function laden(neu){
  if (K && !neu) return K;
  try { K = await (await fetch(PFAD + "?t=" + Date.now(), {cache: "no-store"})).json(); } catch (e) { K = K || {karten: {}}; }
  K.karten = K.karten || {}; K.bereiche = K.bereiche && K.bereiche.length ? K.bereiche : STD;
  return K;
}
export const schluessel = a => a.gruppe || a.name || a.ordner;
export const bereiche = () => (K && K.bereiche) || STD;
export const bereichName = id => (bereiche().find(b => b.id === id) || {name: "Unsortiert"}).name;
// Karte = Datei im Lager, überlagert von der neueren Änderung auf diesem Gerät
export function karte(key){
  const r = (K && K.karten[key]) || {}, e = lsGet(LS, {})[key];
  const k = e && (e.t || 0) >= (r.t || 0) ? {...r, ...e} : r;
  return {bereich: "sonstiges", stand: "gerechnet", herkunft: "", schlagworte: [], archiv: false, ...k};
}
export const suchtext = key => { const k = karte(key); return (bereichName(k.bereich) + " " + (k.schlagworte || []).join(" ") + " " + (k.notiz || "")).toLowerCase(); };

// Filter-Knöpfe: nur Bereiche, in denen etwas liegt. zaehler = {bereichId: Anzahl}
export function chips(zaehler, gesamt){
  const B = bereiche().filter(b => zaehler[b.id]);
  if (B.length < 2) return "";
  if (F.bereich !== "alle" && !zaehler[F.bereich]) F.bereich = "alle";
  return `<div class="chips" id="ordChips" style="margin:10px 2px 4px">
    <button class="chip ${F.bereich === "alle" ? "on" : ""}" data-b="alle">Alle <span style="opacity:.6">${gesamt}</span></button>
    ${B.map(b => `<button class="chip ${F.bereich === b.id ? "on" : ""}" data-b="${b.id}">${b.name} <span style="opacity:.6">${zaehler[b.id]}</span></button>`).join("")}</div>`;
}
export function chipsBinden(wurzel, neu){ wurzel.querySelectorAll("#ordChips .chip").forEach(c => c.onclick = () => { F.bereich = c.dataset.b; neu(); }); }

/* Blatt „Einordnen“ */
export function einordnen(C, key, titel, fertig){
  const k = karte(key);
  const d = C.sheet(`<h3>„${C.esc(titel)}“ einordnen</h3>
    <div class="card">
      <div class="row"><div class="grow">Bereich</div><select id="oB">${bereiche().map(b => `<option value="${b.id}" ${b.id === k.bereich ? "selected" : ""}>${C.esc(b.name)}</option>`).join("")}</select></div>
      <div class="row"><div class="grow">Stand</div><select id="oS">${[["idee", "Idee"], ["gerechnet", "gerechnet, noch nicht gedruckt"], ["gedruckt", "gedruckt"], ["bewaehrt", "bewährt – so lassen"]].map(([v, t]) => `<option value="${v}" ${v === k.stand ? "selected" : ""}>${t}</option>`).join("")}</select></div>
      <div class="row"><div class="grow">Schlagworte</div><input type="text" id="oW" value="${C.esc((k.schlagworte || []).join(", "))}" placeholder="mit Komma getrennt" style="flex:1.6"></div>
      <label class="row" style="cursor:pointer"><div class="grow">Ins Archiv<div class="small">Alte Fassungen und Tests: ausgeblendet, aber nicht gelöscht.</div></div><input type="checkbox" id="oA" ${k.archiv ? "checked" : ""}></label>
    </div>
    <div style="height:12px"></div><button class="btn" id="oOk">Sichern</button><button class="btn grey" id="oZu">Abbrechen</button>
    <p class="hint">${tok() ? "Wird im Lager gespeichert und gilt auf allen deinen Geräten." : "Gilt auf diesem Gerät. Mit hinterlegtem GitHub-Zugang (Werkstatt → Slicen) auch auf allen anderen."}</p>`);
  const q = s => d.querySelector(s);
  q("#oZu").onclick = () => d.remove();
  q("#oOk").onclick = async () => {
    const neu = {bereich: q("#oB").value, stand: q("#oS").value, archiv: q("#oA").checked, t: Date.now(),
      schlagworte: q("#oW").value.split(",").map(x => x.trim()).filter(Boolean).slice(0, 12)};
    const E = lsGet(LS, {}); E[key] = neu; lsSet(LS, E);
    d.remove(); C.toast("Eingeordnet"); fertig && fertig();
    if (tok()) schreiben(key, neu).catch(e => console.warn("Karte nicht ins Lager geschrieben", e));
  };
}
const tok = () => { try { return localStorage.getItem(TOK) || ""; } catch (e) { return ""; } };
const b64 = s => btoa(unescape(encodeURIComponent(s))), ab64 = s => decodeURIComponent(escape(atob(String(s).replace(/\s/g, ""))));
async function schreiben(key, neu, versuch = 0){
  const kopf = {Authorization: `Bearer ${tok()}`, Accept: "application/vnd.github+json"}, url = `https://api.github.com/repos/${REPO}/contents/${PFAD}`;
  const r = await fetch(url, {headers: kopf, cache: "no-store"}); if (!r.ok) throw new Error("lesen " + r.status);
  const j = await r.json(), D = JSON.parse(ab64(j.content));
  D.karten = D.karten || {}; D.karten[key] = {...(D.karten[key] || {}), ...neu};
  const w = await fetch(url, {method: "PUT", headers: kopf, body: JSON.stringify({message: `App: ${key} eingeordnet`, content: b64(JSON.stringify(D, null, 1)), sha: j.sha})});
  if (w.status === 409 && versuch < 2) return schreiben(key, neu, versuch + 1);
  if (!w.ok) throw new Error("schreiben " + w.status);
  if (K) K.karten[key] = D.karten[key];
}
export const _test = {karte, chips, F};
