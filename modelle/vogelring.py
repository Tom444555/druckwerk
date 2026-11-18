#!/usr/bin/env python3
"""Vogel-Ring als Schlüsselanhänger – eigener Entwurf (18.11.2026).

Ein Vogel rollt sich zum Ring: Kopf oben links, Körper im Uhrzeigersinn, Schwanzspitze vor dem Schnabel.
Schuppenfedern (kopfseitige Feder liegt oben), lange Schwungfedern am Außenrand, Schnörkel, Öse.
Beide Seiten gleich, Querschnitt halbrund (gewölbt). Höhenfeld in numpy → Volumen → marching cubes.

Aufruf:
  python3 modelle/vogelring.py --ziel /tmp/vr [--durchmesser 45] [--dicke 7] [--px 0.06] [--saat 3] [--nur-bild]
Ausgabe: vogelring_ganz.stl (einteilig, braucht Stützen unten), vogelring_haelfte_a.stl + _b.stl (flache Rückseite,
zwei Löcher Ø 1,9 für 1,75-mm-Filament als Passstift, kleben), vorschau.png (Höhenbild).
"""
import argparse
import math
from pathlib import Path

import numpy as np
from scipy import ndimage

ap = argparse.ArgumentParser()
ap.add_argument("--ziel", default="/tmp/vogelring")
ap.add_argument("--durchmesser", type=float, default=45.0)   # Außenmaß ohne Öse
ap.add_argument("--dicke", type=float, default=7.0)          # dickste Stelle gesamt
ap.add_argument("--px", type=float, default=0.06)            # Rastermaß mm
ap.add_argument("--saat", type=int, default=3)
ap.add_argument("--nur-bild", action="store_true")
ap.add_argument("--max-dreiecke", type=int, default=450000)
a = ap.parse_args()
rng = np.random.default_rng(a.saat)
ziel = Path(a.ziel); ziel.mkdir(parents=True, exist_ok=True)

# ---- Entwurf in Grundmaßen (Außen-Ø ≈ 45 mm), am Ende skaliert ----
K = a.durchmesser / 45.0
A = a.dicke / 2 / K          # halbe Dicke Körpermitte (Grundmaß)
E = 0.7                      # halbe Dicke am Rand
D = 0.55                     # Tiefe der Federstufen
TH = 125.0                   # Kopf-Winkel (Grad)
SW = 320.0                   # Körper-Bogen

px = a.px / K
N = int(round(52 / px))
ax = (np.arange(N) - N / 2 + 0.5) * px
X, Y = np.meshgrid(ax, ax)
R = np.hypot(X, Y)
TT = np.degrees(np.arctan2(Y, X))
S = ((TH - TT) % 360) / SW            # Lauf entlang des Körpers 0 (Kopf) … 1 (Schwanz)
IN = S <= 1.0


def rc(s):
    return np.interp(s, [0, 0.5, 1], [15.3, 14.8, 15.6])


def wb(s):
    return np.interp(s, [0, 0.08, 0.45, 0.78, 0.9, 0.97], [6.6, 7.6, 11.6, 10.6, 6.0, 1.6])


def pos(s, u=0.0):
    """Punkt auf dem Körper: s entlang, u quer (−1 innen … +1 außen)."""
    th = math.radians(TH - s * SW)
    r = rc(s) + u * wb(s) / 2
    return np.array([r * math.cos(th), r * math.sin(th)]), th


def rahmen(th):
    t = np.array([math.sin(th), -math.cos(th)])   # Richtung Schwanz (Uhrzeigersinn)
    n = np.array([math.cos(th), math.sin(th)])    # nach außen
    return t, n


# ---- Körper: halbrunder Querschnitt ----
U = np.where(IN, (R - rc(S)) / (wb(S) / 2), 9)
koerper = IN & (np.abs(U) < 1)
Hb = np.where(koerper, E + (A - E) * np.sqrt(np.clip(1 - U ** 2, 0, 1)), -1.0)
H = np.where(koerper, Hb - D, -1.0)


def box(c, rad):
    i0 = max(0, int((c[1] - rad - ax[0]) / px)); i1 = min(N, int((c[1] + rad - ax[0]) / px) + 2)
    j0 = max(0, int((c[0] - rad - ax[0]) / px)); j1 = min(N, int((c[0] + rad - ax[0]) / px) + 2)
    return slice(i0, i1), slice(j0, j1)


