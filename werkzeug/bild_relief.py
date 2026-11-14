#!/usr/bin/env python3
"""Bild → mehrfarbiges Wandbild-Relief (bis 4 Farben = 4 Köpfe des Creator 5 Pro).

Ablauf: Bild auf Zielbreite skalieren → glätten → auf ≤ 4 Farben reduzieren (feste Palette oder --farben auto)
→ kleine Inseln und zu schmale Stege der Nachbarfarbe zuschlagen → je Farbe Höhenfeld (geglättete Farbmaske)
→ Isolinie bei 0,5 als Umriss (manifold3d CrossSection) → extrudieren. Die Grundplatte (+ Rahmen) hat die
Grundfarbe, die übrigen Farben liegen als erhabene Flächen darauf. Farben werden in 2D nacheinander
voneinander abgezogen → Schnittvolumen exakt 0, alles liegt flach auf dem Bett.

Aufruf (Beispiel):
  python3 werkzeug/bild_relief.py bild.png --name ranke --breite 180 --rahmen 6 --nur-bild /tmp/ranke.png   # erst ansehen
  python3 werkzeug/bild_relief.py bild.png --name ranke --breite 180 --rahmen 6                              # dann Netze
  python3 werkzeug/druck.py --drucker c5pro --name ranke \
    --teil modelle/ranke_schwarz.stl:PLA:1 --teil modelle/ranke_gold.stl:PLA:2 \
    --teil modelle/ranke_rot.stl:PLA:3 --teil modelle/ranke_weiss.stl:PLA:4 \
    --farben "schwarz,gold,rot,weiss" --zusammen --schicht 0.12
  (Das Skript gibt den passenden druck.py-Aufruf mit den tatsächlich vorhandenen Farben selbst aus.)

Parameter:
  --breite  Gesamtbreite in mm inkl. Rahmen (max. 250)       --dicke   Grundplatte in mm (2.0)
  --relief  Höhe über der Platte: eine Zahl = höchste Farbe, die anderen nach Helligkeit gestaffelt (hell = hoch),
            oder je Farbe „gold=0.8,rot=1.2,weiss=1.6“ (1.2)
  --farben  „schwarz,gold,rot,weiss“ (Vorgabe), mit eigenen Werten „schwarz=#202020,gold=#c9a227,…“, oder „auto“
  --anzahl  Farbanzahl bei auto (2–4)          --grund   Farbe der Grundplatte (Vorgabe: dunkelste)
  --rahmen  Rahmenbreite in mm (0 = keiner)    --loecher Aufhängelöcher-Ø in mm (0 = keine, Vorgabe 4.5)
  --min-flaeche  kleinste Insel in mm² (1.0)   --min-breite  schmalster Steg in mm (0.5 ≈ eine 0,4-mm-Bahn)
  --aufloesung   Raster in mm (0.15)           --nur-bild vorschau.png (nur Farbbild, keine Netze)
  --max-dreiecke Obergrenze je Farbe (380000)  --ziel     Ausgabeordner (modelle)
  --kanten  Kantenschutz 0–1 (0.3): Mischtöne an Farbkanten (Säume) der Nachbarfarbe zuschlagen
Ergebnis: modelle/<name>_<farbe>.stl (eine je Farbe, gleiche Koordinaten).
"""
import argparse, itertools, sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

PALETTE = {"schwarz": (28, 28, 30), "gold": (205, 160, 45), "rot": (185, 30, 35), "weiss": (240, 238, 230),
           "gelb": (245, 200, 30), "blau": (40, 90, 220), "gruen": (35, 160, 70), "grau": (140, 140, 145),
           "orange": (245, 115, 25), "braun": (130, 85, 45), "silber": (190, 190, 190), "lila": (140, 90, 240),
           "pink": (235, 70, 150), "tuerkis": (20, 185, 165)}


def hexfarbe(t):
    t = t.strip().lstrip("#"); return tuple(int(t[i:i + 2], 16) for i in (0, 2, 4))


def helligkeit(rgb): return 0.299 * rgb[0] + 0.587 * rgb[1] + 0.114 * rgb[2]


def naechster_name(rgb, schon):
    for n, _ in sorted(PALETTE.items(), key=lambda kv: sum((a - b) ** 2 for a, b in zip(kv[1], rgb))):
        if n not in schon: return n
    return f"farbe{len(schon) + 1}"


