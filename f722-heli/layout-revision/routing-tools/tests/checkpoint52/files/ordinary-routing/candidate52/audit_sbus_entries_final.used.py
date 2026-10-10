import pathlib,sys,json,hashlib,copy
HERE=pathlib.Path(__file__).resolve().parent;ROOT=HERE.parents[2];S=HERE.parent/'port-a48/candidate05';D=HERE/'candidate02'
sys.path[:0]=[str(ROOT/'ordinary-routing/dsm40-audits'),str(ROOT/'ordinary-routing/dsm41-audits'),str(ROOT/'integrated-routing')]
from audit_dsm40_entries_return import pad_entry,join_entry,groups,geom
from audit_dsm41_entries_return import via_entry
from verify_support_adoption import verify
from shapely.geometry import Point
read=lambda f:json.loads(pathlib.Path(f).read_text());sha=lambda f:hashlib.sha256(pathlib.Path(f).read_bytes()).hexdigest();write=lambda n,r:(D/n).write_text(json.dumps(r,indent=2)+'\n')
before=read(S/'f722-heli.native.json');after=read(D/'f722-heli.native.json');prov=read(D/'construction-provenance.json');h=sha(D/'f722-heli.kicad_pcb');oldh=sha(S/'f722-heli.kicad_pcb');assert h==after['board_sha256']==prov['board_sha256'];assert oldh==before['board_sha256']==prov['source_board_sha256']
old={o['uuid']:o for o in before['objects']};new={o['uuid']:o for o in after['objects']};added=prov['added_records'];tracks=[o for o in new.values()if o['kind']=='track'];pads=[o for o in new.values()if o['kind']=='pad'];vias=[o for o in new.values()if o['kind']=='via'];newtracks=[o for o in added if o['kind']=='track'];physical=lambda o:{k:v for k,v in o.items()if k!='net_code'}
removed={o['uuid']for o in prov['removed_source_records']};assert len(removed)==5;assert all(physical(o)==physical(new[u])for u,o in old.items()if u not in removed and o.get('ref')!='R45')
entries=[];annular=[];joins=[];resolved=[];partial=[]
for t in newtracks:
 layer=next(iter(t['copper']))
 for end in['start','end']:
  xy=t[end];hits=[]
  for pad in pads:
   if pad['net']!=t['net']or layer not in pad['inside']or not geom(pad['inside'][layer]).contains(Point(xy)):continue
   z=pad_entry(t,pad,layer,end)
   if z['passed']:entries.append(z);hits.append({'pad':pad['key']})
   else:partial.append(z)
  for v in vias:
   if v['net']==t['net']and xy==v['xy']:
    z=via_entry(t,v,layer,after);assert z['passed'];annular.append(z);hits.append({'via':v['uuid']})
  for other in tracks:
   if other['uuid']==t['uuid']or other['net']!=t['net']or layer not in other['copper']:continue
   if xy not in[other['start'],other['end']]:continue
   z=join_entry(t,other,layer,min(t['width'],other['width']));assert z['passed'];joins.append(z);hits.append({'track':other['uuid']})
  assert hits,(t['uuid'],end,xy);resolved.append({'track':t['uuid'],'endpoint':end,'xy':xy,'connections':hits})
changed_groups={n:dict(before=groups(before,n),after=groups(after,n))for n in ['SBUS_LV','SBUS_MCU']};assert all(len(r['after'])==1 for r in changed_groups.values())
base=read(S/'power-audit.json');nets={}
for net in base['nets']:
 current=groups(after,net);previous=groups(before,net);assert current==previous and len(current)==1,net;nets[net]={'pad_group_count':1,'complete':True,'groups':current,'source_groups_exactly_preserved':True}
retained={net:{'before':groups(before,net),'after':groups(after,net)}for net in['BARO_SCL','BARO_SDA','PORT_A_RX_MCU','PORT_A_TX_MCU','PORT_A_RX_EXT','PORT_A_TX_EXT','PORT_B_RX_MCU','PORT_B_TX_MCU','PORT_B_RX_EXT','PORT_B_TX_EXT','SWDIO','NRST','ADC_BUS','SBUS_HV']};assert all(z['before']==z['after']for z in retained.values())
controls=[];padby={o['key']:o for o in pads};t=next(t for t in newtracks if t['start']==[11.925,22.35]);bad=copy.deepcopy(t);bad['width']=1.5;controls.append({'name':'oversized_actual_clamp_pad_entry','rejected':not pad_entry(bad,padby['U13.1'],'B.Cu','start')['passed']})
for i,route in enumerate(prov['routes']):
 bad=copy.deepcopy(after);bad['objects']=[o for o in bad['objects']if o['uuid']not in route];controls.append({'name':'remove_complete_path_part_'+str(i),'rejected':len(groups(bad,read(D/'proposal.json')['routes'][i]['net']))>1})
assert all(z['rejected']for z in controls)
gates={'SBUS_LV_and_MCU_complete_native_pad_groups':True,'all_new_track_endpoints_finitely_connected':len(resolved)==2*len(newtracks),'all28_support_groups_preserved':len(nets)==28,'retained_I2C_MCU_ADC_SBUS_groups_preserved':True,'all_undeclared_source_objects_and_footprints_preserved':True,'all_negative_controls_rejected':True}
binding={'board_sha256':h,'source_board_sha256':oldh,'native_sha256':sha(D/'f722-heli.native.json'),'source_native_sha256':sha(S/'f722-heli.native.json')}
audit={'schema':'f722-SBUS-entry-support/v1','passed':True,**binding,'gates':gates,'strict_pad_entries':entries,'full_width_joins':joins,'finite_actual_annular_entries':annular,'new_track_endpoints_checked':len(resolved),'endpoint_inventory':resolved,'partial_pad_entries_not_used_as_connectivity_proof':partial,'changed_groups':changed_groups,'nets':nets,'retained_groups':retained,'negative_controls':controls,'numerical_power_VCAP_applicable':False};write('entry-support-audit.json',audit)
binding.update({'audit':'entry-support-audit.json','audit_sha256':sha(D/'entry-support-audit.json')})
write('endpoint-audit.json',{'schema':'f722-native-endpoint-audit-binding/v1','passed':True,**binding,'new_track_endpoints_checked':len(resolved),'strict_pad_entries_all_pass':all(z['passed']for z in entries),'direct_pad_entries':len(entries),'full_width_joins':len(joins),'finite_annular_entries':len(annular),'new_vias':len(prov['vias']),'negative_controls':len(controls),'scope':'Every new endpoint has finite full-width pad, exact full-width join or actual-annulus proof.'})
support={'schema':'f722-native-support-audit/v1','passed':True,**binding,'source_audit_sha256':sha(S/'power-audit.json'),'audit_source_sha256':sha(__file__),'nets':nets,'ground_native_pad_groups_exactly_preserved':True,'numerical_power_VCAP_applicable':False,'method':'Recomputed all28 native copper/barrel/saved-fill support graphs and both I2C plus retained MCU/ADC/SBUS graphs; exact source pad partitions preserved.'};write('power-audit.json',support);compat=verify(support,base,oldh,h,D);write('support-wrapper-compatibility.json',{'board_sha256':h,'support_wrapper_sha256':sha(D/'power-audit.json'),'verifier_sha256':sha(ROOT/'integrated-routing/verify_support_adoption.py'),**compat})
print(json.dumps({'passed':True,'board_sha256':h,'changed_groups':changed_groups,'support_nets':len(nets),'new_track_endpoints':len(resolved)}))
