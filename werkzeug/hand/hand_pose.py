"""Realistische Hand aus dem MakeHuman-Basismodell (CC0) in Greifhaltung bringen.
Ausgabe: STL in Modell-Koordinaten (mm). Aufruf: python3 hand_pose.py <mh_ordner> <out.stl> [optionen als JSON]"""
import json, sys, numpy as np, trimesh
mh = sys.argv[1]; out = sys.argv[2]
P = json.loads(sys.argv[3]) if len(sys.argv) > 3 else {}
# ---------- Laden ----------
V=[]; F=[]; cur=None
for line in open(f'{mh}/base.obj'):
    if line.startswith('v '): V.append([float(x) for x in line.split()[1:4]])
    elif line.startswith('g '): cur=line.split()[1]
    elif line.startswith('f ') and cur=='body': F.append([int(t.split('/')[0])-1 for t in line.split()[1:]])
V=np.array(V)
sk=json.load(open(f'{mh}/default.mhskel')); B=sk['bones']
J={k:V[v].mean(0) for k,v in sk['joints'].items()}
head=lambda b: J[B[b]['head']]; tail=lambda b: J[B[b]['tail']]
Wt=json.load(open(f'{mh}/default_weights.mhw'))['weights']
nv=len(V); W={}
for b,lst in Wt.items():
    a=np.zeros(nv)
    for i,w in lst: a[i]=w
    W[b]=a
tot=sum(W.values()); tot[tot==0]=1
for b in W: W[b]=W[b]/tot
# ---------- Handrahmen ----------
nrm=lambda v: v/np.linalg.norm(v)
d = nrm(head('finger3-1.R') - head('wrist.R'))
t = head('finger2-1.R') - head('finger5-1.R')
n = nrm(np.cross(t, d)); t = nrm(np.cross(d, n))          # n: aus der Handfläche heraus
# ---------- Pose (Beugewinkel in Grad) ----------
mcp=P.get('mcp',88); pip=P.get('pip',92); dip=P.get('dip',12)
pose={}
spread={2:-4,3:0,4:4,5:9}
for f in (2,3,4,5):
    pose[f'finger{f}-1.R']=(mcp + (f-3)*1.5, spread[f]); pose[f'finger{f}-2.R']=(pip,0); pose[f'finger{f}-3.R']=(dip,0)
pose['finger1-1.R']=(P.get('th1',10),P.get('th1s',-15)); pose['finger1-2.R']=(P.get('th2',15),0); pose['finger1-3.R']=(P.get('th3',20),0)
def rotm(axis,ang):
    if np.linalg.norm(axis)<1e-9: return np.eye(3)
    axis=nrm(axis); a=np.radians(ang); K=np.array([[0,-axis[2],axis[1]],[axis[2],0,-axis[0]],[-axis[1],axis[0],0]])
    return np.eye(3)+np.sin(a)*K+(1-np.cos(a))*K@K
# Handgelenk gerade richten: Handrichtung d auf Unterarmrichtung a drehen (Anteil 'gelenk', 1 = ganz gerade)
a_arm = nrm(head('wrist.R') - head('lowerarm01.R'))
ang_w = np.degrees(np.arccos(np.clip(d@a_arm,-1,1))) * P.get('gelenk',1.0)
R_wrist = rotm(np.cross(d, a_arm), ang_w)
G={}
def glob(b):
    if b in G: return G[b]
    par=B[b]['parent']; Gp=glob(par) if par else np.eye(4)
    M=np.eye(4)
    if b=='wrist.R':
        p=head(b); M[:3,:3]=R_wrist; M[:3,3]=p-R_wrist@p
    if b in pose:
        flex,spr=pose[b]; p=head(b); db=nrm(tail(b)-head(b))
        if b.startswith('finger1'):            # Daumen: Achse quer zur Daumenrichtung, ungefähr Handflächennormale
            ax=nrm(np.cross(db, n)) ; ax=nrm(ax*0.5 + nrm(np.cross(db, t))*0.5)
        else: ax=np.cross(db, n)                # Beugeachse (Beugung zur Handfläche)
        R=rotm(ax, flex) @ rotm(n, spr)
        M[:3,:3]=R; M[:3,3]=p-R@p
    G[b]=Gp@M; return G[b]
Vh=np.c_[V,np.ones(nv)]; Vp=np.zeros((nv,3))
for b in W:
    if W[b].max()==0: continue
    Vp+=W[b][:,None]*(Vh@glob(b).T)[:,:3]
# ---------- Handbereich ausschneiden ----------
hb=[b for b in W if b.endswith('.R') and (b.startswith(('finger','metacarpal','wrist','lowerarm')))]
sel=sum(W[b] for b in hb)>0.5
tris=[]
for f in F:
    if all(sel[i] for i in f):
        tris += [[f[0],f[1],f[2]]] + ([[f[0],f[2],f[3]]] if len(f)==4 else [])
m=trimesh.Trimesh(Vp,np.array(tris),process=True); m.remove_unreferenced_vertices()
# ---------- in Modellrahmen drehen: Finger-Richtung d -> +Z, Handfläche n -> -Y ----------
d2=a_arm; n2=nrm(R_wrist@n - (R_wrist@n@d2)*d2); t2=nrm(np.cross(d2,n2))
R=np.vstack([t2, -n2, d2])          # Zeilen = Zielachsen X,Y,Z (Unterarm senkrecht, Handfläche nach vorn)
s=P.get('scale',58.0)
m.vertices=(m.vertices@R.T)*s
def pj(b, which='head'):            # Gelenkposition nach Pose, im Modellrahmen
    q=np.r_[head(b) if which=='head' else tail(b),1]; return ((glob(b)@q)[:3]@R.T*s).round(2).tolist()
lm={f'k{f}':pj(f'finger{f}-1.R') for f in range(2,6)}
lm.update({f'p{f}':pj(f'finger{f}-2.R') for f in range(2,6)})
lm.update({f'tip{f}':pj(f'finger{f}-3.R','tail') for f in range(1,6)})
lm['wrist']=pj('wrist.R'); lm['ellbogen']=((head('lowerarm01.R'))@R.T*s).round(2).tolist()
json.dump(lm, open(out.replace('.stl','.json'),'w'), indent=1)
m.export(out); print('ok', len(m.faces), m.is_watertight, m.bounds.round(1).tolist())
