#!/usr/bin/env python3
"""gitarrenhalter190.py – Ständer für Toms 190-mm-Gitarren (Schecter und Stratocaster), Entwurf 24.11.2026. Nur gerechnet.

  python3 modelle/gitarrenhalter190.py --ziel /tmp/h [--bild /tmp/h/v.png] [--winkel 12] [--kanal 9.4]

Idee: zwei Wangen (je 5 mm) im Abstand von 30 mm, verbunden nur durch EINE Querstrebe hinten (Spitzbogen) – keine Grundplatte, keine Kufen (Toms Wunsch); jede Wange ist eine geschwungene Linie mit eingelassenem Lochblech-Muster. Die Gitarre steht mit der Korpus-Unterkante in einem Kanal
(Boden senkrecht zur Lehne, vorn eine Lippe) und lehnt mit der Korpus-Rückseite um 12° nach hinten an den Lehnen. Sie liegt auf ZWEI Punkten
(links und rechts der Mitte) auf – der Gurtknopf in der Mitte hängt frei zwischen den Wangen, die Gitarre kippelt nicht.
Die Lehne endet unter dem Hals: die Wirbelräder hinten an der Kopfplatte bleiben frei (deshalb kann die Gitarre nicht liegen).
Druck: aufrecht, wie er steht, ohne Stützen (Lehne 12° Überhang, keine Brücken). Passung geprüft per Schnittvolumen mit beiden Gitarren.
"""
import argparse, math, numpy as np, trimesh, manifold3d as mf
from pathlib import Path

