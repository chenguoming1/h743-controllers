"""Native read-only projected saved-fill coverage; not a return-current/impedance proof."""
import pcbnew as k,json,math,sys,collections,hashlib
from pathlib import Path
xy=lambda p:(p.x/1e6,p.y/1e6)
vec=lambda q:k.VECTOR2I(round(q[0]*1e6),round(q[1]*1e6))
src=Path(sys.argv[1]);outpath=Path(sys.argv[2]);b=k.LoadBoard(str(src));zones={l:[z.GetFilledPolysList(l) for z in b.Zones() if z.GetLayer()==l and z.GetNetname()=='GND'] for l in [k.F_Cu,k.In1_Cu,k.In2_Cu,k.In4_Cu]};out=[]
for t in b.GetTracks():
 if t.GetNetname() not in ['USB_DP','USB_DM','USB_DN'] or t.GetClass()=='PCB_VIA':continue
 a,z=xy(t.GetStart()),xy(t.GetEnd());L=t.GetLength()/1e6;N=max(1,math.ceil(L/.01));w=t.GetWidth()/1e6;layer=t.GetLayer();refs=[k.In1_Cu] if layer==k.F_Cu else [k.In4_Cu] if layer==k.B_Cu else [k.In2_Cu,k.In4_Cu] if layer==k.In3_Cu else [k.F_Cu,k.In2_Cu] if layer==k.In1_Cu else []
 if not refs:continue
 if t.GetClass()=='PCB_ARC':
  c=xy(t.GetCenter());m=xy(t.GetMid());r=math.dist(c,a);th0=math.atan2(a[1]-c[1],a[0]-c[0]);th1=math.atan2(z[1]-c[1],z[0]-c[0]);thm=math.atan2(m[1]-c[1],m[0]-c[0]);sw=(th1-th0)%(2*math.pi)
  if (thm-th0)%(2*math.pi)>sw+1e-6:sw-=2*math.pi
  def sample(f):
   th=th0+f*sw;nx,ny=math.cos(th),math.sin(th);return (c[0]+r*nx,c[1]+r*ny),(nx,ny)
 else:
  dx,dy=z[0]-a[0],z[1]-a[1];length=math.hypot(dx,dy)
  def sample(f):return (a[0]+f*dx,a[1]+f*dy),(-dy/length,dx/length)
 for ref in refs:
  bad_center=bad_edges=0;badpts=[]
  for i in range(N):
   p,n=sample((i+.5)/N);ps=[p,(p[0]+n[0]*w/2,p[1]+n[1]*w/2),(p[0]-n[0]*w/2,p[1]-n[1]*w/2)];inside=[any(poly.Contains(vec(q)) for poly in zones[ref]) for q in ps]
   if not inside[0]:bad_center+=1
   if not all(inside):bad_edges+=1;badpts.append(p)
  out.append(dict(uuid=t.m_Uuid.AsString(),net=t.GetNetname(),layer=b.GetLayerName(layer),reference=b.GetLayerName(ref),width_mm=w,length_mm=L,center_uncovered_mm=bad_center/N*L,center_or_edge_uncovered_mm=bad_edges/N*L,uncovered_examples=badpts[::max(1,len(badpts)//4)][:5]))
summary={}
for row in out:
 key=' '.join([row['net'],row['layer'],row['reference'],'matched_trunk' if row['width_mm']==.17 else 'launch'])
 s=summary.setdefault(key,dict(length_mm=0,center_uncovered_mm=0,center_or_edge_uncovered_mm=0))
 for k1 in s:s[k1]+=row[k1]
result=dict(source=str(src),sha256=hashlib.sha256(src.read_bytes()).hexdigest(),native_version=k.GetBuildVersion(),method='KiCad saved zone SHAPE_POLY_SET.Contains on center and both copper edges at <=0.010 mm midpoint steps. No refill; coverage describes the named source and its saved fill only. No continuous-return/contact/impedance qualification.',summary=summary,segments=out);outpath.write_text(json.dumps(result,indent=2));print(json.dumps(summary,indent=2))
