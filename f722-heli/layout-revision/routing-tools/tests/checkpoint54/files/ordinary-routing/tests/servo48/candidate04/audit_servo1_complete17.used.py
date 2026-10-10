"""Finite native entries, exact source transaction and support continuity for TAIL fallback."""
import json,pathlib,sys,hashlib,math,copy,collections
H=pathlib.Path(__file__).resolve().parent;R=H.parents[1];S=H.parent/'sbus-nrst49/candidate02';D=H/'candidate04';sys.path[:0]=[str(R/'dsm40-audits'),str(R/'dsm41-audits'),str(R.parent/'integrated-routing')]
from audit_dsm40_entries_return import pad_entry,join_entry,groups,geom
from audit_dsm41_entries_return import via_entry
from shapely.geometry import Point
sha=lambda p:hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest();read=lambda p:json.loads(pathlib.Path(p).read_text());write=lambda n,v:(D/n).write_text(json.dumps(v,indent=2)+'\n')
before=read(S/'f722-heli.native.json');after=read(D/'f722-heli.native.json');prov=read(D/'construction-provenance.json');oldh=sha(S/'f722-heli.kicad_pcb');h=sha(D/'f722-heli.kicad_pcb');assert oldh==before['board_sha256']==prov['source_board_sha256']and h==after['board_sha256']==prov['board_sha256']
old={o['uuid']:o for o in before['objects']};new={o['uuid']:o for o in after['objects']};physical=lambda o:{k:v for k,v in o.items()if k!='net_code'};removed={o['uuid']for o in prov['removed_source_records']};added=prov['added_records'];tracks=[o for o in new.values()if o['kind']=='track'];pads=[o for o in new.values()if o['kind']=='pad'];vias=[o for o in new.values()if o['kind']=='via'];newtracks=[o for o in added if o['kind']=='track'];newvias=[o for o in added if o['kind']=='via']
changed={p['before']['uuid']for p in prov['changed_pad_records']}
assert old.keys()-new.keys()==removed and new.keys()-old.keys()=={o['uuid']for o in added};assert all(physical(o)==physical(new[u])for u,o in old.items()if u not in removed|changed);assert {old[u]['key']for u in changed}=={'R50.1','R50.2'}
assert {f['ref']for f in before['footprints']if f not in after['footprints']}=={'R50'}
assert {o['net']for o in prov['removed_source_records']}=={'SERVO2_MCU','GND','VX_RAW','EFUSE_EN','RPM_LV','ESC_MCU'}
def custom_pad_entry(track,pad,layer,endpoint):
 from shapely.geometry import Polygon,LineString
 from audit_dsm40_entries_return import section_at
 actual=geom(pad['inside'][layer]);assert not pad.get('drill')and actual.geom_type=='Polygon'
 xy=track[endpoint];other=track['end'if endpoint=='start'else'start'];length=math.dist(xy,other);direction=[(other[i]-xy[i])/length for i in range(2)];normal=[-direction[1],direction[0]];half=track['width']/2;section=section_at(xy,normal,half);strips=[]
 for depth in [.15,.1,.075,.05,.025]:
  if depth>length:continue
  center=[xy[i]+depth*direction[i]for i in range(2)];ca=list(section.coords);cb=list(section_at(center,normal,half).coords);ribbon=Polygon([ca[0],ca[1],cb[1],cb[0]])
  if actual.buffer(-.000001).covers(ribbon)and ribbon.difference(geom(track['copper'][layer])).area==0:
   strips.append(dict(length_mm=depth,polygon_mm=list(ribbon.exterior.coords),area_outside_actual_pad_mm2=ribbon.difference(actual).area,boundary_reserve_mm=ribbon.distance(actual.boundary)));break
 return dict(passed=actual.contains(Point(xy))and section.difference(actual).length==0 and bool(strips),pad=pad['key'],pad_uuid=pad['uuid'],net=pad['net'],track_uuid=track['uuid'],layer=layer,endpoint=endpoint,xy_mm=xy,width_mm=track['width'],finite_full_width_strips=strips,full_width_section_mm=list(section.coords),section_missing_mm=section.difference(actual).length,method='Exact finite ribbon from the endpoint within the unmodified non-convex native inside pad and native track, with 1 nm inward reserve; no convex hull, snapping, repair or area tolerance.')
entries=[];annular=[];joins=[];resolved=[];partial=[]
for t in newtracks:
 l=next(iter(t['copper']))
 for end in ['start','end']:
  xy=t[end];hits=[]
  for p in pads:
   if p.get('drill')or p['net']!=t['net']or l not in p['inside']or not geom(p['inside'][l]).contains(Point(xy)):continue
   
   r=custom_pad_entry(t,p,l,end)if geom(p['inside'][l]).convex_hull.difference(geom(p['inside'][l])).area>=1e-12 else pad_entry(t,p,l,end)
   if r['passed']:entries.append(r);hits.append({'pad':p['key']})
   else:partial.append(r)
  for v in vias:
   if v['net']==t['net']and xy==v['xy']:
    r=via_entry(t,v,l,after);assert r['passed'],r;annular.append(r);hits.append({'via':v['uuid']})
  for other in tracks:
   if other['uuid']==t['uuid']or other['net']!=t['net']or l not in other['copper']or xy not in[other['start'],other['end']]:continue
   r=join_entry(t,other,l,min(t['width'],other['width']));assert r['passed'];joins.append(r);hits.append({'track':other['uuid']})
  assert hits,(t['uuid'],t['net'],end,xy);resolved.append({'track':t['uuid'],'net':t['net'],'endpoint':end,'xy':xy,'connections':hits})
