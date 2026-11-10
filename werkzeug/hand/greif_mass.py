"""Misst den Griff-Spalt je Finger: Schnitt durch die Fingermitte, Material-Intervalle in Y auf Höhe z."""
import sys, json, numpy as np, trimesh
m=trimesh.load(sys.argv[1]); lm=json.load(open(sys.argv[1].replace('.stl','.json')))
erg={}
for f in (2,3,4,5):
    k=np.array(lm[f'k{f}']); x=k[0]
    zs=[]; 
    for dz in (4,7,10):
        z=k[2]-dz
        o=np.array([[x, m.bounds[0][1]-5, z]]); loc,_,_=m.ray.intersects_location(o,np.array([[0,1,0]]))
        zs.append(np.sort(loc[:,1]).round(1).tolist())
    erg[f]=zs
    print(f, 'Knöchel', k, 'PIP', lm[f'p{f}'], 'Spitze', lm[f'tip{f}'])
    for z in zs: print('   ', z)
