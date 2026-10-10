"""Current simultaneous conditional geometry; named owner restorations remain pending."""
import json,hashlib
from native11_context import *
P=H/'CSGREEN-C-RED-CAP-complete-geometry-native11.json';PACKET=json.loads(P.read_text());assert PACKET['complete_simultaneous_finite_geometry']and PACKET['native_source_board_sha256']==EXPECTED
cut={o['uuid']for o in PACKET['removed_native_records']};physical=lambda o:{k:v for k,v in o.items()if k!='net_code'}
assert all(physical(by[o['uuid']])==physical(o)for o in PACKET['removed_native_records'])
BASE=[q for q in BASE if q[0]['uuid']not in cut]
BASE +=[track(r['net'],r['layer'],r['points'],r['name'],r['width'])for r in PACKET['selected_routes']]
BASE +=[via(v['net'],v['xy'],v['name'])for v in PACKET['selected_vias']]
assert len({q[0]['uuid']for q in BASE})==len(BASE)
REMOVED_NATIVE_IDS=cut;s.OBJECTS=BASE
_source_binding=binding
def binding():
 b=_source_binding();b.update(all_native_objects_retained=False,explicit_source_removals=sorted(cut),speculative_overlays=[dict(file=str(P.relative_to(ROOT)),sha256=hashlib.sha256(P.read_bytes()).hexdigest())],complete_functions=PACKET['complete_functions'],pending_functions=PACKET['pending_functions'],native_candidate=False);return b
