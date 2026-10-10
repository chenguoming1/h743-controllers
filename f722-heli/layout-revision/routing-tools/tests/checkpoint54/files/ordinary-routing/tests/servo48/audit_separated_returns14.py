"""Finite native entries, exact source transaction and support continuity for TAIL fallback."""
import json,pathlib,sys,hashlib,math,copy,collections
H=pathlib.Path(__file__).resolve().parent;R=H.parents[1];S=H.parent/'rpm17/candidate01';D=H/'candidate06';sys.path[:0]=[str(R/'dsm40-audits'),str(R/'dsm41-audits'),str(R.parent/'integrated-routing')]
from audit_dsm40_entries_return import pad_entry,join_entry,groups,geom
from audit_dsm41_entries_return import via_entry
from shapely.geometry import Point
sha=lambda p:hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest();read=lambda p:json.loads(pathlib.Path(p).read_text());write=lambda n,v:(D/n).write_text(json.dumps(v,indent=2)+'\n')
before=read(S/'f722-heli.native.json');after=read(D/'f722-heli.native.json');prov=read(D/'construction-provenance.json');oldh=sha(S/'f722-heli.kicad_pcb');h=sha(D/'f722-heli.kicad_pcb');assert oldh==before['board_sha256']==prov['source_board_sha256']and h==after['board_sha256']==prov['board_sha256']
old={o['uuid']:o for o in before['objects']};new={o['uuid']:o for o in after['objects']};physical=lambda o:{k:v for k,v in o.items()if k!='net_code'};removed={o['uuid']for o in prov['removed_source_records']};added=prov['added_records'];tracks=[o for o in new.values()if o['kind']=='track'];pads=[o for o in new.values()if o['kind']=='pad'];vias=[o for o in new.values()if o['kind']=='via'];newtracks=[o for o in added if o['kind']=='track'];newvias=[o for o in added if o['kind']=='via']
changed={p['before']['uuid']for p in prov['changed_pad_records']}
assert old.keys()-new.keys()==removed and new.keys()-old.keys()=={o['uuid']for o in added};assert all(physical(o)==physical(new[u])for u,o in old.items()if u not in removed|changed);assert not changed
assert before['footprints']==after['footprints']
assert {o['net']for o in prov['removed_source_records']}=={'GND'} and all(o['net']=='GND'for o in added)
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

from shapely.ops import unary_union
base=read(S/'power-audit.json');nets={}
for net in base['nets']:
 a,b=groups(before,net),groups(after,net);assert a==b and len(b)==1,(net,a,b);nets[net]={'groups':b,'pad_group_count':1,'complete':True,'source_groups_exactly_preserved':True}
signals={}
for net in ['SERVO1_MCU','SERVO2_MCU','SERVO3_MCU','TAIL_MCU','ESC_MCU','RPM_LV','RPM_MCU','ADC_DIV_MID','ADC_BUS','SBUS_MCU','SBUS_LV','PORT_A_RX_EXT','PORT_A_TX_EXT','PORT_B_RX_EXT','PORT_B_TX_EXT','PORT_A_RX_MCU','PORT_A_TX_MCU','PORT_B_RX_MCU','PORT_B_TX_MCU','BARO_SCL','BARO_SDA']:
 a,b=groups(before,net),groups(after,net);assert a==b and len(b)==1,(net,a,b);signals[net]={'groups':b,'complete':True,'source_partitions_preserved':True}
