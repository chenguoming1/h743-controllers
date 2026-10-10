"""Source-bound finite native entries and complete donor/support partitions."""
import json,pathlib,sys,hashlib,math,copy,time
from shapely.geometry import Point
from shapely import unary_union
H=pathlib.Path(__file__).resolve().parent;R=H.parents[1];S=R/'candidate55';D=H/'candidate02';START=time.monotonic()
sys.path[:0]=[str(R/'dsm40-audits'),str(R/'dsm41-audits'),str(R.parent/'integrated-routing')]
from audit_dsm40_entries_return import pad_entry,join_entry,groups,geom
from audit_dsm41_entries_return import via_entry
read=lambda p:json.loads(pathlib.Path(p).read_text());sha=lambda p:hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest();write=lambda n,v:(D/n).write_text(json.dumps(v,indent=2)+'\n')
before=read(S/'f722-heli.native.json');after=read(D/'f722-heli.native.json');prov=read(D/'construction-provenance.json');oldh=sha(S/'f722-heli.kicad_pcb');h=sha(D/'f722-heli.kicad_pcb');assert before['board_sha256']==oldh==prov['source_board_sha256'] and after['board_sha256']==h==prov['board_sha256']
old={o['uuid']:o for o in before['objects']};new={o['uuid']:o for o in after['objects']};physical=lambda o:{k:v for k,v in o.items()if k!='net_code'};removed={o['uuid']for o in prov['removed_source_records']};added=prov['added_records'];changed={o['before']['uuid']for o in prov['changed_pad_records']}
assert old.keys()-new.keys()==removed and new.keys()-old.keys()=={o['uuid']for o in added};assert all(physical(o)==physical(new[u])for u,o in old.items()if u not in removed|changed)
assert len(removed)==0 and len(added)==15 and len(changed)==2
assert all(old[u]['ref']=='R4' and old[u]['key']==new[u]['key'] and old[u]['net']==new[u]['net']for u in changed)
tracks=[o for o in new.values()if o['kind']=='track'];pads=[o for o in new.values()if o['kind']=='pad'];vias=[o for o in new.values()if o['kind']=='via'];newtracks=[o for o in added if o['kind']=='track'];newvias=[o for o in added if o['kind']=='via']

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

entries=[];annular=[];joins=[];endpoints=[];partial=[]
for t in newtracks:
 layer=next(iter(t['copper']))
 for end in ['start','end']:
  xy=t[end];hits=[]
  for p in pads:
   if p.get('drill')or p['net']!=t['net']or layer not in p['inside']or not geom(p['inside'][layer]).contains(Point(xy)):continue
   r=custom_pad_entry(t,p,layer,end)if geom(p['inside'][layer]).convex_hull.difference(geom(p['inside'][layer])).area>=1e-12 else pad_entry(t,p,layer,end)
   if r['passed']:entries.append(r);hits.append({'pad':p['key']})
   else:partial.append(r)
  for v in vias:
   if v['net']==t['net']and xy==v['xy']:
    r=via_entry(t,v,layer,after);assert r['passed'],r;annular.append(r);hits.append({'via':v['uuid']})
  for o in tracks:
   if o['uuid']==t['uuid']or o['net']!=t['net']or layer not in o['copper']or xy not in [o['start'],o['end']]:continue
   r=join_entry(t,o,layer,min(t['width'],o['width']));assert r['passed'],r;joins.append(r);hits.append({'track':o['uuid']})
  assert hits,(t['uuid'],t['net'],end,xy,partial);endpoints.append(dict(track=t['uuid'],net=t['net'],endpoint=end,xy=xy,connections=hits))
print('finite_endpoints',len(endpoints),flush=True)
basepower=read(S/'power-audit.json');nets={};signals={}
for net in basepower['nets']:
 a,b=groups(before,net),groups(after,net);assert a==b and len(b)==1,(net,a,b);nets[net]=dict(groups=b,before_groups=len(a),after_groups=len(b),complete=True,source_groups_exactly_preserved=True)
for net in sorted({o['net']for o in added if o['net']!='GND'}):
 a,b=groups(before,net),groups(after,net)
 if net=='FLASH_CS':
  assert len(a)==3 and len(b)==2,(net,a,b)
  assert any(set(x['pads'])=={'R4.2','U3.1'} for x in b) and any(x['pads']==['U1.33'] for x in b)
 else:assert a==b and len(b)==1,(net,a,b)
 signals[net]=dict(before=a,after=b,complete=(len(b)==1),intended_pullup_branch_complete=True,source_partitions_preserved=(a==b))
