"""Read-only S-expression + numerical geometry inspection. No KiCad imports, board writes, or routing solver."""
from pathlib import Path
import re, json, math, hashlib, collections, heapq, itertools, os
os.environ["MPLCONFIGDIR"]="/tmp/nexus-usb-mpl"
import numpy as np
from matplotlib.path import Path as MPath
S=Path('/workspace/scratch/8a35c1f26232/nexus-recovery-20261015/c19-integration/experimental-r43/hardware/nexus-style-fc.kicad_pcb')
D=Path('/workspace/shared/nexus-usb-stack-review')
H='10c4da72046f311a0ad61ac150091573966c8d9fae70fa93a57402a568d059c5'
assert hashlib.sha256(S.read_bytes()).hexdigest()==H
# All atoms kept as strings so no hidden native KiCad dependency.
def parse(s):
 stack=[]; root=None
 for t in re.findall(r'\(|\)|"(?:\\.|[^"\\])*"|[^\s()]+',s):
  if t=='(':
   n=[]
   if stack:stack[-1].append(n)
   stack.append(n)
  elif t==')':
   root=stack.pop()
  else:stack[-1].append(json.loads(t) if t.startswith('"') else t)
 assert not stack
 return root
b=parse(S.read_text())
def allc(n,key):return [x for x in n if isinstance(x,list) and x and x[0]==key]
def one(n,key,default=None):
 r=allc(n,key)
 return r[0] if r else default
def val(n,key,default=None):
 r=one(n,key)
 return r[1] if r and len(r)>1 else default
def vec(n,key):return list(map(float,one(n,key)[1:3]))
ls=[x[1] for x in one(b,'layers')[1:] if isinstance(x,list) and x[1].endswith('.Cu')]
pads=[];tracks=[];vias=[];fills=collections.defaultdict(list);fill_ids=collections.defaultdict(list)
for f in allc(b,'footprint'):
 ref=next(x[2] for x in allc(f,'property') if x[1]=='Reference');value=next(x[2] for x in allc(f,'property') if x[1]=='Value')
 at=one(f,'at')[1:];x,y=map(float,at[:2]);angle=float(at[2]) if len(at)>2 else 0
 c,s=math.cos(math.radians(angle)),math.sin(math.radians(angle))
 for p in allc(f,'pad'):
  px,py=vec(p,'at');pa=one(p,'at')[1:];a=float(pa[2]) if len(pa)>2 else 0
  pads.append(dict(kind='pad',ref=ref,value=value,pin=p[1],type=p[2],shape=p[3],net=val(p,'net'),at=[round(x+c*px+s*py,9),round(y-s*px+c*py,9)],size=vec(p,'size'),rotation=a,layer=val(f,'layer'),layers=one(p,'layers')[1:],uuid=val(p,'uuid')))
for s in allc(b,'segment'):
 tracks.append(dict(kind='segment',net=val(s,'net'),start=vec(s,'start'),end=vec(s,'end'),width=float(val(s,'width')),layer=val(s,'layer'),uuid=val(s,'uuid'),length_mm=math.dist(vec(s,'start'),vec(s,'end'))))
for s in allc(b,'via'):
 vias.append(dict(kind='via',net=val(s,'net'),at=vec(s,'at'),diameter=float(val(s,'size')),drill=float(val(s,'drill')),layers=one(s,'layers')[1:],uuid=val(s,'uuid')))
for z in allc(b,'zone'):
 if val(z,'net')!='GND':continue
 for fi,f in enumerate(allc(z,'filled_polygon')):
  pts=[list(map(float,x[1:3])) for x in one(f,'pts')[1:] if isinstance(x,list)]
  fills[val(f,'layer')].append(pts)
  fill_ids[val(f,'layer')].append({'zone_uuid':val(z,'uuid'),'filled_polygon_index_within_zone':fi,'layer':val(f,'layer'),'id':val(z,'uuid')+':'+str(fi)})