CS, M, RUND = mf.CrossSection, mf.Manifold, mf.JoinType.Round
HIER = Path(__file__).resolve().parent.parent


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--ziel", default="/tmp/halter190"); ap.add_argument("--bild", default="")
    ap.add_argument("--zwei", type=int, default=1, help="1 = zweifarbig: Lochfeld als goldene Blende (gitarrenhalter190_gold.stl)")
    ap.add_argument("--winkel", type=float, default=12.0, help="Neigung der Gitarre nach hinten (Grad)")
    ap.add_argument("--kanal", type=float, default=9.4, help="lichte Weite des Kanals (dickster Korpus 8,74 + Luft)")
    ap.add_argument("--lehne", type=float, default=66.0, help="Länge der Lehne ab Kanalboden")
    a = ap.parse_args()
    w = math.radians(a.winkel); u = np.array([math.sin(w), math.cos(w)]); f = np.array([-math.cos(w), math.sin(w)])   # (Tiefe, Höhe): u = an der Lehne hoch, f = nach vorn
    A = np.array([0.0, 7.5]); B = A + a.kanal * f; B3 = B + 3.0 * f; LIP = 5.5; YR = 52.0; LD = 3.6      # LD = Stärke der Lehne
    P = lambda *q: CS([np.array([list(map(float, x)) for x in q])], mf.FillRule.Positive)
    def poly(*q):
        c = P(*q)
        return c if c.area() > 0 else P(*q[::-1])
    bz = lambda p0, p1, p2, n=48: [((1 - t) ** 2) * np.asarray(p0, float) + 2 * (1 - t) * t * np.asarray(p1, float) + t * t * np.asarray(p2, float) for t in np.linspace(0, 1, n)]
    # Tom 24.11., 12:25: „unten die Querstreben weg, nur hinten eine, und alles etwas eleganter“ → eine Wange = EINE geschwungene Linie:
    # vorn läuft die Lippe in einem Bogen in die Zehe aus, hinten schwingt die Lehne von der Spitze in einem Zug bis zur Ferse.
    oben = A + a.lehne * u; ruecken = bz(oben - LD * f, (A[0] + LD + 6.0, 15.0), (YR, 0.0)); zehe = bz((B3[0] - 10.0, 0.0), (B3[0] - 1.2, 1.6), B3 + LIP * u, 24)
    wange = poly(*zehe, B + LIP * u, B, A, oben, *ruecken)
    kanal = poly(A + 0.02 * u, A + 40 * u, B + 40 * u, B + 0.02 * u)                               # Kanal bleibt frei (Rundung darf ihn nicht zusetzen)
    wange = wange.offset(-0.9, RUND, 2.0, 32).offset(0.9, RUND, 2.0, 32) - kanal.offset(-0.01)
    dreh = np.array([[0, 0, 1, 0], [1, 0, 0, 0], [0, 1, 0, 0]], float)                              # (Tiefe, Höhe, Dicke) → (X, Tiefe, Höhe)
    _s = (wange ^ poly((33.3, -1), (33.7, -1), (33.7, 80), (33.3, 80))).bounds()                 # Wange bei Tiefe 33,5 senkrecht schneiden (Bezier ist in der Tiefe nicht monoton)
    hq = float(_s[3]) - 0.9                                                                        # Höhe der Wange an der Querstrebe
    # Lochblech-Feld: hinter der Lehne, mit Rahmen; 1 mm je Seite eingelassen; Löcher werden nach oben kleiner
    lehne = poly(A, oben, oben - LD * f, A - LD * f); block = poly((B3[0] - 12, -1), (A[0] + LD, -1), (A[0] + LD, A[1] + 1.5), (B3[0] - 12, A[1] + 1.5))
    feld = (wange - lehne.offset(0.3) - block - poly((-40, -1), (YR + 5, -1), (YR + 5, 3.6), (-40, 3.6)) - poly((30.8, -1), (36.2, -1), (36.2, hq + 1.4), (30.8, hq + 1.4)))
    feld = feld.offset(-2.2, RUND, 2.0, 32).offset(-0.7, RUND, 2.0, 32).offset(0.7, RUND, 2.0, 32)
    innen = feld.offset(-0.7, RUND, 2.0, 16); b_ = feld.bounds(); loecher = []; zf = max(b_[3] - b_[1], 1.0)
    for j, zz in enumerate(np.arange(b_[1] + 1.2, b_[3], 3.4 * math.sqrt(3) / 2)):
        rl = 1.3 - 0.75 * (zz - b_[1]) / zf                                                         # unten Ø 2,6, oben Ø 1,1
        for yy in np.arange(b_[0] + (1.7 if j % 2 else 0.0), b_[2], 3.4):
            c = CS.circle(rl, 28).translate([yy, zz])
            if (c - innen.offset(0.7 - 0.25)).area() < 1e-6: loecher.append(c)
    loch = CS.batch_boolean(loecher, mf.OpType.Add) if loecher else CS()
    def fase(cs, t=5.0, c=0.75, n=5):                                                               # Wange mit gebrochenen Kanten (Fase in feinen Stufen)
        k = cs.extrude(t - 2 * c).translate([0, 0, c])
        for i in range(n):
            e = cs.offset(-c * (n - i) / n, RUND, 2.0, 16); h = c / n
            k = k + e.extrude(h + 0.001).translate([0, 0, i * h]) + e.extrude(h + 0.001).translate([0, 0, t - (i + 1) * h - 0.001])
        return k
    def wg(x0):
        k = fase(wange) - feld.extrude(1.0) - feld.extrude(1.0).translate([0, 0, 4.0]) - loch.extrude(7.0).translate([0, 0, -1.0])
        if a.zwei: k = k - scheibe.extrude(3.0).translate([0, 0, 1.0])
        return k.transform(dreh).translate([x0, 0, 0])
    # Zweifarbig (Tom 24.11., „denk dir was aus“): der Halter als kleiner Verstärker – schwarzes Gehäuse, das eingelassene Lochfeld ist die goldene
    # Lautsprecher-Blende. Die Blende ist eine 3 mm starke Scheibe MITTEN in der Wange und greift ringsum 0,6 mm unter den schwarzen Rahmen (Nut):
    # sie hält durch die Form, auch wenn Gold (PLA) und Schwarz (PETG) kaum aneinander haften.
    scheibe = feld.offset(0.6, RUND, 2.0, 16)
    gold_w = (scheibe.offset(-0.02, RUND, 2.0, 16) - loch).extrude(2.96).translate([0, 0, 1.02])
    gold = gold_w.transform(dreh).translate([15.0, 0, 0]) + gold_w.transform(dreh).translate([-20.0, 0, 0]) if a.zwei else None
    # die EINE Querstrebe hinten: Wand zwischen den Wangen mit Spitzbogen (45°, druckt ohne Stützen)
    gipfel = min(12.0, hq - 3.2); bogen = poly((-10.5, -1), (10.5, -1), (10.5, max(1.0, gipfel - 10.5)), (0, gipfel), (-10.5, max(1.0, gipfel - 10.5)))
    strebe = (poly((-16, 0), (16, 0), (16, hq), (-16, hq)) - bogen).extrude(3.2).transform(np.array([[1, 0, 0, 0], [0, 0, 1, 32.0], [0, 1, 0, 0]], float))
    halter = wg(15.0) + wg(-20.0) + strebe
    print(f"Lochfeld: {len(loecher)} Löcher Ø 2,6 → 1,1 je Wange, 1,0 mm vertieft; Querstrebe {hq:.1f} mm hoch mit Spitzbogen bis {gipfel:.1f} mm")
    ziel = Path(a.ziel); ziel.mkdir(parents=True, exist_ok=True)
    me = halter.to_mesh(); t = trimesh.Trimesh(np.asarray(me.vert_properties[:, :3], np.float64), me.tri_verts, process=True); t.export(ziel / "gitarrenhalter190.stl")
    print(f"gitarrenhalter190.stl: dicht={t.is_watertight}, Maße {t.extents.round(1).tolist()} mm, {halter.volume() / 1000:.1f} cm³ (PLA ≈ {halter.volume() * 1.24 / 1000:.0f} g voll)")
    tg = None
    if gold is not None:
        mg = gold.to_mesh(); tg = trimesh.Trimesh(np.asarray(mg.vert_properties[:, :3], np.float64), mg.tri_verts, process=True); tg.export(ziel / "gitarrenhalter190_gold.stl")
        print(f"gitarrenhalter190_gold.stl: dicht={tg.is_watertight}, {gold.volume() / 1000:.2f} cm³, Schnitt mit Schwarz {(gold ^ halter).volume():.3f} mm³"); halter = halter + gold
    # ---- Passung mit beiden Gitarren ----
    G = {"schecter": ("auftraege/2026-11-23_gitarre190_c5pro", ["gitarre190_grau", "gitarre190_rot", "gitarre190_schwarz", "gitarre190_weiss"], 8.74),
         "strat": ("auftraege/2026-11-23_stratocaster190_c5pro", ["strat_korpus", "strat_weiss", "strat_hals", "strat_metall", "strat_schwarz"], 8.15)}
    lage = {}
    for n, (ordner, teile, dick) in G.items():
        ms = {}
        for k in teile:
            pf = HIER / ordner / f"{k}.stl"
            if pf.exists(): ms[k] = trimesh.load(pf, process=True)
        if not ms: print(f"{n}: Dateien fehlen – Passung nicht geprüft"); continue
        v = np.vstack([m.vertices for m in ms.values()]); kz = v[(v[:, 2] < dick + 0.05) & (np.abs(np.abs(v[:, 0]) - 17.5) <= 2.5)]
        y0 = float(kz[:, 1].min())                                                                  # tiefster Korpuspunkt über den Wangen → liegt auf dem Kanalboden
        T = np.array([[1, 0, 0, 0], [0, u[0], f[0], A[0] - y0 * u[0]], [0, u[1], f[1], A[1] - y0 * u[1]], [0, 0, 0, 1]], float)
        lage[n] = (ms, T); schnitt = 0.0
        for k, m in ms.items():
            mm = M(mf.Mesh(np.asarray(m.vertices, np.float32), np.asarray(m.faces, np.uint32)))
            if mm.status() == mf.Error.NoError: schnitt += (mm.transform(T[:3]) ^ halter).volume()
        zmin = float((np.c_[v, np.ones(len(v))] @ T.T)[:, 2].min()); kopf = (np.c_[v, np.ones(len(v))] @ T.T)
        print(f"{n}: steht bei y0 {y0:.2f}, Schnittvolumen mit dem Halter {schnitt:.3f} mm³, tiefster Punkt {zmin:.2f} mm über dem Tisch, "
              f"Kopf bei Tiefe {kopf[:, 1].max():.1f} / Höhe {kopf[:, 2].max():.1f} mm, Luft im Kanal {a.kanal - dick:.2f} mm")
    if a.bild and lage:
        import pyvista as pv
        pv.OFF_SCREEN = True
        FARBE = {"gitarre190_grau": "#8a8d92", "gitarre190_rot": "#6e1423", "gitarre190_schwarz": "#111111", "gitarre190_weiss": "#c9ccd1",
                 "strat_korpus": "#e3d9b6", "strat_weiss": "#f4f4f4", "strat_hals": "#d9b382", "strat_metall": "#b8bcc2", "strat_schwarz": "#111111"}
        pl = pv.Plotter(shape=(1, 3), window_size=(2400, 1300))
        def szene(dx_liste, mit=True):
            for dx, n in dx_liste:
                pl.add_mesh(pv.wrap(t.copy().apply_translation([dx, 0, 0])), color="#1c1c1e", smooth_shading=False)
                if tg is not None: pl.add_mesh(pv.wrap(tg.copy().apply_translation([dx, 0, 0])), color="#c9a227", smooth_shading=False)
                if mit and n in lage:
                    for k, m in lage[n][0].items():
                        c = m.copy(); c.apply_transform(lage[n][1]); c.apply_translation([dx, 0, 0]); pl.add_mesh(pv.wrap(c), color=FARBE.get(k, "#999999"), smooth_shading=False)
        paar = [(-40, "schecter"), (40, "strat")]
        pl.subplot(0, 0); szene(paar); pl.camera.position = (-190, -420, 190); pl.camera.focal_point = (0, 15, 88); pl.camera.up = (0, 0, 1); pl.camera.view_angle = 24; pl.add_text("beide Gitarren im Halter", font_size=12, color="black")
        pl.subplot(0, 1); szene([(0, "schecter")]); pl.camera.position = (420, 15, 90); pl.camera.focal_point = (0, 15, 88); pl.camera.up = (0, 0, 1); pl.camera.view_angle = 26; pl.add_text("von der Seite (12° Neigung)", font_size=12, color="black")
        pl.subplot(0, 2); pl.add_mesh(pv.wrap(t), color="#26262a", smooth_shading=False); tg is not None and pl.add_mesh(pv.wrap(tg), color="#c9a227", smooth_shading=False); pl.camera.position = (150, -190, 130); pl.camera.focal_point = (0, 15, 28); pl.camera.up = (0, 0, 1); pl.camera.view_angle = 26; pl.add_text("Halter allein", font_size=12, color="black")
        pl.screenshot(a.bild); print("Bild:", a.bild)


if __name__ == "__main__":
    main()
