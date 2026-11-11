"""Entfernt lose Kleinteile aus einem STL (z. B. abgeschnittene Astspitzen), damit nichts Unverbundenes gedruckt wird.
Behalten wird alles ab <min_vol> mm³ sowie Teile im Bereich der Fußplatte (liegend: y > -6).
Aufruf: python3 lose_teile.py <ein.stl> <aus.stl> [min_vol]"""
import sys, numpy as np, trimesh, manifold3d as mf
t = trimesh.load(sys.argv[1]); mv = float(sys.argv[3]) if len(sys.argv) > 3 else 60.0
m = mf.Manifold(mf.Mesh(vert_properties=np.asarray(t.vertices, np.float32), tri_verts=np.asarray(t.faces, np.uint32)))
teile = m.decompose(); behalten = [k for k in teile if k.volume() >= mv or k.bounding_box()[1] > -6]
r = mf.Manifold.compose(behalten).to_mesh(); trimesh.Trimesh(r.vert_properties[:, :3], r.tri_verts).export(sys.argv[2])
print(sys.argv[2], 'Teile', len(teile), '->', len(behalten), 'entfernt', round(sum(k.volume() for k in teile if k not in behalten), 2), 'mm³')
