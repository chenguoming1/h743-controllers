"""Exact finite-line/circle/rectangle/arc checks of in-memory child transaction.
Read only. No board output, native runtime, solver or filled-zone inference.
"""
import math,json,hashlib,sys,copy
from pathlib import Path
sys.dont_write_bytecode=True
OUT=Path(__file__).resolve().parent
sys.path.insert(0,str(OUT.parent/'candidate-02/nexus-style-fc/tools'));import sexpr as s
P=json.loads((OUT/'complete-transaction.json').read_text());raw=Path(P['source']['path']).read_bytes();assert hashlib.sha256(raw).hexdigest()==P['source']['sha256'];B=s.parse(raw.decode())
def one(n,k):return s.find(n,k)[0]
def txt(n,k):return s.text(one(n,k)[-1])
def uid(n):return txt(n,'uuid')
def xy(n,k):return tuple(map(float,one(n,k)[1:3]))
def ref(f):return next(s.text(p[2]) for p in s.find(f,'property') if s.text(p[1])=='Reference')
def sub(a,b):return a[0]-b[0],a[1]-b[1]
def add(a,b):return a[0]+b[0],a[1]+b[1]
def mul(a,t):return a[0]*t,a[1]*t
def dot(a,b):return a[0]*b[0]+a[1]*b[1]
def length(a):return math.hypot(*a)
def pointseg(p,a,b):
 d=sub(b,a);den=dot(d,d);t=max(0,min(1,dot(sub(p,a),d)/den)) if den else 0;return length(sub(p,add(a,mul(d,t))))
def cross(a,b):return a[0]*b[1]-a[1]*b[0]
def segseg(a,b,c,d):
 u,v=sub(b,a),sub(d,c);den=cross(u,v)
 if abs(den)>1e-12:
  t=cross(sub(c,a),v)/den;z=cross(sub(c,a),u)/den
  if -1e-10<=t<=1+1e-10 and -1e-10<=z<=1+1e-10:return 0.
 return min(pointseg(a,c,d),pointseg(b,c,d),pointseg(c,a,b),pointseg(d,a,b))
def inrect(p,r):return r[0]<=p[0]<=r[2] and r[1]<=p[1]<=r[3]
def segrect(a,b,r):
 if inrect(a,r) or inrect(b,r):return 0.
 q=[(r[0],r[1]),(r[2],r[1]),(r[2],r[3]),(r[0],r[3])];return min(segseg(a,b,q[i],q[(i+1)%4]) for i in range(4))
def circle(e):
 a,m,b=[xy(e,k) for k in ('start','mid','end')];u,v=sub(m,a),sub(b,a);d=2*cross(u,v);uu,vv=dot(u,u),dot(v,v)
 c=add(a,((uu*v[1]-vv*u[1])/d,(u[0]*vv-v[0]*uu)/d));return c,length(sub(a,c))
def arc_angles(e):
 c,r=circle(e);angle=lambda p:math.atan2(p[1]-c[1],p[0]-c[0]);a,m,b=[angle(xy(e,k)) for k in ('start','mid','end')];sweep=(b-a)%(2*math.pi)
 if (m-a)%(2*math.pi)>sweep:a=b;sweep=(angle(xy(e,'start'))-a)%(2*math.pi)
 return c,r,a,sweep

def segarc(a,b,e):
 c,r,start,sweep=arc_angles(e)
 def on(p):return (math.atan2(p[1]-c[1],p[0]-c[0])-start)%(2*math.pi)<=sweep+1e-9
 ends=[xy(e,k) for k in ('start','end')];candidates=[pointseg(p,a,b) for p in ends]
 for p in (a,b):
  candidates.extend(length(sub(p,x)) for x in ends)
  if on(p):candidates.append(abs(length(sub(p,c))-r))
 v=sub(b,a);ll=dot(v,v)
 if ll:
  vn=(-v[1]/math.sqrt(ll),v[0]/math.sqrt(ll))
  for sign in (-1,1):
   p=add(c,mul(vn,sign*r));t=dot(sub(p,a),v)/ll
   if 0<=t<=1 and on(p):candidates.append(pointseg(p,a,b))
  ac=sub(a,c);bb=2*dot(ac,v);cc=dot(ac,ac)-r*r;disc=bb*bb-4*ll*cc
  if disc>=0:
   for t in ((-bb-math.sqrt(disc))/(2*ll),(-bb+math.sqrt(disc))/(2*ll)):
    if 0<=t<=1 and on(add(a,mul(v,t))):candidates.append(0.)
 return min(candidates)