def lokal(sl, c, t, n):
    dx = X[sl] - c[0]; dy = Y[sl] - c[1]
    return dx * t[0] + dy * t[1], dx * n[0] + dy * n[1]


# ---- Schuppenfedern: vom Schwanz zum Kopf malen, kopfseitige Feder liegt oben ----
rel = np.zeros_like(H)
federn = []
s = 0.985
spalte = 0
while s > 0.02:
    L = float(np.interp(s, [0.02, 0.15, 0.5, 0.95], [1.3, 2.4, 4.6, 5.6]))
    B = L * float(np.interp(s, [0.1, 0.5, 0.95], [0.62, 0.5, 0.42]))
    w = float(wb(s))
    nrow = max(2, int(round(w / (B * 0.82))))
    for k in range(nrow):
        u = -1 + (k + 0.5 + (0.5 if spalte % 2 else 0)) * 2 / nrow
        if abs(u) > 0.97:
            continue
        federn.append((s, u, L * rng.uniform(0.92, 1.08), B * rng.uniform(0.92, 1.08)))
    bogen = math.radians(SW) * float(rc(s))
    s -= (L * 0.55) / bogen
    spalte += 1

for (s, u, L, B) in federn:            # Liste läuft vom Schwanz zum Kopf
    c, th = pos(s, u)
    t, n = rahmen(th)
    sl = box(c, L)
    al, bl = lokal(sl, c, t, n)
    ta = np.clip(al / L + 0.5, 0, 1)                       # 0 Ansatz … 1 Spitze
    spitz = float(np.interp(s, [0.15, 0.6], [0.0, 0.7]))   # hinten spitze, geschwungene Federn
    bog = 0.35 * spitz * B * ta ** 2                        # Spitze biegt leicht nach außen
    q = (al / (L / 2)) ** 2 + ((bl - bog) / (B / 2 * (1 - spitz * ta ** 2) + 1e-3)) ** 2
    m = (q < 1) & koerper[sl]
    rand = np.sqrt(np.clip((1 - q) * 5, 0, 1))             # schmale Rundung an der Kante
    hf = D * (0.15 + 0.95 * ta) * rand
    hf += 0.07 * np.exp(-(bl / 0.13) ** 2) * (ta > 0.12) * rand   # Kiel
    r_ = rel[sl]
    r_[m] = hf[m]
    rel[sl] = r_

H = np.where(koerper, H + rel, -1.0)

# ---- Schwungfedern am Außenrand und Schwanzfächer ----
def klinge(c, t, n, L, B, hoch, kiel=True):
    sl = box(c + t * L / 2, L)
    al, bl = lokal(sl, c, t, n)
    ta = np.clip(al / L, 0, 1)
    halb = B / 2 * np.sin(np.pi * np.clip(ta, 1e-3, 1) ** 0.75)
    halb = np.where((al > 0) & (al < L), halb, 0)
    qb = np.where(halb > 0, (bl / np.maximum(halb, 1e-6)) ** 2, 9)
    m = qb < 1
    h = E + (hoch - E) * np.sqrt(np.clip(1 - qb, 0, 1)) * (1 - 0.55 * ta)
    if kiel:
        h += 0.09 * np.exp(-((bl - 0.12 * halb) / 0.14) ** 2) * (ta < 0.9)
    h = np.where(m, h, -1)
    H[sl] = np.maximum(H[sl], h)


for s in np.linspace(0.2, 0.8, 9):                   # außen, fließen Richtung Schwanz
    c, th = pos(s, 0.82)
    t, n = rahmen(th)
    t = t * math.cos(0.16) + n * math.sin(0.16); t /= np.linalg.norm(t)
    klinge(c, t, n, float(np.interp(s, [0.2, 0.85], [7.5, 10.0])), 2.6, 1.9)
for k, (s, u, dw, L) in enumerate([(0.80, 0.6, 0.30, 10.0), (0.83, 0.2, 0.16, 11.0), (0.86, -0.2, 0.04, 10.5), (0.88, -0.6, -0.08, 8.5)]):
    c, th = pos(s, u)
    t, n = rahmen(th)
    t = t * math.cos(dw) + n * math.sin(dw); t /= np.linalg.norm(t)
    klinge(c, t, n, L, 3.0, 2.4)

