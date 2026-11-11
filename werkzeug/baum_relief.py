#!/usr/bin/env python3
"""Lebensbaum-Ständer v3 – naturnah gewachsener Baum als Relief + Astgabel als Halter.

Wachstumsregeln: da-Vinci-Regel (Querschnitt der Tochteräste zusammen = Mutterast, r1=r*sqrt(1-f), r2=r*sqrt(f)),
dicker Tochterast lenkt weniger ab, unregelmäßige Winkel, Äste streben nach oben und ins Freie, keine Spiegelung.
Äste sind halbrunde Wülste mit Borkenfurchen, Blätter spitz-oval mit Mittelrippe und Seitenadern.

Aufruf:  python3 werkzeug/baum_relief.py [--saat 7] [--nur-bild bild.png]
Ergebnis: modelle/staender_baum_{schwarz,holz,blatt,gold}.stl (liegend = Druckausrichtung)
Koordinaten beim Bauen „stehend“: X Breite, Y nach vorn, Z hoch.
"""
import sys, math, argparse
import numpy as np
from scipy import ndimage

# ---- geprüfte Passmaße (wie die anderen Ständer) ----
hals_b = 10.4; sattel_h = 160; kopf_d = 4.1; luft_unten = 10; fuss_d = 4.0; abstand = 11.0
spalt = hals_b + 0.8; zinke_r = 2.5; zg = fuss_d + luft_unten + sattel_h      # 174 = Oberkante Gabel
zx = spalt / 2 + zinke_r                                                     # Achse der Zinken
gabel_z = zg - 22                                                            # hier endet der Leitast im Relief

