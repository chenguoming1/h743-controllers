"""Complete failed SMD terminal entries inside their own native pad regions.

Add short same-net tracks from the existing route end to the native pad center.
This is explicit native completion, with all prior copper, fills and drill shapes
retained. Native DRC/process/protection and endpoint checks remain mandatory.
"""
import argparse,hashlib,json,shutil,sys
from pathlib import Path
import pcbnew as p
ROOT=Path(__file__).resolve().parent;sys.path.insert(0,str(ROOT/'native-tools'))
from export_native_copper import export
sha=lambda f:hashlib.sha256(Path(f).read_bytes()).hexdigest()
ap=argparse.ArgumentParser(description=__doc__)
for key in ['source','audit','out']:ap.add_argument('--'+key,type=Path,required=True)
a=ap.parse_args();src=a.source;dst=a.out;assert not dst.exists()
board=src/'f722-heli.kicad_pcb';native=json.loads((src/'f722-heli.native.json').read_text());audit=json.loads(a.audit.read_text());lm=json.loads((src/'f722-heli.logical-route-map.json').read_text());assert native['board_sha256']==audit['candidate_board_sha256']==lm['board_sha256']==sha(board)
assert not audit['via_failures'] and not audit['unresolved_contacts']
by_id={o['uuid']:o for o in native['objects']};failures=audit['pad_failures'];assert failures
shutil.copytree(src,dst,ignore=shutil.ignore_patterns('*.json','*.log','*.png','*.svg','*.py','*.ses','*.md','*.kicad_prl','__pycache__'))
for name in ['parts.json','poses-native.json']:
 if(src/name).exists():shutil.copyfile(src/name,dst/name)
b=p.LoadBoard(str(board));rows=[];netmap=dict(lm['logical_route_map'])
for failed in failures:
 pad=by_id[failed['pad_uuid']];old=by_id[failed['track_uuid']];assert pad['smd'] and not pad['drill'] and pad['net']==old['net']==failed['net']
 layer=failed['layer'];start=failed['xy_mm'];end=pad['xy'];assert layer in ['F.Cu','B.Cu'] and old[failed['endpoint']]==start
 t=p.PCB_TRACK(b);t.SetStart(p.VECTOR2I(*[round(v*1e6)for v in start]));t.SetEnd(p.VECTOR2I(*[round(v*1e6)for v in end]));t.SetWidth(127000);t.SetLayer(b.GetLayerID(layer));t.SetNet(b.FindNet(pad['net']));b.Add(t)
 uid=t.m_Uuid.AsString();logical=netmap[old['uuid']];netmap[uid]=logical;rows.append(dict(uuid=uid,logical_net=logical,net=pad['net'],layer=layer,start=start,end=end,width_mm=.127,pad_uuid=pad['uuid'],pad_key=pad['key'],original_route_uuid=old['uuid']))
assert all(t.GetNetname()==next(r['net']for r in rows if r['uuid']==t.m_Uuid.AsString())for t in b.GetTracks()if t.m_Uuid.AsString()in {r['uuid']for r in rows})
out=dst/'f722-heli.kicad_pcb';p.SaveBoard(str(out),b);after=export(out);now={o['uuid']:o for o in after['objects']};assert all(now.get(uid)==o for uid,o in by_id.items())
assert all(native[k]==after[k]for k in ['footprints','zones','edge_cuts','copper_layers'])
assert all(now[r['uuid']]['net']==r['net'] for r in rows)
(dst/'f722-heli.native.json').write_text(json.dumps(after,separators=(',',':'))+'\n')
(dst/'f722-heli.logical-route-map.json').write_text(json.dumps(dict(schema='f722-logical-route-map/v1',board_sha256=sha(out),source_sha256=sha(board),logical_route_map=netmap),indent=2)+'\n')
receipt=dict(source_board_sha256=sha(board),board_sha256=sha(out),source_native_sha256=sha(src/'f722-heli.native.json'),input_audit_sha256=sha(a.audit),constructor_sha256=sha(Path(__file__)),all_source_objects_exact=len(by_id),all_saved_zones_drills_and_poses_exact=True,refill_performed=False,new_vias=0,extensions=rows,engine_claim='Original engine paths retained; these short pad-entry extensions are explicit native completion.',native_qualification_pending=True)
(dst/'pad-entry-completion.json').write_text(json.dumps(receipt,indent=2)+'\n');shutil.copyfile(__file__,dst/'complete_native_pad_entries.used.py');print(json.dumps(receipt))
