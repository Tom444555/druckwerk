// kiweg.js – KI-Ablauf in sechs Schritten: Bild-Idee → Bild erzeugen (extern) → Bild prüfen → In 3D umwandeln → Modell prüfen → Werkstatt/Slicen
// Grundsätze aus dem Video „Eigene STL-Dateien mit KI erstellen“ (Bastlwastl), Auswertung: videos/ki-stl-bastlwastl.html.
// Der Bild-Text ist ein EIGENER Text nach diesen Grundsätzen – der Prompt aus der Videobeschreibung liegt uns nicht vor.
// Alles bleibt im Gerät (localStorage druckwerk_kiweg). Claude selbst erzeugt keine Bilder → Bild-KI extern (ChatGPT o. Ä.).
const KW = "druckwerk_kiweg";   // {idee:{…}, nach:{…}, bild:{id:true}, modell:{id:true}, modellId, fertig:{n:true}, schritt, aktiv}
const lies = () => { try { return JSON.parse(localStorage.getItem(KW)) || {}; } catch (e) { return {}; } };
const schreib = () => { try { localStorage.setItem(KW, JSON.stringify(S)); } catch (e) {} };
const zahl = v => { const n = parseFloat(String(v ?? "").replace(",", ".")); return isFinite(n) ? n : 0; };
const AUSWERTUNG = "videos/ki-stl-bastlwastl.html";
const MAKERLAB = "https://makerworld.com/makerlab/imageto3d";
let C = null, S = {};

export const SCHRITTE = [
  ["Bild-Idee", "Idee"], ["Bild erzeugen", "Bild"], ["Bild prüfen", "Prüfen"],
  ["In 3D umwandeln", "3D"], ["Modell prüfen", "Modell"], ["Werkstatt & Slicen", "Slicen"]];

const STD = {motiv: "", cm: "15", mass: "hoch", aufstellung: "steht", stil: "", details: "", teilung: "ein", teil: "", farbe: "grau", schicht: "0,12"};
const AUFSTELLUNG = {
  "steht": "steht frei auf einer ebenen, flachen Standfläche (Füße oder Sockel mit geradem Boden, sicher und nicht kippelig)",
  "hängt": "wird aufgehängt: eine kompakte, kräftige Öse oben, fest mit dem Körper verbunden",
  "an der Wand": "wird an der Wand montiert: flache, gerade Rückseite ohne Details",
  "liegt": "liegt flach: breite, ebene Unterseite"};
const FARBEN = {"grau": "einfarbig mittelgrau", "hellgrau": "einfarbig hellgrau", "sandfarben": "einfarbig in einem sanften Sandton", "tonfarben": "einfarbig in einem sanften Ton-/Terrakotta-Ton"};

// Prüflisten: [id, Text, Fundstelle im Video oder "" = eigene Ergänzung]
export const PRUEF_BILD = [
  ["eins", "Genau ein Objekt, ganz im Bild, nichts abgeschnitten", "05:07"],
  ["hinter", "Hintergrund neutral und ruhig", "05:07"],
  ["matt", "Einfarbig und matt – kein Glanz, auch nicht in den Augen", "05:39 · 06:10"],
  ["winkel", "Blick leicht schräg von oben – die Tiefe ist erkennbar", "05:39"],
  ["kompakt", "Kompakt und zusammenhängend – nichts schwebt oder fliegt", "06:10"],
  ["hinterschnitt", "Wenig Hinterschneidungen (offener Mund, Zunge, tiefe Lücken)", "09:52"],
  ["stand", "Standfläche bzw. Rückseite passt zur Aufstellung", "06:42"],
  ["glieder", "Zahl der Finger und Glieder stimmt, Klingen und Stäbe sind gerade", "03:02"],
  ["details", "Details sind kräftig genug für die Zielgröße", "07:15 · 19:17"],
  ["teile", "Bei getrennten Teilen: nur ein Teil im Bild", "16:41"]];
