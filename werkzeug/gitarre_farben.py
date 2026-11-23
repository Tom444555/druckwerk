"""Toms Stratocaster-STL (ein Körper, Originalgröße) in 4 Farbteile schneiden und verkleinern.
Teile: korpus (creme), weiss (Schlagbrett, Pickups, Regler), hals (Ahorn), metall (Brücke, Bünde, Saiten, Mechaniken, Buchse).
Saiten werden als druckbare Stege (bis auf die Oberfläche) neu aufgebaut, weil sie verkleinert sonst zu dünn sind.
Aufruf: python3 gitarre_farben.py <original.stl> <ziel_ordner> <laenge_mm> [--schnur 1]
--schnur 1 (23.11.2026, Vorbild Schecter `gitarre_rundum.py --wirbel 1`, Klein-Modus): keine festen Saiten, sondern Schnur bis ~0,3 mm einfädeln –
Saiten aus dem Netz entfernt, Kerben in Sattel und Reiter-Kuppen, sechs Löcher durch den Korpus (string-through, Senkung hinten),
Kegellöcher statt Mechanik-Achsen und strat_wirbel.stl / strat_wirbel_platte.stl mit sechs Steckwirbeln (Kopf 4). Alle Feinheiten im Druckmaß."""
import sys, math, argparse, numpy as np, trimesh, manifold3d as mf
_ap = argparse.ArgumentParser(); _ap.add_argument('src'); _ap.add_argument('dst'); _ap.add_argument('laenge', type=float)
_ap.add_argument('--schnur', type=int, default=0, help='1 = Schnur-Saiten mit Steckwirbeln statt fester Saiten-Stege')
A = _ap.parse_args(); src, dst, laenge = A.src, A.dst, A.laenge
t = trimesh.load(src)
M = mf.Manifold(mf.Mesh(vert_properties=np.asarray(t.vertices, np.float32), tri_verts=np.asarray(t.faces, np.uint32)))
assert M.status() == mf.Error.NoError, M.status()
s = laenge / t.extents[1]
G = 3000.0
def box(x0, x1, y0, y1, z0, z1): return mf.Manifold.cube([x1-x0, y1-y0, z1-z0]).translate([x0, y0, z0])
def ellipse(cx, cy, a, b, winkel, z0, z1):
    return mf.Manifold.cylinder(z1-z0, 1, 1, 64).scale([a, b, 1]).rotate([0, 0, winkel]).translate([cx, cy, z0])
# Rippenbogen (Bauchausschnitt) auf der Rückseite, Bass-Seite an der Taille: flache Mulde, am Rand ca. 11 mm tief
M = M - mf.Manifold.sphere(1, 96).scale([48, 85, 11.5]).translate([-70, -850, 0])
# Armauflage vorne: Decke am unteren Bass-Bogen weich abgerundet (Kreisbogen, tangential an die Decke,
# 95 mm breit, am Rand 19 mm tiefer) – keine Kante
_W, _D = 95.0, 19.0; _R = (_W*_W + _D*_D) / (2*_D)
_w = np.radians(25); _u = np.array([-np.cos(_w), -np.sin(_w)]); _v = np.array([_u[1], -_u[0]]); _P = np.array([-105.0, -1060.0])
_t = np.linspace(0, 2*np.pi, 721)[:-1]
_kreis = mf.CrossSection([np.c_[-_W + _R*np.cos(_t), 44.0 - _R + _R*np.sin(_t)]])
_recht = mf.CrossSection([np.array([[-_W, -20.0], [120, -20.0], [120, 120], [-_W, 120]])])
_keil = mf.Manifold.extrude(_recht - _kreis, 800).translate([0, 0, -400])
_keil = _keil.transform(np.array([[_u[0], 0, _v[0], _P[0]], [_u[1], 0, _v[1], _P[1]], [0, 1, 0, 0]]))
M = M - _keil
# Halsrücken rund (C-Profil): halbe Ellipse unter dem Griffbrett, weiche Übergänge zu Halsfuß und Kopfplatte
_xc, _a, _zo, _zu = 51.8, 26.6, 41.0, 17.1
def _ell(y, n=48): return [[_xc + _a*np.cos(t), y, _zo - (_zo-_zu)*np.sin(t)] for t in np.linspace(0, np.pi, n)]
def _eck(y): return [[_xc-_a-1, y, _zo], [_xc+_a+1, y, _zo], [_xc-_a-1, y, _zu-1], [_xc+_a+1, y, _zu-1]]
_y = [-692.0, -662.0, -348.0, -316.0]
_kern = (mf.Manifold.hull_points(np.array(_eck(_y[0]) + _ell(_y[1]))) + mf.Manifold.hull_points(np.array(_ell(_y[1]) + _ell(_y[2])))
         + mf.Manifold.hull_points(np.array(_ell(_y[2]) + _eck(_y[3]))))