def kmeans(px, k, rng, runden=25):
    """Einfaches k-means (k-means++ Start) auf RGB-Pixeln."""
    c = [px[rng.integers(len(px))]]
    for _ in range(k - 1):
        d = np.min(((px[:, None, :] - np.array(c)[None]) ** 2).sum(-1), 1)
        c.append(px[rng.choice(len(px), p=d / d.sum())])
    c = np.array(c, float)
    for _ in range(runden):
        lab = np.argmin(((px[:, None, :] - c[None]) ** 2).sum(-1), 1)
        c = np.array([px[lab == i].mean(0) if np.any(lab == i) else c[i] for i in range(k)])
    return c


def palette_lesen(a, bild):
    if a.farben.strip().lower() == "auto":
        rng = np.random.default_rng(1); px = bild.reshape(-1, 3).astype(float)
        px = px[rng.choice(len(px), min(len(px), 40000), replace=False)]
        zentren = kmeans(px, max(2, min(4, a.anzahl)), rng); namen = []
        for z in zentren: namen.append(naechster_name(z, namen))
        return {n: tuple(int(v) for v in z) for n, z in zip(namen, zentren)}
    pal = {}
    for teil in a.farben.split(","):
        n, _, w = teil.strip().partition("=")
        n = n.strip().lower().replace("ß", "ss").replace("ü", "ue")
        pal[n] = hexfarbe(w) if w else PALETTE[n]
    if not 1 <= len(pal) <= 4: sys.exit("Es gehen 1 bis 4 Farben (4 Köpfe).")
    return pal


def aufraeumen(lab, k, min_px, r_px):
    """Zu kleine Inseln und zu schmale Stege entfernen; die Lücke füllt die nächstgelegene Farbe."""
    for _ in range(3):
        frei = np.zeros(lab.shape, bool)
        for i in range(k):
            m = lab == i
            if r_px >= 1:                                                     # Öffnen: Stege < min-breite weg
                st = np.hypot(*np.mgrid[-r_px:r_px + 1, -r_px:r_px + 1]) <= r_px
                m2 = ndimage.binary_opening(m, st); frei |= m & ~m2; m = m2
            teile, n = ndimage.label(m)
            if n:
                gr = ndimage.sum(np.ones_like(teile), teile, np.arange(1, n + 1))
                frei |= np.isin(teile, np.nonzero(gr < min_px)[0] + 1)
        if not frei.any(): break
        _, (ii, jj) = ndimage.distance_transform_edt(frei, return_indices=True)
        lab = lab[ii, jj]
    return lab


