#!/usr/bin/env python3
"""Große oder fremde STL in druckbare Stücke teilen – mit Löchern für Passstifte (18.11.2026).

Angeregt vom Bastlwastl-Video zu Aimia (MakerLab): dort setzt das Werkzeug beim Teilen Verbinder mit Spiel 0,20 mm.
Hier geht es mit geraden Schnitten (kein KI-Erkennen von Formen), dafür ohne Konto und ohne Credits.

Aufruf:
  python3 werkzeug/teilen.py modell.stl --aus /tmp/teile                     # automatisch, bis alles in den Bauraum passt
  python3 werkzeug/teilen.py modell.stl --aus /tmp/t --achse z --bei 40      # ein Schnitt quer zur Z-Achse bei 40 mm
  python3 werkzeug/teilen.py modell.stl --aus /tmp/t --achse x --bei mitte --stift filament
Optionen:
  --bett 250        größtes Maß je Stück (Creator 5 Pro: 256 mm, Rand abgezogen)
  --stift druck|filament|keine   druck = gedruckte Stifte (Ø --stift-d, Spiel --spiel je Seite, eigene STL),
                    filament = Stückchen 1,75-mm-Filament (Loch Ø 1,95), keine = nur kleben
  --stift-d 4  --spiel 0.2  --tiefe 6 (je Seite)  --wand 1.6 (Abstand Loch – Außenkante)
  --lage auto|original|schnitt   auto: Schnitt quer zu Z → Schnittfläche nach unten drehen, sonst Lage behalten
Ausgabe: <name>_teil1.stl … , <name>_stift.stl (bei --stift druck), teile.json, Konsolenbericht.
"""
import argparse
import json
import math
from pathlib import Path

import numpy as np
import trimesh
import manifold3d as mf

PERM = {  # Drehung, die die Schnittachse auf Z legt (zyklische Vertauschung, Determinante +1)
    "x": np.array([[0, 1, 0], [0, 0, 1], [1, 0, 0]], float),
    "y": np.array([[0, 0, 1], [1, 0, 0], [0, 1, 0]], float),
    "z": np.eye(3),
}


def zu_manifold(m):
    m = m.copy()
    if not m.is_watertight:
        trimesh.repair.fill_holes(m)
        trimesh.repair.fix_normals(m)
    mm = mf.Manifold(mf.Mesh(vert_properties=np.asarray(m.vertices, np.float32),
                             tri_verts=np.asarray(m.faces, np.uint32)))
    if mm.status() != mf.Error.NoError or mm.volume() <= 0:
        raise SystemExit(f"Netz ist nicht geschlossen ({mm.status()}) – erst mit werkzeug/ki_rohling.py reparieren.")
    return mm


def zu_trimesh(mm):
    g = mm.to_mesh()
    return trimesh.Trimesh(np.asarray(g.vert_properties)[:, :3], np.asarray(g.tri_verts), process=True)


def drehen(mm, R):
    return mm.transform(np.hstack([R, np.zeros((3, 1))]))


def stiftpunkte(querschnitt, r_loch, wand):
    """Punkte für Stifte im Schnitt: je Insel mit Platz einer, längliche Inseln zwei weit auseinander."""
    from matplotlib.path import Path as MPath
    innen = querschnitt.offset(-(r_loch + wand), mf.JoinType.Round)
    pkt = []
    for insel in innen.decompose():
        if insel.area() < math.pi * r_loch ** 2 * 0.5:
            continue
        polys = [np.asarray(p) for p in insel.to_polygons()]
        alle = np.vstack(polys)
        lo, hi = alle.min(0), alle.max(0)
        h = max(0.3, float((hi - lo).max()) / 300)
        gx, gy = np.meshgrid(np.arange(lo[0], hi[0] + h, h), np.arange(lo[1], hi[1] + h, h))
        P = np.c_[gx.ravel(), gy.ravel()]
        drin = np.zeros(len(P), bool)
        for poly in polys:                      # gerade/ungerade-Regel: Löcher heben sich auf
            drin ^= MPath(poly).contains_points(P)
        P = P[drin]
        if not len(P):
            continue
        mitte = P.mean(0)
        p1 = P[np.linalg.norm(P - mitte, axis=1).argmax()]
        p2 = P[np.linalg.norm(P - p1, axis=1).argmax()]
        if np.linalg.norm(p2 - p1) > 8 * r_loch:
            for q, z in ((p1, p2), (p2, p1)):
                ziel = q + 0.18 * (z - q)       # etwas nach innen, nächster Rasterpunkt im Inneren
                pkt.append(P[np.linalg.norm(P - ziel, axis=1).argmin()])
        else:
            pkt.append(P[np.linalg.norm(P - mitte, axis=1).argmin()])
    return pkt


