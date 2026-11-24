#!/usr/bin/env python3
"""anhaenger.py – aus einer kleinen mehrfarbigen Gitarre (je Farbe eine STL, liegend, Rückseite auf z = 0) einen Schlüsselanhänger in EINEM Teil machen.

  python3 werkzeug/anhaenger.py --aus <ordner> --teil korpus=a.stl --teil hals=b.stl --teil metall=c.stl … [--korpus korpus] [--hals hals]

Was es tut (Tom 24.11.2026: „beide Gitarren als Schlüsselanhänger auf 5 cm, als 1 Teil, so viele Details wie möglich“):
1. Hals und Kopfplatte bekommen von unten eine Füllung bis aufs Bett (Farbe --hals): aus dem dünnen Hals (≈ 1,2 mm) wird ein Balken in voller Höhe –
   sonst bricht er am Schlüsselbund. Die Unterseite wird dazu per Strahlen abgetastet (Raster 0,12 mm) und je Zelle eine Säule gesetzt.
   Seit 24.11. als Kiel (--kiel 0.3): unten schmaler, steile Flanken – der Hals wirkt schlanker, bleibt aber durchgehend bis in den Korpus auf dem Bett.
2. Loch für den Schlüsselring vorn oben durch die Kopfplatte (--kopfloch 2.0, an der breitesten Stelle, Rand mindestens --rand). Die frühere Öse am Korpus-Ende: --oese 6.
Die Vorderseite bleibt unverändert. Ausgabe: gleiche Dateinamen im Ordner --aus. Nur gerechnet, nicht gedruckt.
"""
import argparse, shutil, numpy as np, trimesh, manifold3d as mf
from pathlib import Path


