#!/usr/bin/env python3
"""Fotorealistisches Abschlussbild (Blender/Cycles auf der CPU) – Studio-Licht, Boden mit weichem Schatten,
Kunststoff-Material je Farbe (matt; „gold“/„silber“ als Seidenglanz).

Aufruf:
  python3 werkzeug/foto.py a.stl b.stl c.stl --farben schwarz,gold,rot --aus foto.png [--samples 48] [--groesse 900]
  (eine Farbe je Datei; fehlt eine, wird die letzte wiederholt; Farbe auch als #rrggbb)

Braucht Blender als Python-Modul:  pip install --break-system-packages bpy   (nur Python 3.13, ~430 MB)
Dauer auf 2 Kernen: ca. 1–2 Min. bei 48 Samples und 900 px.
"""
import argparse, math, sys, time
from pathlib import Path

FARBEN = {"schwarz": (0.035, 0.035, 0.04), "weiss": (0.92, 0.91, 0.87), "weiß": (0.92, 0.91, 0.87),
          "rot": (0.75, 0.05, 0.05), "gold": (0.86, 0.66, 0.2), "silber": (0.75, 0.75, 0.76),
          "blau": (0.08, 0.25, 0.85), "gruen": (0.08, 0.55, 0.2), "grün": (0.08, 0.55, 0.2),
          "gelb": (0.95, 0.75, 0.05), "orange": (0.95, 0.38, 0.05), "grau": (0.42, 0.42, 0.44),
          "braun": (0.4, 0.22, 0.09), "creme": (0.93, 0.88, 0.72), "natur": (0.9, 0.86, 0.76), "holz": (0.65, 0.45, 0.25),
          "lila": (0.45, 0.25, 0.9), "pink": (0.92, 0.25, 0.55), "tuerkis": (0.05, 0.65, 0.58), "türkis": (0.05, 0.65, 0.58)}
SEIDE = {"gold", "silber"}


def srgb_zu_linear(c):
    return tuple((x / 12.92) if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c)


