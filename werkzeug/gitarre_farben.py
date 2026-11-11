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
# Rippenbogen (Bauchausschnitt) auf der Rückseite, Bass-Seite an der Taille: sanfte Mulde bis 22 mm tief am Rand
M = M - mf.Manifold.sphere(1, 96).scale([62, 100, 22]).translate([-72, -850, 0])
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
