import pathlib,sys,json,hashlib,copy,math,collections
H=pathlib.Path(__file__).resolve().parent;ROOT=H.parents[2];S=ROOT/'ordinary-routing/candidate46';D=H/'candidate01';sys.path[:0]=[str(ROOT/'ordinary-routing/dsm40-audits'),str(ROOT/'ordinary-routing/dsm41-audits'),str(ROOT/'integrated-routing')]
from audit_dsm40_entries_return import pad_entry,join_entry,groups,geom
from audit_dsm41_entries_return import via_entry
from verify_support_adoption import verify
from shapely.geometry import Point,LineString
read=lambda f:json.loads(pathlib.Path(f).read_text());sha=lambda f:hashlib.sha256(pathlib.Path(f).read_bytes()).hexdigest();write=lambda f,r:pathlib.Path(f).write_text(json.dumps(r,indent=2)+'\n')
before=read(S/'f722-heli.native.json');after=read(D/'f722-heli.native.json');p=read(D/'construction-provenance.json');h=sha(D/'f722-heli.kicad_pcb');oldh=sha(S/'f722-heli.kicad_pcb');assert h==after['board_sha256']==p['board_sha256'];assert oldh==before['board_sha256']==p['source_board_sha256']=='87c5ced471edaf2e0ace382d4236bc1787efb869b7ae759c53d87ee76165c0cb'
old={o['uuid']:o for o in before['objects']};new={o['uuid']:o for o in after['objects']};removed={o['uuid']for o in p['removed_source_records']};added=p['added_records'];assert len(removed)==4 and len(added)==23 and len(old)==1950;assert set(old)-set(new)==removed and set(new)-set(old)=={o['uuid']for o in added};assert all(new[u]==o for u,o in old.items()if u not in removed)
assert before['footprints']==after['footprints'];assert all(o['net']in ['SBUS_HV','+3V3_CORE','ADC_DIV_MID']for o in added);assert all(new[u]==o for u,o in old.items()if o['net']in ['GND','RPM_HV'])
tracks=[o for o in after['objects']if o['kind']=='track'];pads=[o for o in after['objects']if o['kind']=='pad'];vias=[o for o in after['objects']if o['kind']=='via'];entries=[];joins=[];annular=[];classified=[];seen=set()
for t in added:
 if t['kind']!='track':continue
 layer=next(iter(t['copper']));width=.2 if t['net']=='+3V3_CORE'else.127;assert t['width']==width
 for endpoint in ['start','end']:
  xy=t[endpoint];hp=[x for x in pads if x['net']==t['net']and layer in x['inside']and geom(x['inside'][layer]).contains(Point(xy))];ht=[x for x in tracks if x['uuid']!=t['uuid']and x['net']==t['net']and layer in x['copper']and xy in [x['start'],x['end']]];hv=[x for x in vias if x['net']==t['net']and layer in x['copper']and x['xy']==xy];classified.append({'track_uuid':t['uuid'],'net':t['net'],'layer':layer,'endpoint':endpoint,'xy':xy,'pads':[x['key']for x in hp],'tracks':[x['uuid']for x in ht],'vias':[x['uuid']for x in hv],'resolved':bool(hp or ht or hv)})
  for x in hp:entries.append(pad_entry(t,x,layer,endpoint))
  for x in ht:
   key=('join',*sorted([t['uuid'],x['uuid']]),layer)
   if key not in seen:seen.add(key);joins.append(join_entry(t,x,layer,width))
  for x in hv:
   key=('via',t['uuid'],x['uuid'],layer)
   if key not in seen:seen.add(key);annular.append(via_entry(t,x,layer,after))
assert len(classified)==40 and all(x['resolved']for x in classified);assert all(x['passed']for x in entries+joins+annular)
sg=groups(before,'SBUS_HV');ng=groups(after,'SBUS_HV');assert len(sg)==2 and len(ng)==1 and ng[0]['pads']==['Q2.3','R26.2','U16.2'];assert groups(before,'RPM_HV')==groups(after,'RPM_HV')
controls=[]
for e in entries:
 bad=copy.deepcopy(new[e['track_uuid']]);bad['width']=2.;controls.append({'name':'oversized_pad_'+e['pad'],'rejected':not pad_entry(bad,new[e['pad_uuid']],e['layer'],e['endpoint'])['passed']})
for e in annular:
 if any(c['name']=='drill_only_'+e['via_uuid']for c in controls):continue
 bad=copy.deepcopy(new[e['via_uuid']]);bad['drill']['outside']=bad['copper'][e['layer']];controls.append({'name':'drill_only_'+e['via_uuid'],'rejected':not via_entry(new[e['track_uuid']],bad,e['layer'],after)['passed']})
