#!/usr/bin/env python3
"""Textur/Vertexfarben → höchstens 4 Filamentfarben (4 Köpfe des Creator 5 Pro).

Eingang: <name>_farbig.glb aus ki_rohling.py (wasserdicht, mm, Z oben) – oder eine andere farbige GLB/OBJ.
Ablauf: Netz gleichmäßig neu vernetzen (--kante) → Farbe je Dreieck aus dem Original → auf die Palette
reduzieren (feste Farben oder --auto N per k-Means im Lab-Raum) → Farbgrenzen glätten, zu kleine Inseln und
zu schmale Stege der Nachbarfarbe geben → Ausgabe auf zwei Wegen:

  (A) <name>_bemalt.3mf  – EIN Körper, Farbe je Dreieck als paint_color (wie in OrcaSlicer gemalt).
      Slicen:  druck.py --drucker c5pro --name <n> --bemalt <name>_bemalt.3mf --farben "…"
  (B) <name>_<k>_<farbe>.stl – je Farbe ein Körper: Oberflächenschale der Farbe (--tiefe mm) per Boolean
      aus dem Grundkörper; der Kern hat die häufigste Farbe. Schnittvolumen paarweise 0.
      Slicen:  druck.py … --teil a.stl:PLA:1 --teil b.stl:PLA:2 … --zusammen

Aufruf:
  python3 werkzeug/textur_farben.py /tmp/fig/fig_farbig.glb --farben "schwarz,gold,rot,weiss" --nur-bild /tmp/v.png
  python3 werkzeug/textur_farben.py /tmp/fig/fig_farbig.glb --farben "schwarz,gold=#d4a017,rot,weiss" --aus /tmp/fig
  python3 werkzeug/textur_farben.py /tmp/fig/fig_farbig.glb --auto 3 --aus /tmp/fig --weg A

Ergebnis (Ordner --aus): Dateien oben, farben.png (Vorschau), farben.json (Zuordnung, Anteile, Aufrufe).
"""
import argparse, itertools, json, sys, time, zipfile
from pathlib import Path

import numpy as np
import trimesh
from scipy import ndimage, sparse
from scipy.spatial import cKDTree

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ki_rohling as kr  # noqa: E402

PALETTE = {"schwarz": (28, 28, 30), "gold": (205, 160, 45), "rot": (185, 30, 35), "weiss": (240, 238, 230),
           "gelb": (245, 200, 30), "blau": (40, 90, 220), "gruen": (35, 160, 70), "grau": (140, 140, 145),
           "orange": (245, 115, 25), "braun": (130, 85, 45), "silber": (190, 190, 190), "lila": (140, 90, 240),
           "pink": (235, 70, 150), "tuerkis": (20, 185, 165), "creme": (240, 230, 200), "haut": (230, 180, 150)}
# Orca/Bambu: ungeteiltes Dreieck in Kopf k (Model.cpp, CONST_FILAMENTS)
PAINT = {1: "4", 2: "8", 3: "0C", 4: "1C"}


def norm_name(n):
    return n.strip().lower().replace("ß", "ss").replace("ä", "ae").replace("ö", "oe").replace("ü", "ue")


def lab(rgb):
    from skimage.color import rgb2lab
    return rgb2lab(np.clip(np.asarray(rgb, float) / 255.0, 0, 1)[None])[0]


def palette_lesen(text):
    pal = {}
    for teil in text.split(","):
        n, _, w = teil.partition("=")
        n = norm_name(n)
        if w:
            w = w.strip().lstrip("#"); pal[n] = tuple(int(w[i:i + 2], 16) for i in (0, 2, 4))
        elif n in PALETTE:
            pal[n] = PALETTE[n]
        else:
            sys.exit(f"Farbe '{n}' unbekannt – mit Wert angeben, z. B. {n}=#a0b0c0. Bekannt: {', '.join(PALETTE)}")
    if not 1 <= len(pal) <= 4:
        sys.exit("1 bis 4 Farben (4 Köpfe).")
    return pal


