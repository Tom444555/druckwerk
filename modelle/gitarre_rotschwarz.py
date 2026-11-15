#!/usr/bin/env python3
"""gitarre_rotschwarz.py – eigene E-Gitarre als Schaustück (T-Form mit Cutaway, zwei Humbucker, 24 Bünde, sechs Mechaniken in Reihe).

Eigener Entwurf in der Optik von Toms Gitarre (Foto = Stilvorlage): rot-schwarz gemaserte Decke, Holzrand, schwarze Hardware.
Kein Nachbau eines Markenmodells: Umriss, Kopfplatte und Maserung sind selbst gezeichnet bzw. gerechnet, kein Schriftzug.

  python3 modelle/gitarre_rotschwarz.py [--laenge 200] [--saat 4] [--schwarz 0.40] [--ziel modelle]
  → modelle/gitarre_rotschwarz_{schwarz,rot,gold,weiss}.stl   (liegt mit dem Rücken flach auf dem Bett, Vorderseite oben, keine Stützen)

Aufbau wie bild_relief.py: 2D-Umrisse (manifold3d CrossSection) → Prismen; Farben überlappen nie (weiß vor schwarz vor rot vor gold).
Köpfe: 1 schwarz (Griffbrett, Hardware, dunkle Maserung) · 2 rot (Decke) · 3 gold (Holz: Korpus, Hals, Rand, Bundmarken) · 4 weiß (Bünde, Sattel, Regler, Polreihen).
Maße in mm bei Grundgröße (Gesamtlänge ca. 191); --laenge skaliert alles gleichmäßig.
"""
import argparse, sys
from pathlib import Path
import numpy as np
from scipy import ndimage, interpolate
import manifold3d as m3
import trimesh

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "werkzeug"))
from bild_relief import umriss

CS = m3.CrossSection; RUND = m3.JoinType.Round
D = 8.0            # Korpusdicke
T = 1.0            # Tiefe der Farbeinlagen in der Decke
MENSUR = 130.9     # Sattel bis Steg
Y_STEG = 20.5
Y_SATTEL = Y_STEG + MENSUR
Y_GB_ENDE = Y_SATTEL - MENSUR * 0.75 - 1.0         # Griffbrett endet knapp hinter dem 24. Bund
GB_H = 0.9         # Griffbrett steht über die Decke


def glatt(punkte, n=500):
    p = np.array(list(punkte) + [punkte[0]], float)
    tck, _ = interpolate.splprep(p.T, s=0, per=True)
    return np.stack(interpolate.splev(np.linspace(0, 1, n, endpoint=False), tck), 1)


def rechteck(b, h, r=0.0):
    c = CS.square((b, h)).translate((-b / 2, -h / 2))
    return c.offset(-r, RUND).offset(r, RUND) if r > 0 else c


def prisma(cs, z0, z1):
    cs = cs.offset(-0.006, m3.JoinType.Miter).simplify(0.004)   # Berührpunkte trennen, fast gerade Punktfolgen ausdünnen (sonst entartete Dreiecke)
    return cs.extrude(z1 - z0).translate((0, 0, z0)) if not cs.is_empty() else m3.Manifold()


def auf(cs, z0, z1, u=0.03):
    """Schicht, die auf einer gleichfarbigen Schicht sitzt: taucht 0,03 mm ein und ist 0,012 mm eingezogen,
    damit beide echt verschmelzen und keine deckungsgleichen Seitenwände entstehen (sonst hauchdünne Doppelflächen)."""
    return prisma(cs.offset(-0.012, m3.JoinType.Miter), z0 - u, z1)


def bund_y(n):
    return Y_SATTEL - MENSUR * (1 - 2 ** (-n / 12))


def hals_halb(y):                                    # halbe Griffbrettbreite
    return 4.25 + (5.75 - 4.25) * (Y_SATTEL - y) / (Y_SATTEL - Y_GB_ENDE)


def maserung(cs, saat, anteil, res=0.1):
    """Dunkle Maserung (fließende Flecken, längs gestreckt) innerhalb der Fläche cs → CrossSection."""
    (x0, y0, x1, y1) = cs.bounds()
    b, h = int((x1 - x0) / res) + 8, int((y1 - y0) / res) + 8
    rng = np.random.default_rng(saat)
    grob = ndimage.gaussian_filter(rng.standard_normal((h, b)), (42, 17))
    fein = ndimage.gaussian_filter(rng.standard_normal((h, b)), (15, 9))
    f = grob / grob.std() + 0.75 * fein / fein.std()
    yy, xx = np.mgrid[0:h, 0:b]
    vx = ndimage.gaussian_filter(rng.standard_normal((h, b)), 30); vy = ndimage.gaussian_filter(rng.standard_normal((h, b)), 30)
    f = ndimage.map_coordinates(f, [yy + 55 * vy / vy.std(), xx + 55 * vx / vx.std()], order=1, mode="reflect")
    m = f > np.quantile(f, 1 - anteil)
    m = ndimage.gaussian_filter(m.astype(np.float32), 4.5) > 0.5
    lab, n = ndimage.label(m)
    if n:
        gr = ndimage.sum(m, lab, range(1, n + 1)); m = np.isin(lab, np.where(gr >= 4.0 / res ** 2)[0] + 1)     # Flecken < 4 mm² weg
    c = umriss(m, res, h * res, 120000).translate((x0 - 4 * res, y0 - 4 * res))
    return c ^ cs


