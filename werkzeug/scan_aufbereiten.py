#!/usr/bin/env python3
"""Meshroom-Ergebnis vom Drehteller druckfertig machen (20.11.2026, mit nachgestelltem Scan geprüft, echter Scan offen).

Annahme (Spickzettel modelle/drehteller_daten/MESHROOM.md): SfMTransform „from_markers“ mit den vier CCTag3-Markern →
Tellermitte = Ursprung, Telleroberseite = Ebene Y=0, Y nach oben, Einheit 100 mm.

Schritte: laden (OBJ/PLY/STL oder ZIP) → Y-oben nach Z-oben drehen, ×100 → alles unter der Schnitthöhe weg
(Teller, Podest) → nur die großen Teile behalten → Löcher schließen, Boden plan → verkleinern → STL + Bericht.
Mit --vergleich bezug.stl: Scan per ICP auf das Bezugsmodell legen und Abweichungen messen (Prüfkörper).

  python3 werkzeug/scan_aufbereiten.py scan.zip --aus /tmp/s [--podest] [--schnitt 0.3] [--einheit 100]
         [--ziel-mm 120] [--max-dreiecke 500000] [--vergleich bezug.stl] [--bild /tmp/s/v.png]
"""
import argparse, json, os, sys, tempfile, zipfile
import numpy as np
import trimesh

PODEST_H = 40.0   # aus modelle/drehteller.py


def laden(pfad):
    if pfad.lower().endswith(".zip"):
        ziel = tempfile.mkdtemp(prefix="scan_")
        with zipfile.ZipFile(pfad) as z:
            for n in z.namelist():
                if ".." in n or n.startswith("/"):
                    raise SystemExit(f"unsicherer Pfad im ZIP: {n}")
            z.extractall(ziel)
        kand = []
        for wurzel, _, dateien in os.walk(ziel):
            kand += [os.path.join(wurzel, d) for d in dateien if d.lower().endswith((".obj", ".ply", ".stl"))]
        if not kand:
            raise SystemExit("kein OBJ/PLY/STL im ZIP")
        pfad = max(kand, key=os.path.getsize)
        print("Netz aus ZIP:", os.path.relpath(pfad, ziel))
    m = trimesh.load(pfad, force="mesh", process=False)
    return trimesh.Trimesh(m.vertices, m.faces, process=True)


def ausrichten(m, einheit, achsen):
    if achsen == "yoben":   # (x, y, z) -> (x, -z, y)
        m.apply_transform(np.array([[1, 0, 0, 0], [0, 0, -1, 0], [0, 1, 0, 0], [0, 0, 0, 1]], float))
    m.apply_scale(einheit)
    return m


def schneiden(m, z):
    oben = m.slice_plane(plane_origin=[0, 0, z], plane_normal=[0, 0, 1], cap=False)
    if oben is None or len(oben.faces) == 0:
        raise SystemExit(f"über z = {z} mm ist nichts – stimmen Einheit/Achsen? (z-Bereich {m.bounds[0][2]:.1f} … {m.bounds[1][2]:.1f})")
    teile = oben.split(only_watertight=False)
    groesste = max(len(t.faces) for t in teile)
    behalten = [t for t in teile if len(t.faces) >= 0.1 * groesste]
    print(f"Schnitt bei z = {z:.1f} mm: {len(teile)} Stücke, {len(behalten)} behalten")
    return trimesh.util.concatenate(behalten)


def schliessen(m, max_dreiecke):
    import pymeshlab
    ms = pymeshlab.MeshSet()
    ms.add_mesh(pymeshlab.Mesh(m.vertices, m.faces))
    ms.meshing_remove_duplicate_vertices()
    ms.meshing_repair_non_manifold_edges()
    ms.meshing_close_holes(maxholesize=100000, newfaceselected=False)
    if ms.current_mesh().face_number() > max_dreiecke:
        ms.meshing_decimation_quadric_edge_collapse(targetfacenum=max_dreiecke, preservenormal=True)
    ms.meshing_repair_non_manifold_edges()
    ms.meshing_close_holes(maxholesize=100000)
    c = ms.current_mesh()
    t = trimesh.Trimesh(c.vertex_matrix(), c.face_matrix(), process=True)
    trimesh.repair.fix_normals(t)
    if not t.is_watertight:   # Scans sind fast nie dicht -> Poisson-Hülle, danach Boden plan schneiden
        print("nicht dicht → Poisson-Rekonstruktion")
        ms.compute_normal_per_vertex()
        ms.generate_surface_reconstruction_screened_poisson(depth=10, preclean=True)
        c = ms.current_mesh()
        t = trimesh.Trimesh(c.vertex_matrix(), c.face_matrix(), process=True)
        t = max(t.split(only_watertight=False), key=lambda k: len(k.faces))
        trimesh.repair.fix_normals(t)
    return t


