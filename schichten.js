// druckwerk – Schichtvorschau: liest die .gcode-Datei und zeigt jede Schicht von oben
export async function zeigen(url, farben, sheet){
  const d = sheet(`<h3>Schichten</h3><p id="sInfo">Druckdatei wird geladen …</p><canvas id="sview"></canvas>
    <div class="card" style="margin:12px 0"><div class="row"><button class="back" id="sM">−</button><input type="range" id="sReg" min="1" max="1" value="1"><button class="back" id="sP">＋</button></div></div>
    <p class="small" style="margin:0 0 10px">Farben = Spulen · grau = Schicht darunter · der Block am Rand ist der Spülturm.</p><button class="btn grey" id="sZu">Schließen</button>`);
  d.querySelector("#sZu").onclick = () => d.remove();
  const info = d.querySelector("#sInfo");
  let txt;
  try { const r = await fetch(url); if (!r.ok) throw 0; txt = await r.text(); } catch (e) { info.textContent = "Datei nicht gefunden."; return; }
  // --- lesen ---
  const L = [];                       // je Schicht: {z, seg:[x1,y1,x2,y2,werkzeug,...]}
  let x = 0, y = 0, t = 0, akt = null, typ = "", minX = 1e9, minY = 1e9, maxX = -1e9, maxY = -1e9;
  let pos = 0;
  while (pos < txt.length) {
    let end = txt.indexOf("\n", pos); if (end < 0) end = txt.length;
    const c0 = txt.charCodeAt(pos);
    if (c0 === 59) {                  // ;Kommentar
      if (txt.startsWith(";LAYER_CHANGE", pos)) { akt = {z: 0, seg: []}; L.push(akt); }
      else if (akt && txt.startsWith(";Z:", pos)) akt.z = parseFloat(txt.slice(pos + 3, end));
      else if (txt.startsWith(";TYPE:", pos)) typ = txt.slice(pos + 6, end).trim();
    } else if (c0 === 84) { const n = parseInt(txt.slice(pos + 1, end)); if (n >= 0 && n < 16) t = n; }   // T0..T3
    else if (c0 === 71) {             // G0/G1/G2/G3
      const z = txt.slice(pos, end), g = z.charCodeAt(1);
      if ((g >= 48 && g <= 51) && z.charCodeAt(2) === 32) {
        let nx = x, ny = y, e = 0, m;
        if ((m = /X(-?[\d.]+)/.exec(z))) nx = +m[1];
        if ((m = /Y(-?[\d.]+)/.exec(z))) ny = +m[1];
        if ((m = /E(-?[\d.]+)/.exec(z))) e = +m[1];
        if (akt && e > 0 && (nx !== x || ny !== y) && typ !== "Custom") {
          akt.seg.push(x, y, nx, ny, t);
          if (nx < minX) minX = nx; if (nx > maxX) maxX = nx; if (ny < minY) minY = ny; if (ny > maxY) maxY = ny;
          if (x < minX) minX = x; if (x > maxX) maxX = x; if (y < minY) minY = y; if (y > maxY) maxY = y;
        }
        x = nx; y = ny;
      }
    }
    pos = end + 1;
  }
  txt = null;
  const S = L.filter(l => l.seg.length);
  if (!S.length) { info.textContent = "Keine Schichten gefunden."; return; }
  // --- zeichnen ---
  const cv = d.querySelector("#sview"), reg = d.querySelector("#sReg");
  const px = Math.min(devicePixelRatio || 1, 2), gr = Math.round(cv.clientWidth * px); cv.width = cv.height = gr;
  const g = cv.getContext("2d"), rand = 14 * px, f = (gr - 2 * rand) / Math.max(maxX - minX, maxY - minY, 1);
  const ox = (gr - (maxX - minX) * f) / 2, oy = (gr - (maxY - minY) * f) / 2;
  const X = v => ox + (v - minX) * f, Y = v => gr - oy - (v - minY) * f;
  const male = (seg, farbe, alpha) => {
    for (let w = 0; w < 4; w++) {
      g.beginPath(); let n = 0;
      for (let i = 0; i < seg.length; i += 5) if (seg[i+4] === w || (w === 3 && seg[i+4] > 3)) { g.moveTo(X(seg[i]), Y(seg[i+1])); g.lineTo(X(seg[i+2]), Y(seg[i+3])); n++; }
      if (!n) continue;
      g.globalAlpha = alpha; g.strokeStyle = farbe || farben[w] || "#888"; g.stroke();
    }
  };
  const dunkel = matchMedia("(prefers-color-scheme: dark)").matches;
  const zeig = () => {
    const i = +reg.value - 1, s = S[i];
    g.globalAlpha = 1; g.clearRect(0, 0, gr, gr); g.lineWidth = Math.max(1, 0.42 * f); g.lineCap = "round";
    if (i > 0) male(S[i-1].seg, dunkel ? "#555" : "#c8c8cc", .5);
    male(s.seg, null, 1);
    // helle Farben bekommen einen feinen Rand, damit man sie sieht
    info.textContent = `Schicht ${i+1} von ${S.length} · Höhe ${s.z.toFixed(2)} mm · ${Math.round(s.seg.length / 5)} Bahnen`;
  };
  reg.max = S.length; reg.value = Math.min(S.length, 3); reg.oninput = zeig;
  d.querySelector("#sM").onclick = () => { reg.value = Math.max(1, +reg.value - 1); zeig(); };
  d.querySelector("#sP").onclick = () => { reg.value = Math.min(S.length, +reg.value + 1); zeig(); };
  zeig();
}
