"""Current complete C/cluster/CS source with the exact native SBUS lead restored."""
from composite_native11_rotated_U15_cluster_CS import *
BEFORE_NATIVE_SBUS_BINDING=binding()
NATIVE_SBUS_ID='ad46ffd3-a7c9-55fc-8989-1df897b6cd34'
PRIVATE_SBUS_ID='caps-right-SBUS-HV-complete-bend'
assert NATIVE_SBUS_ID in REMOVED_NATIVE_IDS
assert any(q[0]['uuid']==PRIVATE_SBUS_ID for q in BASE)
BASE=[q for q in BASE if q[0]['uuid']!=PRIVATE_SBUS_ID]+[entry(by[NATIVE_SBUS_ID])]
REMOVED_NATIVE_IDS=set(REMOVED_NATIVE_IDS)-{NATIVE_SBUS_ID}
_native_sbus_previous_binding=binding
def binding():
 b=_native_sbus_previous_binding();b.update(explicit_source_removals=sorted(REMOVED_NATIVE_IDS),
   native_SBUS_HV_segment_restored=NATIVE_SBUS_ID,unnecessary_private_SBUS_bend_removed=True,diagnostic_left_barrel_unselected=True)
 return b
s.OBJECTS=BASE
