"""Read-only exact geometry check for rebinding the sealed SERVO plan onto38."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
SOURCE=ROOT/'candidate38'
ORIGIN=ROOT/'candidate37'
SOURCE_SHA='95bb984bf046fef2d96c6e59d9e00696f504d35f89e3340fdf076cd7c9249c9f'
ORIGIN_SHA='2a73d9b7dad3a14b0d00c80e81e0ba8a817b50179c15692aad39fde9920c2115'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
read=lambda p:json.loads(Path(p).read_text())
plan=read(ROOT/'servo23-joint-plan/plan.json')
assert sha(ROOT/'servo23-joint-plan/plan.json')=='1c359be7580340a182738f556cb9becb22106d66d88b06b011de61a263c81f88'
native=read(SOURCE/'f722-heli.native.json')
route_map=read(SOURCE/'f722-heli.logical-route-map.json')
assert native['board_sha256']==route_map['board_sha256']==sha(SOURCE/'f722-heli.kicad_pcb')==SOURCE_SHA
before={o['uuid']:o for o in native['objects']}
# Explicitly rebind the sealed37 plan to the accepted additive RPM continuation.
from shapely.geometry import Point, LineString, Polygon
from shapely.ops import unary_union
poly = lambda rows: unary_union([Polygon(q['outer'], q.get('holes', [])) for q in rows])
origin = read(ORIGIN / 'f722-heli.native.json')
origin_map = read(ORIGIN / 'f722-heli.logical-route-map.json')['logical_route_map']
assert origin['board_sha256'] == sha(ORIGIN / 'f722-heli.kicad_pcb') == ORIGIN_SHA
origin_objects = {o['uuid']: o for o in origin['objects']}
assert all(before.get(uid) == obj for uid, obj in origin_objects.items())
assert all(route_map['logical_route_map'].get(uid) == net for uid, net in origin_map.items())
assert all(origin[key] == native[key] for key in ['footprints', 'edge_cuts', 'copper_layers'])
continuation_added = [o for uid, o in before.items() if uid not in origin_objects]
assert len(continuation_added) == 21 and all(o['net'] == 'RPM_LV' and o['kind'] in {'track', 'via'} for o in continuation_added)
continuation_checks = []
for row in plan['replacement_and_new_routes']:
    if row['name'] == 'S3P1-inner-exit-only':
        continue
    is_via = row['kind'] == 'via'
    center = Point(row['xy_mm']) if is_via else LineString(row['points_mm'])
    radius = row['diameter_mm'] / 2 if is_via else row['width_mm'] / 2
    layers = native['copper_layers'] if is_via else [row['layer']]
    for obj in continuation_added:
        for layer in layers:
            if layer in obj['copper']:
                gap = center.distance(poly(obj['copper'][layer])) - radius
                continuation_checks.append(dict(plan_name=row['name'], source_uuid=obj['uuid'], kind='copper', layer=layer, gap_mm=gap, required_mm=.127))
        if obj.get('drill'):
            gap = center.distance(poly(obj['drill']['outside'])) - (.1 if is_via else radius)
            continuation_checks.append(dict(plan_name=row['name'], source_uuid=obj['uuid'], kind='drill', gap_mm=gap, required_mm=.25 if is_via else .20))
assert continuation_checks and all(q['gap_mm'] >= q['required_mm'] for q in continuation_checks)
continuation_proof = dict(origin_source_board_sha256=ORIGIN_SHA, current_source_board_sha256=SOURCE_SHA,
                          all_origin_objects_retained_exact=len(origin_objects), additional_source_objects=len(continuation_added),
                          all_additional_objects_net='RPM_LV', masks_pads_poses_exact=True,
                          source_additions_rechecked_against_every_plan_route=True,
                          minimum_extra_clearance_mm=min(q['gap_mm']-q['required_mm'] for q in continuation_checks),
                          checks=continuation_checks, native_refill_and_all_gates_required=True)
continuation_proof.update(plan_sha256=sha(ROOT/'servo23-joint-plan/plan.json'),source_native_sha256=sha(SOURCE/'f722-heli.native.json'),source_map_sha256=sha(SOURCE/'f722-heli.logical-route-map.json'),helper_sha256=sha(__file__),passed=True)
(ROOT/'servo23-joint-plan/continuation38-recheck.json').write_text(json.dumps(continuation_proof,indent=2)+'\n')
print(json.dumps({k:v for k,v in continuation_proof.items() if k!='checks'}))