export const PRUEF_MODELL = [
  ["grau", "Ohne Farbe (grau) ansehen, rundum drehen und hineinzoomen", "17:43 · 18:15"],
  ["finger", "Finger und Glieder zählen – kein fünfter oder sechster Finger zu viel", "18:46"],
  ["krumm", "Klingen, Stäbe, Schwerter gerade, nicht krumm", "18:46"],
  ["rueck", "Rückseite: nichts erfunden, was nicht auf dem Bild war", "18:46"],
  ["textur", "Details und Texturen bei Zielgröße noch sichtbar", "18:46 · 19:17"],
  ["boden", "Steht eben? Sonst unten plan schneiden lassen", "21:53"],
  ["lose", "Keine losen oder schwebenden Teile, alles verbunden", ""],
  ["duenn", "Keine Stellen dünner als etwa 1,2 mm (Finger, Klingen)", ""]];

/* ---------- Texte für die Bild-KI ---------- */
export function bildText(I){
  I = {...STD, ...(I || {})};
  const cm = zahl(I.cm) || 15, s = I.schicht || "0,12", farbe = FARBEN[I.farbe] || FARBEN.grau;
  const z = ["Erstelle ein Bild als Vorlage für ein KI-3D-Modell, das ich danach mit einem FDM-3D-Drucker drucke.",
    `Motiv: ${String(I.motiv).trim() || "…"}`];
  if (String(I.stil).trim()) z.push(`Stil: ${I.stil.trim()}`);
  if (String(I.details).trim()) z.push(`Oberflächen-Details: ${I.details.trim()} – kräftig genug, dass sie gedruckt sichtbar sind (nichts feiner als etwa 0,5 mm).`);
  z.push(`Zielgröße des gedruckten Objekts: etwa ${String(cm).replace(".", ",")} cm ${I.mass}. Gedruckt wird mit 0,4-mm-Düse und ${s} mm Schichthöhe – plane Form und Details passend zu dieser Größe.`);
  z.push(`Aufstellung: Das Objekt ${AUFSTELLUNG[I.aufstellung] || AUFSTELLUNG.steht}.`);
  if (I.teilung === "getrennt") z.push(`Teilung: Zeige nur dieses eine Teil${String(I.teil).trim() ? `: ${I.teil.trim()}` : ""}. Die anderen Teile erstelle ich später einzeln in eigenen Bildern im gleichen Stil, damit ich sie getrennt drucke und zusammenklebe.`);
  else z.push("Teilung: ein zusammenhängendes Stück, das in einem Teil gedruckt wird.");
  z.push("", "Regeln für das Bild:",
    "- genau ein Objekt, vollständig sichtbar, nichts abgeschnitten",
    "- neutraler, ruhiger, einfarbiger Hintergrund – keine Szene, keine weiteren Gegenstände, kein Text, kein Logo",
    `- das Objekt ${farbe}, matte Oberfläche, nichts Glänzendes, keine Spiegelungen, auch kein Glanz in den Augen`,
    "- weiches, gleichmäßiges Licht mit leichten Schatten, damit Form und Struktur gut zu erkennen sind",
    "- Kamera leicht schräg von oben und etwas seitlich, damit die Tiefe sichtbar ist – nicht genau frontal, nicht genau von der Seite, keine extremen Winkel, kein Weitwinkel",
    "- kompakte, zusammenhängende Form: nichts Schwebendes oder Fliegendes (keine abstehenden Haare, losen Teile, Funken), dünne Teile kräftig und mit dem Körper verbunden",
    "- möglichst wenige Hinterschneidungen und Hohlräume (z. B. Mund geschlossen, keine herausgestreckte Zunge)",
    "- anatomisch stimmig: richtige Zahl an Fingern und Gliedern, gerade Klingen und Stäbe",
    "", "Prüfe vor dem Erzeugen kurz, ob das Motiv so druckbar ist, und vereinfache es, wo nötig.");
  return z.join("\n");
}
export function nachText(I, N){
  I = {...STD, ...(I || {})}; N = N || {};
  const cm = String(zahl(I.cm) || 15).replace(".", ","), z = ["Bitte dieses Bild überarbeiten. Blickwinkel, Hintergrund, Licht sowie die matte, einfarbige Oberfläche bleiben genau gleich."];
  if (N.textur) z.push(`- Mehr Oberflächen-Struktur: ${String(N.texturWas || "").trim() || "deutliche Risse, Dellen und Kratzer"} – kräftig genug für den Druck bei ${cm} cm, nicht feiner als etwa 0,5 mm.`);
  if (N.weg) z.push(`- Entferne: ${String(N.wegWas || "").trim() || "…"}. Die Stelle sauber schließen, nichts Schwebendes zurücklassen.`);
  if (N.trennen) z.push(`- Teile trennen: Zeige nur ${String(N.trennenWas || "").trim() || "…"}. Den Rest erstelle ich in einem eigenen Bild im gleichen Stil, damit ich die Teile getrennt drucke und zusammenklebe.`);
  if (String(N.sonst || "").trim()) z.push("- " + N.sonst.trim());
  if (z.length === 1) z.push("- (oben mindestens eine Änderung wählen)");
  return z.join("\n");
}