assert {u:physical(o)for u,o in old.items()if o['net']!='GND'}=={u:physical(o)for u,o in new.items()if o['net']!='GND'}
# Actual local copper contact graph stops at the first vias, before the planes.
def local_contacts(native):
 ground=[o for o in native['objects']if o['net']=='GND'];lk={o['uuid']:o for o in ground};ss={l:{o['uuid']:geom(o['copper'][l])for o in ground if l in o['copper']}for l in ['F.Cu','B.Cu']};out={}
 for key in ['U12.2','R51.2','R52.2','Y1.2','Y1.4','C18.2','C19.2','C30.2','U5.4','U5.8']:
  o=next(o for o in ground if o.get('key')==key);l=next(iter(o['copper']));seen={o['uuid']};todo=[o['uuid']]
  while todo:
   cur=todo.pop()
   for k,shape in ss[l].items():
    if k in seen or not ss[l][cur].intersects(shape):continue
    seen.add(k)
    if lk[k]['kind']!='via':todo.append(k)
  ts=[{k:v for k,v in lk[u].items()if k in ['uuid','start','end','width','net']}for u in sorted(seen)if lk[u]['kind']=='track']
  out[key]=dict(pad_xy=o['xy'],layer=l,pads=sorted(lk[u]['key']for u in seen if lk[u]['kind']=='pad'),first_vias=[dict(uuid=u,xy=lk[u]['xy'])for u in sorted(seen)if lk[u]['kind']=='via'],tracks=ts,total_trace_centerline_mm=sum(math.dist(t['start'],t['end'])for t in ts))
 return out
contacts=local_contacts(after);previous=local_contacts(before)
assert contacts['U12.2']['pads']==['U12.2'] and contacts['R51.2']['pads']==['R51.2'] and contacts['R52.2']['pads']==['C30.2','R52.2']
assert [v['xy']for v in contacts['U12.2']['first_vias']]==[[13.5984,13.4847]]
assert [v['xy']for v in contacts['R51.2']['first_vias']]==[[12.045672,13.000917]]
assert [v['xy']for v in contacts['R52.2']['first_vias']]==[[16.4574,15.8435]]
for k in ['Y1.2','Y1.4','C18.2','C19.2','U5.4','U5.8']:assert contacts[k]==previous[k],k
# Finite annular contact to both actual saved ground planes for all reviewed ties.
plane={l:unary_union([geom(z['filled'][l])for z in after['zones']if not z['rule']and z['net']=='GND'and l in z['filled']])for l in ['In1.Cu','In4.Cu']};tieids={v['uuid']for row in contacts.values()for v in row['first_vias']};ties=[]
for u in sorted(tieids):
 v=new[u];ann={l:geom(v['copper'][l]).difference(geom(v['drill']['outside']))for l in plane};areas={l:ann[l].intersection(g).area for l,g in plane.items()};assert all(a>0 for a in areas.values()),(u,areas);ties.append(dict(uuid=u,xy_mm=v['xy'],positive_saved_zone_annular_contact_area_mm2=areas))
assert len(newtracks)==7 and len(newvias)==1 and len(resolved)==14
v=newvias[0];assert any(r['via_uuid']==v['uuid']for r in annular) if annular and 'via_uuid'in annular[0]else bool(annular)
# Native process margins, both-side masks, foreign copper, and all drill envelopes.
mask=[(o,l,geom(v['polygons']))for o in after['objects']if o.get('smd')for l,v in o.get('mask',{}).items()];drills=[(o,geom(o['drill']['outside']))for o in after['objects']if o.get('drill')];copper=[(o,l,geom(s))for o in after['objects']for l,s in o.get('copper',{}).items()];outline=geom(after['outline_with_npth']['polygons']);margins=[]
for rec in newvias:
 v=new[rec['uuid']];dr=geom(v['drill']['outside']);vc={l:geom(s)for l,s in v['copper'].items()};gm,mo,ml=min((dr.distance(s),o['key'],l)for o,l,s in mask);gd,du=min((dr.distance(s),o['uuid'])for o,s in drills if o['uuid']!=v['uuid']);gc,cu,cl,cn=min((vc[l].distance(s),o['uuid'],l,o['net'])for o,l,s in copper if o['net']!='GND'and l in vc);ge=dr.distance(outline.boundary);ex=dict(mask=gm-.2,drill=gd-.25,copper=gc-.127,edge_NPTH=ge-.254);assert all(x>=0 for x in ex.values())and outline.covers(dr);margins.append(dict(uuid=v['uuid'],xy_mm=v['xy'],drill_to_SMT_mask_mm=gm,limiting_mask=mo,mask_layer=ml,drill_to_drill_mm=gd,other_drill_uuid=du,copper_clearance_mm=gc,other_copper_uuid=cu,other_copper_net=cn,copper_layer=cl,drill_to_edge_or_NPTH_mm=ge,excess_over_rules_mm=ex,tented=v['tented']))
