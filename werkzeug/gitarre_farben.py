"""Toms Stratocaster-STL (ein Körper, Originalgröße) in 4 Farbteile schneiden und verkleinern.
Teile: korpus (creme), weiss (Schlagbrett, Pickups, Regler), hals (Ahorn), metall (Brücke, Bünde, Saiten, Mechaniken, Buchse).
Saiten werden als druckbare Stege (bis auf die Oberfläche) neu aufgebaut, weil sie verkleinert sonst zu dünn sind.
Aufruf: python3 gitarre_farben.py <original.stl> <ziel_ordner> <laenge_mm> [--schnur 1]
--schnur 1 (23.11.2026, Vorbild Schecter `gitarre_rundum.py --wirbel 1`, Klein-Modus): keine festen Saiten, sondern Schnur bis ~0,3 mm einfädeln –
Saiten aus dem Netz entfernt, Kerben in Sattel und Reiter-Kuppen, sechs Löcher durch den Korpus (string-through, Senkung hinten),
Kegellöcher statt Mechanik-Achsen und strat_wirbel.stl / strat_wirbel_platte.stl mit sechs Steckwirbeln (Kopf 4). Alle Feinheiten im Druckmaß.
--details 1 (23.11.2026 abends, nach Toms 18 Fotos seiner eigenen Strat; nur zusammen mit --schnur 1): fünftes Farbteil strat_schwarz.stl
(Griffbrett-Punkte, Tonabnehmer-Pole, schwarze Mittellage des Schlagbretts als Linie am Rand – liegt komplett ÜBER der Korpusdecke, deshalb
auf Kopf 1 mit Spulenwechsel creme → schwarz druckbar), 22. Bund mit Griffbrett-Überstand, Sattel weiß, alle Schrauben und Gurtknöpfe silber,
Zwei-Punkt-Tremolo (zwei Bolzen statt sechs Schrauben), zwei Saitenniederhalter, Halsstab-Tropfen als Vertiefung, Rückseite plan aufs Bett:
Federfach-Deckel weiß und Halsplatte silber als bündige Einlagen (vorher standen sie 0,3 mm vor und der Korpus schwebte)."""
import sys, math, argparse, numpy as np, trimesh, manifold3d as mf
_ap = argparse.ArgumentParser(); _ap.add_argument('src'); _ap.add_argument('dst'); _ap.add_argument('laenge', type=float)
_ap.add_argument('--schnur', type=int, default=0, help='1 = Schnur-Saiten mit Steckwirbeln statt fester Saiten-Stege')
_ap.add_argument('--details', type=int, default=0, help='1 = Details nach Toms Fotos (5. Farbe schwarz, 22. Bund, Schrauben silber, Rückseite plan …)')
A = _ap.parse_args(); src, dst, laenge = A.src, A.dst, A.laenge
assert not A.details or A.schnur, '--details braucht --schnur 1'
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
        bohr += [mf.Manifold.cylinder(80, RL, RL, 24).translate([x, Y_LOCH, -15])]
    # Hinten wie bei der Schecter mit Lochkugeln als Saitenanker (Tom, 23.11.): eine Rinne über allen sechs Löchern,
    # in der sechs Kugeln Ø 1,8 × 1,5 (Loch 0,5) nebeneinander bündig liegen – Lochabstand nur ~1,94 mm, deshalb Rinne statt Einzelsenkungen
    KUG_D, KUG_H, RIN_B, RIN_T = 1.8, 1.5, 2.0, 1.6                      # Druckmaß
    rin = mf.CrossSection.square([X_LOCH[5] - X_LOCH[0] + p(RIN_B), p(RIN_B)]).translate([X_LOCH[0] - p(RIN_B) / 2, Y_LOCH - p(RIN_B) / 2])
    rin = rin.offset(-p(RIN_B) / 2 + 0.01, mf.JoinType.Round, 2.0, 48).offset(p(RIN_B) / 2 - 0.01, mf.JoinType.Round, 2.0, 48)
    bohr += [rin.extrude(15 + Z_HINTEN + p(RIN_T)).translate([0, 0, -15])]
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
    print(f'Schnur: Kegel hinten Ø {2*WR_H:.2f} → vorn Ø {2*WR_V:.2f}, Lochlänge {H_LOCH:.2f} mm, Klein={KLEIN}; Korpus-Löcher Ø {2*RL*s:.2f}, hinten Rinne {RIN_B} × {RIN_T} tief für Lochkugeln Ø {KUG_D} × {KUG_H}')