def kmeans_lab(X, w, k, rng, runden=30):
    c = [X[rng.choice(len(X), p=w / w.sum())]]
    for _ in range(k - 1):
        d = np.min(((X[:, None] - np.array(c)[None]) ** 2).sum(-1), 1) * w
        c.append(X[rng.choice(len(X), p=d / d.sum())])
    c = np.array(c)
    for _ in range(runden):
        l_ = np.argmin(((X[:, None] - c[None]) ** 2).sum(-1), 1)
        c = np.array([np.average(X[l_ == i], 0, w[l_ == i]) if np.any(l_ == i) else c[i] for i in range(k)])
    return c


# ---------------- Bereinigung auf dem Dreiecksgraphen ----------------
def nachbarn(m):
    """(F,3) Kantennachbarn je Dreieck (−1 = keiner) und dünnbesetzte Matrix der Eckpunkt-Nachbarschaft."""
    F = len(m.faces); nb = -np.ones((F, 3), int); cnt = np.zeros(F, int)
    for a, b in m.face_adjacency:
        if cnt[a] < 3: nb[a, cnt[a]] = b; cnt[a] += 1
        if cnt[b] < 3: nb[b, cnt[b]] = a; cnt[b] += 1
    vf = sparse.csr_matrix((np.ones(F * 3), (np.repeat(np.arange(F), 3), m.faces.ravel())), shape=(F, len(m.vertices)))
    ring = (vf @ vf.T).tocsr(); ring.data[:] = 1
    return nb, ring


def mehrheit(lab_, nb, runden):
    """Kanten-Mehrheit: hat ein Dreieck ≥ 2 von 3 Nachbarn in einer anderen Farbe, übernimmt es diese."""
    for _ in range(runden):
        L = np.where(nb >= 0, lab_[np.maximum(nb, 0)], -1)
        neu = lab_.copy()
        for j in range(3):
            a, b = L[:, j], L[:, (j + 1) % 3]
            neu = np.where((a == b) & (a >= 0) & (a != lab_), a, neu)
        if np.array_equal(neu, lab_):
            break
        lab_ = neu
    return lab_


def auffuellen(lab_, frei, ring, k):
    """Freie Dreiecke (−1) bekommen die häufigste Farbe ihrer Nachbarschaft (wachsend von außen)."""
    lab_ = lab_.copy(); lab_[frei] = -1
    for _ in range(500):
        offen = lab_ < 0
        if not offen.any():
            break
        H = np.stack([ring @ (lab_ == i).astype(np.float32) for i in range(k)], 1)
        neu = offen & (H.max(1) > 0)
        if not neu.any():
            lab_[offen] = 0; break
        lab_[neu] = H[neu].argmax(1)
    return lab_


def inseln(m, lab_, nb, ring, k, min_flaeche):
    """Zusammenhängende Farbflächen kleiner min_flaeche (mm²) der Nachbarfarbe geben."""
    flaechen = m.area_faces
    for _ in range(6):
        a_, b_ = m.face_adjacency.T
        gleich = lab_[a_] == lab_[b_]
        G = sparse.coo_matrix((np.ones(gleich.sum()), (a_[gleich], b_[gleich])), shape=(len(lab_),) * 2)
        n, comp = sparse.csgraph.connected_components(G, directed=False)
        groesse = np.bincount(comp, flaechen, n)
        klein = groesse[comp] < min_flaeche
        if not klein.any():
            break
        lab_ = auffuellen(lab_, klein, ring, k)
    return lab_


