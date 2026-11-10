"""Setzt die Einzelteile von modelle/loopsmiths_amp.scad zu 3 Farb-STLs zusammen (ohne Überschneidungen).
Vorrang: schwarze Einlagen > Biese/Nähte (Spule 4, gold) > weiß > rot > schwarzer Korpus.  Aufruf: python3 loopsmiths_farben.py <teile_ordner> <ziel_ordner>"""
import sys, numpy as np, trimesh, manifold3d as mf
from scipy.spatial import cKDTree
src, dst = sys.argv[1:3]
def M(n):
    t = trimesh.load(f'{src}/{n}.stl')
    m = mf.Manifold(mf.Mesh(vert_properties=np.asarray(t.vertices, np.float32), tri_verts=np.asarray(t.faces, np.uint32)))
    if m.status() != mf.Error.NoError: raise SystemExit(f'{n}: {m.status()}')
    return m
def U(names):
    r = None
    for n in names: r = M(n) if r is None else r + M(n)
    return r
def lederhaut(B=110, T=59, H=62, R=5, z0=0.0, raster=0.3, zelle=1.45, rille=0.28, tiefe=0.26, seed=7):
    """Rundbox als feines Netz (~0,3 mm) mit genarbter Lederstruktur (Worley-Rillen + leicht gewölbte Narben).
    Aufbau: Würfel-Raster je Seite -> auf die Rundbox projiziert -> nach innen verschoben. Boden bleibt glatt."""
    c = np.array([0.0, T/2, z0 + H/2]); hb = np.array([B/2, T/2, H/2]) - R; e = hb + R
    n = np.maximum(2, np.ceil(2*e/raster).astype(int))
    V = []; F = []
    def seite(ax, sg):
        u, w = [i for i in range(3) if i != ax]
        uu = np.linspace(-e[u], e[u], n[u]+1); ww = np.linspace(-e[w], e[w], n[w]+1)
        U_, W_ = np.meshgrid(uu, ww, indexing='ij')
        P = np.zeros(U_.shape + (3,)); P[..., ax] = sg*e[ax]; P[..., u] = U_; P[..., w] = W_
        base = sum(len(v) for v in V); V.append(P.reshape(-1, 3))
        nu, nw = len(uu), len(ww); i, j = np.meshgrid(np.arange(nu-1), np.arange(nw-1), indexing='ij')
        a0 = base + i*nw + j; a1 = a0 + nw; a2 = a0 + 1; a3 = a1 + 1
        q = np.stack([np.stack([a0, a1, a3], -1), np.stack([a0, a3, a2], -1)], -2).reshape(-1, 3)
        # Ausrichtung so, dass die Normalen nach außen zeigen
        if (sg > 0) != ((ax == 1)): q = q[:, ::-1]
        F.append(q)
    for ax in range(3):
        for sg in (-1, 1): seite(ax, sg)
    t = trimesh.Trimesh(np.vstack(V), np.vstack(F), process=True); t.merge_vertices()
    v = t.vertices; pin = np.clip(v, -hb, hb); d = v - pin; nrm = d / np.linalg.norm(d, axis=1)[:, None]
    t.vertices = c + pin + R*nrm
    t.fix_normals()
    rng = np.random.default_rng(seed)
    lo, hi = t.bounds[0] - 2, t.bounds[1] + 2
    g = np.mgrid[lo[0]:hi[0]:zelle, lo[1]:hi[1]:zelle, lo[2]:hi[2]:zelle].reshape(3, -1).T
    pkt = g + rng.uniform(0, zelle, g.shape)
    dd, _ = cKDTree(pkt).query(t.vertices, k=2)
    kante = np.clip(1 - (dd[:, 1] - dd[:, 0]) / rille, 0, 1) ** 1.5      # Rille zwischen zwei Narben
    woelb = 0.35 * (dd[:, 0] / zelle) ** 2                               # Narbe zur Mitte leicht gewölbt
    versatz = -tiefe * np.clip(kante + woelb * (1 - kante), 0, 1)
    versatz[t.vertices[:, 2] < z0 + 0.6] = 0                             # Standfläche glatt
    t.vertices = t.vertices + nrm * versatz[:, None]
    print('Lederhaut:', len(t.faces), 'Flächen, dicht:', t.is_watertight, 'Volumen ok:', t.is_volume)
    return t
def zu_mf(t):
    return mf.Manifold(mf.Mesh(vert_properties=np.asarray(t.vertices, np.float32), tri_verts=np.asarray(t.faces, np.uint32)))
korpus = zu_mf(lederhaut()) - M('korpus_aus') + M('korpus_dazu')
if korpus.status() != mf.Error.NoError: raise SystemExit(f'Leder-Korpus: {korpus.status()}')
einlage = U(['panel_druck', 'zeiger', 'rock', 'buchse_s', 'schalter_s', 'gitter'])
gold    = U(['paspel', 'naehte']) - einlage
weiss   = U(['kissen', 'logo', 'ecken', 'panel', 'knopf', 'buchse_w', 'schalter_w', 'lampe_w', 'griff_kappen', 'schild_text']) - einlage - gold
rot     = U(['band', 'kappe', 'lampe_r', 'schild']) - weiss - gold - einlage
schwarz = (korpus - weiss - rot - gold) + einlage - M('buchse_loch')
boden = mf.Manifold.cube([400, 400, 200]).translate([-200, -200, 0])   # alles unter der Druckplatte abschneiden
for n, m in (('schwarz', schwarz), ('rot', rot), ('weiss', weiss), ('gold', gold)):
    m = m ^ boden
    r = m.to_mesh(); t = trimesh.Trimesh(r.vert_properties[:, :3], r.tri_verts)
    t.export(f'{dst}/loopsmiths_amp_{n}.stl'); print(n, len(t.faces), 'Flächen', t.bounds.round(1).tolist())
