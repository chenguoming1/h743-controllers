"""Ordinary four-signal-layer complete BOOT witness; no ground-plane exception."""
import hashlib,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent.parent/'portc51'))
from composite_native11_C_TX_WP import *
BOOT_FILE=Path(__file__).with_name('joint-BOOT-current-peer-plane-feasibility11.json')
BOOT=json.loads(BOOT_FILE.read_text())
assert BOOT['source']==binding() and BOOT['complete'] and BOOT['graph_connected']
assert not BOOT.get('bounded_plane_bridge')
CUTS={'9e6756f4-4622-4a5f-80e2-4c78e46894ce','d354ba09-c0ed-4352-9f87-8f6fa70ec378'}
assert {x['uuid']for x in BOOT['obsolete_R42_pendant_contact_proof']}==CUTS
BASE=[q for q in BASE if q[0]['uuid']not in CUTS]
BOOT_ROUTES=[dict(r,name='owner-complete-BOOT-'+str(i))for i,r in enumerate(BOOT['routes'])if r['layer']!='B.Cu']
BOOT_VIAS=[dict(v,name='owner-complete-BOOT-via-'+str(i))for i,v in enumerate(BOOT['vias'])]
BASE +=[track(r['net'],r['layer'],r['points'],r['name'],r['width'])for r in BOOT_ROUTES]
BASE +=[via(v['net'],v['xy'],v['name'])for v in BOOT_VIAS]
REMOVED_NATIVE_IDS=REMOVED_NATIVE_IDS|CUTS
assert len({q[0]['uuid']for q in BASE})==len(BASE)
_prior_binding=binding
def binding():
 b=_prior_binding();b.update(complete_BOOT_receipt=dict(file=str(BOOT_FILE.relative_to(ROOT)),sha256=hashlib.sha256(BOOT_FILE.read_bytes()).hexdigest()),explicit_source_removals=sorted(REMOVED_NATIVE_IDS),BOOT_ordinary_complete_pending_seal=True,ground_layer_exception=False)
 return b
s.OBJECTS=BASE