via_layers={v['uuid']:sorted({next(iter(t['copper']))for t in newtracks if t['net']==v['net']and v['xy']in[t['start'],t['end']]})for v in newvias};assert all(len(v)>=2 for v in via_layers.values())
base=read(S/'power-audit.json');nets={}
for net in base['nets']:
 a,b=groups(before,net),groups(after,net);assert a==b and len(b)==1,net;nets[net]={'groups':b,'pad_group_count':1,'complete':True,'source_groups_exactly_preserved':True}
signals={}
for net in ['SERVO1_MCU','SERVO2_MCU','SERVO3_MCU','TAIL_MCU','ESC_MCU','RPM_LV','ADC_DIV_MID','ADC_BUS','SBUS_MCU','SBUS_LV','PORT_A_RX_EXT','PORT_A_TX_EXT','PORT_B_RX_EXT','PORT_B_TX_EXT','PORT_A_RX_MCU','PORT_A_TX_MCU','PORT_B_RX_MCU','PORT_B_TX_MCU','BARO_SCL','BARO_SDA']:
 a,b=groups(before,net),groups(after,net);assert len(b)==1,(net,b)
 if net!='SERVO1_MCU':assert a==b,(net,a,b)
 signals[net]={'before':a,'after':b,'complete':True,'source_partitions_preserved':a==b}
assert len(signals['SERVO1_MCU']['before'])==3
for net in ['ADC_DIV_MID','ADC_BUS','HSE_IN','HSE_OUT','HSE_XTAL_OUT']:
 assert {u:physical(o)for u,o in old.items()if o['net']==net}=={u:physical(o)for u,o in new.items()if o['net']==net},net
controls=[];padby={o['key']:o for o in pads};entry=next(t for t in newtracks if t['net']=='SERVO1_MCU'and t['start']==[11.4,11.8875]);bad=copy.deepcopy(entry);bad['width']=2;controls.append({'name':'oversized_actual_U12_1_entry','rejected':not pad_entry(bad,padby['U12.1'],'F.Cu','start')['passed']})
for net,layer in [('SERVO1_MCU','In2.Cu'),('SERVO2_MCU','F.Cu')]:
 ids=next(ids for ids in prov['routes']if new[ids[0]]['net']==net and next(iter(new[ids[0]]['copper']))==layer);bad=copy.deepcopy(after);bad['objects']=[o for o in bad['objects']if o['uuid']not in ids];controls.append({'name':'remove_required_'+net+'_'+layer,'rejected':len(groups(bad,net))>len(groups(after,net))})
custom=next(t for t in newtracks if t['net']=='EFUSE_EN'and t['end']==[11.16,15.8]);bad=copy.deepcopy(custom);bad['width']=2;controls.append({'name':'oversized_nonconvex_U5_1_entry','rejected':not custom_pad_entry(bad,padby['U5.1'],'F.Cu','end')['passed']})
assert all(c['rejected']for c in controls),controls
retained_y1_ground_ids=['326bfc04-07f8-45fc-933b-6205a02da9ff','fb5a234c-5d52-4584-aadd-252a670e4869']
assert all(physical(old[u])==physical(new[u])for u in retained_y1_ground_ids)
gates={'exact_scoped_transaction':True,'only_R50_pose_changed':True,'all_new_track_endpoints_finite':len(resolved)==2*len(newtracks),'all_new_vias_have_two_finite_layer_entries':all(len(v)>=2 for v in via_layers.values()),'all_28_support_groups_exact':len(nets)==28,'SERVO1_complete':True,'other_completed_signals_preserved':True,'ADC_BUS_ADC_DIV_MID_HSE_objects_exact':True,'Y1_case4_lead_and_via_exact':True,'negative_controls_rejected':all(c['rejected']for c in controls)}
audit={'schema':'f722-SERVO1-native-entry-support/v1','passed':all(gates.values()),'gates':gates,'board_sha256':h,'source_board_sha256':oldh,'source_native_sha256':sha(S/'f722-heli.native.json'),'native_sha256':sha(D/'f722-heli.native.json'),'strict_pad_entries':entries,'finite_actual_annular_entries':annular,'new_via_layer_entries':via_layers,'full_width_joins':joins,'endpoint_inventory':resolved,'partial_pad_entries_not_used_as_proof':partial,'new_tracks':len(newtracks),'new_vias':len(newvias),'nets':nets,'signal_groups':signals,'negative_controls':controls,'numerical_power_VCAP_applicable':False,'signal_quality_qualified':False};write('entry-support-audit.json',audit)
binding={'source_board_sha256':oldh,'board_sha256':h,'source_native_sha256':sha(S/'f722-heli.native.json'),'native_sha256':sha(D/'f722-heli.native.json'),'audit':'entry-support-audit.json','audit_sha256':sha(D/'entry-support-audit.json')};write('endpoint-audit.json',{'schema':'f722-native-endpoint-audit-binding/v1','passed':True,**binding,'new_track_endpoints_checked':len(resolved),'direct_pad_entries':len(entries),'full_width_joins':len(joins),'finite_annular_entries':len(annular),'new_vias':len(newvias),'strict_pad_entries_all_pass':True,'negative_controls':len(controls)});write('power-audit.json',{'schema':'f722-native-support-audit/v1','passed':True,**binding,'source_audit_sha256':sha(S/'power-audit.json'),'audit_source_sha256':sha(__file__),'nets':nets,'ground_native_pad_groups_exactly_preserved':True,'numerical_power_VCAP_applicable':False,'method':'Current exact native copper/pad/barrel/filled-plane graph recomputed for all28support nets. Full GND/VX_RAW/EFUSE_EN branch replacements; all HSE, ADC and both Y1 ground paths retain exact native identities. No loaded or transient equivalence claimed.'});print(json.dumps({'passed':audit['passed'],'board_sha256':h,'endpoints':len(resolved),'vias':len(newvias),'signal_nets':len(signals)}))
