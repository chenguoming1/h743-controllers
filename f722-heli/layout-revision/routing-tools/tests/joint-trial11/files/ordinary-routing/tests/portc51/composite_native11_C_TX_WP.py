"""Complete TX/WP coupled witness and all exact source-bound C support."""
import hashlib,json
from composite_native11_rotated_U15_cluster_CS_native_SBUS import *
TXWP_FILE=Path(__file__).with_name('U15-TX-WP-complete-copper11-transaction-v2.json')
TXWP=json.loads(TXWP_FILE.read_text());assert not TXWP['full_declared_width_peer_audit_pending']
assert TXWP['complete_TX_upstream']and TXWP['complete_WP_copper']
assert TXWP['source']==binding()
cuts={o['uuid']for o in TXWP['removed_native_records']}
for o in TXWP['removed_native_records']:assert physical(o)==physical(by[o['uuid']])
BASE=[q for q in BASE if q[0]['uuid']not in cuts]
for r in TXWP['routes']+TXWP['reserved_peer_routes']:
 q=track(r['net'],r['layer'],r['points'],r['name'],r['width'])
 if 'role'in r:q=(dict(q[0],role=r['role']),q[1],q[2],q[3])
 BASE.append(q)
BASE += [via(v['net'],v['xy'],v['name'])for v in TXWP['vias']+TXWP['reserved_peer_vias']]
REMOVED_NATIVE_IDS=REMOVED_NATIVE_IDS|cuts
assert len({q[0]['uuid']for q in BASE})==len(BASE)
_prior_binding=binding
def binding():
 b=_prior_binding();b.update(TX_WP_receipt=dict(file=str(TXWP_FILE.relative_to(ROOT)),sha256=hashlib.sha256(TXWP_FILE.read_bytes()).hexdigest()),
    explicit_source_removals=sorted(REMOVED_NATIVE_IDS),complete_C_TX_upstream=True,complete_WP_restoration=True,
    three_C_protected_branches_pending=True,all_C_MCU_trunks_pending=True,native_candidate=False)
 return b
def branch_objects(branch,objects):
 alias=branch['net']+'::'+branch['role'];prefixes={r['name']:r for r in BRANCHES};out=[]
 for o,c,m,d in objects:
  net=o['net'];key=o.get('key');r=prefixes.get(o['uuid']);role=o.get('role')
  if r:net=r['net']+'::'+r['role']
  elif role and net in ['PORT_C_RX_EXT','PORT_C_TX_EXT']:net=net+'::'+role
  elif net=='PORT_C_RX_EXT':
   role='upstream'if key in ['J11.1','U15.10']else'downstream'
   net=(alias if branch['net']==net else net+'::bonded')if key=='U15.1'else net+'::'+role
  elif net=='PORT_C_TX_EXT':
   role='upstream'if key in ['J11.2','U15.9']else'downstream'
   net=(alias if branch['net']==net else net+'::bonded')if key=='U15.2'else net+'::'+role
  out.append((dict(o,net=net),c,m,d))
 return alias,out
s.OBJECTS=BASE
