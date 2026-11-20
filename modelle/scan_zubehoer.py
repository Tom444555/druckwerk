#!/usr/bin/env python3
"""Zubehör zum Drehteller (Foto-Scans mit Meshroom) – 20.11.2026, nur gerechnet.

  Halter-Baukasten  – alles steckt mit Zapfen Ø3,1 in den Löchern Ø3,3 des Podests (Lochabstand innen 12 mm):
                      3 Spitzen (Dreipunktauflage), 2 Säulen (stapelbar, oben wieder ein Loch),
                      2 Klemmen (Schlitz 3 mm mit Rastlippen), 1 V-Auflage (zwei Zapfen, für längliche Teile).
  Prüfkörper        – Stufenklotz 60 × 52 mm mit Stufen 2–10 mm, Löchern Ø2–6, Stiften Ø1,5–4, Pyramide, Halbkugel.
                      Wird gedruckt, gescannt und mit werkzeug/scan_aufbereiten.py --vergleich gegen dieses Modell gemessen.

Aufruf: python3 modelle/scan_zubehoer.py --ziel /tmp/sz [--bild /tmp/sz/v.png]
"""
import argparse, math, os
import numpy as np
import manifold3d as m3
import trimesh

SEG = 64
ZAPFEN_D, ZAPFEN_L = 3.1, 9.0     # passt in Ø3,3 (0,1 Spiel je Seite)
LOCH_D = 3.3


def zyl(h, r1, r2=None, n=SEG):
    return m3.Manifold.cylinder(h, r1, r1 if r2 is None else r2, n)


def zapfen(x=0.0, y=0.0):
    """Zapfen von z0 bis ZAPFEN_L, unten 0,4 Fase, oben 45°-Übergang auf Ø8 (druckbar ohne Stützen)."""
    r = ZAPFEN_D / 2
    z = zyl(0.4, r - 0.4, r) + zyl(ZAPFEN_L - 0.4, r).translate([0, 0, 0.4])
    uebergang = zyl(4 - r, r, 4.0).translate([0, 0, ZAPFEN_L])        # 45°: Radius wächst um die Höhe
    return (z + uebergang).translate([x, y, 0]), ZAPFEN_L + (4 - r)


def spitze():
    z, h = zapfen()
    koerper = zyl(3.0, 4.0).translate([0, 0, h])
    kegel = zyl(12.0, 4.0, 0.4).translate([0, 0, h + 3.0])
    return z + koerper + kegel


def saeule(hoehe=20.0):
    z, h = zapfen()
    k = zyl(hoehe, 4.0).translate([0, 0, h])
    oben = h + hoehe
    loch = zyl(ZAPFEN_L + 0.6, LOCH_D / 2).translate([0, 0, oben - ZAPFEN_L - 0.5])
    fase = zyl(0.5, LOCH_D / 2, LOCH_D / 2 + 0.5).translate([0, 0, oben - 0.5])
    return z + k - loch - fase


def klemme():
    z, h = zapfen()
    b, t, hoch = 14.0, 7.0, 26.0
    profil = [(-4, h - 0.01), (4, h - 0.01), (b / 2, h + b / 2 - 4), (b / 2, h + hoch), (-b / 2, h + hoch), (-b / 2, h + b / 2 - 4)]  # 45° unten
    k = m3.Manifold.extrude(m3.CrossSection([profil], m3.FillRule.EvenOdd), t).rotate([90, 0, 90]).translate([-t / 2, 0, 0])
    schlitz = m3.Manifold.cube([t + 2, 3.0, 16.0]).translate([-t / 2 - 1, -1.5, h + hoch - 16.0])
    entlast = m3.Manifold.cylinder(t + 2, 2.0, 2.0, 32).rotate([0, 90, 0]).translate([-t / 2 - 1, 0, h + hoch - 16.0])
    lippen = [m3.Manifold.extrude(m3.CrossSection([[(s * 1.5, 0), (s * 0.9, 0.6), (s * 1.5, 1.2)]], m3.FillRule.EvenOdd), t)
              .rotate([90, 0, 90]).translate([-t / 2, 0, h + hoch - 4.0]) for s in (-1, 1)]
    # Lippen: kleine Dreiecke (je 0,6 mm in den Schlitz), halten dünne Teile
    return z + (k - schlitz - entlast) + m3.Manifold.batch_boolean(lippen, m3.OpType.Add)