stack=[];dep=0;zcenters={}
for x in allc(one(one(b,'setup'),'stackup'),'layer'):
 r={'layer':x[1],'type':val(x,'type'),'thickness_mm':float(val(x,'thickness',0)),'epsilon_r':float(val(x,'epsilon_r',0)) or None,'material':val(x,'material')}
 stack.append(r)
 if x[1].endswith('.Cu') or x[1].startswith('dielectric'):
  if x[1].endswith('.Cu'):zcenters[x[1]]=dep+r['thickness_mm']/2
  dep+=r['thickness_mm']
usbtracks=[t for t in tracks if t['net'] in ('USB_DP','USB_DM')];usbvias=[v for v in vias if v['net'] in ('USB_DP','USB_DM')]
usbparts=[p for p in pads if p['ref'] in ('J6','U7','C25','C28') or p['net'] in ('USB_DP','USB_DM')]
# Pure projected-centerline graph. Report synthetic contact distances separately.
def project(p,a,b):
 d=np.array(b)-a;v=np.dot(np.array(p)-a,d)/np.dot(d,d);v=min(1,max(0,v));q=np.array(a)+v*d
 return v,q.tolist(),math.dist(p,q)
def node(p,l):return (round(p[0],9),round(p[1],9),l)
def graph(net):
 ts=[t for t in usbtracks if t['net']==net];vs=[v for v in usbvias if v['net']==net];ps=[p for p in pads if p['net']==net]
 adj=collections.defaultdict(list);splits={t['uuid']:{0: t['start'],1:t['end']} for t in ts}; joins=[]
 def edge(a,b,w,u,kind):
  if a==b:return
  adj[a].append((b,w,u,kind));adj[b].append((a,w,u,kind))
 for t in ts:
  for e in ('start','end'):
   a=t[e]
   for u in ts:
    if t==u or t['layer']!=u['layer']:continue
    frac,p,d=project(a,u['start'],u['end'])
    if d<=(t['width']+u['width'])/2+1e-8:
     splits[u['uuid']][frac]=p;joins.append((node(a,t['layer']),node(p,u['layer']),d,t['uuid']+'|'+u['uuid'],'near-endpoint-contact'))
 for v in vs:
  for t in ts:
   frac,p,d=project(v['at'],t['start'],t['end'])
   if d<=v['diameter']/2+t['width']/2+1e-8:
    splits[t['uuid']][frac]=p;joins.append((node(v['at'],t['layer']),node(p,t['layer']),d,v['uuid'],'via-contact'))
  for a,e in zip(ls,ls[1:]):edge(node(v['at'],a),node(v['at'],e),abs(zcenters[a]-zcenters[e]),v['uuid'],'barrel')
 for p in ps:
  # This PCB's USB pad entry is at a pad center or coincident segment endpoint.
  for t in ts:
   if t['layer'] not in p['layers'] and '*.Cu' not in p['layers']:continue
   frac,pt,d=project(p['at'],t['start'],t['end'])
   if d<1e-6:
    splits[t['uuid']][frac]=pt;joins.append((node(p['at'],t['layer']),node(pt,t['layer']),d,p['uuid'],'pad-center'))
 for t in ts:
  ss=sorted(splits[t['uuid']].items())
  for (_,a),(_,e) in zip(ss,ss[1:]):edge(node(a,t['layer']),node(e,t['layer']),math.dist(a,e),t['uuid'],'track')
 for a,e,w,u,k in joins:edge(a,e,w,u,k)
 return adj

