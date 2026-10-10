"""Complete TX-to-J11 surface branch followed by the whole WP donor restoration."""
import hashlib,json,math,sys,time,signal
from pathlib import Path
from shapely.geometry import Point,LineString
H=Path(__file__).resolve().parent
import composite_native11_rotated_U15_cluster_CS as g
import route_native11 as rt
import graph_native11 as gg
s=g.s;START=time.monotonic();DEADLINE=START+53
OUT=H/'U15-TX-WP-full-graph11.json'
IDS={'971f6e7d-0866-56ba-8fef-a20acb668542','55fee813-b634-5cc4-8b2d-d9aa997d3941'}
assert all(g.by[u]['net']=='FLASH_WP_N'for u in IDS)
MISO=dict(name='reserved-MISO-actual-entry',net='FLASH_MISO',xy=[30.361319,23.075378])
BASE=[q for q in g.BASE if q[0]['uuid']not in IDS]+[g.via(MISO['net'],MISO['xy'],MISO['name'])]
MISO_ENTRY=dict(name='reserved-MISO-actual-B-entry',net='FLASH_MISO',layer='B.Cu',width=.127,points=[g.one_pad('U3.2')['xy'],MISO['xy']])
R5VIA='13d89c19-a1a8-5d57-bdcc-c9dfc47875da'
target=g.by[R5VIA]['xy'];source=g.one_pad('U3.3')['xy']
out=dict(schema='f722-rotated-C-TX-WP-full-graph11/v1',source=g.binding(),removed_native_records=[g.by[u]for u in sorted(IDS)],
   retained_WP_records=[o for o in g.N['objects']if o['net']=='FLASH_WP_N'and o['uuid']not in IDS],
   R5_pose_and_CORE_feed_unchanged=True,actual_WP_terminals=['R5.2','U3.3'],retained_WP_transition=R5VIA,
   reserved_MISO=MISO,reserved_MISO_entry=MISO_ENTRY,routes=[],vias=[],attempts=[],complete_TX_upstream=False,complete_WP=False,
   all_four_C_branches_complete=False,native_candidate=False,selected=False,reference_scope='Copper-only construction; fresh saved-fill reference and source-bound donor partition checks remain required.')
