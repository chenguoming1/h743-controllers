"""Bounded native7-only RX/GND/HOLD transaction with joint first-barrel capacity."""
import argparse,itertools,json,math,signal,time
from pathlib import Path
from native7_IO4_TX_up_model_v1 import build,adapter,HERE,ROOT

def main(path):
 start=time.monotonic();ct=json.loads(path.read_text());end=start+ct['internal_seconds'];output=ROOT/ct['receipt'];out={'schema':'f722-native7-IO4-native-joint/v5','complete':False,'selected':False,'native_board_edited':False,'routes':[],'vias':[],'checks':[],'first_transition_domains':[],'plans':[]}
 def save():out['seconds']=time.monotonic()-start;output.write_text(json.dumps(out,indent=2,allow_nan=False)+'\n')
 def alarm(sig,frame):out['terminal_reason']='Bounded native7 joint constructor deadline';save();raise TimeoutError()
 for x in ct['source_files']:assert adapter.digest(ROOT/x['path'])==x['sha256'],x['path']
 signal.signal(signal.SIGALRM,alarm);signal.alarm(ct['internal_seconds'])
 try:
  from shapely import unary_union
  from shapely.geometry import Point
  from shapely.ops import polylabel
  g,base,C,view,work,inventory=build();out['source']=g.binding();out['inventory']=inventory;out['contract_sha256']=adapter.digest(path);source=json.loads((ROOT/ct['source_scope']).read_text());assert source['source']==g.binding()
  for r in source['conditional_source_prefix_recipes']:
   net,peers=view(r['net'],r['role'],work);finite=g.check_track(net,r['layer'],r['points'],width=r['width'],objects=peers);assert C._passed(finite),r['name'];q=g.track(r['net'],r['layer'],r['points'],r['name'],r['width']);work.append((dict(q[0],role=r['role']),*q[1:]));out['routes'].append(r)
  def job(name,net,a,b,sl,el,role=None,width=.127):return {'name':name,'net':net,'role':role,'width':width,'a':a,'b':b,'start_layers':sl,'end_layers':el,'layers':list(C.ORDINARY)}
  jobs=[job('RX_down','PORT_C_RX_EXT',[24.7,18.6],g.one_pad('R34.1')['xy'],['F.Cu'],['B.Cu'],'downstream'),job('RX_up','PORT_C_RX_EXT',g.one_pad('U15.6')['xy'],g.one_pad('J11.1')['xy'],['F.Cu'],['F.Cu'],'upstream'),job('HOLD','FLASH_HOLD_N',g.one_pad('R6.2')['xy'],[35.9343,25.077034],['B.Cu'],['In2.Cu'])]
  jobs.append(job('TX_up','PORT_C_TX_EXT',[26.35,17.1],g.one_pad('J11.2')['xy'],['F.Cu'],['F.Cu'],'upstream'))
  # Assign the vacated ground-stitch cell to RX-down, whose complete
  # ordinary inner route removes the measured long F separator.
  seed=json.loads((ROOT/ct['failure_seed']).read_text());assert seed['source']==g.binding()
  seed_via=next(v for v in seed['candidate_barrels'] if v['net']=='GND')
  xy=seed_via['xy'];down=jobs[0]
  out['explicit_RX_down_transition']={'xy':xy,'source_seed':ct['failure_seed'],'fresh_finite_check_required':True}
  C._add_via(g,view,down,work,xy,'native-IO4-RX-down-inner-source-via',out['vias'],out['checks']);save()
  out['protected_corridor_access_guards']=[]
  def remaining_guard(stage):
   checkpoint={'after':stage,'elapsed_seconds':time.monotonic()-start,'jobs':[]};out['protected_corridor_access_guards'].append(checkpoint)
   for peer in jobs:
    pp,_=C._plan(g,view,peer,work,end);checkpoint['jobs'].append({'name':peer['name'],'plan':pp});save()
    if not pp['connected']:raise C.CFailure(stage+' disconnects '+peer['name'])
  remaining_guard('RX-down source barrel')
  C._add_track(g,view,down,work,'F.Cu',down['a'],xy,'native-IO4-RX-down-short-F-entry',out['routes'],out['checks'],end);save()
  remaining_guard('RX-down short F entry')
  C._add_track(g,view,down,work,'In2.Cu',xy,[28.963321,20.840573],'native-IO4-RX-down-inner-trunk',out['routes'],out['checks'],end);save()
  remaining_guard('Complete RX-down In2 path')
  up=jobs[1];pp,_=C._plan(g,view,up,work,end);out['protected_RX_up_plan']=pp;save()
  if not pp['connected'] or pp['new_vias']:raise C.CFailure('RX-up direct/existing-transition corridor no longer available')
  for i,leg in enumerate(pp['legs']):
   C._add_track(g,view,up,work,leg['layer'],leg['start'],leg['end'],'native-IO4-RX-up-corridor-'+str(i),out['routes'],out['checks'],end);save()
  remaining_guard('Both complete protected RX paths')
  out['actual_protected_RX_corridors_held_before_support_barrels']=True;save()
  tx=jobs[3];tp,_=C._plan(g,view,tx,work,end);out['TX_up_restoration_before_support']=tp;save()
  if not tp['connected'] or tp['new_vias']:raise C.CFailure('TX-up ordinary existing-transition restoration unavailable before support allocation')
  for i,leg in enumerate(tp['legs']):
   C._add_track(g,view,tx,work,leg['layer'],leg['start'],leg['end'],'native-IO4-TX-up-restored-'+str(i),out['routes'],out['checks'],end);save()
  remaining_guard('Complete RX pair and TX-up restoration')
  domains={};direct={};graphs={}
  for j in jobs:
   C._deadline(end);plan,graph=C._plan(g,view,j,work,end);graphs[j['name']]=graph;out['plans'].append({'job':j,'plan':plan});save()
   if not plan['connected']:raise C.CFailure('Actual native-only target is disconnected before mutual allocation: '+j['name'])
   source_nodes=set(plan['start_nodes']);target_nodes=set(plan['end_nodes']);seen=set(target_nodes)-source_nodes;todo=list(seen)
   while todo:
    for nxt,w,e in graph['adj'][todo.pop()]:
     if nxt not in seen and nxt not in source_nodes:seen.add(nxt);todo.append(nxt)
   first=[];existing=[]
   for i in source_nodes:
    for nxt,w,e in graph['adj'][i]:
     if nxt not in seen:continue
     if e['kind']=='new_via_region':first.append(e['geometry'])
     else:existing.append(e)
   domain=unary_union(first);domains[j['name']]=domain;direct[j['name']]=bool(source_nodes&target_nodes) or bool(existing)
   sourceF=unary_union([graph['nodes'][i][1] for i in source_nodes if graph['nodes'][i][0]=='F.Cu'])
   out['first_transition_domains'].append({'function':j['name'],'direct_or_existing_transition':direct[j['name']],'existing_transitions':existing,'actual_start_nodes':sorted(source_nodes),'target_connected_first_via_area_mm2':domain.area,'bounds':None if domain.is_empty else list(domain.bounds),'wkb_hex':domain.wkb_hex,'uninterrupted_source_F_area_mm2':sourceF.area,'source_F_wkb_hex':sourceF.wkb_hex});save()
  gj=job('U15_GND','GND',[24.5,17.83],None,['F.Cu'],['F.Cu'],width=.25)
  with C._width_state(g,.25):free,_,vobs=g.rt.domain('GND','F.Cu',objects=work)
  comp=g.rt.component(free,gj['a']);legal=g.s.OUTLINE.buffer(-.479-g.s.ERROR-.0001).difference(g.rt.expanded(vobs));domain=comp.intersection(legal) if comp is not None else Point().buffer(0);domains['U15_GND']=domain
  ground_existing=[q for q in work if q[0]['net']=='GND' and q[0]['kind']=='via' and comp is not None and comp.covers(Point(q[0]['xy']))]
  ground_existing.sort(key=lambda q:math.dist(gj['a'],q[0]['xy']))
  out['first_transition_domains'].append({'function':'U15_GND','width_mm':.25,'source_connected_new_barrel_area_mm2':domain.area,'bounds':None if domain.is_empty else list(domain.bounds),'wkb_hex':domain.wkb_hex,'existing_source_F_reachable_ground_barrels':[{'uuid':q[0]['uuid'],'xy':q[0]['xy'],'distance_mm':math.dist(gj['a'],q[0]['xy']),'shared_return_role_review_pending':True} for q in ground_existing[:8]]});save()
  # Exact necessary spacing bound, without treating a representative as fixed.
  if not direct['RX_down'] and not direct['RX_up']:
   a,b=domains['RX_down'],domains['RX_up'];required=.45+.127+g.s.ERROR
   if a.is_empty or b.is_empty:raise C.CFailure('One protected RX branch has no actual-target-connected first transition')
   def corners(q):x0,y0,x1,y1=q.bounds;return [(x0,y0),(x0,y1),(x1,y0),(x1,y1)]
   upper=max(math.dist(x,y) for x in corners(a) for y in corners(b));out['protected_RX_mutual_first_barrel_capacity']={'required_center_spacing_mm':required,'bounding_box_maximum_possible_center_spacing_mm':upper,'bounding_box_bound_proves_incompatible':upper<required,'actual_domains_not_representative_points':True};save()
   if upper<required:raise C.CFailure('The two actual protected RX first-transition domains cannot hold two process-separated barrels; no GND/HOLD/RX tracks constructed')
  # Finite candidate allocation only after the necessary domain bound passes.
  def choices(domain):
   parts=sorted(g.rt.parts(domain),key=lambda p:p.area,reverse=True);return [C._xy(polylabel(p,tolerance=.00001).coords[0]) for p in parts[:6]]
  options={j['name']:([None] if direct[j['name']] else choices(domains[j['name']])) for j in jobs}
  nearparts=sorted(g.rt.parts(domain),key=lambda p:p.distance(Point(gj['a'])))[:4]
  options['U15_GND']=[{'xy':C._xy(polylabel(p,tolerance=.00001).coords[0]),'existing_uuid':None} for p in nearparts]+[{'xy':q[0]['xy'],'existing_uuid':q[0]['uuid']} for q in ground_existing[:3]]
  if any(not v for v in options.values()):raise C.CFailure('A full support function has no candidate transition in the exact connected domain')
  selected=None;out['barrel_allocation_trials']=[];ordered=['RX_down','RX_up','TX_up','HOLD','U15_GND']
  for values in itertools.product(*(options[k] for k in ordered)):
   C._deadline(end);assign=dict(zip(ordered,values));xy=[v['xy'] if isinstance(v,dict) else v for v in values];spacing=all(math.dist(xy[i],xy[j])>=.577+g.s.ERROR for i in range(len(xy)) for j in range(i+1,len(xy)) if xy[i] is not None and xy[j] is not None);out['barrel_allocation_trials'].append({'assignment':assign,'spacing_passed':spacing})
   if spacing:selected=assign;break
  if selected is None:raise C.CFailure('No mutually separated allocation among recorded source-derived candidate centers; continuous-domain feasibility remains unresolved')
  for j in jobs:
   xy=selected[j['name']]
   if xy is not None:C._add_via(g,view,j,work,xy,'native-IO4-'+j['name']+'-source-via',out['vias'],out['checks'])
  gs=selected['U15_GND'];gj['b']=gs['xy'];out['selected_ground_transition']=gs
  if gs['existing_uuid'] is None:C._add_via(g,view,gj,work,gj['b'],'native-IO4-U15-GND-via',out['vias'],out['checks'])
  # Retire the HOLD donor only if its exact original copper preserves every
  # chosen circle and every actual signal/ground access in the shared state.
  holdids={'00d3d778-abd5-4fa9-8b8f-9877e7b83803','f30237b0-7063-45c1-947a-2b6d75ac6f88','8f22baac-a8ff-4219-8c6b-8d5695979bc7','bcf4a808-4cd6-5541-8d5e-f9545c5dc1a2'}
  retained=list(work);holdnew={v['name'] for v in out['vias'] if v['net']=='FLASH_HOLD_N'};trial=[q for q in work if q[0]['uuid'] not in holdnew]+[base.entry(base.by[u]) for u in sorted(holdids)]
  gate={'finite':[],'actual_target_plans':[],'passed':False};out['unchanged_HOLD_addback']=gate
  for uid in sorted(holdids):
   rec=base.by[uid];others=[q for q in trial if q[0]['uuid']!=uid]
   chk=g.check_via('FLASH_HOLD_N',rec['xy'],objects=others) if rec['kind']=='via' else g.check_track('FLASH_HOLD_N',next(iter(rec['copper'])),[rec['start'],rec['end']],width=rec['width'],objects=others)
   gate['finite'].append({'uuid':uid,'passed':C._passed(chk),'nearest':chk[:4]})
  if all(z['passed'] for z in gate['finite']):
   for j in jobs:
    if j['name']=='HOLD':continue
    p,_=C._plan(g,view,j,trial,end);gate['actual_target_plans'].append({'job':j['name'],'plan':p})
   with C._width_state(g,.25):gf,_,_=g.rt.domain('GND','F.Cu',objects=trial)
   gc=g.rt.component(gf,gj['a']);gate['GND_actual_source_to_selected_barrel_F_connected']=gc is not None and gc.covers(Point(gj['b']))
   gate['passed']=all(z['plan']['connected'] for z in gate['actual_target_plans']) and gate['GND_actual_source_to_selected_barrel_F_connected']
  if gate['passed']:
   work=trial;out['vias']=[v for v in out['vias'] if v['name'] not in holdnew];out['restored_original_HOLD_native_ids']=sorted(holdids);inventory['removed_native_records']=[o for o in inventory['removed_native_records'] if o['uuid'] not in holdids];inventory['removed_native_ids']=[u for u in inventory['removed_native_ids'] if u not in holdids];inventory['native_cut_count']=len(inventory['removed_native_ids'])
  save()
  # All further target transitions are reserved before any new support/signal trunk.
  out['reserved_full_plans']=[]
  for j in jobs:
   plan,_=C._plan(g,view,j,work,end);out['reserved_full_plans'].append({'job':j,'plan':plan});save()
   if not plan['connected']:raise C.CFailure('Mutual first barrels disconnect '+j['name'])
   for i,v in enumerate(plan['new_vias']):C._add_via(g,view,j,work,v['xy'],'native-IO4-'+j['name']+'-target-via-'+str(i),out['vias'],out['checks'])
  out['all_chosen_barrels_mutually_reserved_before_tracks']=True;save()
  C._add_track(g,view,gj,work,'F.Cu',gj['a'],gj['b'],'native-IO4-U15-ground-return',out['routes'],out['checks'],end)
  for j in jobs:
   plan,_=C._plan(g,view,j,work,end)
   if not plan['connected'] or plan['new_vias']:raise C.CFailure('Held full transition allocation no longer supports '+j['name'])
   for i,leg in enumerate(plan['legs']):C._add_track(g,view,j,work,leg['layer'],leg['start'],leg['end'],'native-IO4-'+j['name']+'-leg-'+str(i),out['routes'],out['checks'],end)
   save()
  out['final_actual_functions']={j['name']:C._already_connected(g,view,j,work) for j in jobs};holdpads=dict(jobs[2],b=g.one_pad('U3.7')['xy'],end_layers=['B.Cu']);out['final_actual_functions']['HOLD_R6_to_U3']=C._already_connected(g,view,holdpads,work)
  groundgroups=C._physical_groups(g,work,'GND');gid=gs['existing_uuid'] or 'native-IO4-U15-GND-via';out['final_actual_functions']['U15_GND_to_barrel']=any('U15.3' in z['keys'] and gid in z['ids'] for z in groundgroups)
  rxgroups=C._physical_groups(g,work,'PORT_C_RX_EXT');cutgroups=C._physical_groups(g,work,'PORT_C_RX_EXT',cut_key='U15.5');out['IO5_physical_cut']={'full_external_and_series_tree_connected':any({'J11.1','U15.5','U15.6','R34.1'}.issubset(set(z['keys'])) for z in rxgroups),'no_outside_pad_bypass':not any({'J11.1','R34.1'}.issubset(set(z['keys'])) for z in cutgroups),'cut_key':'U15.5'}
  txgroups=C._physical_groups(g,work,'PORT_C_TX_EXT');txcut=C._physical_groups(g,work,'PORT_C_TX_EXT',cut_key='U15.2');out['IO2_physical_cut']={'full_external_and_series_tree_connected':any({'J11.2','U15.2','U15.9','R35.1'}.issubset(set(z['keys'])) for z in txgroups),'no_outside_pad_bypass':not any({'J11.2','R35.1'}.issubset(set(z['keys'])) for z in txcut),'cut_key':'U15.2'}
  out['mutual_finite']=[]
  for r in out['routes']+out['vias']:
   peers=[q for q in work if q[0]['uuid']!=r['name']];net=r['net']
   if net in C.PROTECTED:net,peers=view(net,r['role'],peers)
   f=g.check_via(net,r['xy'],objects=peers) if r['kind']=='via' else g.check_track(net,r['layer'],r['points'],width=r['width'],objects=peers)
   out['mutual_finite'].append({'name':r['name'],'passed':C._passed(f),'nearest':f[:6]})
  out['complete']=all(out['IO2_physical_cut'][k] for k in ('full_external_and_series_tree_connected','no_outside_pad_bypass')) and all(out['final_actual_functions'].values()) and all(out['IO5_physical_cut'][k] for k in ('full_external_and_series_tree_connected','no_outside_pad_bypass')) and all(z['passed'] for z in out['mutual_finite']);out['terminal_reason']='Complete isolated IO4/GND/HOLD geometry requires fresh paired native, plane/reference/power qualification' if out['complete'] else 'Constructed candidate failed final actual contact/cut or mutual finite gate';save()
 except TimeoutError:pass
 except Exception as e:out['terminal_reason']=str(e);out['exception_type']=type(e).__name__;save()
 finally:
  signal.alarm(0);print(json.dumps({'complete':out['complete'],'seconds':time.monotonic()-start,'terminal_reason':out.get('terminal_reason'),'receipt_sha256':adapter.digest(output)},indent=2))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--contract',type=Path,required=True);main(p.parse_args().contract)
