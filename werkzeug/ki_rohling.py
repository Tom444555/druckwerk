#!/usr/bin/env python3
"""KI-Netz (Rodin, TRELLIS, Hunyuan, Meshy …) → druckfertiger Rohling.

Ablauf: laden (alle Teile der Szene, Textur/Vertexfarben bleiben als Farbquelle erhalten) → Z nach oben →
auf Zielgröße skalieren → Löcher flicken → Voxel-Hülle (Innenflächen, Selbstschnitte, Restlöcher
verschwinden; wasserdicht) → Oberfläche zurück auf das Original ziehen (Details bleiben, Abweichung < 1 Voxel)
→ lose Splitter weg → optional dünne Stellen verdicken → glätten → aufrichten → Standfläche (Schnitt oder Sockel)
→ optional aushöhlen → auf max. Dreiecke vereinfachen → prüfen (dicht, dünne Stellen, Überhänge).

Aufruf:
  python3 werkzeug/ki_rohling.py figur.glb --ziel-mm 80 --aus /tmp/figur
  python3 werkzeug/ki_rohling.py figur.glb --ziel-mm 120 --aus /tmp/figur --boden sockel --glatt 1 --hohl 2

Ergebnis im Ordner --aus:  <name>.stl · <name>_farbig.glb (nur wenn das Original Farbe hat; Eingang für
textur_farben.py) · info.json · vorschau.png
"""
import argparse, json, sys, time
from pathlib import Path

import numpy as np
import trimesh
from scipy import ndimage
from scipy.spatial import cKDTree


# ======================= Laden + Farbquelle (auch von textur_farben.py benutzt) =======================
def lade_teile(pfad):
    """Alle Netze der Datei mit angewendeter Szenen-Transformation (Farbe/Textur bleibt am Netz)."""
    sc = trimesh.load(str(pfad), force="scene", process=False)
    teile = []
    for node in sc.graph.nodes_geometry:
        T, gname = sc.graph[node]
        g = sc.geometry[gname]
        if not isinstance(g, trimesh.Trimesh) or len(g.faces) == 0:
            continue
        g = g.copy(); g.apply_transform(T); teile.append(g)
    if not teile:
        sys.exit(f"Keine Dreiecksnetze in {pfad}")
    return teile


def _bild_holen(mat):
    for k in ("baseColorTexture", "image"):
        im = getattr(mat, k, None)
        if im is not None:
            return np.asarray(im.convert("RGB"), np.float32)
    return None


def _faktor(mat, mit_textur=True):
    """Farbfaktor: bei Textur nur glTF-baseColorFactor (OBJ-Kd ist oft ein Platzhalter), sonst Grundfarbe."""
    f = getattr(mat, "baseColorFactor", None)
    if f is None and not mit_textur:
        f = getattr(mat, "main_color", None)
        if f is None:
            f = getattr(mat, "diffuse", None)
    if f is None:
        return np.ones(3, np.float32)
    f = np.asarray(f, np.float32)[:3]
    return f / 255.0 if f.max() > 1.0 else f


def hat_farbe(m):
    v = m.visual
    if v.kind == "texture" and getattr(v, "uv", None) is not None and _bild_holen(v.material) is not None:
        return True
    if v.kind in ("vertex", "face"):
        c = v.vertex_colors if v.kind == "vertex" else v.face_colors
        return np.ptp(np.asarray(c)[:, :3], axis=0).max() > 0
    return False


def farbe_an(m, p, fi):
    """RGB (0–255) an Oberflächenpunkten p (auf Fläche fi) – aus Textur (bilinear), Vertex- oder Flächenfarben."""
    v = m.visual
    bary = trimesh.triangles.points_to_barycentric(m.triangles[fi], p)
    kaputt = ~np.isfinite(bary).all(1) | (bary.min(1) < -0.01)    # entartete Dreiecke (Splitter, Nadeln)
    bary[kaputt] = 1.0 / 3; bary = np.clip(bary, 0, 1); bary /= bary.sum(1, keepdims=True)
    if v.kind == "texture" and getattr(v, "uv", None) is not None:
        img = _bild_holen(v.material)
        if img is not None:
            uv = (bary[:, :, None] * np.asarray(v.uv)[m.faces[fi]]).sum(1)
            h, w = img.shape[:2]
            x = (uv[:, 0] % 1.0) * (w - 1); y = (1.0 - (uv[:, 1] % 1.0)) * (h - 1)
            x0, y0 = np.floor(x).astype(int), np.floor(y).astype(int)
            x1, y1 = np.minimum(x0 + 1, w - 1), np.minimum(y0 + 1, h - 1)
            fx, fy = (x - x0)[:, None], (y - y0)[:, None]
            c = (img[y0, x0] * (1 - fx) * (1 - fy) + img[y0, x1] * fx * (1 - fy)
                 + img[y1, x0] * (1 - fx) * fy + img[y1, x1] * fx * fy)
            return c * _faktor(v.material)
    if v.kind == "vertex":
        vc = np.asarray(v.vertex_colors, np.float32)[:, :3]
        return (bary[:, :, None] * vc[m.faces[fi]]).sum(1)
    if v.kind == "face":
        return np.asarray(v.face_colors, np.float32)[fi, :3]
    if v.kind == "texture":
        return np.tile(_faktor(v.material, False) * 255, (len(p), 1))
    return np.full((len(p), 3), 170.0, np.float32)


