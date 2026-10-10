"""Complete CS/DSM exchange with independent outward sensor ground returns."""
import hashlib,json
from composite_native11_complete_BOOT import *
DEDICATED_FILE=H/'dedicated-IMU-DSM-CS-complete11.json'
DEDICATED=json.loads(DEDICATED_FILE.read_text())
assert DEDICATED['complete'] and DEDICATED['full_CS_tree_complete'] and DEDICATED['all_terminal_partitions_preserved']
assert DEDICATED['source']==binding()
DEDICATED_CUTS={o['uuid']for o in DEDICATED['removed_native_records']}
DEDICATED_PRIVATE=set(DEDICATED['removed_private_names'])
for o in DEDICATED['removed_native_records']:assert physical(o)==physical(by[o['uuid']])
assert DEDICATED_CUTS|DEDICATED_PRIVATE<={q[0]['uuid']for q in BASE}
BASE=[q for q in BASE if q[0]['uuid']not in DEDICATED_CUTS|DEDICATED_PRIVATE]
BASE +=[track(r['net'],r['layer'],r['points'],r['name'],r['width'])for r in DEDICATED['routes']]
BASE +=[via(v['net'],v['xy'],v['name'])for v in DEDICATED['vias']]
REMOVED_NATIVE_IDS=REMOVED_NATIVE_IDS|DEDICATED_CUTS
assert len({q[0]['uuid']for q in BASE})==len(BASE)
# Accessors expose only actual current pads. Released F divider pads are absent.
pads={}
for o,co,ma,dr in BASE:
 if o.get('kind')=='pad':pads.setdefault(o['key'],[]).append(o)
def one_pad(key):
 rows=pads.get(key,[])
 assert len(rows)==1,(key,'must identify exactly one actual current pad',len(rows))
 return rows[0]
_dedicated_previous_binding=binding
def binding():
 b=_dedicated_previous_binding();b.update(explicit_source_removals=sorted(REMOVED_NATIVE_IDS),
  dedicated_IMU_CS_receipt=dict(file=str(DEDICATED_FILE.relative_to(ROOT)),sha256=hashlib.sha256(DEDICATED_FILE.read_bytes()).hexdigest()),
  shared_U2_6_U2_7_ground_return_changed=False,U2_7_return_relocated=True,two_independent_IMU_return_barrels=True,
  inherited_U2_6_return_exact=True,complete_DSM_transition_restored=True,complete_CS_tree_preserved=True,
  released_F_divider_pads_absent_from_current_accessors=True,B_divider_complete=False,local_divider_support_complete=False,declared_poses={},actual_BOOT_tree_complete=True,actual_ADC_tree_complete=False,original_INT_RPM_DSM_objects_retained=False,original_INT_RPM_objects_retained=True,native_candidate=False,
  fresh_IMU_reference_return_AC_power_review_required=True,
  mounting_body_outward_strip_copper_mm2=DEDICATED['mounting_body_projection']['body_copper_outside_actual_pad_area_mm2'],
  inherited_drill_guidance_departure=DEDICATED['inherited_drill_guidance_departure'])
 b['complete_functions']=['FLASH_CS actual U1.33/U3.1/R4.2 tree','DSM_RX_MCU complete original actual-pad partitions with relocated transition','BOOT actual U1.60/R2.1/both SW1.2 tree','FLASH_WP_N actual R5.2/U3.3 path','GREEN and RED actual-terminal witnesses','SERVO1 complete donor restoration','R34 entries and J11/ABC support','C TX upstream actual U15.2/NC9 to J11.2 with protected cut']
 b['pending_functions']=['Complete FLASH_SCK/FLASH_MISO/FLASH_MOSI','Remaining C protected branches and both MCU links','Complete R43/R44 divider MID and dedicated ground plus ADC connection','Fresh native source/contact/fill/process/return/reference/power/AC qualification']
 return b
s.OBJECTS=BASE
