#!/usr/bin/env python3
"""Drehteller für Foto-Scans (Meshroom) – Creator 5 Pro, 20.11.2026.

Zwei Teile:
  Sockel  – Platte Ø212 mit flachem Laufring, Führungslippen und Mittelzapfen.
  Käfig   – Ring mit 24 Taschen, dazu 48 Walzen (ein Druck).
  Teller  – Ø226 (mit Spülturm), Unterseite mit Rippen, flachem Laufring und Nabe.
Dazwischen laufen 48 gedruckte Walzen (Ø8 × 6,8 mm, je zwei in 24 Taschen) in einem Käfig auf flachen
Laufringen (Ø160–200); Lippen am Sockel führen den Käfig innen und außen. Alles gedruckt, keine Kaufteile.
Oberseite: 25 Felder (Linien), Zahlen 1–25 am Rand, Kreise R50/75/100 mm als Maßstab, Mittelkreuz –
als schwarze Einlage bündig im weißen Teller (Teller wird mit der Oberseite nach unten gedruckt).

Aufruf: python3 modelle/drehteller.py --ziel /tmp/dt [--bild /tmp/dt/v.png]
Slicen: Sockel 0.20/20 %/3 Wände + Bügeln; Käfig+Walzen 0.12/100 %; Teller --zusammen 0.20/15 %/3 Wände + Bügeln
--extra enable_prime_tower=0 (mit Spülturm passt der Ø244-Teller nicht; Kopfwechsel nur in den ersten 3 Schichten).
Montage: Käfig zwischen die Lippen legen, in jede Tasche zwei Walzen, Teller aufsetzen (Zapfen in die Nabe).
"""
import argparse, math, os
import numpy as np
import manifold3d as m3
import trimesh
from matplotlib.textpath import TextPath
from matplotlib.font_manager import FontProperties

# ---------- Maße (mm) ----------
R_TELLER = 113.0      # Teller Ø226 (größter Ø, bei dem der Spülturm noch auf die Platte passt; Ø244 ging nur ohne Turm)
R_SOCKEL = 106.0      # Sockel Ø212
R_I, R_A = 80.0, 100.0  # Laufbahn innen/außen (flache Ringe oben am Sockel, unten am Teller)
D_WALZE = 8.0         # Walzen-Ø
L_WALZE = 6.8         # Walzenlänge (zwei Walzen je Tasche -> wenig Schlupf)
N_TASCHEN = 24
SPIEL = 0.3           # Luft Walze <-> Käfig je Seite
T_KAEFIG = 3.0
T_PLATTE = 4.0        # Tellerplatte
H_RIPPE = 6.0         # Rippen unter dem Teller
N_RIPPEN = 16
B_RIPPE = 3.0
T_SOCKEL = 4.0
H_LAUF = 6.0          # Höhe des Sockel-Laufrings über der Platte
R_ZAPFEN = 6.0
SPIEL_ZAPFEN = 0.3
N_FELDER = 25
EINLAGE = 0.6         # Tiefe der schwarzen Einlage (3 Schichten à 0,2)
B_LINIE = 1.2
B_KREIS = 0.8
H_ZAHL = 9.0
H_ZAHL_RAND = 6.5    # Zahlen auf der Seitenfläche (Rand 10 mm hoch)
SEG = 360
# Meshroom-Hilfen
MARKER_IDS = (0, 1, 2, 3)   # CCTag3 (AliceVision), Ringe aus modelle/drehteller_daten/cctag3.txt
MARKER_R = 12.0             # Marker-Radius (feinster Ring = 10 % = 1,2 mm)
MARKER_BAHN = 75.0          # Abstand der Marker-Mitten von der Tellermitte
MARKER_FELDER = (0, 6, 13, 19)  # Felder (0 = Feld 1), unregelmäßig -> Lage eindeutig
PUNKTE_ABSTAND = 4.2        # Zufallsmuster: Mindestabstand der Punkte
PUNKT_R = (0.6, 1.1)        # Punktradius min/max
PODEST_D, PODEST_H = 70.0, 40.0
PODEST_STIFT_R = 30.0       # Steckstifte Podest -> Teller auf diesem Radius
PODEST_FELDER = (0, 8, 16)
STIFT_D = 4.0
# Visier (Kimme und Korn, steckbar am Sockel, zeigt auf die Zahl am Tellerrand)
VIS_WINKEL = -90.0    # Lage am Sockel (vorn)
# Rastung: federnde Brücke am Sockel greift in 25 Kerben unter dem Tellerrand (Kerben in den Feldmitten)
RAST_WINKEL = -90.0 + 14.4 * 5   # muss -90 + n·14,4 sein, sonst rastet der Teller neben der Zahl ein
RAST_R = 111.5        # Mitte des Tellerrands (R110–113)
RAST_L = 46.0         # freie Länge der Brücke (beidseitig eingespannt)
RAST_T = 1.2          # Dicke der Brücke (federt ~0,6 mm, ~2 N gerechnet)
KERBE_B, KERBE_T = 2.4, 1.0
ZAPFEN_Q = 8.0        # Steckzapfen 8 × 8 mm, Loch +0,4
VIS_R0 = 106.0        # Zapfen von R106 …
VIS_ARM_B = 8.0       # Armbreite