M = M - (mf.Manifold.cube([2*_a+2, _y[3]-_y[0], _zo-_zu+1]).translate([_xc-_a-1, _y[0], _zu-1]) - _kern)
ZK, ZP = 44.02, 45.65              # Korpus-Oberseite, Schlagbrett-Oberseite
NX0, NX1 = 23.5, 80.5              # Halsband in X
Y_HEEL, Y_PG, Y_FB, Y_NUT, Y_KOPF = -733, -770, -806, -322, -300
# --- Saiten: Lage aus dem Netz messen (Punkte oberhalb 50,6) ---
p, _ = trimesh.sample.sample_surface(t, 3000000)
def saiten_x(y):
    q = p[(np.abs(p[:, 1]-y) < 4) & (p[:, 2] > 50.6) & (p[:, 0] > NX0) & (p[:, 0] < NX1), 0]
    q = np.sort(q); gr = np.split(q, np.where(np.diff(q) > 3)[0]+1)
    return [float(g.mean()) for g in gr if len(g) > 20]
ya, yb = -790.0, -390.0; xa, xb = saiten_x(ya), saiten_x(yb)
assert len(xa) == 6 and len(xb) == 6, (xa, xb)
if A.schnur:
    # ================= Schnur-Saiten (alles in Originalmaß, Feinheiten als Druckmaß p(mm)) =================
    p = lambda mm: mm / s
    X_LOCH, Y_LOCH = [26.64, 37.1, 47.6, 58.09, 68.56, 79.02], -1003.04          # vorhandene Saitenkanäle unter den Reitern (gemessen)
    POSTS = [(30.8, -292.1), (39.6, -261.4), (48.5, -230.6), (57.3, -199.8), (66.2, -169.1), (75.1, -138.4)]   # Mechanik-Achsen
    Z_HB, Z_KT = 10.28, 38.05                                                     # Unterseite Mechanik-Gehäuse, Kopfplatten-Oberseite
    # Federfach unter der Brücke (Hohlraum 0–8 mm hinter dem Deckel) füllen, damit die Saitenlöcher volle Wände haben; Zwinge-Leiste hinten bleibt offen
    M = M + (box(7.5, 99.5, -1027.5, -982.5, -0.5, 8.4) - box(-G, G, -1007.2, -998.8, -G, 1.25))
    fx = lambda i, y: xa[i] + (xb[i] - xa[i]) * (y - ya) / (yb - ya)
    KB, Z_K = p(0.40), 49.85                       # Kerbe 0,40 breit (Druck), Grund 49,85 = Unterkante der alten Saiten (~0,18 mm tief im Druck)
    weg = [box(20, 85, -985.9, -323.6, Z_K, G),     # Saiten über Korpus und Griffbrett (Bünde 49,4, Sattel/Reiter bleiben)
           box(20, 85, -319.3, Y_KOPF, 40.0, G),     # Saiten zwischen Sattel und Kopfplatte
           box(-G, G, Y_KOPF, G, Z_KT, G)]           # Kopfplatte: Saiten, Mechanik-Achsen mit Muttern, Saitenniederhalter
    for i in range(6):
        for y0, y1 in ((-992.0, -985.5), (-324.6, -318.6)):                                    # Kerbe in der Reiter-Kuppe, Kerbe im Sattel
            xm = fx(i, (y0 + y1) / 2); weg.append(box(xm - KB / 2, xm + KB / 2, y0, y1, Z_K, G))
        weg.append(box(X_LOCH[i] - 1.7, X_LOCH[i] + 1.7, -1004.8, -991.2, 45.65, G))             # Langloch im Reiter: schräges Saitenstück weg
    M = M - mf.Manifold.batch_boolean(weg, mf.OpType.Add)
    # Löcher durch den Korpus: Ø 0,72 im Druck, hinten Senkung Ø 1,22 × 0,30 (Grund der Zwingen-Leiste bei z 1,2)
    RL, RS, TS, Z_HINTEN = p(0.36), p(0.61), p(0.30), 1.2
    bohr = []
    for x in X_LOCH:
        bohr += [mf.Manifold.cylinder(80, RL, RL, 24).translate([x, Y_LOCH, -15]),
                 mf.Manifold.cylinder(15 + Z_HINTEN, RS, RS, 32).translate([x, Y_LOCH, -15]),
                 mf.Manifold.cylinder(TS, RS, RL, 32).translate([x, Y_LOCH, Z_HINTEN - 0.001])]
    # Kegellöcher wie Schecter Klein-Modus (Druckmaß): Gehäuse-Rand ab Achse ≥ 9 mm echt → GH; Kegel hinten WR_H, vorn WR_V
    GH = 9.0 * s; WR_H = min(1.35, GH - 0.45); KLEIN = WR_H < 1.35; WR_V = WR_H - 0.25 if KLEIN else 1.05
    RING_R, RING_H = WR_V + 0.40, 0.20                                            # Hülse (silber) um das Loch auf der Kopfplatte
    H_LOCH = (Z_KT + p(RING_H) - Z_HB) * s; lang = H_LOCH + 0.3; steig = (WR_H - WR_V) / lang
    ringe = []
    for (x, y) in POSTS:
        ringe.append(mf.Manifold.cylinder(p(RING_H) + 0.05, p(RING_R), p(RING_R - 0.08), 48).translate([x, y, Z_KT - 0.05]))
        bohr.append(mf.Manifold.cylinder(p(lang + 2), p(WR_H + steig), p(WR_V - steig), 48).translate([x, y, Z_HB - p(1)]))
    M = M + mf.Manifold.batch_boolean(ringe, mf.OpType.Add) - mf.Manifold.batch_boolean(bohr, mf.OpType.Add)
    saiten = mf.Manifold()
    print(f'Schnur: Kegel hinten Ø {2*WR_H:.2f} → vorn Ø {2*WR_V:.2f}, Lochlänge {H_LOCH:.2f} mm, Klein={KLEIN}; Korpus-Löcher Ø {2*RL*s:.2f}, Senkung Ø {2*RS*s:.2f}')
