#!/usr/bin/env python3
"""Drehteller für Foto-Scans (Meshroom) – Creator 5 Pro, 20.11.2026.

Zwei Teile:
  Sockel  – Platte Ø200 mit Laufring (V-Rille) und Mittelzapfen.
  Teller  – Ø244 (größter Kreis, den der Slicer auf 256 mm noch anordnet), Unterseite mit Rippen, Laufring (V-Rille) und Nabe.
Dazwischen laufen 6-mm-Kugeln (Stahlkugeln oder Softair-BBs) in den beiden 90°-V-Rillen auf Ø180.
Oberseite: 25 Felder (Linien), Zahlen 1–25 am Rand, Kreise R50/75/100 mm als Maßstab, Mittelkreuz –
als schwarze Einlage bündig im weißen Teller (Teller wird mit der Oberseite nach unten gedruckt).

Aufruf: python3 modelle/drehteller.py --ziel /tmp/dt [--bild /tmp/dt/v.png]
Slicen: Sockel 0.20/20 %/3 Wände; Teller --zusammen 0.20/15 %/3 Wände --extra enable_prime_tower=0
(mit Spülturm passt der Ø244-Teller nicht auf die Platte; Kopfwechsel nur in den ersten 3 Schichten).
Montage: ~88 Kugeln Ø6 (Stahl oder Softair-BB) in die Sockel-Rille, Teller aufsetzen (Zapfen in die Nabe).
"""
import argparse, math, os
import numpy as np
import manifold3d as m3
import trimesh
from matplotlib.textpath import TextPath
from matplotlib.font_manager import FontProperties

# ---------- Maße (mm) ----------
R_TELLER = 122.0      # Teller Ø244 (größter Kreis, den Orca auf der 256er-Platte noch anordnet)
R_SOCKEL = 100.0      # Sockel Ø200
R_LAUF = 90.0         # Mitte der Kugelbahn (Ø180)
B_LAUF = 14.0         # Breite der Laufringe
KUGEL = 6.0           # Kugel-Ø
SPALT = 1.5           # Luft zwischen den Laufringen
T_PLATTE = 4.0        # Tellerplatte
H_RIPPE = 6.0         # Rippen unter dem Teller
N_RIPPEN = 16
B_RIPPE = 3.0
T_SOCKEL = 4.0
H_SOCKELRING = 6.0
R_ZAPFEN = 6.0
SPIEL_ZAPFEN = 0.3
N_FELDER = 25
EINLAGE = 0.6         # Tiefe der schwarzen Einlage (3 Schichten à 0,2)
B_LINIE = 1.2
B_KREIS = 0.8
H_ZAHL = 9.0
SEG = 360

# abgeleitete Höhen (Gebrauchslage, Tisch = z0)
Z_SOCKELRING = T_SOCKEL + H_SOCKELRING          # 10
Z_KUGEL = Z_SOCKELRING + SPALT / 2              # Kugelmitte
V = (KUGEL / 2) * math.sqrt(2)                  # Abstand Kugelmitte -> Rillenspitze bei 90°
Z_TELLER_U = Z_SOCKELRING + SPALT               # 11.5 Unterkante Rippen/Laufring
Z_PLATTE_U = Z_TELLER_U + H_RIPPE               # 17.5
Z_OBEN = Z_PLATTE_U + T_PLATTE                  # 21.5
Z_ZAPFEN = Z_OBEN - 2.0                         # Zapfenspitze
Z_LOCH = Z_OBEN - 1.5                           # Sackloch in der Nabe (1,5 mm Deckel)


def revolve(punkte):
    """Profil (r, z) um die Z-Achse drehen."""
    return m3.Manifold.revolve(m3.CrossSection([punkte], m3.FillRule.EvenOdd), SEG)


def rille(z_spitze, z_kante, nach_oben):
    """V-Rille (90°) als Rotationskörper zum Abziehen."""
    t = abs(z_spitze - z_kante) + 0.01
    z0 = z_kante - 0.01 if nach_oben else z_kante + 0.01
    return revolve([(R_LAUF - t, z0), (R_LAUF + t, z0), (R_LAUF, z_spitze)])


