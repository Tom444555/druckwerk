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
Federfach-Deckel weiß und Halsplatte silber als bündige Einlagen (vorher standen sie 0,3 mm vor und der Korpus schwebte).
--regler 1 (24.11.2026, nur mit --details 1, ab ~215 mm, empfohlen 240): die drei Regler als drehbare Steckteile (Zapfen Ø 2,0, Loch Ø 2,3 × 4,0 im Schlagbrett),
strat_regler.stl / strat_regler_platte.stl mit 3 + 1 Ersatz, kopfüber und stützfrei gedruckt, Kopf 2 (weiß)."""
import sys, math, argparse, numpy as np, trimesh, manifold3d as mf
_ap = argparse.ArgumentParser(); _ap.add_argument('src'); _ap.add_argument('dst'); _ap.add_argument('laenge', type=float)
_ap.add_argument('--schnur', type=int, default=0, help='1 = Schnur-Saiten mit Steckwirbeln statt fester Saiten-Stege')
_ap.add_argument('--details', type=int, default=0, help='1 = Details nach Toms Fotos (5. Farbe schwarz, 22. Bund, Schrauben silber, Rückseite plan …)')
_ap.add_argument('--saiten', type=int, default=1, help='0 = ohne Saiten (für sehr kleine Fassungen wie den 50-mm-Anhänger: die Saitenstege verschmelzen dort zu einem Band)')
_ap.add_argument('--regler', type=int, default=0, help='1 = drei drehbare Steckregler (ab ~215 mm, empfohlen 240): Regler aus dem Netz entfernt, Loch im Schlagbrett, strat_regler.stl / strat_regler_platte.stl (weiß)')
A = _ap.parse_args(); src, dst, laenge = A.src, A.dst, A.laenge
assert not A.details or A.schnur, '--details braucht --schnur 1'
assert not A.regler or A.details, '--regler braucht --details 1'
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
# Kantenrundung auch entlang der Armauflage (Tom 24.11.: „die Rundung auch bei der Abflachung fortführen, dass es umlaufend ist“):
# der Keil hatte dort die Original-Rundung (r ≈ 7, aus dem Netz gemessen) weggeschnitten → scharfe Kante. Neu: derselbe Radius, relativ zur abgesenkten Fläche,
# als Abtrag aus kleinen Hüllkörpern entlang des Umrisses (Stationen alle 1,5 mm, 10 Streifen quer). Außerhalb der Abflachung trifft er nur Luft (dort ist schon rund).
_RKR = 7.0
_um = np.asarray(max((M ^ box(-150, 250, -1140, -810, -50, 200)).slice(9.0).to_polygons(), key=len), float)
if np.sum(_um[:, 0] * np.roll(_um[:, 1], -1) - np.roll(_um[:, 0], -1) * _um[:, 1]) < 0: _um = _um[::-1]
_dl = np.linalg.norm(np.roll(_um, -1, 0) - _um, axis=1); _L = _dl.sum(); _n = int(_L / 1.5)
_uu = np.concatenate([[0], np.cumsum(_dl)]); _q = np.linspace(0, _L, _n, endpoint=False); _zu = np.vstack([_um, _um[:1]])
_S = np.stack([np.interp(_q, _uu, _zu[:, 0]), np.interp(_q, _uu, _zu[:, 1])], 1)
for _ in range(4): _S = (np.roll(_S, 1, 0) + 2 * _S + np.roll(_S, -1, 0)) / 4
_tg = np.roll(_S, -1, 0) - np.roll(_S, 1, 0); _tg /= np.linalg.norm(_tg, axis=1)[:, None]; _N = np.stack([-_tg[:, 1], _tg[:, 0]], 1)   # nach innen
def _zt(pt):
    a_ = float((pt - _P) @ _u)
    return 44.02 if a_ <= -_W else min(44.02, 44.0 - _R + math.sqrt(max(_R * _R - (a_ + _W) ** 2, 0.0)))
def _zc(i, d): return (_zt(_S[i]) - _RKR) if d <= 0 else (_zt(_S[i] + d * _N[i]) - (_RKR - math.sqrt(max(_RKR * _RKR - (_RKR - d) ** 2, 0.0))))
_D = [-5.0] + [float(x) for x in _RKR * (1 - np.cos(np.linspace(0, np.pi / 2, 10)))]
_drin = [float((_S[i] - _P) @ _u) > -_W - 12 for i in range(_n)]
_ab = []                                                       # je zusammenhängendem Lauf EIN Netz (Querschnitt × Stationen) – tausende Einzel-Hüllen sprengten bei 190 mm den Speicher
_start = [i for i in range(_n) if _drin[i] and not _drin[i - 1]] or ([0] if all(_drin) else [])
for i0 in _start:
    lauf = []
    while _drin[(i0 + len(lauf)) % _n] and len(lauf) < _n: lauf.append((i0 + len(lauf)) % _n)
    if len(lauf) < 2: continue
    V, T = [], []; m = len(_D) + 2
    for ii in lauf:
        oben = max(_zt(_S[ii] + d * _N[ii]) for d in _D[1:]) + 5.0
        for d in _D: q2 = _S[ii] + d * _N[ii]; V.append([q2[0], q2[1], _zc(ii, d)])
        qa, qb = _S[ii] + _D[-1] * _N[ii], _S[ii] + _D[0] * _N[ii]; V += [[qa[0], qa[1], oben], [qb[0], qb[1], oben]]
    for a_ in range(len(lauf) - 1):
        for k in range(m):
            k2 = (k + 1) % m; p0, p1, p2, p3 = a_ * m + k, a_ * m + k2, (a_ + 1) * m + k2, (a_ + 1) * m + k
            T += [(p0, p1, p2), (p0, p2, p3)]
    e = (len(lauf) - 1) * m
    for k in range(1, m - 2): T += [(m - 1, k + 1, k), (e + m - 1, e + k, e + k + 1)]; 
    T += [(m - 1, 1, 0), (e + m - 1, e, e + 1)]
    k_ = mf.Manifold(mf.Mesh(np.array(V, np.float32), np.array(T, np.uint32)))
    if k_.volume() < 0: k_ = mf.Manifold(mf.Mesh(np.array(V, np.float32), np.array(T, np.uint32)[:, ::-1]))
    assert k_.status() == mf.Error.NoError and k_.volume() > 0, k_.status()
    _ab.append(k_)
if _ab:
    _v0 = M.volume(); M = M - mf.Manifold.batch_boolean(_ab, mf.OpType.Add)
    print(f'Armauflage: Kantenrundung r {_RKR} über {sum(_drin)} Stationen, Abtrag {(_v0 - M.volume()):.0f} mm³ (Original)')
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
    # Buchsenmulde neu (Toms Foto 23.11.): Hohlraum füllen, saubere Schale (tief am breiten Ende, läuft zur Spitze flach aus), darin schräg Mutter + Hülse + Loch
    BW, BM, BT = -33.7, (144.5, -1044.0), 11.0                                      # Winkel der Platte, Mitte, Muldentiefe unter der Decke
    lok = lambda m: m.rotate([0, 0, BW]).translate([BM[0], BM[1], 0])               # lokal (x = Längsachse zur Spitze) → Modell
    ring_ = lambda pts, z: [[x, y, z] for x, y in pts]
    oben_ = mf.CrossSection([np.array([[-15.0, -9.0], [21.0, -2.6], [21.0, 2.6], [-15.0, 9.0]])]).offset(2.0, mf.JoinType.Round, 2.0, 32).to_polygons()[0]
    unten_ = mf.CrossSection.circle(5.6, 32).scale([1.5, 1.0]).translate([-6.5, 0]).to_polygons()[0]
    # Platten-Umriss = Hülle aus neuer Ellipse und alter Platte des Original-Netzes (Tom 24.11.: rechts stand die alte Platte als zweite Kante über) → ein glatter Rand rundum
    alt_pl = (M ^ ellipse(144.5, -1044, 41, 23, -33.7, ZK - 1, ZK + 2)).slice(ZK + 0.35)
    neu_pl = mf.CrossSection.circle(1.0, 96).scale([34.0, 16.5]).rotate(BW).translate([BM[0], BM[1]])
    # Echte Ovalform, spiegelgleich (Tom 24.11.: die alte Platte des Original-Netzes ist schief – oben links und unten rechts ausgebeult):
    # Länge aus der alten Platte, Breite aus ihrer Mitte; was von der alten Platte außerhalb liegt, wird unten bündig mit Korpus gefüllt und oben weggeschnitten.
    # Achse durch die beiden Schraubenköpfe (wie am echten Teil), Mitte = zwischen den Schrauben
    _kp = [np.asarray(q).mean(0) for q in ((M ^ ellipse(144.5, -1044, 45, 26, -33.7, ZK + 1.6, ZK + 2.4)).slice(ZK + 2.0)).to_polygons() if len(q) > 8]
    _kp = sorted(_kp, key=lambda q: q[0]); _s1, _s2 = np.array(_kp[0]), np.array(_kp[-1])
    PM = (_s1 + _s2) / 2; PW = float(np.degrees(np.arctan2(*(_s2 - _s1)[::-1])))
    _lp = np.vstack([np.asarray(q) for q in alt_pl.translate([-PM[0], -PM[1]]).rotate(-PW).to_polygons()])
    _a = max(float(np.abs(_lp[:, 0]).max()), np.linalg.norm(_s2 - _s1) / 2 + 6.5); _b = float(np.abs(_lp[np.abs(_lp[:, 0]) < 4.0, 1]).max())
    umriss = mf.CrossSection.circle(1.0, 128).scale([_a, _b]).rotate(PW).translate([PM[0], PM[1]])
    print(f'Buchsenplatte: Schrauben {_s1.round(1)} / {_s2.round(1)}, Achse {PW:.1f}° (Mulde {BW}°)')
    alt_huelle = mf.CrossSection.hull(alt_pl).offset(0.3, mf.JoinType.Round, 2.0, 32)
    M = M - (alt_huelle.offset(2.0, mf.JoinType.Round, 2.0, 32) - umriss).extrude(40).translate([0, 0, ZK]) + (alt_huelle - umriss).extrude(3.0).translate([0, 0, ZK - 3.0])   # ab genau ZK schneiden: sonst bleibt eine hauchdünne alte Platte, die die App grau zeigt
    print(f'Buchsenplatte: Oval {2*_a*s:.2f} × {2*_b*s:.2f} mm (Druckmaß)')
    PLATTE = umriss.extrude(BT + 3 + 0.8).translate([0, 0, ZK - BT - 3])   # 0,8 über Decke: deckt die alte Platte (Oberkante ZK+0,74) ganz zu
    M = M + PLATTE
    M = M - lok(mf.Manifold.hull_points(np.array(ring_(oben_, 46.5) + ring_(oben_, ZK - 0.6) + ring_(unten_, ZK - BT))))
    kipp = lambda m: lok(m.rotate([0, 55, 0]).translate([-13.5, 0, ZK - 7.0]))      # Achse 35° über der Waagrechten, zeigt zur Spitze
    mutter = kipp(mf.Manifold.cylinder(7.0, 6.2, 6.2, 6).translate([0, 0, -4.0]) + mf.Manifold.cylinder(9.0, 4.3, 4.3, 32).translate([0, 0, -4.0]))
    mutter = mutter ^ lok(mf.Manifold.cylinder(40, 1, 1, 96).scale([33.0, 15.5, 1]).translate([0, 0, ZK - BT - 3])) ^ box(-G, G, -G, G, -G, ZK + 0.5)
    M = M + mutter - kipp(mf.Manifold.cylinder(14.0, p(0.47), p(0.47), 24).translate([0, 0, -6.0]))
if A.regler:
    # ================= Drehbare Steckregler (24.11.2026, Tom: „die 240 kannst du fertig machen“) =================
    # Lage und Form aus dem Netz gemessen (Mitte der Kappe; Rock r 13,4 bei z 45,65 → Kappe r 9,4 ab z 50, Oberkante 59,6)
    REG = [(107.55, -958.07), (145.94, -979.29), (179.48, -1007.86)]
    ZAPF_R, ZAPF_SP, ZAPF_L, LOCH_T = 1.0, 0.15, 3.6, 4.0                          # Druckmaß: Zapfen Ø 2,0, Spiel 0,15 je Seite, Loch 4,0 tief
    assert 9.4 * s >= ZAPF_R + ZAPF_SP + 0.85, f'Regler zu klein für Steckzapfen (Länge {laenge} mm) – ab etwa 215 mm'
    M = M - mf.Manifold.batch_boolean([zyl(x, y, 13.5, ZP + 0.02, 80) for x, y in REG], mf.OpType.Add)                       # alte Regler weg
    M = M + mf.Manifold.batch_boolean([zyl(x, y, p(2.4), ZP - p(LOCH_T + 0.8), ZP) for x, y in REG], mf.OpType.Add)          # volles Material um das Loch (Hohlräume unter dem Schlagbrett)
    M = M - mf.Manifold.batch_boolean([zyl(x, y, p(ZAPF_R + ZAPF_SP), ZP - p(LOCH_T), ZP + 1, 48) for x, y in REG], mf.OpType.Add)
breiten = [0.6, 0.55, 0.5, 0.42, 0.36, 0.3]   # Stegbreite je Saite im fertigen Modell (mm): E A D dick, g h e dünn
if not A.schnur: saiten = mf.Manifold()
if not A.schnur and not A.saiten: M = M - box(20, 85, -985.9, -323.6, 49.85, G) - box(20, 85, -319.3, Y_KOPF, 40.0, G)   # Saiten aus dem Netz, Mechaniken bleiben
y_s0, y_s1 = -996.0, Y_NUT
for x0, x1, br in ([] if (A.schnur or not A.saiten) else zip(xa, xb, breiten)):
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
    farbe(umriss.extrude(BT + 3.1).translate([0, 0, ZK - BT - 3.1]) ^ lok(mf.Manifold.cylinder(BT + 3.2, 1, 1, 96).scale([34.2, 16.7, 1]).translate([0, 0, ZK - BT - 3.1])), 'metall', ['korpus'])   # Buchsenmulde innen silber
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
    # Schlagbrett dreilagig wie am Original (Tom 24.11.): an der SENKRECHTEN Außenkante unten Weiß, Mitte Schwarz, oben Weiß – oben auf der Fläche keine Linie.
    # Schlagbrett = 0,30 mm = 3 Schichten à 0,08 (Mitten 8,22 / 8,30 / 8,38) → schwarzes Band 0,30 breit am Rand von 0,12 bis 0,195 über der Decke = genau die mittlere Schicht.
    band = aussen - aussen.offset(-p(0.30), mf.JoinType.Round, 2.0, 32)
    farbe(band.extrude(p(0.075)).translate([0, 0, ZK + p(0.12)]), 'schwarz', ['weiss'])
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
    if A.regler:
        # Regler kopfüber gedruckt (Kappe auf dem Bett, Rock weitet sich nach oben, Zapfen zeigt nach oben) – stützfrei. Zapfen leicht kegelig:
        # an der Wurzel 0,01 dicker als das Loch → sitzt mit leichter Reibung, bevor der Rock aufliegt, und lässt sich drehen.
        RT, RSK, HR, HSK = 9.4 * s, 13.4 * s, (59.6 - 45.65) * s, (50.0 - 45.65) * s
        nr = max(16, int(round(2 * math.pi * RT / 0.7)))
        rippe = np.array([[(RT - (0.12 if j % 2 else 0)) * math.cos(j * math.pi / nr), (RT - (0.12 if j % 2 else 0)) * math.sin(j * math.pi / nr)] for j in range(2 * nr)])
        wz = ZAPF_R + ZAPF_SP + 0.01
        knopf = (mf.Manifold.cylinder(0.26, RT - 0.3, RT - 0.12, 64) + mf.CrossSection([rippe]).extrude(HR - HSK - 0.25).translate([0, 0, 0.25])
                 + mf.Manifold.cylinder(HSK - 0.16, RT - 0.12, RSK, 64).translate([0, 0, HR - HSK - 0.01]) + mf.Manifold.cylinder(0.17, RSK, RSK, 64).translate([0, 0, HR - 0.17])
                 + mf.Manifold.cylinder(ZAPF_L, wz, ZAPF_R, 40).translate([0, 0, HR - 0.01]) + mf.Manifold.cylinder(0.25, ZAPF_R, ZAPF_R - 0.2, 40).translate([0, 0, HR + ZAPF_L - 0.02]))
        yr = 2 * sp + 4.5 + 3.0 + RSK + 2.0; ar = 2 * RSK + 1.6
        rr = [knopf.translate([ar * (j % 2), yr + ar * (j // 2), 0]) for j in range(4)]                      # 3 gebraucht + 1 Ersatz
        tr_ = export(mf.Manifold.batch_boolean(rr, mf.OpType.Add), 'strat_regler')
        trp = export(mf.Manifold.batch_boolean([m.translate([x0p, y0p, 0]) for m in rr], mf.OpType.Add), 'strat_regler_platte')
        spalt = ZAPF_L * 0.01 / (wz - ZAPF_R)                                                                # so weit bleibt der Rock über dem Schlagbrett
        zpd = (ZP + c[2]) * s
        sr = [knopf.rotate([180, 0, 0]).translate([(x + c[0]) * s, (y + c[1]) * s, zpd + HR + spalt]) for x, y in REG]
        print(f'strat_regler.stl: dicht={tr_.is_watertight}, 4 Regler (3 + 1 Ersatz), Kappe Ø {2*RT:.2f}, Rock Ø {2*RSK:.2f}, Höhe {HR:.2f}, {nr} Rippen, Zapfen Ø {2*wz:.2f} → {2*ZAPF_R:.2f} × {ZAPF_L}, '
              f'Loch Ø {2*(ZAPF_R+ZAPF_SP):.2f} × {LOCH_T}, Rock {spalt:.2f} über dem Schlagbrett; Platte bis x {trp.bounds[1][0]:.1f}, y {trp.bounds[1][1]:.1f}')
        for n_, m_ in fertig.items(): print(f'  Schnitt Regler/{n_}: {(mf.Manifold.batch_boolean(sr, mf.OpType.Add) ^ m_).volume():.3f} mm³')
        export(mf.Manifold.batch_boolean(sr, mf.OpType.Add), '_regler_steckend')
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