def copper_objects(board):
 objects=[]
 for n in s.find(board,'segment'):
  objects.append({'id':uid(n),'kind':'segment','net':txt(n,'net'),'layers':{txt(n,'layer')},'a':xy(n,'start'),'b':xy(n,'end'),'r':float(one(n,'width')[1])/2})
 for n in s.find(board,'via'):
  objects.append({'id':uid(n),'kind':'circle','net':txt(n,'net'),'layers':{'F.Cu','B.Cu'},'c':xy(n,'at'),'r':float(one(n,'size')[1])/2,'drill':float(one(n,'drill')[1])/2})
 for f in s.find(board,'footprint'):
  for n in s.find(f,'pad'):
   if not s.find(n,'net'):continue
   c=add(xy(f,'at'),xy(n,'at'));w,h=xy(n,'size');layers={s.text(v) for v in one(n,'layers')[1:]};layers={'F.Cu','B.Cu'} if '*.Cu' in layers else layers&{'F.Cu','B.Cu'}
   d={'id':uid(n),'kind':'circle' if s.text(n[3])=='circle' else 'rect','net':txt(n,'net'),'layers':layers,'c':c,'r':w/2,'rect':(c[0]-w/2,c[1]-h/2,c[0]+w/2,c[1]+h/2),'ref':ref(f),'pad':s.text(n[1])}
   assert s.text(n[3]) in ('rect','circle')
   if s.find(n,'drill'):d['drill']=float(one(n,'drill')[1])/2
   objects.append(d)
 return objects

def gap(a,b):
 if not a['layers']&b['layers']:return math.inf
 if a['kind']!='segment' and b['kind']=='segment':return gap(b,a)
 if a['kind']=='segment':
  if b['kind']=='segment':return segseg(a['a'],a['b'],b['a'],b['b'])-a['r']-b['r']
  if b['kind']=='circle':return pointseg(b['c'],a['a'],a['b'])-a['r']-b['r']
  return segrect(a['a'],a['b'],b['rect'])-a['r']
 if a['kind']=='circle' and b['kind']=='circle':return length(sub(a['c'],b['c']))-a['r']-b['r']
 if a['kind']=='rect' and b['kind']=='circle':return gap(b,a)
 if a['kind']=='circle':
  p=a['c'];r=b['rect'];return math.hypot(max(r[0]-p[0],p[0]-r[2],0),max(r[1]-p[1],p[1]-r[3],0))-a['r']
 r,t=a['rect'],b['rect'];return math.hypot(max(r[0]-t[2],t[0]-r[2],0),max(r[1]-t[3],t[1]-r[3],0))

def inside(p):
 x,y=p
 body=100<=x<=122.4 and 100<=y<=108.4
 if body and y>=107.9:
  body=all((x-c)**2+(y-108.4)**2>=.25-1e-12 for c in (100.9,110.3,112.1,121.5))
 tabs=108.4<=y<=111 and (101.4<=x<=109.8 or 112.6<=x<=121)
 # All proposed points are far below the unchanged upper corner arcs.
 return body or tabs

donors={d['uuid'] for r in P['routes'] for d in r['source_donor_segments']};new_nodes=[s.parse(n['native_record']) for r in P['routes'] for n in r['replacement_segments']]
for r in P['routes']:
 for d in r['source_donor_segments']:assert s.dump(next(n for n in s.find(B,'segment') if uid(n)==d['uuid']))==d['native_record']