controls=[];padby={o['key']:o for o in pads};entry=next(t for t in newtracks if t['start']==[12.6,11.8875]);bad=copy.deepcopy(entry);bad['width']=2;controls.append(dict(name='oversized_U12_ground_pad_entry',rejected=not pad_entry(bad,padby['U12.2'],'F.Cu','start')['passed']))
bad=copy.deepcopy(after);bad['objects']=[o for o in bad['objects']if o['uuid']!=v['uuid']];controls.append(dict(name='remove_new_R51_plane_tie',rejected=len(groups(bad,'GND'))>len(groups(after,'GND'))));assert all(x['rejected']for x in controls),controls
rpm=read(S/'construction-provenance.json');rpm_ids={o['uuid']for o in rpm['added_records']};assert len(rpm_ids)==24 and all(physical(new[u])==physical(old[u])for u in rpm_ids)
audit=dict(schema='f722-separated-local-ground-native-entry-support/v1',passed=True,board_sha256=h,source_board_sha256=oldh,source_native_sha256=sha(S/'f722-heli.native.json'),native_sha256=sha(D/'f722-heli.native.json'),new_track_endpoints_checked=len(resolved),new_tracks=len(newtracks),new_vias=len(newvias),strict_pad_entries=entries,finite_actual_annular_entries=annular,full_width_joins=joins,endpoint_inventory=resolved,partial_pad_entries_not_used_as_proof=partial,nets=nets,signal_groups=signals,all156_full_footprints_exact=True,all_non_GND_objects_exact=True,all24_RPM_additive_objects_exact=True,RPM_additive_object_ids=sorted(rpm_ids),previous_outer_layer_contacts_to_first_vias=previous,outer_layer_contacts_to_first_vias=contacts,saved_plane_ties=ties,new_via_process_margins=margins,negative_controls=controls,numerical_power_VCAP_applicable=False,ESD_AC_ADC_noise_qualified=False)
write('entry-support-audit.json',audit);binding=dict(source_board_sha256=oldh,board_sha256=h,source_native_sha256=sha(S/'f722-heli.native.json'),native_sha256=sha(D/'f722-heli.native.json'),audit='entry-support-audit.json',audit_sha256=sha(D/'entry-support-audit.json'))
write('endpoint-audit.json',dict(schema='f722-native-endpoint-audit-binding/v1',passed=True,**binding,new_track_endpoints_checked=len(resolved),direct_pad_entries=len(entries),full_width_joins=len(joins),finite_annular_entries=len(annular),new_vias=1,strict_pad_entries_all_pass=True,negative_controls=len(controls)))
write('power-audit.json',dict(schema='f722-native-support-audit/v1',passed=True,**binding,source_audit_sha256=sha(S/'power-audit.json'),audit_source_sha256=sha(__file__),nets=nets,ground_native_pad_groups_exactly_preserved=True,numerical_power_VCAP_applicable=False,method='Exact native copper/pad/barrel/filled-plane graph recomputed for28support nets. Separate outer-layer first-via graph proves U12, R51 and R52/C30 branches do not rejoin before their intended plane ties. All other native objects and156poses exact. No loaded/transient equivalence claimed.'))
print(json.dumps(dict(passed=True,board_sha256=h,endpoints=len(resolved),support_groups=len(nets),signal_groups=len(signals),reviewed_plane_ties=len(ties),local_pads={k:contacts[k]['pads']for k in ['U12.2','R51.2','R52.2']})))