breiten = [0.6, 0.55, 0.5, 0.42, 0.36, 0.3]   # Stegbreite je Saite im fertigen Modell (mm): E A D dick, g h e dünn
if not A.schnur: saiten = mf.Manifold()
y_s0, y_s1 = -996.0, Y_NUT
for x0, x1, br in ([] if A.schnur else zip(xa, xb, breiten)):
    bs = br / s
    f = lambda y: x0 + (x1-x0)*(y-ya)/(yb-ya)
    ecken = np.array([[f(y_s0)-bs/2, y_s0], [f(y_s0)+bs/2, y_s0], [f(y_s1)+bs/2, y_s1], [f(y_s1)-bs/2, y_s1]])
    st = mf.Manifold.extrude(mf.CrossSection([ecken]), 51.7-43.5).translate([0, 0, 43.5])
    saiten += st
if not A.schnur: saiten = saiten - box(NX0, NX1, Y_HEEL, y_s1+1, 0, 47.0)     # am freien Hals nur bis ins Griffbrett
# --- Metall ---
metall_zone = (box(NX0, NX1, Y_FB, Y_KOPF, 48.03, G)                 # Bünde, Sattel, Saiten über dem Griffbrett
               + box(-G, G, Y_KOPF, G, 38.05, G) + box(-G, G, Y_KOPF, G, -G, 16.95)   # Mechaniken oben/unten
               + box(26, 78, -1000, Y_FB, 49.0, G)                   # Saiten über dem Korpus
               + box(14, 91.5, -1021.5, -975.5, ZK, G) + box(91.5, 101.5, -1021.5, -1003, ZK, G)   # Brücke
               + ellipse(144.5, -1044, 39, 21, -33.7, ZK, 60) + ellipse(146, -1050, 19, 8.5, -33.7, 30, 60))  # Buchse
