#!/usr/bin/env python3
"""Preferred support screen review; static local geometry, no board edits or qualification."""
import json,hashlib,math
from pathlib import Path
from shapely.geometry import Polygon,LineString
from shapely.ops import unary_union
H=Path(__file__).resolve().parent;R=H.parents[2]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
files={'screen':H.parent/'u12-r50-quarter-shift17-screen.json','native':R/'tests/sbus-nrst49/candidate02/f722-heli.native.json','board':R/'tests/sbus-nrst49/candidate02/f722-heli.kicad_pcb','original_evidence':H/'evidence.json','datasheet':H/'YJX-TAXM8M4RDBCCT2T.pdf'}
before={k:sha(p) for k,p in files.items()}
historical={p.name:sha(p) for p in [H/'REPORT.md',H/'evidence.json',H/'ALTERNATIVE-V5.md',H/'alternative-v5-evidence.json']}
s=json.loads(files['screen'].read_text());n=json.loads(files['native'].read_text());e=json.loads(files['original_evidence'].read_text());obs={o['uuid']:o for o in n['objects']};remove=set(s['removed_ids'])
assert before['screen']=='23c445977b5fcc82ac488a3e1094bbb851e9654246eeaa1305cd8b3c4597792a'
assert s['source']==n['board_sha256']==before['board']=='71d33748909bb960c5829973642272460607d8521831a6212975f7de6790d660'
assert s['pose']=={'ref':'R50','xy':[11.95,13.6],'angle':0}
assert all(not x['violations'] and x['minimum']['pass_with_polygon_error'] for x in s['paths']+s['vias'])
assert all(x['passed'] for x in s['mutual'])
protected=set()
for key in ['Y1.2','Y1.4','C18.2','C19.2','C30.2']:
 c=e['original_outer_layer_contacts'][key];protected.update(c['connected_trace_ids']);protected.update(v['uuid'] for v in c['first_vias'])
protected.update(o['uuid'] for o in n['objects'] if o.get('ref') in ['Y1','R9','C18','C19'] or o['net'].startswith('HSE'))
assert not(protected & remove)
assert not any(x['net'].startswith('HSE') for x in s['paths']+s['vias'])
assert not any(x['net']=='GND' and x['layer']=='B.Cu' for x in s['paths'])
def geom(ps):return unary_union([Polygon(x['outer'],x['holes']) for x in ps])
ground=[o for o in n['objects'] if o['net']=='GND' and o['uuid'] not in remove];lk={o['uuid']:o for o in ground}
shapes={l:{o['uuid']:geom(o['copper'][l]) for o in ground if l in o['copper']} for l in ['F.Cu','B.Cu']}
for i,x in enumerate(s['paths']):
 if x['net']!='GND':continue
 k=f'path-{i}';shapes[x['layer']][k]=LineString(x['points']).buffer(x['width']/2,quad_segs=48);lk[k]={'kind':'track','uuid':k}
contacts={}
for key in ['Y1.2','Y1.4','U12.2','R51.2','R52.2','C18.2','C19.2','C30.2']:
 o=next(o for o in ground if o.get('key')==key);l=next(iter(o['copper']));seen={o['uuid']};todo=[o['uuid']]
 while todo:
  cur=todo.pop()
  for k,g in shapes[l].items():
   if k in seen or not shapes[l][cur].intersects(g):continue
   seen.add(k)
   if lk[k]['kind']!='via':todo.append(k)
 contacts[key]={'pads':sorted(lk[k]['key'] for k in seen if lk[k]['kind']=='pad'),'first_vias':[{'uuid':k,'xy':lk[k]['xy']} for k in sorted(seen) if lk[k]['kind']=='via'],'trace_ids':sorted(k for k in seen if lk[k]['kind']=='track')}