if A.details:
    # ================= Details nach Toms Fotos (Originalmaß, Feinheiten als Druckmaß p(mm)) =================
    def rrect(x0, x1, y0, y1, r): return mf.CrossSection.square([x1 - x0 - 2 * r, y1 - y0 - 2 * r]).translate([x0 + r, y0 + r]).offset(r, mf.JoinType.Round, 2.0, 48)
    def zyl(x, y, r, z0, z1, n=40): return mf.Manifold.cylinder(z1 - z0, r, r, n).translate([x, y, z0])
    # Rückseite plan: alles unter der Korpus-Rückseite (z 0) weg; Deckel und Halsplatte als 1,6 dicke Platte bündig wieder einsetzen (Farbe weiter unten)
    DECKEL = rrect(3.0, 102.0, -1030.5, -874.0, 8.0); HPLATTE = rrect(31.0, 71.0, -778.5, -738.5, 5.0)
    SCHLITZ = box(20, 86, Y_LOCH - p(1.0) - 0.2, Y_LOCH + p(1.0) + 0.2, -G, G)       # Rinne der Lochkugeln bleibt offen
    M = (M - box(-G, G, -G, G, -G, 0.0)) + (DECKEL.extrude(1.6) - SCHLITZ) + HPLATTE.extrude(1.6)
    M = M - zyl(51.0, -771.5, p(0.42), -1, p(0.32)) - mf.Manifold.batch_boolean([zyl(x, y, p(0.36), -1, p(0.24), 4) for x in (36.0, 66.0) for y in (-773.6, -743.5)], mf.OpType.Add)   # … und vier Schrauben als Vierkant-Vertiefung
    #                              # Loch der Halswinkel-Verstellung in der Halsplatte
    # Zwei-Punkt-Tremolo: die vier inneren Schrauben weg, außen zwei Bolzen
    BOLZ = [26.5, 78.5]; M = M - mf.Manifold.batch_boolean([zyl(x, -982.8, 3.7, 45.62, 60) for x in (36.5, 47.0, 57.5, 68.0)], mf.OpType.Add)
    M = M + mf.Manifold.batch_boolean([zyl(x, -982.8, 3.9, 45.5, 47.6) + zyl(x, -982.8, 2.6, 47.5, 47.6 + p(0.12)) for x in BOLZ], mf.OpType.Add)
    # 22. Bund auf Griffbrett-Überstand (Toms Hals hat 22 Bünde, das Netz 21)
    Y22, Y_UE = -806.8, -813.4
    ue = mf.CrossSection([np.array([[24.6, -799.0], [80.3, -799.0], [80.3, Y_UE + 3], [77.3, Y_UE], [27.6, Y_UE], [24.6, Y_UE + 3]])[::-1]])
    M = M + ue.extrude(48.0 - ZP + 0.3).translate([0, 0, ZP - 0.3])
    M = M + (mf.Manifold.cylinder(55.0, 1.0, 1.0, 24).scale([1.4, 1, 1]).rotate([0, 90, 0]).translate([24.9, Y22, 48.0]) - box(-G, G, -G, G, -G, 47.5))
    # Saitenniederhalter (Optik, die Schnur läuft daneben/darunter): Fuß + nach oben breiter werdender Steg (45°, druckt ohne Stütze)
    def baum(i, j, y):
        P = lambda k: fx(k, -321.6) + (POSTS[k][0] - fx(k, -321.6)) * (y + 321.6) / (POSTS[k][1] + 321.6)
        xm = (P(i) + P(j)) / 2; a, b, z = p(0.42), p(1.35), Z_KT
        e = lambda hx, hy, zz: [[xm - hx, y - hy, zz], [xm + hx, y - hy, zz], [xm + hx, y + hy, zz], [xm - hx, y + hy, zz]]
        return mf.Manifold.hull_points(np.array(e(a, a, z - 0.5) + e(a, a, z + p(0.30)) + e(b, a, z + p(1.0)) + e(b, a, z + p(1.2))))
    M = M + baum(4, 5, -243.0) + baum(2, 3, -276.0)
    # Halsstab-Tropfen hinter dem Sattel: 0,25 mm vertieft (dunkel geht hier nicht – liegt unter der Korpusdecke), in der Mitte das Loch
    tr = mf.CrossSection.batch_hull([mf.CrossSection.circle(3.6, 48).translate([52.0, -301.5]), mf.CrossSection.circle(0.9, 24).translate([52.0, -314.0])])
    st = M ^ tr.extrude(40).translate([0, 0, 30])
    M = (M - tr.extrude(40).translate([0, 0, 30.5])) + st.translate([0, 0, -p(0.25)]) - zyl(52.0, -303.5, p(0.38), Z_KT - p(0.8), 60, 24)
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
_YF = Y_FB - (8.5 if A.details else 0)
metall_zone = (box(NX0, NX1, _YF, Y_KOPF, 48.03, G)                 # Bünde, Sattel, Saiten über dem Griffbrett
               + box(-G, G, Y_KOPF, G, 38.05, G) + box(-G, G, Y_KOPF, G, -G, 16.95)   # Mechaniken oben/unten
               + box(26, 78, -1000, Y_FB, 49.0, G)                   # Saiten über dem Korpus
               + box(14, 91.5, -1021.5, -975.5, ZK, G) + box(91.5, 101.5, -1021.5, -1003, ZK, G)   # Brücke
               + ellipse(144.5, -1044, 39, 21, -33.7, ZK, 60) + ellipse(146, -1050, 19, 8.5, -33.7, 30, 60))  # Buchse
