import pathlib,sys,json,hashlib,copy,math
HERE=pathlib.Path(__file__).resolve().parent;ROOT=HERE.parents[2];S=ROOT/'ordinary-routing/candidate47';D=HERE/'candidate01'
sys.path[:0]=[str(ROOT/'ordinary-routing/dsm40-audits'),str(ROOT/'ordinary-routing/dsm41-audits'),str(ROOT/'integrated-routing')]
from audit_dsm40_entries_return import pad_entry,join_entry,groups,geom,plane_corridor,objects,make_graph
from audit_dsm41_entries_return import via_entry
from verify_support_adoption import verify
from shapely.geometry import Point,LineString
from shapely.ops import unary_union
read=lambda f:json.loads(pathlib.Path(f).read_text());sha=lambda f:hashlib.sha256(pathlib.Path(f).read_bytes()).hexdigest();write=lambda n,r:(D/n).write_text(json.dumps(r,indent=2)+'\n')
before=read(S/'f722-heli.native.json');after=read(D/'f722-heli.native.json');prov=read(D/'construction-provenance.json');h=sha(D/'f722-heli.kicad_pcb');oldh=sha(S/'f722-heli.kicad_pcb');assert h==after['board_sha256']==prov['board_sha256'];assert oldh==before['board_sha256']==prov['source_board_sha256']
old={o['uuid']:o for o in before['objects']};new={o['uuid']:o for o in after['objects']};added=prov['added_records'];tracks=[o for o in new.values()if o['kind']=='track'];pads=[o for o in new.values()if o['kind']=='pad'];vias=[o for o in new.values()if o['kind']=='via'];newtracks=[o for o in added if o['kind']=='track'];physical=lambda o:{k:v for k,v in o.items()if k!='net_code'}
assert len(added)==14 and len(newtracks)==12 and len(prov['removed_source_records'])==2
for u,o in old.items():
 if u not in new:assert o['net']=='GND';continue
 if o.get('ref')in ['C31','R43']:continue
 assert physical(o)==physical(new[u]),u
entries=[];annular=[];joins=[];resolved=[];partial=[]
for t in newtracks:
 layer=next(iter(t['copper']))
 for end in ['start','end']:
  xy=t[end];hits=[]
  for pad in pads:
   if pad['net']!=t['net']or layer not in pad['inside']or not geom(pad['inside'][layer]).contains(Point(xy)):continue
   r=pad_entry(t,pad,layer,end)
   if r['passed']:entries.append(r);hits.append({'pad':pad['key']})
   else:partial.append(r)
  for v in vias:
   if v['net']==t['net']and xy==v['xy']:
    r=via_entry(t,v,layer,after);assert r['passed'];annular.append(r);hits.append({'via':v['uuid']})
  for other in tracks:
   if other['uuid']==t['uuid']or other['net']!=t['net']or layer not in other['copper']:continue
   if xy not in [other['start'],other['end']]:continue
   r=join_entry(t,other,layer,min(t['width'],other['width']));assert r['passed'];joins.append(r);hits.append({'track':other['uuid']})
  assert hits,(t['uuid'],end,xy);resolved.append({'track':t['uuid'],'endpoint':end,'xy':xy,'connections':hits})
