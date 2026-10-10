#!/usr/bin/env python3
"""One bounded Case A power-feed reconstruction, read-only native geometry."""
import collections, hashlib, importlib.util, json, pathlib, math
HERE=pathlib.Path(__file__).resolve().parent
ROOT=HERE.parents[1]
s=importlib.util.spec_from_file_location('native',HERE.parent/'flash-candidate38/native_geometry.py')
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
from shapely.affinity import translate
from shapely.ops import nearest_points, polygonize
from shapely.strtree import STRtree
BOARD=ROOT/'candidate40/f722-heli.kicad_pcb';NATIVE=ROOT/'candidate40/f722-heli.native.json';MECH=ROOT/'candidate40/owner-mechanical-geometry.json'
EXPECTED='ea6c41fef86c1f66dbf6e2ce24b58858313c5c83f2a518e53385d48aad734ed5'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
N=json.loads(NATIVE.read_text());M=json.loads(MECH.read_text())['current']
assert sha(BOARD)==N['board_sha256']==M['sha256']==EXPECTED
old_evidence={str(p.relative_to(ROOT)):sha(p)for folder in ['dsm-courtyard40','dsm-coordinated-return','dsm-rpm-local38','dsm-gnd-upward38','dsm-protected38']for p in (HERE.parent/folder).rglob('*')if p.is_file()and'__pycache__'not in str(p)}
fs=M['footprints'];OUT=m.geom(N['outline_with_npth']['polygons']);ERROR=N['maximum_polygon_error_mm'];GUARD=.0000003
POSES={'R38':[17.6,23.46,0,'B.Cu'],'R70':[17.3,22.52,180,'B.Cu'],'C70':[18.45,24.66,180,'B.Cu']}
assert all(fs[r]['angle']==p[2] and fs[r]['side']==p[3] for r,p in POSES.items())
shifts={r:(p[0]-fs[r]['xy'][0],p[1]-fs[r]['xy'][1])for r,p in POSES.items()}
def move(g,ref):return translate(g,*shifts[ref])if ref in shifts else g
def build(o,moved=False):
 f=lambda g:move(g,o.get('ref'))if moved else g
 return (o,{l:f(m.geom(p))for l,p in o['copper'].items()},{l:f(m.geom(v['polygons']))for l,v in o.get('mask',{}).items()}if o.get('smd')else{},f(m.geom(o['drill']['outside']))if o.get('drill')else None)
BASE=[build(o)for o in N['objects']]
old_dsm=next(o for o in N['objects']if o['net']=='DSM_RX_EXT'and o['kind']=='track'and o['start']==[16.26,23.59]and o['end']==[17.18,23.59])
CORE_IDS={'564d43f4-fb99-4ccd-80b4-4580af7617f8','b6cf7bc9-8a4c-4cb5-b764-038d677651c3'}
REMOVE=CORE_IDS|{old_dsm['uuid'],'260176e7-2d4d-4020-850f-398625eda69c','30154a77-e29e-465a-aa6f-a2ea55289eb9'}
objects=[build(o,True)for o in N['objects']if o['uuid']not in REMOVE]
paths={
 'CORE':{'net':'+3V3_CORE','layer':'B.Cu','width':.25,'points':[[16.375525,21.252534],[16.85,21.841],[17.298,22.064],[17.78,21.8588],[18.36917,21.505923]]},
 'DSM':{'net':'DSM_RX_EXT','layer':'B.Cu','width':.127,'points':[[16.26,23.59],[16.7,23.59],[16.83,23.46],[17.09,23.46]]},
 'R70_GND':{'net':'GND','layer':'B.Cu','width':.2,'points':[[16.79,22.52],[16.19,23.1]]},
 'R70_ILIM':{'net':'DSM_ILIM','layer':'B.Cu','width':.2,'points':[[19.025,22.5],[17.81,22.52]]},
}
def shape(p):return m.LineString(p['points']).buffer(p['width']/2+GUARD,quad_segs=512)
for name,p in paths.items():
 p['length_mm']=m.LineString(p['points']).length
 objects.append(({'uuid':'proposal:'+name,'kind':'track','net':p['net'],'width':p['width'],'start':p['points'][0],'end':p['points'][-1]}, {'B.Cu':shape(p)}, {}, None))
