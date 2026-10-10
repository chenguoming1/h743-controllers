"""Fresh actual-width coupled audit, with one explicit WP bend-centering trial."""
import copy,hashlib,json,math,time
from pathlib import Path
from shapely.geometry import LineString,Point
import composite_native11_rotated_U15_cluster_CS_native_SBUS as g
H=Path(__file__).resolve().parent;s=g.s;START=time.monotonic()
SOURCE=H/'U15-TX-WP-complete-copper11-transaction.json';T=json.loads(SOURCE.read_text())
assert T['source']==g.BEFORE_NATIVE_SBUS_BINDING
ids={o['uuid']for o in T['removed_native_records']}
for o in T['removed_native_records']:assert g.physical(o)==g.physical(g.by[o['uuid']])
base=[q for q in g.BASE if q[0]['uuid']not in ids]
routes=copy.deepcopy(T['routes']);vias=copy.deepcopy(T['vias'])
peer_routes=T['reserved_peer_routes'];peer_vias=T['reserved_peer_vias']
support=list(g.C['selected_routes'])
# Recover exact path recipes from the loaded source transactions. A recipe is
# accepted only when its freshly generated copper bytes equal the held object.
recipes={}
def collect(v):
 if isinstance(v,dict):
  if all(k in v for k in ['name','net','layer','points','width']):recipes.setdefault(v['name'],[]).append(v)
  for q in v.values():
   if isinstance(q,(dict,list)):collect(q)
 elif isinstance(v,list):
  for q in v:
   if isinstance(q,(dict,list)):collect(q)
for name in ['PACKET','DIV','GR','GREEN','CAP','CS','C','CLUSTER']:
 collect(getattr(g,name))
bindings=[]
for o,c,m,d in base:
 if o['kind']!='track'or o['uuid']in g.by or o['width']==.127:continue
 matches=[]
 for r in recipes.get(o['uuid'],[]):
  fresh=g.track(r['net'],r['layer'],r['points'],r['name'],r['width'])
  if set(c)==set(fresh[1])and all(c[l].wkb_hex==fresh[1][l].wkb_hex for l in c):matches.append(r)
 assert matches,('No exact source path recipe for variable-width held route',o['uuid'],o['width'])
 r=matches[0];assert r['width']==o['width']
 bindings.append(dict(name=r['name'],width_mm=r['width'],generated_copper_bytes_exact=True))
 if r['name']not in [q['name']for q in support]:support.append(r)
out=dict(schema='f722-C-TX-WP-declared-width-audit11/v1',source=g.binding(),source_transaction_sha256=hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
         raw_narrow_support_recheck_preserved=True,trial=None,route_checks=[],via_checks=[],pad_checks=[],selected=False,native_candidate=False)
out['all_added_variable_width_route_bindings']=bindings
out['explicit_peer_revision']=dict(restored_native_record=g.by[g.NATIVE_SBUS_ID],removed_private_route=g.PRIVATE_SBUS_ID,
   prior_exact_binding=g.BEFORE_NATIVE_SBUS_BINDING)
def objects(rr):return base+[g.track(r['net'],r['layer'],r['points'],r['name'],r['width'])for r in rr+peer_routes]+[g.via(v['net'],v['xy'],v['name'])for v in vias+peer_vias]
def check(r,oo):
 s.OBJECTS=[q for q in oo if q[0]['uuid']!=r['name']];s.HALF=r['width']/2
 cc=s.check(LineString(r['points']),s.obstacles(r['net'],r['layer'])[0],True)
 assert all(abs(q['moving_radius_mm']-r['width']/2)<1e-12 for q in cc)
 return dict(name=r['name'],net=r['net'],layer=r['layer'],declared_width_mm=r['width'],moving_radius_mm=r['width']/2,
             passed=all(q['pass_with_polygon_error']for q in cc),nearest=cc[:5],failures=[q for q in cc if not q['pass_with_polygon_error']])