for net,w in [('+3V3_CORE',.2),('ADC_DIV_MID',.127),('SBUS_HV',.127)]:
 e=next(e for e in joins if e['net']==net);a,b=[new[u]for u in e['track_uuids']];bad=copy.deepcopy(a);bad['width']=w-.001;controls.append({'name':'narrowed_join_'+net,'rejected':not join_entry(bad,b,e['layer'],w)['passed']})
bad=copy.deepcopy(after);bad['objects']=[o for o in bad['objects']if not(o['uuid']in set(new)-set(old)and o['net']=='SBUS_HV')];controls.append({'name':'remove_new_SBUS_branch','rejected':len(groups(bad,'SBUS_HV'))==2});assert all(c['rejected']for c in controls)
base=read(S/'power-audit.json');nets={}
for net in base['nets']:
 current=groups(after,net);previous=groups(before,net);assert current==previous and len(current)==1
 nets[net]={'pad_group_count':len(current),'complete':True,'groups':current,'source_groups_exactly_preserved':True}
assert len(nets)==28
coreold=[o for o in p['removed_source_records']if o['net']=='+3V3_CORE'and o['kind']=='track'];corenew=[o for o in added if o['net']=='+3V3_CORE'and o['kind']=='track'];assert len(coreold)==len(corenew)==2 and all(o['width']==.2 for o in coreold+corenew);lens=lambda oo:sum(math.dist(o['start'],o['end'])for o in oo);cr={'before_length_mm':lens(coreold),'after_length_mm':lens(corenew),'delta_length_mm':lens(corenew)-lens(coreold),'width_mm':.2,'source_ends_unchanged':sorted([x for o in coreold for x in [o['start'],o['end']]if x!=[17.110541,9.777898]])==sorted([x for o in corenew for x in [o['start'],o['end']]if x!=[17.1,9.84]]),'all_native_CORE_pad_groups_preserved':True,'all_capacitor_pads_and_GND_objects_exact':True,'numerical_applicability_pending':True};assert cr['source_ends_unchanged']
binding={'board_sha256':h,'source_board_sha256':oldh,'native_sha256':sha(D/'f722-heli.native.json'),'source_native_sha256':sha(S/'f722-heli.native.json')};gates={'all40_new_track_endpoints_resolved':True,'finite_pad_entries':all(x['passed']for x in entries),'full_width_joins':all(x['passed']for x in joins),'finite_actual_annular_entries':all(x['passed']for x in annular),'all28_support_groups_exact':True,'all1946_retained_objects_exact':True,'all156_footprints_exact':True,'complete_SBUS_HV':True,'RPM_HV_unchanged':True,'CORE_width_and_endpoints_preserved':True,'negative_controls':all(x['rejected']for x in controls)}
r={'schema':'f722-SBUS-coordinated-entry-support/v1','passed':True,**binding,'gates':gates,'audit_source_sha256':sha(__file__),'classified_endpoints':classified,'strict_pad_entries':entries,'full_width_joins':joins,'finite_actual_annular_entries':annular,'negative_controls':controls,'CORE_local_feed_review':cr,'SBUS_before_groups':sg,'SBUS_after_groups':ng,'nets':nets,'numerical_power_VCAP_applicable':False};write(D/'entry-support-audit.json',r);binding.update(audit='entry-support-audit.json',audit_sha256=sha(D/'entry-support-audit.json'))
write(D/'endpoint-audit.json',{'schema':'f722-native-endpoint-audit-binding/v1','passed':True,**binding,'new_track_endpoints_checked':len(classified),'direct_pad_entries':len(entries),'full_width_joins':len(joins),'actual_annular_entries':len(annular),'strict_pad_entries_all_pass':True,'negative_controls':len(controls),'scope':'All20 new tracks:14 SBUS,2 CORE supply and4 ADC_DIV_MID. Both new SBUS vias, moved CORE via and existing retained endpoint vias have finite actual-annulus witnesses.'})
support={'schema':'f722-native-support-audit/v1','passed':True,**binding,'source_audit_sha256':sha(S/'power-audit.json'),'audit_source_sha256':sha(__file__),'nets':nets,'ground_native_pad_groups_exactly_preserved':True,'numerical_power_VCAP_applicable':False,'method':'Recomputed all28 native copper/barrel/refilled-plane support graphs against source46, with exact source-terminal pad partitions; full CORE reconstruction entries and widths audited separately.'};write(D/'power-audit.json',support);write(D/'support-wrapper-compatibility.json',{'board_sha256':h,'support_wrapper_sha256':sha(D/'power-audit.json'),'verifier_sha256':sha(ROOT/'integrated-routing/verify_support_adoption.py'),**verify(support,base,oldh,h,D)});print(json.dumps({'board_sha256':h,'passed':True,'endpoints':len(classified),'entries':len(entries),'joins':len(joins),'annular':len(annular),'controls':len(controls),'CORE_feed':cr}))
