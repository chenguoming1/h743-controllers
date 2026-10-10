from pathlib import Path
import json,shutil,datetime
R=Path(__file__).resolve().parents[1];N=R/'repo/f722-heli/layout-revision';C=N/'checks';S=R/'checkpoint11-owner-review';D=R/'ordinary-routing/candidate57';O=C/'checkpoint57-integration'
def read(p):return json.loads(p.read_text())
def write(p,d):p.write_text(json.dumps(d,indent=2)+'\n')
h=read(D/'owner-summary.json')['board_sha256']
for f in ['owner-adoption-assessment.json','exact-ground-and-retained-reference.json','comparison-12-to-11.json','seal_owner_metadata.py','run_owner.sh']:
 shutil.copy2(S/f,O/f)
for f in ['entry-support-audit.json','power-audit-sealed-original.json','power-audit.json','owner-summary.json','support-report-adapter.json']:
 shutil.copy2(D/f,O/f)
shutil.copy2(S/'BOOT-reference/critical-reference.json',O/'BOOT-reference.json')
shutil.copy2(R/'checkpoint11-placement-reproduction/placement-reproduction.json',C/'placement11-reproduction.json')
s=read(C/'current-status.json')
for k in ['loaded_power_diagnostic','current_numerical_power_status']:
 s[k]=s[k].replace('Current12','Current11').replace('current12','current11')
s.update(placement_recipe_current_evidence='placement11-reproduction.json',placement_transform_current_evidence='transform-placement11.json',placement_recipe_original_reproduction='placement11-reproduction.json')
s['i2c_routing']['source_board_sha256']=h
s['reference_preservation']={'board_sha256':h,'receipt':'checkpoint57-integration/exact-ground-and-retained-reference.json','retained_GND_fill_and_drill_geometry_exact':True,'new_BOOT_projection_receipt':'checkpoint57-integration/BOOT-reference.json','AC_or_impedance_qualification':False,'limits':'Inherited source13 boundary-predicate ambiguities remain unresolved. Source12 CS width-edge wedge remains inherited.'}
s['BOOT_pull_down_revision']={'board_sha256':h,'receipt':'checkpoint57-integration/owner-adoption-assessment.json','R2_pose':[40.2,6.2,270,'F.Cu'],'R2_value_ohm':2200,'switch_to_resistor_complete':True,'actual_MCU_connection_complete':False,'electrical_qualified':False}
write(C/'current-status.json',s)
p=N/'README.md';t=p.read_text().replace('checks/checkpoint12-owner-review.json','checks/checkpoint11-owner-review.json');anchor='Checkpoint56 completes';assert anchor in t
t=t.replace(anchor,'Checkpoint57 moves the unchanged 2.2 kΩ BOOT pull-down R2 beside the USB-side switch and completes their branch. The actual MCU BOOT connection remains open. All 156 poses and 558 pad records reproduce. Retained ground-plane fills and physical drill polygons are exact; C31’s existing ground via and rear lead are preserved. The new BOOT trace has continuous projected ground coverage. These checks do not establish startup/noise or physical qualification. See the [owner assessment](checks/checkpoint57-integration/owner-adoption-assessment.json).\n\nThe preceding '+anchor,1);p.write_text(t)
p=R/'ACTIVE-STATE.json';s=read(p);s['updated_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();s['owner_current_review']={'source':'ordinary-routing/candidate57','board_sha256':h,'assessment':'checkpoint11-owner-review/owner-adoption-assessment.json','numerical_power_current':False};write(p,s)
with (R/'OWNER-RESUME.md').open('a') as f:f.write('\n2026-10-10 08:17 UTC: Accepted candidate57 at11 opens/0 errors/0 warnings, PCB '+h+'. R2 only placement change; 156 poses/558 pads reproduced. Exact retained GND/drills, original C31 return preserved. Numerical power remains stale. Publication12 is pending sole publisher; remote13 remains verified.\n')
print('Canonical11 evidence refreshed')
