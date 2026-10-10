"""Complete conditional CS with exact cap, bank, SBUS and shared IMU-return support."""
import hashlib,json
from composite_native11_caps_right import *
CS_PATH=H/'CS-caps-right-IMU-ground-exchange11.json'
CS=json.loads(CS_PATH.read_text())
assert CS['complete'] and CS['ground_replacement_passed'] and CS['SBUS_function_restored']
assert all(q['passed'] for q in CS['bank_checks'])
assert CS['reserved_barrel_check']['passed'] and not CS['selected']
NEW_CUTS={o['uuid'] for o in CS['bank_removed_records']+CS['ground_removed_native_records']}|{CS['SBUS_removed_record']['uuid']}
assert not NEW_CUTS&REMOVED_NATIVE_IDS
for o in CS['bank_removed_records']+CS['ground_removed_native_records']+[CS['SBUS_removed_record']]:assert physical(by[o['uuid']])==physical(o)
BASE=[q for q in BASE if q[0]['uuid'] not in NEW_CUTS]
CS_INNER=[r for r in CS['routes'] if r['layer'] in ['In2.Cu','In3.Cu']]
assert len(CS_INNER)==2
CS_REQUIRED_ROUTES=CS['bank_routes']+[CS['SBUS_complete_replacement'],CS['ground_complete_route']]+CS_INNER
CS_REQUIRED_VIAS=CS['bank_vias']+CS['vias']
BASE += [track(r['net'],r['layer'],r['points'],r['name'],r['width']) for r in CS_REQUIRED_ROUTES]
BASE += [via(v['net'],v['xy'],v['name']) for v in CS_REQUIRED_VIAS]
REMOVED_NATIVE_IDS=REMOVED_NATIVE_IDS|NEW_CUTS
_previous_binding=binding
def binding():
    b=_previous_binding()
    b.update(explicit_source_removals=sorted(REMOVED_NATIVE_IDS),CS_witness=dict(file=str(CS_PATH.relative_to(ROOT)),sha256=hashlib.sha256(CS_PATH.read_bytes()).hexdigest()),
             CS_complete_inner_restoration_pending=False,CS_only_completion_scope=True,full_remaining_capacity_audit_complete=False,
             original_INT_RPM_DSM_objects_retained=True,shared_U2_6_U2_7_ground_return_changed=True,
             native_candidate=False,fresh_IMU_reference_return_AC_power_review_required=True)
    b['complete_functions']=list(dict.fromkeys(b.get('complete_functions',[])+['FLASH_CS actual U1.33/U3.1/R4.2 tree with changed shared IMU ground return']))
    b['pending_functions']=[f for f in b.get('pending_functions',[]) if f!='Complete FLASH_CS inner restoration after cap revision']
    return b
s.OBJECTS=BASE
