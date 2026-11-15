#!/usr/bin/env python3
"""Schnelles Prüfbild (ohne GPU, wenige Sekunden): vier Ansichten + Schnitt + Maßkasten in einer PNG.

Aufruf:   python3 werkzeug/ansichten.py teil_schwarz.stl teil_gold.stl --aus /tmp/teil.png [--farben schwarz,gold]
                    [--schnitt x|y|z] [--bei <mm>] [--titel "Gitarrenhalter"]
Ansichten: vorne (von −Y), rechts (von +X), oben (von +Z), schräg (perspektivisch), Schnitt durch die Mitte
(oder bei --bei mm) und Maßkasten (B × T × H, Volumen je Datei, Dreiecke).
Farben: deutsche Namen (schwarz, gold, rot, weiss/weiß, grau, blau, gruen/grün, orange, natur, tpu) oder #hex;
ohne --farben werden die Namen aus dem Dateinamen gelesen (…_gold.stl), sonst eine Standard-Reihe.
Technik: PyVista/VTK offscreen über EGL (Mesa, CPU) – Rückfall auf das VTK-Standardfenster; Schnitt mit trimesh+matplotlib.
"""
import argparse
import os
import sys
import time

os.environ.setdefault("VTK_DEFAULT_OPENGL_WINDOW", "vtkEGLRenderWindow")   # ohne X-Server, ohne GPU

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import trimesh  # noqa: E402
from matplotlib.patches import PathPatch  # noqa: E402
from matplotlib.path import Path as MPath  # noqa: E402

FARBEN = {"schwarz": "#3b3d42", "gold": "#d4a52a", "rot": "#c8322d", "weiss": "#eeeeea", "weiß": "#eeeeea",
          "grau": "#9a9ea6", "blau": "#2f6fd0", "gruen": "#3a9a4a", "grün": "#3a9a4a", "orange": "#ee7d22",
          "natur": "#e6dcc4", "tpu": "#4a4f57", "silber": "#c4c8cc", "gelb": "#f2cf2a", "lila": "#7d4fc2"}
REIHE = ["grau", "gold", "rot", "blau", "weiss", "gruen"]


def farbe_fuer(name, vorgabe=None, i=0):
    if vorgabe:
        return FARBEN.get(vorgabe.lower(), vorgabe)
    stem = os.path.basename(name).rsplit(".", 1)[0].lower()
    for k in FARBEN:
        if stem.endswith("_" + k) or stem.endswith("-" + k):
            return FARBEN[k]
    return FARBEN[REIHE[i % len(REIHE)]]


def _pv_mesh(t):
    import pyvista as pv
    f = np.hstack([np.full((len(t.faces), 1), 3), t.faces]).astype(np.int64).ravel()
    return pv.PolyData(np.asarray(t.vertices, float), f)


