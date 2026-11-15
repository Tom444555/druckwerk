#!/usr/bin/env python3
"""Druckbarkeits-Prüfung für ein Teil aus einer oder mehreren Farb-STL (gleiche Koordinaten, Lage = Drucklage).

Aufruf:   python3 werkzeug/pruefen.py modelle/x_schwarz.stl modelle/x_rot.stl [--json] [--bauraum 256]
Ausgabe:  Ampel-Liste OK / Hinweis / Fehler mit Zahl; Exit-Code 1 bei mindestens einem Fehler, sonst 0.

Geprüft wird
- je Datei: wasserdicht, Einzelkörper/lose Splitter, Detailbreite (waagrecht gemessen) gegen 0,45 mm Linienbreite;
- am Gesamtteil (Vereinigung aller Farben): Bauraum, Standfläche, Überhänge > 45°, waagrechte Unterseiten (Brücken),
  dünnste Wand per Strahl-Test (Fehler < 0,8 mm, Hinweis < 1,2 mm), scharfe Innenkanten;
- paarweise: Schnittvolumen (muss 0 sein) und Berührungsfläche (Farben sollen aneinander haften).
Schwellen und Quellen: werkzeug/profi.py bzw. werkzeug/QUALITAET.md. Wandstärken-Strahltest braucht embreex
(schnell); ohne embreex rechnet trimesh langsamer mit weniger Stichproben.
"""
import argparse
import itertools
import json
import math
import sys
import time

import numpy as np
import trimesh

WAND_FEHLER, WAND_HINWEIS, DETAIL = 0.8, 1.2, 0.45
UEBERHANG = 45.0
BRUECKE = 5.0
SPLITTER_MM3 = 1.0


class Bericht:
    def __init__(self):
        self.zeilen = []

    def add(self, stufe, text, **daten):
        self.zeilen.append({"stufe": stufe, "text": text, **daten})

    def fehler(self):
        return sum(z["stufe"] == "Fehler" for z in self.zeilen)


def _manifold(m):
    import manifold3d as m3
    return m3.Manifold(m3.Mesh(np.asarray(m.vertices, np.float32), np.asarray(m.faces, np.uint32)))


def _aus_manifold(mf):
    g = mf.to_mesh()
    return trimesh.Trimesh(np.asarray(g.vert_properties)[:, :3], np.asarray(g.tri_verts), process=True)


def _stichproben(m, n, seed=1):
    pts, idx = trimesh.sample.sample_surface(m, n, seed=seed)
    return pts, idx


def _dicke(m, n, nur_waagrecht=False):
    """Strahl-Test: von Oberflächenpunkten entgegen der Normalen bis zur Gegenwand. Gibt (dicke[], flächenanteil je Probe)."""
    pts, idx = _stichproben(m, n)
    nrm = m.face_normals[idx]
    if nur_waagrecht:
        w = np.abs(nrm[:, 2]) < 0.5
        pts, nrm = pts[w], nrm[w]
    if len(pts) == 0:
        return np.array([]), 0.0, pts
    start = pts - nrm * 0.005
    loc, ray_i, _ = m.ray.intersects_location(start, -nrm, multiple_hits=True)
    d = np.full(len(pts), np.inf)
    if len(loc):
        dist = np.linalg.norm(loc - start[ray_i], axis=1)
        gut = dist > 0.005
        np.minimum.at(d, ray_i[gut], dist[gut] + 0.005)
    return d, m.area / n, pts


def _orte(pts, maske, raster=8.0, k=3):
    """Häufigste Orte (Raster-Zellen) der markierten Stichproben als Text."""
    if not maske.any():
        return ""
    zellen, anz = np.unique(np.round(pts[maske] / raster), axis=0, return_counts=True)
    top = np.argsort(-anz)[:k]
    return " – bei " + "; ".join(f"({z[0] * raster:.0f}, {z[1] * raster:.0f}, {z[2] * raster:.0f})" for z in zellen[top])