def trace_check(p,skip=None):
 q=m.LineString(p['points']);r=[]
 for o,c,mask,d in objects:
  if o['uuid']==skip:continue
  if o['net']!=p['net']and p['layer']in c:
   a,b=nearest_points(q,c[p['layer']]);r.append({'object':o.get('key',o['uuid']),'uuid':o['uuid'],'net':o['net'],'category':'foreign_copper','extra_mm':q.distance(c[p['layer']])-p['width']/2-.127,'witness_center':list(a.coords[0]),'witness_obstacle':list(b.coords[0])})
  if o.get('npth')and d is not None:r.append({'object':o['uuid'],'category':'npth','extra_mm':q.distance(d)-p['width']/2-.254})
 for z in N['zones']:
  if z['rule']and p['layer']in z['layers']and(z['forbid']['tracks']or z['forbid']['copper']):r.append({'object':z['uuid'],'category':'keepout','extra_mm':q.distance(m.geom(z['outline']))-p['width']/2})
  elif not z['rule']and z['net']!=p['net']and p['layer']in z['filled']:r.append({'object':z['uuid'],'category':'foreign_zone','extra_mm':q.distance(m.geom(z['filled'][p['layer']]))-p['width']/2-.127})
 r.append({'object':'board_edge','category':'copper_edge','extra_mm':q.distance(OUT.boundary)-p['width']/2-.254})
 r.sort(key=lambda x:x['extra_mm'])
 return {'violations':[x for x in r if x['extra_mm']<ERROR],'nearest':r[:5],'centerline_inside_board':OUT.covers(q)}
checks={name:trace_check(p,'proposal:'+name)for name,p in paths.items()}
padchecks=[]
for o,c,mask,d in objects:
 if o.get('ref')not in POSES:continue
 rr=[]
 for oo,cc,mm,dd in objects:
  if oo['uuid']==o['uuid']:continue
  for l,g in c.items():
   if oo['net']!=o['net']and l in cc:rr.append({'object':oo.get('key',oo['uuid']),'category':'foreign_copper','layer':l,'extra_mm':g.distance(cc[l])-.127})
  if dd is not None:
   for l,g in mask.items():rr.append({'object':oo.get('key',oo['uuid']),'category':'all_drills_to_smt_mask_no_net_exception','layer':l,'extra_mm':g.distance(dd)-.2})
 for l,g in c.items():
  rr.append({'object':'board_edge','category':'copper_edge','layer':l,'extra_mm':g.distance(OUT.boundary)-.254})
  for z in N['zones']:
   if z['rule']and l in z['layers']and(z['forbid'].get('pads')or z['forbid']['copper']):rr.append({'object':z['uuid'],'category':'keepout','layer':l,'extra_mm':g.distance(m.geom(z['outline']))})
 rr.sort(key=lambda x:x['extra_mm'])
 padchecks.append({'pad':o['key'],'before_xy':o['xy'],'after_xy':list(move(m.Point(o['xy']),o['ref']).coords[0]),'violations':[x for x in rr if x['extra_mm']<ERROR],'nearest':rr[:3]})
def fab(f):
 lines=[];pieces=[]
 for g in f['graphics']:
  if g['layer']!='B.Fab':continue
  if g['shape']=='Line':lines.append(m.LineString([g['start'],g['end']]))
  elif g['shape']=='Rect':pieces.append(m.box(min(g['start'][0],g['end'][0]),min(g['start'][1],g['end'][1]),max(g['start'][0],g['end'][0]),max(g['start'][1],g['end'][1])))
 return m.unary_union(pieces+list(polygonize(m.unary_union(lines))))
G={}
for ref,f in fs.items():
 body=move(fab(f),ref);lands=move(m.unary_union([m.geom(p['polygons'].get('B.Cu',[]))for p in f['pads']]),ref)
 header=ref in ['J'+str(i)for i in range(2,9)]
 G[ref]={'court':move(m.geom(f['courtyards'].get('B.Cu',[])),ref),'body':body,'lands':lands,'reserve':m.unary_union([body.buffer(.25 if header else.15,quad_segs=64),lands.buffer(.15 if header else.1,quad_segs=64)])}
assembly=[]
for ref in POSES:
 pairs=[]
 for other,g in G.items():
  if other==ref:continue
  ar=G[ref]['court'].intersection(g['court']).area;res=G[ref]['reserve'].intersection(g['reserve']).area;gap=G[ref]['court'].distance(g['court'])
  if ar>1e-8 or res>1e-8 or(not g['court'].is_empty and gap<.2):pairs.append({'other':other,'courtyard_overlap_mm2':ar,'courtyard_gap_mm':gap,'body_overlap_mm2':G[ref]['body'].intersection(g['body']).area,'reserve_overlap_mm2':res,'reserve_gap_mm':G[ref]['reserve'].distance(g['reserve'])})
 assembly.append({'ref':ref,'court_bounds':G[ref]['court'].bounds,'near_pairs':pairs,'reserve_outside_board_mm2':G[ref]['reserve'].difference(OUT).area,'reserve_board_gap_mm':G[ref]['reserve'].distance(OUT.boundary)})
