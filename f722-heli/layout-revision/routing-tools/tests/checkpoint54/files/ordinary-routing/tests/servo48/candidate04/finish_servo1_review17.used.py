"""Bind the completed SERVO1 native candidate to its saved reviews; no board edits."""
import json, pathlib, hashlib, math, shutil
from shapely.geometry import Polygon, LineString
from shapely.ops import unary_union
H=pathlib.Path(__file__).resolve().parent; R=H.parents[2]; D=H/'candidate04'; S=R/'ordinary-routing/tests/sbus-nrst49/candidate02'
read=lambda p:json.loads(pathlib.Path(p).read_text())
sha=lambda p:hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
write=lambda p,v:pathlib.Path(p).write_text(json.dumps(v,indent=2)+'\n')
def geom(ps): return unary_union([Polygon(p['outer'],p.get('holes',[])) for p in ps])
g=read(D/'f722-heli.native.json'); old=read(S/'f722-heli.native.json'); h=sha(D/'f722-heli.kicad_pcb'); sh=sha(S/'f722-heli.kicad_pcb')
assert h==g['board_sha256']=='755545e8198e9a3649c0e07533c23e67010d91ab6a8b09556d7463e064ac89eb'
assert sh==old['board_sha256']=='71d33748909bb960c5829973642272460607d8521831a6212975f7de6790d660'
ob=g['objects']; by={o['uuid']:o for o in ob}; before={o['uuid']:o for o in old['objects']}; prov=read(D/'construction-provenance.json')
ref=read(D/'servo1-reference/critical-reference.json'); prev=read(H/'reference-source17/critical-reference.json'); assert ref['board_sha256']==h and prev['board_sha256']==sh
mask=[(o,l,geom(v['polygons'])) for o in ob if o.get('smd') for l,v in o.get('mask',{}).items()]
drills=[(o,geom(o['drill']['outside'])) for o in ob if o.get('drill')]
copper=[(o,l,geom(ps)) for o in ob for l,ps in o.get('copper',{}).items()]
outline=geom(g['outline_with_npth']['polygons']); margins=[]
for rec in prov['added_records']:
 if rec['kind']!='via': continue
 v=by[rec['uuid']]; drill=geom(v['drill']['outside']); vc={l:geom(ps) for l,ps in v['copper'].items()}
 gm,mo,ml=min((drill.distance(s),o['key'],l) for o,l,s in mask)
 gd,du=min((drill.distance(s),o['uuid']) for o,s in drills if o['uuid']!=v['uuid'])
 gc,cu,cl,cn=min((vc[l].distance(s),o['uuid'],l,o['net']) for o,l,s in copper if o['net']!=v['net'] and l in vc)
 ge=drill.distance(outline.boundary)
 row=dict(uuid=v['uuid'],net=v['net'],xy_mm=v['xy'],drill_to_SMT_mask_mm=gm,limiting_mask=mo,mask_layer=ml,drill_to_drill_mm=gd,other_drill_uuid=du,copper_clearance_mm=gc,other_copper_uuid=cu,other_copper_net=cn,copper_layer=cl,drill_to_edge_or_NPTH_mm=ge,drill_inside_outline=outline.covers(drill),excess_over_rules_mm=dict(mask=gm-.2,drill=gd-.25,copper=gc-.127,edge_NPTH=ge-.254),tented=v['tented'])
 assert all(x>=0 for x in row['excess_over_rules_mm'].values()) and row['drill_inside_outline']; margins.append(row)
residual=[]
for t in ref['tracks']:
 if t['net']!='SERVO1_MCU':continue
 for f in t['trace_width_missing_by_class']['saved_void_or_edge_outside_own_window']:
  holes=[ref['saved_holes'][t['reference_layer']][i] for i in f['saved_hole_indices']]
  pads=[dict(key=o['key'],net=o['net'],xy_mm=o['xy']) for o in ob if o['kind']=='pad' and o.get('drill') and any(a['bounds_mm'][0]<=o['xy'][0]<=a['bounds_mm'][2] and a['bounds_mm'][1]<=o['xy'][1]<=a['bounds_mm'][3] for a in holes)]
  labels={34:'Merged other-net TAIL_MCU/BARO_SCL via antipad',3:'Merged plated connector pad and TAIL_EXT via void',2:'Merged plated connector pad and own SERVO1 via void; fragment remains outside own-via window'}
  residual.append(dict(track_uuid=t['track_uuid'],signal_layer=t['signal_layer'],reference_layer=t['reference_layer'],fragment=f,saved_holes=holes,plated_pads_within_hole_bounds=pads,classification=labels[f['saved_hole_indices'][0]],classification_limit='Saved hole membership is exact. Pad-center-in-hole-bounds inventory labels nearby participants; it is not a separate causal field calculation.'))
