from pathlib import Path
import json,hashlib,shutil
R=Path(__file__).resolve().parents[1];D=R/'ordinary-routing/candidate57';O=R/'ordinary-routing/candidate56';S=R/'checkpoint11-owner-review'
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,d):
 if p.exists():p.unlink()
 p.write_text(json.dumps(d,indent=2)+'\n')
h=sha(D/'f722-heli.kicad_pcb');old=sha(O/'f722-heli.kicad_pcb')
p=D/'power-audit.json';q=read(p);original=sha(p);shutil.copy2(p,D/'power-audit-sealed-original.json')
assert len(q['nets'])==28
for v in q['nets'].values():
 assert len(v['groups'])==1
 v['pad_group_count']=len(v['groups'])
write(p,q)
write(D/'support-report-adapter.json',{'original_sha256':original,'output_sha256':sha(p),'change':'Add explicit pad_group_count equal to verified len(groups) for all28 singleton support partitions. No geometry, membership or pass rule changed.'})
i=read(O/'f722-heli.import.json');i.update(source_sha256=old,output_sha256=h,construction_kind='Explicit BOOT0 pull-down/switch closure with R2 relocation and dedicated ground leaf; actual MCU BOOT0 remains open.',construction_provenance_sha256=sha(D/'construction-provenance.json'),logical_route_map_sha256=sha(D/'f722-heli.logical-route-map.json'),removed_source_objects=1,new_tracks=2,new_vias=0,owner_integration_sha256=sha(S/'owner-coordinated-integration.json'),native_gate_receipt_sha256=sha(D/'owner-summary.json'))
write(D/'f722-heli.import.json',i)
power=read(O/'power-revalidation-required.json');power.update(board_sha256=h,reason='R2 placement and ground leaf changed after earlier unscreened revisions. Exact retained ground fills do not make corrected source43/37 numerical power/VCAP applicable to this board.')
write(D/'power-revalidation-required.json',power)
write(S/'owner-adoption-assessment.json',{'source_board_sha256':old,'board_sha256':h,'passed_geometric_checkpoint':True,'unfinished_connections':11,'native_errors':0,'native_warnings':0,'only_footprint_change':'R2 F(40.2,6.2),270; unchanged2.2k1% value','retained_reference_evidence':'exact-ground-and-retained-reference.json','BOOT_reference_evidence':'BOOT-reference/critical-reference.json','placement_reproduces':{'poses':156,'pads':558},'new_BOOT_track_mm':1.270127946,'new_ground_leaf_mm':1.063672882,'C31_ground_via_and_B_lead_preserved':True,'actual_MCU_BOOT0_complete':False,'numerical_power_VCAP_applicable':False,'limits':'Inherited reference-boundary ambiguities remain unresolved. Native geometry/reference checks do not qualify startup, AC/noise/ESD behavior, fabrication or flight.'})
print(h)