def umriss(maske, res, h_mm, max_dreiecke=380000):
    """Höhenfeld (geglättete Maske) → Isolinie 0,5 → CrossSection in mm (y nach oben)."""
    import manifold3d as m3
    from skimage import measure
    s = np.pad(ndimage.gaussian_filter(maske.astype(np.float32), 1.0), 1)
    polys = []
    for c in measure.find_contours(s, 0.5):
        if len(c) < 4: continue
        xy = np.stack([(c[:, 1] - 1 + 0.5) * res, h_mm - (c[:, 0] - 1 + 0.5) * res], 1)
        polys.append(xy[:-1] if np.allclose(xy[0], xy[-1]) else xy)
    if not polys: return m3.CrossSection()
    cs, eps = m3.CrossSection(polys, m3.FillRule.EvenOdd).simplify(0.01), 0.01
    while 4.2 * cs.num_vert() > max_dreiecke and eps < 0.2:     # Dreieckszahl begrenzen (≈ 4 je Umrisspunkt)
        eps *= 1.6; cs = cs.simplify(eps)
    return cs


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("bild"); ap.add_argument("--name", default="bild"); ap.add_argument("--breite", type=float, default=150)
    ap.add_argument("--dicke", type=float, default=2.0); ap.add_argument("--relief", default="1.2")
    ap.add_argument("--farben", default="schwarz,gold,rot,weiss"); ap.add_argument("--anzahl", type=int, default=4)
    ap.add_argument("--grund"); ap.add_argument("--rahmen", type=float, default=0.0); ap.add_argument("--loecher", type=float, default=4.5)
    ap.add_argument("--min-flaeche", type=float, default=1.0); ap.add_argument("--min-breite", type=float, default=0.5)
    ap.add_argument("--kanten", type=float, default=0.3, help="Kantenschutz 0–1 (0 = aus): Mischtöne an Kanten der Nachbarfarbe geben")
    ap.add_argument("--glaetten", type=float, default=0.3, help="Bild-Glättung (Sigma in mm)")
    ap.add_argument("--aufloesung", type=float, default=0.15); ap.add_argument("--nur-bild"); ap.add_argument("--ziel", default="modelle")
    ap.add_argument("--max-dreiecke", type=int, default=380000, help="Obergrenze Dreiecke je Farbe")
    a = ap.parse_args()
    if not 10 <= a.breite <= 250: sys.exit("--breite muss zwischen 10 und 250 mm liegen (Bauraum 256 mm).")
    res = a.aufloesung; R = a.rahmen
    # ---- Bild laden und auf Rastergröße bringen (Innenfläche ohne Rahmen) ----
    img = Image.open(a.bild)
    if img.mode in ("RGBA", "LA", "P"):
        img = img.convert("RGBA"); hg = Image.new("RGBA", img.size, (255, 255, 255, 255)); img = Image.alpha_composite(hg, img)
    img = img.convert("RGB"); innen_b = a.breite - 2 * R
    nx = int(round(innen_b / res)); res = innen_b / nx                     # Raster so, dass die Breite exakt stimmt
    ny = int(round(nx * img.height / img.width)); innen_h = ny * res
    if innen_h + 2 * R > 250.001: sys.exit(f"Bild wäre {innen_h + 2 * R:.0f} mm hoch – max. 250 mm, --breite verkleinern.")
    bild = np.asarray(img.resize((nx, ny), Image.LANCZOS), np.float32)
    bild = ndimage.gaussian_filter(bild, (a.glaetten / res, a.glaetten / res, 0))
    # ---- Farben ----
    pal = palette_lesen(a, bild); namen = list(pal); farbw = np.array([pal[n] for n in namen], np.float32)
    w = np.array([0.30, 0.59, 0.11]) ** 0.5                                       # Helligkeits-gewichtete Distanz
    lab = np.argmin((((bild[:, :, None, :] - farbw[None, None]) * w) ** 2).sum(-1), 2)
    if a.kanten > 0:                                       # Mischtöne an Kanten (z. B. Goldsaum um Weiß auf Schwarz) vermeiden:
        g = np.sqrt(sum(ndimage.gaussian_gradient_magnitude(bild[:, :, c], 1.0) ** 2 for c in range(3)))
        unsicher = g > np.maximum(8.0, a.kanten * ndimage.maximum_filter(g, 7))   # steile Übergangszone
        if unsicher.any() and not unsicher.all():                # → Farbe vom nächsten ruhigen Pixel übernehmen
            _, (ii, jj) = ndimage.distance_transform_edt(unsicher, return_indices=True); lab = lab[ii, jj]
    lab = aufraeumen(lab, len(namen), a.min_flaeche / res ** 2, max(0, int(round((a.min_breite / res - 1) / 2))))
    vorhanden = [i for i in range(len(namen)) if np.any(lab == i)]
    grund = namen.index(a.grund) if a.grund else min(range(len(namen)), key=lambda i: helligkeit(pal[namen[i]]))
    if grund not in vorhanden: vorhanden.append(grund)
    oben = sorted([i for i in vorhanden if i != grund], key=lambda i: helligkeit(pal[namen[i]]))
    # Höhen: eine Zahl = höchste Stufe, gestaffelt nach Helligkeit; sonst je Farbe
    if "=" in a.relief:
        hoehe = {namen.index(n.strip()): float(v) for n, v in (t.split("=") for t in a.relief.split(","))}
    else:
        hm = float(a.relief); hoehe = {i: hm * (k + 1) / len(oben) for k, i in enumerate(oben)} if oben else {}
    gesamt_b, gesamt_h = innen_b + 2 * R, innen_h + 2 * R
    anteil = ", ".join(f"{namen[i]} {np.mean(lab == i) * 100:.0f} %" for i in vorhanden)
    print(f"Bild {nx}×{ny} Raster ({res} mm) → {gesamt_b:.1f} × {gesamt_h:.1f} mm, Grund: {namen[grund]}, Anteile: {anteil}")
    print("Höhen über der Platte: " + ", ".join(f"{namen[i]} {hoehe[i]:.2f} mm" for i in oben))
    # Aufhängelöcher (oben, 15 % vom Rand; im Rahmen, wenn er breit genug ist)
    lochpos = []
    if a.loecher > 0:
        ly = gesamt_h - (R / 2 if R >= a.loecher + 3 else max(R, 0) + a.loecher / 2 + 2.5)
        lochpos = [(gesamt_b * 0.15, ly), (gesamt_b * 0.85, ly)]

    if a.nur_bild:
        rgb = np.array([pal[n] for n in namen], np.uint8)[lab]
        rp = int(round(R / res)); out = np.zeros((ny + 2 * rp, nx + 2 * rp, 3), np.uint8); out[:] = pal[namen[grund]]
        out[rp:rp + ny, rp:rp + nx] = rgb
        yy, xx = np.mgrid[0:out.shape[0], 0:out.shape[1]]
        for (lx, ly) in lochpos:
            out[np.hypot(xx * res - lx, (out.shape[0] - yy) * res - ly) < a.loecher / 2] = (255, 255, 255)
        bild_out = Image.fromarray(out)
        if bild_out.width > 1600: bild_out = bild_out.resize((1600, int(1600 * bild_out.height / bild_out.width)), Image.LANCZOS)
        bild_out.save(a.nur_bild); print(f"Vorschau: {a.nur_bild}"); return

    # ================= Netze =================
    import manifold3d as m3, trimesh
    CS = m3.CrossSection
    innen = CS.square((innen_b, innen_h)).translate((R, R))
    loch2d = CS.batch_boolean([CS.circle(a.loecher / 2, 48).translate(p) for p in lochpos], m3.OpType.Add) if lochpos else CS()
    schutz = CS.batch_boolean([CS.circle(a.loecher / 2 + 1.5, 48).translate(p) for p in lochpos], m3.OpType.Add) if lochpos else CS()
    belegt = schutz; koerper = {}
    for i in reversed(oben):                                   # hohe (helle) Farben zuerst, die anderen weichen aus
        r = a.min_breite / 2 * 0.6                             # 2D-Öffnen: Reststege nach dem Glätten entfernen
        f = umriss(lab == i, res, innen_h, a.max_dreiecke).translate((R, R)).offset(-r, m3.JoinType.Round).offset(r, m3.JoinType.Round)
        f = (f ^ innen) - belegt.offset(0.02, m3.JoinType.Miter)   # 0,02 mm Fuge: keine gemeinsamen Kanten → sauber dicht
        belegt = belegt + f
        if not f.is_empty(): koerper[namen[i]] = f.extrude(hoehe[i]).translate((0, 0, a.dicke))
    platte = (CS.square((gesamt_b, gesamt_h)) - loch2d).extrude(a.dicke)
    if R > 0:
        hr = max(hoehe.values()) if hoehe else 0.0
        platte = platte + (CS.square((gesamt_b, gesamt_h)) - innen - loch2d).extrude(hr).translate((0, 0, a.dicke))
    koerper = {namen[grund]: platte, **{namen[i]: koerper[namen[i]] for i in range(len(namen)) if namen[i] in koerper}}
    # ---- Ausgabe + Prüfung ----
    ziel = Path(a.ziel); ziel.mkdir(parents=True, exist_ok=True); dateien = []
    for n, k in koerper.items():
        me = k.to_mesh(); t = trimesh.Trimesh(me.vert_properties[:, :3], me.tri_verts, process=True)
        p = ziel / f"{a.name}_{n}.stl"; t.export(p); dateien.append((n, p))
        if not t.is_watertight: print(f"WARNUNG: {p.name} nicht dicht – --aufloesung oder --min-breite erhöhen")
        print(f"{p}: dicht={t.is_watertight}, {t.volume / 1000:.2f} cm³, {len(t.faces)} Dreiecke, Teile {len(k.decompose())}, "
              f"Maße {np.round(t.extents, 2).tolist()}")
    for (n1, k1), (n2, k2) in itertools.combinations(koerper.items(), 2):
        print(f"Schnittvolumen {n1} ∩ {n2}: {(k1 ^ k2).volume():.4f} mm³")
    teile = " ".join(f"--teil {p}:PLA:{s + 1}" for s, (n, p) in enumerate(dateien))
    print(f"\nSlicen:\npython3 werkzeug/druck.py --drucker c5pro --name {a.name} {teile} "
          f"--farben \"{','.join(n for n, _ in dateien)}\" --zusammen --schicht 0.12")


if __name__ == "__main__":
    main()
