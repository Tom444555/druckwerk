#!/usr/bin/env python3
"""Albatros – Schlüsselanhänger, eigener Entwurf (18.11.2026): runde Scheibe Ø 44 mm, beidseitig gewölbtes Relief (gleitender Albatros über Wellen), Öse oben.
   python3 modelle/albatros.py --ziel /tmp/alb [--halb]   → albatros.stl (ganz, beidseitig) und albatros_haelfte.stl (eine Seite, flach zum Drucken und Kleben)"""
import argparse, math
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi
import manifold3d as mf, trimesh

ap = argparse.ArgumentParser(); ap.add_argument("--ziel", default="/tmp/alb"); ap.add_argument("--raster", type=float, default=0.1); a = ap.parse_args()
R = 22.0                      # Radius der Scheibe
RAND, KERN = 1.15, 2.25       # halbe Dicke am Rand / in der Mitte (Wölbung „halbrund“)
OESE_Y, OESE_RA, OESE_RI, OESE_H = 24.6, 4.2, 2.1, 1.3
PX = 0.05                     # Zeichenraster in mm
X0, X1, Y0, Y1 = -24.0, 24.0, -24.0, 30.0
W, H = int((X1 - X0) / PX), int((Y1 - Y0) / PX)
px = lambda p: [((x - X0) / PX, (Y1 - y) / PX) for x, y in p]
yy, xx = np.mgrid[0:H, 0:W]; X = X0 + (xx + 0.5) * PX; Y = Y1 - (yy + 0.5) * PX; RR = np.hypot(X, Y)

def maske(*polys, kreise=()):
    im = Image.new("L", (W, H), 0); d = ImageDraw.Draw(im)
    for p in polys: d.polygon(px(p), fill=255)
    for (cx, cy, r) in kreise: d.ellipse(px([(cx - r, cy + r)]) + px([(cx + r, cy - r)]), fill=255)
    return np.asarray(im) > 127
def band(mitte, breiten, n=60):          # weiche Fläche entlang einer Mittellinie (Catmull-Rom) mit wechselnder Breite
    m = np.array(mitte, float); t = np.linspace(0, len(m) - 1, n); i = np.clip(t.astype(int), 0, len(m) - 2); f = (t - i)[:, None]
    P = lambda k: m[np.clip(k, 0, len(m) - 1)]
    c = 0.5 * ((2 * P(i)) + (-P(i - 1) + P(i + 1)) * f + (2 * P(i - 1) - 5 * P(i) + 4 * P(i + 1) - P(i + 2)) * f ** 2 + (-P(i - 1) + 3 * P(i) - 3 * P(i + 1) + P(i + 2)) * f ** 3)
    b = np.interp(t, np.arange(len(breiten)), breiten); g = np.gradient(c, axis=0); nrm = np.stack([-g[:, 1], g[:, 0]], 1); nrm /= np.linalg.norm(nrm, axis=1, keepdims=True)
    return [tuple(q) for q in (c + nrm * b[:, None] / 2)] + [tuple(q) for q in (c - nrm * b[:, None] / 2)[::-1]], c
def kissen(m, hoch, weit):               # aufgeblasene Form: Höhe wächst mit dem Abstand zum Rand (runder Querschnitt)
    d = ndi.distance_transform_edt(m) * PX; return hoch * np.sqrt(np.clip(1 - (1 - np.clip(d / weit, 0, 1)) ** 2, 0, 1))

# --- Grundkörper: Linse + Randwulst
h = RAND + (KERN - RAND) * np.sqrt(np.clip(1 - (RR / R) ** 2, 0, 1))
wulst = np.clip(1 - ((RR - (R - 1.0)) / 1.0) ** 2, 0, 1); h += 0.55 * np.sqrt(wulst) * (RR <= R)
# --- Wellen unten: drei Kämme, nach oben auslaufend
for k, (y0, amp, lam, ph) in enumerate([(-10.5, 1.0, 13.0, 0.4), (-14.0, 1.2, 11.0, 2.1), (-17.4, 1.0, 9.0, 4.0)]):
    kamm = y0 + amp * np.sin(X / lam * 2 * math.pi + ph) + 0.35 * np.sin(X / 3.1 + ph * 2)
    t = (kamm - Y) / 3.0                                         # 0 am Kamm, 1 am Fuß
    prof = np.where((t >= 0) & (t <= 1), 0.75 * (1 - t) ** 1.6, 0) + np.where((t < 0) & (t > -0.18), 0.75 * (1 + t / 0.18), 0)
    h += prof * (RR < R - 1.9) * np.clip((R - 1.9 - RR) / 1.0, 0, 1)
# --- Albatros im Gleitflug: lange schmale Flügel, Körper schräg, Kopf mit langem Hakenschnabel
fl_l, ml = band([(-0.6, 0.8), (-6.5, 4.6), (-13.0, 5.6), (-19.0, 2.4)], [4.6, 4.3, 3.2, 0.7])
fl_r, mr = band([(1.2, 0.2), (7.0, 3.4), (13.2, 3.3), (18.8, -0.9)], [4.6, 4.2, 3.0, 0.7])
rumpf, _ = band([(-3.3, -7.4), (-1.2, -3.0), (0.6, 1.2), (2.1, 5.2), (3.0, 7.6)], [1.2, 4.6, 5.2, 3.6, 2.9])
schwanz = [(-2.2, -5.6), (-5.4, -9.6), (-3.6, -9.9), (-2.4, -9.0), (-1.6, -9.9), (-0.2, -6.0)]
schnabel, _ = band([(3.2, 8.2), (4.6, 10.4), (6.2, 12.2), (7.5, 12.5), (7.9, 11.4)], [1.9, 1.5, 1.1, 0.9, 0.3])
kopf = (3.05, 7.7, 2.05)
vogel = np.zeros_like(h)
for m, hoch, weit in [(maske(fl_l), 0.95, 1.5), (maske(fl_r), 0.95, 1.5), (maske(schwanz), 0.55, 0.9), (maske(rumpf), 1.45, 2.2), (maske(kreise=[kopf]), 1.45, 1.7), (maske(schnabel), 1.0, 0.6)]:
    vogel = np.maximum(vogel, kissen(m, hoch, weit))
