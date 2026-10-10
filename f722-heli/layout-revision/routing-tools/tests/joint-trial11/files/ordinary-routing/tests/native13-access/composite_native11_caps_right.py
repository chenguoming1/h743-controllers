"""Conditional complete C13/C11 support; CS inner restoration remains explicit."""
import hashlib
import json
from composite_native11_divider_green_mid import *

CAP_PATH=H/'C13-C11-right-preserve-INT11.json'
CAP=json.loads(CAP_PATH.read_text())
assert CAP['support_finite_pass'] and CAP['original_INT_RPM_DSM_objects_retained']
assert not CAP['selected'] and CAP['CS_complete_inner_restoration_pending']
physical=lambda o:{k:v for k,v in o.items() if k!='net_code'}
for o in CAP['removed_native_records']:
    assert physical(by[o['uuid']])==physical(o)
CAP_CUTS={o['uuid'] for o in CAP['removed_native_records']}
CAP_PRIVATE_CUTS=set(CAP['removed_private_routes'])
assert not CAP_CUTS & REMOVED_NATIVE_IDS
assert CAP_PRIVATE_CUTS <= {q[0]['uuid'] for q in BASE}
moving={p['uuid'] for p in CAP['transformed_pads']}
BASE=[q for q in BASE if q[0]['uuid'] not in CAP_CUTS|CAP_PRIVATE_CUTS|moving]
BASE += [entry(p) for p in CAP['transformed_pads']]
BASE += [track(r['net'],r['layer'],r['points'],r['name'],r['width']) for r in CAP['routes']]
REMOVED_NATIVE_IDS=REMOVED_NATIVE_IDS|CAP_CUTS
_old_one_pad=one_pad
_cap_pads={p['key']:p for p in CAP['transformed_pads']}
def one_pad(key):
    return _cap_pads[key] if key in _cap_pads else _old_one_pad(key)
_old_binding=binding
def binding():
    b=_old_binding()
    b.update(cap_support_receipt=dict(file=str(CAP_PATH.relative_to(ROOT)),sha256=hashlib.sha256(CAP_PATH.read_bytes()).hexdigest()),
             explicit_source_removals=sorted(REMOVED_NATIVE_IDS),cap_poses=CAP['poses'],
             explicit_private_replacements=sorted(CAP_PRIVATE_CUTS),CS_complete_inner_restoration_pending=True,
             original_INT_RPM_DSM_objects_retained=True,IMU_feed_replacement_still_required_for_barrel=False,
             fresh_IMU_reference_power_AC_required=True,prospective_MID_minimum_extra_clearance_mm=.000734354138162141,
             diagnostic_left_barrel_selected=False)
    b['complete_functions']=[f for f in b.get('complete_functions',[]) if not f.startswith('FLASH_CS')]
    b['pending_functions']=list(dict.fromkeys(b.get('pending_functions',[])+['Complete FLASH_CS inner restoration after cap revision']))
    return b
s.OBJECTS=BASE
