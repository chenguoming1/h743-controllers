import sys,json,math,hashlib
sys.path.insert(0,'/workspace/shared/nexus-main-placement-fix/scripts')
from router import *
p='/workspace/shared/nexus-main-placement-fix/stage35/hardware/nexus-style-fc.kicad_pcb';b=k.LoadBoard(p);out={'sha256':hashlib.sha256(open(p,'rb').read()).hexdigest()};zones={l:[z.GetFilledPolysList(l) for z in b.Zones() if z.GetNetname()=='GND' and z.HasFilledPolysForLayer(l)] for l in [k.F_Cu,k.In1_Cu,k.In4_Cu,k.B_Cu]}
def inside(p,l):return any(ps.Contains(vec(p)) for ps in zones[l])
for q in [(106.65,110.1),(104.6,106.6),(104.35,110.95),(102.675,108.225)]:
 key=str(q);out[key]={}
 for l in [k.In1_Cu,k.In4_Cu]:
  out[key][b.GetLayerName(l)]={'center':inside(q,l),'rings':{str(r):sum(inside((q[0]+r*math.cos(a*math.pi/180),q[1]+r*math.sin(a*math.pi/180)),l) for a in range(360)) for r in [.11,.2,.225,.25,.3,.4,.5,1]}}
print('RINGS',json.dumps(out),flush=True)
rows=[]
for t in b.GetTracks():
 if t.GetClass()=='PCB_TRACK' and t.GetNetname()=='3V3_SENS' and t.GetLayer()==k.In2_Cu:
  a,z=xy(t.GetStart()),xy(t.GetEnd());le=math.dist(a,z);n=math.ceil(le/.025);dx=(z[0]-a[0])/le;dy=(z[1]-a[1])/le;bad={str(w):[] for w in [0,.0635,.15]}
  for i in range(n+1):
   d=le*i/n;c=(a[0]+d*dx,a[1]+d*dy)
   for w in [0,.0635,.15]:
    if not all(inside((c[0]-dy*v,c[1]+dx*v),k.In1_Cu) for v in [-w,0,w]):bad[str(w)].append(round(d,4))
  rows.append({'uuid':t.m_Uuid.AsString(),'a':a,'z':z,'length':le,'sample_count':n+1,'bad_distances':bad})
out['sensor']=rows
for ref in ['C9','C1','C21','C24','U1','U5']:
 f=next(f for f in b.GetFootprints() if f.GetReference()==ref)
 print('PADS',ref,[(p.GetNumber(),p.GetNetname(),xy(p.GetPosition())) for p in f.Pads() if ref not in ['U1','U5'] or p.GetNetname()=='GND'],flush=True)
print('LOCALGND',[(t.m_Uuid.AsString(),b.GetLayerName(t.GetLayer()),xy(t.GetStart()),xy(t.GetEnd()),t.GetWidth()/1e6) for t in b.GetTracks() if t.GetClass()=='PCB_TRACK' and t.GetNetname()=='GND' and 100< t.GetStart().x/1e6<108.5 and 104<t.GetStart().y/1e6<117 and 100<t.GetEnd().x/1e6<108.5 and 104<t.GetEnd().y/1e6<117],flush=True)
json.dump(out,open('/workspace/shared/nexus-main-placement-fix/stage35/verification/returns/plane-proof.json','w'),indent=2)
print('SENSOR',json.dumps(rows),flush=True)