assert contacts['Y1.2']['pads']==['Y1.2'] and contacts['Y1.4']['pads']==['Y1.4']
assert [v['xy'] for v in contacts['Y1.4']['first_vias']]==[[13.1048,13.3702]]
assert [v['xy'] for v in contacts['Y1.2']['first_vias']]==[[10.2299,11.7982]]
assert [v['xy'] for v in contacts['U12.2']['first_vias']]==[[13.5984,13.4847]]
plane=[]
for xy in [[10.2299,11.7982],[13.1048,13.3702],[13.5984,13.4847],[10.2,15.35],[10.874,9.9139],[16.4574,15.8435]]:
 v=next(o for o in ground if o['kind']=='via' and o['xy']==xy)
 for z in n['zones']:
  if z['rule'] or z['net']!='GND':continue
  for l,ps in z['filled'].items():
   area=geom(v['copper'][l]).difference(geom(v['drill']['outside'])).intersection(geom(ps)).area
   plane.append({'via_xy':xy,'layer':l,'zone_uuid':z['uuid'],'filled_polygon_count':len(ps),'contact_area_mm2_after_drill_subtraction':area})
assert all(x['contact_area_mm2_after_drill_subtraction']>0 for x in plane)
length=lambda pts:sum(math.dist(a,b) for a,b in zip(pts,pts[1:]))
ps=s['paths'];shared=length([[12.5,12.72],[13.5984,12.92],[13.5984,13.4847]])
en=next(x for x in ps if x['net']=='EFUSE_EN');r_en=1.724e-8*(length(en['points'])/1000)/(.127*.035/1e6)
metric={'U12_return_mm':length(ps[2]['points']),'R51_return_mm':length(ps[7]['points'])+shared,'R51_own_0p20mm_lead_mm':length(ps[7]['points']),'U12_R51_shared_0p25mm_lead_mm':shared,'R52_return_mm':length(ps[8]['points']),'Y1_2_return_mm':1.0500177379454108,'Y1_4_return_mm':1.0499671804394646,'C18_return_mm':1.4557929263738298,'C19_return_mm':1.250025283744292,'C30_return_mm':1.2499868039303457,'EN_length_mm':length(en['points']),'EN_width_mm':.127,'EN_nominal_R_ohm_at_35um_copper':r_en,'EN_drop_at_0p1uA_V':r_en*1e-7,'EN_drop_at_23V_over_1p485Mohm_V':r_en*23/1485000,'VX_branch_to_R50_mm':length(ps[5]['points']),'VX_feeder_mm':length(ps[9]['points']),'VX_lower_branch_mm':length(ps[10]['points']),'crystal4_to_eFuse_via_center_separation_mm':math.dist([13.1048,13.3702],[13.5984,13.4847])}
result={'status':'Preferred measured local support proposal; supersedes historical ab19 shared-crystal and v5 crystal-bridge alternatives. Final transaction/native gates pending.','inputs':{k:{'path':str(p),'sha256':before[k]} for k,p in files.items()},'historical_reports_preserved':historical,'pose':s['pose'],'screen_counts':{'paths':len(ps),'vias':len(s['vias']),'mutual':len(s['mutual']),'all_saved_checks_pass':True},'screen_minimum_path_extra_clearance_mm':min(x['minimum']['extra_clearance_mm'] for x in ps),'screen_minimum_via_extra_clearance_mm':min(x['minimum']['extra_clearance_mm'] for x in s['vias']),'screen_minimum_mutual_gap_mm':min(x['gap_mm'] for x in s['mutual']),'screen_support_paths':[dict(x,index=i) for i,x in enumerate(ps) if x['net'] in ['GND','EFUSE_EN','VX_RAW']],'metric':metric,'protected_original_object_ids_preserved':sorted(protected),'outer_layer_contacts_ideal_proposal':contacts,'saved_native_plane_contacts':plane,'efuse_input_limits_and_conditions_from_original_review':{k:v for k,v in e['efuse_dc'].items() if not k.startswith(('trace_','copper_','nominal_','new_trace_'))},'conditions':['Only the local screens are passed, not native DRC/refill.','Original separate Y1 grounds are retained, but common system-plane impedance is not modeled.','U12 now shares eFuse ground via and 1.681160 mm trace with R51; transient coupling remains unqualified.','New ground or route adjacency can affect parasitics; unchanged signal objects do not establish complete unchanged electromagnetic environment.','Broader VX_RAW reconstruction is geometry only, no fresh loaded-power or transient verification.']}
assert before=={k:sha(p) for k,p in files.items()};assert historical=={name:sha(H/name) for name in historical}
(H/'preferred-quarter-shift-evidence.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'metric':metric,'saved_checks':result['screen_counts'],'historical_reports_unchanged':True,'plane_contacts':len(plane)},indent=2))