idx=next(i for i,r in enumerate(routes)if r['name']=='WP-full-restored-leg-2');old=copy.deepcopy(routes[idx]);candidate=copy.deepcopy(old)
candidate['points'][1]=[31.20,23.30];candidate['length_mm']=LineString(candidate['points']).length
oldcheck=check(old,objects(routes));trialroutes=copy.deepcopy(routes);trialroutes[idx]=candidate
newcheck=check(candidate,objects(trialroutes))
accept=newcheck['passed']and newcheck['nearest'][0]['extra_clearance_mm']>oldcheck['nearest'][0]['extra_clearance_mm']
out['trial']=dict(before_route=old,after_route=candidate,before_check=oldcheck,after_check=newcheck,accepted=accept,nominal_CAD_only=True,manufacturing_tolerance_qualification=False)
if accept:routes=trialroutes
oo=objects(routes)
for r in support+routes+peer_routes:out['route_checks'].append(check(r,oo))
for v in vias+peer_vias:
 s.OBJECTS=[q for q in oo if q[0]['uuid']!=v['name']];s.HALF=.0635
 cc=s.check(Point(v['xy']),s.obstacles(v['net'],'B.Cu')[1],True)
 out['via_checks'].append(dict(name=v['name'],xy=v['xy'],passed=all(q['pass_with_polygon_error']for q in cc),nearest=cc[:5],failures=[q for q in cc if not q['pass_with_polygon_error']]))
for p in g.C['changed_pad_records']:
 cu=s.geom(p['copper']['F.Cu']);mask=s.geom(p['mask']['F.Mask']['polygons']);bad=[];nearest=[]
 for o,c,m,d in oo:
  if o['uuid']==p['uuid']:continue
  if o['net']!=p['net']and'F.Cu'in c:nearest.append(dict(uuid=o['uuid'],category='foreign_copper',extra_mm=cu.distance(c['F.Cu'])-.127))
  if d is not None:
   nearest.append(dict(uuid=o['uuid'],category='all_drill_mask',extra_mm=mask.distance(d)-.20))
   if o['net']!=p['net']:nearest.append(dict(uuid=o['uuid'],category='foreign_drill_copper',extra_mm=cu.distance(d)-(.254 if o.get('npth')else .20)))
 nearest.sort(key=lambda q:q['extra_mm']);bad=[q for q in nearest if q['extra_mm']<s.ERROR]
 out['pad_checks'].append(dict(key=p['key'],passed=not bad,nearest=nearest[:4],failures=bad))
out['passed']=all(q['passed']for q in out['route_checks']+out['via_checks']+out['pad_checks'])
out['seconds']=time.monotonic()-START;out['script_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
P=H/'U15-TX-WP-declared-width-audit11.json';P.write_text(json.dumps(out,indent=2)+'\n')
if out['passed']:
 final=copy.deepcopy(T);final['schema']='f722-U15-TX-WP-clean-complete-copper11/v2';final['routes']=routes
 final['source']=g.binding();final['explicit_peer_revision']=out['explicit_peer_revision']
 final['declared_width_audit']=dict(file=str(P),sha256=hashlib.sha256(P.read_bytes()).hexdigest())
 final['full_declared_width_peer_audit_pending']=False;final['WP_trace_length_after_mm']=sum(LineString(r['points']).length for r in routes if r['net']=='FLASH_WP_N')+math.dist(g.by['e8b68519-c47c-595d-8067-8b37a365a7eb']['start'],g.by['e8b68519-c47c-595d-8067-8b37a365a7eb']['end'])
 final['one_bend_centering_applied']=accept
 (H/'U15-TX-WP-complete-copper11-transaction-v2.json').write_text(json.dumps(final,indent=2)+'\n')
print('CENTERING',accept,'PASSED',out['passed'],'TERMINAL',out['seconds'],flush=True)
for q in out['route_checks']+out['via_checks']+out['pad_checks']:
 if not q['passed']:print('FAIL',q.get('name',q.get('key')),q['failures'],flush=True)