def save():
 out['seconds']=time.monotonic()-START;out['script_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest();OUT.write_text(json.dumps(out,indent=2)+'\n')
def alarm(sig,frame):
 out['terminal_reason']='Bounded full-layer construction deadline; partial paths remain unselected.';save();print('TERMINAL_TIMEOUT',flush=True);raise SystemExit(0)
signal.signal(signal.SIGALRM,alarm);signal.alarm(53)
def checked(net,layer,points,name,objects):
 r=dict(net=net,layer=layer,width=.127,points=points,name=name);s.OBJECTS=objects;s.HALF=.0635
 cc=s.check(LineString(points),s.obstacles(net,layer)[0],True)
 return r,dict(passed=all(q['pass_with_polygon_error']for q in cc),failures=[q for q in cc if not q['pass_with_polygon_error']],nearest=cc[:4])
out['C_source_support_rechecks']=[]
for cr in g.C['selected_routes']:
 _,ck=checked(cr['net'],cr['layer'],cr['points'],cr['name'],[q for q in BASE if q[0]['uuid']!=cr['name']])
 out['C_source_support_rechecks'].append(dict(name=cr['name'],**ck))
if not all(q['passed']for q in out['C_source_support_rechecks']):out['terminal_reason']='New cluster conflicts with previously passing complete C support.';save();print('C_SUPPORT_REFUSED',flush=True);sys.exit(0)
mr,mc=checked(MISO_ENTRY['net'],MISO_ENTRY['layer'],MISO_ENTRY['points'],MISO_ENTRY['name'],BASE)
out['MISO_actual_B_entry_check']=mc
if not mc['passed']:out['terminal_reason']='The provisional MISO barrel has no proved direct actual-pad entry in this context.';save();print('MISO_ENTRY_REFUSED',flush=True);sys.exit(0)
BASE.append(g.track(mr['net'],mr['layer'],mr['points'],mr['name'],mr['width']))
tx=g.BRANCHES[2];alias,local=g.branch_objects(tx,BASE)
free,obs,vo=rt.domain(alias,'F.Cu',objects=local);comp=rt.component(free,tx['points'][-1]);end=g.one_pad('J11.2')['xy']
out['TX_domain']=dict(component_area_mm2=None if comp is None else comp.area,actual_J11_in_component=bool(comp is not None and comp.covers(Point(end))))
save();print('TX_DOMAIN',out['TX_domain'],flush=True)
path=rt.route(comp,tx['points'][-1],end,DEADLINE)
if path is None:out['terminal_reason']='Complete WP target release still leaves TX actual terminals disconnected or route budget exhausted.';save();print('TERMINAL',out['seconds']);sys.exit(0)
r,ck=checked(alias,'F.Cu',path,'rotated-TX-complete-J11-tail',local);r['net']=tx['net'];r['role']='upstream';r['length_mm']=LineString(path).length
out['TX_check']=ck
if not ck['passed']:save();print('TX_REFUSED',flush=True);sys.exit(0)
out['routes'].append(r);out['complete_TX_upstream']=True
BASE.append(g.track(r['net'],r['layer'],r['points'],r['name'],r['width']));save();print('TX_COMPLETE',r['length_mm'],flush=True)
from shapely import unary_union
cut=s.geom(g.one_pad('U15.2')['inside']['F.Cu'])
up=unary_union([g.track(tx['net'],'F.Cu',tx['points'],tx['name'])[1]['F.Cu'],g.track(r['net'],'F.Cu',r['points'],r['name'])[1]['F.Cu'],s.geom(g.one_pad('U15.9')['copper']['F.Cu'])]).difference(cut)
dn=g.track(g.BRANCHES[3]['net'],'F.Cu',g.BRANCHES[3]['points'],g.BRANCHES[3]['name'])[1]['F.Cu'].difference(cut)
out['complete_TX_actual_IO_cut']=dict(pad='U15.2',gap_mm=up.distance(dn),passed=up.distance(dn)>=.127+s.ERROR)
if not out['complete_TX_actual_IO_cut']['passed']:out['terminal_reason']='Full TX path failed the actual bonded-pad cut.';out['complete_TX_upstream']=False;save();sys.exit(0)
# Restore the complete actual WP function on all four permitted signal layers.
out['WP_original_U3_transition_retained']=True
out['WP_additional_transition_cap']=None
wpnet='FLASH_WP_N';gr=gg.build(wpnet,BASE)
pa=g.one_pad('U3.3');pb=g.one_pad('R5.2')
plan=gg.connect(gr,pa['xy'],pb['xy'],tuple(pa['copper']),tuple(pb['copper']))
out['WP_actual_terminal_graph']=plan;save();print('WP_GRAPH',plan['connected'],plan['additional_transition_count'],flush=True)
if plan['connected']:
 added=[];good=True
 for i,v in enumerate(plan['new_vias']):
  s.OBJECTS=BASE+added;s.HALF=.0635;vc=s.check(Point(v['xy']),s.obstacles(wpnet,'B.Cu')[1],True)
  if not all(q['pass_with_polygon_error']for q in vc):out['WP_via_failure']=vc;good=False;break
  vv=dict(name=f'WP-full-new-via-{i}',net=wpnet,xy=v['xy'],diameter_mm=.45,drill_mm=.2)
  out['vias'].append(vv);added.append(g.via(wpnet,v['xy'],vv['name']))
 objects=BASE+added
 if good:
  for i,leg in enumerate(plan['legs']):
   if leg['start']==leg['end']:continue
   ff,oo,vv=rt.domain(wpnet,leg['layer'],objects=objects);cc=rt.component(ff,leg['start'])
   pp=rt.route(cc,leg['start'],leg['end'],DEADLINE)
   if pp is None:out['WP_unconstructed_leg']=leg;good=False;break
   rr,ck=checked(wpnet,leg['layer'],pp,f'WP-full-restored-leg-{i}',objects)
   if not ck['passed']:out['WP_failed_leg']=dict(leg=leg,check=ck);good=False;break
   rr.update(length_mm=LineString(pp).length,nearest=ck['nearest']);out['routes'].append(rr)
   objects.append(g.track(wpnet,rr['layer'],rr['points'],rr['name'],.127));save();print('WP_LEG',i,rr['layer'],rr['length_mm'],flush=True)
 out['complete_WP']=good
else:
 out['WP_actual_start_components']=[dict(layer=gr['nodes'][i][0],area_mm2=gr['nodes'][i][1].area,bounds=list(gr['nodes'][i][1].bounds),wkb_hex=gr['nodes'][i][1].wkb_hex)for i in plan['start_nodes']]
out['complete_coupled_pair']=out['complete_TX_upstream']and out['complete_WP']
out['terminal_reason']='Complete TX and WP actual-terminal copper witness; remaining full-cell/native gates remain.'if out['complete_coupled_pair']else'Actual WP four-signal-layer graph or its complete construction remains blocked; original source transition retained.'
save();print('WP_COMPLETE',out['complete_WP'],flush=True);print('TERMINAL',out['seconds'],flush=True)