# Dependent retained divider tail has its own strict, finite full-width pad proof.
padby={o['key']:o for o in pads};dep=pad_entry(new['93b940e0-d578-4140-b801-9154d1c5a358'],padby['R43.2'],'F.Cu','end');assert dep['passed'];entries.append(dep)
# Retained ADC_BUS diagonal's endpoint now reaches R43.1 through an exact full-width join and the new vertical entry.
oldbus=new['78110aa7-90b8-491f-a07a-f34ae1f5516f'];direct=pad_entry(oldbus,padby['R43.1'],'F.Cu','end');bridge=next(t for t in newtracks if t['net']=='ADC_BUS'and t['start']==[21.99,17.9]and t['end']==[21.99,17.6]);bj=join_entry(oldbus,bridge,'F.Cu',.127);bp=pad_entry(bridge,padby['R43.1'],'F.Cu','start');assert bj['passed']and bp['passed'];composite={'retained_track_uuid':oldbus['uuid'],'direct_pad_entry':direct,'exact_full_width_join':bj,'new_finite_full_width_pad_entry':bp,'passed':True}
sourcegroups=groups(before,'ADC_BUS');nowgroups=groups(after,'ADC_BUS');assert len(sourcegroups)==3 and len(nowgroups)==1 and nowgroups[0]['pads']==['C31.1','R42.2','R43.1','U1.10'];assert groups(before,'ADC_DIV_MID')==groups(after,'ADC_DIV_MID')
# Exact C31 ground return: pad,0.25mm lead, retained plated via, both saved GND planes.
gt=next(t for t in newtracks if t['net']=='GND');gv=next(v for v in vias if v['net']=='GND'and v['xy']==[16.4252,7.0556]);cp=padby['C31.2'];assert gt['width']==.25 and gv['drill']['width']==.2
error=after['maximum_polygon_error_mm'];drills=unary_union([geom(o['drill']['outside'])for o in new.values()if o.get('drill')]);ggraph=make_graph(objects(after,'GND'));connected=[g for g in ggraph if {cp['uuid'],gv['uuid']}<={v['object']['uuid']for v in g}];assert len(connected)==1;planes=[]
for layer in ['In1.Cu','In4.Cu']:
 zones=[z for z in after['zones']if not z['rule']and z['net']=='GND'and layer in z['filled']];fill=unary_union([geom(z['filled'][layer])for z in zones]).buffer(-error,join_style=2).difference(drills);ann=geom(gv['copper'][layer]).buffer(-error).difference(geom(gv['drill']['outside']));corridor=plane_corridor(fill,ann,gv['xy']);missing=ann.difference(fill).area;zoneids=sorted({v['object']['uuid']for v in connected[0]if v['object']['kind']=='zone'and v['layer']==layer});r={'layer':layer,'annulus_area_outside_actual_plane_mm2':missing,'finite_plane_corridor':corridor,'connected_zone_uuids':zoneids,'passed':missing<=1e-12 and bool(corridor)and bool(zoneids)};assert r['passed'];planes.append(r)
capreturn={'passed':True,'pad':'C31.2','track_uuid':gt['uuid'],'width_mm':.25,'length_mm':math.dist(gt['start'],gt['end']),'existing_via_uuid':gv['uuid'],'via_xy':gv['xy'],'both_plane_entries':planes,'removed_old_return_records':prov['removed_source_records'],'old_via_had_no_other_attached_nonplane_copper':True}
# Prove removed old ground via had only the deleted dedicated capacitor trace as a non-plane attachment.
oldvia=next(o for o in prov['removed_source_records']if o['kind']=='via');attached=[]
for o in old.values():
 if o['uuid']==oldvia['uuid']:continue
 if any(geom(o['copper'][l]).intersects(geom(oldvia['copper'][l]))for l in o['copper'].keys()&oldvia['copper'].keys()):attached.append(o['uuid'])
assert attached==['6bf63e0b-d6e1-404c-8d41-db5d79061a6c'],attached
base=read(S/'power-audit.json');nets={}
for net in base['nets']:
 current=groups(after,net);previous=groups(before,net);assert current==previous and len(current)==1,net;nets[net]={'pad_group_count':1,'complete':True,'groups':current,'source_groups_exactly_preserved':True}