def boden_plan(m, z):
    """Alles unter z abschneiden und den Schnitt mit einer ebenen Fläche schließen."""
    b = m.slice_plane(plane_origin=[0, 0, z], plane_normal=[0, 0, 1], cap=True)
    return b if b is not None and len(b.faces) else m


def vergleichen(scan, bezug_pfad):
    bezug = trimesh.load(bezug_pfad, force="mesh")
    a = scan.copy()
    a.apply_translation(bezug.centroid - a.centroid)
    best = None
    for w in range(0, 360, 90):   # vier Startlagen um Z (Prüfkörper ist eindeutig, ICP findet sonst ein Nebenminimum)
        r = trimesh.transformations.rotation_matrix(np.radians(w), [0, 0, 1], bezug.centroid)
        pts = trimesh.transform_points(a.sample(8000, seed=1) if hasattr(a, "sample") else a.vertices, r)
        mat, _, kosten = trimesh.registration.icp(pts, bezug, max_iterations=60, scale=False)
        if best is None or kosten < best[1]:
            best = (mat @ r, kosten)
    a.apply_transform(best[0])
    probe = a.sample(20000, seed=2)
    _, abst, _ = trimesh.proximity.closest_point(bezug, probe)
    erg = {"mittel_mm": float(np.mean(abst)), "p95_mm": float(np.percentile(abst, 95)), "max_mm": float(np.max(abst)),
           "masse_scan": [float(x) for x in a.extents], "masse_bezug": [float(x) for x in bezug.extents]}
    return a, erg


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("eingabe")
    ap.add_argument("--aus", required=True)
    ap.add_argument("--name", default="scan")
    ap.add_argument("--einheit", type=float, default=100.0, help="mm je Meshroom-Einheit (Marker: 100)")
    ap.add_argument("--achsen", choices=["yoben", "zoben"], default="yoben")
    ap.add_argument("--podest", action="store_true", help="Podest (40 mm) mit wegschneiden")
    ap.add_argument("--schnitt", type=float, default=0.3, help="mm über Teller bzw. Podest")
    ap.add_argument("--ziel-mm", type=float, help="größtes Maß danach auf diesen Wert skalieren")
    ap.add_argument("--max-dreiecke", type=int, default=500000)
    ap.add_argument("--vergleich", help="Bezugs-STL (z. B. Prüfkörper)")
    ap.add_argument("--bild")
    a = ap.parse_args()
    os.makedirs(a.aus, exist_ok=True)

    m = ausrichten(laden(a.eingabe), a.einheit, a.achsen)
    z = (PODEST_H if a.podest else 0.0) + a.schnitt
    m = schneiden(m, z)
    m = schliessen(m, a.max_dreiecke)
    m = boden_plan(m, z + 0.2)
    m.apply_translation([-m.centroid[0], -m.centroid[1], -m.bounds[0][2]])
    if a.ziel_mm:
        m.apply_scale(a.ziel_mm / max(m.extents))
    bericht = {"dreiecke": len(m.faces), "dicht": bool(m.is_watertight), "masse_mm": [round(float(x), 2) for x in m.extents],
               "schnitt_mm": z, "einheit": a.einheit}
    if a.vergleich:
        m, erg = vergleichen(m, a.vergleich)
        bericht["vergleich"] = {k: (round(v, 3) if isinstance(v, float) else [round(x, 2) for x in v]) for k, v in erg.items()}
    aus = os.path.join(a.aus, a.name + ".stl")
    m.export(aus)
    json.dump(bericht, open(os.path.join(a.aus, a.name + "_bericht.json"), "w"), indent=1, ensure_ascii=False)
    print(json.dumps(bericht, ensure_ascii=False))
    print("→", aus)
    if a.bild:
        os.system(f'{sys.executable} {os.path.join(os.path.dirname(__file__), "ansichten.py")} "{aus}" --aus "{a.bild}" >/dev/null 2>&1')


if __name__ == "__main__":
    main()