entries=[]
for o,c,mask,d in objects:
 if o.get('ref')not in POSES:continue
 inside=move(m.geom(o['inside']['B.Cu']),o['ref'])
 for oo,cc,mm,dd in objects:
  if oo['kind']!='track'or oo['net']!=o['net']or'B.Cu'not in cc:continue
  for end in ['start','end']:
   p=m.Point(oo[end])
   if inside.covers(p):entries.append({'pad':o['key'],'track':oo['uuid'],'endpoint':oo[end],'width_mm':oo['width'],'full_cap_extra_mm':inside.boundary.distance(p)-oo['width']/2})
transitions=[]
for pt in [paths['CORE']['points'][0],paths['CORE']['points'][-1]]:
 p=m.Point(pt);cap=p.buffer(.125+GUARD,quad_segs=512)
 retained=[(o,c['B.Cu'])for o,c,mask,d in objects if not o['uuid'].startswith('proposal:')and o['net']=='+3V3_CORE'and'B.Cu'in c and c['B.Cu'].covers(p)]
 union=m.unary_union([g for o,g in retained])
 transitions.append({'xy':pt,'retained_tracks':[{'uuid':o['uuid'],'width_mm':o['width']}for o,g in retained],'full_0p25_cap_outside_retained_copper_mm2':cap.difference(union).area,'full_cap_extra_mm':union.boundary.distance(p)-.125,'overlap_area_mm2':cap.intersection(union).area})
def graph(items,net,cut=False):
 nodes=[];barrels=collections.defaultdict(list);cutpad=m.geom(next(o for o in N['objects']if o.get('key')=='D7.1')['inside']['B.Cu'])
 for o,c,mask,d in items:
  if o['net']!=net or(cut and o.get('key')=='D7.1'):continue
  for l,g in c.items():
   if d is not None:g=g.difference(d)
   if cut and l=='B.Cu':g=g.difference(cutpad)
   pieces=[g]if g.geom_type=='Polygon'else list(g.geoms)
   for part in pieces:
    if part.is_empty or part.area<=0:continue
    i=len(nodes);nodes.append((o,l,part))
    if o.get('barrel_layers'):barrels[o['uuid']].append(i)
 par=list(range(len(nodes)))
 def find(i):
  while par[i]!=i:par[i]=par[par[i]];i=par[i]
  return i
 for ids in barrels.values():
  for i in ids[1:]:par[find(i)]=find(ids[0])
 for layer in N['copper_layers']:
  ids=[i for i,(o,l,g)in enumerate(nodes)if l==layer];gs=[nodes[i][2]for i in ids];tree=STRtree(gs)
  for k,g in enumerate(gs):
   for j in tree.query(g,predicate='intersects'):
    if j>k and g.intersection(gs[j]).area>0:par[find(ids[k])]=find(ids[j])
 groups=collections.defaultdict(lambda:{'pads':[],'uuids':set()})
 for i,(o,l,g)in enumerate(nodes):
  group=groups[find(i)];group['uuids'].add(o['uuid'])
  if o.get('key')and o['kind']=='pad':group['pads'].append(o['key'])
 return sorted([{'pads':sorted(set(g['pads'])),'uuids':sorted(g['uuids'])}for g in groups.values()],key=lambda g:(g['pads'],g['uuids']))
topology={}
for net in ['+3V3_CORE','+3V3_DSM','DSM_ILIM','DSM_RX_EXT','DSM_RX_MCU','GND']:
 before=graph(BASE,net);after=graph(objects,net)
 topology[net]={'before_pad_groups':sorted([g['pads']for g in before if g['pads']]),'after_pad_groups':sorted([g['pads']for g in after if g['pads']]),'before_component_count':len(before),'after_component_count':len(after)}
 topology[net]['same_pad_partition']=topology[net]['before_pad_groups']==topology[net]['after_pad_groups']
