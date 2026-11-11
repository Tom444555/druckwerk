// druckwerk – Bibliothek + Werkstatt (Modelle ansehen, umbauen, Farben/Spulen, Export STL/3MF/OBJ/GLB)
import * as THREE from "three";
import { STLLoader } from "three/addons/loaders/STLLoader.js";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import { zipSync, strToU8 } from "three/addons/libs/fflate.module.js";

const $ = s => document.querySelector(s);
const PLATTE = 260;                                  // Kobra X Bauraum in mm
const STD_FARBEN = ["#222222", "#f5f5f5", "#e0352b", "#d4a017"];
let C = null;                                        // Kontext aus index.html (LAGER, farbe, FARBEN, esc, toast, sheet, go)

/* ---------- Speicher auf dem Gerät (IndexedDB) ---------- */
let _mem = new Map();                                // Rückfall, wenn IndexedDB gesperrt ist
function db(){
  return new Promise((ok, err) => {
    const r = indexedDB.open("druckwerk", 1);
    r.onupgradeneeded = () => r.result.createObjectStore("modelle", {keyPath: "id"});
    r.onsuccess = () => ok(r.result); r.onerror = () => err(r.error);
  });
}
async function dbTx(mode, fn){
  const d = await db();
  return new Promise((ok, err) => {
    const tx = d.transaction("modelle", mode), q = fn(tx.objectStore("modelle"));
    tx.oncomplete = () => ok(q && q.result); tx.onerror = () => err(tx.error);
  });
}
const eigeneAlle = async () => { try { return (await dbTx("readonly", s => s.getAll())) || []; } catch(e) { return [..._mem.values()]; } };
const eigenesHolen = async id => { try { return await dbTx("readonly", s => s.get(id)); } catch(e) { return _mem.get(id); } };
const eigenesSichern = async m => { _mem.set(m.id, m); try { await dbTx("readwrite", s => s.put(m)); } catch(e) {} };
const eigenesLoeschen = async id => { _mem.delete(id); try { await dbTx("readwrite", s => s.delete(id)); } catch(e) {} };