# abgeleitete Höhen (Gebrauchslage, Tisch = z0)
Z_LAUF_U = T_SOCKEL + H_LAUF                    # 10  Lauffläche Sockel
Z_ACHSE = Z_LAUF_U + D_WALZE / 2                # 14  Walzenachse
Z_TELLER_U = Z_LAUF_U + D_WALZE                 # 18  Lauffläche Teller = Unterkante Rippen
Z_PLATTE_U = Z_TELLER_U + H_RIPPE               # 24
Z_OBEN = Z_PLATTE_U + T_PLATTE                  # 28
Z_LIPPE = Z_ACHSE + 1.0                         # Führungslippen am Sockel (innen/außen) bis 15
Z_ZAPFEN = Z_OBEN - 2.0
Z_LOCH = Z_OBEN - 1.5
# Käfig
K_I, K_A = R_I - 0.5, R_A + 0.5                 # 79.5 … 100.5
TASCHE_L = 2 * L_WALZE + 1.4                    # 15 mm radial
TASCHE_B = D_WALZE + 2 * SPIEL
R_TASCHE = (R_I + R_A) / 2                      # 90
LIPPE_I = (K_I - 2.8, K_I - 0.5)                # 76.7 … 79.0
LIPPE_A = (K_A + 0.5, K_A + 3.0)                # 101 … 103.5


def revolve(punkte):
    """Profil (r, z) um die Z-Achse drehen."""
    return m3.Manifold.revolve(m3.CrossSection([punkte], m3.FillRule.EvenOdd), SEG)


def ring(r0, r1, z0, z1):
    return revolve([(r0, z0), (r1, z0), (r1, z1), (r0, z1)])


def visier_maße():
    z_arm = (Z_LAUF_U, Z_LAUF_U + 6.0)                     # Arm 10 … 16, unter dem Teller (18) durch
    z_ziel = Z_TELLER_U + 0.5                              # Visierlinie knapp über der Tellerunterkante, unter den Zahlen
    korn_r = (R_TELLER + 2.0, R_TELLER + 5.0)
    kimme_r = (R_TELLER + 34.0, R_TELLER + 37.0)
    return z_arm, z_ziel, korn_r, kimme_r