C=copy.deepcopy(B);C[:]=[n for n in C if not(isinstance(n,list) and n[0]=='segment' and uid(n) in donors)];C+=new_nodes
assert len(s.find(C,'segment'))==73
for key in ('footprint','via','zone','gr_line','gr_arc','setup','general'):assert s.find(C,key)==s.find(B,key)
obs=copper_objects(C);oldobs=copper_objects(B);byid={o['id']:o for o in obs};edges=[n for n in C if isinstance(n,list) and n[0] in ('gr_line','gr_arc') and txt(n,'layer')=='Edge.Cuts']
checks=[]
for n in new_nodes:
 o=byid[uid(n)];a,b=o['a'],o['b'];assert inside(a) and inside(b)
 ed=[(segarc(a,b,e) if e[0]=='gr_arc' else segseg(a,b,xy(e,'start'),xy(e,'end')))-o['r'] for e in edges];i=min(range(len(ed)),key=ed.__getitem__)
 foreign=[(gap(o,q),q) for q in obs if q['net']!=o['net'] and o['layers']&q['layers']];fg,fq=min(foreign,key=lambda v:v[0])
 holes=[(pointseg(q['c'],a,b)-q['drill']-o['r'],q) for q in obs if 'drill' in q and q['net']!=o['net']];hg,hq=min(holes,key=lambda v:v[0])
 assert ed[i]>=.254-1e-8,(uid(n),'edge',ed[i]);assert fg>=.15-1e-8,(uid(n),'copper',fg,fq);assert hg>=.25-1e-8,(uid(n),'hole',hg,hq)
 checks.append({'uuid':uid(n),'net':o['net'],'width':2*o['r'],'edge_clearance_mm':ed[i],'nearest_edge_uuid':uid(edges[i]),'foreign_copper_clearance_mm':fg,'nearest_foreign_uuid':fq['id'],'nearest_foreign_net':fq['net'],'foreign_hole_clearance_mm':hg,'nearest_hole_uuid':hq['id']})

def comps(objects,nn):
 os=[o for o in objects if o['net']==nn];unseen=set(range(len(os)));components=[]
 while unseen:
  stack=[unseen.pop()];comp=[]
  while stack:
   i=stack.pop();comp.append(i)
   for j in list(unseen):
    if gap(os[i],os[j])<=1e-8:unseen.remove(j);stack.append(j)
  components.append({'objects':[os[i]['id'] for i in comp],'pads':[{'ref':os[i]['ref'],'pad':os[i]['pad'],'uuid':os[i]['id']} for i in comp if 'ref' in os[i]]})
 return components
connectivity={}
ports=[]
for r in P['routes']:
 nn=r['net'];oldc=comps(oldobs,nn);newc=comps(obs,nn);assert len(newc)==1,(nn,newc)
 connectivity[nn]={'source_components_without_zones':oldc,'proposed_components_without_zones':newc,'all_pads_count':sum(len(c['pads']) for c in newc)}
 olddon=[o for o in oldobs if o['id'] in {d['uuid'] for d in r['source_donor_segments']}];newdon=[byid[n['uuid']] for n in r['replacement_segments']]
 boundary=[]
 for q in oldobs:
  if q['net']!=nn or q['id'] in donors:continue
  old_gap=min(gap(o,q) for o in olddon);new_gap=min(gap(o,q) for o in newdon)
  if old_gap<=1e-8:assert new_gap<=1e-8,(nn,q,old_gap,new_gap)
  if old_gap<=1e-8 or new_gap<=1e-8:boundary.append({'external_uuid':q['id'],'kind':q['kind'],'reference':q.get('ref'),'pad':q.get('pad'),'old_gap':old_gap,'new_gap':new_gap,'preserved_or_new_terminal':'preserved' if old_gap<=1e-8 else 'new terminal connection'})
 ports.append({'net':nn,'external_contacts':boundary,'terminal':r['terminal_port']})
report={'status':'Read-only exact analytic line/arc/rectangle/circle checks; no native DRC or zone inference','source_sha256':P['source']['sha256'],'proposal_sha256':hashlib.sha256((OUT/'complete-transaction.json').read_bytes()).hexdigest(),'new_segments':checks,'minimum_new_route_edge_mm':min(c['edge_clearance_mm'] for c in checks),'minimum_new_route_foreign_copper_mm':min(c['foreign_copper_clearance_mm'] for c in checks),'minimum_new_route_foreign_hole_mm':min(c['foreign_hole_clearance_mm'] for c in checks),'connectivity_without_zones':connectivity,'external_port_accounting':ports,'unchanged_non_donor_objects':True,'native_and_refill_required':True}
(OUT/'static-verification.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'edge_min':report['minimum_new_route_edge_mm'],'foreign_min':report['minimum_new_route_foreign_copper_mm'],'hole_min':report['minimum_new_route_foreign_hole_mm'],'pads':{n:v['all_pads_count'] for n,v in connectivity.items()},'external_port_accounting':ports},indent=2))
