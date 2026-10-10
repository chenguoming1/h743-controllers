import pathlib,sys,json,hashlib,copy,math
HERE=pathlib.Path(__file__).resolve().parent;ROOT=HERE.parents[2];S=ROOT/'ordinary-routing/candidate45';D=HERE/'candidate01'
sys.path[:0]=[str(ROOT/'ordinary-routing/dsm40-audits'),str(ROOT/'integrated-routing')]
from audit_dsm40_entries_return import pad_entry,join_entry,groups,geom
from verify_support_adoption import verify
import plan
read=lambda f:json.loads(pathlib.Path(f).read_text());sha=lambda f:hashlib.sha256(pathlib.Path(f).read_bytes()).hexdigest();write=lambda f,r:pathlib.Path(f).write_text(json.dumps(r,indent=2)+'\n')
before=read(S/'f722-heli.native.json');after=read(D/'f722-heli.native.json');prov=read(D/'construction-provenance.json');h=sha(D/'f722-heli.kicad_pcb');oldh=sha(S/'f722-heli.kicad_pcb');assert h==after['board_sha256']==prov['board_sha256'];assert oldh==before['board_sha256']==prov['source_board_sha256']==plan.m.EXPECTED
old={o['uuid']:o for o in before['objects']};new={o['uuid']:o for o in after['objects']};added=prov['added_records'];assert len(added)==9 and all(o['net']=='RPM_HV'and o['width']==.127 and list(o['copper'])==['F.Cu']for o in added)
assert all(new[u]==o for u,o in old.items())and set(new)-set(old)=={t['uuid']for t in added};assert all(before[k]==after[k]for k in ['footprints','zones','edge_cuts','outline_with_npth','copper_layers','board_thickness_mm'])
pads={o['key']:o for o in new.values()if o['kind']=='pad'};entries=[pad_entry(added[0],pads['R25.2'],'F.Cu','start'),pad_entry(added[-1],pads['U16.1'],'F.Cu','end')];joins=[join_entry(a,b,'F.Cu',.127)for a,b in zip(added,added[1:])];assert all(x['passed']for x in entries+joins)
sourcegroups=groups(before,'RPM_HV');currentgroups=groups(after,'RPM_HV');assert len(sourcegroups)==2 and len(currentgroups)==1 and currentgroups[0]['pads']==['Q1.3','R25.2','U16.1']
obs=plan.trace_obs('RPM_HV','F.Cu','U16.1')[0];points=[added[0]['start']]+[t['end']for t in added];checks=plan.m.check(plan.m.LineString(points),obs,True);assert checks[0]['extra_clearance_mm']>=plan.m.ERROR
controls=[]
bad=copy.deepcopy(added[0]);bad['width']=1.2;controls.append({'name':'oversized_full_width_source_pad_entry','rejected':not pad_entry(bad,pads['R25.2'],'F.Cu','start')['passed']})
bad=copy.deepcopy(added[-1]);bad['width']=2.;controls.append({'name':'oversized_full_width_actual_TVS_pad_entry','rejected':not pad_entry(bad,pads['U16.1'],'F.Cu','end')['passed']})
bad=copy.deepcopy(added[1]);bad['start']=[bad['start'][0]+.01,bad['start'][1]];controls.append({'name':'broken_exact_track_join','rejected':not join_entry(added[0],bad,'F.Cu',.127)['passed']})
bad=copy.deepcopy(after);bad['objects']=[o for o in bad['objects']if o['uuid']not in {t['uuid']for t in added}];controls.append({'name':'remove_new_branch_reopens_RPM_HV','rejected':len(groups(bad,'RPM_HV'))!=1})
controls.append({'name':'unrefined_straight_pad_join_foreign_collision','rejected':plan.m.check(plan.m.LineString([pads['R25.2']['xy'],pads['U16.1']['xy']]),obs)[0]['extra_clearance_mm']<0})
assert all(c['rejected']for c in controls)
base=read(S/'power-audit.json');nets={}
for net in base['nets']:
 current=groups(after,net);previous=groups(before,net);assert current==previous and len(current)==1
 nets[net]={'pad_group_count':len(current),'complete':True,'groups':current,'source_groups_exactly_preserved':True}