class FarbQuelle:
    """Dichte Stichprobe der Original-Oberfläche: Punkt, Flächennormale, Farbe. Nachschlagen per k-d-Baum."""

    def __init__(self, teile, abstand=0.06, max_punkte=3_000_000, mit_farbe=True):
        flaeche = sum(t.area for t in teile)
        n_ges = int(min(max_punkte, max(200_000, flaeche / abstand ** 2)))
        P, N, C = [], [], []
        for t in teile:
            k = max(1000, int(n_ges * t.area / flaeche))
            p, fi = trimesh.sample.sample_surface(t, k, seed=1)
            P.append(p); N.append(t.face_normals[fi])
            C.append(farbe_an(t, p, fi) if mit_farbe else np.zeros((len(p), 3), np.float32))
        self.p = np.concatenate(P); self.n = np.concatenate(N); self.c = np.concatenate(C).astype(np.float32)
        self.baum = cKDTree(self.p)
        self.abstand = np.sqrt(flaeche / len(self.p))

    def farbe(self, q, k=4):
        d, i = self.baum.query(q, k, workers=-1)
        if k == 1:
            return self.c[i], d
        w = 1.0 / (d + 1e-6); w /= w.sum(1, keepdims=True)
        return (self.c[i] * w[:, :, None]).sum(1), d[:, 0]

    def anziehen(self, q, max_d):
        """Punkte auf die Original-Oberfläche projizieren (Ebene des nächsten Stichprobenpunkts), nur wenn nah genug."""
        d, i = self.baum.query(q, 1, workers=-1)
        n = self.n[i]
        neu = q - ((q - self.p[i]) * n).sum(1, keepdims=True) * n
        ok = d < max_d
        q = q.copy(); q[ok] = neu[ok]
        return q, ok


# ======================= Bild (Software-Rasterer, ohne GPU/OpenGL) =======================
def _ansicht(V, F, FC, w, h, azimut, hoehe, s=None, licht=(-0.45, -0.75, 0.55)):
    """Orthografische Ansicht, Maleralgorithmus (hinten zuerst), zweiseitige Beleuchtung → robust auch bei
    falsch orientierten Flächen."""
    from PIL import Image, ImageDraw
    a, e = np.radians(azimut), np.radians(hoehe)
    Rz = np.array([[np.cos(a), -np.sin(a), 0], [np.sin(a), np.cos(a), 0], [0, 0, 1]])
    Rx = np.array([[1, 0, 0], [0, np.cos(e), -np.sin(e)], [0, np.sin(e), np.cos(e)]])
    P = (V - (V.min(0) + V.max(0)) / 2) @ Rz.T @ Rx.T          # Kamera bei −Y, schaut nach +Y, Z oben
    tri = P[F]
    nrm = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
    nrm /= np.maximum(np.linalg.norm(nrm, axis=1), 1e-12)[:, None]
    nrm[nrm[:, 1] > 0] *= -1                                    # zweiseitig: immer zur Kamera
    L = np.asarray(licht, float); L /= np.linalg.norm(L)
    hell = 0.40 + 0.55 * np.clip(nrm @ L, 0, 1) + 0.18 * np.clip(-nrm[:, 1], 0, 1) ** 4
    col = np.clip(np.asarray(FC, float)[:, :3] * hell[:, None], 0, 255).astype(np.uint8)
    if s is None:
        ext = np.ptp(P[:, [0, 2]], 0); s = 0.9 * min(w / ext[0], h / ext[1])
    px = tri[:, :, [0, 2]] * s * [1, -1] + [w / 2, h / 2]
    img = Image.new("RGB", (w, h), (246, 246, 248)); dr = ImageDraw.Draw(img)
    for i in np.argsort(-tri[:, :, 1].mean(1)):
        dr.polygon([tuple(q) for q in px[i]], fill=tuple(col[i]))
    return img


