#!/usr/bin/env python3
"""Fertige Figur (STL/OBJ/npz) für maximale Details aufbereiten – gedacht für die 0,25-mm-Düse mit 0,08-mm-Schichten.

  python3 -I werkzeug/verfeinern.py figur.stl --aus /tmp/f/figur_fein.stl [--kante 0.22] [--fein 1.2] [--mittel 0.6]
          [--korn 0.06] [--korn-zelle 0.45] [--skala 1.0] [--drehen-z 0] [--bett] [--glatt-unter 0.4] [--bild /tmp/f/v.png]

Was passiert (die Form bleibt, nur die Oberfläche wird schärfer):
  1. Netz verdichten, bis keine Kante länger als --kante ist (sonst gibt es nichts, worin feine Struktur stehen könnte).
  2. Vorhandene Struktur verstärken: der Abstand zur leicht geglätteten Fläche (≈ 0,4 mm) wird um --fein vergrößert,
     das Band bis zur stark geglätteten Fläche (≈ 1,3 mm) um --mittel. Schuppen, Fugen, Adern werden tiefer und kantiger.
  3. Feines Korn (Zellmuster, nur nach innen) als Hautstruktur – --korn 0 schaltet es ab.
  Standfläche (unterste --glatt-unter mm) bleibt unverändert. --bett legt das Teil für druck.py --zusammen mittig aufs Bett (128/128, z = 0).
Grenze: es entsteht keine neue Form, nur schärfere und feinere Oberfläche. Vorher/Nachher-Bild mit --bild ansehen."""
import argparse, sys, math, numpy as np


