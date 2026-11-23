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

export async function zeigen(ziel, C, danach){
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
    <div class="mk" data-i="${i}" data-b="${C.esc(p.bereich || "sonstiges")}" data-n="${C.esc(((p.titel || p.ordner) + " " + (p.schlagworte || []).join(" ") + " privat").toLowerCase())}" role="button" tabindex="0">
      <div class="mb"><img data-bild="${C.esc(p.vorschau ? p.ordner + "/" + p.vorschau : "")}" alt="" hidden></div>
      <div class="mt"><b>${C.esc(p.titel || p.ordner)}</b><div class="small">🔒 privat · ${(p.auftraege || []).length ? `${p.auftraege.length} Druckdatei${p.auftraege.length > 1 ? "en" : ""}` : `${p.teile.length} Datei${p.teile.length > 1 ? "en" : ""}`}</div></div></div>`).join("")}</div>
    <div id="pvDetail"></div>`;
  if (danach) danach();
  // Vorschaubilder nacheinander holen
  (async () => { for (const img of ziel.querySelectorAll("img[data-bild]")) { const p = img.dataset.bild; if (!p) continue;
    try { if (!bilder.has(p)) bilder.set(p, URL.createObjectURL(await roh(p, "blob"))); img.src = bilder.get(p); img.hidden = false; } catch (e) {} } })();
  ziel.querySelectorAll(".mk").forEach(k => k.onclick = k.onkeydown = e => {
    if (e.type === "keydown" && e.key !== "Enter") return; detail(ziel.querySelector("#pvDetail"), P[+k.dataset.i], C); });
}