def _cluster(m, maske):
    """Zusammenhängende Flächengruppen der markierten Dreiecke → Liste (fläche, mitte, dreiecke)."""
    fi = np.nonzero(maske)[0]
    if len(fi) == 0:
        return []
    adj = m.face_adjacency
    sel = maske[adj[:, 0]] & maske[adj[:, 1]]
    gruppen = trimesh.graph.connected_components(adj[sel], nodes=fi, min_len=1)
    aus = []
    for g in gruppen:
        g = np.asarray(g)
        a = m.area_faces[g].sum()
        c = (m.triangles_center[g] * m.area_faces[g, None]).sum(0) / max(a, 1e-9)
        aus.append((a, c, g))
    return sorted(aus, key=lambda x: -x[0])


def _spanne(m, g):
    """Kürzere Seite des kleinsten umschließenden Rechtecks (XY) einer Flächengruppe = Brückenlänge."""
    v = m.vertices[np.unique(m.faces[g])][:, :2]
    if len(v) < 3:
        return 0.0
    try:
        _, ext = trimesh.bounds.oriented_bounds_2d(v)
        return float(min(ext))
    except Exception:
        e = v.max(0) - v.min(0)
        return float(min(e))


def pruefe(pfade, bauraum=256.0, proben=60000):
    b = Bericht()
    t0 = time.time()
    netze = {}
    for p in pfade:
        m = trimesh.load(p, force="mesh")
        netze[p.split("/")[-1]] = m
    namen = list(netze)
    dreiecke = sum(len(m.faces) for m in netze.values())
    b.kopf = f"{', '.join(namen)} ({len(namen)} Datei{'en' if len(namen) > 1 else ''}, {dreiecke:,} Dreiecke)".replace(
        f"{dreiecke:,}", f"{dreiecke:,}".replace(",", "."))

    # ---- je Datei ----
    for n, m in netze.items():
        if not m.is_watertight:
            b.add("Fehler", f"{n}: nicht wasserdicht ({len(trimesh.grouping.group_rows(m.edges_sorted, require_count=1))} offene Kanten)")
        else:
            b.add("OK", f"{n}: wasserdicht, {m.volume / 1000:.2f} cm³")
        teile = m.split(only_watertight=False)
        klein = [t for t in teile if abs(t.volume) < SPLITTER_MM3]
        if klein:
            b.add("Fehler", f"{n}: {len(klein)} lose Splitter < {SPLITTER_MM3} mm³ (entfernen)", anzahl=len(klein))
        if len(teile) - len(klein) > 1:
            b.add("Hinweis", f"{n}: {len(teile) - len(klein)} getrennte Körper (gewollt? z. B. Buchstaben, Einlagen)")
        # Detailbreite waagrecht (Schrift, Stege) – der Slicer lässt < 1 Linienbreite weg
        d, a1, pts = _dicke(m, min(proben, max(5000, len(m.faces))), nur_waagrecht=True)
        if len(d):
            fl = float((d < DETAIL).sum() * a1)
            dmin = float(np.percentile(d[np.isfinite(d)], 0.5)) if np.isfinite(d).any() else float("nan")
            if fl > max(1.0, 0.002 * m.area):
                b.add("Fehler", f"{n}: Details schmaler als {DETAIL} mm auf {fl:.1f} mm² (fallen beim Slicen weg)"
                      f"{_orte(pts, d < DETAIL)}", flaeche=fl)
            else:
                b.add("OK", f"{n}: kleinste Detailbreite ≈ {dmin:.2f} mm (≥ {DETAIL})", wert=dmin)

    # ---- Gesamtteil ----
    if len(netze) > 1 and all(m.is_watertight for m in netze.values()):
        mf = {k: _manifold(m) for k, m in netze.items()}
        ges_mf = mf[namen[0]]
        for k in namen[1:]:
            ges_mf = ges_mf + mf[k]
        ges = _aus_manifold(ges_mf)
    else:
        mf = {}
        ges = trimesh.util.concatenate(list(netze.values())) if len(netze) > 1 else netze[namen[0]]
    ext = ges.extents
    if (ext > bauraum).any():
        b.add("Fehler", f"Maße {ext[0]:.1f} × {ext[1]:.1f} × {ext[2]:.1f} mm passen nicht in {bauraum:.0f}³ – drehen oder teilen")
    else:
        b.add("OK", f"Maße {ext[0]:.1f} × {ext[1]:.1f} × {ext[2]:.1f} mm (≤ {bauraum:.0f})", masse=ext.round(2).tolist())

    zmin = ges.bounds[0, 2]
    nz = ges.face_normals[:, 2]
    zf = ges.triangles[:, :, 2]
    am_bett = (zf.max(1) < zmin + 0.05)
    boden = am_bett & (nz < -0.99)
    a_boden = float(ges.area_faces[boden].sum())
    try:
        grund = _hull_area(ges.vertices[:, :2])          # Grundriss = konvexe Hülle in XY
    except Exception:
        grund = float(ext[0] * ext[1])
    anteil = a_boden / max(grund, 1e-9)
    if a_boden < 1.0:
        b.add("Fehler", "keine Standfläche bei z = min (Teil liegt nicht flach auf)")
    elif anteil < 0.15 and ext[2] > 3 * math.sqrt(a_boden):
        b.add("Hinweis", f"Standfläche {a_boden:.0f} mm² = {anteil:.0%} des Grundrisses bei {ext[2]:.0f} mm Höhe → Brim empfohlen",
              wert=a_boden)
    else:
        b.add("OK", f"Standfläche {a_boden:.0f} mm² ({anteil:.0%} des Grundrisses)", wert=a_boden)

    grenze = -math.sin(math.radians(UEBERHANG + 1.0))          # 1° Toleranz: 45°-Fasen sind erlaubt
    ueber = (~am_bett) & (nz < grenze) & (nz >= -0.985)
    gruppen = [g for g in _cluster(ges, ueber) if g[0] > 0.5]
    a_ue = sum(g[0] for g in gruppen)
    if a_ue > 5.0:
        orte = "; ".join(f"{g[0]:.0f} mm² bei ({g[1][0]:.0f}, {g[1][1]:.0f}, {g[1][2]:.0f})" for g in gruppen[:3])
        b.add("Hinweis", f"Überhänge > {UEBERHANG:.0f}°: {a_ue:.0f} mm² in {len(gruppen)} Bereichen – {orte} → Stützen oder Fase",
              flaeche=a_ue)
    else:
        b.add("OK", f"Überhänge > {UEBERHANG:.0f}°: {a_ue:.1f} mm²", flaeche=a_ue)

    flach = (~am_bett) & (nz < -0.985)
    bruecken = [(g[0], g[1], _spanne(ges, g[2])) for g in _cluster(ges, flach) if g[0] > 0.5]
    lang = [x for x in bruecken if x[2] > BRUECKE]
    if lang:
        orte = "; ".join(f"{x[2]:.1f} mm bei z={x[1][2]:.1f}" for x in sorted(lang, key=lambda x: -x[2])[:3])
        b.add("Hinweis", f"{len(lang)} waagrechte Unterseiten/Brücken > {BRUECKE:.0f} mm: {orte} → Stützen prüfen",
              anzahl=len(lang))
    else:
        mx = max([x[2] for x in bruecken], default=0.0)
        b.add("OK", f"Brücken: {len(bruecken)}, längste {mx:.1f} mm (≤ {BRUECKE:.0f})")

    d, a1, pts = _dicke(ges, proben)
    if len(d):
        fin = d[np.isfinite(d)]
        fl08 = float((d < WAND_FEHLER).sum() * a1)
        fl12 = float((d < WAND_HINWEIS).sum() * a1)
        dmin = float(np.percentile(fin, 1.0)) if len(fin) else float("nan")
        schwelle = max(2.0, 0.003 * ges.area)
        if fl08 > schwelle:
            b.add("Fehler", f"Wand dünner als {WAND_FEHLER} mm auf {fl08:.0f} mm² (1-%-Wert {dmin:.2f} mm)"
                  f"{_orte(pts, d < WAND_FEHLER)}", flaeche=fl08)
        elif fl12 > schwelle:
            b.add("Hinweis", f"Wand dünner als {WAND_HINWEIS} mm auf {fl12:.0f} mm² (1-%-Wert {dmin:.2f} mm)"
                  f"{_orte(pts, d < WAND_HINWEIS)}", flaeche=fl12)
        else:
            b.add("OK", f"dünnste Wand (1-%-Wert) {dmin:.2f} mm", wert=dmin)

    ang = ges.face_adjacency_angles
    konkav = ~ges.face_adjacency_convex
    scharf = konkav & (ang > math.radians(70))
    if scharf.any():
        ek = ges.face_adjacency_edges[scharf]
        laenge = float(np.linalg.norm(ges.vertices[ek[:, 0]] - ges.vertices[ek[:, 1]], axis=1).sum())
        b.add("Hinweis", f"scharfe Innenkanten: {laenge:.0f} mm Länge → Rundung ≥ 0,2 mm senkt Spannungsspitzen", laenge=laenge)
    else:
        b.add("OK", "keine scharfen Innenkanten")

    # ---- paarweise ----
    for x, y in itertools.combinations(namen, 2):
        if mf:
            sv = (mf[x] ^ mf[y]).volume()
            if sv > 0.01:
                b.add("Fehler", f"{x} ∩ {y}: Schnittvolumen {sv:.2f} mm³ (muss 0 sein)", wert=sv)
            else:
                b.add("OK", f"{x} ∩ {y}: Schnittvolumen {sv:.3f} mm³")
        kontakt = _beruehrung(netze[x], netze[y])
        if kontakt < 1.0:
            b.add("Hinweis", f"{x} / {y}: berühren sich kaum ({kontakt:.1f} mm²) – getrennte Teile oder Luftspalt?", wert=kontakt)
        else:
            b.add("OK", f"{x} / {y}: Berührfläche {kontakt:.0f} mm²", wert=kontakt)
    b.zeit = time.time() - t0
    return b


