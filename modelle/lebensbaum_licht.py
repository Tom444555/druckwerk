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
FUSS_B = 66.0

# ---- Lichtbild ----
BASIS = 1.5          # Wandstärke des Himmels (leuchtet)
MOND = 0.85          # dünnste Stelle (zwei Bahnen)
RAND_B, RAND_H = 2.6, 1.9      # Rahmen: Breite, Höhe über dem Himmel
RADIUS = 130.0       # Biegeradius der Rückseite
UEBERHANG = 55.0     # größter Überhang in Grad gegen die Senkrechte


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

    zu, zo, P = 14.0, 58.0, 40.0                                               # Stamm: unten, oben, Windungslänge
    blaetter = []

    def blatt(x, z, th, gross=1.0):
        if z < zo + 3: return
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
    for sd_ in (-1, 1): wachse(sd_ * 1.2, gabel_z + 1, sd_ * math.radians(14 + rng.uniform(0, 10)), 1.9, lang=1.2)
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
    return xs, zs, hw, hl, len(blaetter)


def bild(saat):
    xs, zs, hw, hl, nb = baum(saat); rng = np.random.default_rng(saat + 1000)
    gx, gz = np.meshgrid(xs, zs)
    rel = np.maximum(np.maximum(hw, hl), 0).astype(np.float32)             # Baum über dem Himmel
    frei = ndimage.distance_transform_edt(rel <= 0) * RES                      # Abstand zum Baum (mm)
    t = BASIS + rel
    # Boden: sanfte Hügel mit Gras-Riefen
    gh = 7.5 + 2.2 * np.sin(gx / 23.0 + 0.6) + 1.2 * np.sin(gx / 9.0 + 2.0)
    gras = 0.55 + 0.22 * np.sin(gx / 0.9 + 3 * np.sin(gz / 2.3)) * np.clip((gh - gz) / 3.0, 0, 1)
    boden = np.clip((gh - gz) / 0.5, 0, 1) * gras
    t = np.maximum(t, BASIS + boden)
    # Mondsichel (dünn = hell) mit feinem Wulst
    mx, mz, mr = -73.0, 160.0, 12.5
    d1 = np.hypot(gx - mx, gz - mz); d2 = np.hypot(gx - (mx + 5.5), gz - (mz + 2.5))
    sichel = (d1 < mr) & (d2 > mr - 1.6)
    hof = (d1 < mr + 1.0) & ~sichel & (d2 > mr - 2.6) & (d1 > mr - 0.0)
    t = np.where(sichel & (rel <= 0), MOND, t); t = np.where(hof & (rel <= 0), BASIS + 0.5, t)
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