def man(t):
    m = mf.Manifold(mf.Mesh(np.asarray(t.vertices, np.float32), np.asarray(t.faces, np.uint32)))
    return m if m.status() == mf.Error.NoError else None


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--teil", action="append", required=True, help="name=datei.stl (mehrfach)")
    ap.add_argument("--aus", required=True); ap.add_argument("--korpus", default=None); ap.add_argument("--hals", default=None)
    ap.add_argument("--raster", type=float, default=0.12); ap.add_argument("--oese", type=float, default=0.0, help="Außen-Ø einer Öse am Korpus-Ende (0 = keine; Tom 24.11.: weg, Loch in die Kopfplatte)")
    ap.add_argument("--loch", type=float, default=3.2)
    ap.add_argument("--kopfloch", type=float, default=2.0, help="Loch-Ø durch die Kopfplatte für den Schlüsselring (0 = keins); wird kleiner, wenn sonst weniger als --rand stehen bleibt")
    ap.add_argument("--rand", type=float, default=0.7); ap.add_argument("--kiel", type=float, default=0.3, help="Hals hinten schlanker: Einzug je Seite als Anteil der Halsbreite (0 = Balken)")
    ap.add_argument("--spalt", type=float, default=0.3, help="unter dem Korpus Spalte bis zu dieser Höhe füllen (Korpus liegt dann satt auf dem Bett)")
    a = ap.parse_args()
    T = {}
    for s in a.teil:
        n, f = s.split("=", 1); T[n] = (Path(f), trimesh.load(f, process=True))
    namen = list(T); korpus = a.korpus or namen[0]; hals = a.hals or korpus
    alle = trimesh.util.concatenate([t for _, t in T.values()])
    b = alle.bounds; print(f"Gitarre {alle.extents.round(1).tolist()} mm")
    # Korpus-Ende und Hals-Anfang aus dem Breitenprofil entlang y (Korpus unten bei kleinem y)
    v = alle.vertices; ys = np.arange(b[0][1], b[1][1], 0.25)
    br = np.array([np.ptp(v[np.abs(v[:, 1] - y) < 0.3, 0]) if (np.abs(v[:, 1] - y) < 0.3).any() else 0 for y in ys])
    i_max = int(np.argmax(br)); schmal = np.where((np.arange(len(ys)) > i_max) & (br < 0.42 * br.max()))[0]
    y_hals = float(ys[schmal[0]]) if len(schmal) else float(ys[-1]); print(f"Korpus bis y {y_hals:.1f} mm, größte Breite {br.max():.1f} mm")
    aus = Path(a.aus); aus.mkdir(parents=True, exist_ok=True)
    zus = {korpus: [], hals: []}
    # 1) Füllung unter Hals und Kopfplatte
    r = a.raster; gx = np.arange(b[0][0] + r / 2, b[1][0], r); gy = np.arange(b[0][1] + r / 2, b[1][1], r)
    X, Y = np.meshgrid(gx, gy); o = np.column_stack([X.ravel(), Y.ravel(), np.full(X.size, -1.0)])
    loc, idx, _ = alle.ray.intersects_location(o, np.tile([0, 0, 1.0], (len(o), 1)), multiple_hits=False)
    zb = np.full(len(o), np.nan); zb[idx] = loc[:, 2]
    im_hals = o[:, 1] > y_hals - 0.4
    # Hals hinten schlanker (Tom 24.11.): Füllung als Kiel – unten schmal, nach oben bis zur vollen Halsbreite (steile Flanken, druckt ohne Stützen); läuft durchgehend in den Korpus.
    from scipy import ndimage
    maske = (zb == zb).reshape(X.shape); dist = ndimage.distance_transform_edt(maske) * r; breite = maske.sum(axis=1) * r
    jh = np.where(gy > y_hals)[0]; med = float(np.median(breite[jh[: max(1, int(len(jh) * 0.55))]]))
    jk = [j for j in jh[int(len(jh) * 0.45):] if breite[j] > 1.2 * med]; y_kopf = float(gy[jk[0]]) if jk else float(gy[-1])
    print(f"Hals {med:.2f} mm breit, Kopfplatte ab y {y_kopf:.1f}")
    einzug = a.kiel * med * np.clip((y_kopf - Y) / 1.5, 0.0, 1.0)                                  # an der Kopfplatte läuft der Kiel in die volle Fläche aus
    start = (zb.reshape(X.shape) * np.clip(1.0 - dist / np.maximum(einzug, 1e-6), 0.0, 1.0)).ravel() if a.kiel > 0 else np.zeros(len(o))
    def saeule(p, z, z0=0.0):
        z0 = float(z0) if z0 > 0.03 else 0.0
        return mf.Manifold.cube([r + 0.01, r + 0.01, float(z) + 0.04 - z0]).translate([float(p[0] - r / 2), float(p[1] - r / 2), z0])
    saeulen = [saeule(p, z, z0) for p, z, z0 in zip(o[im_hals], zb[im_hals], start[im_hals]) if z == z and z > 0.06 and z - z0 > 0.02]
    # Loch für den Schlüsselring vorn oben in der Kopfplatte: breiteste Stelle der Kopfplatte
    lochk = None
    if a.kopfloch > 0:
        dk = np.where((Y > y_kopf + 0.5) & maske, dist, 0.0); j0, i0_ = np.unravel_index(int(np.argmax(dk)), dk.shape)
        dl = min(a.kopfloch, 2 * (float(dk[j0, i0_]) - a.rand)); lochk = mf.Manifold.cylinder(40, dl / 2, dl / 2, 48).translate([float(gx[i0_]), float(gy[j0]), -20])
        lochxy = (float(gx[i0_]), float(gy[j0]), dl / 2); print(f"Loch in der Kopfplatte: Ø {dl:.2f} bei x {gx[i0_]:.1f} / y {gy[j0]:.1f}, Rand ringsum mindestens {dk[j0, i0_] - dl / 2:.2f} mm")
    if saeulen:
        f = mf.Manifold.batch_boolean(saeulen, mf.OpType.Add); zus[hals].append(f)
        print(f"Füllung unter dem Hals: {len(saeulen)} Säulen, {f.volume():.1f} mm³, bis {np.nanmax(zb[im_hals]):.2f} mm hoch")
    # unter dem Korpus nur die ebene Rückseite aufs Bett holen, wenn sie schwebt (vorstehende Deckel im Netz): häufigste Höhe suchen – Rundungen und Ausfräsungen bleiben
    zk = zb[~im_hals]; zk = zk[zk == zk]
    if len(zk):
        h, kanten = np.histogram(zk, bins=np.arange(-0.01, a.spalt + 0.02, 0.02)); eben = float(kanten[int(np.argmax(h))] + 0.01)
        if eben > 0.04:
            sk = [saeule(p, z) for p, z in zip(o[~im_hals], zb[~im_hals]) if z == z and abs(z - eben) < 0.025]
            zus[korpus].append(mf.Manifold.batch_boolean(sk, mf.OpType.Add)); print(f"Korpus-Rückseite lag {eben:.2f} mm über dem Bett → {len(sk)} Säulen darunter")
    # 2) Öse am Korpus-Ende
    if a.oese > 0:
        kt = T[korpus][1]; kv = kt.vertices; i0 = int(np.argmin(kv[:, 1])); x0 = float(np.median(kv[kv[:, 1] < kv[i0, 1] + 0.15, 0]))
        dick = min(2.0, float(kt.bounds[1][2])); R, rl = a.oese / 2, a.loch / 2; cy = float(kv[i0, 1]) - R + 0.9
        ring = (mf.Manifold.cylinder(dick, R, R, 64) - mf.Manifold.cylinder(dick + 1, rl, rl, 48).translate([0, 0, -0.5])).translate([x0, cy, 0])
        fase = mf.Manifold.cylinder(0.3, R - 0.3, R, 64).translate([x0, cy, 0]) + mf.Manifold.cylinder(dick - 0.6, R, R, 64).translate([x0, cy, 0.3]) + mf.Manifold.cylinder(0.3, R, R - 0.3, 64).translate([x0, cy, dick - 0.3])
        zus[korpus].append(ring ^ fase); print(f"Öse: außen Ø {a.oese}, Loch Ø {a.loch}, {dick:.2f} dick, Mitte x {x0:.1f} / y {cy:.1f}; Gesamtlänge {b[1][1] - (cy - R):.1f} mm")
    for n, (pf, t) in T.items():
        ziel = aus / pf.name; m = man(t)
        if m is None:                                            # nicht mannigfaltig: Zusätze als eigene Körper in dieselbe Datei (der Slicer vereinigt Überlappungen)
            if lochk is not None:                                # Loch: Flächen im Lochkreis weglassen
                c = t.triangles_center; t = t.copy(); t.update_faces(np.hypot(c[:, 0] - lochxy[0], c[:, 1] - lochxy[1]) > lochxy[2] + 0.05); t.remove_unreferenced_vertices()
            zz = [z - lochk if lochk is not None else z for z in zus.get(n, [])]
            teile = [t] + [trimesh.Trimesh(z.to_mesh().vert_properties[:, :3], z.to_mesh().tri_verts) for z in zz]
            trimesh.util.concatenate(teile).export(ziel); print(f"{n}: nicht dicht – Zusätze als eigene Körper angehängt, {len(t.faces)} Flächen")
        else:
            for z in zus.get(n, []): m = m + z
            if lochk is not None: m = m - lochk
            me = m.to_mesh(); o2 = trimesh.Trimesh(me.vert_properties[:, :3], me.tri_verts); o2.export(ziel)
            print(f"{n}: {len(o2.faces)} Flächen, dicht={o2.is_watertight}, {o2.extents.round(1).tolist()}")


if __name__ == "__main__":
    main()