def farbe(name):
    n = name.strip().lower()
    if n.startswith("#"):
        return srgb_zu_linear(tuple(int(n[i:i + 2], 16) / 255 for i in (1, 3, 5))), False
    if n not in FARBEN:
        sys.exit(f"Farbe '{name}' unbekannt. Möglich: {', '.join(FARBEN)} oder #rrggbb")
    return srgb_zu_linear(FARBEN[n]), n in SEIDE


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("stl", nargs="+")
    ap.add_argument("--farben", default="grau")
    ap.add_argument("--aus", required=True)
    ap.add_argument("--samples", type=int, default=48)
    ap.add_argument("--groesse", type=int, default=900, help="Bildbreite in px (Höhe = 0,8 × Breite)")
    ap.add_argument("--winkel", type=float, default=-35, help="Kamera-Drehung um Z in Grad (0 = von vorn)")
    ap.add_argument("--hoehe", type=float, default=18, help="Kamera-Höhenwinkel in Grad")
    a = ap.parse_args()
    t0 = time.time()
    try:
        import bpy
        from mathutils import Vector
    except ImportError:
        sys.exit("Blender-Modul fehlt: pip install --break-system-packages bpy")

    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    namen = [x for x in a.farben.split(",") if x.strip()]
    objekte = []
    for i, pfad in enumerate(a.stl):
        bpy.ops.wm.stl_import(filepath=str(Path(pfad).resolve()))
        ob = bpy.context.selected_objects[0]
        rgb, seide = farbe(namen[min(i, len(namen) - 1)])
        mat = bpy.data.materials.new(f"PLA_{i}"); mat.use_nodes = True
        bsdf = mat.node_tree.nodes["Principled BSDF"]
        bsdf.inputs["Base Color"].default_value = (*rgb, 1)
        bsdf.inputs["Roughness"].default_value = 0.28 if seide else 0.5
        bsdf.inputs["Metallic"].default_value = 0.55 if seide else 0.0
        if "Coat Weight" in bsdf.inputs and seide:
            bsdf.inputs["Coat Weight"].default_value = 0.3
        ob.data.materials.append(mat)
        try:
            bpy.context.view_layer.objects.active = ob
            bpy.ops.object.shade_auto_smooth(angle=math.radians(35))
        except Exception:
            for p in ob.data.polygons:
                p.use_smooth = True
        objekte.append(ob)

    # Begrenzung aller Objekte
    pts = [ob.matrix_world @ Vector(c) for ob in objekte for c in ob.bound_box]
    lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    mitte = (lo + hi) / 2; r = (hi - lo).length / 2

    # Boden (helles Grau, matt) – großzügig, damit kein Horizont sichtbar ist
    bpy.ops.mesh.primitive_plane_add(size=r * 60, location=(mitte.x, mitte.y, lo.z))
    boden = bpy.context.active_object
    bm = bpy.data.materials.new("Boden"); bm.use_nodes = True
    bb = bm.node_tree.nodes["Principled BSDF"]
    bb.inputs["Base Color"].default_value = (0.62, 0.62, 0.64, 1); bb.inputs["Roughness"].default_value = 0.8
    boden.data.materials.append(bm)

    # Welt: weiches, helles Umgebungslicht
    welt = bpy.data.worlds.new("Studio"); sc.world = welt; welt.use_nodes = True
    welt.node_tree.nodes["Background"].inputs["Color"].default_value = (0.75, 0.76, 0.78, 1)
    welt.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.45

    def licht(name, energie, groesse, az, el, abst):
        az, el = math.radians(az), math.radians(el)
        pos = mitte + Vector((math.sin(az) * math.cos(el), -math.cos(az) * math.cos(el), math.sin(el))) * abst
        L = bpy.data.lights.new(name, "AREA"); L.energy = energie; L.size = groesse
        o = bpy.data.objects.new(name, L); o.location = pos
        o.rotation_euler = (mitte - pos).to_track_quat("-Z", "Y").to_euler()
        sc.collection.objects.link(o)
    s = r / 50.0                                                    # Lichtstärke mit der Modellgröße skalieren (mm)
    licht("Haupt", 9.0e4 * s * s, r * 2.2, a.winkel - 40, 50, r * 4)
    licht("Fuell", 3.0e4 * s * s, r * 3.0, a.winkel + 70, 25, r * 4)
    licht("Kante", 5.0e4 * s * s, r * 1.5, a.winkel + 160, 40, r * 4)

    # Kamera
    cam_d = bpy.data.cameras.new("Kamera"); cam_d.lens = 70
    cam = bpy.data.objects.new("Kamera", cam_d); sc.collection.objects.link(cam); sc.camera = cam
    az, el = math.radians(a.winkel), math.radians(a.hoehe)
    richtung = Vector((math.sin(az) * math.cos(el), -math.cos(az) * math.cos(el), math.sin(el)))
    fov = 2 * math.atan(18 / cam_d.lens)                           # Sensorbreite 36 mm, Höhe 0,8 × Breite
    abst = r / math.sin(fov * 0.8 / 2) * 1.02
    cam.location = mitte + richtung * abst
    cam.rotation_euler = (-richtung).to_track_quat("-Z", "Y").to_euler()
    cam_d.clip_start = r * 0.01; cam_d.clip_end = abst + r * 100

    # Render
    sc.render.engine = "CYCLES"; sc.cycles.device = "CPU"
    sc.cycles.samples = a.samples; sc.cycles.use_denoising = True
    sc.cycles.max_bounces = 6
    sc.render.resolution_x = a.groesse; sc.render.resolution_y = int(a.groesse * 0.8); sc.render.resolution_percentage = 100
    sc.render.image_settings.file_format = "PNG"
    try:
        sc.view_settings.view_transform = "AgX"; sc.view_settings.look = "AgX - Medium High Contrast"
    except Exception:
        pass
    sc.render.filepath = str(Path(a.aus).resolve())
    bpy.ops.render.render(write_still=True)
    print(f"OK  {a.aus}  ({time.time() - t0:.0f} s, {a.samples} Samples, {a.groesse} px)")


if __name__ == "__main__":
    main()
