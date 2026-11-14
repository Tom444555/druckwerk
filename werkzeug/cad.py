#!/usr/bin/env python3
"""CAD-Stufe mit build123d: führt ein Modell-Skript aus und schreibt je Farbe eine STL + eine STEP-Datei.

Aufruf:   python3 werkzeug/cad.py modelle/beispiel_winkel.py [--name winkel] [--ziel modelle]
Ergebnis: modelle/<name>.stl (eine Farbe) bzw. modelle/<name>_<farbe>.stl (mehrere) + modelle/<name>.step
Danach:   python3 werkzeug/druck.py --drucker c5pro --name <name> --teil modelle/<name>.stl:PETG:1 --schicht 0.20 --waende 4

Modell-Skript: definiert `modell()` und gibt zurück
  - einen build123d-Körper (eine Farbe) oder
  - ein dict {"schwarz": körper1, "gold": körper2, …} – Reihenfolge = Kopf 1…4, gleiche Koordinaten.
Helfer (im Skript: `from cad import rundung, fase, schraubloch`):
  rundung(teil, kanten, r) · fase(teil, kanten, l) · schraubloch(teil, (x,y,z), m=4, art="senk"|"zyl"|"durch",
  tiefe=…, richtung=(0,0,-1))  – Bohrung beginnt an der Oberfläche im Punkt (x,y,z) und geht in `richtung`.
Maße in mm, Spiel 0,2 mm (wie modelle/baukasten/baukasten.scad). Installation: werkzeug/setup.sh (pip build123d).
"""
import argparse, itertools, runpy, sys
from pathlib import Path

from build123d import (Compound, Cone, Cylinder, Plane, Pos, Vector, chamfer, export_step, export_stl, fillet)

SPIEL = 0.2
DURCH = {3: 3.4, 4: 4.5, 5: 5.5, 6: 6.6, 8: 9.0}          # ISO 273 mittel
SENK_DK = {3: 6.72, 4: 8.96, 5: 11.2, 6: 13.44, 8: 17.92}  # DIN 7991 / ISO 10642
ZYL_DK = {3: 5.5, 4: 7.0, 5: 8.5, 6: 10.0, 8: 13.0}        # DIN 912


def rundung(teil, kanten, r):
    """Kanten runden (build123d fillet). kanten z. B. teil.edges().filter_by(Axis.Z)"""
    return fillet(kanten, r)


def fase(teil, kanten, l):
    """Kanten anfasen (45°)."""
    return chamfer(kanten, l)


def schraubloch(teil, pos, m=4, art="senk", tiefe=20.0, richtung=(0, 0, -1), spiel=SPIEL, versenkt=0.2):
    """Schraubloch abziehen: Durchgang (ISO 273 + Spiel), optional Senkkopf 90° oder Zylinderkopf-Senkung."""
    d = DURCH[m] + spiel
    werkzeug = Pos(0, 0, -tiefe / 2 + 0.01) * Cylinder(d / 2, tiefe + 0.02)
    if art == "senk":
        dk = SENK_DK[m] + 2 * spiel
        werkzeug += Pos(0, 0, -versenkt - dk / 4) * Cone(0, dk / 2, dk / 2)
        werkzeug += Pos(0, 0, -versenkt / 2 + 0.01) * Cylinder(dk / 2, versenkt + 0.02)
    elif art == "zyl":
        kt = m + 0.4; dk = ZYL_DK[m] + 0.8 + spiel
        werkzeug += Pos(0, 0, -kt / 2 + 0.01) * Cylinder(dk / 2, kt + 0.02)
    r = Vector(*richtung).normalized()
    ebene = Plane(origin=pos, z_dir=-r)                      # lokale +Z zeigt aus dem Teil heraus
    return teil - ebene.location * werkzeug


def _pruefe(pfad):
    import trimesh
    t = trimesh.load(pfad)
    return t.is_watertight, t.volume, t.extents, t


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("skript"); ap.add_argument("--name"); ap.add_argument("--ziel", default="modelle")
    ap.add_argument("--fein", type=float, default=0.01, help="STL-Toleranz in mm (kleiner = feiner)")
    a = ap.parse_args()
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    skript = Path(a.skript); name = a.name or skript.stem.replace("beispiel_", "")
    ergebnis = runpy.run_path(str(skript))["modell"]()
    farben = ergebnis if isinstance(ergebnis, dict) else {"": ergebnis}
    ziel = Path(a.ziel); ziel.mkdir(parents=True, exist_ok=True)
    netze = {}
    for farbe, koerper in farben.items():
        datei = ziel / (f"{name}_{farbe}.stl" if farbe else f"{name}.stl")
        export_stl(koerper, str(datei), tolerance=a.fein, angular_tolerance=0.1)
        dicht, vol, mass, t = _pruefe(datei); netze[datei.name] = t
        print(f"{datei}: dicht={dicht}, {vol / 1000:.2f} cm³, Maße {mass.round(2).tolist()} mm, {len(t.faces)} Dreiecke")
    step = ziel / f"{name}.step"
    export_step(Compound(list(farben.values())) if len(farben) > 1 else next(iter(farben.values())), str(step))
    print(f"{step}: STEP geschrieben")
    if len(netze) > 1:                                      # Farbkörper dürfen sich nicht überschneiden
        import manifold3d as m3, numpy as np
        mf = {k: m3.Manifold(m3.Mesh(np.asarray(t.vertices, np.float32), np.asarray(t.faces, np.uint32))) for k, t in netze.items()}
        for x, y in itertools.combinations(mf, 2):
            print(f"Schnittvolumen {x} ∩ {y}: {(mf[x] ^ mf[y]).volume():.3f} mm³")
    teile = " ".join(f"--teil {ziel}/{k}:PLA:{i + 1}" for i, k in enumerate(netze))
    print(f"Slicen: python3 werkzeug/druck.py --drucker c5pro --name {name} {teile}"
          f"{' --zusammen' if len(netze) > 1 else ''} --schicht 0.20 --infill 30 --waende 4")


if __name__ == "__main__":
    main()