function detail(box, p, C){
  const masse = t => t.masse_mm ? t.masse_mm.map(x => Math.round(x)).join(" × ") + " mm" : "";
  const offenbar = t => /\.(stl|3mf|obj)$/i.test(t.datei);
  const ansehbar = (p.auftraege || []).length || p.teile.some(t => offenbar(t) && t.mb <= 30);
  box.innerHTML = `<div class="card" style="margin-top:10px"><h3 style="margin:0 0 4px">${C.esc(p.titel || p.ordner)}</h3>
    <div class="small">${C.esc(p.art || "")}</div>
    ${ansehbar ? `<button class="btn" id="pvAnsehen" style="margin:10px 0 4px">In 3D ansehen</button>` : ""}
    ${p.notiz ? `<p class="small">${C.esc(p.notiz)}</p>` : ""}
    ${p.teile.map((t, i) => `<div class="row" style="align-items:flex-start;gap:8px;padding:8px 0;border-top:.5px solid var(--sep)">
      <div class="grow"><b>${C.esc(t.datei)}</b><div class="small">${masse(t)}${t.passt === false ? " · größer als der Drucker – Claude teilt es" : t.passt ? " · passt in den Drucker" : ""} · ${t.mb} MB</div></div>
      ${offenbar(t) && t.mb <= 30 ? `<button class="btn grey" data-w="${i}" style="width:auto;padding:6px 12px;margin:0">Werkstatt</button>` : ""}</div>`).join("")}
    ${(p.auftraege || []).length ? `<h3 style="margin:14px 0 2px;font-size:15px">Fertige Druckdateien</h3>${p.auftraege.map((a, i) => `<div class="row" style="align-items:flex-start;gap:8px;padding:8px 0;border-top:.5px solid var(--sep)">
      <div class="grow"><b>${C.esc(a.titel || a.gcode)}</b><div class="small">${a.gcode_zip ? "als ZIP – nach dem Laden entpacken · " : ""}${C.esc(a.zeit || "")} · Düse ${C.esc(String(a.duese_mm || "0.4").replace(".", ","))} mm · ${C.esc((a.slots || []).filter(s => s.farbe !== "leer").map(s => `Kopf ${s.slot} ${s.material} ${s.farbe}`).join(", "))}</div></div>
      <button class="btn grey" data-a="${i}" style="width:auto;padding:6px 12px;margin:0">Ansehen</button>
      <button class="btn" data-g="${i}" style="width:auto;padding:6px 12px;margin:0">Laden</button></div>`).join("")}` : ""}
    <a class="btn grey" style="margin-top:10px;display:block;text-align:center" target="_blank" rel="noopener"
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
  // 3D-Ansicht: Teile einer Druckdatei (leichte .app.stl, wenn vorhanden) holen und in der Werkstatt öffnen
  const ansehen = async (b, a) => {
    const alt = b.textContent; b.disabled = true; b.textContent = "lädt …";
    try {
      const W = await import("./werkstatt.js");
      let teile, slots = [], schluessel, name;
      if (a) {
        const pfad = `${p.ordner}/auftraege/${a.ordner}`, info = await roh(pfad + "/auftrag.json");
        const liste = (info.teile_app && info.teile_app.length ? info.teile_app : info.teile) || [];
        if (!liste.length) throw new Error("keine Teile");
        teile = [];
        for (const [k, t] of liste.entries()) { b.textContent = `lädt ${k + 1}/${liste.length} …`;
          teile.push({name: t.datei.replace(/(\.app)?\.stl$/i, ""), slot: Math.min(t.slot || 1, 4), stl: await (await roh(pfad + "/" + t.datei, "blob")).arrayBuffer()}); }
        slots = (info.slots || []).filter(s => s.slot <= 4).sort((x, y) => x.slot - y.slot).map(s => C.farbe(s.farbe));
        schluessel = p.ordner + "_" + a.ordner; name = (p.titel || p.ordner) + (p.auftraege.length > 1 ? " – " + (a.titel || a.ordner) : "");
      } else {
        const st = p.teile.filter(t => /\.stl$/i.test(t.datei) && t.mb <= 30);
        if (!st.length) {   // nur 3MF/OBJ: wie bisher über die Werkstatt-Einfuhr
          const t = p.teile.find(t => offenbar(t) && t.mb <= 30), blob = await roh(p.ordner + "/" + t.datei, "blob");
          const id = await W.dateienImportieren([new File([blob], t.datei)], C); return C.go("werkstatt:e:" + id);
        }
        teile = [];
        for (const [k, t] of st.entries()) { b.textContent = `lädt ${k + 1}/${st.length} …`;
          teile.push({name: t.datei.replace(/\.stl$/i, ""), slot: Math.min(k + 1, 4), stl: await (await roh(p.ordner + "/" + t.datei, "blob")).arrayBuffer()}); }
        schluessel = p.ordner; name = p.titel || p.ordner;
      }
      const id = await W.privatAblegen({schluessel, name, slots, teile}, C);
      C.go("werkstatt:e:" + id);
    } catch (e) { console.error(e); C.toast("Konnte nicht geladen werden"); b.disabled = false; b.textContent = alt; }
  };
  const gross = box.querySelector("#pvAnsehen");
  if (gross) gross.onclick = () => ansehen(gross, (p.auftraege || [])[0]);
  box.querySelectorAll("[data-a]").forEach(b => b.onclick = () => ansehen(b, p.auftraege[+b.dataset.a]));
  box.querySelectorAll("[data-g]").forEach(b => b.onclick = async () => {
    const a = p.auftraege[+b.dataset.g]; b.disabled = true; b.textContent = "lädt …";
    try {
      const datei = a.gcode_zip || a.gcode;                    // sehr große Druckdateien liegen als ZIP im Lager (GitHub-Grenze 100 MB)
      const blob = await roh(`${p.ordner}/auftraege/${a.ordner}/${datei}`, "blob");
      const url = URL.createObjectURL(blob), l = document.createElement("a"); l.href = url; l.download = datei; document.body.appendChild(l); l.click(); l.remove();
      setTimeout(() => URL.revokeObjectURL(url), 60000); C.toast("Geladen – in „Dateien“ unter Downloads", 4000);
    } catch (e) { C.toast("Konnte nicht geladen werden"); }
    b.disabled = false; b.textContent = "Laden";
  });
  box.scrollIntoView({behavior: "smooth", block: "start"});
}