assert len(nets)==28
# Pad partitions for all other nets follow exactly from unchanged native records
# and saved zones: added copper is exclusively RPM_HV and all foreign clearance
# checks pass. Recompute critical I2C explicitly as an additional current check.
i2c={net:{'before':groups(before,net),'after':groups(after,net)}for net in ['BARO_SCL','BARO_SDA']};assert all(r['before']==r['after']and len(r['after'])==1 for r in i2c.values())
gates={'RPM_HV_all_three_terminals_connected':True,'finite_full_width_actual_pad_entries':all(x['passed']for x in entries),'eight_full_width_joins':all(x['passed']for x in joins),'all18_new_endpoints_accounted':True,'native_distance_checks':checks[0]['extra_clearance_mm']>=plan.m.ERROR,'all28_support_groups_exact':True,'both_I2C_groups_exact':True,'all1941_source_records_exact':len(old)==1941 and all(new[u]==o for u,o in old.items()),'all156_footprints_exact':before['footprints']==after['footprints'],'all_saved_zone_records_exact':before['zones']==after['zones'],'negative_controls':all(x['rejected']for x in controls)}
audit={'schema':'f722-HV-entry-support/v1','passed':all(gates.values()),'gates':gates,'source_board_sha256':oldh,'board_sha256':h,'source_native_sha256':sha(S/'f722-heli.native.json'),'native_sha256':sha(D/'f722-heli.native.json'),'audit_source_sha256':sha(__file__),'strict_pad_entries':entries,'full_width_joins':joins,'new_track_endpoints_checked':18,'RPM_HV_source_groups':sourcegroups,'RPM_HV_current_groups':currentgroups,'native_distance_nearest':checks[:20],'nominal_CAD_copper_gap_mm':checks[0]['physical_gap_mm'],'CAD_excess_is_not_manufacturing_margin':True,'negative_controls':controls,'nets':nets,'I2C_exact_groups':i2c,'numerical_power_VCAP_applicable':False}
assert audit['passed'];write(D/'entry-support-audit.json',audit);binding={'board_sha256':h,'source_board_sha256':oldh,'native_sha256':sha(D/'f722-heli.native.json'),'source_native_sha256':sha(S/'f722-heli.native.json'),'audit':'entry-support-audit.json','audit_sha256':sha(D/'entry-support-audit.json')}
write(D/'endpoint-audit.json',{'schema':'f722-native-endpoint-audit-binding/v1','passed':True,**binding,'new_track_endpoints_checked':18,'direct_pad_entries':2,'full_width_joins':8,'new_vias':0,'strict_pad_entries_all_pass':True,'negative_controls':len(controls),'scope':'Nine added0.127mm native round-ended F.Cu segments, source R25.2 and actual bonded U16.1 entries; all18 endpoints have finite full-width proof.'})
support={'schema':'f722-native-support-audit/v1','passed':True,**binding,'source_audit_sha256':sha(S/'power-audit.json'),'audit_source_sha256':sha(__file__),'nets':nets,'ground_native_pad_groups_exactly_preserved':True,'numerical_power_VCAP_applicable':False,'method':'Recomputed all28 native copper/barrel/fill support graphs and compared their exact current pad partitions against source45.'};write(D/'power-audit.json',support);compat=verify(support,base,oldh,h,D);write(D/'support-wrapper-compatibility.json',{'board_sha256':h,'support_wrapper_sha256':sha(D/'power-audit.json'),'verifier_sha256':sha(ROOT/'integrated-routing/verify_support_adoption.py'),**compat})
print(json.dumps({'passed':audit['passed'],'board_sha256':h,'RPM_HV_groups':currentgroups,'nominal_CAD_copper_gap_mm':checks[0]['physical_gap_mm'],'support_nets':len(nets)}))
