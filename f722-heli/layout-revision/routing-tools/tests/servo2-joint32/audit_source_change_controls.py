"""Check the exact SERVO2 replacement and logical ownership, with rejection controls."""
import copy
import hashlib
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from validate_ordinary_rewrite import validate

sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
read = lambda p: json.loads(p.read_text())
source, candidate = ROOT/'candidate32', ROOT/'candidate33'
receipt_path = Path(__file__).with_name('construction.json')
before, after = [read(p/'f722-heli.native.json') for p in [source,candidate]]
before_map, after_map = [read(p/'f722-heli.logical-route-map.json') for p in [source,candidate]]
receipt = read(receipt_path)
allowed, change = validate(before,after,receipt_path,sha(source/'f722-heli.native.json'))
old = {o['uuid']:o for o in before['objects']}
now = {o['uuid']:o for o in after['objects']}
expected = {uid:r['after'] for uid,r in receipt['logical_reassignments'].items()}
actual = {}
for uid, alias in before_map['logical_route_map'].items():
    if uid not in now: continue
    new_alias = after_map['logical_route_map'][uid]
    if alias != new_alias: actual[uid] = new_alias
assert actual == expected
for uid,r in receipt['logical_reassignments'].items():
    assert before_map['logical_route_map'][uid] == r['before']
    assert old[uid] == now[uid] and old[uid]['kind'] == 'via'
assert after_map['board_sha256'] == after['board_sha256'] == sha(candidate/'f722-heli.kicad_pcb')
assert all(uid in now and now[uid]['net'] == alias.split('::')[0] for uid,alias in after_map['logical_route_map'].items())

def reject(label, changed_after=None, changed_receipt=None):
    with tempfile.TemporaryDirectory(prefix='f722-rewrite-control-') as folder:
        path = Path(folder)/'receipt.json'
        path.write_text(json.dumps(changed_receipt or receipt))
        try:
            validate(before, changed_after or after, path, sha(source/'f722-heli.native.json'))
        except AssertionError:
            return dict(control=label,rejected=True)
    raise AssertionError('Negative control accepted: '+label)

controls=[]
ground = next(o for o in before['objects'] if o['kind']=='via' and o['net']=='GND')
r=copy.deepcopy(receipt);r['mutable_route_uuids'].append(ground['uuid']);controls.append(reject('wrong_net_ground_via_allowance',changed_receipt=r))
q=copy.deepcopy(after);q['objects']=[o for o in q['objects'] if o['uuid']!=ground['uuid']];controls.append(reject('undeclared_ground_removal',changed_after=q))
r=copy.deepcopy(receipt);r['source_board_sha256']='0'*64;controls.append(reject('stale_source_receipt',changed_receipt=r))
q=copy.deepcopy(after);next(o for o in q['objects'] if o['uuid'] in actual)['xy'][0]+=.01;controls.append(reject('in_place_existing_via_move',changed_after=q))
q=copy.deepcopy(after);next(o for o in q['objects'] if o['uuid'] not in old)['net']='USB_P';controls.append(reject('new_copper_on_undeclared_net',changed_after=q))
result=dict(passed=True,source_board_sha256=before['board_sha256'],board_sha256=after['board_sha256'],
            source_change=change,exact_logical_reassignments=receipt['logical_reassignments'],
            reassigned_via_native_record_unchanged=True,negative_controls=controls,
            audit_source_sha256=sha(Path(__file__)),validator_sha256=sha(ROOT/'validate_ordinary_rewrite.py'),
            source_map_sha256=sha(source/'f722-heli.logical-route-map.json'),map_sha256=sha(candidate/'f722-heli.logical-route-map.json'))
(candidate/'source-change-controls.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(dict(passed=True,negative_controls=len(controls),removed=len(change['actual_removed_uuids']),added=len(change['actual_added_uuids']),logical_reassignments=len(actual))))