/* ---------- Ansicht ---------- */
export async function ansicht(app, ctx, n){
  C = ctx; S = lies();
  S.idee = {...STD, ...(S.idee || {})}; S.nach = S.nach || {}; S.bild = S.bild || {}; S.modell = S.modell || {}; S.fertig = S.fertig || {};
  n = Math.min(6, Math.max(1, parseInt(n, 10) || S.schritt || 1));
  S.schritt = n; S.aktiv = true; schreib();
  const kopf = `<button class="back" id="kwZur">‹ Bibliothek</button><h1>Modell per KI</h1>
    <div class="kwfort" role="list">${SCHRITTE.map(([t, k], i) => `<button role="listitem" data-kw="${i + 1}" class="${i + 1 === n ? "on" : S.fertig[i + 1] ? "ok" : ""}" aria-label="Schritt ${i + 1}: ${t}"${i + 1 === n ? ' aria-current="step"' : ""}>
      <span>${S.fertig[i + 1] && i + 1 !== n ? "✓" : i + 1}</span>${k}</button>`).join("")}</div>
    <h2>Schritt ${n} von 6 · ${SCHRITTE[n - 1][0]}</h2>`;
  const fuss = `<div class="wrow" style="margin-top:18px">${n > 1 ? `<button class="wb" id="kwZurueck">‹ Zurück</button>` : ""}
    ${n < 6 ? `<button class="wb an" id="kwWeiter">Weiter: ${SCHRITTE[n][0]} ›</button>` : `<button class="wb an" id="kwFertig">Ablauf abschließen</button>`}</div>
    <p class="hint">Grundsätze aus dem Video „Eigene STL-Dateien mit KI erstellen“ (Bastlwastl) – <a href="${AUSWERTUNG}" style="color:var(--blue)">Auswertung lesen</a>.</p><div style="height:20px"></div>`;
  app.innerHTML = kopf + [, eins, zwei, drei, vier, fuenf, sechs][n]() + fuss;
  app.querySelector("#kwZur").onclick = () => C.go("bibliothek");
  app.querySelectorAll("[data-kw]").forEach(b => b.onclick = () => C.go("kiweg:" + b.dataset.kw));
  const zb = app.querySelector("#kwZurueck"); if (zb) zb.onclick = () => C.go("kiweg:" + (n - 1));
  const wb = app.querySelector("#kwWeiter"); if (wb) wb.onclick = () => { S.fertig[n] = true; schreib(); C.go("kiweg:" + (n + 1)); };
  const fb = app.querySelector("#kwFertig"); if (fb) fb.onclick = () => abschliessen();
  binden(app, n);
}

const esc = s => C.esc(s);
const chips = (k, opts, wert) => `<div class="chips">${opts.map(o => `<button class="chip ${wert === o ? "on" : ""}" data-ch="${k}" data-v="${esc(o)}">${esc(o)}</button>`).join("")}</div>`;
const liste = (L, haken, art) => { const n = L.filter(([id]) => haken[id]).length;
  return `<div class="card">${L.map(([id, t, z]) => `<div class="row oben"><button class="haken ${haken[id] ? "on" : ""}" data-pr="${art}" data-id="${id}" aria-pressed="${!!haken[id]}" aria-label="${esc(t)}">${haken[id] ? "✓" : ""}</button>
    <div class="grow"><div>${esc(t)}</div><div class="small">${z ? "laut Video " + z : "📚 eigene Ergänzung"}</div></div></div>`).join("")}</div>
    <p class="hint">${n} von ${L.length} abgehakt · nur auf diesem Gerät gespeichert · <a href="#" data-leeren="${art}" style="color:var(--sub)">zurücksetzen</a></p>`; };