assert len(residual)==4
deltas={n:{k:ref['nets'][n][k]-prev['nets'][n][k] for k in ['native_planar_length_mm','physical_GND_centerline_missing_mm','physical_GND_trace_width_missing_mm2']} for n in ref['nets']}
assert all(v==0 for n in ['ADC_BUS','ADC_DIV_MID','TAIL_MCU'] for v in deltas[n].values())
length=read(H/'signal-review/servo1-path-comparison.json')['candidate04']['paths']['U1.56__U12.1']['branch_track_inventory_mm']
details=dict(schema='f722-SERVO1-margin-reference-details/v1',source_board_sha256=sh,board_sha256=h,native_sha256=sha(D/'f722-heli.native.json'),via_process_margins=margins,SERVO1_reference_totals=ref['nets']['SERVO1_MCU'],SERVO1_outside_window_width_fragments=residual,SERVO1_transitions=[t for t in ref['transitions'] if t['net']=='SERVO1_MCU'],affected_net_numeric_deltas_after_minus_before=deltas,GND_ties_verified_against_both_saved_planes=len(ref['GND_ties']['accepted']),GND_native_pad_groups_exactly_preserved=read(D/'power-audit.json')['ground_native_pad_groups_exactly_preserved'],propagation_sensitivity=[dict(assumed_uniform_effective_epsilon=e,MCU_clamp_one_way_ns=length*math.sqrt(e)/299.792458,MCU_clamp_round_trip_ns=2*length*math.sqrt(e)/299.792458) for e in [2.8,4.1,4.4]],geometry_method='Actual saved native polygons and drill envelopes; no snapping, normalization, polygon repair, tolerance-based residual suppression or electrical waiver.',limits='Positive plane contacts establish saved DC connectivity, not AC return impedance. Propagation arithmetic omits package and vertical-barrel delay and is not a field solve or waveform simulation.')
write(D/'signal-geometry-details.json',details)
# Bind original crystal/load-cap objects and the complete preferred local support to native copper.
pref=read(H/'servo1-support-review/preferred-quarter-shift-evidence.json')
def stable(o):return {k:v for k,v in o.items() if k!='net_code'}
assert all(stable(by[u])==stable(before[u]) for u in pref['protected_original_object_ids_preserved'])
for net in ['ADC_BUS','ADC_DIV_MID','+3V3_CORE','HSE_IN','HSE_OUT','HSE_XTAL_OUT']:
 assert {o['uuid']:stable(o) for o in ob if o['net']==net}=={o['uuid']:stable(o) for o in old['objects'] if o['net']==net}
support_bound=[]
for p in pref['screen_support_paths']:
 ids=[]
 for a,b in zip(p['points'],p['points'][1:]):
  matches=[o['uuid'] for o in ob if o['kind']=='track' and o['net']==p['net'] and p['layer'] in o['copper'] and o['width']==p['width'] and (o['start']==a and o['end']==b or o['start']==b and o['end']==a)]
  assert len(matches)==1,(p,a,b,matches)
  ids+=matches
 support_bound.append(dict(net=p['net'],layer=p['layer'],width=p['width'],points=p['points'],native_track_uuids=ids))
ground=[o for o in ob if o['net']=='GND']; lk={o['uuid']:o for o in ground}; shapes={l:{o['uuid']:geom(o['copper'][l]) for o in ground if l in o['copper']} for l in ['F.Cu','B.Cu']}; contacts={}
keys=['Y1.2','Y1.4','U12.2','R51.2','R52.2','C18.2','C19.2','C30.2']+[o['key'] for o in ground if o.get('ref')=='U5']
for key in keys:
 o=next(o for o in ground if o.get('key')==key); l=next(iter(o['copper'])); seen={o['uuid']}; todo=[o['uuid']]
 while todo:
  cur=todo.pop()
  for k,shape in shapes[l].items():
   if k in seen or not shapes[l][cur].intersects(shape):continue
   seen.add(k)
   if lk[k]['kind']!='via':todo.append(k)
 contacts[key]=dict(pad_xy=o['xy'],pads=sorted(lk[k]['key'] for k in seen if lk[k]['kind']=='pad'),first_vias=[dict(uuid=k,xy=lk[k]['xy']) for k in sorted(seen) if lk[k]['kind']=='via'],tracks=[{k:v for k,v in lk[u].items() if k in ['uuid','start','end','width','net']} for u in sorted(seen) if lk[u]['kind']=='track'])
assert contacts['Y1.2']['pads']==['Y1.2'] and contacts['Y1.4']['pads']==['Y1.4']
for key in ['U5.4','U5.8']:
 for v in contacts[key]['first_vias']+contacts[key]['tracks']: assert stable(by[v['uuid']])==stable(before[v['uuid']])
 contacts[key]['total_trace_centerline_mm']=sum(math.dist(t['start'],t['end']) for t in contacts[key]['tracks'])
 contacts[key]['manufacturer_function']='PGTH tied to GND' if key=='U5.4' else 'GND reference for internal circuits'