def ansichten_rendern(netze, farben, groesse=(700, 560)):
    """Gibt dict name → RGB-Bild (numpy) für vorne/rechts/oben/schräg zurück."""
    import pyvista as pv
    pv.OFF_SCREEN = True
    lo = np.min([t.bounds[0] for t in netze], axis=0); hi = np.max([t.bounds[1] for t in netze], axis=0)
    mitte = (lo + hi) / 2; diag = float(np.linalg.norm(hi - lo))
    pl = pv.Plotter(off_screen=True, window_size=groesse, lighting="three lights")
    pl.set_background("#f4f5f7", top="#ffffff")
    for t, c in zip(netze, farben):
        m = _pv_mesh(t)
        pl.add_mesh(m, color=c, smooth_shading=True, split_sharp_edges=True, feature_angle=35,
                    specular=0.25, specular_power=20, ambient=0.18, diffuse=0.8)
        kanten = m.extract_feature_edges(feature_angle=35, boundary_edges=False, non_manifold_edges=False,
                                         manifold_edges=False)
        if kanten.n_cells:
            pl.add_mesh(kanten, color="#1c1e22" if c != FARBEN["schwarz"] else "#9da3ad", line_width=1.2)
    # Bettplatte als dezente Linie unter dem Teil
    platte = pv.Plane(center=(mitte[0], mitte[1], lo[2] - 0.05), i_size=(hi[0] - lo[0]) * 1.3 + 10,
                      j_size=(hi[1] - lo[1]) * 1.3 + 10)
    pl.add_mesh(platte, color="#d9dce1", ambient=0.6, opacity=0.6)
    bilder = {}
    dist = diag * 2.2
    sichten = {
        "vorne (von −Y)": ((0, -1, 0), (0, 0, 1), True),
        "rechts (von +X)": ((1, 0, 0), (0, 0, 1), True),
        "oben (von +Z)": ((0, 0, 1), (0, 1, 0), True),
        "schräg": ((0.9, -1.25, 0.85), (0, 0, 1), False),
    }
    for name, (richtung, oben, parallel) in sichten.items():
        r = np.asarray(richtung, float); r /= np.linalg.norm(r)
        pl.camera.focal_point = mitte
        pl.camera.position = mitte + r * dist
        pl.camera.up = oben
        if parallel:
            pl.enable_parallel_projection()
        else:
            pl.disable_parallel_projection()
        pl.reset_camera()
        if parallel:                                       # Maßstab so, dass das Teil das Feld füllt
            ecken = np.array([[x, y, z] for x in (lo[0], hi[0]) for y in (lo[1], hi[1]) for z in (lo[2], hi[2])])
            u = np.asarray(oben, float); rechts = np.cross(u, r)
            h = np.ptp(ecken @ u); w = np.ptp(ecken @ rechts)
            pl.camera.parallel_scale = max(h / 2, w / 2 / (groesse[0] / groesse[1])) * 1.12 + 0.5
        else:
            pl.camera.zoom(1.3)
        bilder[name] = pl.screenshot(return_img=True)
    pl.close()
    return bilder


def _schnitt_schleifen(t, achse, bei):
    """Schnittlinien als geschlossene 2D-Schleifen (Achsen: x→(Y,Z), y→(X,Z), z→(X,Y))."""
    n = {"x": (1, 0, 0), "y": (0, 1, 0), "z": (0, 0, 1)}[achse]
    o = np.zeros(3); o["xyz".index(achse)] = bei
    try:
        p = t.section(plane_origin=o, plane_normal=n)
    except Exception:
        return []
    if p is None:
        return []
    ix = {"x": (1, 2), "y": (0, 2), "z": (0, 1)}[achse]
    aus = []
    for kurve in p.discrete:
        k = np.asarray(kurve)[:, ix]
        if len(k) >= 3:
            aus.append(k)
    return aus


def _flaechen_patch(schleifen, farbe):
    """Schleifen zu einer gefüllten Fläche mit Löchern (Verschachtelungstiefe → Umlaufsinn)."""
    pfade = [MPath(s) for s in schleifen]
    verts, codes = [], []
    for i, s in enumerate(schleifen):
        tiefe = sum(pfade[j].contains_point(s[0]) for j in range(len(schleifen)) if j != i)
        fl = 0.5 * np.sum(s[:-1, 0] * s[1:, 1] - s[1:, 0] * s[:-1, 1])
        if (tiefe % 2 == 0) != (fl > 0):
            s = s[::-1]
        verts.extend(s.tolist()); codes.extend([MPath.MOVETO] + [MPath.LINETO] * (len(s) - 2) + [MPath.CLOSEPOLY])
    return PathPatch(MPath(verts, codes), facecolor=farbe, edgecolor="#1c1e22", lw=0.6)