def visier():
    """Kimme und Korn in Gebrauchslage, Blick radial auf die Tellermitte (Richtung VIS_WINKEL)."""
    (za0, za1), zz, (k0, k1), (m0, m1) = visier_maße()
    q = ZAPFEN_Q
    zapfen = m3.Manifold.cube([q, q, za0 + 0.01]).translate([VIS_R0, -q / 2, 0])
    arm = m3.Manifold.cube([m1 - VIS_R0, VIS_ARM_B, za1 - za0]).translate([VIS_R0, -VIS_ARM_B / 2, za0])
    korn = m3.Manifold.cube([k1 - k0, 1.6, zz - za1 + 0.01]).translate([k0, -0.8, za1 - 0.01])
    kimme = m3.Manifold.cube([m1 - m0, 16.0, zz + 1.0]).translate([m0, -8.0, 0])  # flach: Zahl bleibt darüber sichtbar
    kerbe = m3.Manifold.cube([m1 - m0 + 2, 2.4, 20]).translate([m0 - 1, -1.2, zz])
    v = zapfen + arm + korn + kimme - kerbe
    return v.rotate([0, 0, VIS_WINKEL])


def sockel():
    k = revolve([(0, 0), (R_SOCKEL - 1, 0), (R_SOCKEL, 1), (R_SOCKEL, T_SOCKEL), (0, T_SOCKEL)])
    lauf = ring(R_I, R_A, T_SOCKEL - 0.1, Z_LAUF_U)
    lippen = ring(*LIPPE_I, T_SOCKEL - 0.1, Z_LIPPE) + ring(*LIPPE_A, T_SOCKEL - 0.1, Z_LIPPE)
    zapfen = revolve([(0, T_SOCKEL - 0.1), (R_ZAPFEN + 3, T_SOCKEL - 0.1), (R_ZAPFEN, T_SOCKEL + 3),
                      (R_ZAPFEN, Z_ZAPFEN - 1), (R_ZAPFEN - 1, Z_ZAPFEN), (0, Z_ZAPFEN)])
    speichen = [m3.Manifold.cube([LIPPE_I[0] - R_ZAPFEN - 1, 3, 3]).translate([R_ZAPFEN + 2, -1.5, T_SOCKEL - 0.1]).rotate([0, 0, i * 45])
                for i in range(8)]
    # Steckaufnahme für das Visier (Block mit senkrechtem Vierkantloch)
    q, sp = ZAPFEN_Q, 0.2
    block = m3.Manifold.cube([VIS_R0 + q + 4 - (LIPPE_A[1] + 0.5), 20, Z_LAUF_U]).translate([LIPPE_A[1] + 0.5, -10, 0])
    loch = m3.Manifold.cube([q + 2 * sp, q + 2 * sp, 40]).translate([VIS_R0 - sp, -q / 2 - sp, -5])
    aufnahme = (block - loch).rotate([0, 0, VIS_WINKEL])
    return k + lauf + lippen + zapfen + m3.Manifold.batch_boolean(speichen, m3.OpType.Add) + aufnahme - loch.rotate([0, 0, VIS_WINKEL]) + rastung()


def rastung():
    """Lasche am Sockel mit zwei Pfosten und einer Brücke (Feder), oben ein Nocken (r 1, 0,6 mm in die Kerbe)."""
    l, t, b = RAST_L, RAST_T, 4.0
    z_o = Z_TELLER_U - 1.4                     # Brücken-Oberkante 16,6
    lasche = m3.Manifold.cube([18, l + 12, T_SOCKEL]).translate([R_SOCKEL - 6, -(l + 12) / 2, 0])
    pfosten = [m3.Manifold.cube([b, 4, z_o - T_SOCKEL + 0.1]).translate([RAST_R - b / 2, y, T_SOCKEL - 0.1]) for y in (-l / 2 - 4, l / 2)]
    bruecke = m3.Manifold.cube([b, l + 8, t]).translate([RAST_R - b / 2, -l / 2 - 4, z_o - t])
    nocken = m3.Manifold.cylinder(b, 1.0, 1.0, 32).rotate([0, 90, 0]).translate([RAST_R - b / 2, 0, z_o + 1.0])
    return (lasche + m3.Manifold.batch_boolean(pfosten, m3.OpType.Add) + bruecke + nocken).rotate([0, 0, RAST_WINKEL])