# Federn: Schwungfedern als Rillen quer zum Flügel, außen dichter; Armdecken als zweite Reihe
rille = np.zeros_like(h)
def federn(mitte, seite):
    for i in range(8, len(mitte) - 3, 3):
        p, q = mitte[i], mitte[i + 1]; r_ = np.array([q[0] - p[0], q[1] - p[1]]); r_ /= np.linalg.norm(r_)
        schraeg = r_ * 0.75 + np.array([r_[1], -r_[0]]) * (-0.66)          # nach hinten außen geneigt
        d = np.abs((X - p[0]) * schraeg[1] - (Y - p[1]) * schraeg[0]) / np.linalg.norm(schraeg); laengs = (X - p[0]) * schraeg[0] + (Y - p[1]) * schraeg[1]
        rille[:] = np.maximum(rille, np.clip(1 - d / 0.2, 0, 1) * ((laengs > -0.2) & (laengs < 3.2)))
federn(ml, -1); federn(mr[:, ::1], 1)
fl = maske(fl_l) | maske(fl_r)
vogel -= 0.28 * rille * fl * (vogel > 0.3)
dz = ndi.distance_transform_edt(fl) * PX; vogel += 0.16 * np.clip(1 - np.abs(dz - 1.25) / 0.22, 0, 1) * fl * 0  # (Stufe der Decken: aus – zu fein für 0,4-mm-Düse)
auge = np.hypot(X - 3.55, Y - 8.1) < 0.36; vogel = np.where(auge, vogel - 0.35, vogel)
vogel = ndi.gaussian_filter(vogel, 0.06 / PX)
h = np.where(vogel > 0.02, np.maximum(h, h * 0 + 0) + vogel, h)
# --- Öse: flach, außerhalb der Scheibe
oese = (np.hypot(X, Y - OESE_Y) <= OESE_RA + 0.2) & (RR > R - 0.3)
h = np.where(RR <= R, h, np.where(oese, OESE_H, 0.06))
h = ndi.gaussian_filter(h, 0.05 / PX)

# --- Netz: Höhenfeld oben, gespiegelt unten (oder plan), danach mit dem Umriss schneiden
s = max(1, round(a.raster / PX)); hz = h[::s, ::s]; Xs, Ys = X[::s, ::s], Y[::s, ::s]; n, m_ = hz.shape
def koerper(unten):
    v = np.concatenate([np.stack([Xs, Ys, hz], -1).reshape(-1, 3), np.stack([Xs, Ys, unten], -1).reshape(-1, 3)]); idx = np.arange(n * m_).reshape(n, m_); o = n * m_
    A, B, C, D = idx[:-1, :-1].ravel(), idx[:-1, 1:].ravel(), idx[1:, :-1].ravel(), idx[1:, 1:].ravel()
    f = [np.stack([A, C, B], 1), np.stack([B, C, D], 1), np.stack([A + o, B + o, C + o], 1), np.stack([B + o, D + o, C + o], 1)]
    rand = np.concatenate([idx[0, :], idx[1:, -1], idx[-1, -2::-1], idx[-2:0:-1, 0]]); r2 = np.roll(rand, -1)
    f += [np.stack([rand, r2, rand + o], 1), np.stack([r2, r2 + o, rand + o], 1)]
    k = mf.Manifold(mf.Mesh(vert_properties=v.astype(np.float32), tri_verts=np.concatenate(f).astype(np.uint32)))
    if k.volume() < 0: k = mf.Manifold(mf.Mesh(vert_properties=v.astype(np.float32), tri_verts=np.concatenate(f)[:, ::-1].astype(np.uint32)))
    kreis = lambda r, cx=0, cy=0, seg=240: [[cx + r * math.cos(t), cy + r * math.sin(t)] for t in np.linspace(0, 2 * math.pi, seg, endpoint=False)]
    umriss = (mf.CrossSection([kreis(R)]) + mf.CrossSection([kreis(OESE_RA, 0, OESE_Y, 96)])) - mf.CrossSection([kreis(OESE_RI, 0, OESE_Y, 64)])
    return k ^ umriss.extrude(20).translate((0, 0, -10))
ziel = Path(a.ziel); ziel.mkdir(parents=True, exist_ok=True)
for name, unten in (("albatros", -hz), ("albatros_haelfte", np.zeros_like(hz))):
    k = koerper(unten); me = k.to_mesh(); t = trimesh.Trimesh(me.vert_properties[:, :3], me.tri_verts, process=True)
    t.export(ziel / f"{name}.stl"); print(f"{name}.stl: dicht={t.is_watertight}, {len(t.faces)} Dreiecke, Maße {np.round(t.extents, 1)} mm, {t.volume / 1000 * 1.24:.1f} g PLA massiv")
