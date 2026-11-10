"""Setzt die Einzelteile von modelle/loopsmiths_amp.scad zu 3 Farb-STLs zusammen (ohne Überschneidungen).
Vorrang: schwarze Einlagen > weiß > rot > schwarzer Korpus.  Aufruf: python3 loopsmiths_farben.py <teile_ordner> <ziel_ordner>"""
import sys, numpy as np, trimesh, manifold3d as mf
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
einlage = U(['panel_druck', 'zeiger', 'rock', 'buchse_s', 'schalter_s', 'gitter'])
weiss   = U(['keder', 'logo', 'ecken', 'panel', 'knopf', 'buchse_w', 'schalter_w', 'lampe_w', 'griff_kappen', 'schild_text']) - einlage
rot     = U(['stoff', 'band', 'kappe', 'lampe_r', 'schild']) - weiss - einlage
schwarz = (M('korpus') - weiss - rot) + einlage - M('buchse_loch')
boden = mf.Manifold.cube([400, 400, 200]).translate([-200, -200, 0])   # alles unter der Druckplatte abschneiden
for n, m in (('schwarz', schwarz), ('rot', rot), ('weiss', weiss)):
    m = m ^ boden
    r = m.to_mesh(); t = trimesh.Trimesh(r.vert_properties[:, :3], r.tri_verts)
    t.export(f'{dst}/loopsmiths_amp_{n}.stl'); print(n, len(t.faces), 'Flächen', t.bounds.round(1).tolist())
