#!/usr/bin/env python3
"""gitarrenhalter190.py – Ständer für Toms 190-mm-Gitarren (Schecter und Stratocaster), Entwurf 24.11.2026. Nur gerechnet.

  python3 modelle/gitarrenhalter190.py --ziel /tmp/h [--bild /tmp/h/v.png] [--winkel 12] [--kanal 9.4]

Idee: zwei Wangen (je 5 mm) im Abstand von 30 mm auf einer Grundplatte. Die Gitarre steht mit der Korpus-Unterkante in einem Kanal
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
    ap.add_argument("--winkel", type=float, default=12.0, help="Neigung der Gitarre nach hinten (Grad)")
    ap.add_argument("--kanal", type=float, default=9.4, help="lichte Weite des Kanals (dickster Korpus 8,74 + Luft)")
    ap.add_argument("--lehne", type=float, default=66.0, help="Länge der Lehne ab Kanalboden")
    a = ap.parse_args()
    w = math.radians(a.winkel); u = np.array([math.sin(w), math.cos(w)]); f = np.array([-math.cos(w), math.sin(w)])   # (Tiefe, Höhe): u = an der Lehne hoch, f = nach vorn
    A = np.array([0.0, 7.5]); B = A + a.kanal * f; B3 = B + 3.2 * f; Ar = A - 4.5 * f; LIP = 5.5; YR = 50.0; FUSS = 3.2
    P = lambda *q: CS([np.array([list(map(float, x)) for x in q])], mf.FillRule.Positive)
    def poly(*q):
        c = P(*q)
        return c if c.area() > 0 else P(*q[::-1])
    oben = Ar + (a.lehne - 6) * u
    bez = [((1 - t) ** 2) * oben + 2 * (1 - t) * t * np.array([Ar[0] + 7.0, 13.0]) + t * t * np.array([YR, FUSS]) for t in np.linspace(0, 1, 40)]   # geschwungene Rückenlinie
    wange = (poly((B3[0] - 7, 0), (YR, 0), (YR, FUSS), (B3[0] - 7, FUSS))                       # Fuß
             + poly((B3[0], 0), (Ar[0], 0), Ar, A, B, B3)                                           # Block unter dem Kanal
             + poly(A, A + a.lehne * u, Ar + a.lehne * u, Ar)                                       # Lehne
             + poly(B, B + LIP * u, B3 + LIP * u, B3)                                               # Lippe vorn
             + poly(Ar, *bez, (YR, 0), (Ar[0], 0)))                                                 # Rückenflosse
    kanal = poly(A + 0.02 * u, A + 40 * u, B + 40 * u, B + 0.02 * u)                               # Kanal bleibt frei (Rundung darf ihn nicht zusetzen)
    wange = wange.offset(-0.8, RUND, 2.0, 32).offset(0.8, RUND, 2.0, 32) - kanal.offset(-0.01)
    dreh = np.array([[0, 0, 1, 0], [1, 0, 0, 0], [0, 1, 0, 0]], float)                              # (Tiefe, Höhe, Dicke) → (X, Tiefe, Höhe)
    def wg(x0): return wange.extrude(5.0).transform(dreh).translate([x0, 0, 0])
    yF = B3[0] - 7
    platte = CS.square([52 - 16, YR - yF + 4 - 16]).translate([-18, yF - 2 + 8]).offset(8, RUND, 2.0, 48).extrude(FUSS)
    hq = float(np.interp(31.5, [q[0] for q in bez], [q[1] for q in bez])) - 0.6
    steg = M.cube([40, 3.0, hq]).translate([-20, 30, 0])                                            # Querwand hinten: verbindet die Wangen
    halter = platte + wg(15.0) + wg(-20.0) + steg
    ziel = Path(a.ziel); ziel.mkdir(parents=True, exist_ok=True)
    me = halter.to_mesh(); t = trimesh.Trimesh(np.asarray(me.vert_properties[:, :3], np.float64), me.tri_verts, process=True); t.export(ziel / "gitarrenhalter190.stl")
    print(f"gitarrenhalter190.stl: dicht={t.is_watertight}, Maße {t.extents.round(1).tolist()} mm, {halter.volume() / 1000:.1f} cm³ (PLA ≈ {halter.volume() * 1.24 / 1000:.0f} g voll)")
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
        print(f"{n}: steht bei y0 {y0:.2f}, Schnittvolumen mit dem Halter {schnitt:.3f} mm³, tiefster Punkt {zmin:.2f} mm über dem Tisch (Platte {FUSS}), "
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
                if mit and n in lage:
                    for k, m in lage[n][0].items():
                        c = m.copy(); c.apply_transform(lage[n][1]); c.apply_translation([dx, 0, 0]); pl.add_mesh(pv.wrap(c), color=FARBE.get(k, "#999999"), smooth_shading=False)
        paar = [(-40, "schecter"), (40, "strat")]
        pl.subplot(0, 0); szene(paar); pl.camera.position = (-190, -420, 190); pl.camera.focal_point = (0, 15, 88); pl.camera.up = (0, 0, 1); pl.camera.view_angle = 24; pl.add_text("beide Gitarren im Halter", font_size=12, color="black")
        pl.subplot(0, 1); szene([(0, "schecter")]); pl.camera.position = (420, 15, 90); pl.camera.focal_point = (0, 15, 88); pl.camera.up = (0, 0, 1); pl.camera.view_angle = 26; pl.add_text("von der Seite (12° Neigung)", font_size=12, color="black")
        pl.subplot(0, 2); pl.add_mesh(pv.wrap(t), color="#6b6f76", smooth_shading=False); pl.camera.position = (150, -190, 130); pl.camera.focal_point = (0, 15, 28); pl.camera.up = (0, 0, 1); pl.camera.view_angle = 26; pl.add_text("Halter allein", font_size=12, color="black")
        pl.screenshot(a.bild); print("Bild:", a.bild)


if __name__ == "__main__":
    main()