function eins(){
  const I = S.idee, cm = zahl(I.cm);
  return `<p class="hint" style="margin-top:0">Du beschreibst das Motiv – die Regeln aus dem Video stehen schon im Text. Den fertigen Text gibst du einer Bild-KI (z. B. ChatGPT); Claude selbst erzeugt keine Bilder.</p>
  <div class="card">
    <label class="row frage"><div class="small">Motiv</div><textarea data-i="motiv" placeholder="z. B. Frosch in Ritterrüstung, Visier offen, Schwert in der Hand, grimmig">${esc(I.motiv)}</textarea></label>
    <div class="row"><div class="grow">Zielgröße</div><input type="text" inputmode="decimal" class="zahl" data-i="cm" value="${esc(I.cm)}" placeholder="15"><span class="small">cm</span></div>
    <div class="row frage"><div class="small">gemessen als</div>${chips("mass", ["hoch", "breit", "lang"], I.mass)}</div>
    <div class="row frage"><div class="small">Aufstellung</div>${chips("aufstellung", Object.keys(AUFSTELLUNG), I.aufstellung)}</div>
    <label class="row frage"><div class="small">Stil</div><input type="text" data-i="stil" value="${esc(I.stil)}" placeholder="z. B. Fantasy, detailreich, leicht comichaft" style="margin-top:4px"></label>
    <label class="row frage"><div class="small">Oberflächen-Details</div><textarea data-i="details" placeholder="z. B. Risse und Dellen in der Rüstung, Kettenhemd sichtbar, Schwert glatt">${esc(I.details)}</textarea></label>
  </div>
  ${cm && cm < 8 ? `<div class="warn">Bei ${esc(I.cm)} cm passen mit 0,4-mm-Düse nur wenig Details – im Video werden mindestens 15–20 cm empfohlen (19:17).</div>` : ""}
  ${cm > 25.6 ? `<div class="warn">Größer als der Bauraum (25,6 cm) – dann besser „getrennte Teile“ wählen.</div>` : ""}
  <h2>Bauweise</h2><div class="seg"><button data-ch="teilung" data-v="ein" class="${I.teilung === "ein" ? "on" : ""}">Ein Stück</button><button data-ch="teilung" data-v="getrennt" class="${I.teilung === "getrennt" ? "on" : ""}">Getrennte Teile</button></div>
  ${I.teilung === "getrennt" ? `<div class="card" style="margin-top:10px"><label class="row frage"><div class="small">Welches Teil kommt in dieses Bild?</div>
    <input type="text" data-i="teil" value="${esc(I.teil)}" placeholder="z. B. nur die Schnecke, ohne Schild" style="margin-top:4px"></label></div>
    <p class="hint">Je Teil ein eigenes Bild und eine eigene Umwandlung (kostet je Teil), dafür weniger Stützen; im Slicer zusammensetzen oder nach dem Druck kleben (16:41–17:43).</p>`
    : `<p class="hint">Ein Stück ist einfacher, braucht bei abstehenden Teilen aber viele Stützen (17:13).</p>`}
  <h2>Farbe im Bild</h2>${chips("farbe", Object.keys(FARBEN), I.farbe)}
  <p class="hint">Einfarbig und matt – so liest die 3D-KI Licht, Schatten und Struktur am besten (05:07–05:39). Die Druckfarben wählst du später.</p>
  <h2>Schichthöhe</h2>${chips("schicht", ["0,12", "0,16", "0,20"], I.schicht)}
  <h2>Text für die Bild-KI</h2><div class="card"><pre class="prompt" id="kwText"></pre></div>
  <p class="hint">Eigener Text nach den Grundsätzen aus dem Video – der Prompt aus der Videobeschreibung liegt uns nicht vor.</p>
  <button class="btn" id="kwKop" style="margin-top:12px">Kopieren</button>
  <a class="btn grey" id="kwGpt" href="https://chatgpt.com/" target="_blank" rel="noopener">Kopieren und ChatGPT öffnen</a>
  <p class="hint">ChatGPT öffnet sich leer – Text einfügen (lange tippen → „Einsetzen“). Andere Bild-KIs gehen genauso.</p>
  <div class="card" style="margin-top:14px"><div class="row chev" id="kwHabe" style="cursor:pointer" role="button" tabindex="0"><div class="grow"><b>Ich habe schon ein Bild oder Foto</b><div class="small">direkt zu Schritt 3: Bild prüfen</div></div></div></div>`;
}