def laden(p):
    if p.endswith(".npz"):
        d = np.load(p); return d["v"].astype(np.float64), d["f"].astype(np.int64)
    import trimesh
    t = trimesh.load(p, force="mesh"); return np.asarray(t.vertices, np.float64), np.asarray(t.faces, np.int64)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ein"); ap.add_argument("--aus", required=True)
    ap.add_argument("--kante", type=float, default=0.22); ap.add_argument("--fein", type=float, default=1.2); ap.add_argument("--mittel", type=float, default=0.6)
    ap.add_argument("--korn", type=float, default=0.06); ap.add_argument("--korn-zelle", type=float, default=0.45)
    ap.add_argument("--skala", type=float, default=1.0); ap.add_argument("--drehen-z", type=float, default=0.0)
    ap.add_argument("--bett", action="store_true"); ap.add_argument("--glatt-unter", type=float, default=0.4)
    ap.add_argument("--band-fein", type=float, default=0.4); ap.add_argument("--band-mittel", type=float, default=1.5)
    ap.add_argument("--grenze", type=float, default=0.45, help="größte Verschiebung je Punkt in mm")
    ap.add_argument("--max-dreiecke", type=float, default=4.5e6); ap.add_argument("--bild", default=""); ap.add_argument("--zoom", type=float, default=3.0)
    a = ap.parse_args()
    import pymeshlab, trimesh
    from scipy.spatial import cKDTree
    v, f = laden(a.ein)
    if a.skala != 1.0: v = v * a.skala
    if a.drehen_z:
        w = math.radians(a.drehen_z); c, s = math.cos(w), math.sin(w); v = v @ np.array([[c, s, 0], [-s, c, 0], [0, 0, 1]])
    v[:, 2] -= v[:, 2].min()
    print(f"Eingang: {len(f):,} Dreiecke, Maße {np.ptp(v, axis=0).round(1)} mm".replace(",", "."))
    ms = pymeshlab.MeshSet(); ms.add_mesh(pymeshlab.Mesh(v, f))
    ms.meshing_remove_duplicate_vertices(); ms.meshing_remove_duplicate_faces(); ms.meshing_remove_null_faces()
    for _ in range(3):                                # Unterteilen braucht ein mannigfaltiges Netz
        ms.meshing_repair_non_manifold_edges(method=0); ms.meshing_repair_non_manifold_vertices()
    ms.meshing_remove_unreferenced_vertices()
    # 1. verdichten – die Zielkante wird größer gewählt, wenn das Netz sonst zu schwer würde
    flaeche = ms.get_geometric_measures()["surface_area"]
    kante = max(a.kante, math.sqrt(flaeche / (a.max_dreiecke * 0.21)))
    if kante > a.kante + 1e-6: print(f"Hinweis: Fläche {flaeche / 100:.0f} cm² → Kante {kante:.2f} statt {a.kante:.2f} mm (sonst über {a.max_dreiecke / 1e6:.1f} Mio. Dreiecke)")
    for _ in range(6):
        vor = ms.current_mesh().face_number()
        ms.meshing_surface_subdivision_midpoint(iterations=1, threshold=pymeshlab.PureValue(kante))
        if ms.current_mesh().face_number() <= vor * 1.02 or ms.current_mesh().face_number() > a.max_dreiecke: break
    m = ms.current_mesh(); v = m.vertex_matrix().copy(); f = m.face_matrix().copy()
    print(f"verdichtet: {len(f):,} Dreiecke (Kante ≤ {kante:.2f} mm)".replace(",", "."))
    # mittlere Kantenlänge → Zahl der Glättungsschritte für eine Reichweite in mm (Reichweite ≈ Kante · √Schritte)
    e = np.linalg.norm(v[f[:, 0]] - v[f[:, 1]], axis=1); em = float(np.median(e))
    def glatt(reichweite):                            # einfache Laplace-Glättung; Reichweite ≈ Kante · √(Schritte / 2)
        n = int(np.clip(2 * (reichweite / em) ** 2, 3, 900))
        ms2 = pymeshlab.MeshSet(); ms2.add_mesh(pymeshlab.Mesh(v, f)); ms2.apply_coord_laplacian_smoothing(stepsmoothnum=n, cotangentweight=False)
        ms2.compute_normal_per_vertex(); mm = ms2.current_mesh(); nn = mm.vertex_normal_matrix()
        return mm.vertex_matrix().copy(), nn / np.maximum(np.linalg.norm(nn, axis=1), 1e-9)[:, None]
    g1, _ = glatt(a.band_fein); g2, n2 = glatt(a.band_mittel)
    d_fein = np.einsum("ij,ij->i", v - g1, n2); d_mittel = np.einsum("ij,ij->i", g1 - g2, n2)
    versatz = a.fein * d_fein + a.mittel * d_mittel
    print(f"vorhandene Struktur: fein ±{np.percentile(np.abs(d_fein), 95):.2f} mm, mittel ±{np.percentile(np.abs(d_mittel), 95):.2f} mm (95 %)")
    # 3. Korn: Zellmuster, Rille an den Zellgrenzen, nur nach innen
    if a.korn > 0:
        Z = max(a.korn_zelle, 2.5 * kante)                 # Zelle braucht mindestens 2–3 Netzkanten, sonst wird es Rauschen
        if Z > a.korn_zelle + 1e-6: print(f"Hinweis: Korn-Zelle {Z:.2f} statt {a.korn_zelle:.2f} mm (Netz gröber)")
        zelle = np.floor(v / Z).astype(np.int64); best = np.full(len(v), 9.0); zweit = np.full(len(v), 9.0)
        def kern(c):                                  # fester Zufallspunkt je Gitterzelle
            h = (c[:, 0] * 73856093) ^ (c[:, 1] * 19349663) ^ (c[:, 2] * 83492791)
            r = np.stack([((h * k) % 1000003) / 1000003.0 for k in (1, 7919, 104729)], 1); return (c + r) * Z
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for dz in (-1, 0, 1):
                    dd = np.linalg.norm(v - kern(zelle + np.array([dx, dy, dz])), axis=1)
                    neu_best = np.minimum(best, dd); zweit = np.minimum(zweit, np.maximum(best, dd)); best = neu_best
        rille = np.clip(1 - (zweit - best) / (0.32 * Z), 0, 1) ** 1.5
        versatz = versatz - a.korn * rille
    versatz = np.clip(versatz, -a.grenze, a.grenze)
    unten = np.clip((v[:, 2] - a.glatt_unter) / 0.6, 0, 1)        # Standfläche bleibt
    vneu = v + n2 * (versatz * unten)[:, None]
    vneu[:, 2] = np.maximum(vneu[:, 2], 0)
    if a.bett:
        mitte = (vneu[:, :2].min(0) + vneu[:, :2].max(0)) / 2; vneu[:, :2] += 128 - mitte
    t = trimesh.Trimesh(vneu, f, process=False); t.export(a.aus)
    print(f"geschrieben: {a.aus} · {len(f):,} Dreiecke · Maße {np.ptp(vneu, axis=0).round(1)} mm · dicht: {t.is_watertight}".replace(",", "."))
    if a.bild:
        import pyvista as pv
        pv.OFF_SCREEN = True
        def netz(p): return pv.PolyData(p, np.hstack([np.full((len(f), 1), 3), f]).ravel())
        c = (vneu.min(0) + vneu.max(0)) / 2; r = float(np.abs(vneu - c).max()); vv = v.copy()
        if a.bett: vv[:, :2] += 128 - (v[:, :2].min(0) + v[:, :2].max(0)) / 2
        from PIL import Image
        teile = []
        for p_, name in ((vv, "vorher"), (vneu, "nachher")):
            pl = pv.Plotter(shape=(1, 3), window_size=(2100, 700)); m_ = netz(p_)
            for j, (k, zo) in enumerate((((2.4, -2.6, 1.8), 1.0), ((1.2, -1.4, 0.9), a.zoom), ((-1.4, 1.2, 1.1), a.zoom))):
                pl.subplot(0, j); pl.add_mesh(m_, color="#b9bdc4", smooth_shading=False, specular=0.35)
                pl.camera_position = [tuple(c + np.array(k) * r), tuple(c), (0, 0, 1)]; pl.camera.zoom(zo); pl.add_text(name, font_size=10)
            teile.append(Image.fromarray(pl.screenshot(None))); pl.close(); del m_
        b = Image.new("RGB", (2100, 1400)); b.paste(teile[0], (0, 0)); b.paste(teile[1], (0, 700)); b.save(a.bild)

if __name__ == "__main__":
    main()