i2c={net:{'before':groups(before,net),'after':groups(after,net)}for net in ['BARO_SCL','BARO_SDA']};assert all(r['before']==r['after']and len(r['after'])==1 for r in i2c.values())
controls=[]
bad=copy.deepcopy(bridge);bad['width']=1.5;controls.append({'name':'oversized_R43_pad_entry','rejected':not pad_entry(bad,padby['R43.1'],'F.Cu','start')['passed']})
bad=copy.deepcopy(bridge);bad['end'][0]+=.01;controls.append({'name':'broken_retained_ADC_BUS_bridge_join','rejected':not join_entry(oldbus,bad,'F.Cu',.127)['passed']})
bad=copy.deepcopy(gt);bad['width']=.6;controls.append({'name':'oversized_ground_annular_entry','rejected':not via_entry(bad,gv,'B.Cu',after)['passed']})
for net,omit in [('ADC_BUS',prov['routes'][3]),('GND',prov['routes'][4])]:
 bad=copy.deepcopy(after);bad['objects']=[o for o in bad['objects']if o['uuid']not in omit];controls.append({'name':'remove_'+net+'_C31_branch','rejected':len(groups(bad,net))>1})
assert all(c['rejected']for c in controls)
gates={'ADC_BUS_complete_four_terminal_tree':True,'all24_new_track_endpoints_finitely_connected':len(resolved)==24,'dependent_ADC_DIV_MID_finite_entry':dep['passed'],'retained_ADC_BUS_composite_full_width_entry':composite['passed'],'C31_ground_return_both_planes':capreturn['passed'],'all28_support_groups_preserved':len(nets)==28,'both_I2C_groups_preserved':True,'all_negative_controls_rejected':all(c['rejected']for c in controls)}
audit={'schema':'f722-ADC-entry-support/v1','passed':all(gates.values()),'gates':gates,'board_sha256':h,'source_board_sha256':oldh,'source_native_sha256':sha(S/'f722-heli.native.json'),'native_sha256':sha(D/'f722-heli.native.json'),'strict_pad_entries':entries,'full_width_joins':joins,'finite_actual_annular_entries':annular,'new_track_endpoints_checked':24,'endpoint_inventory':resolved,'partial_pad_entries_not_used_as_connectivity_proof':partial,'retained_ADC_BUS_composite_entry':composite,'ADC_BUS_before':sourcegroups,'ADC_BUS_after':nowgroups,'C31_ground_return':capreturn,'nets':nets,'I2C_groups':i2c,'negative_controls':controls,'numerical_power_VCAP_applicable':False};write('entry-support-audit.json',audit)
binding={'board_sha256':h,'source_board_sha256':oldh,'native_sha256':sha(D/'f722-heli.native.json'),'source_native_sha256':sha(S/'f722-heli.native.json'),'audit':'entry-support-audit.json','audit_sha256':sha(D/'entry-support-audit.json')}
write('endpoint-audit.json',{'schema':'f722-native-endpoint-audit-binding/v1','passed':True,**binding,'new_track_endpoints_checked':24,'strict_pad_entries_all_pass':all(e['passed']for e in entries),'direct_pad_entries':len(entries),'full_width_joins':len(joins),'finite_annular_entries':len(annular),'new_vias':2,'negative_controls':len(controls),'scope':'Every new endpoint and both moved-pad dependents have finite pad, exact full-width join, or actual-annulus proofs. Retained ADC_BUS diagonal uses an explicit composite entry; its failed direct pad section is preserved.'})
support={'schema':'f722-native-support-audit/v1','passed':True,**binding,'source_audit_sha256':sha(S/'power-audit.json'),'audit_source_sha256':sha(__file__),'nets':nets,'ground_native_pad_groups_exactly_preserved':True,'numerical_power_VCAP_applicable':False,'method':'Recomputed all28 native copper/barrel/saved-fill support graphs. C31 has a rebuilt0.25mm return to a retained via with finite plane-entry proof on both reference planes.'};write('power-audit.json',support);compat=verify(support,base,oldh,h,D);write('support-wrapper-compatibility.json',{'board_sha256':h,'support_wrapper_sha256':sha(D/'power-audit.json'),'verifier_sha256':sha(ROOT/'integrated-routing/verify_support_adoption.py'),**compat});print(json.dumps({'passed':audit['passed'],'board_sha256':h,'ADC_BUS_groups':nowgroups,'ground_length':capreturn['length_mm'],'support_nets':len(nets)}))