def _hull_area(xy):
    from scipy.spatial import ConvexHull
    return float(ConvexHull(xy).volume)


def _beruehrung(a, b, n=20000):
    """Fläche von a, die b berührt (Abstand < 0,05 mm entlang der Normalen)."""
    pts, idx = _stichproben(a, n, seed=2)
    nrm = a.face_normals[idx]
    start = pts - nrm * 0.03
    loc, ri, _ = b.ray.intersects_location(start, nrm, multiple_hits=False)
    if not len(loc):
        return 0.0
    dist = np.linalg.norm(loc - start[ri], axis=1)
    return float((dist < 0.08).sum() * a.area / n)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("stl", nargs="+")
    ap.add_argument("--json", action="store_true", help="Ergebnis als JSON")
    ap.add_argument("--bauraum", type=float, default=256.0)
    ap.add_argument("--proben", type=int, default=60000, help="Strahlen für den Wandtest")
    a = ap.parse_args()
    b = pruefe(a.stl, a.bauraum, a.proben)
    if a.json:
        print(json.dumps({"dateien": a.stl, "fehler": b.fehler(), "zeit_s": round(b.zeit, 1), "punkte": b.zeilen},
                         ensure_ascii=False, indent=1, default=float))
    else:
        print(f"Prüfung: {b.kopf}")
        for z in b.zeilen:
            print(f"{z['stufe']:<8}{z['text']}")
        hinweise = sum(z["stufe"] == "Hinweis" for z in b.zeilen)
        print(f"Ergebnis: {b.fehler()} Fehler, {hinweise} Hinweise ({b.zeit:.1f} s)"
              f"{'' if trimesh.ray.has_embree else ' – ohne embreex langsam'}")
    sys.exit(1 if b.fehler() else 0)


if __name__ == "__main__":
    main()
