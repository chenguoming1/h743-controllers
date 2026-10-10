"""One graph-only RX/MISO prerequisite; exact original R3/power/grounds held."""
import argparse,importlib.util,json,resource,signal,sys,time
from pathlib import Path
from shapely.geometry import Point
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(H))
import native7_recovered_context_v3 as adapter
from prepare_native7_coordinated_context_v3 import replay
import native7_joint_routing_helpers_v3 as routing
import native7_positive_contact_partition_v1 as positive
OLD_CS={'8a55abc3-716e-448f-887e-c4ef9f2907bd','296bfec5-72b7-4194-9568-a88d79de25ed'}
MISO={'recovered-four-source-3','recovered-MISO-source-to-MID','recovered-FLASH_MISO-source-via'}

def main(path):
 start=time.monotonic();c=json.loads(path.read_text())
 for row in c['source_files']:assert adapter.digest(ROOT/row['path'])==row['sha256'],row['path']
 deadline=start+c['internal_seconds'];output=ROOT/c['receipt'];out={'schema':'f722-native7-original-R3-MISO-release-preflight/v1','complete':False,'prerequisite_passed':False,'selected':False,'graph_only':True,'router_called':False,'contract_sha256':adapter.digest(path),'stages':[]}
 def save():
  out['seconds']=time.monotonic()-start;r=resource.getrusage(resource.RUSAGE_SELF);out['resources']={'cpu_user_seconds':r.ru_utime,'cpu_system_seconds':r.ru_stime,'peak_resident_memory_KiB':r.ru_maxrss};output.write_text(json.dumps(out,indent=2,allow_nan=False)+'\n')
 def alarm(*args):raise TimeoutError('Bounded MISO-release prerequisite deadline')
 signal.signal(signal.SIGALRM,alarm);signal.alarm(c['internal_seconds'])
 try:
  spec=importlib.util.spec_from_file_location('MISO_release_C',ROOT/c['C_helper']);C=importlib.util.module_from_spec(spec);spec.loader.exec_module(C)
  g=adapter.load();out['source']=g.binding();proposal,scope,cuts,held,added,reservation,rv=replay(g);_,_,view=C._load(g,held+added+[rv]);job=next(j for j in C._jobs(g) if j['name']=='RX_down')
  original_CS=[q for q in g.BASE if q[0]['uuid'] in OLD_CS];assert len(original_CS)==2
  objects=held+added+original_CS;cuts=set(cuts)-OLD_CS;assert len(cuts)==88
  seed=json.loads((ROOT/c['source_packet']).read_text());v=seed['vias'][0];alias,branch=C._view(view,job,objects);checks=g.check_via(alias,v['xy'],objects=branch)
  out['fixed_northern_barrel']={'recipe':v,'finite_pass':C._passed(checks),'nearest':checks[:5]}
  if not C._passed(checks):raise RuntimeError('Held northern barrel fails process checks with original R3 contacts')
  q=g.via(v['net'],v['xy'],v['name']);objects.append((dict(q[0],role='downstream'),*q[1:]));out['removed_native_ids']=sorted(cuts);out['restored_original_R3_CS_records']=[q[0] for q in original_CS]
  holes=positive.drill_voids(objects,g.N['copper_layers']);contacts=[]
  for net,keys in [('IMU_CS',['U1.20','U2.12','R3.2']),('+3V3_IMU',['R3.1','C12.1','C11.1','C13.1','U2.5','U2.8','FB2.2'])]:
   _,m=positive.partition(objects,net,g.N['copper_layers'],holes=holes);hit=set(m[g.one_pad(keys[0])['uuid']])
   for key in keys[1:]:hit &= m[g.one_pad(key)['uuid']]
   contacts.append({'net':net,'actual_pads':keys,'passed':bool(hit)})
  out['actual_original_R3_and_main_supply_contacts']=contacts
  if not all(x['passed'] for x in contacts):raise RuntimeError('Original R3/main supply contacts not complete')
  def F_gate(label,work):
   alias,branch=C._view(view,job,work);free,obs,vo=g.rt.domain(alias,'F.Cu',width=.127,objects=branch);source=g.rt.component(free,job['a']);target=g.rt.component(free,v['xy'])
   row={'label':label,'source':job['a'],'target_barrel':v['xy'],'connected':source is not None and source.covers(Point(v['xy'])),'source_component_area_mm2':None if source is None else source.area,'source_component_bounds':None if source is None else list(source.bounds),'source_component_wkb_hex':None if source is None else source.wkb_hex,'target_component_area_mm2':None if target is None else target.area,'target_component_bounds':None if target is None else list(target.bounds),'target_component_wkb_hex':None if target is None else target.wkb_hex}
   out['stages'].append(row);save();return row
  baseline=F_gate('original_R3_and_complete_MISO_entry_held',objects)
  removed=[q for q in objects if q[0]['uuid'] in MISO];assert len(removed)==3 and all(q[0]['net']=='FLASH_MISO' for q in removed)
  out['removed_MISO_proposal_records']=[q[0] for q in removed]
  work=[q for q in objects if q[0]['uuid'] not in MISO]
  released=F_gate('only_complete_MISO_proposal_entry_released',work)
  if not released['connected']:raise RuntimeError('Releasing only the complete MISO entry does not create the required RX F approach')
  router=routing.Router(g,work,deadline);graph,mid_plan=router.graph('FLASH_MISO',g.one_pad('U1.35')['xy'],[25.384531,14.536071],('B.Cu',),('In3.Cu',))
  actual=g.gg.connect(graph,g.one_pad('U1.35')['xy'],g.one_pad('U3.2')['xy'],('B.Cu',),('B.Cu',));out['MISO_to_retained_MID_plan']=mid_plan;out['MISO_actual_U3_target_plan']=actual
  out['MISO_source_domains']=[]
  for node in mid_plan['start_nodes']:
   layer,p=graph['nodes'][node];eligible=graph['eligible'].get(node)
   out['MISO_source_domains'].append({'node':node,'layer':layer,'area_mm2':p.area,'bounds':list(p.bounds),'wkb_hex':p.wkb_hex,'legal_barrel_area_mm2':0 if eligible is None else eligible.area,'legal_barrel_wkb_hex':None if eligible is None else eligible.wkb_hex})
  if not mid_plan['connected'] or not actual['connected']:raise RuntimeError('Released MISO lacks actual MID or U3 access before joint allocation')
  out['prerequisite_passed']=True;out['terminal_reason']='RX F approach and individual MISO MID/U3 access pass; simultaneous finite routes remain unproved'
  out['baseline_already_passed']=baseline['connected']
 except Exception as exc:out['terminal_reason']=str(exc);out['exception_type']=type(exc).__name__
 finally:
  signal.alarm(0);save();print(json.dumps({k:out.get(k) for k in ['prerequisite_passed','baseline_already_passed','terminal_reason','seconds','resources']},indent=2),flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--contract',type=Path,required=True);main(p.parse_args().contract)