ties=[t for t in ref['GND_ties']['accepted'] if t['xy_mm'] in [[10.2299,11.7982],[13.1048,13.3702],[13.5984,13.4847],[10.2,15.35],[10.874,9.9139],[16.4574,15.8435],[10.76,18.0],[14.15,17.23]]]
assert len(ties)==8 and all(all(a>0 for a in t['positive_saved_zone_contact_area_mm2'].values()) for t in ties)
sd=D/'conditional-support-review';sd.mkdir(exist_ok=True)
for name in ['PREFERRED-QUARTER-SHIFT.md','preferred-quarter-shift-evidence.json','preferred-quarter-shift-run-summary.json','review_preferred_quarter_shift.py','YJX-TAXM8M4RDBCCT2T.pdf','YJX-TAXM8M4RDBCCT2T.txt']:
 shutil.copy2(H/'servo1-support-review'/name,sd/name)
for name in ['TPS25947.pdf','USBLC6-4-DocID11068-Rev7.pdf']:shutil.copy2(R/'independent-core-voltage-review/sources'/name,sd/name)
write(sd/'native-binding.json',dict(schema='f722-SERVO1-support-native-binding/v1',board_sha256=h,source_board_sha256=sh,preferred_evidence_sha256=sha(sd/'preferred-quarter-shift-evidence.json'),all_preferred_support_segments_bound_exactly=True,native_support_segments=support_bound,original_crystal_load_cap_object_ids_exact=pref['protected_original_object_ids_preserved'],ADC_and_CORE_and_HSE_objects_exact=True,outer_layer_contacts_to_first_vias=contacts,saved_plane_ties=ties,all116_saved_plane_ties_contact_both_planes=len(ref['GND_ties']['accepted'])==116,metrics=pref['metric'],passed=True,transient_qualified=False,numerical_power_VCAP_applicable=False))
si=D/'conditional-signal-review';si.mkdir(exist_ok=True)
for name in ['servo1-path-comparison.json','servo1-path-comparison.log','measure_servo1_paths.py','fetched-source-index.json','stm32f7x2_lqfp64.ibs','Readme.txt']:shutil.copy2(H/'signal-review'/name,si/name)
shutil.copy2(H/'signal-review/selected-pb3-speed00-model.txt',si/'selected-low-speed-model.txt');shutil.copytree(H/'signal-review/firmware',si/'firmware',dirs_exist_ok=True)
ev=read(H/'signal-review/electrical-evidence.json'); ev['schema']='f722-pinned-SERVO1-source-electrical-evidence/v1';ev['board_sha256']=h;ev['resource'].update(servo=1,gpio='PB4',package_pin=56);ev['resource'].pop('alternate_function',None)
ev['IBIS'].update(package_pin_R_ohm=.049290,package_pin_L_nH=2.180,package_pin_C_pF=.020000);ev['U12']['bonded_IO_pin']=1
ev['R20']=ev.pop('R23');ev['R20']['position']='25.599422 mm beyond clamp; about43.657758 mm drawn branch inventory from MCU; not driver-end source termination'
ev['assessment']=dict(geometry_checkpoint_recommended_conditionally=True,electrical_release_qualified=False,limits=['Pinned firmware source, no installed register readback','Manufacturer LOW-speed maximum is not a guaranteed minimum edge time','External receiver and cable are unspecified','No board/cable distributed waveform or ESD simulation','U12 shares return with eFuse OVCSEL/ILM; transient coupling unqualified','Fresh loaded power and VCAP validation pending'])
assert next(f for f in g['footprints'] if f['ref']=='R20')['value']=='470R / 1% / 0.20W'
pin=next(line for line in (si/'stm32f7x2_lqfp64.ibs').read_text().splitlines() if line.split()[:2]==['56','PB4']);assert 'io8p_arsudq_ft' in pin
ev['IBIS']['exact_pin_line']=pin;ev['IBIS']['file_sha256']=sha(si/'stm32f7x2_lqfp64.ibs');write(si/'electrical-evidence.json',ev)
print(json.dumps(dict(board_sha256=h,reference_fragments=len(residual),residual_area_mm2=sum(x['fragment']['area_mm2'] for x in residual),GND_ties=len(ref['GND_ties']['accepted']),via_count=len(margins),minimum_via_rule_surplus_mm=min(v for row in margins for v in row['excess_over_rules_mm'].values()),U5_ground_keys=[k for k in keys if k.startswith('U5.')],support_bound_segments=sum(len(x['native_track_uuids']) for x in support_bound))))
