"""Prepare a bounded native alternative to a failed single-layer branch insertion.

Only an actual captured located trace between adjacent protected-chain SMD pads
is accepted. Complete the ends inside those pads, simplify by native line of
sight, and retain all native clearance rules outside legitimate shared pads.
This edits no board and never substitutes an engine success claim.
"""
import argparse, hashlib, json, sys
from pathlib import Path
from shapely.geometry import Polygon, Point, LineString
from shapely.ops import unary_union

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'native-tools'))
from check_protection_paths import make_graph, groups_for_key

sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
poly = lambda rows: unary_union([Polygon(p['outer'], p.get('holes', [])) for p in rows])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ['board', 'native', 'logical-route-map', 'model', 'located-receipt', 'engine-log', 'out']:
        parser.add_argument('--' + key, type=Path, required=True)
    parser.add_argument('--logical-net', required=True)
    parser.add_argument("--continuation-source", type=Path)
    a = parser.parse_args()
    n = json.loads(a.native.read_text())
    model = json.loads(a.model.read_text())
    lm = json.loads(a.logical_route_map.read_text())
    raw = json.loads(a.located_receipt.read_text())
    assert n['board_sha256'] == model['board_sha256'] == lm['board_sha256'] == raw['board_sha256'] == sha(a.board)
    assert raw['model_sha256'] == sha(a.model)
    origin_source = dict(board_path=str(a.board.resolve()), board_sha256=sha(a.board),
                         native_path=str(a.native.resolve()), native_sha256=sha(a.native),
                         logical_map_path=str(a.logical_route_map.resolve()), logical_map_sha256=sha(a.logical_route_map))
    if a.continuation_source is not None:
        next_board = a.continuation_source / 'f722-heli.kicad_pcb'
        next_native = a.continuation_source / 'f722-heli.native.json'
        next_map = a.continuation_source / 'f722-heli.logical-route-map.json'
        newer = json.loads(next_native.read_text())
        newer_map = json.loads(next_map.read_text())
        assert newer['board_sha256'] == newer_map['board_sha256'] == sha(next_board)
        current = {o['uuid']: o for o in newer['objects']}
        assert all(current.get(o['uuid']) == o for o in n['objects']), 'Continuation changed source copper/pads'
        assert all(n[k] == newer[k] for k in ['footprints', 'edge_cuts', 'copper_layers'])
        assert all(newer_map['logical_route_map'].get(uid) == logical for uid, logical in lm['logical_route_map'].items())
        a.board, a.native, a.logical_route_map = next_board, next_native, next_map
        n, lm = newer, newer_map
    logical = a.logical_net
    net = model['aliases'][logical]
    role = model['roles'][net]
    assert role['kind'] == 'protected_chain'
    branch = next(b for b in role['branches'] if b['logical_net'] == logical)
    assert len(branch['terminals']) == 2
    records = []
    for line in a.engine_log.read_text().splitlines():
        if line.startswith('INSERT_DIAGNOSTIC '):
            r = json.loads(line[len('INSERT_DIAGNOSTIC '):])
            if r.get('net') == logical:
                records.append(r)
    assert records == raw['records'], 'Captured records differ from the retained actual engine log.'
    traces = [r for r in records if r['stage'] == 'located_trace']
    assert len(traces) == 1 and any(r['stage'] == 'failed_forced_trace_polyline' for r in records)
    located = traces[0]
    layer = located['layer']
    assert layer in ['F.Cu', 'B.Cu'] and located['half_width_mm'] == .0635
    assert not any('via' in r['stage'] for r in records), 'Multi-layer paths require separate native construction review.'
    pads = {o['key']: o for o in n['objects'] if o['kind'] == 'pad'}
    source, target = [pads[k] for k in branch['terminals']]
    assert source['smd'] and target['smd'], 'Use an annular entry method for plated terminal pads.'
    graph = make_graph([o for o in n['objects'] if o['net'] == net])
    assert not groups_for_key(graph, source['key']).intersection(groups_for_key(graph, target['key']))
    branches = {b['logical_net']: b for b in role['branches']}
    outline = poly(n['outline_with_npth']['polygons'])
    obstacles, holes, shared_obstacles, rules = [], [], [], []
    shared_receipts = []
    for o in n['objects']:
        if o.get('drill'):
            holes.append((o, poly(o['drill']['outside'])))
        if layer not in o['copper'] or o['uuid'] in [source['uuid'], target['uuid']]:
            continue
        shape = poly(o['copper'][layer])
        if o['net'] == net and o['kind'] != 'pad':
            alias = lm['logical_route_map'][o['uuid']]
            assert alias != logical, 'Existing copper in the same branch requires separate continuation review.'
            common = set(branch['terminals']).intersection(branches[alias]['terminals'])
            if common:
                cut = unary_union([poly(pads[key]['inside'][layer]) for key in common])
                shared_obstacles.append((o, shape.difference(cut), cut))
                shared_receipts.append(dict(uuid=o['uuid'], logical_net=alias, shared_pad_keys=sorted(common)))
                continue
        obstacles.append((o, shape))
    for z in n['zones']:
        if not z['rule']:
            assert layer not in z['layers'], 'This no-refill method requires an outside layer without a copper zone.'
        elif layer in z['layers'] and (z['forbid']['tracks'] or z['forbid']['copper']):
            rules.append((z, poly(z['outline'])))

    def check(points):
        line = LineString(points)
        shape = line.buffer(.0635, quad_segs=128)
        rows = [dict(kind='outline_npth', uuid='outline', gap_mm=line.distance(outline.boundary) - .0635, required_mm=.254)]
        if not outline.covers(shape):
            return False, [dict(kind='outside_outline')]
        for o, g in obstacles:
            rows.append(dict(kind='foreign_or_other_branch_copper', uuid=o['uuid'], key=o.get('key'), net=o['net'], gap_mm=line.distance(g) - .0635, required_mm=.127))
        for o, g, cut in shared_obstacles:
            rows.append(dict(kind='other_branch_outside_shared_pad', uuid=o['uuid'], gap_mm=shape.difference(cut).distance(g), required_mm=.127))
        for o, g in holes:
            if o['net'] == net and not o.get('npth'):
                continue
            rows.append(dict(kind='drill', uuid=o['uuid'], gap_mm=line.distance(g) - .0635, required_mm=.254 if o.get('npth') else .20))
        for z, g in rules:
            rows.append(dict(kind='rule', uuid=z['uuid'], gap_mm=line.distance(g) - .0635, required_mm=0))
        for r in rows:
            r['extra_mm'] = r['gap_mm'] - r['required_mm']
        rows.sort(key=lambda r: r['extra_mm'])
        return rows[0]['extra_mm'] >= 0, rows[:12]

    located_points = located['requested_corners_mm']
    def orientation_score(points):
        return Point(points[0]).distance(Point(source['xy'])) + Point(points[-1]).distance(Point(target['xy']))
    points = list(located_points)
    if orientation_score(points[::-1]) < orientation_score(points):
        points.reverse()
    for o, xy in zip([source, target], [points[0], points[-1]]):
        assert poly(o['inside'][layer]).covers(Point(xy)), 'Located endpoint is not in its claimed native terminal.'
    completed = [source['xy']] + points + [target['xy']]
    completed = [p for i, p in enumerate(completed) if i == 0 or p != completed[i - 1]]
    ok, raw_checks = check(completed)
    assert ok, raw_checks
    simplified = [completed[0]]
    i = 0
    while i < len(completed) - 1:
        for j in range(len(completed) - 1, i, -1):
            if check([completed[i], completed[j]])[0]:
                break
        simplified.append(completed[j])
        i = j
    ok, checks = check(simplified)
    assert ok
    entries = []
    for o in [source, target]:
        point = Point(o['xy'])
        copper = poly(o['inside'][layer])
        depth = point.distance(copper.boundary)
        assert copper.covers(point) and depth >= .0685
        entries.append(dict(pad=o['key'], uuid=o['uuid'], point_mm=o['xy'], full_round_cap_inside_native_pad=True, extra_containment_mm=depth - .0635))
    row = dict(net=net, logical_net=logical, layer=layer, terminals=branch['terminals'], terminal_uuids=[source['uuid'], target['uuid']], different_native_components_before=True, points_mm=simplified, width_mm=.127, vias=[], length_mm=LineString(simplified).length, minimum_extra_clearance_mm=checks[0]['extra_mm'], pad_entry=entries, logical_role=role, native_drc_performed=False, acceptance_claimed=False)
    files = {'f722-heli': a.board, 'f722-heli.native': a.native, 'model': a.model, 'f722-heli.logical-route-map': a.logical_route_map, 'screen': Path(__file__), 'located_receipt': a.located_receipt, 'engine_log': a.engine_log}
    receipt = dict(source_identity={key: dict(path=str(path.resolve()), sha256=sha(path)) for key, path in files.items()}, board_sha256=sha(a.board), source_unchanged=True, proposal_mutual_conflicts=[], proposals=[row], engine_provenance=dict(status='Actual engine located path; insertion failed; explicit native alternative only.', raw_points=located_points, endpoint_completion='Pad centers with full-width containment reserve', simplification='Coordinate-preserving line of sight, checked against actual native copper and permitted shared-pad regions'), shared_pad_obstacle_cuts=shared_receipts, raw_checks=raw_checks, simplified_checks=checks, mandatory_native_gates=['Native DRC/process/strict parity and intended logical ownership', 'Actual shared-pad cut with outside-pad clearance', 'Source geometry and exact power/fill/drill applicability', 'Owner adoption; no engine-success or numerical-power claim'])
    receipt['engine_provenance']['origin_source'] = origin_source
    receipt['engine_provenance']['additional_native_copper_and_drills_rechecked'] = a.continuation_source is not None
    receipt['engine_provenance']['source_model_is_topology_template_only'] = a.continuation_source is not None
    if a.continuation_source is not None:
        receipt['source_identity']['origin_board'] = dict(path=origin_source['board_path'], sha256=origin_source['board_sha256'])
        receipt['source_identity']['origin_native'] = dict(path=origin_source['native_path'], sha256=origin_source['native_sha256'])
        receipt['source_identity']['origin_logical_map'] = dict(path=origin_source['logical_map_path'], sha256=origin_source['logical_map_sha256'])
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps(dict(points=simplified, minimum_extra_clearance_mm=row['minimum_extra_clearance_mm'], length_mm=row['length_mm'])))


if __name__ == '__main__':
    main()