def sockel():
    k = revolve([(0, 0), (R_SOCKEL - 1, 0), (R_SOCKEL, 1), (R_SOCKEL, T_SOCKEL), (0, T_SOCKEL)])
    ring = revolve([(R_LAUF - B_LAUF / 2, T_SOCKEL - 0.1), (R_LAUF + B_LAUF / 2, T_SOCKEL - 0.1),
                    (R_LAUF + B_LAUF / 2, Z_SOCKELRING), (R_LAUF - B_LAUF / 2, Z_SOCKELRING)])
    # Zapfen mit Fuß-Kegel und Fase oben
    zapfen = revolve([(0, T_SOCKEL - 0.1), (R_ZAPFEN + 3, T_SOCKEL - 0.1), (R_ZAPFEN, T_SOCKEL + 3),
                      (R_ZAPFEN, Z_ZAPFEN - 1), (R_ZAPFEN - 1, Z_ZAPFEN), (0, Z_ZAPFEN)])
    # Rippen unter der Platte gibt es nicht (liegt flach auf); dafür Speichen auf der Platte zwischen Zapfen und Ring
    speichen = []
    for i in range(8):
        a = i * 45
        b = m3.Manifold.cube([R_LAUF - R_ZAPFEN - 3, 3, 3]).translate([R_ZAPFEN + 2, -1.5, T_SOCKEL - 0.1])
        speichen.append(b.rotate([0, 0, a]))
    s = k + ring + zapfen + m3.Manifold.batch_boolean(speichen, m3.OpType.Add)
    s = s - rille(Z_KUGEL - V, Z_SOCKELRING, nach_oben=False)
    return s


def teller_koerper():
    platte = revolve([(0, Z_PLATTE_U), (R_TELLER, Z_PLATTE_U), (R_TELLER, Z_OBEN - 0.8),
                      (R_TELLER - 0.8, Z_OBEN), (0, Z_OBEN)])
    rand = revolve([(R_TELLER - 3, Z_TELLER_U), (R_TELLER, Z_TELLER_U), (R_TELLER, Z_PLATTE_U + 0.1),
                    (R_TELLER - 3, Z_PLATTE_U + 0.1)])
    lauf = revolve([(R_LAUF - B_LAUF / 2, Z_TELLER_U), (R_LAUF + B_LAUF / 2, Z_TELLER_U),
                    (R_LAUF + B_LAUF / 2, Z_PLATTE_U + 0.1), (R_LAUF - B_LAUF / 2, Z_PLATTE_U + 0.1)])
    nabe = revolve([(0, Z_TELLER_U), (16, Z_TELLER_U), (16, Z_PLATTE_U + 0.1), (0, Z_PLATTE_U + 0.1)])
    rippen = []
    for i in range(N_RIPPEN):
        b = m3.Manifold.cube([R_TELLER - 2 - 15, B_RIPPE, H_RIPPE + 0.1]).translate([15, -B_RIPPE / 2, Z_TELLER_U])
        rippen.append(b.rotate([0, 0, i * 360 / N_RIPPEN + 360 / N_RIPPEN / 2]))
    t = platte + rand + lauf + nabe + m3.Manifold.batch_boolean(rippen, m3.OpType.Add)
    t = t - rille(Z_KUGEL + V, Z_TELLER_U, nach_oben=True)
    loch = revolve([(0, Z_TELLER_U - 1), (R_ZAPFEN + SPIEL_ZAPFEN + 0.6, Z_TELLER_U - 1),
                    (R_ZAPFEN + SPIEL_ZAPFEN, Z_TELLER_U + 0.5), (R_ZAPFEN + SPIEL_ZAPFEN, Z_LOCH), (0, Z_LOCH)])
    return t - loch


# ---------- Markierungen (2D) ----------
def rechteck(x0, x1, b):
    return m3.CrossSection([[(x0, -b / 2), (x1, -b / 2), (x1, b / 2), (x0, b / 2)]])


def kreisring(r, b):
    return m3.CrossSection.circle(r + b / 2, SEG) - m3.CrossSection.circle(r - b / 2, SEG)


def zahl(text, h):
    fp = FontProperties(family="DejaVu Sans", weight="bold")
    p = TextPath((0, 0), text, size=h, prop=fp)
    polys = [np.asarray(q) for q in p.to_polygons() if len(q) >= 3]
    cs = m3.CrossSection([q.tolist() for q in polys], m3.FillRule.EvenOdd)
    (x0, y0), (x1, y1) = cs.bounds()[:2], cs.bounds()[2:]
    return cs.translate([-(x0 + x1) / 2, -(y0 + y1) / 2])


