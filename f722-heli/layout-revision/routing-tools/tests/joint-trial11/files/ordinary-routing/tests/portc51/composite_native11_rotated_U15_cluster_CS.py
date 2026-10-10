"""Rotated C cell with corrected complete R42/C31 and SERVO1 support held."""
import hashlib,json
from composite_native11_rotated_U15_CS import *
CLUSTER_FILE=Path(__file__).resolve().parent.parent/'boot56/R42-C31-full-supply12757-corrected.json'
CLUSTER=json.loads(CLUSTER_FILE.read_text())
assert CLUSTER['complete_cluster'] and CLUSTER['held_BOOT_route']['layer']=='B.Cu'
assert CLUSTER['source']['board_sha256']==N['board_sha256']
K={p['uuid']for p in CLUSTER['removed_native_records']}
for p in CLUSTER['removed_native_records']:assert physical(p)==physical(by[p['uuid']]),p['uuid']
BASE=[q for q in BASE if q[0]['uuid']not in K and q[0].get('ref')not in ['R42','C31']]
BASE += [entry(p)for p in CLUSTER['selected']['transformed_pad_records']]
BASE += [track(r['net'],r['layer'],r['points'],r['name'],r['width'])for r in CLUSTER['routes']+CLUSTER['held_SERVO_routes']+[CLUSTER['held_BOOT_route']]]
BASE += [via(v['net'],v['xy'],v['name'])for v in CLUSTER['vias']+CLUSTER['held_SERVO_vias']+[CLUSTER['held_BOOT_via']]]
assert len({q[0]['uuid']for q in BASE})==len(BASE)
REMOVED_NATIVE_IDS=REMOVED_NATIVE_IDS|K
_cluster_pads={p['key']:p for p in CLUSTER['selected']['transformed_pad_records']}
_previous_one_pad=one_pad
def one_pad(key):return _cluster_pads[key]if key in _cluster_pads else _previous_one_pad(key)
_previous_binding=binding
def binding():
 b=_previous_binding();b.update(cluster_receipt=dict(file=str(CLUSTER_FILE.relative_to(ROOT)),sha256=hashlib.sha256(CLUSTER_FILE.read_bytes()).hexdigest()),
    explicit_source_removals=sorted(REMOVED_NATIVE_IDS),complete_three_terminal_ADC_cluster=True,complete_SERVO1_support=True,
    actual_BOOT_entry_layer='B.Cu',actual_ADC_divider_join_pending=True,cluster_poses=CLUSTER['selected']['poses'])
 return b
s.OBJECTS=BASE
