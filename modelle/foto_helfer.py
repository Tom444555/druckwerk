#!/usr/bin/env python3
"""Foto-Helfer zum Vermessen und Scannen – 20.11.2026, nur gerechnet.

  Messmatte   – Platte 250 × 180 × 3 mm, weiß mit schwarzer Einlage: vier ArUco-Marker (4x4, IDs 0–3, 30 mm),
                Messstriche am Rand (1/5/10 mm). Teil auf das weiße Feld legen, von oben fotografieren →
                werkzeug/messmatte.py zieht den Umriss in echten mm heraus. Lage der Marker: messmatte.json.
  Makroschlitten – Schiene 190 × 70 mit Schwalbenschwanz, Schlitten 70 × 70 mit Kameraschraube 1/4",
                Spindel M6 (1 mm je Umdrehung), Drehknopf mit 10 Strichen (= 0,1 mm), Stativmutter 1/4" unten.
                Kaufteile: M6-Gewindestange 220 mm, 4 Muttern M6, 1 Mutter 1/4"-20, 1 Stativschraube 1/4" mit Ring.

Aufruf: python3 modelle/foto_helfer.py --ziel /tmp/fh [--bild /tmp/fh/v.png]
"""
import argparse, json, math, os
import numpy as np
import manifold3d as m3
import trimesh
import cv2

# ---------------- Messmatte ----------------
MM_L, MM_B, MM_T = 250.0, 180.0, 3.0
MARKER = 30.0                 # Kantenlänge (6 × 5 mm Zellen inkl. schwarzem Rand)
RAND = 6.0                    # Abstand Marker – Plattenkante
EINLAGE = 0.6


def marker_mitten():
    x0, x1 = RAND + MARKER / 2, MM_L - RAND - MARKER / 2
    y0, y1 = RAND + MARKER / 2, MM_B - RAND - MARKER / 2
    return {0: (x0, y1), 1: (x1, y1), 2: (x1, y0), 3: (x0, y0)}   # 0 oben links, im Uhrzeigersinn


def aruco_2d(idx, mitte):
    d = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
    bild = cv2.aruco.generateImageMarker(d, idx, 6, borderBits=1)   # 6 × 6 Zellen, 0 = schwarz
    z = MARKER / 6
    cx, cy = mitte
    teile = []
    for r in range(6):
        for c in range(6):
            if bild[r, c] == 0:
                x = cx - MARKER / 2 + c * z
                y = cy + MARKER / 2 - (r + 1) * z
                teile.append(m3.CrossSection.square([z + 0.01, z + 0.01]).translate([x, y]))
    return m3.CrossSection.batch_boolean(teile, m3.OpType.Add)


def striche_2d():
    """Messstriche an allen vier Kanten zwischen den Markern: 1 mm kurz, 5 mm mittel, 10 mm lang."""
    teile, b = [], 0.5
    def strich(x, y, l, waagrecht):
        return m3.CrossSection.square([b, l] if not waagrecht else [l, b]).translate([x - (b / 2 if not waagrecht else 0), y - (0 if not waagrecht else b / 2)])
    x_a, x_e = RAND + MARKER + 6, MM_L - RAND - MARKER - 6
    for i in range(int(x_e - x_a) + 1):
        x = x_a + i
        l = 6.0 if i % 10 == 0 else (4.0 if i % 5 == 0 else 2.5)
        teile.append(strich(x, 2.0, l, False))
        teile.append(strich(x, MM_B - 2.0 - l, l, False))
    y_a, y_e = RAND + MARKER + 6, MM_B - RAND - MARKER - 6
    for i in range(int(y_e - y_a) + 1):
        y = y_a + i
        l = 6.0 if i % 10 == 0 else (4.0 if i % 5 == 0 else 2.5)
        teile.append(strich(2.0, y, l, True))
        teile.append(strich(MM_L - 2.0 - l, y, l, True))
    return m3.CrossSection.batch_boolean(teile, m3.OpType.Add)


def messmatte():
    """(weiß, schwarz) in Druckglage: Oberseite nach unten, Bett-Koordinaten."""
    k = m3.Manifold.cube([MM_L, MM_B, MM_T])
    f = m3.CrossSection.batch_boolean([aruco_2d(i, p) for i, p in marker_mitten().items()] + [striche_2d()], m3.OpType.Add)
    roh = m3.Manifold.extrude(f, EINLAGE + 0.2).translate([0, 0, MM_T - EINLAGE])
    w, s = k - roh, roh ^ k
    def kopf(m):
        return m.rotate([180, 0, 0]).translate([128 - MM_L / 2, 110 + MM_B / 2, MM_T])
    return kopf(w), kopf(s)


