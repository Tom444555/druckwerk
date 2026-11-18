/* Private Modelle aus Tom444555/druckwerk-modelle (seit 18.11.2026).
   Liest das private Lager über die GitHub-API mit dem Schlüssel auf diesem Gerät (localStorage druckwerk_token).
   Ohne Schlüssel oder ohne Zugriff erscheint nur ein Hinweis. Nichts davon landet im öffentlichen Lager. */
const REPO = "Tom444555/druckwerk-modelle", TOK = "druckwerk_token";
const API = p => `https://api.github.com/repos/${REPO}/contents/${p.split("/").map(encodeURIComponent).join("/")}`;
const token = () => { try { return localStorage.getItem(TOK) || ""; } catch (e) { return ""; } };
const roh = async (pfad, art = "json") => {
  const r = await fetch(API(pfad), {headers: {Authorization: `Bearer ${token()}`, Accept: "application/vnd.github.raw+json"}, cache: "no-store"});
  if (!r.ok) throw Object.assign(new Error("HTTP " + r.status), {status: r.status});
  return art === "json" ? r.json() : r.blob();
};
const bilder = new Map();
const claudeLink = t => "https://claude.ai/code/new?repo=Tom444555%2Fdruckwerk&q=" + encodeURIComponent(t);

export async function zeigen(ziel, C){
  if (!ziel) return;
  const kopf = `<h2>Private Modelle</h2>`;
  if (!token()) {
    ziel.innerHTML = kopf + `<div class="card small">Deine privaten Modelle (Gitarren-Bausätze, Albatros …) erscheinen hier, sobald dein GitHub-Zugang
      auf diesem Gerät hinterlegt ist – derselbe wie beim Slicen aus der App. Der Schlüssel braucht Zugriff auf <b>druckwerk-modelle</b>.</div>`;
    return;
  }
  ziel.innerHTML = kopf + `<div class="card small">Wird geladen …</div>`;
  let idx;
  try { idx = await roh("index.json"); }
  catch (e) {
    ziel.innerHTML = kopf + `<div class="card small">${e.status === 404 || e.status === 403 || e.status === 401
      ? "Dein GitHub-Schlüssel hat noch keinen Zugriff auf <b>druckwerk-modelle</b>. Auf github.com unter Settings → Developer settings → Fine-grained tokens beim Schlüssel das Lager dazunehmen."
      : "Konnte nicht geladen werden (offline?)."}</div>`;
    return;
  }
  const P = idx.projekte || [];
  ziel.innerHTML = kopf + `<div class="mgrid">${P.map((p, i) => `
    <div class="mk" data-i="${i}" data-n="${C.esc((p.titel || p.ordner).toLowerCase())}" role="button" tabindex="0">
      <div class="mb"><img data-bild="${C.esc(p.vorschau ? p.ordner + "/" + p.vorschau : "")}" alt="" hidden></div>
      <div class="mt"><b>${C.esc(p.titel || p.ordner)}</b><div class="small">${p.teile.length} Datei${p.teile.length > 1 ? "en" : ""} · privat</div></div></div>`).join("")}</div>
    <div id="pvDetail"></div>`;
  // Vorschaubilder nacheinander holen
  (async () => { for (const img of ziel.querySelectorAll("img[data-bild]")) { const p = img.dataset.bild; if (!p) continue;
    try { if (!bilder.has(p)) bilder.set(p, URL.createObjectURL(await roh(p, "blob"))); img.src = bilder.get(p); img.hidden = false; } catch (e) {} } })();
  ziel.querySelectorAll(".mk").forEach(k => k.onclick = k.onkeydown = e => {
    if (e.type === "keydown" && e.key !== "Enter") return; detail(ziel.querySelector("#pvDetail"), P[+k.dataset.i], C); });
}

function detail(box, p, C){
  const masse = t => t.masse_mm ? t.masse_mm.map(x => Math.round(x)).join(" × ") + " mm" : "";
  const offenbar = t => /\.(stl|3mf|obj)$/i.test(t.datei);
  box.innerHTML = `<div class="card" style="margin-top:10px"><h3 style="margin:0 0 4px">${C.esc(p.titel || p.ordner)}</h3>
    <div class="small">${C.esc(p.art || "")}</div>
    ${p.notiz ? `<p class="small">${C.esc(p.notiz)}</p>` : ""}
    ${p.teile.map((t, i) => `<div class="row" style="align-items:flex-start;gap:8px;padding:8px 0;border-top:.5px solid var(--sep)">
      <div class="grow"><b>${C.esc(t.datei)}</b><div class="small">${masse(t)}${t.passt === false ? " · größer als der Drucker – Claude teilt es" : t.passt ? " · passt in den Drucker" : ""} · ${t.mb} MB</div></div>
      ${offenbar(t) && t.mb <= 30 ? `<button class="btn grey" data-w="${i}" style="width:auto;padding:6px 12px;margin:0">Werkstatt</button>` : ""}</div>`).join("")}
    <a class="btn" style="margin-top:10px;display:block;text-align:center" target="_blank" rel="noopener"
      href="${claudeLink(`druckwerk: Privates Modell „${p.titel || p.ordner}“ (Ordner ${p.ordner} im privaten Lager Tom444555/druckwerk-modelle) für den Creator 5 Pro drucken. Wünsche: `)}">Mit Claude drucken</a>
    <p class="hint">Herkunft: ${C.esc(p.herkunft || "unbekannt")}. Bleibt privat – nur auf deinen Geräten mit deinem Schlüssel sichtbar.</p></div>`;
  box.querySelectorAll("[data-w]").forEach(b => b.onclick = async () => {
    const t = p.teile[+b.dataset.w]; b.disabled = true; b.textContent = "lädt …";
    try {
      const blob = await roh(p.ordner + "/" + t.datei, "blob");
      const f = new File([blob], t.datei);
      const { dateienImportieren } = await import("./werkstatt.js");
      const id = await dateienImportieren([f], C); C.go("werkstatt:e:" + id);
    } catch (e) { C.toast("Konnte nicht geladen werden"); b.disabled = false; b.textContent = "Werkstatt"; }
  });
  box.scrollIntoView({behavior: "smooth", block: "start"});
}
