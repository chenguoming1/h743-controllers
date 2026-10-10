"""Exact CS conductive-tree and return-contact audit for the compact successor."""
import datetime,hashlib,json,math,signal,time
from pathlib import Path
import composite_native11_CS_caps_return as c
from shapely.geometry import LineString,Point
START=time.monotonic();signal.alarm(10);s=c.s
OUT=c.H/'CS-caps-return-sealed11.json';assert not OUT.exists()
items=[q for q in c.BASE if q[0]['net']=='FLASH_CS'];parent=list(range(len(items)))
def find(i):
    while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
    return i
edges=[]
for i,(o,co,ma,dr) in enumerate(items):
    for j in range(i):
        other,cc,_,_=items[j];layers=[l for l in co if l in cc and co[l].intersects(cc[l])]
        if layers:parent[find(i)]=find(j);edges.append(dict(a=o['uuid'],b=other['uuid'],layers=layers))
terminals={key:[i for i,(o,co,ma,dr) in enumerate(items) if o.get('key')==key] for key in ['U1.33','U3.1','R4.2']}
assert all(len(v)==1 for v in terminals.values()),terminals
groups={key:find(v[0]) for key,v in terminals.items()};tree_pass=len(set(groups.values()))==1
joins={}
for name,xy in [('retained_MCU_entry_via',[25.266112,10.724566]),('retained_U3_R4_entry_via',[32.582039,21.210477])]:
    rows=[i for i,(o,co,ma,dr) in enumerate(items) if o['kind']=='via' and o['xy']==xy]
    assert len(rows)==1;joins[name]=dict(uuid=items[rows[0]][0]['uuid'],xy=xy,group=find(rows[0]),connected_to_actual_terminals=find(rows[0]) in set(groups.values()))
out=dict(schema='f722-CS-caps-return-sealed/v1',created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),source=c.binding(),
         scope='Complete FLASH_CS actual U1.33/U3.1/R4.2 function and its exact changed support only; other joint functions remain incomplete.',
         complete_CS_tree=tree_pass,actual_terminal_groups=groups,retained_join_proofs=joins,CS_contact_edges=edges,
         compact_CS_inner_routes=c.CS_INNER,constructed_duplicate_endpoint_routes_omitted=[r for r in c.CS['routes'] if r['layer']=='B.Cu'],
         removal_of_duplicate_routes_justified_by_retained_conductive_tree=tree_pass,
         added_CS_inner_length_mm=sum(r['length_mm'] for r in c.CS_INNER),actual_MCU_to_U3_constructed_length_mm=c.CS['total_new_CS_length_mm'],
         bank_removed_records=c.CS['bank_removed_records'],bank_routes=c.CS['bank_routes'],bank_vias=c.CS['bank_vias'],
         SBUS_removed_record=c.CS['SBUS_removed_record'],SBUS_complete_route=c.CS['SBUS_complete_replacement'],SBUS_contact_audit=c.CS['SBUS_same_net_contact_audit'],
         ground_removed_records=c.CS['ground_removed_native_records'],ground_complete_route=c.CS['ground_complete_route'],CS_new_vias=c.CS['vias'],
         ground_old_external_contacts=c.CS['removed_ground_external_contacts'],ground_new_contacts=c.CS['ground_new_same_net_contacts'],
         before_capacity=c.CS['before'],after_capacity=c.CS['after'],unfinished_after_check=['PORT_C_TX_MCU'],full_capacity_audit_complete=False,
         dedicated_return_comparison=dict(file='tests/native13-access/CS-IMU-ground-return-options11.json',sha256=hashlib.sha256((c.H/'CS-IMU-ground-return-options11.json').read_bytes()).hexdigest(),bounds=[22.3,12.5,24.7,14.0]),
         pending_native_reference_power_AC_return_qualification=True,native_candidate=False,selected_for_joint_adoption=False)
ground=c.CS['ground_complete_route'];newg=c.track('GND','F.Cu',ground['points'],ground['name'],.25)[1]['F.Cu']
oldleaf=c.entry(c.by['a4901cd4-da0d-44c6-8240-3a96cda6c6a9'])[1]['F.Cu'];oldaxis=LineString([[23.209999,12.5125],[23.21,13.3625]])
overlap=newg.intersection(oldleaf);axis_shared=oldaxis.intersection(newg)
out['shared_return_geometry']=dict(actual_pins=['U2.6','U2.7'],retained_plane_via='23f2b322-6468-4bbf-b0a8-6d4b51e76bbf',
    old_each_pad_to_via_centerline_mm=math.dist([23.709999,12.5125],[23.71,13.3625]),new_U2_7_centerline_mm=ground['length_mm'],
    unchanged_U2_6_centerline_mm=oldaxis.length,shared_copper_overlap_area_mm2=overlap.area,shared_copper_overlap_bounds=list(overlap.bounds),
    retained_U2_6_centerline_covered_by_new_ground_copper_mm=axis_shared.length,
    interpretation='Both sensor ground pins share the retained barrel and an overlapping series copper section. These dimensions are not an AC/noise-equivalence claim.')
checks=[]
for r in c.CS_INNER+[ground,c.CS['SBUS_complete_replacement']]:
    s.OBJECTS=[q for q in c.BASE if q[0]['uuid']!=r['name']];s.HALF=r['width']/2
    ch=s.check(LineString(r['points']),s.obstacles(r['net'],r['layer'])[0],True)
    checks.append(dict(name=r['name'],passed=all(x['pass_with_polygon_error'] for x in ch),failures=[x for x in ch if not x['pass_with_polygon_error']]))
out['compact_changed_route_checks']=checks;out['compact_finite_pass']=all(q['passed'] for q in checks)
out['files']={}
for name in ['composite_native11_caps_right.py','C13-C11-right-preserve-INT11.json','CS-caps-right-IMU-ground-exchange11.json','CS-IMU-ground-return-options11.json','composite_native11_CS_caps_return.py','seal_CS_caps_return11.py']:
    p=c.H/name;out['files'][str(p.relative_to(c.ROOT))]=hashlib.sha256(p.read_bytes()).hexdigest()
out['seconds']=time.monotonic()-START
OUT.write_text(json.dumps(out,indent=2)+'\n')
print('TERMINAL',tree_pass,out['compact_finite_pass'],out['seconds'],flush=True)
assert tree_pass and out['compact_finite_pass']