def schneiden(mm, achse, z0, a, nr):
    """Ein Schnitt quer zu `achse` bei Lage z0 (Weltkoordinate). Gibt (unten, oben, anzahl_stifte)."""
    R = PERM[achse]
    m = drehen(mm, R)
    oben, unten = m.split_by_plane([0, 0, 1], z0)
    n = 0
    if a.stift != "keine":
        r = (1.95 / 2) if a.stift == "filament" else (a.stift_d / 2 + a.spiel)
        bo, bu = np.array(oben.bounding_box()), np.array(unten.bounding_box())
        platz = min(bo[5] - z0, z0 - bu[2])                 # Dicke der dünneren Hälfte
        tiefe = min(6.0 if a.stift == "filament" else a.tiefe, 0.4 * platz) + 0.5
        a.tiefe_echt = min(getattr(a, "tiefe_echt", 99), tiefe - 0.5)
        punkte = stiftpunkte(m.slice(z0), r, a.wand)
        for (x, y) in punkte:
            loch = mf.Manifold.cylinder(2 * tiefe, r, r, 48, True).translate([float(x), float(y), z0])
            oben -= loch
            unten -= loch
        n = len(punkte)
    return drehen(unten, R.T), drehen(oben, R.T), n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("stl")
    ap.add_argument("--aus", required=True)
    ap.add_argument("--name")
    ap.add_argument("--achse", default="auto", choices=["auto", "x", "y", "z"])
    ap.add_argument("--bei", default="mitte")
    ap.add_argument("--bett", type=float, default=250.0)
    ap.add_argument("--stift", default="druck", choices=["druck", "filament", "keine"])
    ap.add_argument("--stift-d", type=float, default=4.0)
    ap.add_argument("--spiel", type=float, default=0.2)
    ap.add_argument("--tiefe", type=float, default=6.0)
    ap.add_argument("--wand", type=float, default=1.6)
    ap.add_argument("--lage", default="auto", choices=["auto", "original", "schnitt"])
    a = ap.parse_args()

    aus = Path(a.aus); aus.mkdir(parents=True, exist_ok=True)
    name = a.name or Path(a.stl).stem
    start = zu_manifold(trimesh.load(a.stl, force="mesh"))
    stuecke = [(start, None)]          # (Netz, Achse des letzten Schnitts, Seite)
    stifte = 0
    schnitte = []
    if a.achse == "auto":
        fertig = []
        while stuecke:
            mm, info = stuecke.pop()
            bb = np.array(mm.bounding_box()); lo, hi = bb[:3], bb[3:]
            ext = hi - lo
            if ext.max() <= a.bett:
                fertig.append((mm, info)); continue
            ach = "xyz"[int(ext.argmax())]
            teile = math.ceil(ext.max() / a.bett)
            z0 = float(lo[ext.argmax()] + ext.max() / teile)   # erstes Stück voll, Rest weiter teilen
            u, o, n = schneiden(mm, ach, z0, a, len(schnitte))
            stifte += n; schnitte.append((ach, round(z0, 2), n))
            stuecke += [(u, (ach, "unten")), (o, (ach, "oben"))]
        stuecke = fertig
    else:
        bb = np.array(start.bounding_box()); lo, hi = bb[:3], bb[3:]
        i = "xyz".index(a.achse)
        z0 = float((lo[i] + hi[i]) / 2 if a.bei == "mitte" else float(a.bei))
        u, o, n = schneiden(start, a.achse, z0, a, 0)
        stifte += n; schnitte.append((a.achse, round(z0, 2), n))
        stuecke = [(u, (a.achse, "unten")), (o, (a.achse, "oben"))]

    bericht = {"quelle": str(a.stl), "schnitte": schnitte, "stifte": stifte, "teile": []}
    for k, (mm, info) in enumerate(sorted(stuecke, key=lambda s: -s[0].volume()), 1):
        t = zu_trimesh(mm)
        lage = a.lage
        if lage == "auto":
            lage = "schnitt" if info and info[0] == "z" else "original"
        if lage == "schnitt" and info and info[1] == "unten":
            # Schnittfläche liegt oben → umdrehen, damit sie auf dem Bett liegt
            t.apply_transform(trimesh.transformations.rotation_matrix(math.pi, [1, 0, 0]))
        t.apply_translation(-t.bounds[0] * [0, 0, 1])
        datei = aus / f"{name}_teil{k}.stl"
        t.export(datei)
        e = np.round(t.extents, 1).tolist()
        bericht["teile"].append({"datei": datei.name, "masse_mm": e, "volumen_cm3": round(t.volume / 1000, 1),
                                 "dicht": bool(t.is_watertight), "passt": bool(max(e) <= a.bett + 6)})
        print(f"{datei.name}: {e[0]} × {e[1]} × {e[2]} mm, {t.volume / 1000:.1f} cm³, dicht={t.is_watertight}, "
              f"{'passt' if max(e) <= a.bett + 6 else 'ZU GROSS'}")
    if a.stift == "druck" and stifte:
        l = 2 * round(getattr(a, "tiefe_echt", a.tiefe), 1)
        s = trimesh.creation.cylinder(radius=a.stift_d / 2, height=l, sections=48)
        s.apply_translation([0, 0, l / 2])
        s.export(aus / f"{name}_stift.stl")
        print(f"{name}_stift.stl: Ø {a.stift_d} × {l} mm – {stifte} Stück drucken (liegend, 100 % Füllung)")
    elif a.stift == "filament" and stifte:
        print(f"{stifte} Stückchen 1,75-mm-Filament, je {2 * round(a.tiefe_echt, 1)} mm, als Passstift (Loch Ø 1,95)")
    print("Schnitte:", ", ".join(f"{s[0]}={s[1]} mm ({s[2]} Stifte)" for s in schnitte) or "keine nötig")
    (aus / "teile.json").write_text(json.dumps(bericht, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
