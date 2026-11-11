"""Toms Stratocaster-STL (ein Körper, Originalgröße) in 4 Farbteile schneiden und verkleinern.
Teile: korpus (creme), weiss (Schlagbrett, Pickups, Regler), hals (Ahorn), metall (Brücke, Bünde, Saiten, Mechaniken, Buchse).
Saiten werden als druckbare Stege (bis auf die Oberfläche) neu aufgebaut, weil sie verkleinert sonst zu dünn sind.
Aufruf: python3 gitarre_farben.py <original.stl> <ziel_ordner> <laenge_mm>"""
import sys, numpy as np, trimesh, manifold3d as mf
src, dst, laenge = sys.argv[1], sys.argv[2], float(sys.argv[3])
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
breiten = [0.6, 0.55, 0.5, 0.42, 0.36, 0.3]   # Stegbreite je Saite im fertigen Modell (mm): E A D dick, g h e dünn
saiten = mf.Manifold()
y_s0, y_s1 = -996.0, Y_NUT
for x0, x1, br in zip(xa, xb, breiten):
    bs = br / s
    f = lambda y: x0 + (x1-x0)*(y-ya)/(yb-ya)
    ecken = np.array([[f(y_s0)-bs/2, y_s0], [f(y_s0)+bs/2, y_s0], [f(y_s1)+bs/2, y_s1], [f(y_s1)-bs/2, y_s1]])
    st = mf.Manifold.extrude(mf.CrossSection([ecken]), 51.7-43.5).translate([0, 0, 43.5])
    saiten += st
saiten = saiten - box(NX0, NX1, Y_HEEL, y_s1+1, 0, 47.0)     # am freien Hals nur bis ins Griffbrett
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
for n, m in (('korpus', korpus), ('weiss', weiss), ('hals', hals), ('metall', metall)):
    m = m.translate(c).scale([s, s, s])
    grenze = 3.0 if n in ('korpus', 'hals') else 0.02          # Schnitt-Splitter und lose Innenteile entfernen (mm³)
    teile = [k for k in m.decompose() if k.volume() > grenze]
    m = mf.Manifold.compose(teile); r = m.to_mesh()
    o = trimesh.Trimesh(r.vert_properties[:, :3], r.tri_verts); o.export(f'{dst}/strat_{n}.stl')
    print(n, len(o.faces), 'Flächen', o.extents.round(1).tolist(), 'Vol', round(m.volume(), 1))
print('Maßstab', round(s, 4))