/* ---------- Geometrie-Helfer ---------- */
function sauber(geo){                                // nur Positionen, nicht indiziert, Normale neu
  let g = geo.index ? geo.toNonIndexed() : geo;
  const n = new THREE.BufferGeometry();
  n.setAttribute("position", new THREE.BufferAttribute(new Float32Array(g.getAttribute("position").array), 3));
  n.computeVertexNormals();
  return n;
}
function wende(geo){                                 // Dreiecke umdrehen (nach Spiegeln)
  const p = geo.getAttribute("position").array;
  for (let i = 0; i < p.length; i += 9) for (let k = 0; k < 3; k++) { const t = p[i+3+k]; p[i+3+k] = p[i+6+k]; p[i+6+k] = t; }
}
function stlBinaer(geos){                            // ein oder mehrere Teile -> binäre STL
  const n = geos.reduce((s, g) => s + g.getAttribute("position").count / 3, 0);
  const buf = new ArrayBuffer(84 + n * 50), dv = new DataView(buf);
  dv.setUint32(80, n, true);
  let o = 84; const a = new THREE.Vector3(), b = new THREE.Vector3(), c = new THREE.Vector3(), nn = new THREE.Vector3();
  for (const g of geos) {
    const p = g.getAttribute("position").array;
    for (let i = 0; i < p.length; i += 9) {
      a.set(p[i], p[i+1], p[i+2]); b.set(p[i+3], p[i+4], p[i+5]); c.set(p[i+6], p[i+7], p[i+8]);
      nn.subVectors(b, a).cross(c.clone().sub(a)).normalize();
      dv.setFloat32(o, nn.x, true); dv.setFloat32(o+4, nn.y, true); dv.setFloat32(o+8, nn.z, true); o += 12;
      for (let k = 0; k < 9; k++) { dv.setFloat32(o, p[i+k], true); o += 4; }
      o += 2;
    }
  }
  return buf;
}
function indiziert(geo){                             // gleiche Punkte zusammenfassen (für 3MF/OBJ nötig)
  const p = geo.getAttribute("position").array, map = new Map(), v = [], t = new Uint32Array(p.length / 3);
  for (let i = 0; i < p.length; i += 3) {
    const k = Math.round(p[i]*1e4) + "," + Math.round(p[i+1]*1e4) + "," + Math.round(p[i+2]*1e4);
    let id = map.get(k);
    if (id === undefined) { id = v.length / 3; map.set(k, id); v.push(p[i], p[i+1], p[i+2]); }
    t[i/3] = id;
  }
  return {v, t};
}
const z5 = x => (Math.round(x * 1e5) / 1e5).toString();
const xmlEsc = s => String(s).replace(/[&<>"]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
const datei = s => String(s).replace(/[^\wäöüÄÖÜß\-]+/g, "_").replace(/^_+|_+$/g, "") || "modell";

/* ---------- Export ---------- */
function laden(name, daten, typ){
  const u = URL.createObjectURL(new Blob([daten], {type: typ || "application/octet-stream"}));
  const a = document.createElement("a"); a.href = u; a.download = name; document.body.appendChild(a); a.click(); a.remove();
  setTimeout(() => URL.revokeObjectURL(u), 20000);
}
function export3mf(M){
  const teile = M.teile.filter(t => !t.weg);
  const mats = M.slots.map((f, i) => `<base name="Spule ${i+1}" displaycolor="${f.toUpperCase()}FF"/>`).join("");
  const st = ['<?xml version="1.0" encoding="UTF-8"?>\n<model unit="millimeter" xml:lang="de" xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02" xmlns:BambuStudio="http://schemas.bambulab.com/package/2021">\n',
    `<metadata name="Application">BambuStudio-01.09.00.00</metadata>\n<metadata name="BambuStudio:3mfVersion">1</metadata>\n<metadata name="Title">${xmlEsc(M.name)}</metadata>\n`,
    `<resources>\n<basematerials id="100">${mats}</basematerials>\n`];
  teile.forEach((t, i) => {
    const {v, t: tri} = indiziert(t.geo), z = [];
    z.push(`<object id="${i+1}" name="${xmlEsc(t.name)}" type="model" pid="100" pindex="${t.slot-1}"><mesh><vertices>`);
    for (let k = 0; k < v.length; k += 3) z.push(`<vertex x="${z5(v[k])}" y="${z5(v[k+1])}" z="${z5(v[k+2])}"/>`);
    z.push("</vertices><triangles>");
    for (let k = 0; k < tri.length; k += 3) if (tri[k] !== tri[k+1] && tri[k+1] !== tri[k+2] && tri[k] !== tri[k+2])
      z.push(`<triangle v1="${tri[k]}" v2="${tri[k+1]}" v3="${tri[k+2]}"/>`);
    z.push("</triangles></mesh></object>\n");
    st.push(z.join(""));
  });
  // alle Teile als EIN Objekt (Baugruppe), damit sie im Slicer zusammenbleiben
  const gid = teile.length + 1;
  st.push(`<object id="${gid}" name="${xmlEsc(M.name)}" type="model"><components>${teile.map((t, i) => `<component objectid="${i+1}"/>`).join("")}</components></object>\n`);
  st.push(`</resources>\n<build><item objectid="${gid}" printable="1"/></build>\n</model>\n`);
  const cfg = `<?xml version="1.0" encoding="UTF-8"?>\n<config>\n<object id="${gid}">\n<metadata key="name" value="${xmlEsc(M.name)}"/>\n<metadata key="extruder" value="${teile[0] ? teile[0].slot : 1}"/>\n` +
    teile.map((t, i) => `<part id="${i+1}" subtype="normal_part">\n<metadata key="name" value="${xmlEsc(t.name)}"/>\n<metadata key="extruder" value="${t.slot}"/>\n</part>\n`).join("") + `</object>\n</config>\n`;
  const enc = new TextEncoder();
  return zipSync({
    "[Content_Types].xml": strToU8('<?xml version="1.0" encoding="UTF-8"?>\n<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/></Types>'),
    "_rels/.rels": strToU8('<?xml version="1.0" encoding="UTF-8"?>\n<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Target="/3D/3dmodel.model" Id="rel-1" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>'),
    "3D/3dmodel.model": enc.encode(st.join("")),
    "Metadata/model_settings.config": strToU8(cfg),
  }, {level: 6});
}
function exportObj(M){
  const teile = M.teile.filter(t => !t.weg), o = [`mtllib ${datei(M.name)}.mtl\n`];
  let off = 1;
  for (const t of teile) {
    const {v, t: tri} = indiziert(t.geo), z = [`o ${datei(t.name)}\nusemtl spule${t.slot}\n`];
    for (let k = 0; k < v.length; k += 3) z.push(`v ${z5(v[k])} ${z5(v[k+1])} ${z5(v[k+2])}\n`);
    for (let k = 0; k < tri.length; k += 3) z.push(`f ${tri[k]+off} ${tri[k+1]+off} ${tri[k+2]+off}\n`);
    off += v.length / 3; o.push(z.join(""));
  }
  const mtl = M.slots.map((f, i) => { const c = new THREE.Color(f);
    return `newmtl spule${i+1}\nKd ${c.r.toFixed(3)} ${c.g.toFixed(3)} ${c.b.toFixed(3)}\n`; }).join("\n");
  return zipSync({[datei(M.name) + ".obj"]: new TextEncoder().encode(o.join("")), [datei(M.name) + ".mtl"]: strToU8(mtl)});
}
async function exportGlb(M){
  const { GLTFExporter } = await import("three/addons/exporters/GLTFExporter.js");
  const g = new THREE.Group(); g.rotation.x = -Math.PI / 2; g.scale.setScalar(0.001);   // glTF: Y oben, Meter
  for (const t of M.teile.filter(t => !t.weg)) { const m = new THREE.Mesh(t.geo, new THREE.MeshStandardMaterial({color: M.slots[t.slot-1], roughness: .6})); m.name = t.name; g.add(m); }
  const sz = new THREE.Scene(); sz.add(g); sz.updateMatrixWorld(true);
  return await new GLTFExporter().parseAsync(sz, {binary: true});
}

/* ---------- Bibliothek ---------- */
export async function bibliothek(app, ctx){
  C = ctx;
  const eigene = (await eigeneAlle()).sort((a, b) => (b.datum || "").localeCompare(a.datum || ""));
  // Lager: je Modellname nur einmal (Kobra bevorzugt)
  const lager = []; for (const a of C.LAGER) { const i = lager.findIndex(x => x.name === a.name);
    if (i < 0) lager.push(a); else if (a.drucker === "kobrax" && lager[i].drucker !== "kobrax") lager[i] = a; }
  const karte = (id, bild, name, sub, punkte) => `
    <div class="mk" data-m="${C.esc(id)}" data-n="${C.esc(name.toLowerCase())}">
      <div class="mb">${bild ? `<img src="${C.esc(bild)}" alt="" loading="lazy">` : ""}</div>
      <div class="mt"><b>${C.esc(name)}</b><div class="small">${C.esc(sub)}</div>
        <div class="dots">${punkte.map(f => `<span class="dot" style="background:${f}"></span>`).join("")}</div></div></div>`;
  app.innerHTML = `<h1>Bibliothek</h1>
    <div class="card"><div class="row"><input type="text" id="suche" placeholder="Modell suchen"></div></div>
    <label class="btn" style="margin-top:12px">Eigene Datei öffnen (STL · 3MF · OBJ)
      <input type="file" id="imp" accept=".stl,.3mf,.obj" multiple hidden></label>
    <p class="hint">Mehrere Dateien zusammen wählen = ein Modell aus mehreren Teilen (je Teil eine Farbe).</p>
    ${eigene.length ? `<h2>Meine Modelle (auf diesem Gerät)</h2><div class="mgrid">${eigene.map(m =>
      karte("e:" + m.id, m.bild, m.name, `${m.teile.length} Teil${m.teile.length > 1 ? "e" : ""} · ${m.datum || ""}`, [...new Set(m.teile.map(t => m.slots[t.slot-1]))])).join("")}</div>` : ""}
    <h2>Aus dem Lager (${lager.length})</h2>
    <div class="mgrid">${lager.map(a => karte("l:" + a.ordner, a.vorschau ? `auftraege/${a.ordner}/${a.vorschau}` : "", a.name,
      `${a.teile.length} Teil${a.teile.length > 1 ? "e" : ""} · ${a.datum}`, a.slots.map(s => C.farbe(s.farbe)))).join("")}</div>`;
  app.querySelectorAll(".mk").forEach(k => k.onclick = () => C.go("werkstatt:" + k.dataset.m));
  $("#suche").oninput = e => { const q = e.target.value.toLowerCase().trim();
    app.querySelectorAll(".mk").forEach(k => k.style.display = k.dataset.n.includes(q) ? "" : "none"); };
  $("#imp").onchange = async e => {
    const fs = [...e.target.files]; if (!fs.length) return;
    C.toast("Datei wird gelesen …");
    try { const m = await importieren(fs); await eigenesSichern(m); C.go("werkstatt:e:" + m.id); }
    catch (err) { C.toast("Datei konnte nicht gelesen werden"); console.error(err); }
  };
}

async function importieren(files){
  const teile = [];
  for (const f of files) {
    const ext = f.name.split(".").pop().toLowerCase(), basis = f.name.replace(/\.[^.]+$/, "");
    const buf = await f.arrayBuffer();
    if (ext === "stl") teile.push({name: basis, geo: sauber(new STLLoader().parse(buf))});
    else {
      let obj;
      if (ext === "3mf") { const { ThreeMFLoader } = await import("three/addons/loaders/3MFLoader.js"); obj = new ThreeMFLoader().parse(buf); }
      else if (ext === "obj") { const { OBJLoader } = await import("three/addons/loaders/OBJLoader.js"); obj = new OBJLoader().parse(new TextDecoder().decode(buf)); }
      else throw new Error("Format " + ext);
      obj.updateMatrixWorld(true); let n = 0;
      obj.traverse(o => { if (o.isMesh && o.geometry) { const g = sauber(o.geometry); g.applyMatrix4(o.matrixWorld);
        if (o.matrixWorld.determinant() < 0) wende(g); g.computeVertexNormals();
        let farbe = null; const mt = Array.isArray(o.material) ? o.material[0] : o.material;
        if (mt && mt.color) farbe = "#" + mt.color.getHexString();
        teile.push({name: o.name || `${basis} ${++n}`, geo: g, farbe}); } });
    }
  }
  if (!teile.length) throw new Error("kein Netz");
  // Farben -> bis zu 4 Spulen
  const slots = [...STD_FARBEN]; const gesehen = [];
  teile.forEach((t, i) => {
    if (t.farbe) { let k = gesehen.indexOf(t.farbe); if (k < 0 && gesehen.length < 4) { gesehen.push(t.farbe); k = gesehen.length - 1; slots[k] = t.farbe; } t.slot = k < 0 ? 1 : k + 1; }
    else t.slot = files.length > 1 || teile.length > 1 ? Math.min(i + 1, 4) : 1;
  });
  return { id: "m" + Date.now().toString(36), name: files[0].name.replace(/\.[^.]+$/, ""), datum: new Date().toISOString().slice(0, 10),
    herkunft: "Datei", slots, bild: "", teile: teile.map(t => ({name: t.name, slot: t.slot, stl: stlBinaer([t.geo])})) };
}

/* ---------- Werkstatt ---------- */
let M = null, R = null;                              // Modell, Renderer-Zustand
export async function werkstatt(app, ctx, id){
  C = ctx;
  app.innerHTML = `<button class="back" id="zur">‹ Bibliothek</button><h1 id="wname">Werkstatt</h1>
    <div id="wview"><span class="small" id="wtext">Modell wird geladen …</span></div><div id="wui"></div>`;
  $("#zur").onclick = () => C.go("bibliothek");
  try { M = await modellLaden(id, t => { const e = $("#wtext"); if (e) e.textContent = t; }); }
  catch (e) { console.error(e); $("#wtext").textContent = "Modell konnte nicht geladen werden"; return; }
  if (!$("#wview")) return;
  $("#wname").textContent = M.name;
  szene(); setzen(new THREE.Matrix4(), null, true); ui();
}

async function modellLaden(id, fortschritt){
  const m = { id, name: "", teile: [], slots: [...STD_FARBEN], kum: new THREE.Matrix4(), undo: [], ops: [], lager: null, eigen: null };
  if (id.startsWith("l:")) {
    const a = C.LAGER.find(x => x.ordner === id.slice(2)); if (!a) throw new Error("nicht im Lager");
    m.name = a.name; m.lager = a; a.slots.forEach(s => { if (s.slot <= 4) m.slots[s.slot-1] = "#" + new THREE.Color(C.farbe(s.farbe)).getHexString(); });
    m.material = a.slots.map(s => s.material);
    const ld = new STLLoader();
    for (const [i, t] of a.teile.entries()) {
      const g = await ld.loadAsync(`auftraege/${a.ordner}/${encodeURIComponent(t.datei)}`, ev => { if (ev.total) fortschritt(`Teil ${i+1}/${a.teile.length} · ${Math.round(100*ev.loaded/ev.total)} %`); });
      m.teile.push({name: t.datei.replace(/\.stl$/i, ""), slot: Math.min(t.slot, 4), geo: sauber(g)});
    }
  } else {
    const e = await eigenesHolen(id.slice(2)); if (!e) throw new Error("nicht gefunden");
    m.name = e.name; m.eigen = e; m.slots = [...e.slots]; m.ops = [...(e.ops || [])];
    for (const t of e.teile) m.teile.push({name: t.name, slot: t.slot, geo: sauber(new STLLoader().parse(t.stl))});
  }
  return m;
}

function szene(){
  const el = $("#wview"), w = el.clientWidth, h = el.clientHeight;
  const r = new THREE.WebGLRenderer({antialias: true, alpha: true, preserveDrawingBuffer: true});
  r.setPixelRatio(Math.min(devicePixelRatio, 2)); r.setSize(w, h); r.domElement.style.cssText = "position:absolute;inset:0;border-radius:12px;touch-action:none";
  el.appendChild(r.domElement);
  const sc = new THREE.Scene();
  sc.add(new THREE.HemisphereLight(0xffffff, 0x777777, 1.7));
  const dl = new THREE.DirectionalLight(0xffffff, 1.3); dl.position.set(150, -200, 300); sc.add(dl);
  const cam = new THREE.PerspectiveCamera(38, w / h, 1, 5000); cam.up.set(0, 0, 1);
  const dunkel = matchMedia("(prefers-color-scheme: dark)").matches;
  const gitter = new THREE.GridHelper(PLATTE, 26, dunkel ? 0x666666 : 0x999999, dunkel ? 0x333333 : 0xcccccc); gitter.rotation.x = Math.PI / 2; sc.add(gitter);
  const platte = new THREE.Mesh(new THREE.PlaneGeometry(PLATTE, PLATTE), new THREE.MeshBasicMaterial({color: dunkel ? 0x1c1c1e : 0xe9e9ee, transparent: true, opacity: .6, side: THREE.DoubleSide}));
  platte.position.z = -0.05; sc.add(platte);
  const grp = new THREE.Group(); sc.add(grp);
  for (const t of M.teile) { t.mesh = new THREE.Mesh(t.geo, new THREE.MeshStandardMaterial({color: M.slots[t.slot-1], roughness: .6})); grp.add(t.mesh); }
  const ctl = new OrbitControls(cam, r.domElement); ctl.enableDamping = true;
  R = {r, sc, cam, ctl, grp, waehlen: false};
  new ResizeObserver(() => { const w = el.clientWidth, h = el.clientHeight; if (!w || !h) return; r.setSize(w, h); cam.aspect = w / h; cam.updateProjectionMatrix(); }).observe(el);
  // Fläche antippen -> nach unten legen
  let px = 0, py = 0;
  r.domElement.addEventListener("pointerdown", e => { px = e.clientX; py = e.clientY; });
  r.domElement.addEventListener("pointerup", e => {
    if (!R.waehlen || Math.hypot(e.clientX - px, e.clientY - py) > 6) return;
    const b = r.domElement.getBoundingClientRect(), rc = new THREE.Raycaster();
    rc.setFromCamera(new THREE.Vector2(((e.clientX - b.left) / b.width) * 2 - 1, -((e.clientY - b.top) / b.height) * 2 + 1), cam);
    const tr = rc.intersectObjects(M.teile.filter(t => !t.weg).map(t => t.mesh))[0];
    if (!tr) return;
    const q = new THREE.Quaternion().setFromUnitVectors(tr.face.normal.clone().normalize(), new THREE.Vector3(0, 0, -1));
    R.waehlen = false; setzen(new THREE.Matrix4().makeRotationFromQuaternion(q), "Auf angetippte Fläche gelegt"); ui();
  });
  (function lauf(){ if (!document.body.contains(r.domElement)) { r.dispose(); return; } ctl.update(); r.render(sc, cam); requestAnimationFrame(lauf); })();
}

function kasten(){
  const b = new THREE.Box3();
  for (const t of M.teile) if (!t.weg) { t.geo.computeBoundingBox(); b.union(t.geo.boundingBox); }
  return b;
}
function roh(mat){
  const neg = mat.determinant() < 0;
  for (const t of M.teile) { t.geo.applyMatrix4(mat); if (neg) wende(t.geo); t.geo.computeVertexNormals(); t.geo.computeBoundingBox(); t.geo.computeBoundingSphere(); }
  M.kum.premultiply(mat);
}
// Änderung anwenden und Modell wieder mittig auf die Platte stellen
function setzen(mat, text, kamera){
  roh(mat);
  const b = kasten(), c = b.getCenter(new THREE.Vector3());
  const sitz = new THREE.Matrix4().makeTranslation(-c.x, -c.y, -b.min.z); roh(sitz);
  if (text) { M.undo.push(sitz.multiply(mat)); M.ops.push(text); }
  // Kamera: Blickrichtung behalten, Abstand ans Modell anpassen
  const s = kasten().getSize(new THREE.Vector3()), d = Math.max(s.length(), 30) * 2.1;
  const ziel = new THREE.Vector3(0, 0, s.z / 2);
  const ri = kamera ? new THREE.Vector3(.55, -.72, .42) : R.cam.position.clone().sub(R.ctl.target).normalize();
  if (kamera || text) { R.ctl.target.copy(ziel); R.cam.position.copy(ziel).addScaledVector(ri.normalize(), d); R.ctl.update(); }
}
function rueck(){
  const m = M.undo.pop(); if (!m) return; M.ops.pop(); roh(m.clone().invert()); setzen(new THREE.Matrix4(), null, false);
  const s = kasten().getSize(new THREE.Vector3()); R.ctl.target.set(0, 0, s.z / 2);
}
const fnum = x => (Math.round(x * 10) / 10).toString().replace(".", ",");
const lesen = v => parseFloat(String(v).replace(",", "."));
const farbName = hex => { const h = new THREE.Color(hex).getHexString();
  for (const [n, f] of Object.entries(C.FARBEN)) if (new THREE.Color(f).getHexString() === h) return n; return hex; };

function ui(){
  const u = $("#wui"); if (!u) return;
  const s = kasten().getSize(new THREE.Vector3());
  const zuGross = s.x > PLATTE || s.y > PLATTE || s.z > PLATTE;
  const sichtbar = M.teile.filter(t => !t.weg);
  const dreiecke = sichtbar.reduce((n, t) => n + t.geo.getAttribute("position").count / 3, 0);
  $("#wtext").textContent = R.waehlen ? "Jetzt die Fläche antippen, die unten liegen soll" : "Drehen mit Finger · Platte 260 × 260 mm";
  u.innerHTML = `
    <div class="stats"><div class="stat"><span class="small">Breite X</span><b>${fnum(s.x)}</b></div>
      <div class="stat"><span class="small">Tiefe Y</span><b>${fnum(s.y)}</b></div>
      <div class="stat"><span class="small">Höhe Z</span><b>${fnum(s.z)}</b></div></div>
    ${zuGross ? `<div class="warn">⚠ Größer als der Bauraum (260 mm) – bitte verkleinern.</div>` : ""}
    <div class="wrow"><button class="wb" id="uRueck" ${M.undo.length ? "" : "disabled"}>↶ Rückgängig</button>
      <button class="wb" id="uAlles" ${M.undo.length ? "" : "disabled"}>Alles zurück</button></div>

    <h2>Größe</h2><div class="card">
      <div class="row"><div class="grow">Skalieren</div><input class="zahl" id="gPro" inputmode="decimal" value="100"><span class="val">%</span><button class="wb klein" id="gOk">Anwenden</button></div>
      <div class="row"><div class="grow">Breite X</div><input class="zahl" data-ax="x" inputmode="decimal" value="${fnum(s.x)}"><span class="val">mm</span></div>
      <div class="row"><div class="grow">Tiefe Y</div><input class="zahl" data-ax="y" inputmode="decimal" value="${fnum(s.y)}"><span class="val">mm</span></div>
      <div class="row"><div class="grow">Höhe Z</div><input class="zahl" data-ax="z" inputmode="decimal" value="${fnum(s.z)}"><span class="val">mm</span></div>
      <div class="row"><div class="grow">Proportionen halten</div><input type="checkbox" id="gProp" ${M.frei ? "" : "checked"}></div>
    </div><p class="hint">Maß eintippen und bestätigen – mit „Proportionen halten“ wächst alles gleichmäßig mit.</p>

    <h2>Drehen</h2>
    <div class="seg" id="achse">${["x","y","z"].map(a => `<button data-a="${a}" class="${(M.achse || "z") === a ? "on" : ""}">Achse ${a.toUpperCase()}</button>`).join("")}</div>
    <div class="wrow" style="margin-top:8px">${[-90,-15,15,90].map(g => `<button class="wb" data-g="${g}">${g > 0 ? "+" : "−"}${Math.abs(g)}°</button>`).join("")}</div>
    <div class="wrow"><button class="wb ${R.waehlen ? "an" : ""}" id="flaeche">${R.waehlen ? "Fläche antippen … (abbrechen)" : "Auf Fläche legen"}</button></div>

    <h2>Spiegeln</h2>
    <div class="wrow">${["x","y","z"].map(a => `<button class="wb" data-sp="${a}">${a.toUpperCase()}</button>`).join("")}</div>

    <h2>Spulen (Farben)</h2>
    <div class="card"><div class="row" style="justify-content:space-around">${M.slots.map((f, i) => `
      <button class="spule" data-sl="${i}"><span style="background:${f}"></span>Spule ${i+1}</button>`).join("")}</div></div>
    <p class="hint">Spule antippen = Farbe ändern. Jedes Teil bekommt unten seine Spule.</p>

    <h2>Teile (${sichtbar.length}) · ${dreiecke < 1000 ? dreiecke : Math.round(dreiecke / 1000) + " Tsd."} Dreiecke</h2>
    <div class="card">${M.teile.map((t, i) => t.weg ? "" : `
      <div class="row"><span class="dot" style="background:${M.slots[t.slot-1]};width:22px;height:22px"></span>
        <div class="grow tname" style="${t.aus ? "opacity:.4" : ""}">${C.esc(t.name)}</div>
        <div class="seg mini">${[1,2,3,4].map(n => `<button data-t="${i}" data-n="${n}" class="${t.slot === n ? "on" : ""}">${n}</button>`).join("")}</div>
        <button class="back" data-auge="${i}" title="ein/aus">${t.aus ? "◌" : "◉"}</button>
        ${sichtbar.length > 1 ? `<button class="back" data-del="${i}" style="color:var(--red)">✕</button>` : ""}</div>`).join("")}
    </div>

    <h2>Speichern</h2>
    <button class="btn" id="expo">Speichern / Exportieren …</button>
    <button class="btn grey" id="merken">In „Meine Modelle“ sichern</button>
    <button class="btn grey" id="claude">An Claude zum Slicen schicken</button>
    ${M.eigen ? `<button class="btn grey" id="weg" style="color:var(--red)">Aus „Meine Modelle“ löschen</button>` : ""}
    ${M.ops.length ? `<h2>Änderungen</h2><div class="card">${M.ops.map(o => `<div class="row"><div class="grow small">${C.esc(o)}</div></div>`).join("")}</div>` : ""}`;

  const neu = () => ui();
  $("#uRueck").onclick = () => { rueck(); neu(); };
  $("#uAlles").onclick = () => { while (M.undo.length) rueck(); neu(); };
  $("#gProp").onchange = e => { M.frei = !e.target.checked; };
  $("#gOk").onclick = () => { const f = lesen($("#gPro").value) / 100; if (!(f > 0) || f === 1) return;
    setzen(new THREE.Matrix4().makeScale(f, f, f), `Skaliert auf ${fnum(f * 100)} %`, true); neu(); };
  u.querySelectorAll("[data-ax]").forEach(e => e.onchange = () => {
    const ax = e.dataset.ax, ziel = lesen(e.value), ist = kasten().getSize(new THREE.Vector3())[ax];
    if (!(ziel > 0) || !(ist > 0)) return neu();
    const f = ziel / ist; if (Math.abs(f - 1) < 1e-4) return;
    const m = M.frei ? new THREE.Matrix4().makeScale(ax === "x" ? f : 1, ax === "y" ? f : 1, ax === "z" ? f : 1) : new THREE.Matrix4().makeScale(f, f, f);
    setzen(m, M.frei ? `${ax.toUpperCase()} gestreckt auf ${fnum(ziel)} mm` : `Skaliert auf ${fnum(f * 100)} % (${ax.toUpperCase()} = ${fnum(ziel)} mm)`, true); neu(); });
  u.querySelectorAll("#achse button").forEach(b => b.onclick = () => { M.achse = b.dataset.a; neu(); });
  u.querySelectorAll("[data-g]").forEach(b => b.onclick = () => { const a = M.achse || "z", g = +b.dataset.g, w = g * Math.PI / 180;
    const m = a === "x" ? new THREE.Matrix4().makeRotationX(w) : a === "y" ? new THREE.Matrix4().makeRotationY(w) : new THREE.Matrix4().makeRotationZ(w);
    setzen(m, `Gedreht um ${a.toUpperCase()} ${g > 0 ? "+" : "−"}${Math.abs(g)}°`); neu(); });
  $("#flaeche").onclick = () => { R.waehlen = !R.waehlen; neu(); if (R.waehlen) $("#wview").scrollIntoView({behavior: "smooth", block: "start"}); };
  u.querySelectorAll("[data-sp]").forEach(b => b.onclick = () => { const a = b.dataset.sp;
    setzen(new THREE.Matrix4().makeScale(a === "x" ? -1 : 1, a === "y" ? -1 : 1, a === "z" ? -1 : 1), `Gespiegelt an ${a.toUpperCase()}`); neu(); });
  u.querySelectorAll("[data-sl]").forEach(b => b.onclick = () => farbWahl(+b.dataset.sl));
  u.querySelectorAll("[data-t]").forEach(b => b.onclick = () => { const t = M.teile[+b.dataset.t]; t.slot = +b.dataset.n; t.mesh.material.color.set(M.slots[t.slot-1]); neu(); });
  u.querySelectorAll("[data-auge]").forEach(b => b.onclick = () => { const t = M.teile[+b.dataset.auge]; t.aus = !t.aus; t.mesh.visible = !t.aus; neu(); });
  u.querySelectorAll("[data-del]").forEach(b => b.onclick = () => { const t = M.teile[+b.dataset.del]; t.weg = true; t.mesh.visible = false; M.ops.push(`Teil „${t.name}“ entfernt`); M.undo.push(new THREE.Matrix4()); setzen(new THREE.Matrix4()); neu(); });
  $("#expo").onclick = exportWahl;
  $("#merken").onclick = merken;
  $("#claude").onclick = anClaude;
  const w = $("#weg"); if (w) w.onclick = async () => { await eigenesLoeschen(M.eigen.id); C.toast("Gelöscht"); C.go("bibliothek"); };
}

function farbWahl(i){
  const namen = ["schwarz","weiß","grau","silber","rot","orange","gelb","gold","grün","türkis","blau","lila","pink","braun","holz","creme","natur"];
  const d = C.sheet(`<h3>Farbe für Spule ${i+1}</h3>
    <div class="palette">${namen.map(n => `<button data-f="${C.farbe(n)}"><span style="background:${C.farbe(n)}"></span>${n}</button>`).join("")}</div>
    <div class="card" style="margin:12px 0"><div class="row"><div class="grow">Eigene Farbe</div><input type="color" id="fEigen" value="${M.slots[i]}"></div></div>
    <button class="btn grey" id="fZu">Fertig</button>`);
  const nimm = f => { M.slots[i] = "#" + new THREE.Color(f).getHexString(); for (const t of M.teile) if (t.slot === i + 1) t.mesh.material.color.set(M.slots[i]); ui(); };
  d.querySelectorAll("[data-f]").forEach(b => b.onclick = () => { nimm(b.dataset.f); d.remove(); });
  d.querySelector("#fEigen").oninput = e => nimm(e.target.value);
  d.querySelector("#fZu").onclick = () => d.remove();
}

function exportWahl(){
  const n = datei(M.name), teile = M.teile.filter(t => !t.weg);
  const d = C.sheet(`<h3>„${C.esc(M.name)}“ speichern</h3><p>Mit allen Änderungen, in mm.</p>
    <button class="btn" data-x="3mf">3MF – Teile, Farben &amp; Spulen (empfohlen)</button>
    <button class="btn grey" data-x="stl">STL – alles in einer Datei</button>
    ${teile.length > 1 ? `<button class="btn grey" data-x="stlzip">STL – jedes Teil einzeln (ZIP)</button>` : ""}
    <button class="btn grey" data-x="obj">OBJ + Farben (ZIP)</button>
    <button class="btn grey" data-x="glb">GLB – 3D-Ansicht mit Farben</button>`);
  d.querySelectorAll("[data-x]").forEach(b => b.onclick = async () => {
    const x = b.dataset.x; b.textContent = "Wird erstellt …";
    await new Promise(r => setTimeout(r, 30));
    try {
      if (x === "3mf") laden(n + ".3mf", export3mf(M), "model/3mf");
      if (x === "stl") laden(n + ".stl", stlBinaer(teile.map(t => t.geo)), "model/stl");
      if (x === "stlzip") { const z = {}; teile.forEach((t, i) => z[`${i+1}_spule${t.slot}_${datei(t.name)}.stl`] = new Uint8Array(stlBinaer([t.geo]))); laden(n + "_teile.zip", zipSync(z), "application/zip"); }
      if (x === "obj") laden(n + "_obj.zip", exportObj(M), "application/zip");
      if (x === "glb") laden(n + ".glb", await exportGlb(M), "model/gltf-binary");
      C.toast("Gespeichert");
    } catch (e) { console.error(e); C.toast("Export fehlgeschlagen"); }
    d.remove();
  });
}

async function merken(){
  R.r.render(R.sc, R.cam);
  let bild = ""; try { const c = document.createElement("canvas"); c.width = 360; c.height = 270;
    c.getContext("2d").drawImage(R.r.domElement, 0, 0, 360, 270); bild = c.toDataURL("image/jpeg", .8); } catch (e) {}
  const neuId = M.eigen ? M.eigen.id : "m" + Date.now().toString(36);
  const e = { id: neuId, name: M.eigen ? M.eigen.name : M.name + " (bearbeitet)", datum: new Date().toISOString().slice(0, 10),
    herkunft: M.lager ? "Lager: " + M.lager.ordner : (M.eigen && M.eigen.herkunft) || "Datei", slots: [...M.slots], bild, ops: [...M.ops],
    teile: M.teile.filter(t => !t.weg).map(t => ({name: t.name, slot: t.slot, stl: stlBinaer([t.geo])})) };
  await eigenesSichern(e); M.eigen = e; C.toast("In „Meine Modelle“ gesichert"); ui();
}

function anClaude(){
  const s = kasten().getSize(new THREE.Vector3()), teile = M.teile.filter(t => !t.weg);
  const benutzt = [...new Set(teile.map(t => t.slot))].sort();
  const e = M.kum.elements, mx = [0,1,2].map(r => [0,1,2,3].map(c => +e[c*4+r].toFixed(5)).join(" ")).join(" | ");
  let p = `druckwerk: „${M.name}“ auf der Kobra X slicen.\n`;
  if (M.lager) p += `Modell aus dem Lager: ${M.lager.ordner}\n` + (M.ops.length ? `Änderungen aus der Werkstatt:\n${M.ops.map(o => "- " + o).join("\n")}\nMatrix (auf die Original-STL anwenden): ${mx}\n` : "Ohne Änderung der Form.\n");
  else p += `Modell: hänge ich als 3MF an (Export aus der Werkstatt).\n`;
  p += `Endmaß: ${fnum(s.x)} × ${fnum(s.y)} × ${fnum(s.z)} mm\n`;
  p += benutzt.map(n => `Spule ${n}: ${(M.material && M.material[n-1]) || "PLA"} ${farbName(M.slots[n-1])} – ${teile.filter(t => t.slot === n).map(t => t.name).join(", ")}`).join("\n");
  const d = C.sheet(`<h3>Auftrag für Claude</h3><div class="card" style="margin-bottom:12px"><pre class="prompt">${C.esc(p)}</pre></div>
    ${M.lager ? "" : `<p>Erst als 3MF speichern und im Chat anhängen.</p>`}
    <button class="btn" id="cKop">Kopieren</button><a class="btn grey" target="_blank" href="https://claude.ai/new?q=${encodeURIComponent(p)}">In Claude öffnen</a>`);
  d.querySelector("#cKop").onclick = async () => { try { await navigator.clipboard.writeText(p); C.toast("Kopiert"); } catch (e) { C.toast("Bitte markieren und kopieren"); } };
}

// nur für Tests
export const _test = { export3mf, exportObj, exportGlb, stlBinaer, get M(){ return M; } };