function zwei(){
  const N = S.nach;
  const opt = (k, t, ph) => `<div class="row oben"><button class="haken ${N[k] ? "on" : ""}" data-n="${k}" aria-pressed="${!!N[k]}" aria-label="${esc(t)}">${N[k] ? "✓" : ""}</button>
    <div class="grow"><div>${esc(t)}</div>${N[k] ? `<input type="text" data-nw="${k}Was" value="${esc(N[k + "Was"] || "")}" placeholder="${esc(ph)}" style="margin-top:6px;font-size:15px">` : ""}</div></div>`;
  return `<div class="card"><ol class="steps">
    <li>ChatGPT oder eine andere Bild-KI öffnen, den Text aus Schritt 1 einfügen und abschicken.</li>
    <li>Warten, bis das Bild fertig ist (dauert etwas).</li>
    <li>Gefällt etwas nicht: unten die Vorlage „Bild nachbessern“ nutzen – das ist billiger als eine misslungene Umwandlung.</li>
    <li>Bild speichern (Fotos oder Dateien), so dass du es wiederfindest.</li></ol></div>
  <p class="hint">Mehrere Figuren einer Serie: in ChatGPT ein <b>Projekt</b> statt eines einzelnen Chats anlegen (07:46). Diktieren per Mikrofon spart Tipparbeit (08:48).</p>
  <div class="card" style="margin-top:10px"><div class="row chev" id="kwTextNochmal" style="cursor:pointer" role="button" tabindex="0"><div class="grow">Text aus Schritt 1 nochmals kopieren</div></div></div>
  <h2>Vorlage: Bild nachbessern</h2>
  <div class="card">${opt("textur", "Mehr Textur", "z. B. Risse und Dellen in allen Metallteilen")}${opt("weg", "Teil entfernen", "z. B. das Cape")}${opt("trennen", "Teile trennen", "z. B. die Schnecke ohne Schild")}
    <label class="row frage"><div class="small">Sonstiges (optional)</div><input type="text" data-nw="sonst" value="${esc(N.sonst || "")}" placeholder="z. B. Das Schwert bleibt glatt." style="margin-top:4px"></label></div>
  <div class="card" style="margin-top:10px"><pre class="prompt" id="kwNach"></pre></div>
  <button class="btn grey" id="kwNachKop" style="margin-top:12px">Nachbessern-Text kopieren</button>
  <p class="hint">Im Video: Cape entfernt, Risse und Dellen in die Rüstung (10:24–11:27).</p>`;
}

function drei(){
  return `<div class="warn">Jede Umwandlung in Schritt 4 kostet Geld oder Punkte – vorher lohnt der genaue Blick (07:46).</div>
  <h2>Bild prüfen, bevor es Geld kostet</h2>${liste(PRUEF_BILD, S.bild, "bild")}
  <div style="height:12px"></div><button class="btn grey" id="kwNachbessern">Etwas passt nicht → Bild nachbessern</button>`;
}

