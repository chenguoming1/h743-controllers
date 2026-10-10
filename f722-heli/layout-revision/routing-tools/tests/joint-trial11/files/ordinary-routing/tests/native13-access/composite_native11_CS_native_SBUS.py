"""Complete CS support with the original native SBUS segment restored exactly."""
from composite_native11_CS_caps_return import *
NATIVE_SBUS_ID='ad46ffd3-a7c9-55fc-8989-1df897b6cd34'
assert NATIVE_SBUS_ID in REMOVED_NATIVE_IDS
assert by[NATIVE_SBUS_ID]['net']=='SBUS_HV'
BASE=[q for q in BASE if q[0]['uuid']!='caps-right-SBUS-HV-complete-bend']+[entry(by[NATIVE_SBUS_ID])]
CS_REQUIRED_ROUTES=[r for r in CS_REQUIRED_ROUTES if r['name']!='caps-right-SBUS-HV-complete-bend']
REMOVED_NATIVE_IDS=set(REMOVED_NATIVE_IDS)-{NATIVE_SBUS_ID}
_before_native_sbus=binding
def binding():
    b=_before_native_sbus();b.update(explicit_source_removals=sorted(REMOVED_NATIVE_IDS),native_SBUS_HV_segment_restored=NATIVE_SBUS_ID,
        unnecessary_private_SBUS_bend_removed=True,diagnostic_left_barrel_unselected=True)
    return b
s.OBJECTS=BASE
