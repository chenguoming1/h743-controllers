"""Construct the explicitly reviewed two-branch SERVO2 native routing candidate.

This is a coordinated native rewrite, not an engine success or acceptance.
Only source SERVO2 P0 routes may be reconciled; all other copper stays exact.
"""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / 'candidate32'
OUT = ROOT / 'tests/servo2-joint32'
OUT.mkdir(parents=True, exist_ok=True)
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
read = lambda p: json.loads(p.read_text())
board = SOURCE / 'f722-heli.kicad_pcb'
native_path = SOURCE / 'f722-heli.native.json'
map_path = SOURCE / 'f722-heli.logical-route-map.json'
model_path = ROOT / 'model-candidate32-ready/model.json'
origin_path = ROOT / 'model-candidate31-ready/filtered05.successes/count2/snapshot.after.json'
n, lm, model, origin = map(read, [native_path, map_path, model_path, origin_path])
assert sha(board) == n['board_sha256'] == lm['board_sha256'] == model['board_sha256'] == '20072f5ed493d88dda69d61a69d8c6d9bcad9aa6d7eabed93ca060aa473cb035'
logical = lm['logical_route_map']
old = [o for o in n['objects'] if logical.get(o['uuid']) == 'SERVO2_MCU::P0']
assert len(old) == 15 and all(o['kind'] in ['track', 'via'] and o['net'] == 'SERVO2_MCU' for o in old)
assert not any(value == 'SERVO2_MCU::P1' for value in logical.values())
old_via = '2b07387c-0e51-4096-a791-30766feb86b6'
old_tail = '7ef93c2f-799a-4117-b124-c76999e6093b'
routes = []
def trace(alias, layer, points):
    assert len(points) >= 2 and layer in model['routable_layers']
    pts = [[round(v, 5) for v in xy] for xy in points]
    assert all(a != b for a, b in zip(pts, pts[1:]))
    routes.append(dict(kind='track', fixed='NOT_FIXED', nets=[alias], layer=layer, width=.127, points=pts))
def via(alias, xy):
    routes.append(dict(kind='via', fixed='NOT_FIXED', nets=[alias], xy=xy, diameter=.45, drill=.20))
for o in old:
    if o['kind'] == 'via':
        via('SERVO2_MCU::P1' if o['uuid'] == old_via else 'SERVO2_MCU::P0', o['xy'])
    else:
        layer = next(iter(o['copper']))
        if o['uuid'] == old_tail or (layer == 'F.Cu' and min(o['start'][1], o['end'][1]) > 10):
            continue
        trace('SERVO2_MCU::P0', layer, [o['start'], o['end']])

p0_front = [[10.7,10.7],[11.01,11.01],[11.01,12.505],[11.25,12.745],[12.79133,12.745],[13.21354,12.32279],[13.21354,12.2144]]
p1_front = [[10.16087,11.17593],[10.244,11.17593],[10.69,11.62193],[10.69,12.556],[11.138,13.004],[12.899,13.004],[13.035,12.868],[13.45,12.868],[13.45,11.8875]]
p0_tail = [[10.16087,10.03687],[10.16087,10.3],[10.56087,10.7],[10.7,10.7]]
trace('SERVO2_MCU::P0', 'F.Cu', p0_front)
trace('SERVO2_MCU::P0', 'In3.Cu', p0_tail)
via('SERVO2_MCU::P0', [10.7,10.7])
trace('SERVO2_MCU::P1', 'F.Cu', p1_front)
p1_origin = [r for r in origin['routes'] if r['nets'] == ['SERVO2_MCU::P1']]
inner = [r for r in p1_origin if r['kind'] == 'track' and r['layer'] == 'In2.Cu' and len(r['points']) > 2]
back = [r for r in p1_origin if r['kind'] == 'track' and r['layer'] == 'B.Cu']
assert len(inner) == len(back) == 1
trace('SERVO2_MCU::P1', 'In2.Cu', inner[0]['points'])
assert back[0]['points'][0] == [20.70863,18.77499]
trace('SERVO2_MCU::P1', 'B.Cu', [[20.71,19.475]] + back[0]['points'])
via('SERVO2_MCU::P1', [21.51385,13.71343])

source_logical = dict(logical)
source_logical[old_via] = 'SERVO2_MCU::P1'
contract = dict(schema='f722-explicit-ordinary-rewrite-import/v1', engine_planning_model=False,
                physical_board=str(board), physical_native=str(native_path), board_sha256=sha(board),
                native_sha256=sha(native_path), aliases=model['aliases'], ordinary_nets=model['ordinary_nets'],
                routable_layers=model['routable_layers'], mutable_source_ids=sorted(o['uuid'] for o in old),
                source_logical_nets=source_logical, regenerable_reference_zones=model['regenerable_reference_zones'],
                scope='Only declared SERVO2 routes may be removed/reconciled; power/critical/pad/pose geometry is immutable.')
model_out = OUT / 'native-construction-model.json'
model_out.write_text(json.dumps(contract, indent=2) + '\n')
networks = []
for alias in ['SERVO2_MCU::P0','SERVO2_MCU::P1']:
    wires = []
    for r in routes:
        if r['nets'] != [alias]: continue
        if r['kind'] == 'track':
            points = ' '.join(f'{round(x*1e5)} {-round(y*1e5)}' for x,y in r['points'])
            wires.append(f'(wire (path {r["layer"]} 12700 {points}) (type route))')
        else:
            x,y = r['xy']; wires.append(f'(via VIA_450_200 {round(x*1e5)} {-round(y*1e5)})')
    networks.append('(net ' + json.dumps(alias) + ' ' + ' '.join(wires) + ')')
session = '(session "explicit-servo2-joint" (base_design "f722-local") (routes (resolution mm 100000) (library_out (padstack VIA_450_200 (shape (circle F.Cu 45000)) (attach off))) (network_out ' + ' '.join(networks) + ')))\n'
(OUT/'constructed.ses').write_text(session)
report = dict(board_sha256=sha(board), model_sha256=sha(model_out), routes=routes,
              engine_routing_performed=False, explicit_native_construction=True, native_validation_required=True)
(OUT/'constructed-report.json').write_text(json.dumps(report,indent=2)+'\n')
receipt = dict(schema='f722-coordinated-servo2-native-construction/v1', engine_routing_performed=False,
               source_board_sha256=sha(board), source_native_sha256=sha(native_path), physical_net='SERVO2_MCU',
               mutable_route_uuids=contract['mutable_source_ids'], logical_reassignments={old_via:{'before':'SERVO2_MCU::P0','after':'SERVO2_MCU::P1'}},
               p0_front=p0_front,p1_front=p1_front,p0_inner_tail=p0_tail,
               reused_engine_p1_origin_sha256=sha(origin_path), source_route_map_sha256=sha(map_path),
               constructor_sha256=sha(Path(__file__)), role_model_sha256=sha(model_path),
               model_sha256=sha(model_out), session_sha256=sha(OUT/'constructed.ses'), report_sha256=sha(OUT/'constructed-report.json'),
               endpoint_completion='P1 MCU end extended inside actual U1.57 pad to [20.71,19.475], one nanometre from exported pad-center x; full native endpoint proof required.',
               mandatory_gates=['Explicit allowed removals and logical via reassignment','Native DRC/all/strict parity/process/mechanical/firmware','Finite full-width pad and drilled annular entry','Actual U12.3 cut and outside-pad gap','All support connectivity and source-bound critical/reference checks'],
               acceptance_claimed=False)
(OUT/'construction.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(dict(routes=len(routes),construction_receipt=str(OUT/'construction.json'))))
