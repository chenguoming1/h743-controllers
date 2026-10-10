"""Conditional complete three-terminal ADC cluster; actual divider join is explicit."""
import hashlib
import json
import sys
from pathlib import Path
_CLUSTER_HOME=Path(__file__).resolve().parent
sys.path.insert(0,str(_CLUSTER_HOME.parent/'native13-access'))
from composite_native11_divider_joint import *
_CLUSTER_PATH=_CLUSTER_HOME/'R42-C31-full-supply12757-corrected.json'
CLUSTER=json.loads(_CLUSTER_PATH.read_text())
assert CLUSTER['complete_cluster'] and CLUSTER['corrected_inherited_BOOT_layer']['actual']=='B.Cu'
assert CLUSTER['held_BOOT_route']['layer']=='B.Cu'
assert CLUSTER['source']==binding()
_CLUSTER_CUTS={q['uuid']for q in CLUSTER['removed_native_records']}
for q in CLUSTER['removed_native_records']:
    assert {k:v for k,v in q.items()if k!='net_code'}=={k:v for k,v in by[q['uuid']].items()if k!='net_code'}
BASE=[q for q in BASE if q[0]['uuid']not in _CLUSTER_CUTS and q[0].get('ref')not in ('R42','C31')]
CLUSTER_PADS=CLUSTER['selected']['transformed_pad_records']
CLUSTER_ROUTES=CLUSTER['routes']+CLUSTER['held_SERVO_routes']+[CLUSTER['held_BOOT_route']]
CLUSTER_VIAS=CLUSTER['vias']+CLUSTER['held_SERVO_vias']+[CLUSTER['held_BOOT_via']]
BASE += [entry(q)for q in CLUSTER_PADS]
BASE += [track(q['net'],q['layer'],q['points'],q['name'],q['width'])for q in CLUSTER_ROUTES]
BASE += [via(q['net'],q['xy'],q['name'])for q in CLUSTER_VIAS]
assert len({q[0]['uuid']for q in BASE})==len(BASE)
REMOVED_NATIVE_IDS=set(REMOVED_NATIVE_IDS)|_CLUSTER_CUTS
pads={}
for o,c,m,d in BASE:
    if o['kind']=='pad':pads.setdefault(o['key'],[]).append(o)
def one_pad(key):
    rows=pads[key];assert len(rows)==1,(key,len(rows));return rows[0]
_cluster_prior_binding=binding
def binding():
    b=_cluster_prior_binding()
    b.update(cluster_receipt=dict(file=str(_CLUSTER_PATH.relative_to(ROOT)),sha256=hashlib.sha256(_CLUSTER_PATH.read_bytes()).hexdigest()),explicit_source_removals=sorted(REMOVED_NATIVE_IDS),cluster_poses=CLUSTER['selected']['poses'],complete_three_terminal_ADC_cluster=True,actual_ADC_tree_complete=CLUSTER['complete_ADC_tree'],actual_BOOT_tree_complete=False,old_R42_footprint_and_exclusive_supply_leaf_released=True,old_C31_ground_return_replaced=True,plane_behavior_qualified=False,fresh_power_ADC_settling_noise_reference_required=True,native_candidate=False)
    b['complete_functions']=list(dict.fromkeys(b.get('complete_functions',[])+['R42 actual supply and R42.2/C31.1/U1.10 ADC cluster','C31 dedicated ground return','SERVO1 complete donor restoration']))
    b['pending_functions']=[f for f in b.get('pending_functions',[])if 'SERVO1 transition'not in f]
    return b
s.OBJECTS=BASE