def path(net,src,sp,dst,dp):
 ps=[p for p in pads if p['net']==net]
 a=next(p for p in ps if (p['ref'],p['pin'])==(src,sp));e=next(p for p in ps if (p['ref'],p['pin'])==(dst,dp));adj=graph(net);root=node(a['at'],a['layer']);end=node(e['at'],e['layer'])
 counter=itertools.count();heap=[(0,next(counter),root,[])];seen=set()
 while heap:
  cost,_,n,pth=heapq.heappop(heap)
  if n in seen:continue
  seen.add(n)
  if n==end:
   layers=collections.defaultdict(float);trans=[]
   for r in pth:
    if r['kind']=='track':layers[r['a'][2]]+=r['length_mm']
    if r['kind']=='barrel' and r['uuid'] not in trans:trans.append(r['uuid'])
   return dict(net=net,source=src+'.'+sp,target=dst+'.'+dp,track_centerline_mm=sum(layers.values()),layers_mm=dict(layers),barrel_mm=sum(r['length_mm'] for r in pth if r['kind']=='barrel'),synthetic_contact_mm=sum(r['length_mm'] for r in pth if r['kind'] not in ('track','barrel')),geometric_sum_mm=cost,via_count=len(trans),via_uuids=trans,path=pth)
  for nn,w,u,k in adj[n]:
   if nn not in seen:heapq.heappush(heap,(cost+w,next(counter),nn,pth+[dict(a=n,b=nn,length_mm=w,uuid=u,kind=k)]))
 return {'net':net,'source':src+'.'+sp,'target':dst+'.'+dp,'status':'no exact centerline/contact path; not electrical-open diagnosis'}
paths=[]
for net,mc,cp in [('USB_DP','45',('A6','B6')),('USB_DM','44',('A7','B7'))]:
 for p in cp:paths.append(path(net,'J6',p,'U1',mc))
 paths.append(path(net,'J6',cp[0],'J6',cp[1]))
 for pin in (('3','4') if net=='USB_DP' else ('1','6')):
  paths.append(path(net,'J6',cp[0],'U7',pin))
# Post-refill polygons are static evidence only, no new fill computed.
mpaths={l:[MPath(np.array(p)) for p in pp] for l,pp in fills.items()}
def inside(points,layer):
 out=np.zeros(len(points),dtype=bool)
 for p in mpaths[layer]:out|=p.contains_points(points,radius=1e-10)
 return out
coverage=[]
for t in usbtracks:
 L=t['length_mm'];n=max(1,math.ceil(L/.01));ss=(np.arange(n)+.5)/n
 a=np.array(t['start']);b=np.array(t['end']);ps=a[None,:]+ss[:,None]*(b-a)[None,:];tangent=(b-a)/L;normal=np.array([-tangent[1],tangent[0]])
 refs=['In1.Cu'] if t['layer']=='F.Cu' else ['In4.Cu'] if t['layer']=='B.Cu' else ['In1.Cu','In2.Cu','In4.Cu']
 for ref in refs:
  good=inside(ps,ref);edgea=inside(ps+normal*t['width']/2,ref);edgeb=inside(ps-normal*t['width']/2,ref)
  bad=[];s=None
  for i,v in enumerate(list(good)+[True]):
   if not v and s is None:s=i
   elif v and s is not None:
    bad.append({'length_mm':(i-s)/n*L,'start':(a+(s/n)*(b-a)).tolist(),'end':(a+(i/n)*(b-a)).tolist()});s=None
  touch_points=np.concatenate([ps,ps+normal*t['width']/2,ps-normal*t['width']/2]);touched=[fill_ids[ref][pi] for pi,poly in enumerate(mpaths[ref]) if poly.contains_points(touch_points,radius=1e-10).any()]
  coverage.append(dict(projected_saved_polygon_ids=touched,net=t['net'],uuid=t['uuid'],layer=t['layer'],reference=ref,length_mm=L,sample_spacing_mm=L/n,samples=n,uncovered_length_midpoint_estimate_mm=(~good).sum()*L/n,uncovered_intervals=bad,edge_uncovered_length_midpoint_estimate_mm=(~(edgea&edgeb)).sum()*L/n))
