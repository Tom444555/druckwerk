// mehr.js – Reiter „Wissen“: alles zum Nachschlagen an einem Ort (Material, Modelle, Hilfe) und Gerät & Daten.
const $ = (s, r = document) => r.querySelector(s);
const ls = (k, d) => { try { const v = JSON.parse(localStorage.getItem(k)); return v ?? d; } catch (e) { return d; } };
const standalone = () => { try { return matchMedia("(display-mode: standalone)").matches || navigator.standalone === true; } catch (e) { return false; } };
const tokenDa = () => { try { return !!localStorage.getItem("druckwerk_token"); } catch (e) { return false; } };

export async function seite(app, C){
  const K = await import("./wissen.js");
  const zeile = (ziel, t, sub) => `<div class="row chev" data-ziel="${ziel}" style="cursor:pointer" role="button" tabindex="0"><div class="grow">${t}<div class="small">${sub}</div></div></div>`;
  app.innerHTML = `<h1>Wissen</h1>
  <div class="card"><div class="row"><input type="text" id="mSuch" placeholder="Suchen: Material, Fehler, Zubehör …" aria-label="Wissen durchsuchen" style="flex:1"></div></div>
  <div id="mTreffer"></div><div id="mHaupt">
  <h2>Material</h2><div class="card">
    ${zeile("m:filamente", "Filamente", "Welches Material wofür – mit Temperaturen und Tipps")}
    ${zeile("m:vergleich", "Vergleich", "Rangliste nach Festigkeit, Hitze, Einfachheit")}
    ${zeile("m:lager", "Meine Spulen", "Was du da hast, was in welchem Kopf sitzt")}
    ${zeile("m:zubehoer", "Zubehör", "Düsen, Platten, Trockner – was sich lohnt")}</div>
  <h2>Modelle</h2><div class="card">
    ${zeile("workflow", "Von der Idee zum Modell", "Alle Wege, Werkzeuge und Ausbau-Vorschläge")}
    ${zeile("bibliothek", "Bibliothek &amp; Werkstatt", "Modelle ansehen, drehen, skalieren, selbst slicen")}
    ${zeile("kiweg:1", "Modell per KI", "Bild-Idee → Bild → 3D-Modell → Druck")}
    <a class="row chev" href="https://www.printables.com/" target="_blank" rel="noopener" style="color:inherit;text-decoration:none"><div class="grow">Printables.com<div class="small">STL-Modelle – fertige Vorlagen zum Laden; Datei oder Link dann unter „Neu“ an Claude geben</div></div></a></div>
  <h2>Hilfe</h2><div class="card">
    ${zeile("anleitung", "Anleitung: Mac und Flash Studio", "Teile in Flash Studio öffnen, per WLAN drucken, eigene Änderungen zurückholen")}
    ${zeile("w:problem", "Problem lösen", "Fehlerbilder und was dagegen hilft")}
    <a class="row chev" href="videos/index.html" style="color:inherit;text-decoration:none"><div class="grow">Videos ausgewertet<div class="small">PLA-Einstellungen · STL mit KI · Foto in 3D · Technische Filamente · Meshy · Fuzzy Skin</div></div></a></div>
  <h2>Gerät &amp; Daten</h2>
  <div class="card">
    <div class="row chev" id="stSich" style="cursor:pointer" role="button" tabindex="0"><div class="grow">Sicherung erstellen<div class="small">Haken, Spulen, Tagebuch mit Fotos, eigene Modelle – als eine Datei${ls("druckwerk_gesichert", "") ? " · zuletzt " + C.deDatum(ls("druckwerk_gesichert", "")) : ""}</div></div></div>
    <label class="row chev" style="cursor:pointer"><div class="grow">Sicherung wiederherstellen<div class="small">Datei wählen (auch vom anderen Gerät)</div></div>
      <input type="file" id="stWieder" accept=".json,application/json" hidden></label>
    <div class="row chev" id="stHome" style="cursor:pointer" role="button" tabindex="0"><div class="grow">Als App auf den Home-Bildschirm<div class="small">${standalone() ? "läuft bereits als App ✓" : "eigenes Symbol, startet ohne Safari"}</div></div></div>
    <div class="row"><div class="grow">GitHub-Zugang<div class="small">nur nötig, wenn du in der Werkstatt selbst slicen willst</div></div><span class="val">${tokenDa() ? "eingerichtet" : "nicht eingerichtet"}</span>
      ${tokenDa() ? `<button class="back" id="stTok" style="color:var(--red)">entfernen</button>` : ""}</div>
  </div>
  <p class="hint">Haken, Spulen und Tagebuch liegen nur in diesem Gerät. Eine Sicherung ab und zu schützt vor Verlust (z. B. wenn Safari Website-Daten löscht).</p>
  <div style="height:20px"></div></div>`;
  const geh = ziel => { const [art, x] = ziel.split(":");
    if (art === "m") { K.U.mat = x; K.U.zub = "alle"; return C.go("material"); }
    if (art === "anleitung") return import("./zurueck.js").then(Z => Z.anleitung(C));
    if (art === "w") return K.oeffnen(x, C, "");
    C.go(ziel); };
  app.querySelectorAll("[data-ziel]").forEach(b => b.onclick = b.onkeydown = e => { if (e.type === "keydown" && e.key !== "Enter") return; geh(b.dataset.ziel); });
  $("#stSich").onclick = async () => (await import("./sicherung.js")).sichern(C);
  $("#stWieder").onchange = async e => { const f = e.target.files && e.target.files[0]; e.target.value = ""; if (f) (await import("./sicherung.js")).wiederherstellen(f, C); };
  $("#stHome").onclick = () => { const d = C.sheet(`<h3>Als App installieren</h3><p>${standalone() ? "Druckwerk läuft schon als App." : "Einmal einrichten – danach startet Druckwerk wie eine App."}</p>
    <div class="card"><ol class="steps"><li>In <b>Safari</b> öffnen: tom444555.github.io/druckwerk</li><li>Unten (iPad: oben) das <b>Teilen-Symbol</b> antippen</li>
      <li><b>„Zum Home-Bildschirm“</b> wählen → „Hinzufügen“</li></ol></div>
    <p class="hint">Achtung: Die App auf dem Home-Bildschirm hat ihren eigenen Speicher. Haken, Spulen und Tagebuch aus Safari vorher mit „Sicherung erstellen“ sichern und in der App wiederherstellen.</p>
    <div style="height:12px"></div><button class="btn grey" id="hZu">Fertig</button>`); d.querySelector("#hZu").onclick = () => d.remove(); };
  const tk = $("#stTok"); if (tk) tk.onclick = () => { try { localStorage.removeItem("druckwerk_token"); } catch (e) {} C.toast("Zugang entfernt"); seite(app, C); };
  const such = $("#mSuch"), tr = $("#mTreffer"), haupt = $("#mHaupt");
  such.oninput = async () => { const q = such.value.trim();
    if (q.length < 2) { tr.innerHTML = ""; haupt.style.display = ""; return; }
    let R = []; try { R = await K.suche(q); } catch (e) {}
    if (such.value.trim() !== q) return;
    haupt.style.display = "none";
    tr.innerHTML = `<h2>${R.length} Treffer</h2>` + (R.length ? `<div class="card">${R.slice(0, 40).map((x, i) => `
      <div class="row chev" data-tr="${i}" style="cursor:pointer" role="button" tabindex="0"><div class="grow"><div><b>${C.esc(x.t)}</b> <span class="pill">${C.esc(x.art)}</span></div>
        <div class="small" style="overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${C.esc(x.sub || "")}</div></div></div>`).join("")}</div>` : `<div class="empty">Nichts gefunden.</div>`) + `<div style="height:20px"></div>`;
    tr.querySelectorAll("[data-tr]").forEach(r => r.onclick = r.onkeydown = e => { if (e.type === "keydown" && e.key !== "Enter") return; K.oeffnen(R[+r.dataset.tr].ziel, C, q); }); };
}