def bild(stl, aus, farben=None, schnitt="y", bei=None, titel=None):
    t0 = time.time()
    netze = [trimesh.load(p, force="mesh") for p in stl]
    vorgaben = (farben.split(",") if farben else [None] * len(stl))
    vorgaben += [None] * (len(stl) - len(vorgaben))
    cols = [farbe_fuer(p, v, i) for i, (p, v) in enumerate(zip(stl, vorgaben))]
    lo = np.min([t.bounds[0] for t in netze], axis=0); hi = np.max([t.bounds[1] for t in netze], axis=0)
    ext = hi - lo
    bei = (lo + hi)["xyz".index(schnitt)] / 2 if bei is None else bei
    bilder = ansichten_rendern(netze, cols)
    t_render = time.time() - t0

    fig = plt.figure(figsize=(15, 9.4), dpi=100, facecolor="white")
    gs = fig.add_gridspec(2, 3, wspace=0.03, hspace=0.08, left=0.01, right=0.99, top=0.93, bottom=0.02)
    for k, (name, img) in enumerate(bilder.items()):
        ax = fig.add_subplot(gs[k // 2, k % 2] if k < 2 else gs[1, k - 2])
        ax.imshow(img); ax.set_axis_off(); ax.set_title(name, fontsize=11, color="#333")
    # Schnitt
    ax = fig.add_subplot(gs[0, 2]); ax.set_aspect("equal")
    ix = {"x": (1, 2), "y": (0, 2), "z": (0, 1)}[schnitt]
    for t, c in zip(netze, cols):
        s = _schnitt_schleifen(t, schnitt, bei)
        if s:
            ax.add_patch(_flaechen_patch(s, c))
    ax.set_xlim(lo[ix[0]] - 2, hi[ix[0]] + 2); ax.set_ylim(lo[ix[1]] - 2, hi[ix[1]] + 2)
    ax.grid(True, color="#e3e5e8", lw=0.6); ax.tick_params(labelsize=8)
    ax.set_xlabel("XYZ"[ix[0]] + " [mm]", fontsize=9); ax.set_ylabel("XYZ"[ix[1]] + " [mm]", fontsize=9)
    ax.set_title(f"Schnitt {schnitt} = {bei:.1f} mm", fontsize=11, color="#333")
    # Maßkasten
    ax = fig.add_subplot(gs[1, 2]); ax.set_axis_off()
    zeilen = [("Breite X", f"{ext[0]:.1f} mm"), ("Tiefe Y", f"{ext[1]:.1f} mm"), ("Höhe Z", f"{ext[2]:.1f} mm")]
    vol = 0.0
    y = 0.95
    ax.text(0.02, y, "Maße", fontsize=13, weight="bold", color="#222", transform=ax.transAxes); y -= 0.09
    for a, b in zeilen:
        ax.text(0.04, y, a, fontsize=11, transform=ax.transAxes); ax.text(0.55, y, b, fontsize=11, transform=ax.transAxes)
        y -= 0.07
    y -= 0.03
    ax.text(0.02, y, "Dateien", fontsize=13, weight="bold", color="#222", transform=ax.transAxes); y -= 0.08
    for p, t, c in zip(stl, netze, cols):
        v = abs(t.volume) / 1000 if t.is_watertight else float("nan"); vol += 0 if np.isnan(v) else v
        ax.add_patch(plt.Rectangle((0.04, y - 0.01), 0.035, 0.045, color=c, ec="#222", lw=0.5, transform=ax.transAxes))
        ax.text(0.10, y, f"{os.path.basename(p)[:34]}", fontsize=9.5, transform=ax.transAxes)
        ax.text(0.10, y - 0.045, f"{v:.2f} cm³ · {len(t.faces):,} Dreiecke".replace(",", "."), fontsize=8.5,
                color="#555", transform=ax.transAxes)
        y -= 0.11
    ax.text(0.04, y, f"Volumen gesamt {vol:.2f} cm³ (≈ {vol * 1.24:.0f} g PLA bei 100 %)", fontsize=10,
            transform=ax.transAxes)
    fig.suptitle(titel or os.path.basename(stl[0]).rsplit(".", 1)[0], fontsize=15, weight="bold", x=0.01, ha="left")
    fig.savefig(aus, dpi=100)
    plt.close(fig)
    return time.time() - t0, t_render


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("stl", nargs="+"); ap.add_argument("--aus", required=True)
    ap.add_argument("--farben"); ap.add_argument("--schnitt", choices=["x", "y", "z"], default="y")
    ap.add_argument("--bei", type=float); ap.add_argument("--titel")
    a = ap.parse_args()
    ges, ren = bild(a.stl, a.aus, a.farben, a.schnitt, a.bei, a.titel)
    print(f"{a.aus}: geschrieben in {ges:.1f} s (davon 3D {ren:.1f} s)")


if __name__ == "__main__":
    sys.exit(main())
