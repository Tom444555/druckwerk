#!/usr/bin/env python3
"""Lebensbaum-Ständer v5 – breiter, flacher Lebensbaum als Relief + Astgabel als Halter (Eigenentwurf).

Optik: kurzer, dicker, gedrehter Stamm aus Strängen, weit ausladende flache Krone mit dichtem Laub,
„leuchtende“ feine Zweige über dem Laub und ein breites Wurzelgeflecht am Boden und auf der Fußplatte.
Wachstum: da-Vinci-Regel (r1=r*sqrt(1-f), r2=r*sqrt(f)), unregelmäßige Winkel, Äste suchen freie Lücken.

Aufruf:  python3 werkzeug/baum_relief.py [--saat 4] [--nur-bild bild.png]
Ergebnis: modelle/staender_baum_{schwarz,gold,blatt,weiss}.stl (liegend = Druckausrichtung)
Koordinaten beim Bauen „stehend“: X Breite, Y nach vorn, Z hoch.
"""
import math, argparse
import numpy as np
from scipy import ndimage

# ---- geprüfte Passmaße (wie die anderen Ständer) ----
hals_b = 10.4; sattel_h = 160; kopf_d = 4.1; luft_unten = 10; fuss_d = 4.0; abstand = 11.0
spalt = hals_b + 0.8; zinke_r = 2.5; zg = fuss_d + luft_unten + sattel_h      # 174 = Oberkante Gabel
zx = spalt / 2 + zinke_r                                                     # Achse der Zinken
gabel_z = zg - 22                                                            # hier endet der Leitast im Relief