function vier(){
  const I = S.idee, mm = Math.round((zahl(I.cm) || 15) * 10);
  return `<div class="card"><div class="row oben"><div class="grow"><b>A · In der App (fal.ai)</b>
      <div class="small">Bild wählen, Dienst aussuchen (ca. 0,25–0,53 $ je Modell). Das fertige Modell landet in „Meine Modelle“ und öffnet sich in der Werkstatt. Zielgröße aus Schritt 1: ${mm} mm.</div></div></div>
    <div style="padding:0 16px 14px"><button class="btn" id="kwApp">In der App umwandeln</button></div></div>
  <div class="card" style="margin-top:12px"><div class="row oben"><div class="grow"><b>B · Extern: MakerWorld MakerLab</b>
      <div class="small">Bild-zu-3D im Browser, so wie im Video (11:59–20:52).</div></div></div>
    <ol class="steps">
      <li>MakerLab öffnen → „Bild zu 3D“, Bild hineinziehen.</li>
      <li>Modell wählen – im Video am liebsten <b>Tripo 3.1 Standard</b>, Auswahl ändert sich laufend (15:10). Tipp: Bildschirmfoto der Liste an ChatGPT geben und fragen, welches zum Bild passt (15:40).</li>
      <li>Vor dem Bestätigen Kosten und Dauer ansehen (bis zu 20 Min., 14:38). Im Video kostet schon die Erzeugung Punkte, der Download nochmals (13:35, 20:21).</li>
      <li>Ergebnis in der Ansicht <b>„keine Farbe“</b> prüfen – Liste in Schritt 5.</li>
      <li>Drucker mit 0,4-mm-Düse wählen, <b>STL</b> herunterladen (3MF und GLB gehen auch).</li></ol>
    <div style="padding:0 16px 14px"><a class="btn grey" href="${MAKERLAB}" target="_blank" rel="noopener">MakerLab öffnen</a>
      <label class="btn" style="margin-top:10px">Heruntergeladene STL importieren<input type="file" id="kwImp" accept=".stl,.3mf,.obj" multiple hidden></label></div></div>
  <div class="card" style="margin-top:12px"><div class="row oben"><div class="grow"><b>C · Bei Claude im Chat (kostenlos, grob)</b>
      <div class="small">Claude rechnet das Bild selbst um – ohne Dienst und ohne Schlüssel, in etwa 2 Minuten. Deutlich gröber als A und B: gut zum Ausprobieren und für einfache, kompakte Figuren; dünne Teile gehen verloren.</div></div></div>
    <div style="padding:0 16px 14px"><a class="btn grey" target="_blank" rel="noopener" href="https://claude.ai/new?q=${encodeURIComponent(`druckwerk: Bitte das angehängte Bild hier im Chat mit werkzeug/ki_lokal.py in ein 3D-Modell umwandeln (Zielhöhe ${mm} mm). Erst die Vorschau zeigen, noch nicht slicen.`)}">In Claude öffnen und Bild anhängen</a></div></div>
  <p class="hint">KI-Modelle sind nicht maßhaltig – für Deko und Figuren gedacht. Hohle Dinge (Vase, Helm, Maske) gelingen laut Video kaum (02:31).</p>
  ${S.modellId ? `<div class="card" style="margin-top:12px"><div class="row"><span class="haken on" aria-hidden="true">✓</span><div class="grow">Modell ist in „Meine Modelle“</div></div></div>` : ""}`;
}

function fuenf(){
  return `<p class="hint" style="margin-top:0">In MakerLab die Ansicht „keine Farbe“ wählen, in der Werkstatt alle Teile auf eine graue oder weiße Spule stellen – so sieht es aus wie gedruckt (18:15).</p>
  <h2>3D-Modell in Grau auf Fehler prüfen</h2>${liste(PRUEF_MODELL, S.modell, "modell")}
  <div style="height:12px"></div>
  ${S.modellId ? `<button class="btn" id="kwWerk">Modell in der Werkstatt ansehen</button>` : `<button class="btn" id="kwBib">Bibliothek öffnen</button>`}
  <button class="btn grey" id="kwNachbessern">Fehler gefunden → Bild nachbessern</button>
  <p class="hint">Fehler entstehen meist schon im Bild: lieber dort korrigieren und neu umwandeln (18:46).</p>`;
}