RES = 0.125; X0, X1, Z0, Z1 = -50.0, 50.0, 0.0, 182.0
HMAX = 5.3                                                                   # hinter der Gitarre max. 5,5 mm


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--saat", type=int, default=17); ap.add_argument("--nur-bild")
    a = ap.parse_args(); rng = np.random.default_rng(a.saat)
    nx = int(round((X1 - X0) / RES)) + 1; nz = int(round((Z1 - Z0) / RES)) + 1
    xs = X0 + np.arange(nx) * RES; zs = Z0 + np.arange(nz) * RES
    hw = np.full((nz, nx), -0.5, np.float32)        # Holzhöhe
    mu = np.zeros((nz, nx), np.float32); ms = np.zeros((nz, nx), np.float32); mr = np.zeros((nz, nx), np.float32)
    hl = np.full((nz, nx), -0.5, np.float32)        # Blatthöhe
    belegt = np.zeros((int(Z1 / 2) + 2, 52), np.float32)                      # grobe Belegung (2 mm)

    def H(r): return min(HMAX, 1.1 + 1.15 * r)

    def stempel(x, z, th, r, s, hmax=None):
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
        mu[j0:j1, i0:i1][m] = u[m]; ms[j0:j1, i0:i1][m] = (s + v)[m]; mr[j0:j1, i0:i1][m] = r
        bj = int(z / 2); bi = int((x + 52) / 2)
        if 0 <= bj < belegt.shape[0] and 0 <= bi < 52: belegt[bj, bi] += r

    def innen(x, z):                                # unregelmäßige Kronenform
        w = 43 + 3 * math.sin(z / 9.0) ; return (x / w) ** 2 + ((z - 124) / 55.0) ** 2 < 1 and 62 < z < 179.5 and abs(x) < 48.5

    def frei(x, z, th, weit=12):
        t = 0.0
        for d in (4, 8, weit):
            px = x + math.sin(th) * d; pz = z + math.cos(th) * d
            if not innen(px, pz): t += 8; continue
            bj = int(pz / 2); bi = int((px + 52) / 2); t += belegt[max(0, bj - 1):bj + 2, max(0, bi - 1):bi + 2].sum()
        return t

    blaetter = []

    def blatt(x, z, th, gross=1.0):
        if (abs(x) < 6.0 and z < gabel_z + 4) or z < zo + 4: return
        blaetter.append((x, z, th, rng.uniform(4.8, 7.4) * gross, rng.uniform(1.6, 3.2), rng.uniform(-0.6, 0.6), rng.uniform(-0.25, 0.25)))

    def wachse(x, z, th, r, wurzel=False, sstart=0.0):
        stapel = [(x, z, th, r, 0)]
        while stapel:
            x, z, th, r, tiefe = stapel.pop()
            L = (9.0 if wurzel else 6.8) * r ** 0.75 * rng.uniform(0.75, 1.3); s = rng.uniform(0, 500); n = int(L / 0.4)
            seite = 1 if rng.random() < 0.5 else -1; naechst = rng.uniform(2, 5); tot = False
            for k in range(n):
                th += rng.normal(0, 0.055 / math.sqrt(r))
                if wurzel:
                    th += 0.03 * (math.copysign(2.05, th) - th)                    # Wurzeln kriechen nach unten/außen
                    if z < 0.3 or abs(x) > 37: tot = True; break
                else:
                    th -= (0.0015 if r > 1.3 else 0.006) * th                                              # leichter Zug nach oben
                    ax = x + math.sin(th) * 5; az = z + math.cos(th) * 5
                    if not innen(ax, az):
                        zur = math.atan2(-x, 127 - z); dth = (zur - th + math.pi) % (2 * math.pi) - math.pi
                        th += 0.09 * np.sign(dth)
                    if not innen(x, z): tot = True; break
                x += math.sin(th) * 0.4; z += math.cos(th) * 0.4; s += 0.4; r *= 0.9985
                stempel(x, z, th, r * (1 + 0.09 * math.sin(s * 0.9) + 0.05 * math.sin(s * 2.3)) if r > 0.8 else r, s)
                if not wurzel and r < 0.8:
                    naechst -= 0.4
                    if naechst <= 0:
                        naechst = rng.uniform(3.0, 5.0); seite = -seite
                        if rng.random() < 0.8: blatt(x, z, th + seite * rng.uniform(0.6, 1.1), 0.9)
            if wurzel:
                if tot or r < 0.75: continue
            elif tot or r < 0.52:
                blatt(x, z, th + rng.uniform(-0.25, 0.25))
                for sd in (-1, 1):
                    if rng.random() < 0.75: blatt(x, z, th + sd * rng.uniform(0.6, 1.0), 0.85)
                continue
            f = rng.uniform(0.24, 0.5); r1 = r * math.sqrt(1 - f); r2 = r * math.sqrt(f)
            beste = None
            for _ in range(6):
                sd = rng.choice([-1, 1]); a1 = -sd * math.radians(rng.uniform(6, 22)) * (f / 0.5 + 0.3)
                a2 = sd * math.radians(rng.uniform(30, 58))
                w = (0 if wurzel else frei(x, z, th + a1) + frei(x, z, th + a2))
                if beste is None or w < beste[0]: beste = (w, a1, a2)
            stapel.append((x, z, th + beste[1], r1, tiefe + 1))
            if r2 > 0.42: stapel.append((x, z, th + beste[2], r2, tiefe + 1))

    # ---- Lebensbaum-Stamm: Stränge winden sich umeinander, werden unten zu Wurzeln und oben zu Ästen ----
    zu, zo, P = 19.0, 70.0, 46.0
    def amp(z):
        t = (z - (zu + zo) / 2) / ((zo - zu) / 2); return 3.3 + (2.4 if t > 0 else 7.0) * abs(t) ** 3
    def strang(pos, r, ziel, wziel):
        ph = math.asin(pos); z = zu; s = rng.uniform(0, 300); pts = []
        while z <= zo + 0.01:
            arg = 2 * math.pi * (z - zo) / P + ph; x = amp(z) * math.sin(arg)
            dxdz = (amp(z + 0.3) * math.sin(2 * math.pi * (z + 0.3 - zo) / P + ph) - x) / 0.3
            th = math.atan2(dxdz, 1.0); rr = r * (1 + 0.08 * math.sin(s * 0.8))
            stempel(x, z, th, rr, s, hmax=min(HMAX, 3.5 + 1.8 * math.cos(arg))); pts.append((x, z, th)); z += 0.3; s += 0.35
        x, z, th = pts[-1]; wachse(x, z, 0.3 * th + 0.7 * math.radians(ziel), r)
        x, z, th = pts[0]; wachse(x, z, math.radians(wziel), r * 0.95, wurzel=True)
    for pos, r, ziel, wziel in [(-0.97, 2.7, -78, 0), (-0.55, 2.6, -42, 0), (0.5, 2.6, 40, 0), (0.96, 2.7, 76, 0), (-0.2, 2.2, -18, 0), (0.25, 2.2, 22, 0)]:
        x_u = amp(zu) * math.sin(2 * math.pi * (zu - zo) / P + math.asin(pos))
        strang(pos, r, ziel, math.copysign(100 + 45 * (1 - min(1, abs(x_u) / 10)), x_u if abs(x_u) > 0.5 else rng.choice([-1, 1])))
    # Leitast: zwei Stränge, die sich bis zur Gabel umeinander drehen
    for k in (0, 1):
        z = zu - 6; s = rng.uniform(0, 300)
        while z <= gabel_z + 2:
            arg = 2 * math.pi * z / 38.0 + k * math.pi; a_ = 2.0 + 3.0 * math.exp(-max(z - 4, 0) / 6.0); x = a_ * math.sin(arg)
            th = math.atan2(a_ * math.cos(arg) * 2 * math.pi / 38.0, 1.0); r = 2.55 - 0.45 * max(0, z - zo) / (gabel_z - zo)
            stempel(x, z, th, r * (1 + 0.07 * math.sin(s * 0.7)), s, hmax=min(HMAX, 3.9 + 1.4 * math.cos(arg))); z += 0.3; s += 0.33
    s0 = 1 if rng.random() < 0.5 else -1
    for i, (zz, rr) in enumerate([(92, 2.0), (106, 1.9), (119, 1.8), (131, 1.65), (142, 1.5), (149, 1.4)]):
        sd = s0 * (1 if i % 2 == 0 else -1); wachse(sd * 2.5, zz + rng.uniform(-2, 2), sd * math.radians(62 - 6 * i + rng.uniform(-8, 8)), rr)
    for w, rr in [(150, 2.2), (-152, 2.2), (172, 1.7), (-170, 1.6)]:                 # zusätzliche Wurzeln
        wachse(math.copysign(3.0, w), rng.uniform(10, 16), math.radians(w), rr, wurzel=True)

    # ---- Borke: Furchen längs des Astes ----
    tex = ndimage.zoom(rng.random((96, 96)).astype(np.float32), 8, order=3, mode="wrap")
    def rausch(a, b): return ndimage.map_coordinates(tex, [(a * 8) % 760, (b * 8) % 760], order=1, mode="wrap")
    staerke = np.clip((mr - 0.7) / 1.6, 0, 1) * 0.62
    n1 = rausch(ms / 8.0 + mr * 3.1, mu / 1.15 + 40); n2 = rausch(ms / 3.2 + 11, mu / 0.62 + 7); n3 = rausch(ms / 1.6 + 5, mu / 2.4 + 90)
    furche = np.exp(-((n1 - 0.5) / 0.075) ** 2) + 0.45 * np.exp(-((n2 - 0.5) / 0.09) ** 2) + 0.3 * np.exp(-((n3 - 0.5) / 0.05) ** 2)
    schuppe = (rausch(ms / 5.0 + 70, mu / 1.6 + 3) - 0.5) * 0.5                      # Borkenplatten leicht versetzt
    hw = np.where(hw > 0, np.maximum(0.6, hw - staerke * (furche - schuppe)), hw).astype(np.float32)

    # ---- Blätter: spitz-oval, gewölbt, Mittelrippe + Seitenadern ----
    for (x, z, th, L, h0, neig, kr) in blaetter:
        stiel = 0.7; cx = x + math.sin(th) * stiel; cz = z + math.cos(th) * stiel; W = L * rng.uniform(0.40, 0.5)
        R = L + 1; i0 = max(0, int((cx - R - X0) / RES)); i1 = min(nx, int((cx + R - X0) / RES) + 2)
        j0 = max(0, int((cz - R - Z0) / RES)); j1 = min(nz, int((cz + R - Z0) / RES) + 2)
        if i0 >= i1 or j0 >= j1: continue
        dx = xs[i0:i1][None, :] - cx; dz = zs[j0:j1][:, None] - cz
        t = (dx * math.sin(th) + dz * math.cos(th)) / L; v = dx * math.cos(th) - dz * math.sin(th)
        v = v - kr * L * 4 * t * (1 - t) * 0.25                                  # leicht gebogene Mittelrippe
        tt = np.clip(t, 0, 1); halb = W / 2 * np.sin(math.pi * tt ** 0.72) ** 0.85 * (1 - 0.25 * tt)
        m = (t > 0) & (t < 1) & (np.abs(v) < halb)
        q = np.clip(np.abs(v) / np.maximum(halb, 1e-3), 0, 1)
        h = h0 + neig * (tt - 0.5) + 0.42 * q - 0.5 * np.clip(q - 0.8, 0, 1) / 0.2 * 0.6
        h -= 0.34 * np.exp(-(v / 0.24) ** 2)                                       # Mittelrippe
        ader = np.cos(2 * math.pi * (tt * L - np.abs(v) * 1.1) / 1.25)
        h -= 0.24 * np.clip(ader - 0.55, 0, 1) / 0.45 * (q < 0.9)
        h = np.maximum(h, 0.7); sub = hl[j0:j1, i0:i1]; m &= h > sub; sub[m] = h[m]
        mst = (t > -stiel / L - 0.02) & (t <= 0.05) & (np.abs(v) < 0.3)             # Blattstiel
        sub[mst & (sub < 0.9)] = 0.9
    blatt_oben = hl > np.maximum(hw, 0) + 0.05
    hholz = np.where(blatt_oben, -0.5, hw).astype(np.float32); hblatt = np.where(blatt_oben, hl, -0.5).astype(np.float32)
    print(f"Blätter: {len(blaetter)}  Holz {(hholz>0).mean()*100:.0f} %  Blatt {(hblatt>0).mean()*100:.0f} % der Fläche", flush=True)

    if a.nur_bild:
        from matplotlib.colors import LightSource; from PIL import Image
        hh = np.maximum(np.maximum(hholz, hblatt), 0); ls = LightSource(azdeg=315, altdeg=40)
        sch = ls.hillshade(hh, vert_exag=2.2, dx=RES, dy=RES)
        farbe = np.zeros(hh.shape + (3,)); farbe[:] = (0.93, 0.93, 0.93)
        farbe[hholz > 0] = (0.86, 0.66, 0.18); farbe[hblatt > 0] = (0.78, 0.10, 0.10)
        bild = (np.clip(farbe * (0.35 + 0.75 * sch[..., None]), 0, 1) * 255).astype(np.uint8)[::-1]
        Image.fromarray(bild).save(a.nur_bild); return

    # ================= Netze =================
    import manifold3d as m3, trimesh
    def relief(h):                                   # Höhenfeld -> wasserdichter Körper, bei y=0 abgeschnitten
        gx, gz = np.meshgrid(xs, zs); top = np.stack([gx.ravel(), h.ravel(), gz.ravel()], 1)
        idx = np.arange(nz * nx).reshape(nz, nx); a_, b_, c_, d_ = idx[:-1, :-1], idx[:-1, 1:], idx[1:, :-1], idx[1:, 1:]
        tri = [np.stack([a_.ravel(), c_.ravel(), b_.ravel()], 1), np.stack([b_.ravel(), c_.ravel(), d_.ravel()], 1)]
        ring = np.concatenate([idx[0, :-1], idx[:-1, -1], idx[-1, :0:-1], idx[:0:-1, 0]])
        n0 = len(top); unten = top[ring].copy(); unten[:, 1] = -1.0; mitte = np.array([[0, -1.0, (Z0 + Z1) / 2]])
        k = len(ring); r0 = np.arange(k); r1 = (r0 + 1) % k
        tri.append(np.stack([ring[r0], ring[r1], n0 + r0], 1)); tri.append(np.stack([ring[r1], n0 + r1, n0 + r0], 1))
        tri.append(np.stack([n0 + r0, n0 + r1, np.full(k, n0 + k)], 1))
        V = np.concatenate([top, unten, mitte]).astype(np.float32); F = np.concatenate(tri).astype(np.uint32)
        k_ = m3.Manifold(m3.Mesh(V, F))
        if k_.volume() < 0: k_ = m3.Manifold(m3.Mesh(V, F[:, ::-1].copy()))
        assert k_.status() == m3.Error.NoError and k_.volume() > 0, k_.status()
        return k_.trim_by_plane((0, 1, 0), 0.0)
    kug = lambda p, r, n=20: m3.Manifold.sphere(r, n).translate(p)
    def wulst(pkt, boden=False):                     # Kette aus Kugeln, je zwei per Hülle verbunden
        teile = []
        for (p, r), (q, r2) in zip(pkt[:-1], pkt[1:]):
            A = kug(p, r).to_mesh().vert_properties[:, :3]; B = kug(q, r2).to_mesh().vert_properties[:, :3]; P = np.concatenate([A, B])
            if boden: P2 = P.copy(); P2[:, 1] = 0; P = np.concatenate([P, P2])
            teile.append(m3.Manifold.hull_points(P))
        return m3.Manifold.batch_boolean(teile, m3.OpType.Add)

    holz = relief(hholz); blatt_k = relief(hblatt); print("Relief fertig", flush=True)
    # ---- Astgabel als Halter: Leitast teilt sich in zwei Äste, die nach vorn wachsen ----
    gab = []
    for sd in (-1, 1):
        gab.append(wulst([((0, 2.6, gabel_z - 3), 3.3), ((sd * 4.4, 5.6, zg - 11.5), 3.0), ((sd * zx, 8.4, zg - 2.9), 2.5),
                          ((sd * zx, abstand, zg - zinke_r), zinke_r)], boden=True))
        gab.append(wulst([((sd * zx, abstand, zg - zinke_r), zinke_r), ((sd * zx, abstand + 3.6, zg - zinke_r - 0.15), 2.4),
                          ((sd * zx, abstand + kopf_d + 3.1, zg - zinke_r), 2.3), ((sd * zx, abstand + kopf_d + 3.9, zg + 1.0), 1.55)]))
        gab.append(kug((sd * (zx + 1.6), 7.2, zg - 9.5), 1.5))                       # Astknoten
    gab.append(wulst([((0, 5.0, zg - 13), 3.2), ((0, 7.7, zg - 6.6), 3.2)], boden=True))   # Zwiesel zwischen den Ästen
    gabel = m3.Manifold.batch_boolean(gab, m3.OpType.Add)
    gabel -= m3.Manifold.cube((spalt, 40, 60)).translate((-spalt / 2, abstand - 0.05, zg - 40))   # Platz für den Hals
    gabel -= m3.Manifold.cube((60, abstand + kopf_d + 1.2, 20)).translate((-30, -1, zg))          # Platz für die Kopfplatte
    gabel = gabel.trim_by_plane((0, 1, 0), 0.0)
    # ---- Fußplatte (Plektrumform) + Wurzeln darauf + Einlage ----
    cs = m3.CrossSection; kreis = lambda x, y, r, n=48: cs.circle(r, n).translate((x, y))
    fuss2d = cs.batch_hull([kreis(sx * 36, 2.5, 2.5) for sx in (-1, 1)] + [kreis(sx * 35.5, 10, 3) for sx in (-1, 1)] +
                           [kreis(sx * 29, 28, 9) for sx in (-1, 1)] + [kreis(sx * 14, 50, 10) for sx in (-1, 1)] + [kreis(0, 58, 9)])
    fuss = fuss2d.extrude(fuss_d) + (fuss2d - fuss2d.offset(-1.3, m3.JoinType.Round)).extrude(0.6).translate((0, 0, fuss_d - 0.01))
    wz = []
    for w0, L, r0_ in [(-80, 30, 2.3), (-52, 30, 2.1), (-24, 23, 2.0), (4, 17, 1.6), (30, 24, 2.0), (57, 31, 2.2), (82, 28, 2.1)]:
        offen = [(0.0, 4.0, math.radians(w0 + rng.uniform(-5, 5)), r0_, L)]
        while offen:
            x, y, th, r, L = offen.pop(); pkt = [((x, y, fuss_d - 0.35 * r), r)]
            for k in range(int(L / 1.5)):
                th += rng.normal(0, 0.11); x += math.sin(th) * 1.5; y += math.cos(th) * 1.5; r *= 0.955
                if math.hypot(x, y - 50) < 12.5 + r or y < 3: break
                pkt.append(((x, y, fuss_d - 0.35 * r), r))
            if len(pkt) > 1: wz.append(wulst([(p, rr) for p, rr in pkt]))
            if r > 1.0 and L > 12 and len(pkt) > 4:
                sd = rng.choice([-1, 1]); offen.append((x, y, th + sd * 0.55, r * 0.75, L * 0.45)); offen.append((x, y, th - sd * 0.3, r * 0.8, L * 0.5))
    wurz = m3.Manifold.batch_boolean(wz, m3.OpType.Add) ^ fuss2d.offset(-1.6, m3.JoinType.Round).extrude(20)
    wurz = wurz.trim_by_plane((0, 0, 1), fuss_d - 0.3)
    rr_ = 4.1; b = 0.56; ring = lambda r: cs.circle(r + b / 2, 72) - cs.circle(r - b / 2, 72)
    blume = (cs.batch_boolean([ring(rr_)] + [ring(rr_).translate((rr_ * math.cos(w), rr_ * math.sin(w))) for w in np.radians(range(0, 360, 60))], m3.OpType.Add)
             ^ cs.circle(2 * rr_ + b / 2, 72)) + ring(2 * rr_) + ring(2 * rr_ + 1.5)
    blume += cs.batch_boolean([cs.circle(0.45, 16).translate(((2 * rr_ + 0.75) * math.cos(w), (2 * rr_ + 0.75) * math.sin(w))) for w in np.radians(range(0, 360, 30))], m3.OpType.Add)
    gold = blume.extrude(0.7).translate((0, 50, fuss_d - 0.7))

    holz = holz + gabel + wurz
    blatt_k = blatt_k - gabel - wurz
    schwarz = fuss - holz - gold - blatt_k
    print("Booleans fertig", flush=True)
    def raus(k, name, minvol=0.3):
        teile = [t for t in k.decompose() if t.volume() > minvol]
        k = m3.Manifold.compose(teile).rotate((90, 0, 0)); me = k.to_mesh()
        t = trimesh.Trimesh(me.vert_properties[:, :3], me.tri_verts, process=False)
        t.export(f"modelle/staender_baum_{name}.stl"); bb = t.bounds
        print(f"{name}: {len(teile)} Teile, {t.volume/1000:.1f} cm³, {len(t.faces)} Dreiecke, Maße {np.round(bb[1]-bb[0],1)}", flush=True)
    raus(schwarz, "schwarz", 5); raus(holz, "holz", 0.5); raus(blatt_k, "blatt", 0.4); raus(gold, "gold", 0.0)


if __name__ == "__main__":
    main()
