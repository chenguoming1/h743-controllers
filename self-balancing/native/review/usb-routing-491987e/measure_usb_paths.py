"""Independent pad-center routed-length graph, with actual barrel Z length.
Does not estimate internal IC/package/cable delay or certify signal integrity.
"""
import pcbnew as p,json,math,heapq,sys,hashlib,collections
from pathlib import Path
src=Path(sys.argv[1]);out=Path(sys.argv[2]);b=p.LoadBoard(str(src));th=p.ToMM(b.GetDesignSettings().GetBoardThickness())
def xy(q):return (round(p.ToMM(q.x),9),round(p.ToMM(q.y),9))
def node(pt,l):return(round(pt[0],6),round(pt[1],6),l)
def project(q,a,z):
 dx,dy=z[0]-a[0],z[1]-a[1];den=dx*dx+dy*dy;t=((q[0]-a[0])*dx+(q[1]-a[1])*dy)/den if den else 0
 return t,(a[0]+t*dx,a[1]+t*dy)
usb=lambda n:any(x in n for x in ['USB_CONN_','USB_ESD_','USB_MCU_'])
tracks=[t for t in b.GetTracks() if usb(t.GetNetname()) and not isinstance(t,p.PCB_VIA)]
vias=[v for v in b.GetTracks() if usb(v.GetNetname()) and isinstance(v,p.PCB_VIA)]
pads=[(f,pad) for f in b.GetFootprints() for pad in f.Pads() if usb(pad.GetNetname())]
G=collections.defaultdict(list);coords=collections.defaultdict(set);padnodes={};totals=collections.defaultdict(float)
def edge(a,z,dist,kind,uuid=''):
 G[a].append((z,dist,kind,uuid));G[z].append((a,dist,kind,uuid))
for t in tracks:
 key=(t.GetNetname(),t.GetLayer());coords[key]|={xy(t.GetStart()),xy(t.GetEnd())};totals[key[0]]+=p.ToMM(t.GetLength())
for v in vias:
 for l in (p.F_Cu,p.B_Cu):coords[v.GetNetname(),l].add(xy(v.GetPosition()))
 edge(node(xy(v.GetPosition()),p.F_Cu),node(xy(v.GetPosition()),p.B_Cu),th,'barrel',v.m_Uuid.AsString())
for f,pad in pads:
 l=f.GetLayer();pt=xy(pad.GetPosition());key=(pad.GetNetname(),l);coords[key].add(pt);padnodes[f.GetReference()+'.'+pad.GetNumber()]=node(pt,l)
# Split true centerline intersections, including mid-segment branches.
for i,t in enumerate(tracks):
 a,z=xy(t.GetStart()),xy(t.GetEnd());u=(z[0]-a[0],z[1]-a[1])
 for s in tracks[i+1:]:
  if s.GetNetname()!=t.GetNetname() or s.GetLayer()!=t.GetLayer():continue
  c,d=xy(s.GetStart()),xy(s.GetEnd());v=(d[0]-c[0],d[1]-c[1]);den=u[0]*v[1]-u[1]*v[0]
  if abs(den)<1e-12:continue
  w=(c[0]-a[0],c[1]-a[1]);ta=(w[0]*v[1]-w[1]*v[0])/den;tb=(w[0]*u[1]-w[1]*u[0])/den
  if -1e-7<=ta<=1+1e-7 and -1e-7<=tb<=1+1e-7:coords[t.GetNetname(),t.GetLayer()].add((a[0]+ta*u[0],a[1]+ta*u[1]))
for t in tracks:
 a,z=xy(t.GetStart()),xy(t.GetEnd());l=t.GetLayer();pts=[]
 for q in coords[t.GetNetname(),l]:
  u,r=project(q,a,z)
  if -1e-7<=u<=1+1e-7 and math.dist(q,r)<2e-6:pts.append((u,q))
 pts.sort()
 for (_,q),(_,r) in zip(pts,pts[1:]):edge(node(q,l),node(r,l),math.dist(q,r),'planar',t.m_Uuid.AsString())
# Conductive pad metal ties together all centerline anchors physically inside it.
for f,pad in pads:
 l=f.GetLayer();center=xy(pad.GetPosition());pn=node(center,l)
 for q in coords[pad.GetNetname(),l]:
  if pad.HitTest(p.VECTOR2I(p.FromMM(q[0]),p.FromMM(q[1]))):
   qn=node(q,l)
   if pn!=qn:edge(pn,qn,math.dist(center,q),'pad-center')
def shortest(a,z):
 start,end=padnodes[a],padnodes[z];Q=[(0,start)];dist={start:0};prev={}
 while Q:
  cost,n=heapq.heappop(Q)
  if cost!=dist[n]:continue
  if n==end:break
  for nxt,w,kind,uid in G[n]:
   c=cost+w
   if c<dist.get(nxt,math.inf):dist[nxt]=c;prev[nxt]=(n,kind,w,uid);heapq.heappush(Q,(c,nxt))
 if end not in dist:raise RuntimeError('No path '+a+' -> '+z)
 path=[];n=end
 while n!=start:
  last,kind,w,uid=prev[n];path.append(dict(a=list(last),b=list(n),kind=kind,length_mm=w,uuid=uid));n=last
 path.reverse();return dict(start=a,end=z,total_mm=dist[end],planar_mm=sum(x['length_mm'] for x in path if x['kind']!='barrel'),barrel_mm=sum(x['length_mm'] for x in path if x['kind']=='barrel'),barrel_count=sum(x['kind']=='barrel' for x in path),path=path)
routes={}
for key,a,z in [('conn_A_P','J2.A6','U4.3'),('conn_A_N','J2.A7','U4.1'),('conn_B_P','J2.B6','U4.3'),('conn_B_N','J2.B7','U4.1'),('esd_P','U4.4','R8.1'),('esd_N','U4.6','R7.1'),('mcu_P','R8.2','U1.71'),('mcu_N','R7.2','U1.70')]:routes[key]=shortest(a,z)
pairs={}
for part in ('conn_A','conn_B','esd','mcu'):
 P,N=routes[part+'_P']['total_mm'],routes[part+'_N']['total_mm'];pairs[part]=dict(P_mm=P,N_mm=N,skew_N_minus_P_mm=N-P)
endtoend={}
for orient in ('A','B'):
 P=sum(routes[k]['total_mm'] for k in ('conn_'+orient+'_P','esd_P','mcu_P'));N=sum(routes[k]['total_mm'] for k in ('conn_'+orient+'_N','esd_N','mcu_N'));endtoend[orient]=dict(P_mm=P,N_mm=N,skew_N_minus_P_mm=N-P)
report=dict(source_sha256=hashlib.sha256(src.read_bytes()).hexdigest(),board_thickness_mm=th,method='Shortest connected centerline route from named pad center to pad center; actual 1.5384 mm board thickness per F/B barrel. Pad-center conductive links included. Internal ESD, resistor, MCU, connector and cable delay excluded; this is geometric length, not measured electrical delay.',net_planar_copper_mm=totals,pairs=pairs,end_to_end_external_copper=endtoend,routes=routes)
out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'pairs':pairs,'end_to_end':endtoend},indent=2))