# Every unchanged non-ground net retains its exact conductive objects; source fill only affects GND.
changednets={o['net']for o in added}|{o['net']for o in prov['removed_source_records']}
unchangednets=sorted({o['net']for o in old.values()}-changednets)
for net in unchangednets:assert {u:physical(o)for u,o in old.items()if o['net']==net}=={u:physical(o)for u,o in new.items()if o['net']==net}
print('support_groups',len(nets),'changed_signal_groups',len(signals),flush=True)
# Explicit full-width replacement for the conducting role of the original R4 pad.
bridge=next(t for t in newtracks if t['net']=='+3V3_CORE' and t['start']==[28.01,19.8] and t['end']==[28.25,17.98])
leaf=new['4d92c569-21f9-4a2f-a9fa-75ceb96db10b'];c3=next(p for p in pads if p['key']=='C3.1')
junction=dict(bridge_uuid=bridge['uuid'],retained_leaf_uuid=leaf['uuid'],old_R4_pad_no_longer_used=True,full_width_join=join_entry(bridge,leaf,'B.Cu',.20),actual_C3_entry=pad_entry(bridge,c3,'B.Cu','end'),all_original_CORE_objects_retained=True)
assert junction['full_width_join']['passed'] and junction['actual_C3_entry']['passed']
assert all(physical(o)==physical(new[u]) for u,o in old.items() if o['net']=='+3V3_CORE' and u not in changed)
# The corrected supply route terminates deliberately on C15, without C14 or remote-via overlap.
feed_shape=unary_union([geom(new[u]['copper']['B.Cu']) for u in prov['routes'][0]])
c15=next(p for p in pads if p['key']=='C15.1');c14=next(p for p in pads if p['key']=='C14.1')
c15_lead=new['a31c2226-97c3-48f7-b672-1e3a574d1b51']
feed_contact=dict(terminal='C15.1',C14_pad_overlap_mm2=feed_shape.intersection(geom(c14['copper']['B.Cu'])).area,C15_lead_contact_outside_actual_pad_mm2=feed_shape.intersection(geom(c15_lead['copper']['B.Cu'])).difference(geom(c15['inside']['B.Cu'])).area)
assert feed_contact['C14_pad_overlap_mm2']==0 and feed_contact['C15_lead_contact_outside_actual_pad_mm2']==0,feed_contact
controls=[];t=next(t for t in newtracks if t['net']=='FLASH_CS' and t['end']==[40.04,19]);pad=next(p for p in pads if p['key']=='R4.2');bad=copy.deepcopy(t);bad['width']=2;controls.append(dict(name='oversized_R4_CS_entry',rejected=not pad_entry(bad,pad,'B.Cu','end')['passed']))
bad=copy.deepcopy(after);bad['objects']=[o for o in bad['objects']if o['uuid']!=newvias[0]['uuid']];controls.append(dict(name='remove_required_CS_transition',rejected=len(groups(bad,'FLASH_CS'))>len(groups(after,'FLASH_CS'))));assert all(c['rejected']for c in controls)
audit=dict(schema='f722-R4-pullup-entry-support-native55/v1',passed=True,board_sha256=h,source_board_sha256=oldh,native_sha256=sha(D/'f722-heli.native.json'),source_native_sha256=sha(S/'f722-heli.native.json'),new_tracks=len(newtracks),new_vias=len(newvias),new_track_endpoints_checked=len(endpoints),strict_pad_entries=entries,finite_actual_annular_entries=annular,full_width_joins=joins,endpoint_inventory=endpoints,partial_pad_entries_not_used_as_proof=partial,nets=nets,signal_groups=signals,unchanged_net_objects_exact=unchangednets,reconstructed_CORE_junction=junction,deliberate_C15_feed_contact=feed_contact,negative_controls=controls,numerical_power_qualified=False,signal_quality_qualified=False,reference_AC_qualified=False,seconds=time.monotonic()-START)
write('entry-support-audit.json',audit);binding=dict(source_board_sha256=oldh,board_sha256=h,source_native_sha256=sha(S/'f722-heli.native.json'),native_sha256=sha(D/'f722-heli.native.json'),audit='entry-support-audit.json',audit_sha256=sha(D/'entry-support-audit.json'))
write('endpoint-audit.json',dict(schema='f722-native-endpoint-audit-binding/v1',passed=True,**binding,new_track_endpoints_checked=len(endpoints),strict_pad_entries_all_pass=True,new_vias=len(newvias),negative_controls=controls))
write('power-audit.json',dict(schema='f722-native-support-audit/v1',passed=True,**binding,nets=nets,ground_native_pad_groups_exactly_preserved=True,numerical_power_qualified=False,method='Recomputed exact native copper/pad/barrel/filled-plane groups for every28support net; Original CORE junction reconstructed with a full-width .20 mm lead and actual C3 contact; all original copper retained. Fresh numerical power/VCAP remains pending.'))
print('TERMINAL',h,len(endpoints),audit['seconds'],flush=True)