core_cut=graph([x for x in BASE if x[0]['uuid']not in CORE_IDS],'+3V3_CORE')
for g in core_cut:g['model_contacts']=sorted(set(g['pads'])&{'U9.6','L2.2','U11.4','U1.19','U1.32','U1.48','U1.64','U3.8','U4.2','U4.6','U4.8','FB1.1','FB2.1'})
dsmcut=graph(objects,'DSM_RX_EXT',True)
padcut=m.geom(next(o for o in N['objects']if o.get('key')=='D7.1')['inside']['B.Cu'])
oldbranch_ids=set(json.loads((HERE.parent/'dsm-coordinated-return/proposal39.json').read_text())['preserved_J12_branch_uuids']) if 'preserved_J12_branch_uuids' in json.loads((HERE.parent/'dsm-coordinated-return/proposal39.json').read_text())else {'5621756c-04c4-4446-885c-16e2ffe55e98','6d6f4fbe-e156-4a7b-adb0-8a402f5182ed','743ed88b-ad5c-4f7b-868b-9f8dd193bcef','b5893fce-831a-43a5-9ad8-48a7a3452310','d35bc9c2-6be1-43f8-982b-78887f5daf8d','d91a80d5-51c1-4a7d-97b0-b51e3b549e63','16655551-ebce-43e4-b159-dd08539e44ec'}
oldc=m.unary_union([c['B.Cu']for o,c,mask,d in objects if o['uuid']in oldbranch_ids and'B.Cu'in c]).difference(padcut)
newc=m.unary_union([c['B.Cu']for o,c,mask,d in objects if o['net']=='DSM_RX_EXT'and o['uuid']not in oldbranch_ids and o.get('key')!='D7.1'and'B.Cu'in c]).difference(padcut)
removed=[{k:o[k]for k in ['uuid','net','start','end','width']}|{'length_mm':m.LineString([o['start'],o['end']]).length}for o in N['objects']if o['uuid']in REMOVE]
old_core_length=sum(x['length_mm']for x in removed if x['uuid']in CORE_IDS);new_core_length=paths['CORE']['length_mm']
ledger=ROOT.parent/'static-power-validation/pilot-candidate19-operator-refined-released/ledger.json';L=json.loads(ledger.read_text());material=L['material'];assert sha(ledger)=='f811c4d93dd074e5d74fb000db2d1218d10199ceb7c0562173be437fda572951'
rho=1.7241e-5*(1+.00393*(material['temperature_C']-20))/material['conductivity_IACS'];rold=rho*old_core_length/(.3*material['thickness_mm']);rnew=rho*new_core_length/(.25*material['thickness_mm'])
resistance={'model_ledger':str(ledger.relative_to(ROOT.parent)),'model_ledger_sha256':sha(ledger),'material':material,'rho_ohm_mm':rho,'old_length_mm':old_core_length,'old_width_mm':.3,'new_length_mm':new_core_length,'new_width_mm':.25,'old_L_over_W':old_core_length/.3,'new_L_over_W':new_core_length/.25,'L_over_W_ratio':(new_core_length/.25)/(old_core_length/.3),'old_rectangular_strip_ohm':rold,'new_rectangular_strip_ohm':rnew,'incremental_strip_ohm':rnew-rold,'current_screens':[{'current_A':i,'new_strip_drop_V':i*rnew,'incremental_drop_V':i*(rnew-rold),'new_strip_loss_W':i*i*rnew}for i in [.32,.82]],'scope':'Conservative fixed-temperature project material assumptions and nominal rectangular-strip estimate only. Does not model current crowding, spreading, return drop, transient decoupling, thermal rise or manufacturing tolerance. Fresh source-bound sheet/barrel solve required. No inherited numerical result. The copper bridge isolates C4.1/C6.1/U1.1/U1.64/U13.5; U11.4 and DSM path are on the source side. 0.32 A is the full electronics allocation bound, 0.82 A additionally bounds all modeled CORE demand even though DSM does not traverse this branch. No universal CORE sink floor exists in the current model; do not apply the classic DSM floor to MCU pads.'}
failures=[]
for name,width,pts in [
 ('fixed_Case_A_original_feed_0p30',.3,[[16.375525,21.252534],[17.241613,22.160802],[18.36917,21.505923]]),
 ('Case_A_final_tangent_path_0p30',.3,paths['CORE']['points']),
 ('Case_A_first_0p25_bend',.25,[[16.375525,21.252534],[17.22,22.0972],[17.78,21.8588],[18.36917,21.505923]]),
 ('Case_A_second_0p25_bend',.25,[[16.375525,21.252534],[17.25,22.0844],[17.78,21.8588],[18.36917,21.505923]])]:
 failures.append({'name':name,'width_mm':width,'points':pts,'check':trace_check({'net':'+3V3_CORE','layer':'B.Cu','width':width,'points':pts})})