def messmatte_json():
    ecken = {}
    for i, (cx, cy) in marker_mitten().items():
        h = MARKER / 2   # ArUco-Reihenfolge: oben links, oben rechts, unten rechts, unten links (Draufsicht)
        ecken[str(i)] = [[cx - h, cy + h], [cx + h, cy + h], [cx + h, cy - h], [cx - h, cy - h]]
    feld = [RAND + MARKER + 2, RAND + 10, MM_L - RAND - MARKER - 2, MM_B - RAND - 10]
    return {"woerterbuch": "DICT_4X4_50", "marker_mm": MARKER, "platte_mm": [MM_L, MM_B], "ecken_mm": ecken,
            "messfeld_mm": feld, "hinweis": "Ursprung unten links, y nach oben, Draufsicht"}


# ---------------- Makroschlitten ----------------
S_L, S_B = 190.0, 70.0
BASIS_H = 10.0                # Schienensockel
SW_H, SW_U, SW_O = 6.0, 30.0, 38.0   # Schwalbenschwanz: Höhe, Breite unten/oben (45°)
SPIEL = 0.3
SP_Y, SP_Z = -27.0, 22.0      # Spindelachse
SP_LOCH = 6.5
SCHL_L, SCHL_H = 70.0, 32.0   # Schlitten Länge, Oberkante
MUTTER_M6 = (10.0, 5.2)       # Schlüsselweite, Höhe
MUTTER_ZOLL = (11.1, 5.6)     # 1/4"-20


def sechskant(sw, h, n=6):
    r = sw / 2 / math.cos(math.pi / 6)
    return m3.Manifold.cylinder(h, r, r, n).rotate([0, 0, 30])


def schwalbe(u, o, h, l, z0):
    cs = m3.CrossSection([[(-u / 2, 0), (u / 2, 0), (o / 2, h), (-o / 2, h)]])
    return m3.Manifold.extrude(cs, l).rotate([90, 0, 90]).translate([0, 0, z0])


def schiene():
    k = m3.Manifold.cube([S_L, S_B, BASIS_H]).translate([0, -S_B / 2, 0])
    k = k + schwalbe(SW_U, SW_O, SW_H, S_L - 24, BASIS_H - 0.01).translate([12, 0, 0])
    for x0 in (0.0, S_L - 12.0):     # Endböcke mit Spindellager
        bock = m3.Manifold.cube([12, 18, SP_Z + 7 - BASIS_H + 0.01]).translate([x0, SP_Y - 9, BASIS_H - 0.01])
        k = k + bock
    k = k - m3.Manifold.cylinder(S_L + 2, SP_LOCH / 2, SP_LOCH / 2, 32).rotate([0, 90, 0]).translate([-1, SP_Y, SP_Z])
    # Zeiger am vorderen Bock (für die Striche am Knopf)
    k = k + m3.Manifold.extrude(m3.CrossSection([[(-2, 0), (2, 0), (0, 4)]]), 1.6).rotate([90, 0, 90]).translate([-1.6, SP_Y, SP_Z + 7])
    # Stativ: Loch 1/4" + Mutterntasche von unten, mittig
    k = k - m3.Manifold.cylinder(BASIS_H + 2, 3.4, 3.4, 32).translate([S_L / 2, 0, -1])
    k = k - sechskant(MUTTER_ZOLL[0] + 0.3, MUTTER_ZOLL[1] + 0.3).translate([S_L / 2, 0, -0.01])
    # Gewicht sparen: Taschen unten seitlich
    for x in (25.0, S_L - 65.0):
        k = k - m3.Manifold.cube([40, 16, 6]).translate([x, 12, -0.01])
    return k


def schlitten():
    z0 = BASIS_H + SPIEL
    k = m3.Manifold.cube([SCHL_L, S_B, SCHL_H - z0]).translate([0, -S_B / 2, z0])
    k = k - schwalbe(SW_U + 2 * SPIEL, SW_O + 2 * SPIEL, SW_H + SPIEL, SCHL_L + 2, BASIS_H - 0.01).translate([-1, 0, 0])
    # Spindel: Durchgang + Mutterntasche (von oben einlegen)
    k = k - m3.Manifold.cylinder(SCHL_L + 2, SP_LOCH / 2 + 0.2, SP_LOCH / 2 + 0.2, 32).rotate([0, 90, 0]).translate([-1, SP_Y, SP_Z])
    tasche = sechskant(MUTTER_M6[0] + 0.3, MUTTER_M6[1] + 0.3).rotate([0, 90, 0]).translate([SCHL_L / 2 - (MUTTER_M6[1] + 0.3) / 2, SP_Y, SP_Z])
    schacht = m3.Manifold.cube([MUTTER_M6[1] + 0.3, MUTTER_M6[0] + 0.3, 20]).translate([SCHL_L / 2 - (MUTTER_M6[1] + 0.3) / 2, SP_Y - (MUTTER_M6[0] + 0.3) / 2, SP_Z])
    k = k - tasche - schacht
    # Kameraschraube 1/4": Loch + Senkung für den Kopf von unten (über dem Schwalbenschwanz)
    k = k - m3.Manifold.cylinder(40, 3.4, 3.4, 32).translate([SCHL_L / 2, 4, 0])
    k = k - m3.Manifold.cylinder(5.0, 8.5, 8.5, 48).translate([SCHL_L / 2, 4, BASIS_H + SW_H - 0.01])
    # Korkauflage-Vertiefung oben (0,6 mm, optional Gummi/Kork einkleben)
    k = k - m3.Manifold.cube([SCHL_L - 10, 50, 0.6]).translate([5, -21, SCHL_H - 0.6])
    return k


