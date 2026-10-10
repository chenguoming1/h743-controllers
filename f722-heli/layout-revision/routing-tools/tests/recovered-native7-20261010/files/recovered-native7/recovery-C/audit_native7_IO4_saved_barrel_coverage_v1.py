"""Saved exact-domain coverage attribution only; never builds a graph or route."""
import argparse,json,math,signal,time
from pathlib import Path
from native7_RX_IO4_model_v3 import build,adapter,HERE,ROOT

def main(path):
 start=time.monotonic();ct=json.loads(path.read_text());end=start+ct['internal_seconds'];out={'schema':'f722-native7-IO4-saved-barrel-coverage/v1','selected':False,'graph_or_router_run':False,'diagnostic_exclusions_are_not_replacements':True};output=ROOT/ct['receipt']
 def save():out['seconds']=time.monotonic()-start;output.write_text(json.dumps(out,indent=2,allow_nan=False)+'\n')
 def alarm(sig,frame):out['terminal_reason']='Saved-domain audit deadline';save();raise TimeoutError()
 for row in ct['source_files']:assert adapter.digest(ROOT/row['path'])==row['sha256']
 signal.signal(signal.SIGALRM,alarm);signal.alarm(ct['internal_seconds'])
 try:
  from shapely import from_wkb,unary_union
  g,base,C,view,work,before,inventory,jobs=build();packet=json.loads((ROOT/ct['packet']).read_text());raw=json.loads((ROOT/ct['saved_receipt']).read_text());scope=raw['scope'];cuts={r['uuid'] for r in scope['additional_removed_native_records']}
  for r in packet['routes']:
   if r['net']=='PORT_C_RX_EXT':
    q=g.track(r['net'],r['layer'],r['points'],r['name'],r['width']);work.append((dict(q[0],role=r['role']),*q[1:]))
  work=[q for q in work if q[0]['uuid'] not in cuts]
  for r in raw['routes']:
   q=g.track(r['net'],r['layer'],r['points'],r['name'],r['width']);work.append((dict(q[0],role=r['role']),*q[1:]))
  plan=raw['full_80_cut_RX_down_from_proved_prefix'];chamber=unary_union([from_wkb(bytes.fromhex(x['domain_wkb_hex'])) for x in plan['actual_frontier'] if x['side']=='source' and x['layer']=='F.Cu']);out['source']=g.binding();out['saved_chamber']={'area_mm2':chamber.area,'bounds':list(chamber.bounds),'receipt_sha256':adapter.digest(ROOT/ct['saved_receipt'])}
  alias,peers=view('PORT_C_RX_EXT','downstream',work);g.s.OBJECTS=peers;g.s.HALF=.0635;_,vo,_=g.s.obstacles(alias,'F.Cu');blocked=[]
  for row in vo:
   if row['category']=='edge_npth_copper':continue
   radius=(row['required_center_distance_mm']+g.s.ERROR+.0001)/math.cos(math.pi/128)
   if row['geometry'].distance(chamber)>radius:continue
   part=chamber.intersection(row['geometry'].buffer(radius,quad_segs=32))
   if not part.is_empty:blocked.append((row,part))
  cover=unary_union([p for r,p in blocked]);available=chamber.difference(cover);out['baseline_saved_chamber_legal_via_area_mm2']=available.area
  uuids={r['uuid'] for r,p in blocked};rank=[]
  for uid in uuids:
   rows=[(r,p) for r,p in blocked if r['uuid']==uid];shape=unary_union([p for r,p in rows]);rank.append({'uuid':uid,'object':rows[0][0]['object'],'net':rows[0][0]['net'],'kind':rows[0][0]['kind'],'coverage_mm2':shape.area,'categories':sorted({r['category'] for r,p in rows}),'layers':sorted({l for r,p in rows for l in r['layers']})})
  rank.sort(key=lambda x:x['coverage_mm2'],reverse=True);out['coverage_contributors']=rank;save()
  ids=[r['uuid'] for r in rank[:12]];old='97282ff5-d6b5-415f-a3c4-0390df70f0ea'
  if old not in ids:ids.append(old)
  out['single_object_exclusion_in_fixed_saved_chamber']=[]
  for uid in ids:
   C._deadline(end);other=unary_union([p for r,p in blocked if r['uuid']!=uid]);gain=chamber.difference(other)
   out['single_object_exclusion_in_fixed_saved_chamber'].append({'uuid':uid,'legal_area_mm2':gain.area,'bounds':None if gain.is_empty else list(gain.bounds),'domain_wkb_hex':gain.wkb_hex,'F_region_not_recomputed':True});save()
  # Compare the same saved chamber with only the native7 IO4/support scope.
  pad_delta={r['after']['uuid']:r['after'] for r in inventory['pad_net_delta']};nativecuts=set(scope['U15_ground_wall_native_ids']+scope['HOLD_complete_transition_native_ids'])|{r['uuid'] for r in inventory['additional_old_RX_prefix_removed_records']}
  native=[base.entry(pad_delta.get(q[0]['uuid'],q[0])) for q in base.BASE if q[0]['uuid'] not in nativecuts]
  for q in work:
   if q[0]['uuid'] in ('IO4-RX-up-bonded-to-NC6','IO4-joint-RX-down-prefix'):native.append(q)
  alias,np=view('PORT_C_RX_EXT','downstream',native);g.s.OBJECTS=np;_,nv,_=g.s.obstacles(alias,'F.Cu');legal=g.s.OUTLINE.buffer(-.479-g.s.ERROR-.0001).difference(g.rt.expanded(nv));v=chamber.intersection(legal)
  out['native7_only_IO4_comparison']={'native_cut_count':len(nativecuts),'native_cut_ids':sorted(nativecuts),'saved_common_chamber_legal_via_area_mm2':v.area,'domain_wkb_hex':v.wkb_hex,'F_connectivity_in_native_only_context_not_queried':True,'all_original_ordinary_IMU_C12_R3_copper_retained_except_declared_HOLD_and_U15_supports':True}
  out['terminal_reason']='Saved chamber coverage and limited native-only comparison measured; no deletion, placement, route or plane equivalence selected';save()
 except TimeoutError:pass
 except Exception as e:out['terminal_reason']=str(e);out['exception_type']=type(e).__name__;save()
 finally:
  signal.alarm(0);print(json.dumps({'terminal_reason':out.get('terminal_reason'),'seconds':time.monotonic()-start,'receipt_sha256':adapter.digest(output)},indent=2))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--contract',type=Path,required=True);main(p.parse_args().contract)