via=next(c['B.Cu']for o,c,mask,d in objects if o['uuid']=='3bdf9d5b-0ff4-4ef3-96c4-515517c5f18b');r70pad=next(c['B.Cu']for o,c,mask,d in objects if o.get('key')=='R70.1');gap=via.distance(r70pad)
all_pass=not any(c['violations']or not c['centerline_inside_board']for c in checks.values())and not any(p['violations']for p in padchecks)and not any(a['reserve_outside_board_mm2']>1e-8 or any(p['courtyard_overlap_mm2']>1e-8 or p['reserve_overlap_mm2']>1e-8 for p in a['near_pairs'])for a in assembly)and all(t['same_pad_partition']for t in topology.values())and all(t['full_0p25_cap_outside_retained_copper_mm2']<1e-10 for t in transitions)and all(e['full_cap_extra_mm']>=ERROR for e in entries)and len(dsmcut)==2 and oldc.distance(newc)>=.127+ERROR
out={'status':'complete_nominal_geometry_hypothesis_requires_native_refill_reference_and_fresh_power'if all_pass else'blocked','all_selected_checks_pass':all_pass,'source40':{'board_sha256':EXPECTED,'native_sha256':sha(NATIVE),'mechanical_sha256':sha(MECH)},'method':'Source40 exact native copper/masks/drills, positive-area copper contacts only, finite drill subtracted and physical barrels linked; no chip internal conduction, gap snapping or same-net drill-mask exception. Conservative outward track buffers by 0.3 nm; native error 10 nm. No source mutation or solver. GND graph excludes stale plane fills and compares unchanged pad partitions; final ground continuity/refill remains required.','poses':POSES,'remove_source_tracks':removed,'paths':paths,'track_checks':checks,'moved_pad_checks':padchecks,'assembly':assembly,'entries':entries,'full_width_feed_transitions':transitions,'topology':topology,'CORE_components_without_old_feed':core_cut,'D7_cut':{'actual_native_inside_pad_subtracted':True,'after_cut_pad_groups':[g['pads']for g in dsmcut],'after_cut_component_count':len(dsmcut),'outside_pad_gap_mm':oldc.distance(newc),'minimum_mm':.127,'preserved_J12_branch_uuids':sorted(oldbranch_ids)},'power_screen':resistance,'preserved_failed_bounded_alternatives':failures,'corridor':{'foreign_objects':['3bdf9d5b-0ff4-4ef3-96c4-515517c5f18b','R70.1'],'physical_gap_mm':gap,'maximum_track_width_at_minimum_gap_mm':gap-.254,'width_0p30_deficit_mm':.554-gap,'width_0p25_residual_mm':gap-.504},'source_unchanged':sha(BOARD)==EXPECTED,'prior_evidence_unchanged':all(sha(ROOT/k)==v for k,v in old_evidence.items())}
(HERE/'result.json').write_text(json.dumps(out,indent=2)+'\n')
packet={'schema':'f722-constructor-geometry-proposal/v1','status':out['status'],'source_board':'ordinary-routing/candidate40/f722-heli.kicad_pcb','source_board_sha256':EXPECTED,'source_native_sha256':sha(NATIVE),'source_mechanical_sha256':sha(MECH),'move_footprints':[{'ref':r,'before_pose':fs[r]['xy']+[fs[r]['angle'],fs[r]['side']],'after_pose':p,'preserve_identity_nets_values_and_side':True}for r,p in POSES.items()],'remove_track_uuids':sorted(REMOVE),'add_paths':paths,'add_vias':[],'retained':'Everything else from source40, including dedicated D7 ground via (16.2,24.64), its 0.25 mm return, SBUS/RPM repairs and accepted J12 branch. C70 both existing supply/GND tracks retained with full-cap entries. All other CORE source feed remains original width.','entry_and_geometry_receipt':'result.json','required_acceptance':['Exact-source native construction and complete fill/DRC, including all courtyards with no exception','Footprint pad identities, orthogonal poses, body/reserve/edge/header/socket access and complete pad entries','Net/schematic/firmware parity, positive-area connection and full actual D7-pad cut with branch gap >=0.127 mm','Both-face drill-to-every-SMT-mask >=0.20 mm, drill gaps >=0.25 mm, same-net no exception; through via tenting/process preserved','Reference-plane classification and explicit changed power/decoupling/return support review','Fresh current-source numerical sheet/barrel power and VCAP analysis with existing conservative material/current assumptions; no inherited numerical acceptance','Rebind to accepted source39 before adoption; source40 remains isolated and is not canonical'],'no_adoption_or_power_qualification':True}
(HERE/'proposal40.json').write_text(json.dumps(packet,indent=2)+'\n')
print(json.dumps({'status':out['status'],'all_pass':all_pass,'track_minima':{k:v['nearest'][0]for k,v in checks.items()},'pad_failures':[p for p in padchecks if p['violations']],'transitions':transitions,'D7_cut':out['D7_cut'],'same_pad_partitions':{k:v['same_pad_partition']for k,v in topology.items()},'power':resistance},indent=2))
