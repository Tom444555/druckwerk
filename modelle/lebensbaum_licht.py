#!/usr/bin/env python3
"""Lebensbaum-Lichtbild – stehendes, gebogenes Relief in Weiß für die 0,4-mm-Düse (Eigenentwurf).

Idee: Das Relief wird STEHEND gedruckt. So bildet jede 0,12-mm-Schicht die Tiefe als Kontur ab –
viel feiner als ein liegendes Relief (Prinzip Lithophanie). Der Bogen macht die dünne Wand steif
und lässt sie von selbst stehen. Mit Licht dahinter (LED-Teelicht) leuchten Himmel, Mond und Sterne,
der Baum steht dunkel davor.

Baum-Wachstum aus werkzeug/baum_relief.py übernommen (ohne Gitarren-Gabel).
Stützfrei: Überhänge werden rechnerisch auf höchstens UEBERHANG Grad begrenzt (Fase unter jedem Vorsprung).

Aufruf:  python3 modelle/lebensbaum_licht.py [--saat 6] [--nur-bild v.png] [--ziel modelle]
"""
import math, argparse
import numpy as np
from scipy import ndimage

hals_b = 10.4; sattel_h = 160; luft_unten = 10; fuss_d = 4.0
zg = fuss_d + luft_unten + sattel_h; gabel_z = zg - 22        # Ende des Leitasts (Maß aus dem Ständer)
RES = 0.16; X0, X1, Z0, Z1 = -97.0, 97.0, 0.0, 182.0
HMAX = 5.3
KA, KB, KZ = 86.0, 105.0, 72.0
H_ADER = 3.4; H_BLATT = 3.1
FUSS_B = 95.0       # Wurzeln dürfen fast bis zum Rahmen laufen

# ---- Lichtbild ----
BASIS = 1.5          # Wandstärke des Himmels (leuchtet)
MOND = 0.85          # dünnste Stelle (zwei Bahnen)
RAND_B, RAND_H = 2.6, 1.9      # Rahmen: Breite, Höhe über dem Himmel
RADIUS = 130.0       # Biegeradius der Rückseite
UEBERHANG = 55.0     # größter Überhang in Grad gegen die Senkrechte


# ---- Endlos-Schleife aus zwei Wurzelsträngen, Namen in den beiden Schlaufen ----
NAMEN = ("Thomas", "Sandra")
LA, LZ, LK = 57.0, 15.4, 0.66          # halbe Breite, Mitte (Höhe), Stauchung in der Höhe
STRICH = 0.6                           # Strichbreite der Namen (feiner löst die 0,4-mm-Düse nicht auf)
SCHRIFTEN = ["/usr/share/texmf/fonts/opentype/public/tex-gyre/texgyrechorus-mediumitalic.otf", "/usr/share/texmf/fonts/opentype/public/tex-gyre/texgyrepagella-bolditalic.otf",
             "/usr/share/fonts/truetype/dejavu/DejaVuSerif-BoldItalic.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"]

def schleife(t):                       # Lemniskate (liegende Acht)
    c = math.cos(t); s_ = math.sin(t); d = 1 + s_ * s_
    return LA * c / d, LZ + LK * LA * s_ * c / d

def in_schleife(x, z, f=1.0):          # innerhalb einer der beiden Schlaufen? (geht auch mit Feldern)
    Z = (z - LZ) / LK; q = x * x + Z * Z
    return q * q < f * LA * LA * (x * x - Z * Z)