metall = (M ^ metall_zone) + saiten
# --- Hals (Ahorn) ---
hals_zone = (box(NX0, NX1, Y_HEEL, G, -G, G) + box(-G, G, Y_KOPF-30, G, -G, G)
             + box(NX0, NX1, Y_PG, Y_HEEL, ZK, G) + box(NX0, NX1, Y_FB, Y_PG, ZP, G))
hals = (M ^ hals_zone) - metall
# --- Weiß: alles über der Korpus-Oberseite ---
weiss = (M ^ box(-G, G, -G, Y_HEEL, ZK, G)) - metall - hals
korpus = M - metall - hals - weiss
z0 = t.bounds[0][2]; c = [-(t.bounds[0][0]+t.bounds[1][0])/2, -t.bounds[0][1], -z0]
fertig = {}
for n, m in (('korpus', korpus), ('weiss', weiss), ('hals', hals), ('metall', metall)):
    m = m.translate(c).scale([s, s, s])
    grenze = 3.0 if n in ('korpus', 'hals') else 0.02          # Schnitt-Splitter und lose Innenteile entfernen (mm³)
    teile = [k for k in m.decompose() if k.volume() > grenze]
    m = mf.Manifold.compose(teile); r = m.to_mesh(); fertig[n] = m
    o = trimesh.Trimesh(r.vert_properties[:, :3], r.tri_verts); o.export(f'{dst}/strat_{n}.stl')
    print(n, len(o.faces), 'Flächen', o.extents.round(1).tolist(), 'Vol', round(m.volume(), 1))