function sechs(){
  return `<div class="card"><ol class="steps">
    <li><b>Größe</b> in der Werkstatt auf die Zielgröße stellen (mm) – wichtig für die Details (19:17).</li>
    <li><b>Auf Fläche legen</b>: die Unterseite der Füße bzw. des Sockels antippen (21:53).</li>
    <li><b>Boden plan schneiden</b>, wenn er uneben ist – unten 1–2 mm weg, bis eine solide Schnittfläche entsteht (21:53–22:25). Das kann die Werkstatt noch nicht: dafür den Auftrag an Claude nehmen.</li>
    <li>Nochmals ansehen: muss ein Teil abgeschnitten oder getrennt werden (22:25)?</li>
    <li><b>Slicen</b>: Stützen, Füllung, Wände wie bei jeder STL – Figur z. B. Schicht 0,12–0,20, Füllung 10–15 %, Stützen automatisch.</li>
    <li>Getrennte Teile: zusammen in die Werkstatt laden oder nach dem Druck kleben (17:43).</li></ol></div>
  <div style="height:12px"></div>
  ${S.modellId ? `<button class="btn" id="kwWerk">Werkstatt öffnen (Größe, Fläche, Slicen)</button>` : `<button class="btn" id="kwBib">Bibliothek öffnen</button>`}
  <button class="btn grey" id="kwClaude">Auftrag an Claude: Boden schneiden &amp; aufbereiten</button>
  <p class="hint">Öffnet unter „Neu“ den geführten Weg „Aus Foto per KI“ mit deinen Angaben aus Schritt 1.</p>`;
}

/* ---------- Bedienung ---------- */
async function kopieren(text){
  try { await navigator.clipboard.writeText(text); C.toast("Kopiert"); return true; }
  catch (e) {
    const d = C.sheet(`<h3>Bitte selbst kopieren</h3><p>Text antippen, „Alles auswählen“ → „Kopieren“.</p><div class="card"><textarea readonly style="min-height:220px;font-size:14px">${esc(text)}</textarea></div>
      <div style="height:12px"></div><button class="btn grey" id="kpZu">Fertig</button>`);
    const t = d.querySelector("textarea"); try { t.focus(); t.select(); } catch (x) {}
    d.querySelector("#kpZu").onclick = () => d.remove(); return false;
  }
}