# ---- Kopf, Schnabel, Auge ----
ck, thk = pos(-0.02, 0.05)
tk, nk = rahmen(thk)
vorn = -tk                                         # Blickrichtung (gegen den Uhrzeigersinn)
sl = box(ck, 7)
al, bl = lokal(sl, ck, vorn, nk)
q = (al / 5.0) ** 2 + (bl / 4.2) ** 2
hk = np.where(q < 1, E + (A - E) * np.sqrt(np.clip(1 - q, 0, 1)), -1)
H[sl] = np.where(q < 1, np.maximum(hk, H[sl] * (al < -1.5)), H[sl])

# Schnabel: gebogener Haken, zeigt nach vorn-innen
rot = math.radians(32)
sd = vorn * math.cos(rot) - nk * math.sin(rot)
sn = np.array([-sd[1], sd[0]])
cb = ck + vorn * 2.6 - nk * 0.6
sl = box(cb + sd * 3, 7)
al, bl = lokal(sl, cb, sd, sn)
Ls = 7.0
ta = np.clip(al / Ls, 0, 1)
krumm = 1.8 * ta ** 2.2                                  # Haken biegt nach innen
halb = np.where((al > -0.5) & (al < Ls), 2.0 * (1 - ta) ** 0.9 + 0.12, 0)
qb = np.where(halb > 0, ((bl + krumm) / np.maximum(halb, 1e-6)) ** 2, 9)
hs = np.where(qb < 1, E + (2.9 * (1 - 0.6 * ta) - E) * np.sqrt(np.clip(1 - qb, 0, 1)), -1)
hs -= np.where(qb < 1, 0.28 * np.exp(-(((bl + krumm) + 0.25 * halb) / 0.1) ** 2) * (ta < 0.75), 0)  # Mundspalte
H[sl] = np.maximum(H[sl], hs)

# Auge mit Ring und Braue
ca = ck + vorn * 0.6 + nk * 0.9
sl = box(ca, 3.5)
dx = X[sl] - ca[0]; dy = Y[sl] - ca[1]
rr = np.hypot(dx, dy)
H[sl] = H[sl] - 0.35 * np.exp(-((rr - 0.95) / 0.22) ** 2)        # Rille um das Auge
H[sl] = H[sl] + 0.35 * np.sqrt(np.clip(1 - (rr / 0.62) ** 2, 0, 1))
al, bl = lokal(sl, ca, vorn, nk)
braue = np.exp(-((bl - 1.05 - 0.25 * al) / 0.32) ** 2) * (al > -1.8) * (al < 1.6)
H[sl] = H[sl] + 0.55 * braue

# kleine Kopffedern am Hinterkopf
for (s, u) in [(0.0, 0.55), (0.0, -0.05), (0.03, 0.3), (0.03, -0.35), (0.06, 0.6), (0.06, 0.05), (0.06, -0.5)]:
    c, th = pos(s, u)
    t, n = rahmen(th)
    sl = box(c, 1.6)
    al, bl = lokal(sl, c, t, n)
    q = (al / 0.75) ** 2 + (bl / 0.5) ** 2
    m = q < 1
    h = H[sl]
    h[m] = h[m] + 0.22 * (0.4 + 0.6 * np.clip(al / 1.5 + 0.5, 0, 1))[m] * np.sqrt(np.clip((1 - q) * 4, 0, 1))[m]
    H[sl] = h

# ---- Schnörkel: erhabene Spiralen ----
def spirale(c, r0, dreh, umd=1.7, b=0.32, h=0.55):
    phi = np.linspace(0, umd * 2 * np.pi, 400)
    rr = r0 * (1 - phi / (umd * 2 * np.pi)) ** 1.1 + 0.15
    pts = c + np.stack([rr * np.cos(phi * dreh), rr * np.sin(phi * dreh)], 1)
    sl = box(c, r0 + 1)
    gitter = np.zeros(H[sl].shape, bool)
    ii = ((pts[:, 1] - Y[sl][0, 0]) / px).round().astype(int)
    jj = ((pts[:, 0] - X[sl][0, 0]) / px).round().astype(int)
    ok = (ii >= 0) & (ii < gitter.shape[0]) & (jj >= 0) & (jj < gitter.shape[1])
    gitter[ii[ok], jj[ok]] = True
    d = ndimage.distance_transform_edt(~gitter) * px
    H[sl] = np.where(H[sl] > 0, H[sl] + h * np.sqrt(np.clip(1 - (d / b) ** 2, 0, 1)), H[sl])


for (s, u, r0, dr) in [(0.3, -0.4, 2.7, 1), (0.56, 0.05, 2.9, 1), (0.76, -0.45, 2.5, 1)]:
    c, _ = pos(s, u)
    spirale(c, r0, dr)