metall = (M ^ metall_zone) + saiten
# --- Hals (Ahorn) ---
hals_zone = (box(NX0, NX1, Y_HEEL, G, -G, G) + box(-G, G, Y_KOPF-30, G, -G, G)
             + box(NX0, NX1, Y_PG, Y_HEEL, ZK, G) + box(NX0, NX1, _YF, Y_PG, ZP, G))
hals = (M ^ hals_zone) - metall
# --- Weiß: alles über der Korpus-Oberseite ---
weiss = (M ^ box(-G, G, -G, Y_HEEL, ZK, G)) - metall - hals
korpus = M - metall - hals - weiss
F = {'korpus': korpus, 'weiss': weiss, 'hals': hals, 'metall': metall}
if A.details:
    F['schwarz'] = mf.Manifold()
    def farbe(zone, ziel, von=None):
        for n in list(F):
            if n == ziel or (von and n not in von): continue
            st = F[n] ^ zone
            if st.volume() > 1e-6: F[n] = F[n] - zone; F[ziel] = F[ziel] + st
    add = lambda L: mf.Manifold.batch_boolean(L, mf.OpType.Add)
    farbe(box(-G, G, -G, Y_HEEL, ZK + 0.02, G), 'weiss', ['korpus'])                                    # Korpus-Reste über der Decke (Schalter-Innenleben)
    farbe(box(-G, G, Y_HEEL, G, ZK + 0.02, G), 'hals', ['korpus'])                                      # Splitter an der Halstasche
    SCHR = [(96.8, -984.7), (2.0, -983.3), (179.0, -967.1), (89.7, -954.8), (162.7, -949.3), (13.7, -940.7), (-14.8, -931.3), (134.9, -918.8), (155.3, -916.3),
            (90.5, -891.5), (12.6, -890.7), (1.3, -881.0), (13.2, -831.2), (90.5, -830.6), (163.1, -821.7), (86.3, -811.2), (5.8, -779.3), (169.5, -762.2), (189.0, -1022.8)]
    farbe(add([zyl(x, y, 3.9, ZP + 0.03, 47.2) for x, y in SCHR]), 'metall', ['weiss'])                 # 11 Schlagbrett-, 6 Tonabnehmer-, 2 Schalter-Schrauben
    pol = F['weiss'].slice((ZK + ZP) / 2).to_polygons()
    fl = lambda P: 0.5 * float(np.sum(P[:, 0] * np.roll(P[:, 1], -1) - np.roll(P[:, 0], -1) * P[:, 1]))
    aussen = mf.CrossSection([max(pol, key=lambda P: abs(fl(P)))]).simplify(0.04)
    # Buchsenplatte samt Schrauben und die Brückenplatten-Ecke am Tremolo-Loch ganz silber (Tom 23.11.: Ränder waren weiß) – alles Weiße dort, das nicht Schlagbrett ist
    farbe((ellipse(144.5, -1044, 47, 28, -33.7, ZK + 0.02, 62) + box(84, 104, -1023, -974, ZK + 0.02, 62)) - aussen.offset(0.05).extrude(40).translate([0, 0, 30]), 'metall', ['weiss'])
    farbe(box(20, 85, -327.5, -316.5, 47.5, G), 'weiss', ['metall', 'hals'])                                   # Sattel hell (Knochen)
    farbe(box(38, 65, -1140, -1130.2, 8, 36) + box(-64, -34, -664.8, -640, 8, 36), 'metall', ['korpus'])  # Gurtknöpfe
    farbe(HPLATTE.extrude(p(0.32)), 'metall', ['korpus', 'hals'])                                       # Halsplatte
    DS = [(10.4, -1022.7), (94.7, -1022.7), (10.3, -957.7), (94.7, -957.7), (11.0, -881.5), (94.2, -881.5)]
    farbe(add([zyl(x, y, 3.0, 0, p(0.32)) for x, y in DS]), 'metall', ['korpus'])                       # sechs Deckelschrauben
    farbe(DECKEL.extrude(p(0.32)), 'weiss', ['korpus'])                                                 # Federfach-Deckel
    # --- Schwarz (alles über der Decke) ---
    farbe(box(20, 82, -840, -821, 46.85, G) + box(20, 82, -900, -881, 46.85, G) + box(20, 82, -962, -934, 46.85, G), 'schwarz', ['weiss'])   # 18 Pole
    BY = [-321.2, -368.4, -403.9, -437.1, -469.1, -498.1, -526.3, -552.6, -576.7, -599.9, -621.8, -642.4, -662.0, -680.2, -697.7, -714.3, -729.6, -743.8, -757.9, -770.2, -782.8, -794.9, Y22]
    PKT = [(52.2, (BY[n - 1] + BY[n]) / 2) for n in (3, 5, 7, 9, 15, 17, 19, 21)] + [(52.2 - 11.0, (BY[11] + BY[12]) / 2), (52.2 + 11.0, (BY[11] + BY[12]) / 2)]
    farbe(add([zyl(x, y, 3.2, 48.0 - p(0.26), 49.0) for x, y in PKT]), 'schwarz', ['hals'])              # Griffbrett-Punkte Ø 1,18 × 0,26 tief
    # Schlagbrett dreilagig: schwarze Mittellage als Linie 0,30 breit, 0,28 vom Rand, von 0,12 über der Decke bis oben (bei Schicht 0,08: eine Schicht Weiß, zwei Schwarz, dazwischen bleibt Kopf 1 eine Schicht frei für den Spulenwechsel)
    ring = aussen.offset(-p(0.28), mf.JoinType.Round, 2.0, 32) - aussen.offset(-p(0.58), mf.JoinType.Round, 2.0, 32)
    farbe(ring.extrude(ZP - ZK - p(0.12) + 0.5).translate([0, 0, ZK + p(0.12)]) ^ box(-G, G, -G, G, -G, ZP + 0.001), 'schwarz', ['weiss'])
    print(f'Details: Schlagbrett-Umriss {abs(fl(max(pol, key=lambda P: abs(fl(P))))) * s * s:.0f} mm², {len(PKT)} Punkte, {len(SCHR)} Schrauben vorn')