def baum(saat):
    rng = np.random.default_rng(saat)
    nx = int(round((X1 - X0) / RES)) + 1; nz = int(round((Z1 - Z0) / RES)) + 1
    xs = X0 + np.arange(nx) * RES; zs = Z0 + np.arange(nz) * RES
    hw = np.full((nz, nx), -0.5, np.float32)        # Holzhöhe
    mu = np.zeros((nz, nx), np.float32); ms = np.zeros((nz, nx), np.float32); mr = np.zeros((nz, nx), np.float32)
    mg = np.zeros((nz, nx), bool)                   # „leuchtende“ feine Zweige/Wurzeln (zweite Farbe)
    hl = np.full((nz, nx), -0.5, np.float32)        # Blatthöhe
    belegt = np.zeros((int(Z1 / 2) + 2, 100), np.float32)                     # grobe Belegung (2 mm)

    def H(r): return min(HMAX, 1.1 + 1.15 * r)

    def stempel(x, z, th, r, s, hmax=None, gold=False):
        Hh = H(r) if hmax is None else hmax
        i0 = max(0, int((x - r - X0) / RES)); i1 = min(nx, int((x + r - X0) / RES) + 2)
        j0 = max(0, int((z - r - Z0) / RES)); j1 = min(nz, int((z + r - Z0) / RES) + 2)
        if i0 >= i1 or j0 >= j1: return
        dx = xs[i0:i1][None, :] - x; dz = zs[j0:j1][:, None] - z
        d2 = dx * dx + dz * dz; m = d2 < r * r
        h = 0.6 + (Hh - 0.6) * np.sqrt(np.clip(1 - d2 / (r * r), 0, 1))
        sub = hw[j0:j1, i0:i1]; m &= h > sub
        sub[m] = h[m]
        u = dx * math.cos(th) - dz * math.sin(th); v = dx * math.sin(th) + dz * math.cos(th)
        mu[j0:j1, i0:i1][m] = u[m]; ms[j0:j1, i0:i1][m] = (s + v)[m]; mr[j0:j1, i0:i1][m] = r; mg[j0:j1, i0:i1][m] = gold
        bj = int(z / 2); bi = int((x + 100) / 2)
        if 0 <= bj < belegt.shape[0] and 0 <= bi < 100: belegt[bj, bi] += r

    def innen(x, z):                                # breite Kuppel mit flacher Unterkante und unruhigem Rand
        if not (55 < z < 179.5): return False
        w = KA + 4 * math.sin(z / 7.0)
        return abs(x) < w if z < KZ else (x / w) ** 2 + ((z - KZ) / (KB + 3 * math.sin(x / 11.0))) ** 2 < 1

    def frei(x, z, th, weit=12):
        t = 0.0
        for d in (4, 8, weit):
            px = x + math.sin(th) * d; pz = z + math.cos(th) * d
            if not innen(px, pz): t += 8; continue
            bj = int(pz / 2); bi = int((px + 100) / 2); t += belegt[max(0, bj - 1):bj + 2, max(0, bi - 1):bi + 2].sum()
        return t

    zu, zo, P = 21.5, 58.0, 40.0                                               # Stamm: unten, oben, Windungslänge
    blaetter = []

    def blatt(x, z, th, gross=1.0):
        if z < zo + 3: return
        blaetter.append((x, z, th, rng.uniform(4.0, 6.2) * gross, rng.uniform(1.3, 2.6), rng.uniform(-0.5, 0.5), rng.uniform(-0.25, 0.25)))

    def wachse(x, z, th, r, wurzel=False, lang=1.0):
        stapel = [(x, z, th, r, lang)]
        while stapel:
            x, z, th, r, lg = stapel.pop()
            L = (8.0 if wurzel else 6.8) * r ** 0.75 * rng.uniform(0.75, 1.3) * lg; s = rng.uniform(0, 500); n = int(L / 0.4)
            zziel = rng.uniform(4.5, 19.0) if wurzel else 0.0                    # jede Wurzel sucht ihre eigene Tiefe -> Stränge trennen sich
            seite = 1 if rng.random() < 0.5 else -1; naechst = rng.uniform(1.5, 3.5); tot = False; trieb = rng.uniform(1, 4); gedreht = 0.0
            for k in range(n):
                th += rng.normal(0, 0.055 / math.sqrt(r))
                if wurzel:                                                     # Wurzeln kriechen flach am Boden entlang
                    soll = min(2.25, max(1.25, 1.66 + 0.07 * (z - zziel)))               # oben eher abwärts, unten eher flach
                    th += 0.05 * (math.copysign(soll, th) - th)
                    nah = min((FUSS_B - abs(x)) / 34.0, (z - 0.6) / 6.0, 1.0)          # zum Rand und zum Boden hin spitz auslaufen
                    if nah < 1: r *= 0.9815 + 0.017 * max(nah, 0.0)
                    if z < 0.7 or z > 37 or abs(x) > FUSS_B - 0.6 or r < 0.24 or in_schleife(x, z): tot = True; break
                else:
                    th -= (0.0 if r > 1.3 else 0.004) * th                    # dicke Äste laden aus, dünne streben nach oben
                    ax = x + math.sin(th) * 5; az = z + math.cos(th) * 5
                    if not innen(ax, az):
                        zur = math.atan2(-x, KZ + 35 - z); dth = (zur - th + math.pi) % (2 * math.pi) - math.pi
                        th += 0.07 * np.sign(dth); gedreht += 0.07
                        if r < 0.9 or gedreht > 1.3: tot = True; break
                    if not innen(x, z): tot = True; break
                x += math.sin(th) * 0.4; z += math.cos(th) * 0.4; s += 0.4; r *= 0.9985
                ader = (r < 0.95) if wurzel else (0.6 <= r < 1.1)
                rr = r * (1 + 0.09 * math.sin(s * 0.9) + 0.05 * math.sin(s * 2.3)) if r > 0.8 else r
                stempel(x, z, th, rr, s, hmax=(min(HMAX, 0.85 + 1.0 * rr) if wurzel else (H_ADER if ader else None)), gold=ader)
                if not wurzel and 0.6 < r < 1.8:                                # Kurztriebe: viele kleine Zweige mit Laub
                    trieb -= 0.4
                    if trieb <= 0:
                        trieb = rng.uniform(2.2, 4.2); stapel.append((x, z, th + rng.choice([-1, 1]) * rng.uniform(0.5, 1.2), rng.uniform(0.46, 0.58), rng.uniform(1.0, 1.8)))
                if not wurzel and r < 0.85:
                    naechst -= 0.4
                    if naechst <= 0:
                        naechst = rng.uniform(1.8, 3.2); seite = -seite
                        if rng.random() < 0.85: blatt(x, z, th + seite * rng.uniform(0.6, 1.1), 0.9)
            if wurzel:
                if tot or r < 0.30: continue
            elif tot or r < 0.52:
                blatt(x, z, th + rng.uniform(-0.25, 0.25))
                for sd in (-1, 1):
                    if rng.random() < 0.8: blatt(x, z, th + sd * rng.uniform(0.6, 1.0), 0.85)
                continue
            f = rng.uniform(0.10, 0.28) if wurzel else rng.uniform(0.24, 0.5); r1 = r * math.sqrt(1 - f); r2 = r * math.sqrt(f)
            beste = None
            for _ in range(6):
                sd = rng.choice([-1, 1]); a1 = -sd * math.radians(rng.uniform(6, 22)) * (f / 0.5 + 0.3)
                a2 = sd * math.radians(rng.uniform(30, 58))
                w = (0 if wurzel else frei(x, z, th + a1) + frei(x, z, th + a2))
                if beste is None or w < beste[0]: beste = (w, a1, a2)
            stapel.append((x, z, th + beste[1], r1, 1.0))
            if r2 > 0.38: stapel.append((x, z, th + beste[2], r2, 1.0))

    # ---- Stamm: Stränge winden sich umeinander, unten werden sie zu Wurzeln, oben zu Ästen ----
    def mitte(z): return 6.5 * math.sin(math.pi * min(1.0, max(0.0, (z - zu) / (zo - zu)))) if z < zo else 0.0   # geschwungener Stamm
    def amp(z):
        t = (z - (zu + zo) / 2) / ((zo - zu) / 2); return 4.6 + (3.6 if t > 0 else 5.0) * abs(t) ** 3
    def sx(z, ph): return mitte(z) + amp(z) * math.sin(2 * math.pi * (z - zo) / P + ph)
    for pos, r, ziel in [(-0.97, 3.0, -86), (-0.62, 2.9, -60), (-0.27, 2.6, -32), (0.27, 2.6, 30), (0.62, 2.9, 58), (0.97, 3.0, 84)]:
        ph = math.asin(pos); z = zu; s = rng.uniform(0, 300); pts = []
        while z <= zo + 0.01:
            x = sx(z, ph); th = math.atan2(sx(z + 0.3, ph) - x, 0.3)
            stempel(x, z, th, r * (1 + 0.08 * math.sin(s * 0.8)), s, hmax=min(HMAX, 3.6 + 1.7 * math.cos(2 * math.pi * (z - zo) / P + ph)))
            pts.append((x, z, th)); z += 0.3; s += 0.35
        x, z, th = pts[-1]; wachse(x, z, 0.25 * th + 0.75 * math.radians(ziel), r, lang=1.6)
        x, z, th = pts[0]
        if False: wachse(x, z, math.copysign(math.radians(100 + rng.uniform(0, 25)), x if abs(x) > 1 else rng.choice([-1, 1])), r * 0.95, wurzel=True, lang=1.5)
    for k in (0, 1):                                                           # Leitast: zwei Stränge bis zur Gabel
        z = zu - 6; s = rng.uniform(0, 300)
        while z <= gabel_z + 2:
            arg = 2 * math.pi * z / 38.0 + k * math.pi; a_ = 2.1 + 3.0 * math.exp(-max(z - 4, 0) / 6.0); x = mitte(z) + a_ * math.sin(arg)
            th = math.atan2(a_ * math.cos(arg) * 2 * math.pi / 38.0, 1.0); r = 2.6 - 0.5 * max(0, z - zo) / (gabel_z - zo)
            stempel(x, z, th, r * (1 + 0.07 * math.sin(s * 0.7)), s, hmax=min(HMAX, 3.9 + 1.4 * math.cos(arg))); z += 0.3; s += 0.33
    for sd_ in (-1, 1): wachse(sd_ * 1.2, gabel_z + 1, sd_ * math.radians(14 + rng.uniform(0, 10)), 1.9, lang=1.2)
    s0 = 1 if rng.random() < 0.5 else -1
    for i, (zz, rr) in enumerate([(78, 2.2), (93, 2.1), (107, 2.0), (120, 1.85), (132, 1.7), (142, 1.55), (149, 1.4)]):
        sd = s0 * (1 if i % 2 == 0 else -1); wachse(sd * 2.5, zz + rng.uniform(-2, 2), sd * math.radians(72 - 6 * i + rng.uniform(-8, 8)), rr, lang=1.3)
    # ---- Wurzeln: zwei Stränge legen sich zur Endlos-Schleife (über/unter gekreuzt), außen laufen sie zum Rand aus ----
    # Die Schleife ist kein glatter Ring: zwei Stränge sind wie ein Tau umeinander gedreht (wie der Stamm – zwei Leben, ein Seil),
    # liegen abwechselnd vorn und hinten, werden mal dicker, mal dünner, und an der Kreuzung läuft ein Paar über das andere.
    n_ = 5000; tt_ = 2 * math.pi * np.arange(n_ + 1) / n_; pk = np.array([schleife(v) for v in tt_])
    pk[:, 1] += 0.5 * np.sin(3 * tt_ + 0.7) * np.abs(np.cos(tt_))                # leicht unregelmäßig, nicht wie mit dem Zirkel
    bog = np.concatenate([[0], np.cumsum(np.hypot(*np.diff(pk, axis=0).T))]); om = 2 * math.pi * round(bog[-1] / 11.5) / bog[-1]
    for k in (0, 1):
        s_ = rng.uniform(0, 300)
        for q in range(n_):
            x, z = pk[q]; dx, dz = pk[q + 1] - pk[q]; l_ = math.hypot(dx, dz) or 1e-9; ph = om * bog[q] + k * math.pi
            ab = 1.3 * math.sin(ph); th = math.atan2(dx, dz) + 0.35 * math.cos(ph)
            stempel(x + ab * dz / l_, z - ab * dx / l_, th, 1.3 * (1 + 0.12 * math.sin(s_ * 0.5) + 0.06 * math.sin(s_ * 1.7)), s_,
                    hmax=2.5 + 0.95 * math.cos(ph) + 0.75 * math.sin(tt_[q])); s_ += l_
    for sd in (-1, 1):
        for t0, r0 in [(0.0, 2.3), (0.2, 2.0), (-0.2, 2.0), (0.4, 1.7), (-0.4, 1.7), (0.6, 1.4), (-0.62, 1.5), (0.85, 1.2), (-0.9, 1.3)]:
            x, z = schleife(t0); dx = x - 0.62 * LA; dz = (z - LZ) / LK; n0 = math.hypot(dx, dz) or 1.0
            wachse(sd * (x + 2.2 * dx / n0), z + 2.2 * dz / n0, sd * math.atan2(dx, dz), r0 * rng.uniform(0.9, 1.1), wurzel=True, lang=1.4)

    # ---- Borke: Furchen längs des Astes, Platten, feine Risse ----
    tex = ndimage.zoom(rng.random((96, 96)).astype(np.float32), 8, order=3, mode="wrap")
    def rausch(a_, b_): return ndimage.map_coordinates(tex, [(a_ * 8) % 760, (b_ * 8) % 760], order=1, mode="wrap")
    staerke = np.clip((mr - 0.7) / 1.6, 0, 1) * 0.65
    n1 = rausch(ms / 8.0 + mr * 3.1, mu / 1.15 + 40); n2 = rausch(ms / 3.2 + 11, mu / 0.62 + 7); n3 = rausch(ms / 1.6 + 5, mu / 2.4 + 90)
    furche = np.exp(-((n1 - 0.5) / 0.075) ** 2) + 0.45 * np.exp(-((n2 - 0.5) / 0.09) ** 2) + 0.3 * np.exp(-((n3 - 0.5) / 0.05) ** 2)
    schuppe = (rausch(ms / 5.0 + 70, mu / 1.6 + 3) - 0.5) * 0.5
    hw = np.where(hw > 0, np.maximum(0.6, hw - staerke * (furche - schuppe)), hw).astype(np.float32)

    # ---- Blätter: klein, spitz-oval, entlang der Mittelrippe gefaltet, mit Seitenadern ----
    for (x, z, th, L, h0, neig, kr) in blaetter:
        stiel = 0.5; cx = x + math.sin(th) * stiel; cz = z + math.cos(th) * stiel; W = L * rng.uniform(0.42, 0.52)
        R = L + 1; i0 = max(0, int((cx - R - X0) / RES)); i1 = min(nx, int((cx + R - X0) / RES) + 2)
        j0 = max(0, int((cz - R - Z0) / RES)); j1 = min(nz, int((cz + R - Z0) / RES) + 2)
        if i0 >= i1 or j0 >= j1: continue
        dx = xs[i0:i1][None, :] - cx; dz = zs[j0:j1][:, None] - cz
        t = (dx * math.sin(th) + dz * math.cos(th)) / L; v = dx * math.cos(th) - dz * math.sin(th)
        v = v - kr * L * 4 * t * (1 - t) * 0.25
        tt = np.clip(t, 0, 1); halb = W / 2 * np.sin(math.pi * tt ** 0.72) ** 0.85 * (1 - 0.25 * tt)
        m = (t > 0) & (t < 1) & (np.abs(v) < halb)
        q = np.clip(np.abs(v) / np.maximum(halb, 1e-3), 0, 1)
        h = h0 + neig * (tt - 0.5) + 0.42 * q - 0.3 * np.clip(q - 0.8, 0, 1) / 0.2
        h -= 0.32 * np.exp(-(v / 0.22) ** 2)
        ader = np.cos(2 * math.pi * (tt * L - np.abs(v) * 1.1) / 1.05)
        h -= 0.22 * np.clip(ader - 0.55, 0, 1) / 0.45 * (q < 0.9)
        h = np.clip(h, 0.7, H_BLATT); sub = hl[j0:j1, i0:i1]; m &= h > sub; sub[m] = h[m]
    return xs, zs, hw, hl, len(blaetter)


