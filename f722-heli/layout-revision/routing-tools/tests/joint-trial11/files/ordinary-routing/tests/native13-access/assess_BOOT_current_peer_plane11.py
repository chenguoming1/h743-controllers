"""Complete SERVO1 donor restoration on isolated joint divider geometry."""
import hashlib,json,math,heapq,signal,time,sys
from pathlib import Path
START=time.monotonic()
sys.path.insert(0,str(Path(__file__).resolve().parent.parent/'portc51'))
import composite_native11_C_TX_WP as g
import shapely
from shapely.geometry import Point,LineString
from shapely.ops import polylabel
from shapely import unary_union
from shapely.strtree import STRtree
s=g.s;RES=.0001;layers=['B.Cu','In3.Cu','In2.Cu','F.Cu'];s.HALF=.0635
WHICH='BOOT';NET='BOOT0';s.OBJECTS=g.BASE

SERVO_FILE=g.H/'joint-divider-SERVO1-restore11.json';BOOT_FILE=g.H.parent/'boot56/joint57-adc-first.json'
servo=json.loads(SERVO_FILE.read_text());boot=json.loads(BOOT_FILE.read_text())['pinned_BOOT_entry'];assert servo['complete'] and boot['track']['passed']
# Corrected cluster already holds actual B-layer BOOT and complete SERVO1.
s.OBJECTS=list(g.BASE)
OBSOLETE={'9e6756f4-4622-4a5f-80e2-4c78e46894ce','d354ba09-c0ed-4352-9f87-8f6fa70ec378'}
# Verify exact contact ownership against this current composite before pruning.
contact_rows=[]
for uid in sorted(OBSOLETE):
 q=next(q for q in s.OBJECTS if q[0]['uuid']==uid)
 hits=[]
 for other in s.OBJECTS:
  if other[0]['uuid']==uid:continue
  if any(c.intersects(other[1][layer]) for layer,c in q[1].items() if layer in other[1]):hits.append(other[0]['uuid'])
 expected=({'d354ba09-c0ed-4352-9f87-8f6fa70ec378'} if q[0]['kind']=='via' else {'9e6756f4-4622-4a5f-80e2-4c78e46894ce','f0c78c2d-6c54-45da-a11d-287af10c7e04'})
 assert set(hits)==expected,(uid,hits)
 contact_rows.append({'uuid':uid,'exact_current_contacts':hits})