def markierung_2d():
    teile = []
    for i in range(N_FELDER):
        a = 90 - i * 360 / N_FELDER                       # Linie i = Anfang von Feld i+1, im Uhrzeigersinn
        teile.append(rechteck(20, R_TELLER - 17, B_LINIE).rotate(a))
        # Zahl mittig im Feld, Kopf nach außen
        am = a - 180 / N_FELDER
        t = str(i + 1) + ("." if i + 1 in (6, 9) else "")  # 6./9. unterscheidbar
        z = zahl(t, H_ZAHL).rotate(am - 90)
        r = R_TELLER - 9.5
        teile.append(z.translate([r * math.cos(math.radians(am)), r * math.sin(math.radians(am))]))
    for r in (50, 75, 100):
        teile.append(kreisring(r, B_KREIS))
    teile.append(rechteck(-8, 8, 1.0))
    teile.append(rechteck(-8, 8, 1.0).rotate(90))
    teile.append(kreisring(14, B_KREIS))
    return m3.CrossSection.batch_boolean(teile, m3.OpType.Add)


def teller():
    k = teller_koerper()
    ein = m3.Manifold.extrude(markierung_2d(), EINLAGE + 0.05).translate([0, 0, Z_OBEN - EINLAGE])
    ein = ein ^ k
    return k - ein, ein


def nach_trimesh(m):
    g = m.to_mesh()
    return trimesh.Trimesh(np.asarray(g.vert_properties)[:, :3], np.asarray(g.tri_verts), process=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ziel", default="modelle")
    ap.add_argument("--bild")
    a = ap.parse_args()
    os.makedirs(a.ziel, exist_ok=True)
    s = sockel()
    weiss, schwarz = teller()
    # Druckglage Teller: Oberseite nach unten (180° um X), auf z=0
    def kopf(m):
        return m.rotate([180, 0, 0]).translate([128, 128, Z_OBEN])  # --zusammen (assemble) braucht Bett-Koordinaten
    out = {
        "drehteller_sockel": s,
        "drehteller_teller_weiss": kopf(weiss),
        "drehteller_teller_schwarz": kopf(schwarz),
    }
    for n, m in out.items():
        t = nach_trimesh(m)
        t.export(os.path.join(a.ziel, n + ".stl"))
        b = t.bounds
        print(f"{n}: {len(t.faces)} Dreiecke, dicht={t.is_watertight}, Maße {np.round(b[1]-b[0],2)}, Vol {m.volume():.0f} mm³")
    print("Schnitt weiß/schwarz:", round((weiss ^ schwarz).volume(), 3), "mm³")
    print("Schnitt Sockel/Teller (Gebrauchslage):", round((s ^ (weiss + schwarz)).volume(), 3), "mm³")
    n_kugeln = int(2 * math.pi * R_LAUF / KUGEL) - 3
    print(f"Kugelbahn Ø{2*R_LAUF:.0f} mm: {n_kugeln} Kugeln à {KUGEL} mm; Höhe gesamt {Z_OBEN} mm")
    if a.bild:
        bild(weiss, schwarz, s, a.bild)


def bild(weiss, schwarz, s, pfad):
    import pyvista as pv
    pv.OFF_SCREEN = True
    def pm(m):
        t = nach_trimesh(m)
        f = np.hstack([np.full((len(t.faces), 1), 3), t.faces]).ravel()
        return pv.PolyData(np.asarray(t.vertices), f)
    pl = pv.Plotter(shape=(1, 2), window_size=(1600, 800))
    pl.subplot(0, 0)
    pl.add_mesh(pm(weiss), color="#f2f2f2"); pl.add_mesh(pm(schwarz), color="#111111")
    pl.view_xy(); pl.camera.zoom(1.3); pl.add_text("Oberseite", font_size=12)
    pl.subplot(0, 1)
    pl.add_mesh(pm(s), color="#c8c8c8")
    pl.add_mesh(pm(weiss.translate([0, 0, 60])), color="#f2f2f2")
    pl.add_mesh(pm(schwarz.translate([0, 0, 60])), color="#111111")
    pl.camera_position = [(260, -420, -40), (0, 0, 30), (0, 0, 1)]
    pl.add_text("Unterseite + Sockel", font_size=12)
    pl.screenshot(pfad)


if __name__ == "__main__":
    main()