z0 = 0.0 if A.details else t.bounds[0][2]; c = [-(t.bounds[0][0]+t.bounds[1][0])/2, -t.bounds[0][1], -z0]
fertig = {}
for n, m in F.items():
    m = m.translate(c).scale([s, s, s])
    grenze = 3.0 if n in ('korpus', 'hals') else (0.004 if n == 'schwarz' else 0.02)          # Schnitt-Splitter und lose Innenteile entfernen (mm³)
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
    k_ = KUG_D / 2 / 0.9 * 0.9                                                       # Form wie die Schecter-Lochkugel (2,4 × 2,0), auf Ø 1,8 × 1,5 verkleinert
    kugel = (mf.Manifold.cylinder(0.3, 0.64, 0.9, 32) + mf.Manifold.cylinder(0.9, 0.9, 0.9, 32).translate([0, 0, 0.29])
             + mf.Manifold.cylinder(0.31, 0.9, 0.64, 32).translate([0, 0, 1.18]) - mf.Manifold.cylinder(3, 0.25, 0.25, 16).translate([0, 0, -0.5]))
    raster += [kugel.translate([-sp / 2 + 3.0 * (j % 4), 2 * sp + 1.5 + 3.0 * (j // 4), 0]) for j in range(8)]   # 6 gebraucht + 2 Ersatz
    tw = export(mf.Manifold.batch_boolean(raster, mf.OpType.Add), 'strat_wirbel')  # Wirbel + 8 Lochkugeln
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