RES = 0.16; X0, X1, Z0, Z1 = -97.0, 97.0, 0.0, 182.0
HMAX = 5.3                                                                   # hinter der Gitarre max. 5,5 mm
KA, KB, KZ = 86.0, 105.0, 72.0                                               # Krone: Halbachsen, Mitte
H_ADER = 3.4; H_BLATT = 3.1                                                  # feine Zweige liegen über dem Laub
FUSS_B = 66.0                                                                # halbe Fußbreite hinten


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--saat", type=int, default=6); ap.add_argument("--nur-bild")
    a = ap.parse_args(); rng = np.random.default_rng(a.saat)
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

    zu, zo, P = 14.0, 58.0, 40.0                                               # Stamm: unten, oben, Windungslänge
    blaetter = []

    def blatt(x, z, th, gross=1.0):
        if (abs(x) < 6.0 and z < gabel_z + 4) or z < zo + 3: return
        blaetter.append((x, z, th, rng.uniform(4.0, 6.2) * gross, rng.uniform(1.3, 2.6), rng.uniform(-0.5, 0.5), rng.uniform(-0.25, 0.25)))

    def wachse(x, z, th, r, wurzel=False, lang=1.0):
        stapel = [(x, z, th, r, lang)]
        while stapel:
            x, z, th, r, lg = stapel.pop()
            L = (8.0 if wurzel else 6.8) * r ** 0.75 * rng.uniform(0.75, 1.3) * lg; s = rng.uniform(0, 500); n = int(L / 0.4)
            seite = 1 if rng.random() < 0.5 else -1; naechst = rng.uniform(1.5, 3.5); tot = False; trieb = rng.uniform(1, 4); gedreht = 0.0
            for k in range(n):
                th += rng.normal(0, 0.055 / math.sqrt(r))
                if wurzel:                                                     # Wurzeln kriechen flach am Boden entlang
                    soll = min(2.25, max(1.3, 1.72 + 0.045 * (z - 9)))               # oben eher abwärts, unten eher flach
                    th += 0.05 * (math.copysign(soll, th) - th)
                    if z < 0.7 or z > 30 or abs(x) > FUSS_B - 2: tot = True; break
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
                stempel(x, z, th, rr, s, hmax=(H_ADER if ader and not wurzel else None), gold=ader)
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
                if tot or r < 0.55: continue
            elif tot or r < 0.52:
                blatt(x, z, th + rng.uniform(-0.25, 0.25))
                for sd in (-1, 1):
                    if rng.random() < 0.8: blatt(x, z, th + sd * rng.uniform(0.6, 1.0), 0.85)
                continue
            f = rng.uniform(0.24, 0.5); r1 = r * math.sqrt(1 - f); r2 = r * math.sqrt(f)
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
        t = (z - (zu + zo) / 2) / ((zo - zu) / 2); return 4.6 + (3.6 if t > 0 else 9.0) * abs(t) ** 3
    def sx(z, ph): return mitte(z) + amp(z) * math.sin(2 * math.pi * (z - zo) / P + ph)
    for pos, r, ziel in [(-0.97, 3.0, -86), (-0.62, 2.9, -60), (-0.27, 2.6, -32), (0.27, 2.6, 30), (0.62, 2.9, 58), (0.97, 3.0, 84)]:
        ph = math.asin(pos); z = zu; s = rng.uniform(0, 300); pts = []
        while z <= zo + 0.01:
            x = sx(z, ph); th = math.atan2(sx(z + 0.3, ph) - x, 0.3)
            stempel(x, z, th, r * (1 + 0.08 * math.sin(s * 0.8)), s, hmax=min(HMAX, 3.6 + 1.7 * math.cos(2 * math.pi * (z - zo) / P + ph)))
            pts.append((x, z, th)); z += 0.3; s += 0.35
        x, z, th = pts[-1]; wachse(x, z, 0.25 * th + 0.75 * math.radians(ziel), r, lang=1.6)
        x, z, th = pts[0]; wachse(x, z, math.copysign(math.radians(100 + rng.uniform(0, 25)), x if abs(x) > 1 else rng.choice([-1, 1])), r * 0.95, wurzel=True, lang=1.5)
    for k in (0, 1):                                                           # Leitast: zwei Stränge bis zur Gabel
        z = zu - 6; s = rng.uniform(0, 300)
        while z <= gabel_z + 2:
            arg = 2 * math.pi * z / 38.0 + k * math.pi; a_ = 2.1 + 3.0 * math.exp(-max(z - 4, 0) / 6.0); x = mitte(z) + a_ * math.sin(arg)
            th = math.atan2(a_ * math.cos(arg) * 2 * math.pi / 38.0, 1.0); r = 2.6 - 0.5 * max(0, z - zo) / (gabel_z - zo)
            stempel(x, z, th, r * (1 + 0.07 * math.sin(s * 0.7)), s, hmax=min(HMAX, 3.9 + 1.4 * math.cos(arg))); z += 0.3; s += 0.33
    s0 = 1 if rng.random() < 0.5 else -1
    for i, (zz, rr) in enumerate([(78, 2.2), (93, 2.1), (107, 2.0), (120, 1.85), (132, 1.7), (142, 1.55), (149, 1.4)]):
        sd = s0 * (1 if i % 2 == 0 else -1); wachse(sd * 2.5, zz + rng.uniform(-2, 2), sd * math.radians(72 - 6 * i + rng.uniform(-8, 8)), rr, lang=1.3)
    for w, rr in [(96, 2.4), (-97, 2.4), (112, 2.0), (-115, 2.0), (135, 1.6), (-138, 1.6)]:      # zusätzliche Wurzeln
        wachse(mitte(18) + math.copysign(4.0, w), rng.uniform(9, 20), math.radians(w), rr, wurzel=True, lang=1.4)

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
    blatt_oben = hl > np.maximum(hw, 0) + 0.05
    hschw = np.where(blatt_oben | mg, -0.5, hw).astype(np.float32); hgold = np.where(mg & ~blatt_oben, hw, -0.5).astype(np.float32)
    hblatt = np.where(blatt_oben, hl, -0.5).astype(np.float32)
    print(f"Blätter: {len(blaetter)}  Stamm/Äste {(hschw>0).mean()*100:.0f} %  Adern {(hgold>0).mean()*100:.0f} %  Laub {(hblatt>0).mean()*100:.0f} % der Fläche", flush=True)

    if a.nur_bild:
        from matplotlib.colors import LightSource; from PIL import Image
        hh = np.maximum(np.maximum(np.maximum(hschw, hblatt), hgold), 0); ls = LightSource(azdeg=315, altdeg=40)
        sch = ls.hillshade(hh, vert_exag=2.2, dx=RES, dy=RES)
        farbe = np.zeros(hh.shape + (3,)); farbe[:] = (0.93, 0.93, 0.93)
        farbe[hschw > 0] = (0.25, 0.25, 0.27); farbe[hgold > 0] = (0.92, 0.72, 0.2); farbe[hblatt > 0] = (0.78, 0.10, 0.10)
        bild = (np.clip(farbe * (0.35 + 0.75 * sch[..., None]), 0, 1) * 255).astype(np.uint8)[::-1]
        Image.fromarray(bild).save(a.nur_bild); return

    # ================= Netze =================
    import manifold3d as m3, trimesh, fast_simplification
    def relief(h):                                   # Höhenfeld -> wasserdichter Körper, bei y=0 abgeschnitten
        gx, gz = np.meshgrid(xs, zs); top = np.stack([gx.ravel(), h.ravel(), gz.ravel()], 1)
        idx = np.arange(nz * nx).reshape(nz, nx); a_, b_, c_, d_ = idx[:-1, :-1], idx[:-1, 1:], idx[1:, :-1], idx[1:, 1:]
        tri = [np.stack([a_.ravel(), c_.ravel(), b_.ravel()], 1), np.stack([b_.ravel(), c_.ravel(), d_.ravel()], 1)]
        ring = np.concatenate([idx[0, :-1], idx[:-1, -1], idx[-1, :0:-1], idx[:0:-1, 0]])
        n0 = len(top); unten = top[ring].copy(); unten[:, 1] = -1.0; mitte_ = np.array([[0, -1.0, (Z0 + Z1) / 2]])
        k = len(ring); r0 = np.arange(k); r1 = (r0 + 1) % k
        tri.append(np.stack([ring[r0], ring[r1], n0 + r0], 1)); tri.append(np.stack([ring[r1], n0 + r1, n0 + r0], 1))
        tri.append(np.stack([n0 + r0, n0 + r1, np.full(k, n0 + k)], 1))
        V = np.concatenate([top, unten, mitte_]).astype(np.float32); F = np.concatenate(tri).astype(np.uint32)
        k_ = m3.Manifold(m3.Mesh(V, F))
        if k_.volume() < 0: k_ = m3.Manifold(m3.Mesh(V, F[:, ::-1].copy()))
        assert k_.status() == m3.Error.NoError and k_.volume() > 0, k_.status()
        return k_.trim_by_plane((0, 1, 0), 0.0)
    kug = lambda p, r, n=16: m3.Manifold.sphere(r, n).translate(p)
    def wulst(pkt, boden=False, n=16):               # Kette aus Kugeln, je zwei per Hülle verbunden
        teile = []
        for (p, r), (q, r2) in zip(pkt[:-1], pkt[1:]):
            A = kug(p, r, n).to_mesh().vert_properties[:, :3]; B = kug(q, r2, n).to_mesh().vert_properties[:, :3]; Pk = np.concatenate([A, B])
            if boden: P2 = Pk.copy(); P2[:, 1] = 0; Pk = np.concatenate([Pk, P2])
            teile.append(m3.Manifold.hull_points(Pk))
        return m3.Manifold.batch_boolean(teile, m3.OpType.Add)

    holz = relief(hschw); ader_k = relief(hgold); blatt_k = relief(hblatt); print("Relief fertig", flush=True)
    # ---- Astgabel als Halter ----
    gab = []
    for sd in (-1, 1):
        gab.append(wulst([((0, 2.6, gabel_z - 3), 3.3), ((sd * 4.4, 5.6, zg - 11.5), 3.0), ((sd * zx, 8.4, zg - 2.9), 2.5),
                          ((sd * zx, abstand, zg - zinke_r), zinke_r)], boden=True, n=24))
        gab.append(wulst([((sd * zx, abstand, zg - zinke_r), zinke_r), ((sd * zx, abstand + 3.6, zg - zinke_r - 0.15), 2.4),
                          ((sd * zx, abstand + kopf_d + 3.1, zg - zinke_r), 2.3), ((sd * zx, abstand + kopf_d + 3.9, zg + 1.0), 1.55)], n=24))
        gab.append(kug((sd * (zx + 1.6), 7.2, zg - 9.5), 1.5))
    gab.append(wulst([((0, 5.0, zg - 13), 3.2), ((0, 7.7, zg - 6.6), 3.2)], boden=True, n=24))
    gabel = m3.Manifold.batch_boolean(gab, m3.OpType.Add)
    gabel -= m3.Manifold.cube((spalt, 40, 60)).translate((-spalt / 2, abstand - 0.05, zg - 40))
    gabel -= m3.Manifold.cube((60, abstand + kopf_d + 1.2, 20)).translate((-30, -1, zg))
    gabel = gabel.trim_by_plane((0, 1, 0), 0.0)
    # ---- breite Fußplatte + Wurzelgeflecht darauf + Einlage ----
    cs = m3.CrossSection; kreis = lambda x, y, r, n=48: cs.circle(r, n).translate((x, y))
    fuss2d = cs.batch_hull([kreis(sd * (FUSS_B - 2.5), 2.5, 2.5) for sd in (-1, 1)] + [kreis(sd * (FUSS_B - 9), 20, 9) for sd in (-1, 1)] +
                           [kreis(sd * 38, 44, 11) for sd in (-1, 1)] + [kreis(sd * 14, 54, 10) for sd in (-1, 1)] + [kreis(0, 60, 9)])
    fuss = fuss2d.extrude(fuss_d) + (fuss2d - fuss2d.offset(-1.3, m3.JoinType.Round)).extrude(0.6).translate((0, 0, fuss_d - 0.01))
    bx, by = 0.0, 52.0                                                          # Einlage „Blume des Lebens“
    wz = []
    for w0 in [-86, -72, -57, -42, -26, -10, 8, 24, 40, 56, 71, 85]:
        w0 += rng.uniform(-4, 4); Lw = 26 + 30 * abs(math.sin(math.radians(w0))) ** 2
        offen = [(mitte(18) * 0.5, 4.0, math.radians(w0), rng.uniform(1.9, 2.5), Lw)]
        while offen:
            x, y, th, r, L = offen.pop(); pkt = [((x, y, fuss_d - 0.35 * r), r)]
            for k in range(int(L / 1.3)):
                th += rng.normal(0, 0.13); x += math.sin(th) * 1.3; y += math.cos(th) * 1.3; r *= 0.965
                if math.hypot(x - bx, y - by) < 11.5 + r or y < 2.5 + r or abs(x) > FUSS_B or y > 70 or r < 0.5: break
                pkt.append(((x, y, fuss_d - 0.35 * r), r))
            if len(pkt) > 1: wz.append(wulst(pkt, n=10))
            if r > 0.62 and L > 5 and len(pkt) > 3:
                sd = rng.choice([-1, 1]); f = rng.uniform(0.3, 0.5)
                offen.append((x, y, th + sd * rng.uniform(0.4, 0.8), r * math.sqrt(f), L * 0.55)); offen.append((x, y, th - sd * rng.uniform(0.1, 0.35), r * math.sqrt(1 - f), L * 0.62))
    wurz = m3.Manifold.batch_boolean(wz, m3.OpType.Add) ^ fuss2d.offset(-1.6, m3.JoinType.Round).extrude(20)
    wurz = wurz.trim_by_plane((0, 0, 1), fuss_d - 0.3)
    rr_ = 3.6; b = 0.56; ring = lambda r: cs.circle(r + b / 2, 72) - cs.circle(r - b / 2, 72)
    blume = (cs.batch_boolean([ring(rr_)] + [ring(rr_).translate((rr_ * math.cos(w), rr_ * math.sin(w))) for w in np.radians(range(0, 360, 60))], m3.OpType.Add)
             ^ cs.circle(2 * rr_ + b / 2, 72)) + ring(2 * rr_) + ring(2 * rr_ + 1.5)
    blume += cs.batch_boolean([cs.circle(0.45, 16).translate(((2 * rr_ + 0.75) * math.cos(w), (2 * rr_ + 0.75) * math.sin(w))) for w in np.radians(range(0, 360, 30))], m3.OpType.Add)
    weiss = blume.extrude(0.7).translate((bx, by, fuss_d - 0.7))

    holz = holz + gabel
    gold = (ader_k - gabel) + (wurz - holz)
    blatt_k = blatt_k - gabel
    schwarz = (fuss - gold - weiss - blatt_k) + holz
    print("Booleans fertig", flush=True)
    def raus(k, name, minvol, ziel):
        teile = [t for t in k.decompose() if t.volume() > minvol]
        k = m3.Manifold.compose(teile).rotate((90, 0, 0)); me = k.to_mesh()
        V = np.array(me.vert_properties[:, :3], dtype=np.float64, order='C'); F = np.array(me.tri_verts, dtype=np.int32, order='C').reshape(-1, 3); n0 = len(F)
        if n0 > ziel: V, F = fast_simplification.simplify(V, F, target_count=int(ziel), agg=4)
        t = trimesh.Trimesh(V, F, process=True)
        t.export(f"modelle/staender_baum_{name}.stl"); bb = t.bounds
        print(f"{name}: {len(teile)} Teile, {t.volume/1000:.1f} cm³, {n0} -> {len(t.faces)} Dreiecke, dicht={t.is_watertight}, Maße {np.round(bb[1]-bb[0],1)}", flush=True)
    raus(schwarz, "schwarz", 0.5, 10**9); raus(gold, "gold", 0.15, 10**9); raus(blatt_k, "blatt", 0.3, 10**9); raus(weiss, "weiss", 0.0, 10**9)


if __name__ == "__main__":
    main()
