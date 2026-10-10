"""Passing local rotated clamp, with the complete B-divider explicitly pending."""
import copy, hashlib, json, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent.parent/'native13-access'))
from composite_native11_CS_caps_return import *
CFILE=Path(__file__).with_name('U15-rotated-original-channels-feed11.json')
C=json.loads(CFILE.read_text());assert C['finite_pass']
physical=lambda o:{k:v for k,v in o.items()if k!='net_code'}
for o in C['removed_native_records']:assert physical(o)==physical(by[o['uuid']]),o['uuid']
C_CUTS={o['uuid']for o in C['removed_native_records']}
C_PRIVATE=set(C['removed_private_records'])
BASE=[q for q in BASE if q[0]['uuid']not in C_CUTS|C_PRIVATE and q[0].get('ref')not in ['U15','R43','R44']]
BASE += [entry(p)for p in C['changed_pad_records']]
BASE += [track(r['net'],r['layer'],r['points'],r['name'],r['width'])for r in C['selected_routes']]
REMOVED_NATIVE_IDS=REMOVED_NATIVE_IDS|C_CUTS
BRANCHES=C['selected_routes'][1:5]
_old_one_pad=one_pad
_c_pads={p['key']:p for p in C['changed_pad_records']}
def one_pad(key):return _c_pads[key]if key in _c_pads else _old_one_pad(key)
_old_binding=binding
def binding():
 b=_old_binding();b.update(rotated_U15_receipt=dict(file=str(CFILE.relative_to(ROOT)),sha256=hashlib.sha256(CFILE.read_bytes()).hexdigest()),
    explicit_source_removals=sorted(REMOVED_NATIVE_IDS),U15_transform=C['footprint_transform'],
    pending_B_divider_dependency=C['pending_B_divider_dependency'],complete_C_branches=False)
 return b
def branch_objects(branch,objects):
 """Physical branch isolation outside the actual bonded pin."""
 alias=branch['net']+'::'+branch['role'];names={r['name']:r for r in BRANCHES};out=[]
 for o,c,m,d in objects:
  net=o['net'];key=o.get('key');r=names.get(o['uuid'])
  if r:net=r['net']+'::'+r['role']
  elif net=='PORT_C_RX_EXT':
   role='upstream'if key in ['J11.1','U15.10']else'downstream';net=alias if key=='U15.1'else net+'::'+role
  elif net=='PORT_C_TX_EXT':
   role='upstream'if key in ['J11.2','U15.9']else'downstream';net=alias if key=='U15.2'else net+'::'+role
  out.append((dict(o,net=net),c,m,d))
 return alias,out
s.OBJECTS=BASE