def bild(V, F, FC, pfad, groesse=(1200, 620), titel=None):
    """Zwei Ansichten (vorn links / hinten rechts) im gleichen Maßstab, 2× überabgetastet."""
    from PIL import Image, ImageDraw
    w, h = groesse; k = 2
    V = np.asarray(V, float); F = np.asarray(F)
    if FC is None:
        FC = np.tile([200.0, 200, 205], (len(F), 1))
    d = np.linalg.norm(np.ptp(V, 0))                            # Diagonale passt in beide Ansichten
    s = 0.92 * min(w * k / 2, h * k) / d
    a = _ansicht(V, F, FC, w * k // 2, h * k, -35, 18, s)
    b = _ansicht(V, F, FC, w * k // 2, h * k, 145, 18, s)
    img = Image.new("RGB", (w * k, h * k)); img.paste(a, (0, 0)); img.paste(b, (w * k // 2, 0))
    img = img.resize((w, h), Image.LANCZOS)
    if titel:
        ImageDraw.Draw(img).text((12, 10), titel, fill=(60, 60, 66))
    img.save(pfad)


# ======================= Voxel-Werkzeuge =======================
def _kugel(r):
    r = max(1, int(round(r)))
    g = np.mgrid[-r:r + 1, -r:r + 1, -r:r + 1]
    return (g ** 2).sum(0) <= r * r + 0.5


def voxel_fuellen(teile, voxel, rand=4, schliessen=1, abstand=None):
    """Oberflächen-Stichprobe → Voxel-Schale → von außen fluten → alles Nicht-Außen ist Körper.
    schliessen = Radius (Voxel) des Morphologie-Schließens (schließt Restlöcher bis ~2·r)."""
    lo = np.min([t.bounds[0] for t in teile], 0); hi = np.max([t.bounds[1] for t in teile], 0)
    pad = rand + schliessen + 2
    org = lo - pad * voxel
    dims = np.ceil((hi - lo) / voxel).astype(int) + 2 * pad + 1
    schale = np.zeros(dims, bool)
    a = abstand or voxel * 0.45
    for t in teile:
        n = int(min(12_000_000, max(50_000, t.area / a ** 2)))
        for start in range(0, n, 2_000_000):
            p, _ = trimesh.sample.sample_surface(t, min(2_000_000, n - start), seed=start + 7)
            ij = np.floor((p - org) / voxel).astype(int)
            schale[ij[:, 0], ij[:, 1], ij[:, 2]] = True
        # auch alle Eckpunkte (feine Spitzen)
        ij = np.floor((t.vertices - org) / voxel).astype(int)
        schale[ij[:, 0], ij[:, 1], ij[:, 2]] = True
    st = _kugel(schliessen)
    dick = ndimage.binary_dilation(schale, st)
    aussen_l, _ = ndimage.label(~dick)
    rand_ids = np.unique(np.concatenate([aussen_l[0].ravel(), aussen_l[-1].ravel(), aussen_l[:, 0].ravel(),
                                         aussen_l[:, -1].ravel(), aussen_l[:, :, 0].ravel(), aussen_l[:, :, -1].ravel()]))
    rand_ids = rand_ids[rand_ids > 0]
    aussen = np.isin(aussen_l, rand_ids)
    koerper = ~aussen
    koerper = ndimage.binary_erosion(koerper, st, border_value=0) | (schale & koerper)   # Schließen: zurück auf die Oberfläche
    return koerper, org, schale


def netz_aus_voxeln(maske, org, voxel, sigma=0.75):
    from skimage import measure
    f = ndimage.gaussian_filter(np.pad(maske, 1).astype(np.float32), sigma)
    v, fa, _, _ = measure.marching_cubes(f, 0.5, spacing=(voxel,) * 3)
    v += org - voxel
    m = trimesh.Trimesh(v, fa[:, ::-1], process=True)
    if m.volume < 0:
        m.invert()
    return m


def loecher_flicken(m, max_kanten=4000):
    """Jede zusammenhängende Gruppe von Randkanten (Loch) mit einem Fächer vom Schwerpunkt aus schließen."""
    kanten = m.edges_sorted
    eind, zahl = np.unique(kanten, axis=0, return_counts=True)
    rand = eind[zahl == 1]
    if len(rand) == 0:
        return m, 0
    from scipy.sparse.csgraph import connected_components
    n_v = len(m.vertices)
    G = sparse_coo(rand, n_v)
    _, comp = connected_components(G, directed=False)
    gruppen = {}
    for e in rand:
        gruppen.setdefault(comp[e[0]], []).append(e)
    V = [m.vertices]; F = [m.faces]; n_neu = n_v; anz = 0
    for kl in gruppen.values():
        if len(kl) > max_kanten or len(kl) < 3:
            continue
        kl = np.array(kl)
        mitte = m.vertices[np.unique(kl)].mean(0)
        V.append(mitte[None]); F.append(np.c_[kl, np.full(len(kl), n_neu)]); n_neu += 1; anz += 1
    return trimesh.Trimesh(np.vstack(V), np.vstack(F), process=False), anz


def sparse_coo(kanten, n):
    from scipy import sparse
    return sparse.coo_matrix((np.ones(len(kanten)), (kanten[:, 0], kanten[:, 1])), shape=(n, n))


def zu_manifold(m):
    import manifold3d as mf
    M = mf.Manifold(mf.Mesh(vert_properties=np.asarray(m.vertices, np.float32), tri_verts=np.asarray(m.faces, np.uint32)))
    return M


def aus_manifold(M):
    r = M.to_mesh()
    return trimesh.Trimesh(np.asarray(r.vert_properties)[:, :3], np.asarray(r.tri_verts), process=False)


def duenne_stellen(maske, voxel, grenze_mm, org, min_vol_mm3=0.5):
    """Stellen, die beim Öffnen mit einer Kugel (Ø grenze_mm) verschwinden = dünner als grenze_mm."""
    r = grenze_mm / 2 / voxel
    if r < 0.75:
        return [], np.zeros_like(maske)
    offen = ndimage.binary_opening(maske, _kugel(r))
    duenn = maske & ~offen
    duenn = ndimage.binary_opening(duenn, _kugel(1)) if r > 2 else duenn     # Treppen-Rauschen an Kanten weg
    lab, n = ndimage.label(duenn)
    stellen = []
    if n:
        vol = ndimage.sum(duenn, lab, range(1, n + 1)) * voxel ** 3
        ctr = ndimage.center_of_mass(duenn, lab, range(1, n + 1))
        for v, c in sorted(zip(vol, ctr), key=lambda x: -x[0]):
            if v >= min_vol_mm3:
                stellen.append({"ort_mm": np.round(org + np.array(c) * voxel, 1).tolist(), "volumen_mm3": round(float(v), 1)})
    return stellen, duenn


# ======================= Hauptablauf =======================
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("eingabe")
    ap.add_argument("--ziel-mm", type=float, required=True, help="Zielgröße in mm (Höhe, siehe --mass)")
    ap.add_argument("--mass", choices=["hoehe", "max"], default="hoehe", help="--ziel-mm gilt für die Höhe (Z) oder die längste Seite")
    ap.add_argument("--aus", required=True, help="Ausgabeordner")
    ap.add_argument("--name", default=None)
    ap.add_argument("--oben", choices=["auto", "y", "z", "-y", "-z", "x", "-x"], default="auto",
                    help="welche Achse im Original oben ist (auto: GLB/OBJ = y, STL = z)")
    ap.add_argument("--drehen", default="", help="zusätzlich drehen in Grad um X,Y,Z, z. B. '0,0,90'")
    ap.add_argument("--aufrichten", choices=["auto", "aus"], default="auto",
                    help="auto: schiefe Lage bis 25° gerade stellen (lange Achse bzw. größte Auflagefläche)")
    ap.add_argument("--boden", default="auto", help="auto | schnitt:<mm> | sockel | aus")
    ap.add_argument("--sockel-hoehe", type=float, default=2.4)
    ap.add_argument("--sockel-rand", type=float, default=3.0)
    ap.add_argument("--max-dreiecke", type=int, default=400_000)
    ap.add_argument("--glatt", type=int, choices=[0, 1, 2, 3], default=0, help="Glätten 0 (aus) … 3 (stark)")
    ap.add_argument("--hohl", type=float, default=0.0, help="aushöhlen mit dieser Wandstärke in mm (0 = voll)")
    ap.add_argument("--duenn", type=float, default=0.8, help="Warnschwelle Wandstärke in mm")
    ap.add_argument("--verdicken", action="store_true", help="Stellen dünner als --duenn aufdicken")
    ap.add_argument("--voxel", type=float, default=None, help="Voxelgröße in mm (Standard: Größe/380, 0,1–0,5)")
    ap.add_argument("--loch-max", type=int, default=4000, help="Löcher bis zu so vielen Randkanten flach schließen")
    ap.add_argument("--sockel-farbe", default="#262626")
    a = ap.parse_args()
    t_start = time.time(); warn = []
    eing = Path(a.eingabe); ziel = Path(a.aus); ziel.mkdir(parents=True, exist_ok=True)
    name = a.name or eing.stem
    log = lambda *x: print(f"[{time.time() - t_start:5.1f}s]", *x, flush=True)

    # ---- 1. Laden ----
    teile = lade_teile(eing)
    farbig = any(hat_farbe(t) for t in teile)
    n_roh = sum(len(t.faces) for t in teile)
    log(f"geladen: {len(teile)} Teil(e), {n_roh} Dreiecke, Farbe: {'ja' if farbig else 'nein'}")

    # ---- 2. Achsen: Z oben ----
    oben = a.oben if a.oben != "auto" else ("z" if eing.suffix.lower() in (".stl", ".3mf", ".ply", ".off") else "y")
    R = {"z": np.eye(4), "-z": trimesh.transformations.rotation_matrix(np.pi, [1, 0, 0]),
         "y": trimesh.transformations.rotation_matrix(np.pi / 2, [1, 0, 0]),
         "-y": trimesh.transformations.rotation_matrix(-np.pi / 2, [1, 0, 0]),
         "x": trimesh.transformations.rotation_matrix(-np.pi / 2, [0, 1, 0]),
         "-x": trimesh.transformations.rotation_matrix(np.pi / 2, [0, 1, 0])}[oben]
    if a.drehen:
        wx, wy, wz = [np.radians(float(x)) for x in a.drehen.split(",")]
        R = trimesh.transformations.euler_matrix(wx, wy, wz, "sxyz") @ R
    for t in teile:
        t.apply_transform(R)

    # ---- 3. Grob skalieren (Splitter verfälschen die Größe → größtes Teil-Bündel nehmen) ----
    alle = trimesh.util.concatenate([trimesh.Trimesh(t.vertices, t.faces, process=False) for t in teile])
    lo, hi = np.percentile(alle.vertices, 0.05, 0), np.percentile(alle.vertices, 99.95, 0)
    ausdehnung = hi - lo
    s = a.ziel_mm / (ausdehnung[2] if a.mass == "hoehe" else ausdehnung.max())
    S = np.diag([s, s, s, 1.0]); S[:3, 3] = -((lo + hi) / 2) * s
    for t in teile:
        t.apply_transform(S)
    T_gesamt = S @ R                                  # Original → aktuelle Koordinaten (nur Info)

    # ---- 4. Geometrie-Kopie: Nähte schließen, Löcher mit Fächer-Flicken schließen ----
    # (pymeshlab-Reparaturfilter hängen sich bei manchen KI-Netzen auf → eigene, einfache Variante;
    #  der Flicken muss nur dicht sein, die Oberfläche entsteht danach aus der Voxel-Hülle)
    geo = trimesh.util.concatenate([trimesh.Trimesh(t.vertices, t.faces, process=False) for t in teile])
    geo.merge_vertices(digits_vertex=5)
    geschlossen, n_loch = loecher_flicken(geo, a.loch_max)
    log(f"Löcher geflickt: {n_loch}")
    # ---- 5. Voxel-Hülle ----
    groesse = geschlossen.extents.max()
    voxel = a.voxel or float(np.clip(groesse / 380, 0.1, 0.5))
    r_schl = max(1, int(round(0.4 / voxel)))
    for versuch in range(3):
        koerper, org, schale = voxel_fuellen([geschlossen], voxel, schliessen=r_schl)
        verh = koerper.sum() / max(1, schale.sum())
        if verh > 2.5 or versuch == 2:
            break
        r_schl *= 2; warn.append(f"Hülle leckte (große Löcher) – Schließradius auf {r_schl * voxel:.1f} mm erhöht")
    if verh <= 2.5:
        warn.append("Körper wirkt hohl/undicht – große Öffnung? Ergebnis prüfen (ggf. --loch-max erhöhen).")
    # Splitter / lose Teile
    lab, n = ndimage.label(koerper)
    entfernt = 0
    if n > 1:
        gr = ndimage.sum(koerper, lab, range(1, n + 1))
        behalten = [i + 1 for i, g in enumerate(gr) if g >= max(0.05 * gr.max(), 3.0 / voxel ** 3)]
        entfernt = n - len(behalten)
        koerper = np.isin(lab, behalten)
        if len(behalten) > 1:
            warn.append(f"{len(behalten)} getrennte größere Teile – stehen sie einzeln stabil?")
    log(f"Voxel {voxel:.3f} mm, Gitter {koerper.shape}, Splitter entfernt: {entfernt}")
    verdickt = np.zeros_like(koerper)
    if a.verdicken:
        stellen, duenn = duenne_stellen(koerper, voxel, a.duenn, org, 0.0)
        if duenn.any():
            r = max(1, int(np.ceil(a.duenn / 2 / voxel)))
            verdickt = ndimage.binary_dilation(duenn, _kugel(r)) & ~koerper
            koerper = koerper | verdickt
            log(f"verdickt: {len(stellen)} Stelle(n), +{verdickt.sum() * voxel ** 3:.0f} mm³")

    m = netz_aus_voxeln(koerper, org, voxel)
    log(f"Voxel-Netz: {len(m.faces)} Dreiecke, dicht: {m.is_watertight}")

    # ---- 6. Auf das Original zurückziehen (Details) ----
    quelle = FarbQuelle(teile, abstand=max(0.03, voxel * 0.3), mit_farbe=farbig)
    neu, ok = quelle.anziehen(np.asarray(m.vertices), max_d=voxel * 2.0)
    if verdickt.any():
        ij = np.clip(np.floor((neu - org) / voxel).astype(int), 0, np.array(verdickt.shape) - 1)
        nah_v = ndimage.binary_dilation(verdickt, _kugel(1))[ij[:, 0], ij[:, 1], ij[:, 2]]
        neu[nah_v] = np.asarray(m.vertices)[nah_v]
    m = trimesh.Trimesh(neu, m.faces, process=False)
    log(f"angezogen: {ok.mean() * 100:.0f} % der Punkte auf Original-Oberfläche")
    if a.glatt:
        trimesh.smoothing.filter_taubin(m, lamb=0.5, nu=-0.53, iterations={1: 4, 2: 12, 3: 30}[a.glatt])

    # ---- 7. Aufrichten ----
    # (a) längliche Figuren: Hauptträgheitsachse (lange Achse) senkrecht stellen, wenn sie 2–25° schief steht
    # (b) sonst: größte Fläche der konvexen Hülle unten (≥ 4 % der Grundfläche), die höchstens 25° schief steht
    kipp = 0.0; Rk = None
    if a.aufrichten == "auto":
        try:
            w_, v_ = np.linalg.eigh(m.moment_inertia)
            achse = v_[:, 0] * np.sign(v_[2, 0] or 1)
            neig = np.degrees(np.arccos(np.clip(achse[2], -1, 1)))
            if w_[1] / max(w_[0], 1e-9) >= 1.4 and 2.0 <= neig <= 25:
                Rk = trimesh.geometry.align_vectors(achse, [0, 0, 1.0]); kipp = neig; wie = "lange Achse"
            else:
                h_ = m.convex_hull
                flaechen = [(h_.area_faces[f_].sum(), h_.face_normals[f_[0]]) for f_ in h_.facets]
                flaechen += [(h_.area_faces[i], h_.face_normals[i]) for i in range(len(h_.faces))]
                beste = None
                for fl_, n_ in flaechen:
                    w2 = np.degrees(np.arccos(np.clip(n_ @ [0, 0, -1.0], -1, 1)))
                    if w2 <= 25 and fl_ >= 0.04 * h_.extents[0] * h_.extents[1] and (beste is None or fl_ > beste[0]):
                        beste = (fl_, n_, w2)
                if beste and beste[2] > 0.5:
                    Rk = trimesh.geometry.align_vectors(beste[1], [0, 0, -1.0]); kipp = beste[2]; wie = "Auflagefläche"
            if Rk is not None:
                m.apply_transform(Rk); T_gesamt = Rk @ T_gesamt
                for t in teile: t.apply_transform(Rk)
                log(f"aufgerichtet um {kipp:.1f}° ({wie})")
        except Exception as e:
            warn.append(f"Aufrichten übersprungen: {e}")
    # genaue Zielgröße nach dem Aufrichten
    k = a.ziel_mm / (m.extents[2] if a.mass == "hoehe" else m.extents.max())
    Sk = np.diag([k, k, k, 1.0])
    m.apply_transform(Sk); T_gesamt = Sk @ T_gesamt
    for t in teile: t.apply_transform(Sk)

    # ---- 8. Standfläche ----
    import manifold3d as mf
    M = zu_manifold(m)
    if M.status() != mf.Error.NoError:
        warn.append(f"Netz für Booleans nicht sauber ({M.status()}) – Boden/Hohl übersprungen")
        M = None
    boden = a.boden; schnitt_mm = 0.0; stand = 0.0; sockel_oben = None
    if M is not None:
        zmin = M.bounding_box()[2]; hoehe = M.bounding_box()[5] - zmin
        proj = M.project(); F_proj = max(proj.area(), 1e-6)
        ziel_flaeche = min(max(25.0, 0.12 * F_proj), 0.5 * F_proj)
        schwer = m.center_mass[:2]
        def steht(cs):            # Schwerpunkt mit 1 mm Abstand innerhalb der konvexen Hülle der Standfläche?
            return cs.area() > 0 and (cs.hull().offset(-1.0, mf.JoinType.Round) ^ mf.CrossSection.circle(0.3, 12)
                                      .translate([float(schwer[0]), float(schwer[1])])).area() > 0
        if boden == "auto":
            hmax = min(0.06 * hoehe, 4.0)
            boden = "sockel"
            for h in np.arange(0.1, hmax + 1e-9, 0.1):
                cs = M.slice(zmin + h)
                if cs.area() >= ziel_flaeche and steht(cs):
                    boden = f"schnitt:{h:.1f}"; break
            log(f"Boden auto → {boden} (Ziel-Standfläche {ziel_flaeche:.0f} mm², Schwerpunkt darüber)")
        if boden.startswith("schnitt"):
            schnitt_mm = float(boden.split(":")[1]) if ":" in boden else 1.0
            M = M.trim_by_plane([0, 0, 1], zmin + schnitt_mm)
        elif boden == "sockel":
            unten = M.slice(zmin + min(1.5, 0.05 * hoehe))
            basis = (unten if unten.area() > 0.25 * F_proj else proj).hull()
            basis = basis.offset(a.sockel_rand, mf.JoinType.Round, circular_segments=96)
            einsink = min(1.0, 0.03 * hoehe)
            sockel = mf.Manifold.extrude(basis, a.sockel_hoehe).translate([0, 0, zmin + einsink - a.sockel_hoehe])
            M = M + sockel
            sockel_oben = a.sockel_hoehe                           # Sockel-Oberseite über der Unterseite (vor Endskalierung)
        b = M.bounding_box()
        k2 = a.ziel_mm / ((b[5] - b[2]) if a.mass == "hoehe" else max(b[3] - b[0], b[4] - b[1], b[5] - b[2]))
        M = M.translate([-(b[0] + b[3]) / 2, -(b[1] + b[4]) / 2, -b[2]]).scale([k2, k2, k2])   # Zielmaß inkl. Boden
        T_ = np.diag([k2, k2, k2, 1.0]); T_[:3, 3] = np.array([-(b[0] + b[3]) / 2, -(b[1] + b[4]) / 2, -b[2]]) * k2
        T_gesamt = T_ @ T_gesamt
        if sockel_oben is not None:
            sockel_oben *= k2
        for t in teile: t.apply_transform(T_)
        stand = M.slice(0.05).area()

        # ---- 9. Aushöhlen ----
        if a.hohl > 0:
            mm = aus_manifold(M)
            vh = max(voxel, a.hohl / 4)
            kv, org2, _ = voxel_fuellen([mm], vh, schliessen=1)
            tiefe = ndimage.distance_transform_edt(kv) * vh
            innen = tiefe > a.hohl
            zs = org2[2] + (np.arange(kv.shape[2]) + 0.5) * vh
            innen[:, :, zs < a.hohl + (a.sockel_hoehe if boden == "sockel" else 0)] = False   # Boden bleibt voll
            innen = ndimage.binary_opening(innen, _kugel(1))
            if innen.sum() * vh ** 3 > 50:
                I = zu_manifold(netz_aus_voxeln(innen, org2, vh, sigma=1.0))
                if I.status() == mf.Error.NoError:
                    vol0 = M.volume(); M = M - I
                    log(f"ausgehöhlt: {vol0 / 1000:.1f} → {M.volume() / 1000:.1f} cm³")
                else:
                    warn.append("Aushöhlen fehlgeschlagen (Innennetz unsauber)")
            else:
                warn.append("Zu klein zum Aushöhlen")
        m = aus_manifold(M)

    # ---- 10. Vereinfachen ----
    if len(m.faces) > a.max_dreiecke:
        import pymeshlab
        ms = pymeshlab.MeshSet(); ms.add_mesh(pymeshlab.Mesh(m.vertices, m.faces))
        ms.meshing_decimation_quadric_edge_collapse(targetfacenum=a.max_dreiecke, preservenormal=True,
                                                    preservetopology=True, qualitythr=0.4, planarquadric=True)
        mm_ = ms.current_mesh(); m2 = trimesh.Trimesh(mm_.vertex_matrix(), mm_.face_matrix(), process=True)
        if m2.is_watertight:
            m = m2
        else:
            warn.append("Vereinfachen hätte das Netz geöffnet – unvereinfacht gelassen")
    log(f"fertig: {len(m.faces)} Dreiecke, dicht {m.is_watertight}")

    # ---- 11. Prüfen ----
    vp = max(0.1, min(voxel, 0.25))
    kv, org3, _ = voxel_fuellen([m], vp, schliessen=1)
    stellen, _ = duenne_stellen(kv, vp, a.duenn, org3)
    stellen = [x for x in stellen if x["ort_mm"][2] > 0.6]        # Schnittkante am Bett (spitz auslaufend) ist harmlos
    if stellen:
        warn.append(f"{len(stellen)} Stelle(n) dünner als {a.duenn} mm (größte {stellen[0]['volumen_mm3']} mm³ bei "
                    f"{stellen[0]['ort_mm']}) – mit --verdicken aufdicken oder größer drucken")
    nz = m.face_normals[:, 2]; fl = m.area_faces
    boden_f = m.triangles_center[:, 2] < 0.3
    ueber = (nz < -np.cos(np.radians(45))) & ~boden_f
    ueber_anteil = float(fl[ueber].sum() / fl.sum())
    if ueber_anteil > 0.03:
        warn.append(f"Überhänge > 45°: {ueber_anteil * 100:.0f} % der Oberfläche → Stützen (auto) einplanen")
    if m.extents.max() > 250:
        warn.append(f"größer als der Bauraum (max. 250 mm): {m.extents.round(1).tolist()}")
    # Standfestigkeit: Schwerpunkt über der Standfläche?
    stabil = None
    try:
        import manifold3d as mf
        sf = zu_manifold(m).slice(0.05)
        hull2 = sf.hull(); c = m.center_mass
        stabil = bool(hull2.area() > 0 and (hull2 ^ mf.CrossSection.circle(0.5, 16).translate([c[0], c[1]])).area() > 0)
    except Exception:
        pass
    if stand < 20:
        warn.append(f"kleine Standfläche ({stand:.0f} mm²) – Brim an oder --boden sockel")
    if stabil is False:
        warn.append("Schwerpunkt liegt nicht über der Standfläche – kippt ohne Stütze/Sockel")

    # ---- 12. Ausgabe ----
    stl = ziel / f"{name}.stl"; m.export(stl)
    FC = None; info_farbe = None
    if farbig:
        quelle = FarbQuelle(teile, abstand=max(0.03, voxel * 0.3))
        vc, d = quelle.farbe(np.asarray(m.vertices), k=4)
        weit = d > max(1.5, 4 * voxel)                            # Sockel/Schnittflächen: keine Originalfarbe in der Nähe
        if sockel_oben is not None:                               # Sockel bekommt eine eigene Farbe
            weit |= (np.asarray(m.vertices)[:, 2] <= sockel_oben + 0.05) & (d > 0.25)
        sf = np.array([int(a.sockel_farbe.lstrip("#")[i:i + 2], 16) for i in (0, 2, 4)], np.float32)
        vc[weit] = sf
        mc = m.copy(); mc.visual = trimesh.visual.ColorVisuals(mc, vertex_colors=np.c_[np.clip(vc, 0, 255), np.full(len(vc), 255)].astype(np.uint8))
        mc.export(ziel / f"{name}_farbig.glb")
        FC = vc[m.faces].mean(1); info_farbe = f"{name}_farbig.glb"
    bild(np.asarray(m.vertices), np.asarray(m.faces), FC, ziel / "vorschau.png",
         titel=f"{name}: {m.extents[0]:.0f} x {m.extents[1]:.0f} x {m.extents[2]:.0f} mm, {len(m.faces)} Dreiecke")
    info = {"name": name, "eingabe": eing.name, "masse_mm": np.round(m.extents, 1).tolist(),
            "dreiecke": int(len(m.faces)), "dreiecke_roh": int(n_roh), "wasserdicht": bool(m.is_watertight),
            "volumen_cm3": round(float(m.volume) / 1000, 2), "stl": stl.name, "farbig": info_farbe,
            "oben_achse": oben, "aufgerichtet_grad": round(kipp, 1), "boden": boden, "schnitt_mm": schnitt_mm,
            "standflaeche_mm2": round(float(stand), 1), "steht_stabil": stabil,
            "ueberhang_anteil": round(ueber_anteil, 3), "duenne_stellen": stellen[:10], "splitter_entfernt": int(entfernt),
            "voxel_mm": round(voxel, 3), "transform_original": np.round(T_gesamt, 6).tolist(), "glatt": a.glatt, "hohl_mm": a.hohl, "warnungen": warn,
            "laufzeit_s": round(time.time() - t_start, 1)}
    (ziel / "info.json").write_text(json.dumps(info, ensure_ascii=False, indent=1), encoding="utf-8")
    log(f"OK  {stl}  {info['masse_mm']} mm, {info['dreiecke']} Dreiecke, dicht {info['wasserdicht']}")
    for w_ in warn:
        print("  ⚠", w_)


if __name__ == "__main__":
    main()
