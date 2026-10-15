"""Seal the read-only research artifacts; never changes board or schematic."""
from source_context import *
import uuid
p=D/'complete-transaction.json';o=json.loads(p.read_text())
for q in o['add_primitives']:
 q['uuid']=str(uuid.uuid5(uuid.NAMESPACE_URL,'nexus-r57-usb-proposal:'+H+':'+q['id']))
o['schema']='nexus-read-only-primitive-transaction-v1';o['application_preconditions']=['Require whole source SHA256 match before applying; otherwise compare every local retained and deleted record and re-screen changed context.','Remove only delete_uuids; preserve original bridge and reused-via UUIDs without duplication.','Add exact segment endpoints or arc start/mid/end with supplied ordinary-via dimensions. Coordinates in mm; any CAD quantization requires fresh native validation.','This file is a proposed transaction, not a board patch that has been applied.'];o['selected_connector_variant']='ports/compact-in1-port-proposal.json';p.write_text(json.dumps(o,indent=2)+'\n')
s=D/'integration-screen.json';r=json.loads(s.read_text());bar=json.loads((D/'ports/compact-in1-path-via-accounting.json').read_text())
for row in r['exact_endpoint_paths']:
 b=next(x for x in bar['paths'] if x['net']==row['net'] and x['orientation']==row['connector'][3]);row['used_barrel_centerline_bookkeeping_mm']=b['used_barrel_mm']+abs(zcenters['B.Cu']-zcenters['In3.Cu']);row['barrel_bookkeeping_note']='Copper layer-center separations for used transitions only; excludes unused through-via stubs, spreading, capacitance and inductance. Not electrical delay.'
r['source_sha256_after']=hashlib.sha256(S.read_bytes()).hexdigest();s.write_text(json.dumps(r,indent=2)+'\n')