# ---- Öse am Nacken ----
so = 0.07
co, tho = pos(so, 1.0)
_, no = rahmen(tho)
co = co + no * 2.0
sl = box(co, 4)
rr = np.hypot(X[sl] - co[0], Y[sl] - co[1])
ro, ri = 3.0, 1.65
v = (rr - (ro + ri) / 2) / ((ro - ri) / 2)
hoe = np.where(np.abs(v) < 1, 0.5 + 1.15 * np.sqrt(np.clip(1 - v ** 2, 0, 1)), -1)
H[sl] = np.maximum(H[sl], hoe)
H[sl] = np.where(rr < ri, -1, H[sl])

# ---- glätten (eine Rasterbreite), auf Endmaß bringen ----
H = ndimage.gaussian_filter(H, 0.9)
H = np.where(H < 0.25, -1, H)
Hmm = H * K
print(f"Raster {N}×{N}, {len(federn)} Federn, Dicke max {2 * Hmm.max():.2f} mm")

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
ls = matplotlib.colors.LightSource(azdeg=315, altdeg=40)
Hs = np.where(H > 0, H, 0)
bild = ls.shade(Hs[::-1], cmap=plt.cm.gray, vert_exag=6, blend_mode="soft", vmin=-1, vmax=A + 0.5)
bild[(H <= 0)[::-1]] = [0.05, 0.05, 0.06, 1]
plt.imsave(ziel / "vorschau.png", bild)
if a.nur_bild:
    raise SystemExit

# ---- Netze ----
import trimesh
from skimage import measure


def netz(F, z0, dz, name):
    F = np.pad(F, 1, constant_values=-1)
    v, f, _, _ = measure.marching_cubes(F, 0.0, spacing=(px * K, px * K, dz))
    v = v - np.array([px * K, px * K, dz])
    v = np.stack([v[:, 1] + ax[0] * K, v[:, 0] + ax[0] * K, v[:, 2] + z0], 1)
    m = trimesh.Trimesh(v, f[:, ::-1], process=True)
    m.fix_normals()
    try:
        import pymeshlab
        if len(m.faces) > a.max_dreiecke:
            ms = pymeshlab.MeshSet()
            ms.add_mesh(pymeshlab.Mesh(m.vertices, m.faces))
            ms.meshing_decimation_quadric_edge_collapse(targetfacenum=a.max_dreiecke, preservetopology=True,
                                                        preserveboundary=True, qualitythr=0.4)
            mm = ms.current_mesh()
            m = trimesh.Trimesh(mm.vertex_matrix(), mm.face_matrix(), process=True)
            m.fix_normals()
    except ImportError:
        pass
    m.export(ziel / name)
    print(f"{name}: {len(m.faces)} Dreiecke, dicht={m.is_watertight}, {m.volume:.0f} mm³, Maße {np.round(m.extents, 2)}")
    return m


dz = px * K
zmax = Hmm.max() + dz
zs = np.arange(-zmax, zmax + dz, dz)
F = Hmm[:, :, None] - np.abs(zs[None, None, :])
netz(F, zs[0], dz, "vogelring_ganz.stl")

# Hälften mit Passstift-Löchern
za = np.arange(0, zmax + dz, dz)
Fh = np.minimum(Hmm[:, :, None] - za[None, None, :], za[None, None, :] + 1e-3)
for s in (0.36, 0.7):
    c, _ = pos(s, 0.0)
    d = np.hypot(X * K - c[0] * K, Y * K - c[1] * K)[:, :, None] - 0.95
    loch = np.maximum(d, za[None, None, :] - 2.3)      # Ø 1,9, 2,3 mm tief
    Fh = np.minimum(Fh, -loch) if False else np.where((d < 0) & (za[None, None, :] < 2.3), np.minimum(Fh, d), Fh)
Fh[:, :, 0] = -1e-3 * 0 - 1                          # Boden offen schließen: Fläche bei z=0
mA = netz(np.concatenate([np.full(Fh[:, :, :1].shape, -1.0), Fh], 2), -dz, dz, "vogelring_haelfte_a.stl")
mB = mA.copy()
mB.apply_transform(trimesh.transformations.reflection_matrix([0, 0, 0], [1, 0, 0]))
mB.fix_normals()
mB.export(ziel / "vogelring_haelfte_b.stl")
print("Hälfte B = Spiegelbild von A (für die Rückseite)")