print('Maßstab', round(s, 4))
if A.schnur:
    # ================= Steckwirbel (Druckmaß, stehend: Rändelrad unten, Stift oben) – Formeln aus gitarre_rundum.py =================
    D = lambda P: np.array([(P[0] + c[0]) * s, (P[1] + c[1]) * s])
    zhb = (Z_HB + c[2]) * s; mech = [D(P) for P in POSTS]
    ABST = min(np.linalg.norm(mech[i + 1] - mech[i]) for i in range(5))
    r0 = WR_H + 0.05 + steig * 0.6                                                  # 0,05 Übermaß: sitzt fest, bevor das Rad anliegt
    RR = min(3.2, ABST - r0 - 0.2) if KLEIN else 3.2
    KH = max(2.6, 13.0 * s) if KLEIN else 5.0; QL = 0.25 if KLEIN else 0.38
    TIEF = 2.8 if 2 * RR + 0.3 > ABST else 0.0                                      # Räder auf zwei Ebenen, wenn sie sich sonst berühren
    rk = WR_V - 0.07
    def wirbel_bau(tief):
        zahn = np.array([[(RR - (0.28 if j % 2 else 0)) * math.cos(j * math.pi / 30), (RR - (0.28 if j % 2 else 0)) * math.sin(j * math.pi / 30)] for j in range(60)])
        rad = mf.CrossSection([zahn]).extrude(2.6) + mf.Manifold.cylinder(0.5, min(2.6, RR - 0.3), r0 + 0.25, 40).translate([0, 0, 2.59])
        zv = 3.08 + tief
        stift = mf.Manifold.cylinder(lang + 1.2, r0, r0 - steig * (lang + 1.2), 40).translate([0, 0, zv])
        if tief: stift = stift + mf.Manifold.cylinder(tief + 0.02, r0, r0, 40).translate([0, 0, 3.08])
        zs0 = zv + lang + 1.2
        kopf_w = mf.Manifold.cylinder(KH, rk, rk, 40).translate([0, 0, zs0 - 0.02]) + mf.Manifold.cylinder(0.3, rk, rk - 0.25, 40).translate([0, 0, zs0 + KH - 0.03])
        w = rad + stift + kopf_w - mf.Manifold.cylinder(6, QL, QL, 16).rotate([90, 0, 0]).translate([0, 3, zs0 + KH * 0.6])
        return w, zhb - zv - (r0 - WR_H) / steig                                    # Wirbel und Höhe seines Fußes im eingesteckten Zustand
    wa, wb = wirbel_bau(0.0), wirbel_bau(TIEF)
    def export(m, name):
        r = m.to_mesh(); o = trimesh.Trimesh(np.asarray(r.vert_properties[:, :3], np.float64), r.tri_verts, process=True)
        o.export(f'{dst}/{name}.stl'); return o
    sp = max(9.0, 2 * RR + 2.0)
    raster = [(wa, wb)[j % 2][0].translate([sp * (j % 3), sp * (j // 3), 0]) for j in range(6)]
    tw = export(mf.Manifold.batch_boolean(raster, mf.OpType.Add), 'strat_wirbel')
    bb = mf.Manifold.batch_boolean(list(fertig.values()), mf.OpType.Add).bounding_box()
    x0p = bb[3] + 6 + RR; y0p = bb[1] + 6 + RR
    tp = export(mf.Manifold.batch_boolean([m.translate([x0p, y0p, 0]) for m in raster], mf.OpType.Add), 'strat_wirbel_platte')
    print(f'strat_wirbel.stl: dicht={tw.is_watertight}, 6 Wirbel, Rad Ø {2*RR:.1f}, Stufe {TIEF} mm, Höhe {tw.extents[2]:.1f}, Kegel Ø {2*r0:.2f} → {2*(r0 - steig*(lang+1.2)):.2f}, '
          f'Stift Ø {2*rk:.2f} × {KH:.1f}, Querloch Ø {2*QL:.2f}, Mechanik-Abstand {ABST:.2f}')
    print(f'Platte: Gitarre x {bb[0]:.1f}…{bb[3]:.1f}, y {bb[1]:.1f}…{bb[4]:.1f}; mit Wirbeln x {bb[0]:.1f}…{tp.bounds[1][0]:.1f}, y {min(bb[1], tp.bounds[0][1]):.1f}…{max(bb[4], tp.bounds[1][1]):.1f}')
    # Prüfung: Schnittvolumen Farben untereinander und mit eingesteckten Wirbeln
    nm = list(fertig)
    for i in range(len(nm)):
        for j in range(i + 1, len(nm)): print(f'  Schnitt {nm[i]}/{nm[j]}: {(fertig[nm[i]] ^ fertig[nm[j]]).volume():.3f} mm³')
    steck = [(wa, wb)[j % 2][0].translate([mech[j][0], mech[j][1], (wa, wb)[j % 2][1]]) for j in range(6)]
    for n_, m_ in fertig.items(): print(f'  Schnitt Wirbel/{n_}: {(mf.Manifold.batch_boolean(steck, mf.OpType.Add) ^ m_).volume():.3f} mm³')
    print(f'  Schnitt Wirbel untereinander: {sum((steck[i] ^ steck[j]).volume() for i in range(6) for j in range(i + 1, 6)):.3f} mm³')
    print(f'  Wirbel-Unterkante eingesteckt: {min((wa, wb)[j % 2][1] for j in range(6)):.2f} / {(wb[1]):.2f} mm (Bett = 0)')
    export(mf.Manifold.batch_boolean(steck, mf.OpType.Add), '_wirbel_steckend')