s.OBJECTS=[q for q in s.OBJECTS if q[0]['uuid']not in OBSOLETE]
OUT=g.H/'joint-BOOT-current-peer-plane-feasibility11.json'
out={'schema':'f722-complete-BOOT-joint-SERVO1-held11/v1','source':g.binding(),'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'routes':[],'vias':[],'complete':False,'reference_qualified':False,'native_candidate':False}
out['source']['all_native_objects_retained']=False
out['explicit_removed_native_records']=[g.by[u] for u in sorted(g.REMOVED_NATIVE_IDS)]
out['joint_overlay_sha256']=hashlib.sha256(Path(g.__file__).read_bytes()).hexdigest()
out['joint_source_binding']=g.binding()
out['restored_net']=NET
out['held_receipts']={str(p.relative_to(g.ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()for p in [SERVO_FILE,BOOT_FILE]}
out['corrected_ADC_three_terminal_cluster_held']=True
out['full_ADC_pending_B_divider']=True
out['obsolete_R42_pendant_contact_proof']=contact_rows
out['adoptable']=False
cross=[]
bootline=LineString(boot['track']['points']);bootvia=Point(18.983413,18.246418)
for r in servo['routes']:
 q=LineString(r['points']);cross.append({'type':'trace-trace','distance':bootline.distance(q),'minimum':boot['track']['width']/2+r['width']/2+.127});cross.append({'type':'BOOT-via-SERVO-trace','distance':bootvia.distance(q),'minimum':.225+r['width']/2+.127})
for v in servo['vias']:
 q=Point(v['xy']);cross.append({'type':'SERVO-via-BOOT-trace','distance':q.distance(bootline),'minimum':.225+boot['track']['width']/2+.127});cross.append({'type':'via-via','distance':q.distance(bootvia),'minimum':.577})
out['held_BOOT_SERVO_mutual_finite_clearance']=cross
assert all(x['distance']>=x['minimum']+s.ERROR for x in cross),cross
def save():out['seconds']=time.monotonic()-START;OUT.write_text(json.dumps(out,indent=2)+'\n')
def timeout(sig,frame):out['terminal_reason']='Bounded40second limit; incomplete results are diagnostic only';save();raise SystemExit(0)
signal.signal(signal.SIGALRM,timeout);signal.alarm(max(1,int(40-(time.monotonic()-START))))
def parts(x):return [p for p in (x.geoms if hasattr(x,'geoms') else [x]) if p.geom_type=='Polygon' and not p.is_empty]
def expanded(obs):return unary_union([o['geometry'].buffer((o['required_center_distance_mm']+s.ERROR+RES)/math.cos(math.pi/128),quad_segs=32) for o in obs if o['category']!='edge_npth_copper'])
def shortest(comp,A,B):
 if comp.covers(LineString([A,B])):return [A,B]
 tris=list(shapely.constrained_delaunay_triangles(comp).geoms);centers=[tuple(t.centroid.coords[0])for t in tris];edges={};adj=[{}for t in tris]
 for j,t in enumerate(tris):
  cc=list(t.exterior.coords)
  for a,b in zip(cc,cc[1:]):
   key=tuple(sorted((a,b)))
   if key in edges:
    k=edges[key];m=((a[0]+b[0])/2,(a[1]+b[1])/2);w=math.dist(centers[j],m)+math.dist(centers[k],m);adj[j][k]=(w,m);adj[k][j]=(w,m)
   else:edges[key]=j
 si=next(j for j,t in enumerate(tris)if t.covers(Point(A)));ei=next(j for j,t in enumerate(tris)if t.covers(Point(B)));q=[(0,si)];ds={si:0};prev={}
 while q:
  cost,j=heapq.heappop(q)
  if cost!=ds[j]:continue
  if j==ei:break
  for k,(w,_)in adj[j].items():
   nc=cost+w
   if nc<ds.get(k,math.inf):ds[k]=nc;prev[k]=j;heapq.heappush(q,(nc,k))
 assert ei in ds;seq=[ei]
 while seq[-1]!=si:seq.append(prev[seq[-1]])
 seq.reverse();raw=[A]
 for a,b in zip(seq,seq[1:]):raw.extend([centers[a],adj[a][b][1]])
 raw.extend([centers[ei],B]);p=[raw[0]];j=0
 while j<len(raw)-1:
  k=len(raw)-1
  while k>j+1 and not comp.covers(LineString([raw[j],raw[k]])):k-=1
  p.append(raw[k]);j=k
 return p
nodes=[];bylayer={};obstacles={};adj={}
for layer in layers:
 obs,vo,_=s.obstacles(NET,layer);obstacles[layer]=obs;free=s.OUTLINE.buffer(-.3175-s.ERROR-RES).difference(expanded(obs));bylayer[layer]=[]
 for p in parts(free):i=len(nodes);nodes.append((layer,p));bylayer[layer].append(i);adj[i]=[]
 print('LAYER',layer,len(bylayer[layer]),flush=True)
legal=s.OUTLINE.buffer(-.479-s.ERROR-RES).difference(expanded(vo));eligible={i:p.intersection(legal)for i,(l,p)in enumerate(nodes)};eligible={i:p for i,p in eligible.items()if not p.is_empty and p.area>1e-7}
for ai,la in enumerate(layers):
 for lb in layers[ai+1:]:
  ids=[i for i in bylayer[lb]if i in eligible]
  if not ids:continue
  tree=STRtree([eligible[i]for i in ids])
  for a in bylayer[la]:
   if a not in eligible:continue
   for j in tree.query(eligible[a],predicate='intersects'):
    b=ids[int(j)];pp=parts(eligible[a].intersection(eligible[b]));
    if not pp:continue
    p=max(pp,key=lambda p:p.area)
    if p.area<=1e-7:continue
    adj[a].append((b,p,None));adj[b].append((a,p,None))
for o,cu,ma,dr in s.OBJECTS:
 if o['kind']!='via' or o['net']!=NET:continue
 hit=[i for i,(l,p)in enumerate(nodes)if l in cu and p.covers(Point(o['xy']))]
 for i,a in enumerate(hit):
  for b in hit[i+1:]:adj[a].append((b,Point(o['xy']),o['uuid']));adj[b].append((a,Point(o['xy']),o['uuid']))
A={'xy':g.one_pad('U1.60')['xy']};B={'xy':g.one_pad('R2.1')['xy']}
START_LAYER='B.Cu';END_LAYER='F.Cu'
out['actual_native_junctions']={'start':A['xy'],'end':B['xy'],'start_layer':START_LAYER,'end_layer':END_LAYER}
starts={i for i in bylayer[START_LAYER]if nodes[i][1].covers(Point(A['xy']))};ends={i for i in bylayer[END_LAYER]if nodes[i][1].covers(Point(B['xy']))};q=[(0,i)for i in starts];heapq.heapify(q);ds={i:0 for i in starts};prev={};goal=None
while q:
 cost,j=heapq.heappop(q)
 if cost!=ds[j]:continue
 if j in ends:goal=j;break
 for k,p,existing in adj[j]:
  nc=cost+(0 if existing else 1)
  if nc<ds.get(k,math.inf):ds[k]=nc;prev[k]=(j,p,existing);heapq.heappush(q,(nc,k))
out['endpoint_component_summary']={'starts':[{'id':i,'area_mm2':nodes[i][1].area,'bounds':list(nodes[i][1].bounds),'legal_via_area_mm2':eligible.get(i,Point()).area}for i in starts],'ends':[{'id':i,'area_mm2':nodes[i][1].area,'bounds':list(nodes[i][1].bounds),'legal_via_area_mm2':eligible.get(i,Point()).area}for i in ends],'reachable_components':[{'id':i,'layer':nodes[i][0],'area_mm2':nodes[i][1].area,'legal_via_area_mm2':eligible.get(i,Point()).area}for i in ds]}
out['graph_connected']=goal is not None;save()
if goal is None:
 # Read-only isolated manufacturing-feasibility alternative. Ground fills are
 # intentionally not preserved as obstacles; a real native fill/return review is mandatory.
 origin=[18.983413,18.246418];MAX_PLANE_LENGTH=2.5
 endds={i:0 for i in ends};endq=[(0,i)for i in ends];heapq.heapify(endq)
 while endq:
  cost,j=heapq.heappop(endq)
  if cost!=endds[j]:continue
  for k,pp,ex in adj[j]:
   nc=cost+(0 if ex else 1)
   if nc<endds.get(k,math.inf):endds[k]=nc;heapq.heappush(endq,(nc,k))
 regions=sorted(parts(legal.intersection(Point(origin).buffer(MAX_PLANE_LENGTH,quad_segs=128))),key=lambda z:z.distance(Point(origin)))
 out['plane_bridge_scope']={'maximum_track_length_mm':MAX_PLANE_LENGTH,'allowed_layers':['In1.Cu','In4.Cu'],'origin_existing_BOOT_via':origin,'native_ground_layer_rule_would_fail_without_explicit_review':True,'new_GND_fill_and_power_VCAP_reference_required':True,'adopted':False}
 out['plane_bridge_trials']=[];selected=None
 critical={'HSE_IN','HSE_OUT','HSE_XTAL_OUT','VCAP','VCAP_CAP','IMU_CS','IMU_INT','IMU_MISO','IMU_MOSI','IMU_SCK','USB_N','USB_P','USB_CC1','USB_CC2','+3V3_ANALOG','+3V3_IMU'}
 for plane,adjacent in [('In1.Cu',['F.Cu','In2.Cu']),('In4.Cu',['In3.Cu','B.Cu'])]:
  po,_,_=s.obstacles(NET,plane);protect=unary_union([c[l]for o,c,m,d in s.OBJECTS if o['net']in critical for l in adjacent if l in c]);pfree=s.OUTLINE.buffer(-.3175-s.ERROR-RES).difference(expanded(po)).difference(protect.buffer(.1905+s.ERROR+RES));pcs=[z for z in parts(pfree)if z.covers(Point(origin))]
  if not pcs:out['plane_bridge_trials'].append({'layer':plane,'origin_available_with_critical_projection_reserve':False});continue
  pc=pcs[0]
  for reg in regions:
   candidates=parts(reg.intersection(pc).intersection(unary_union([nodes[i][1]for i in endds])))
   if not candidates:continue
   pp=max(candidates,key=lambda z:z.area);pt=polylabel(pp,tolerance=.0001);xy=[round(pt.x,6),round(pt.y,6)];hits=[i for i in endds if nodes[i][1].covers(Point(xy))]
   row={'layer':plane,'xy':xy,'ordinary_components_reaching_switch':hits};out['plane_bridge_trials'].append(row)
   if not hits:continue
   points=[[round(x,6),round(y,6)]for x,y in shortest(pc,origin,xy)];line=LineString(points);tc=s.check(line,po,True);vc=s.check(Point(xy),vo,True);row.update(points=points,length_mm=line.length,finite_pass=all(x['pass_with_polygon_error']for x in tc+vc),critical_projection_cut_empty=line.buffer(.1905+s.ERROR).intersection(protect).is_empty)
   if not(row['finite_pass']and row['critical_projection_cut_empty']and line.length<=MAX_PLANE_LENGTH):continue
   j=min(hits,key=lambda i:endds[i]);selected=(j,xy,row);break
  if selected:break
 if selected is None:out['terminal_reason']='No complete <=2.5mm GND-layer bridge with critical-projection reserve and ordinary path to switch';save();raise SystemExit(0)
 j,xy,row=selected;out['bounded_plane_bridge']=row;out['routes'].append({'net':NET,'layer':row['layer'],'points':row['points'],'width':.127,'length_mm':row['length_mm'],'isolated_GND_layer_exception':True});out['vias'].append({'net':NET,'xy':xy,'diameter':.45,'drill':.2});A={'xy':xy};starts={j};q=[(0,j)];ds={j:0};prev={};goal=None
 while q:
  cost,j=heapq.heappop(q)
  if cost!=ds[j]:continue
  if j in ends:goal=j;break
  for k,pp,ex in adj[j]:
   nc=cost+(0 if ex else 1)
   if nc<ds.get(k,math.inf):ds[k]=nc;prev[k]=(j,pp,ex);heapq.heappush(q,(nc,k))
 assert goal is not None
 out['route_start_after_existing_BOOT_prefix_and_plane_bridge']=xy
 out['graph_connected_with_isolated_plane_exception']=True;save()

seq=[];cur=goal
while cur not in starts:
 before,p,existing=prev[cur];seq.append((before,cur,p,existing));cur=before
seq.reverse();cursor=A['xy'];current=cur;segments=[]
for aa,bb,p,existing in seq:
 pt=p if existing else polylabel(p,tolerance=.0001);xy=[round(pt.x,6),round(pt.y,6)]
 if existing:out.setdefault('retained_own_via_transitions',[]).append({'uuid':existing,'xy':xy})
 else:
  check=s.check(Point(xy),vo,True);assert all(r['pass_with_polygon_error']for r in check);out['vias'].append({'net':NET,'xy':xy,'diameter':.45,'drill':.2,'nearest':check[:4]})
 segments.append((current,cursor,xy));cursor=xy;current=bb
segments.append((goal,cursor,B['xy']))
for i,Axy,Bxy in segments:
 layer,p=nodes[i];points=[[round(x,6),round(y,6)]for x,y in shortest(p,Axy,Bxy)];line=LineString(points);check=s.check(line,obstacles[layer],True);assert all(r['pass_with_polygon_error']for r in check);out['routes'].append({'net':NET,'layer':layer,'points':points,'width':.127,'length_mm':line.length,'nearest':check[:4]});print('ROUTE',layer,line.length,flush=True);save()
pairs=[math.dist(a['xy'],b['xy'])for i,a in enumerate(out['vias'])for b in out['vias'][i+1:]];out['mutual_via_center_distances_mm']=pairs;out['mutual_via_process_passed']=all(x>=.577+s.ERROR for x in pairs);out['complete']=out['mutual_via_process_passed'];out['total_length_mm']=sum(r['length_mm']for r in out['routes']);out['terminal_reason']='Complete copper/process proposal; remaining-terminal capacity, native finite entries, refill/reference and electrical reviews pending';save();signal.alarm(0);print('TERMINAL',out['complete'],out['seconds'],flush=True)