def v_auflage():
    """Zwei Zapfen im Abstand 12 mm, Block 32 × 14 × 12 mit 90°-V oben (gedruckt kopfüber)."""
    l, b, hoch, tief = 32.0, 14.0, 12.0, 6.0
    blk = m3.Manifold.cube([l, b, hoch]).translate([-l / 2, -b / 2, 0])
    v = m3.Manifold.extrude(m3.CrossSection([[(-tief, hoch + 0.01), (tief, hoch + 0.01), (0, hoch - tief)]], m3.FillRule.EvenOdd), l + 2)
    v = v.rotate([90, 0, 90]).translate([-l / 2 - 1, 0, 0])
    k = blk - v
    zs = []
    for x in (-6.0, 6.0):  # Zapfen nach unten
        r = ZAPFEN_D / 2
        zs.append((zyl(0.4, r - 0.4, r) + zyl(ZAPFEN_L - 0.4 + 0.01, r).translate([0, 0, 0.4])).rotate([180, 0, 0]).translate([x, 0, 0.01]))
    k = k + m3.Manifold.batch_boolean(zs, m3.OpType.Add)
    return k.rotate([180, 0, 0]).translate([0, 0, hoch])  # kopfüber: V liegt auf dem Bett, Zapfen oben


def baukasten():
    teile = []
    for i in range(3):
        teile.append(spitze().translate([i * 14, 0, 0]))
    for i in range(2):
        teile.append(saeule().translate([i * 14, 16, 0]))
    for i in range(2):
        teile.append(klemme().translate([i * 14 + 35, 16, 0]))
    teile.append(v_auflage().translate([60, -2, 0]))
    return m3.Manifold.batch_boolean(teile, m3.OpType.Add)


def pruefkoerper():
    """Stufenklotz. Ursprung: Mitte der Grundfläche, Stufen steigen in +x, Merkmale in +y."""
    L, B, G = 60.0, 52.0, 5.0
    k = m3.Manifold.cube([L, B, G]).translate([-L / 2, -B / 2, 0])
    for i, h in enumerate((2, 4, 6, 8, 10)):            # Stufen 12 × 18 mm
        k = k + m3.Manifold.cube([12, 18, h]).translate([-L / 2 + i * 12, -B / 2, G - 0.01])
    for i, d in enumerate((2, 3, 4, 5, 6)):             # Sacklöcher 4 mm tief
        k = k - zyl(4.01, d / 2, n=48).translate([-L / 2 + 6 + i * 11, -1.0, G - 4.0])
    for i, d in enumerate((1.5, 2, 3, 4)):              # Stifte 6 mm hoch
        k = k + zyl(6.0, d / 2, n=48).translate([-L / 2 + 8 + i * 9, 9.0, G - 0.01])
    pyr = m3.Manifold.cylinder(6.0, 6.0 * math.sqrt(2), 0.01, 4).rotate([0, 0, 45]).translate([17, 9.0, G - 0.01])  # 45°-Pyramide 12 × 12
    kugel = m3.Manifold.sphere(6.0, 96).translate([0, 0, 0]) ^ m3.Manifold.cube([20, 20, 10]).translate([-10, -10, 0])
    k = k + pyr + kugel.translate([-10, 19.0, G - 0.01])
    k = k - zyl(G + 1, 1.5, n=32).translate([L / 2 - 4, B / 2 - 4, -0.5])   # Durchgangsloch als Lage-Merkmal (nur eine Ecke)
    return k


def nach_trimesh(m):
    g = m.to_mesh()
    return trimesh.Trimesh(np.asarray(g.vert_properties)[:, :3], np.asarray(g.tri_verts), process=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ziel", default="/tmp/sz")
    ap.add_argument("--bild")
    a = ap.parse_args()
    os.makedirs(a.ziel, exist_ok=True)
    teile = {"scan_halter": baukasten().translate([100, 120, 0]), "scan_pruefkoerper": pruefkoerper().translate([128, 128, 0])}
    for n, m in teile.items():
        t = nach_trimesh(m)
        t.export(os.path.join(a.ziel, n + ".stl"))
        print(f"{n}: dicht={t.is_watertight}, Maße {np.round(t.bounds[1] - t.bounds[0], 2)}, Vol {m.volume():.0f} mm³")
    # Bezugsmodell für den Vergleich (Ursprung Mitte Grundfläche)
    nach_trimesh(pruefkoerper()).export(os.path.join(a.ziel, "scan_pruefkoerper_bezug.stl"))
    if a.bild:
        import pyvista as pv
        pv.OFF_SCREEN = True
        pl = pv.Plotter(shape=(1, 2), window_size=(1600, 700))
        for i, (n, m) in enumerate(teile.items()):
            t = nach_trimesh(m)
            f = np.hstack([np.full((len(t.faces), 1), 3), t.faces]).ravel()
            pl.subplot(0, i); pl.add_mesh(pv.PolyData(np.asarray(t.vertices), f), color="#d8d8d8")
            pl.camera_position = "iso"; pl.add_text(n, font_size=12)
        pl.screenshot(a.bild)


if __name__ == "__main__":
    main()