def oeffnen(lab_, ring, k, schritte, reihenfolge):
    """Stege schmaler als ~2·schritte Dreiecksringe entfernen (Erosion + Dilatation je Farbe)."""
    if schritte < 1:
        return lab_
    frei = np.zeros(len(lab_), bool)
    for i in reihenfolge:
        mk = lab_ == i
        e = mk.copy()
        for _ in range(schritte):
            e = e & ((ring @ (~e).astype(np.float32)) == 0)
        d = e.copy()
        for _ in range(schritte):
            d = d | ((ring @ d.astype(np.float32)) > 0)
        frei |= mk & ~d
    return auffuellen(lab_, frei, ring, k)


# ---------------- (A) 3MF mit paint_color ----------------
def schreibe_3mf(pfad, V, F, slots, name):
    pc = np.array([PAINT[int(s)] for s in range(1, 5)])
    vz = "".join(f'<vertex x="{x:.4f}" y="{y:.4f}" z="{z:.4f}"/>' for x, y, z in V)
    tz = "".join(f'<triangle v1="{a}" v2="{b}" v3="{c}" paint_color="{p}"/>'
                 for (a, b, c), p in zip(F, pc[np.asarray(slots) - 1]))
    model = ('<?xml version="1.0" encoding="UTF-8"?>\n<model unit="millimeter" xml:lang="en-US" '
             'xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02">\n'
             '<metadata name="Application">druckwerk textur_farben</metadata>\n'
             f'<resources><object id="1" name="{name}" type="model"><mesh><vertices>{vz}</vertices>'
             f'<triangles>{tz}</triangles></mesh></object></resources>\n'
             '<build><item objectid="1" printable="1"/></build>\n</model>\n')
    cfg = ('<?xml version="1.0" encoding="UTF-8"?>\n<config>\n<object id="1">\n'
           f'<metadata key="name" value="{name}"/>\n<metadata key="extruder" value="1"/>\n'
           f'<part id="1" subtype="normal_part">\n<metadata key="name" value="{name}"/>\n'
           '<metadata key="extruder" value="1"/>\n</part>\n</object>\n</config>\n')
    ct = ('<?xml version="1.0" encoding="UTF-8"?>\n<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
          '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
          '<Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/></Types>\n')
    rels = ('<?xml version="1.0" encoding="UTF-8"?>\n<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Target="/3D/3dmodel.model" Id="rel0" '
            'Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>\n')
    with zipfile.ZipFile(pfad, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", ct); z.writestr("_rels/.rels", rels)
        z.writestr("3D/3dmodel.model", model); z.writestr("Metadata/model_settings.config", cfg)


def lese_3mf(pfad):
    """Gegenstück (für druck.py): Eckpunkte, Dreiecke, Kopf je Dreieck (0 = Grundfarbe)."""
    import re
    with zipfile.ZipFile(pfad) as z:
        name = next(n for n in z.namelist() if n.lower().endswith(".model") and n.startswith("3D/"))
        x = z.read(name).decode("utf-8")
    V = np.array(re.findall(r'<vertex x="([^"]+)" y="([^"]+)" z="([^"]+)"', x), float)
    T = re.findall(r'<triangle v1="(\d+)" v2="(\d+)" v3="(\d+)"(?: paint_color="([0-9A-F]*)")?', x)
    F = np.array([t[:3] for t in T], int)
    rueck = {v: k for k, v in PAINT.items()}
    S = np.array([rueck.get(t[3], 0) for t in T], int)
    return V, F, S


# ---------------- (B) Farbkörper ----------------
def farbkoerper(m, lab_, basis, tiefe, voxel, log):
    import manifold3d as mf
    M = kr.zu_manifold(m)
    if M.status() != mf.Error.NoError:
        raise RuntimeError(f"Grundkörper nicht wasserdicht ({M.status()}) – erst ki_rohling.py")
    koerper, org, _ = kr.voxel_fuellen([m], voxel, schliessen=1, rand=4)
    innen_t = ndimage.distance_transform_edt(koerper) * voxel
    aussen_t = ndimage.distance_transform_edt(~koerper) * voxel
    band = (koerper & (innen_t <= tiefe + voxel)) | (~koerper & (aussen_t <= 2.5 * voxel))
    idx = np.argwhere(band)
    _, nf = cKDTree(m.triangles_center).query(org + (idx + 0.5) * voxel, workers=-1)
    L = np.full(koerper.shape, -1, np.int16); L[tuple(idx.T)] = lab_[nf]
    teile = {}; belegt = mf.Manifold()
    farben = [i for i in np.unique(lab_) if i != basis]
    for i in farben:
        mk = L == i
        mk = ndimage.binary_dilation(mk, iterations=1) & band          # 1 Voxel Überlapp, wird unten aufgelöst
        R = kr.zu_manifold(kr.netz_aus_voxeln(mk, org, voxel, sigma=0.6))
        if R.status() != mf.Error.NoError:
            raise RuntimeError(f"Farbbereich {i} nicht sauber vernetzt ({R.status()})")
        stueck = (M ^ R) - belegt
        stueck = mf.Manifold.compose([k for k in stueck.decompose() if k.volume() > 0.3])    # Splitter → Kern
        teile[i] = stueck; belegt = belegt + stueck
        log(f"  Farbkörper {i}: {stueck.volume():.0f} mm³")
    kern = (M - belegt).decompose()
    weg = sum(k.volume() for k in kern if k.volume() <= 0.05)
    teile[basis] = mf.Manifold.compose([k for k in kern if k.volume() > 0.05])        # Schnitt-Splitter im Kern weg
    log(f"  Kern: {teile[basis].volume():.0f} mm³ (Splitter verworfen: {weg:.2f} mm³)")
    return M, teile


# ---------------- Hauptablauf ----------------
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("eingabe")
    ap.add_argument("--farben", default="schwarz,gold,rot,weiss",
                    help="Palette in Slot-Reihenfolge, Werte anpassbar: 'schwarz,gold=#d4a017,rot,weiss'")
    ap.add_argument("--auto", type=int, default=0, help="statt fester Palette: N Farben (2–4) automatisch finden")
    ap.add_argument("--aus", default=None, help="Ausgabeordner (Standard: Ordner der Eingabe)")
    ap.add_argument("--name", default=None)
    ap.add_argument("--nur-bild", default=None, help="nur die Farbvorschau rechnen und als PNG speichern")
    ap.add_argument("--weg", choices=["A", "B", "beide"], default="beide")
    ap.add_argument("--kante", type=float, default=0.4, help="Kantenlänge beim Neuvernetzen in mm (Farbgenauigkeit)")
    ap.add_argument("--min-flaeche", type=float, default=1.0, help="kleinste Farbinsel in mm²")
    ap.add_argument("--min-breite", type=float, default=0.8, help="schmalster Farbsteg in mm")
    ap.add_argument("--glaetten", type=int, default=3, help="Runden Kanten-Glättung der Farbgrenzen")
    ap.add_argument("--hell", type=float, default=1.0, help="Gewicht der Helligkeit beim Farbvergleich (<1: Schatten zählen weniger)")
    ap.add_argument("--tiefe", type=float, default=1.2, help="(B) Tiefe der Farbschale in mm")
    ap.add_argument("--kern", default=None, help="(B) Farbe des Kerns (Standard: häufigste)")
    ap.add_argument("--voxel", type=float, default=None, help="(B) Voxelgröße in mm (Standard tiefe/6, 0,12–0,25)")
    a = ap.parse_args()
    t0 = time.time(); log = lambda *x: print(f"[{time.time() - t0:5.1f}s]", *x, flush=True)
    eing = Path(a.eingabe)
    name = a.name or eing.stem.replace("_farbig", "")
    ziel = Path(a.aus) if a.aus else eing.parent
    ziel.mkdir(parents=True, exist_ok=True)

    teile = kr.lade_teile(eing)
    if not any(kr.hat_farbe(t) for t in teile):
        sys.exit("Eingabe hat keine Farbe (Textur/Vertexfarben). Erst ki_rohling.py auf die farbige GLB anwenden.")
    geo = trimesh.util.concatenate([trimesh.Trimesh(t.vertices, t.faces, process=False) for t in teile])
    geo.merge_vertices(digits_vertex=5)
    if not geo.is_watertight:
        print("  ⚠ Netz nicht wasserdicht – Weg B braucht ki_rohling.py vorher.")
    quelle = kr.FarbQuelle(teile, abstand=0.05)

    # ---- Neu vernetzen (gleichmäßige Dreiecke → saubere Farbkanten) ----
    import pymeshlab
    ms = pymeshlab.MeshSet(); ms.add_mesh(pymeshlab.Mesh(geo.vertices, geo.faces))
    ms.meshing_isotropic_explicit_remeshing(targetlen=pymeshlab.PureValue(a.kante), iterations=4,
                                            featuredeg=60, maxsurfdist=pymeshlab.PureValue(a.kante * 0.1))
    mm_ = ms.current_mesh()
    m = trimesh.Trimesh(mm_.vertex_matrix(), mm_.face_matrix(), process=True)
    if geo.is_watertight and not m.is_watertight:
        trimesh.repair.fill_holes(m)
    log(f"neu vernetzt: {len(m.faces)} Dreiecke (Kante {a.kante} mm), dicht {m.is_watertight}")

    # ---- Farbe je Dreieck ----
    cz, _ = quelle.farbe(m.triangles_center, k=4)
    cv, _ = quelle.farbe(m.vertices, k=4)
    rgb = 0.5 * cz + 0.5 * cv[m.faces].mean(1)
    L = lab(rgb); L[:, 0] *= a.hell
    w = m.area_faces
    if a.auto:
        k = int(np.clip(a.auto, 2, 4))
        zentren = kmeans_lab(L, w, k, np.random.default_rng(1))
        from skimage.color import lab2rgb
        z_rgb = [tuple(int(v) for v in np.clip(lab2rgb((z * [1 / a.hell, 1, 1])[None])[0] * 255, 0, 255)) for z in zentren]
        pal = {}
        for zr in sorted(z_rgb, key=lambda c: sum(c)):                  # dunkel → hell = Slot 1 …
            frei = [n for n in PALETTE if n not in pal]
            n = min(frei, key=lambda n_: np.sum(((lab(PALETTE[n_]) - lab(zr)) * [0.4, 1, 1]) ** 2))   # Name nach Farbton
            pal[n] = zr
    else:
        pal = palette_lesen(a.farben)
    namen = list(pal)
    P = np.array([lab(pal[n]) for n in namen]); P[:, 0] *= a.hell
    lab_ = np.argmin(((L[:, None] - P[None]) ** 2).sum(-1), 1)
    k = len(namen)

    # ---- Bereinigen ----
    nb, ring = nachbarn(m)
    lab_ = mehrheit(lab_, nb, a.glaetten)
    anteil = np.bincount(lab_, w, k)
    reihenfolge = list(np.argsort(anteil))                           # kleine Farben zuerst öffnen
    lab_ = oeffnen(lab_, ring, k, int(round(a.min_breite / 2 / (a.kante * 0.87))), reihenfolge)
    lab_ = inseln(m, lab_, nb, ring, k, a.min_flaeche)
    lab_ = mehrheit(lab_, nb, a.glaetten)
    lab_ = inseln(m, lab_, nb, ring, k, a.min_flaeche)
    anteil = np.bincount(lab_, w, k) / w.sum()
    genutzt = [i for i in range(k) if anteil[i] > 0]
    slot_von = {i: s + 1 for s, i in enumerate(genutzt)}             # Slots fortlaufend in Palettenreihenfolge
    log("Farben: " + ", ".join(f"Kopf {slot_von[i]} {namen[i]} {anteil[i] * 100:.1f} %" for i in genutzt)
        + ("" if len(genutzt) == k else f"  (nicht genutzt: {', '.join(namen[i] for i in range(k) if i not in genutzt)})"))
    FC = np.array([pal[namen[i]] for i in lab_], float)
    bildpfad = Path(a.nur_bild) if a.nur_bild else ziel / "farben.png"
    kr.bild(m.vertices, m.faces, FC, bildpfad,
            titel=f"{name}: " + " · ".join(f"{slot_von[i]} {namen[i]} {anteil[i] * 100:.0f}%" for i in genutzt))
    log(f"Bild: {bildpfad}")
    if a.nur_bild:
        return

    farben_txt = ",".join(namen[i] for i in genutzt)
    info = {"name": name, "eingabe": eing.name, "dreiecke": int(len(m.faces)), "kante_mm": a.kante,
            "farben": [{"slot": slot_von[i], "farbe": namen[i], "rgb": list(pal[namen[i]]),
                        "anteil": round(float(anteil[i]), 4)} for i in genutzt], "aufrufe": {}}
    slots = np.array([slot_von[i] for i in lab_])
    if a.weg in ("A", "beide"):
        p3 = ziel / f"{name}_bemalt.3mf"
        schreibe_3mf(p3, m.vertices, m.faces, slots, name)
        info["bemalt"] = p3.name
        info["aufrufe"]["A"] = (f"python3 werkzeug/druck.py --drucker c5pro --name {name} --bemalt {p3} "
                                f"--farben \"{farben_txt}\" --schicht 0.12 --stuetzen auto")
        log(f"(A) {p3.name}: {p3.stat().st_size / 1e6:.1f} MB")
    if a.weg in ("B", "beide"):
        basis = genutzt[int(np.argmax([anteil[i] for i in genutzt]))]
        if a.kern:
            basis = namen.index(norm_name(a.kern))
        voxel = a.voxel or float(np.clip(a.tiefe / 6, 0.12, 0.25))
        if not m.is_watertight:
            log("(B) übersprungen: Netz nicht wasserdicht")
        else:
            try:
                M, koerper = farbkoerper(m, lab_, basis, a.tiefe, voxel, log)
                dateien = []
                for i in genutzt:
                    if i not in koerper or koerper[i].is_empty():
                        continue
                    t = kr.aus_manifold(koerper[i])
                    p = ziel / f"{name}_{slot_von[i]}_{namen[i]}.stl"; t.export(p)
                    dateien.append((slot_von[i], p, koerper[i]))
                    log(f"(B) {p.name}: {koerper[i].volume() / 1000:.2f} cm³, {len(t.faces)} Dreiecke, dicht {t.is_watertight}")
                schnitt = max([(x[2] ^ y[2]).volume() for x, y in itertools.combinations(dateien, 2)] or [0.0])
                summe = sum(x[2].volume() for x in dateien)
                log(f"(B) Schnittvolumen paarweise max. {schnitt:.4f} mm³, Summe {summe:.1f} / Körper {M.volume():.1f} mm³")
                if schnitt > 0.01:
                    log("(B) ⚠ Farbkörper überschneiden sich – Ergebnis prüfen")
                info["koerper"] = [{"slot": s, "datei": p.name} for s, p, _ in dateien]
                info["schnitt_max_mm3"] = round(float(schnitt), 4)
                teile_txt = " ".join(f"--teil {p}:PLA:{s}" for s, p, _ in dateien)
                info["aufrufe"]["B"] = (f"python3 werkzeug/druck.py --drucker c5pro --name {name} {teile_txt} "
                                        f"--farben \"{farben_txt}\" --zusammen --schicht 0.12 --stuetzen auto")
            except RuntimeError as e:
                log(f"(B) nicht möglich: {e}")
    (ziel / "farben.json").write_text(json.dumps(info, ensure_ascii=False, indent=1), encoding="utf-8")
    for k_, v in info["aufrufe"].items():
        print(f"\nSlicen ({k_}):\n{v}")


if __name__ == "__main__":
    main()
