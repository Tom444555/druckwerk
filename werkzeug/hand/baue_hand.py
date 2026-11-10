"""Baut die realistische Greif-Hand für modelle/ftz_hand_*.scad.
Ablauf: MakeHuman-Hand (CC0) biegen -> an „FTZ“ ausrichten -> glätten (Loop-Unterteilung)
-> Adern + Sehnen auf dem Handrücken einformen -> Unterarm im Sockel abschneiden/schließen
-> Überschneidung mit Schrift/Brett/Leiste/Sockel abziehen -> STL.
Aufruf: python3 baue_hand.py <mh_ordner> <teile_ordner mit fritz/ftz/brett/leiste/sockel.stl> <out.stl>
"""
import sys, json, subprocess, numpy as np, trimesh, manifold3d as mf
from scipy.spatial import cKDTree

mh, teile, out = sys.argv[1:4]
HIER = __file__.rsplit('/', 1)[0]
# --- Maße aus ftz_hand_basis.scad ---
echo = subprocess.run(['openscad', '-o', '/tmp/_m.echo', f'{teile}/brett.scad'], capture_output=True, text=True)
ftz_oben, yc, s_hoehe, tiefe_ftz = json.loads(open('/tmp/_m.echo').read().split('MASSE = ')[1].split('\n')[0])
x_mittelfinger = 4.0          # Mittelfinger greift über das „T“
POSE = {"scale": 60, "mcp": 85, "pip": 80, "dip": 5, "th1": -30, "th1s": 0}

# 1) Hand biegen
roh = '/tmp/hand_roh.stl'
subprocess.run(['python3', f'{HIER}/hand_pose.py', mh, roh, json.dumps(POSE)], check=True)
m = trimesh.load(roh); lm = json.load(open(roh.replace('.stl', '.json')))

# 2) Griff messen (Mittelfinger): Spalt vor der Handfläche + Unterkante Grundglied
k3 = np.array(lm['k3'])
def treffer(o, d):
    loc, _, _ = m.ray.intersects_location(np.array([o]), np.array([d])); return loc
ys = np.sort(treffer([k3[0], m.bounds[0][1]-5, k3[2]-7], [0, 1, 0])[:, 1])
gap_y = (ys[1] + ys[2]) / 2
zs = np.sort(treffer([k3[0], gap_y, k3[2]-30], [0, 0, 1])[:, 2])
unterkante = zs[0]
print(f'Spalt Mittelfinger: {ys[2]-ys[1]:.1f} mm, Unterkante Grundglied z={unterkante:.1f}')
T = np.array([x_mittelfinger - k3[0], yc - gap_y, ftz_oben + 0.4 - unterkante])
m.apply_translation(T)
lm = {k: (np.array(v) + T).tolist() for k, v in lm.items()}

# 3) Glätten: zweimal Loop-Unterteilung
v, f = trimesh.remesh.subdivide_loop(m.vertices, m.faces, iterations=3)
m = trimesh.Trimesh(v, f, process=True)
trimesh.smoothing.filter_taubin(m, iterations=10)     # Knickstellen vom Biegen glätten