def kaeffig_taschen():
    t = []
    for i in range(N_TASCHEN):
        b = m3.Manifold.cube([TASCHE_L, TASCHE_B, 20]).translate([R_TASCHE - TASCHE_L / 2, -TASCHE_B / 2, -10])
        t.append(b.rotate([0, 0, i * 360 / N_TASCHEN]))
    return m3.Manifold.batch_boolean(t, m3.OpType.Add)


def kaefig():
    """Käfig in Gebrauchslage (mittig auf der Walzenachse)."""
    k = ring(K_I, K_A, Z_ACHSE - T_KAEFIG / 2, Z_ACHSE + T_KAEFIG / 2)
    return k - kaeffig_taschen().translate([0, 0, Z_ACHSE])


def walze():
    """Walze stehend (Achse z), mit Fasen 0,5 gegen Elefantenfuß/Grat."""
    r, f = D_WALZE / 2, 0.5
    return revolve([(0, 0), (r - f, 0), (r, f), (r, L_WALZE - f), (r - f, L_WALZE), (0, L_WALZE)])


def walzen_gebrauch():
    """Walzen liegend in den Taschen (für Schnittprüfung und Bild)."""
    w = walze().translate([0, 0, -L_WALZE / 2]).rotate([0, 90, 0])  # Achse jetzt x
    teile = []
    for i in range(N_TASCHEN):
        for x in (R_TASCHE - L_WALZE / 2 - 0.35, R_TASCHE + L_WALZE / 2 + 0.35):
            teile.append(w.translate([x, 0, Z_ACHSE]).rotate([0, 0, i * 360 / N_TASCHEN]))
    return m3.Manifold.batch_boolean(teile, m3.OpType.Add)


def teller_koerper():
    platte = revolve([(0, Z_PLATTE_U), (R_TELLER, Z_PLATTE_U), (R_TELLER, Z_OBEN - 0.8),
                      (R_TELLER - 0.8, Z_OBEN), (0, Z_OBEN)])
    rand = ring(R_TELLER - 3, R_TELLER, Z_TELLER_U, Z_PLATTE_U + 0.1)
    lauf = ring(R_I, R_A, Z_TELLER_U, Z_PLATTE_U + 0.1)
    nabe = ring(0, 16, Z_TELLER_U, Z_PLATTE_U + 0.1)
    rippen = []
    for i in range(N_RIPPEN):
        b = m3.Manifold.cube([R_TELLER - 2 - 15, B_RIPPE, H_RIPPE + 0.1]).translate([15, -B_RIPPE / 2, Z_TELLER_U])
        rippen.append(b.rotate([0, 0, i * 360 / N_RIPPEN + 360 / N_RIPPEN / 2]))
    t = platte + rand + lauf + nabe + m3.Manifold.batch_boolean(rippen, m3.OpType.Add)
    kerbe = m3.Manifold.extrude(m3.CrossSection([[(-KERBE_B / 2, -0.01), (KERBE_B / 2, -0.01), (0, KERBE_T)]]), 6.0)  # Dreieck in (y,z), Länge entlang x
    kerbe = kerbe.rotate([90, 0, 90]).translate([R_TELLER - 5, 0, Z_TELLER_U])
    t = t - m3.Manifold.batch_boolean([kerbe.rotate([0, 0, math.degrees(feld_mitte(i))]) for i in range(N_FELDER)], m3.OpType.Add)
    loch = revolve([(0, Z_TELLER_U - 1), (R_ZAPFEN + SPIEL_ZAPFEN + 0.6, Z_TELLER_U - 1),
                    (R_ZAPFEN + SPIEL_ZAPFEN, Z_TELLER_U + 0.5), (R_ZAPFEN + SPIEL_ZAPFEN, Z_LOCH), (0, Z_LOCH)])
    stifte = m3.Manifold.batch_boolean([m3.Manifold.extrude(c, 3.2).translate([0, 0, Z_OBEN - 3.0]) for c in podest_loecher_2d()], m3.OpType.Add)
    return t - loch - stifte


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


def feld_mitte(i):
    return math.radians(90 - i * 360 / N_FELDER - 180 / N_FELDER)