function binden(app, n){
  const neu = () => { const y = scrollY; ansicht(app, C, n); scrollTo(0, y); };
  const tx = app.querySelector("#kwText"), aktuell = () => { if (tx) tx.textContent = bildText(S.idee); };
  aktuell();
  app.querySelectorAll("[data-i]").forEach(e => e.oninput = () => { S.idee[e.dataset.i] = e.value; schreib(); aktuell(); });
  const cmF = app.querySelector('[data-i="cm"]'); if (cmF) cmF.onchange = () => neu();
  app.querySelectorAll("[data-ch]").forEach(b => b.onclick = () => { S.idee[b.dataset.ch] = b.dataset.v; schreib(); neu(); });
  const k = app.querySelector("#kwKop"); if (k) k.onclick = () => kopieren(bildText(S.idee));
  const g = app.querySelector("#kwGpt"); if (g) g.onclick = () => { try { navigator.clipboard.writeText(bildText(S.idee)).then(() => C.toast("Kopiert – in ChatGPT einfügen"), () => {}); } catch (e) {} };
  const h = app.querySelector("#kwHabe"); if (h) h.onclick = h.onkeydown = e => { if (e.type === "keydown" && e.key !== "Enter") return; S.fertig[1] = S.fertig[2] = true; schreib(); C.go("kiweg:3"); };
  // Schritt 2
  const nt = app.querySelector("#kwNach"), nach = () => { if (nt) nt.textContent = nachText(S.idee, S.nach); };
  nach();
  app.querySelectorAll("[data-n]").forEach(b => b.onclick = () => { S.nach[b.dataset.n] = !S.nach[b.dataset.n]; schreib(); neu(); });
  app.querySelectorAll("[data-nw]").forEach(e => e.oninput = () => { S.nach[e.dataset.nw] = e.value; schreib(); nach(); });
  const nk = app.querySelector("#kwNachKop"); if (nk) nk.onclick = () => kopieren(nachText(S.idee, S.nach));
  const tn = app.querySelector("#kwTextNochmal"); if (tn) tn.onclick = tn.onkeydown = e => { if (e.type === "keydown" && e.key !== "Enter") return; kopieren(bildText(S.idee)); };
  // Prüflisten
  app.querySelectorAll("[data-pr]").forEach(b => b.onclick = () => { const L = S[b.dataset.pr]; L[b.dataset.id] = !L[b.dataset.id]; if (!L[b.dataset.id]) delete L[b.dataset.id]; schreib(); neu(); });
  app.querySelectorAll("[data-leeren]").forEach(a => a.onclick = e => { e.preventDefault(); S[a.dataset.leeren] = {}; schreib(); neu(); });
  const nb = app.querySelector("#kwNachbessern"); if (nb) nb.onclick = () => C.go("kiweg:2");
  // Schritt 4
  const ap = app.querySelector("#kwApp"); if (ap) ap.onclick = async () => {
    const mm = Math.round((zahl(S.idee.cm) || 15) * 10);
    try { const w = JSON.parse(localStorage.getItem("druckwerk_ki_wahl") || "{}") || {}; if (mm >= 10 && mm <= 256) localStorage.setItem("druckwerk_ki_wahl", JSON.stringify({...w, mm})); } catch (e) {}
    try { (await import("./ki.js")).oeffnen(C); } catch (e) { C.toast("Konnte nicht geladen werden"); } };
  const im = app.querySelector("#kwImp"); if (im) im.onchange = async e => {
    const fs = [...e.target.files]; e.target.value = ""; if (!fs.length) return;
    C.toast("Datei wird gelesen …");
    try { const id = await (await import("./werkstatt.js")).dateienImportieren(fs, C); S = {...lies(), modellId: id}; S.fertig = {...(S.fertig || {}), 4: true}; schreib(); C.toast("In „Meine Modelle“ gespeichert"); C.go("kiweg:5"); }
    catch (err) { console.error(err); C.toast("Datei konnte nicht gelesen werden"); } };
  // Schritt 5 + 6
  const wk = app.querySelector("#kwWerk"); if (wk) wk.onclick = () => C.go("werkstatt:e:" + S.modellId);
  const bb = app.querySelector("#kwBib"); if (bb) bb.onclick = () => C.go("bibliothek");
  const cl = app.querySelector("#kwClaude"); if (cl) cl.onclick = () => { const I = S.idee;
    const groesse = `${String(zahl(I.cm) || 15).replace(".", ",")} cm ${I.mass}`;
    if (C.neuStart) C.neuStart("", "deko", "", "foto", {motiv: I.motiv, groesse, aufstellung: I.aufstellung, teilung: I.teilung === "getrennt" ? "getrennte Teile" : "ein Stück",
      standflaeche: "ja", sonst: [I.details && "Details: " + I.details, I.teil && "Teil: " + I.teil].filter(Boolean).join(" · ")});
    else C.go("neu"); };
}

function abschliessen(){
  const d = C.sheet(`<h3>Ablauf abschließen?</h3><p>Prüflisten und Fortschritt werden zurückgesetzt. Deine Bild-Idee bleibt als Vorlage stehen.</p>
    <button class="btn" id="abJa">Abschließen</button><button class="btn rot" id="abAlles">Alles leeren (auch die Bild-Idee)</button><button class="btn grey" id="abNein">Abbrechen</button>`);
  d.querySelector("#abNein").onclick = () => d.remove();
  d.querySelector("#abJa").onclick = () => { S = {idee: S.idee}; schreib(); d.remove(); C.toast("Abgeschlossen"); C.go("bibliothek"); };
  d.querySelector("#abAlles").onclick = () => { S = {}; try { localStorage.removeItem(KW); } catch (e) {} d.remove(); C.toast("Geleert"); C.go("bibliothek"); };
}

// Für Bibliothek/Start: läuft ein Ablauf? → {schritt, titel}
export const offen = () => { const s = lies(); return s.aktiv ? {schritt: s.schritt || 1, titel: SCHRITTE[(s.schritt || 1) - 1][0]} : null; };
// Für ki.js: Modell aus der App ist fertig → im Ablauf vermerken
export function modellFertig(id){
  const s = lies(); if (!s.aktiv) return false;
  s.modellId = id; s.fertig = {...(s.fertig || {}), 4: true}; s.schritt = 5;
  try { localStorage.setItem(KW, JSON.stringify(s)); } catch (e) {} return true;
}