FARBE = {"schwarz": "#1b1b1d", "rot": "#b3121c", "gold": "#c9a24a", "weiss": "#ecebe6"}


def draufsicht(flaechen, pfad, laenge):
    """Farbige Draufsicht aus den 2D-Flächen (Reihenfolge = von unten nach oben)."""
    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.path import Path as MP
    from matplotlib.patches import PathPatch
    fig, ax = plt.subplots(figsize=(4.6, 10.4), dpi=170)
    for name, cs in flaechen:
        v, c = [], []
        for poly in cs.to_polygons():
            poly = np.asarray(poly)
            if len(poly) < 3: continue
            v += list(poly) + [poly[0]]; c += [MP.MOVETO] + [MP.LINETO] * (len(poly) - 1) + [MP.CLOSEPOLY]
        if v:
            ax.add_patch(PathPatch(MP(v, c), facecolor=FARBE[name], edgecolor="none"))
    ax.set_xlim(-40, 40); ax.set_ylim(-6, 200); ax.set_aspect("equal"); ax.axis("off")
    ax.set_title(f"Eigener Entwurf · {laenge:.0f} mm · schwarz / rot / gold / weiß", fontsize=9)
    fig.savefig(pfad, bbox_inches="tight", facecolor="white"); plt.close(fig)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--laenge", type=float, default=200.0); ap.add_argument("--saat", type=int, default=4)
    ap.add_argument("--schwarz", type=float, default=0.40, help="Anteil der dunklen Maserung in der Decke")
    ap.add_argument("--bild", help="Draufsicht in Farbe als PNG (Vorschau für Tom)")
    ap.add_argument("--ziel", default=str(Path(__file__).resolve().parent)); ap.add_argument("--name", default="gitarre_rotschwarz")
    a = ap.parse_args()

    # ---------------- Korpus (eigener Umriss, T-Form mit Cutaway rechts) ----------------
    korpus = CS([glatt([(0, 0), (12, 0.3), (23, 2.6), (30.3, 9), (33, 19), (31.2, 31), (27.8, 42), (27.2, 50), (29.6, 58), (31, 65),
                        (30.2, 70.5), (26.8, 74.2), (22.4, 73.6), (18.4, 69.6), (14.8, 64.8), (10.6, 61.6), (6.2, 61), (0, 64), (-6.3, 72.5),
                        (-12, 78.4), (-20, 80), (-27, 77.2), (-31, 70), (-32, 62), (-29.6, 53), (-27.6, 45), (-28.6, 36), (-32, 26),
                        (-33, 17), (-30, 8), (-22, 2.4), (-11, 0.3)])], m3.FillRule.NonZero)
    decke = korpus.offset(-1.2, RUND)                                         # Holzrand 1,2 mm um die Decke
    # ---------------- Hals, Griffbrett, Kopfplatte ----------------
    gb = CS([np.array([(-hals_halb(Y_GB_ENDE), Y_GB_ENDE), (hals_halb(Y_GB_ENDE), Y_GB_ENDE), (4.25, Y_SATTEL), (-4.25, Y_SATTEL)])], m3.FillRule.NonZero)
    hals = CS([np.array([(-hals_halb(60), 60), (hals_halb(60), 60), (4.25, Y_SATTEL + 1.5), (-4.25, Y_SATTEL + 1.5)])], m3.FillRule.NonZero)
    ks = Y_SATTEL + 0.7                                                       # Kopfplatte: sechs in Reihe, Mechaniken links, Spitze rechts oben
    kopf = CS([np.array([(-4.25, 0), (-6.6, 2.4), (-9.6, 6.5), (-9.9, 10), (-6.2, 19), (-1.6, 28), (3.4, 36), (7.4, 39.6), (9.4, 38.2),
                         (8.7, 30), (6.9, 18), (5.3, 8), (4.25, 0)]) + (0, ks)], m3.FillRule.NonZero)
    kopf = kopf.offset(-1.0, RUND).offset(2.0, RUND).offset(-1.0, RUND)       # Ecken runden
    kopf_fl = kopf.offset(-0.8, RUND) - rechteck(12, 3.0).translate((0, ks + 0.5))   # rote Fläche, am Sattel bleibt Holz
    HK = 6.2                                                                  # Kopfplatte liegt tiefer als das Griffbrett
    # Mechaniken: Achsen auf der Fläche, Flügel links außen
    mech = [np.array([-6.6, ks + 7.5]) + i * np.array([2.35, 4.75]) for i in range(6)]
    achsen = CS.batch_boolean([CS.circle(0.95, 32).translate(tuple(p)) for p in mech], m3.OpType.Add)
    fluegel = CS.batch_boolean([rechteck(3.6, 2.6, 0.7).rotate(-26).translate(tuple(p + np.array([-3.9, 1.9]))) + rechteck(3.4, 1.0).rotate(-26).translate(tuple(p + np.array([-2.0, 0.95])))
                                for p in mech], m3.OpType.Add)
    # ---------------- Hardware auf der Decke ----------------
    def tonabnehmer(y):
        rahmen = rechteck(16.0, 8.0, 0.9).translate((0, y))
        spulen = (rechteck(13.0, 2.2, 0.3).translate((0, y + 1.45)) + rechteck(13.0, 2.2, 0.3).translate((0, y - 1.45)))
        pole = (rechteck(10.6, 0.8).translate((0, y + 1.45)) + rechteck(10.6, 0.8).translate((0, y - 1.45)))
        return rahmen, spulen, pole
    ta = [tonabnehmer(46.0), tonabnehmer(31.0)]
    rahmen = ta[0][0] + ta[1][0]; spulen = ta[0][1] + ta[1][1]; pole = ta[0][2] + ta[1][2]
    steg = rechteck(15.0, 7.0, 0.7).translate((0, Y_STEG - 1.0))
    reiter = CS.batch_boolean([rechteck(1.7, 3.4, 0.3).translate(((i - 2.5) * 2.2, Y_STEG - 0.4)) for i in range(6)], m3.OpType.Add)
    regler = CS.circle(2.2, 48).translate((16.5, 18.0)) + CS.circle(2.2, 48).translate((20.8, 9.6))
    schalter = rechteck(6.0, 1.2, 0.5).rotate(-58).translate((17.0, 28.5)); schaltknopf = CS.circle(0.8, 24).translate((16.2, 29.8))
    gurt = rechteck(2.6, 3.0, 0.8).translate((0, -0.6)) + rechteck(2.6, 3.0, 0.8).rotate(20).translate((-22.6, 80.6))
    # Bünde und Bundmarken
    def quer(y, hoch):                                                       # Streifen quer über das Griffbrett
        return rechteck(13.0, hoch).translate((0, y)) ^ gb
    buende = CS.batch_boolean([quer(bund_y(n), 0.5) for n in range(1, 25)], m3.OpType.Add)
    sattel = rechteck(8.5, 0.9).translate((0, Y_SATTEL + 0.45))
    marken = []
    for n in (3, 5, 7, 9, 12, 15, 17, 19, 21, 24):
        ym = (bund_y(n) + bund_y(n - 1)) / 2; luft = (bund_y(n - 1) - bund_y(n)) - 0.5    # Platz zwischen zwei Bünden
        hoch = min(2.4, luft - 1.4) if luft >= 3.4 else luft - 0.04                       # enge Bünde: Marke füllt das Feld (kein dünner Steg)
        for dx in ((-1.5, 1.5) if n in (12, 24) else (0,)):
            marken.append(rechteck(1.5, hoch).translate((dx, ym)))
    marken = CS.batch_boolean(marken, m3.OpType.Add)

    # ---------------- Flächenaufteilung (alles in 2D, 0,02 mm Fuge → keine gemeinsamen Kanten, keine Splitter) ----------------
    F = lambda c: c.offset(0.02, m3.JoinType.Miter)
    def sauber(c, amin=0.4):                                                 # Inselchen unter 0,4 mm² entfernen (sonst lose Splitter)
        gut = [q for q in c.decompose() if q.area() >= amin]
        return CS.batch_boolean(gut, m3.OpType.Add) if gut else CS()
    oeffnen = lambda c, r=0.3: sauber(c.offset(-r, RUND).offset(r, RUND), 1.3)   # Maserung: Inseln ab 1,3 mm²
    rahmen2 = rahmen - F(spulen)
    belegt = gb + rahmen + steg + regler + schalter
    frei = decke - F(belegt)
    dunkel = oeffnen(maserung(frei, a.saat, a.schwarz))
    rot2d = oeffnen(frei - F(dunkel)); dunkel = oeffnen(frei - F(rot2d), 0.24); rot2d = sauber(frei - F(dunkel))               # Rot zuerst sauber, Dunkel füllt den Rest
    keil = lambda c: sauber(c.offset(-0.12, RUND).offset(0.12, RUND))        # spitze Keile an Stoßstellen kappen
    rand = keil((korpus.offset(-0.04, RUND) - F(decke)) - F(gb))   # 0,04 mm eingezogen: keine fast deckungsgleichen Wände
    #                                       # Holzrand um die Decke
    kfl = kopf_fl - F(achsen)
    kdunkel = oeffnen(maserung(kfl, a.saat + 1, a.schwarz))
    krot = oeffnen(kfl - F(kdunkel)); kdunkel = oeffnen(kfl - F(krot), 0.24); krot = sauber(kfl - F(kdunkel))
    krand = keil(kopf.offset(-0.04, RUND) - F(kopf_fl))
    fluegel = sauber(fluegel - F(kopf)); gurt = sauber(gurt - F(korpus))
    gb_oben = sauber(gb - F(buende + marken))
    spulen_oben = sauber(spulen - F(pole)); rahmen2 = sauber(rahmen2)

    # ---------------- Körper je Farbe (nur Vereinigungen, nie Abziehen in 3D) ----------------
    Z = D; ZG = Z + GB_H
    teile = {
        "schwarz": [prisma(dunkel, Z - T, Z), prisma(kdunkel, HK - 0.8, HK), prisma(gb, Z - T, ZG - 0.6), auf(gb_oben, ZG - 0.6, ZG),
                    prisma(rahmen2, Z - T, Z + 0.9), prisma(steg, Z - T, Z + 1.4), auf(reiter, Z + 1.4, Z + 1.9),
                    prisma(schalter, Z - T, Z + 0.3), auf(schaltknopf, Z + 0.3, Z + 1.7), prisma(achsen, HK - 0.8, HK + 1.3),
                    prisma(fluegel, 0, 3.0), prisma(gurt, 0, 4.6)],
        "rot": [prisma(rot2d, Z - T, Z), prisma(krot, HK - 0.8, HK), prisma(spulen, Z - T, Z + 0.7), auf(spulen_oben, Z + 0.7, Z + 1.1)],
        "gold": [prisma(korpus.offset(-0.4, RUND), 0, 0.4), auf(korpus, 0.4, Z - T), auf(rand, Z - T, Z),
                 prisma(hals.offset(-0.4, RUND), 0, 0.4), auf(hals, 0.4, Z - T),
                 prisma(kopf.offset(-0.4, RUND), 0, 0.4), auf(kopf, 0.4, HK - 0.8), auf(krand, HK - 0.8, HK),
                 prisma(marken, ZG - 0.6, ZG)],
        "weiss": [prisma(buende, ZG - 0.6, ZG), prisma(sattel, Z - T, ZG + 0.3), prisma(regler, Z - T, Z + 2.4), prisma(pole, Z + 0.7, Z + 1.1)],
    }
    M = m3.Manifold
    vereint = lambda l: M.batch_boolean([k for k in l if not k.is_empty()], m3.OpType.Add)
    koerper = {n: vereint(l) for n, l in teile.items()}
    flaechen = [("gold", korpus + hals + kopf), ("schwarz", fluegel + gurt + dunkel + kdunkel + gb_oben + rahmen2 + steg + schalter + achsen),
                ("rot", rot2d + krot + spulen_oben), ("gold", marken), ("weiss", buende + sattel + regler + pole)]

    # ---------------- Skalieren, ausgeben, prüfen ----------------
    alle = vereint(list(koerper.values())); bb = alle.bounding_box()
    if a.bild:
        draufsicht(flaechen, a.bild, a.laenge)
    f = a.laenge / (bb[4] - bb[1])
    ziel = Path(a.ziel); ziel.mkdir(parents=True, exist_ok=True)
    print(f"Grundlänge {bb[4] - bb[1]:.1f} mm → Faktor {f:.3f}")
    for n, k in koerper.items():
        k = k.translate((-(bb[0] + bb[3]) / 2, -bb[1], 0)).scale((f, f, f))
        me = k.to_mesh(); t = trimesh.Trimesh(me.vert_properties[:, :3], me.tri_verts, process=True)
        p = ziel / f"{a.name}_{n}.stl"; t.export(p)
        print(f"{p.name}: dicht={t.is_watertight}, {t.volume / 1000:.2f} cm³, {len(t.faces)} Dreiecke, Teile {len(k.decompose())}, Maße {np.round(t.extents, 1).tolist()}")


if __name__ == "__main__":
    main()