def knopf():
    d, h = 40.0, 10.0
    k = m3.Manifold.cylinder(h, d / 2, d / 2, 96)
    for i in range(30):     # Griffrillen außen
        k = k - m3.Manifold.cylinder(h + 2, 1.0, 1.0, 16).translate([d / 2 + 0.3, 0, -1]).rotate([0, 0, i * 12])
    k = k - sechskant(MUTTER_M6[0] + 0.3, MUTTER_M6[1] + 0.5).translate([0, 0, h - MUTTER_M6[1] - 0.5 + 0.01])
    k = k - m3.Manifold.cylinder(h + 2, SP_LOCH / 2, SP_LOCH / 2, 32).translate([0, 0, -1])
    from matplotlib.textpath import TextPath
    from matplotlib.font_manager import FontProperties
    fp = FontProperties(family="DejaVu Sans", weight="bold")
    for i in range(10):      # 10 Striche = 0,1 mm, Ziffern 0–9 (0,8 mm tief auf der Unterseite = später außen)
        a = i * 36
        st = m3.Manifold.cube([1.0, 5.0, 0.8]).translate([-0.5, d / 2 - 6.5, -0.01]).rotate([0, 0, -a])
        p = TextPath((0, 0), str(i), size=4.5, prop=fp)
        cs = m3.CrossSection([q.tolist() for q in p.to_polygons() if len(q) >= 3], m3.FillRule.EvenOdd)
        (x0, y0), (x1, y1) = cs.bounds()[:2], cs.bounds()[2:]
        cs = cs.translate([-(x0 + x1) / 2, -(y0 + y1) / 2]).mirror([1, 0])   # Unterseite: gespiegelt, damit von außen lesbar
        z = m3.Manifold.extrude(cs, 0.8).translate([0, d / 2 - 11, -0.01]).rotate([0, 0, -a])
        k = k - st - z
    return k


def nach_trimesh(m):
    g = m.to_mesh()
    return trimesh.Trimesh(np.asarray(g.vert_properties)[:, :3], np.asarray(g.tri_verts), process=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ziel", default="/tmp/fh")
    ap.add_argument("--bild")
    a = ap.parse_args()
    os.makedirs(a.ziel, exist_ok=True)
    w, s = messmatte()
    sch, sl = schiene(), schlitten()
    print("Schnitt Schiene/Schlitten (Mitte):", round((sch ^ sl.translate([60, 0, 0])).volume(), 3), "mm³")
    print("Schnitt weiß/schwarz:", round((w ^ s).volume(), 3))
    teile = {"messmatte_weiss": w, "messmatte_schwarz": s,
             "makro_schiene": sch.translate([128 - S_L / 2, 128, 0]),
             "makro_schlitten_knopf": (sl.rotate([180, 0, 0]).translate([0, 0, SCHL_H]) + knopf().translate([SCHL_L + 30, 0, 0])).translate([80, 128, 0])}
    for n, m in teile.items():
        t = nach_trimesh(m)
        t.export(os.path.join(a.ziel, n + ".stl"))
        print(f"{n}: dicht={t.is_watertight}, Maße {np.round(t.bounds[1] - t.bounds[0], 2)}")
    json.dump(messmatte_json(), open(os.path.join(a.ziel, "messmatte.json"), "w"), indent=1)
    if a.bild:
        import pyvista as pv
        pv.OFF_SCREEN = True
        def pm(m):
            t = nach_trimesh(m); f = np.hstack([np.full((len(t.faces), 1), 3), t.faces]).ravel()
            return pv.PolyData(np.asarray(t.vertices), f)
        pl = pv.Plotter(shape=(1, 2), window_size=(1600, 700))
        pl.subplot(0, 0)
        oben_w = w.rotate([180, 0, 0]); oben_s = s.rotate([180, 0, 0])
        pl.add_mesh(pm(oben_w), color="#f2f2f2"); pl.add_mesh(pm(oben_s), color="#111111"); pl.view_xy(); pl.add_text("Messmatte", font_size=12)
        pl.subplot(0, 1)
        pl.add_mesh(pm(sch), color="#c8c8c8"); pl.add_mesh(pm(sl.translate([60, 0, 0])), color="#e0a040")
        pl.add_mesh(pm(m3.Manifold.cylinder(S_L + 30, 3, 3, 24).rotate([0, 90, 0]).translate([-25, SP_Y, SP_Z])), color="#777777")
        pl.add_mesh(pm(knopf().rotate([0, -90, 0]).translate([-25, SP_Y, SP_Z])), color="#333333")
        pl.camera_position = [(-180, -260, 160), (95, 0, 15), (0, 0, 1)]; pl.add_text("Makroschlitten", font_size=12)
        pl.screenshot(a.bild)


if __name__ == "__main__":
    main()