# 4) Adern/Sehnen auf dem Handrücken (+Y-Seite) und Unterarm einformen
w = np.array(lm['wrist']); K = {f: np.array(lm[f'k{f}']) for f in (2, 3, 4, 5)}
def P(*pts): return [np.array(p, float) for p in pts]
def zw(a, b, t): return a + (b - a) * t
zh = lambda z: z  # Lesbarkeit
# Handrücken-Ebene: x quer, z hoch. Punkte als (x, z)
wx, wz = w[0], w[2]
knx = {f: K[f][0] for f in K}; knz = {f: K[f][2] for f in K}
bogen_z = wz + 0.45 * (np.mean(list(knz.values())) - wz)
adern = [  # (Pfad in x/z, Höhe mm, Radius mm)
    # Venenbogen quer über den Handrücken
    ([(knx[5]-2, bogen_z+4), (knx[4], bogen_z-1), (knx[3]-3, bogen_z+1.5), (knx[3]+4, bogen_z-2), (knx[2]+3, bogen_z+3)], 1.0, 1.4),
    # Äste zu den Fingerzwischenräumen
    ([(knx[4], bogen_z-1), ((knx[4]+knx[5])/2, knz[5]-6)], 0.8, 1.2),
    ([(knx[3]-3, bogen_z+1.5), ((knx[3]+knx[4])/2, knz[4]-5)], 0.8, 1.2),
    ([(knx[3]+4, bogen_z-2), ((knx[2]+knx[3])/2+1, knz[3]-6)], 0.8, 1.2),
    # Hauptvenen zum Handgelenk und weiter den Unterarm hinab (gewunden)
    ([(knx[5]-2, bogen_z+4), (wx-9, wz+6), (wx-10, wz-5), (wx-7, wz-18), (wx-9, wz-32), (wx-6, s_hoehe+2)], 1.1, 1.7),
    ([(knx[2]+3, bogen_z+3), (wx+8, wz+4), (wx+6, wz-8), (wx+9, wz-20), (wx+5, wz-34), (wx+7, s_hoehe+2)], 1.1, 1.7),
    ([(wx-7, wz-18), (wx-1, wz-25), (wx+5, wz-34)], 0.9, 1.4),
]
sehnen = [([(wx + (knx[f]-wx)*0.15, wz+2), (knx[f], knz[f]-4)], 0.45, 2.4) for f in (2, 3, 4, 5)]

def dichte(pfad, schritt=0.3):
    pts = []
    for a, b in zip(pfad[:-1], pfad[1:]):
        a, b = np.array(a), np.array(b); n = max(2, int(np.linalg.norm(b-a)/schritt))
        pts += [a + (b-a)*t for t in np.linspace(0, 1, n, endpoint=False)]
    return np.array(pts + [np.array(pfad[-1])])

vn = m.vertex_normals.copy(); V = m.vertices.copy()
ruecken = vn[:, 1] > 0.25                    # nur nach hinten zeigende Flächen
# nur die äußere Rückseite (nicht Fingerinnenseiten): y nahe der maximalen Tiefe an dieser Stelle
disp = np.zeros(len(V))
for pfad, h, r in adern + sehnen:
    d2 = dichte(pfad); tree = cKDTree(d2)
    dist, _ = tree.query(V[:, [0, 2]])
    bump = h * np.exp(-(dist / r) ** 2)
    disp = np.maximum(disp, np.where(ruecken & (V[:, 2] < max(knz.values()) - 2), bump, 0))
# Verschiebung über Nachbarn glätten (weiche Übergänge statt Kanten)
nb = m.vertex_neighbors
for _ in range(3):
    disp = np.array([0.5*disp[i] + 0.5*np.mean(disp[n]) if len(n) else disp[i] for i, n in enumerate(nb)])
m.vertices = V + vn * disp[:, None]
print('Adern eingeformt, max. Höhe', disp.max().round(2))

# 5) Unterarm im Sockel abschneiden (Schnitt 1 mm unter Sockeloberkante) und schließen
m = m.slice_plane([0, 0, s_hoehe - 1.0], [0, 0, 1], cap=True)
m.merge_vertices(); m.fix_normals()
print('wasserdicht:', m.is_watertight, 'Flächen:', len(m.faces))

# 6) Mit Manifold freischneiden
def to_mf(tm):
    return mf.Manifold(mf.Mesh(vert_properties=np.asarray(tm.vertices, np.float32), tri_verts=np.asarray(tm.faces, np.uint32)))
hand = to_mf(m)
if hand.status() != mf.Error.NoError or hand.is_empty():
    raise SystemExit(f'Hand nicht manifold: {hand.status()}')
for n in ('fritz', 'ftz', 'brett', 'leiste', 'sockel'):
    hand = hand - to_mf(trimesh.load(f'{teile}/{n}.stl'))
r = hand.to_mesh()
erg = trimesh.Trimesh(r.vert_properties[:, :3], r.tri_verts)
erg.export(out)
print('fertig', out, len(erg.faces), 'Flächen, Maße', erg.bounds.round(1).tolist())