# Parallel-pair evidence: run lengths with exactly parallel opposite-net lines. Also sample nearest on same layer.
parallel=[];pair_samples=[]
for t in usbtracks:
 opp=[u for u in usbtracks if u['net']!=t['net'] and u['layer']==t['layer']]
 a=np.array(t['start']);e=np.array(t['end']);L=t['length_mm'];d=(e-a)/L
 for u in opp:
  if t['net']!='USB_DP':continue
  q=np.array(u['start']);r=np.array(u['end']);du=(r-q)/u['length_mm']
  if abs((d[0]*du[1]-d[1]*du[0]))>1e-6:continue
  off=abs((d[0]*(q-a)[1]-d[1]*(q-a)[0]));starts=sorted([np.dot(q-a,d),np.dot(r-a,d)]);lo=max(0,starts[0]);hi=min(L,starts[1]);ol=max(0,hi-lo)
  if ol>1e-6:parallel.append(dict(dp_uuid=t['uuid'],dm_uuid=u['uuid'],layer=t['layer'],overlap_mm=ol,center_spacing_mm=off,edge_gap_mm=off-(t['width']+u['width'])/2))
 n=max(1,math.ceil(L/.01))
 for i in range(n):
  p=(a+(i+.5)/n*(e-a)).tolist();best=None
  for u in opp:
   frac,q,dist=project(p,u['start'],u['end']);du=(np.array(u['end'])-u['start'])/u['length_mm'];ang=math.degrees(math.acos(min(1,abs(float(np.dot(d,du))))))
   row=dict(net=t['net'],layer=t['layer'],uuid=t['uuid'],at=p,weight_mm=L/n,opposite_uuid=u['uuid'],center_distance_mm=dist,edge_gap_mm=dist-(t['width']+u['width'])/2,local_angle_deg=ang,opposite_projection_interior=(0<frac<1))
   if best is None or dist<best['center_distance_mm']:best=row
  if best:pair_samples.append(best)
summary={}
for net in ['USB_DP','USB_DM']:
 ts=[t for t in usbtracks if t['net']==net];s={'track_count':len(ts),'via_count':sum(v['net']==net for v in usbvias),'total_track_centerline_mm':sum(t['length_mm'] for t in ts),'layer_sums_mm':{},'widths_mm':sorted(set(t['width'] for t in ts))}
 for l in ls:s['layer_sums_mm'][l]=sum(t['length_mm'] for t in ts if t['layer']==l)
 rows=[x for x in pair_samples if x['net']==net];tot=sum(x['weight_mm'] for x in rows)
 s['nearest_opposite_same_layer_pairing']={'definition':'Track midpoint sampling <=0.010 mm; close+aligned = edge gap <=0.250 mm, absolute local angle <=10 degrees, opposite projection interior; descriptive only, not an impedance rule.','sampled_track_mm':tot,'close_aligned_mm':sum(x['weight_mm'] for x in rows if x['edge_gap_mm']<=.25 and x['local_angle_deg']<=10 and x['opposite_projection_interior']),'nearest_gap_min_mm':min(x['edge_gap_mm'] for x in rows),'nearest_gap_max_mm':max(x['edge_gap_mm'] for x in rows)}
 summary[net]=s
report=dict(board_path=str(S),board_sha256=H,analysis_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),method='Static S-expression parsing; NumPy line projections and Matplotlib polygon containment, no native KiCad operation.',stack=stack,copper_center_z_mm=zcenters,stack_copper_dielectric_sum_mm=dep,saved_fill_polygon_id_definition='zone UUID plus zero-based filled_polygon occurrence within that zone in exact source. IDs indicate sampled projected membership, not proof of finite 3D return connectivity.',parts=usbparts,usb_tracks=usbtracks,usb_vias=usbvias,summary=summary,paths=paths,stored_fill_reference_coverage=coverage,exact_parallel_overlaps=parallel,limits=['Path lengths are geometric centerline estimates, exclude package/cable electrical delay. Synthetic contacts account for noncoincident copper endpoints.','No native DRC rerun, no field solver, no fabrication qualification.','Reference check projects track center and two edges into saved filled GND polygons. Via antipads and line terminations are included; sampling is not a continuous return-path/EM validation.'])
assert hashlib.sha256(S.read_bytes()).hexdigest()==H
(D/'geometry-evidence.json').write_text(json.dumps(report,indent=2,default=lambda v:v.item() if hasattr(v,'item') else v)+'\n')
print(json.dumps({'summary':summary,'paths':[{k:v for k,v in x.items() if k!='path'} for x in paths],'stack':stack,'pads':[p for p in usbparts if p['net'] in ('USB_DP','USB_DM')]},indent=2))