def bild(saat):
    xs, zs, hw, hl, nb = baum(saat); rng = np.random.default_rng(saat + 1000)
    gx, gz = np.meshgrid(xs, zs)
    rel = np.maximum(np.maximum(hw, hl), 0).astype(np.float32)             # Baum über dem Himmel
    frei = ndimage.distance_transform_edt(rel <= 0) * RES                      # Abstand zum Baum (mm)
    t = BASIS + rel
    # Boden: sanfte Hügel mit Gras-Riefen
    gh = 14.5 + 2.2 * np.sin(gx / 23.0 + 0.6) + 1.2 * np.sin(gx / 9.0 + 2.0)   # Bodenlinie: Wurzeln liegen sichtbar darunter
    gras = 0.55 + 0.22 * np.sin(gx / 0.9 + 3 * np.sin(gz / 2.3)) * np.clip((gh - gz) / 3.0, 0, 1)
    boden = np.clip((gh - gz) / 0.5, 0, 1) * gras
    t = np.maximum(t, BASIS + boden)
    # Schlaufen innen glatt, darin die Namen als dünne Stellen (im Auflicht vertieft, mit Licht dahinter leuchtend)
    innen = in_schleife(gx, gz) & (rel <= 0); t = np.where(innen, BASIS, t)
    platz = ndimage.distance_transform_edt(innen) * RES > 1.5
    from PIL import Image, ImageDraw, ImageFont, ImageFilter
    import os
    schrift = next(f for f in SCHRIFTEN if os.path.exists(f))
    # Ultrafeine Schrift: Kanzlei-Kursive auf ihre Mittellinie reduziert (ein Strich, STRICH mm breit). Von jedem Namen
    # läuft ein Haarstrich nach außen und nach innen in den Wurzelstrang – die Schleife "schreibt" beide Namen in einem Zug.
    from skimage.morphology import skeletonize
    F = 4; fe = RES / F; hz = int(34.0 / fe); hx = t.shape[1] * F                # feines Raster nur für den Wurzelbereich
    def linie(name, q):
        ft = ImageFont.truetype(schrift, q); l, o, r_, u = ft.getbbox(name); w = r_ - l + 12; h = u - o + 12
        im = Image.new("L", (w, h), 0); ImageDraw.Draw(im).text((6 - l, 6 - o), name, fill=255, font=ft)
        return skeletonize(np.array(im)[::-1] > 128)
    def lage(sk, sd):
        h, w = sk.shape; ys, xs_ = np.nonzero(sk)
        for dx in (0.0, -1.5, 1.5, -3.0, 3.0):
            for dz in (0.0, -0.8, 0.8, -1.6, 1.6):
                i0 = int(round((sd * 0.60 * LA + dx - X0) / fe - w / 2)); j0 = int(round((LZ + dz - Z0) / fe - h / 2))
                jj = (j0 + ys) // F; ii = (i0 + xs_) // F
                if jj.min() >= 0 and ii.min() >= 0 and platz[jj, ii].all(): return i0, j0
        return None
    q = next(q for q in range(520, 120, -10) if all(lage(linie(n_, q), sd) for n_, sd in zip(NAMEN, (-1, 1))))
    fein = np.zeros((hz, hx), bool)
    for name, sd in zip(NAMEN, (-1, 1)):
        sk = linie(name, q); i0, j0 = lage(sk, sd); h, w = sk.shape; fein[j0:j0 + h, i0:i0 + w] |= sk
        ys, xs_ = np.nonzero(sk)
        for ende, ziel in ((xs_.argmin(), -1), (xs_.argmax(), 1)):                # Haarstriche zu beiden Seiten
            ax = X0 + (i0 + xs_[ende]) * fe; az = Z0 + (j0 + ys[ende]) * fe
            aussen = (ziel == sd); bx = sd * (LA - 0.5) if aussen else sd * 3.0; bz = LZ
            u = np.linspace(0, 1, 1500); lx = ax + (bx - ax) * u; lz = az + (bz - az) * u ** (1.6 if aussen else 1.3) + (1.1 if aussen else 0.7) * np.sin(2 * math.pi * u) * (1 - u)
            fein[np.clip(((lz - Z0) / fe).astype(int), 0, hz - 1), np.clip(((lx - X0) / fe).astype(int), 0, hx - 1)] = True
    rr_ = int(round(STRICH / 2 / fe)); yy, xx = np.mgrid[-rr_:rr_ + 1, -rr_:rr_ + 1]
    dick = ndimage.binary_dilation(fein, structure=(yy * yy + xx * xx <= rr_ * rr_))
    alpha = dick[:hz // F * F, :].reshape(hz // F, F, -1, F).mean((1, 3)).astype(np.float32)   # weiche Kante
    nzr = alpha.shape[0]; sub = t[:nzr]; maske = innen[:nzr] & (alpha > 0)
    sub[maske] = (BASIS - (BASIS - MOND) * alpha)[maske]
    print(f"Namen: Kursive {q * fe * 0.7:.1f} mm hoch, Strich {STRICH} mm", flush=True)
    # Mond: helle Sichel mit Kratern und Meeren, dunkle Seite schwach durchscheinend (Erdschein), feiner Ring
    mx, mz, mr = -72.0, 158.5, 14.5
    d1 = np.hypot(gx - mx, gz - mz); d2 = np.hypot(gx - (mx + 7.0), gz - (mz + 3.0))
    hell = np.clip((d2 - (mr - 1.2)) / 0.7, 0, 1)                             # 1 = Sichel, 0 = dunkle Seite, weicher Übergang
    rm = np.random.default_rng(77)
    meer = ndimage.gaussian_filter(rm.random(gx.shape).astype(np.float32), 9.0); meer = (meer - meer.mean()) / meer.std()
    tm = (MOND + 0.42 * (1 - hell)) + 0.16 * np.clip(meer, 0, 1.5) * (0.4 + 0.6 * hell)
    for _ in range(26):                                                       # Krater: Wall + Mulde + kleiner Zentralberg
        w = rm.uniform(0, 2 * math.pi); a_ = mr * math.sqrt(rm.uniform(0, 0.92)); cr = rm.choice([0.7, 1.0, 1.4, 2.0, 2.7], p=[0.3, 0.3, 0.2, 0.13, 0.07])
        dd = np.hypot(gx - (mx + a_ * math.cos(w)), gz - (mz + a_ * math.sin(w)))
        tm += 0.30 * np.exp(-((dd - cr) / 0.24) ** 2) - 0.10 * (dd < cr - 0.2) * (1 - hell) + (0.18 * np.exp(-(dd / 0.3) ** 2) if cr > 1.8 else 0)
    tm += 0.25 * np.clip((d1 - (mr - 0.9)) / 0.9, 0, 1) ** 2                   # Randverdunklung: die Kugel wirkt rund
    tm = np.clip(tm, MOND, BASIS + 0.25)
    scheibe = (d1 < mr) & (rel <= 0); ring = (d1 >= mr) & (d1 < mr + 0.75) & (rel <= 0)
    t = np.where(scheibe, tm, t); t = np.where(ring, BASIS + 0.45, t)
    # Sterne: kleine Mulden im freien Himmel
    n = 0
    for _ in range(4000):
        if n >= 70: break
        x = rng.uniform(X0 + 5, X1 - 5); z = rng.uniform(34, Z1 - 5)
        i = int((x - X0) / RES); j = int((z - Z0) / RES)
        if frei[j, i] < 2.6 or np.hypot(x - mx, z - mz) < mr + 3 or z < gh[j, i] + 6: continue
        r = rng.choice([0.55, 0.7, 0.9, 1.2], p=[0.35, 0.3, 0.25, 0.1]); d = np.hypot(gx - x, gz - z)
        m = d < r; t[m] = np.minimum(t[m], MOND + (BASIS - MOND) * (d[m] / r) ** 2); frei[d < r + 3.5] = 0; n += 1
    # Rahmen mit Innenfase
    rd = np.minimum(np.minimum(gx - X0, X1 - gx), np.minimum(gz - Z0, Z1 - gz))
    rand = RAND_H * np.clip((RAND_B + 1.2 - rd) / 1.2, 0, 1); t = np.where(rand > 0, np.maximum(t, BASIS + rand), t)
    # stützfrei: von oben nach unten unter jedem Vorsprung eine Fase auffüllen
    k = math.tan(math.radians(UEBERHANG)) * RES; vor = t.copy()
    for j in range(len(zs) - 2, -1, -1): t[j] = np.maximum(t[j], t[j + 1] - k)
    print(f"Blätter {nb}, Sterne {n}, Dicke {t.min():.2f}–{t.max():.2f} mm, Fasen-Zuwachs {(t - vor).mean() * 1000:.0f} µm im Mittel", flush=True)
    return xs, zs, t.astype(np.float32)


def vorschau(t, pfad):
    from matplotlib.colors import LightSource; from PIL import Image
    ls = LightSource(azdeg=315, altdeg=38); sch = ls.hillshade(t, vert_exag=2.4, dx=RES, dy=RES)
    auf = np.clip(0.30 + 0.78 * sch, 0, 1)[..., None] * np.array([0.97, 0.96, 0.93])     # Auflicht, weißes PLA
    durch = np.exp(-(t - MOND) / 1.7)[..., None] * np.array([1.0, 0.86, 0.62]) * 0.95 + 0.04   # Licht von hinten (geschätzt)
    b = np.concatenate([auf, np.ones((t.shape[0], 30, 3)), np.clip(durch, 0, 1)], 1)[::-1]
    Image.fromarray((b * 255).astype(np.uint8)).save(pfad)


def netz(xs, zs, t, ziel_dreiecke):
    import trimesh, fast_simplification
    t = t[:, ::-1]                                                          # spiegeln: nach dem Drehen zeigt das Bild seitenrichtig nach vorn (−Y)
    nz, nx = t.shape; gx, gz = np.meshgrid(xs, zs)
    vorn = np.stack([gx.ravel(), t.ravel(), gz.ravel()], 1)
    hu = np.stack([xs, np.zeros(nx), np.full(nx, zs[0])], 1); ho = np.stack([xs, np.zeros(nx), np.full(nx, zs[-1])], 1)
    V = np.concatenate([vorn, hu, ho]).astype(np.float64)
    idx = np.arange(nz * nx).reshape(nz, nx); U = nz * nx + np.arange(nx); O = U + nx
    a, b, c, d = idx[:-1, :-1], idx[:-1, 1:], idx[1:, :-1], idx[1:, 1:]
    F = [np.stack([a.ravel(), b.ravel(), c.ravel()], 1), np.stack([b.ravel(), d.ravel(), c.ravel()], 1)]
    q = lambda p0, p1, q0, q1: [np.stack([p0, q0, p1], 1), np.stack([p1, q0, q1], 1)]
    F += q(idx[0, :-1], idx[0, 1:], U[:-1], U[1:])                          # Unterseite
    F += q(idx[-1, 1:], idx[-1, :-1], O[1:], O[:-1])                        # Oberseite
    F += q(U[:-1], U[1:], O[:-1], O[1:])                                    # Rückseite
    for i, sinn in ((0, 1), (nx - 1, -1)):                                  # Seiten als Fächer
        sp = idx[:, i]; f = np.stack([np.full(nz - 1, U[i]), sp[:-1], sp[1:]], 1); e = np.array([[U[i], sp[-1], O[i]]])
        f = np.concatenate([f, e]); F.append(f if sinn > 0 else f[:, ::-1])
    F = np.concatenate(F).astype(np.int64)
    # biegen: Rückseite auf Radius RADIUS, Relief außen (gewölbte Seite)
    ph = V[:, 0] / RADIUS; r = RADIUS + V[:, 1]
    V = np.stack([r * np.sin(ph), r * np.cos(ph) - RADIUS, V[:, 2]], 1)
    m = trimesh.Trimesh(V, F, process=False)
    if m.volume < 0: m.invert()
    n0 = len(m.faces)
    if ziel_dreiecke and n0 > ziel_dreiecke:
        V2, F2 = fast_simplification.simplify(np.ascontiguousarray(m.vertices), np.ascontiguousarray(m.faces, dtype=np.int32), target_count=int(ziel_dreiecke), agg=3)
        m = trimesh.Trimesh(V2, F2, process=True)
        if m.volume < 0: m.invert()
    m.apply_transform(trimesh.transformations.rotation_matrix(math.pi, [0, 0, 1]))   # Relief nach vorn
    m.apply_translation([0, -m.bounds[0][1], 0])
    print(f"Netz: {n0} -> {len(m.faces)} Dreiecke, dicht={m.is_watertight}, {m.volume / 1000:.1f} cm³ (~{m.volume / 1000 * 1.24:.0f} g PLA), Maße {np.round(m.extents, 1)}", flush=True)
    return m


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--saat", type=int, default=4); ap.add_argument("--nur-bild")
    ap.add_argument("--ziel", default="modelle"); ap.add_argument("--dreiecke", type=int, default=700000)
    a = ap.parse_args(); xs, zs, t = bild(a.saat)
    if a.nur_bild: vorschau(t, a.nur_bild); return
    m = netz(xs, zs, t, a.dreiecke); m.export(f"{a.ziel}/lebensbaum_licht.stl")


if __name__ == "__main__":
    main()