def marker_orte():
    return [(MARKER_BAHN * math.cos(feld_mitte(f)), MARKER_BAHN * math.sin(feld_mitte(f))) for f in MARKER_FELDER]


def cctag(idx, r):
    """CCTag3 als schwarze Fläche: Scheibe 100 minus weiß 90, schwarz 80 … (Einheiten % von r)."""
    radien = [int(x) for x in open(os.path.join(os.path.dirname(__file__), "drehteller_daten", "cctag3.txt")).read().splitlines()[idx].split()]
    cs = m3.CrossSection.circle(r, 128)
    weiss = True
    for q in radien:
        k = m3.CrossSection.circle(r * q / 100, 128)
        cs = cs - k if weiss else cs + k
        weiss = not weiss
    return cs


def podest_loecher_2d(spiel=0.2):
    return [m3.CrossSection.circle(STIFT_D / 2 + spiel, 32).translate(
        [PODEST_STIFT_R * math.cos(feld_mitte(f)), PODEST_STIFT_R * math.sin(feld_mitte(f))]) for f in PODEST_FELDER]


def markierung_2d():
    teile = []
    for i in range(N_FELDER):
        a = 90 - i * 360 / N_FELDER                       # Linie i = Anfang von Feld i+1, im Uhrzeigersinn
        teile.append(rechteck(20, R_TELLER - 17, B_LINIE).rotate(a))
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
    linien = m3.CrossSection.batch_boolean(teile, m3.OpType.Add)
    # Freiflächen um die Marker (weißer Rand) und um die Podest-Löcher
    frei = [m3.CrossSection.circle(MARKER_R + 3.5, 96).translate([x, y]) for x, y in marker_orte()]
    frei += [m3.CrossSection.circle(STIFT_D / 2 + 1.5, 32).translate([PODEST_STIFT_R * math.cos(feld_mitte(f)), PODEST_STIFT_R * math.sin(feld_mitte(f))])
             for f in PODEST_FELDER]
    frei = m3.CrossSection.batch_boolean(frei, m3.OpType.Add)
    linien = linien - frei
    # Zufallsmuster (feste Saat, damit jeder Neubau gleich aussieht)
    rng = np.random.default_rng(25)
    pkt, gitter, g = [], {}, PUNKTE_ABSTAND
    for _ in range(60000):
        r = math.sqrt(rng.uniform(18 ** 2, (R_TELLER - 3) ** 2)); w = rng.uniform(0, 2 * math.pi)
        x, y = r * math.cos(w), r * math.sin(w)
        gx, gy = int(x // g), int(y // g)
        if all((x - a) ** 2 + (y - b) ** 2 > g * g for i in (-1, 0, 1) for j in (-1, 0, 1) for a, b in gitter.get((gx + i, gy + j), [])):
            pkt.append((x, y)); gitter.setdefault((gx, gy), []).append((x, y))
    punkte = m3.CrossSection.batch_boolean(
        [m3.CrossSection.circle(rng.uniform(*PUNKT_R), 12).translate([x, y]) for x, y in pkt], m3.OpType.Add)
    punkte = punkte - linien.offset(1.0, m3.JoinType.Round) - frei.offset(0.5, m3.JoinType.Round) \
        - (m3.CrossSection.circle(R_TELLER, SEG) - m3.CrossSection.circle(R_TELLER - 2.5, SEG))
    punkte = m3.CrossSection([p for p in punkte.to_polygons() if abs(m3.CrossSection([p]).area()) > 0.8])  # Splitter weg
    marker = m3.CrossSection.batch_boolean([cctag(i, MARKER_R).translate([x, y]) for i, (x, y) in zip(MARKER_IDS, marker_orte())], m3.OpType.Add)
    return linien + punkte + marker


def rand_markierung(k):
    """Zahlen 1–25 und senkrechte Linien auf dem Außenrand (Seitenfläche) – für die Kamera von der Seite."""
    teile = []
    tiefe, z_mitte = EINLAGE + 0.2, (Z_TELLER_U + Z_OBEN - 0.8) / 2
    def aussen(cs, winkel):
        m = m3.Manifold.extrude(cs, tiefe).rotate([90, 0, 0]).translate([0, -(R_TELLER - EINLAGE), 0])
        return m.rotate([0, 0, winkel + 90])
    for i in range(N_FELDER):
        a = 90 - i * 360 / N_FELDER
        am = a - 180 / N_FELDER
        teile.append(aussen(zahl(str(i + 1), H_ZAHL_RAND).translate([0, z_mitte]), am))
        linie = m3.CrossSection([[(-B_LINIE / 2, Z_TELLER_U + 0.4), (B_LINIE / 2, Z_TELLER_U + 0.4),
                                  (B_LINIE / 2, Z_OBEN - 1.0), (-B_LINIE / 2, Z_OBEN - 1.0)]])
        teile.append(aussen(linie, a))
    return m3.Manifold.batch_boolean(teile, m3.OpType.Add)  # roh, ragt 0,2 mm über den Rand


def teller():
    k = teller_koerper()
    ein = m3.Manifold.extrude(markierung_2d(), EINLAGE + 0.05).translate([0, 0, Z_OBEN - EINLAGE])
    roh = ein + rand_markierung(k)
    return k - roh, roh ^ k


def podest_druck():
    """Podest (Ø70 × 40) kopfüber + 8 Steckstifte Ø3 × 18 – ein Druck, Bett-Koordinaten."""
    r = PODEST_D / 2
    p = revolve([(0, 0), (r - 0.6, 0), (r, 0.6), (r, PODEST_H - 0.6), (r - 0.6, PODEST_H), (0, PODEST_H)])
    loecher = [(0, 0)] + [(12 * math.cos(math.radians(a)), 12 * math.sin(math.radians(a))) for a in range(0, 360, 60)] \
        + [(24 * math.cos(math.radians(a + 15)), 24 * math.sin(math.radians(a + 15))) for a in range(0, 360, 30)]
    for x, y in loecher:  # Oberseite liegt unten (z0): Löcher Ø3,3 × 10 für die Stifte
        p = p - m3.Manifold.cylinder(10.0, 1.65, 1.65, 24).translate([x, y, -0.01])
    for f in PODEST_FELDER:  # Steckzapfen nach oben (= später unten zum Teller)
        w = -feld_mitte(f)   # gespiegelt, weil kopfüber
        p = p + m3.Manifold.cylinder(2.8 + 0.01, STIFT_D / 2, STIFT_D / 2 - 0.3, 32).translate(
            [PODEST_STIFT_R * math.cos(w), PODEST_STIFT_R * math.sin(w), PODEST_H - 0.01])
    stift = revolve([(0, 0), (1.1, 0), (1.5, 0.4), (1.5, 17.6), (1.1, 18), (0, 18)])
    stifte = [stift.translate([r + 8 + (i % 4) * 7, -10.5 + (i // 4) * 7, 0]) for i in range(8)]
    return (p + m3.Manifold.batch_boolean(stifte, m3.OpType.Add)).translate([110, 128, 0])


def wuerfel():
    """Maßwürfel 20 mm, Ziffern 1–6 als schwarze Einlage – (weiß, schwarz) in Bett-Koordinaten."""
    a, t = 20.0, EINLAGE
    k = m3.Manifold.cube([a, a, a], True)
    seiten = [((0, 0, 0), 1), ((180, 0, 0), 6), ((90, 0, 0), 2), ((-90, 0, 0), 5), ((0, 90, 0), 3), ((0, -90, 0), 4)]
    roh = []
    for rot, n in seiten:
        e = m3.Manifold.extrude(zahl(str(n), 12.0), t + 0.2).translate([0, 0, a / 2 - t])
        roh.append(e.rotate(list(rot)))
    roh = m3.Manifold.batch_boolean(roh, m3.OpType.Add)
    w, s = k - roh, roh ^ k
    v = [128, 128, a / 2]
    return w.translate(v), s.translate(v)


def nach_trimesh(m):
    g = m.to_mesh()
    return trimesh.Trimesh(np.asarray(g.vert_properties)[:, :3], np.asarray(g.tri_verts), process=True)


def druck_kaefig_walzen():
    """Käfig flach + alle Walzen stehend im Innenraum des Käfigs (ein Druck)."""
    k = kaefig().translate([0, 0, -(Z_ACHSE - T_KAEFIG / 2)])
    w = walze()
    pos, n, a = [], 2 * N_TASCHEN, D_WALZE + 4.0
    for ix in range(-8, 9):
        for iy in range(-8, 9):
            x, y = ix * a, iy * a
            if math.hypot(x, y) < K_I - 8 and len(pos) < n:
                pos.append((x, y))
    assert len(pos) == n, len(pos)
    alles = k + m3.Manifold.batch_boolean([w.translate([x, y, 0]) for x, y in pos], m3.OpType.Add)
    return alles.translate([128, 128, 0])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ziel", default="modelle")
    ap.add_argument("--bild")
    ap.add_argument("--teller", type=float, default=2 * R_TELLER, help="Teller-Ø in mm")
    a = ap.parse_args()
    globals()["R_TELLER"] = a.teller / 2
    os.makedirs(a.ziel, exist_ok=True)
    s = sockel()
    vis = visier()
    weiss, schwarz = teller()
    k, w = kaefig(), walzen_gebrauch()
    def kopf(m):  # Teller: Oberseite nach unten, Bett-Koordinaten (für --zusammen)
        return m.rotate([180, 0, 0]).translate([128, 128, Z_OBEN])
    out = {
        "drehteller_sockel": s,
        "drehteller_kaefig_walzen": druck_kaefig_walzen(),
        "drehteller_teller_weiss": kopf(weiss),
        "drehteller_teller_schwarz": kopf(schwarz),
        "drehteller_visier": vis.rotate([0, 0, -VIS_WINKEL]).translate([0, 0, 0]),
        "drehteller_podest_stifte": podest_druck(),
        "drehteller_wuerfel_weiss": wuerfel()[0],
        "drehteller_wuerfel_schwarz": wuerfel()[1],
    }
    for n, m in out.items():
        t = nach_trimesh(m)
        t.export(os.path.join(a.ziel, n + ".stl"))
        b = t.bounds
        print(f"{n}: {len(t.faces)} Dreiecke, dicht={t.is_watertight}, Maße {np.round(b[1]-b[0],2)}, Vol {m.volume():.0f} mm³")
    teller_ganz = weiss + schwarz
    for name, x, y in [("weiß/schwarz", weiss, schwarz), ("Sockel/Teller", s, teller_ganz), ("Sockel/Käfig", s, k),
                       ("Teller/Käfig", teller_ganz, k), ("Walzen/Käfig", w, k), ("Walzen/Sockel", w, s), ("Walzen/Teller", w, teller_ganz),
                       ("Visier/Sockel", vis, s), ("Visier/Teller", vis, teller_ganz)]:
        print(f"Schnitt {name}: {(x ^ y).volume():.3f} mm³")
    print(f"Walzen: {2*N_TASCHEN} Stück Ø{D_WALZE} × {L_WALZE} mm, {N_TASCHEN} Taschen; Höhe gesamt {Z_OBEN} mm")
    if a.bild:
        bild(weiss, schwarz, s, k, w, a.bild, vis)


def bild(weiss, schwarz, s, k, w, pfad, vis=None):
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
    pl.add_mesh(pm(k.translate([0, 0, 25])), color="#e0a040")
    pl.add_mesh(pm(w.translate([0, 0, 25])), color="#5080c0")
    pl.camera_position = [(170, -330, 230), (0, 0, 20), (0, 0, 1)]
    if vis is not None:
        pl.add_mesh(pm(vis), color="#222222")
    pl.add_text("Sockel mit Visier, Käfig + Walzen (angehoben)", font_size=12)
    pl.screenshot(pfad)


if __name__ == "__main__":
    main()
