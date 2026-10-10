#!/usr/bin/env python3
"""Conservative physical pad-cut checks using a read-only native geometry export.

Requires Shapely 2.x. Copper is ERROR_OUTSIDE; cuts are ERROR_INSIDE at 10 nm
maximum error. Pieces are rebuilt after subtraction. A pad number is a label,
not a conductive edge; only native physical contact and real plated barrels
connect layers. The report is scoped geometry evidence, not ESD qualification.
"""
import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path
from shapely.geometry import Polygon, GeometryCollection
from shapely.ops import unary_union, nearest_points
from shapely.strtree import STRtree

NUMERIC_EPS_MM = 1e-9  # Floating-point robustness only; 1000 times below 1 nm CAD IU.


def geometry(data):
    polys = [Polygon(x['outer'], x.get('holes', [])) for x in data if len(x['outer']) >= 3]
    for g in polys:
        if not g.is_valid:
            raise ValueError('Invalid native polygon; no silent repair is permitted')
    return unary_union(polys) if polys else GeometryCollection()


def pieces(g):
    if g.is_empty:
        return []
    if g.geom_type == 'Polygon':
        return [g]
    if hasattr(g, 'geoms'):
        return [p for part in g.geoms for p in pieces(part)]
    return []


class DSU:
    def __init__(self, n):
        self.parent = list(range(n))
    def find(self, x):
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]
        return x
    def join(self, x, y):
        x, y = self.find(x), self.find(y)
        if x != y:
            self.parent[y] = x


def make_graph(objects, cuts=None):
    cuts = cuts or {}
    nodes = []
    by_layer = defaultdict(list)
    plated = defaultdict(list)
    for obj in objects:
        for layer, raw in obj['copper'].items():
            g = geometry(raw)
            # Native copper envelope includes the drill void. Remove only an
            # ERROR_INSIDE void so surviving copper remains an overestimate.
            hole = geometry(obj['drill']['inside']) if obj.get('drill') else None
            if hole is not None:
                g = g.difference(hole)
            if layer in cuts:
                g = g.difference(cuts[layer])
            for part in pieces(g):
                idx = len(nodes)
                nodes.append({'object': obj, 'layer': layer, 'geometry': part})
                by_layer[layer].append(idx)
                # A layer contributes to a plated barrel only where the
                # surviving copper reaches the actual drill boundary.
                if obj.get('plated') and hole is not None and layer in obj.get('barrel_layers', []):
                    if part.distance(hole.boundary) <= NUMERIC_EPS_MM:
                        plated[obj['uuid']].append(idx)
    dsu = DSU(len(nodes))
    for indices in by_layer.values():
        geoms = [nodes[i]['geometry'] for i in indices]
        tree = STRtree(geoms)
        for local_i, g in enumerate(geoms):
            for local_j in tree.query(g, predicate='dwithin', distance=NUMERIC_EPS_MM):
                if local_j > local_i:
                    dsu.join(indices[local_i], indices[local_j])
    for indices in plated.values():
        for i in indices[1:]:
            dsu.join(indices[0], i)
    groups = defaultdict(list)
    for i, node in enumerate(nodes):
        groups[dsu.find(i)].append(node)
    return list(groups.values())


def groups_for_key(groups, key):
    return {i for i, group in enumerate(groups) if any(n['object'].get('key') == key for n in group)}


def pad_groups(groups):
    result = []
    for group in groups:
        keys = sorted({n['object']['key'] for n in group if n['object']['kind'] == 'pad'})
        if keys:
            result.append(keys)
    return sorted(result)


def group_geometry(groups, ids, layer):
    return unary_union([n['geometry'] for i in ids for n in groups[i] if n['layer'] == layer])


def run_check(snapshot, contract):
    net, clamp, source, target = [contract[k] for k in ['net', 'clamp', 'source', 'target']]
    result = dict(contract)
    objects = [x for x in snapshot['objects'] if x['net'] == net]
    pad_objects = [x for x in objects if x['kind'] == 'pad']
    found = {key: [x for x in pad_objects if x['key'] == key] for key in [clamp, source, target]}
    missing = [key for key, values in found.items() if not values]
    if missing:
        return dict(result, error='missing_or_wrong_net_endpoint', missing=missing, complete_clamp_first_path_passes=False)
    if len(found[clamp]) != 1:
        return dict(result, error='ambiguous_physical_clamp_pad', complete_clamp_first_path_passes=False)
    actual = found[clamp][0]
    if actual.get('plated'):
        return dict(result, error='plated_clamp_cut_not_supported', complete_clamp_first_path_passes=False)
    cuts = {layer: geometry(poly) for layer, poly in actual['inside'].items()}
    zone_nets = [z['uuid'] for z in snapshot['zones'] if not z['rule'] and z['net'] == net]
    if zone_nets:
        return dict(result, error='signal_net_zones_require_additional_validation', zone_uuids=zone_nets,
                    complete_clamp_first_path_passes=False)
    # The chosen contracts remove SMT pads only. A cut intersecting a drilled
    # barrel would require a 3D barrel-cut model and is rejected explicitly.
    for obj in objects:
        if obj.get('plated') and obj.get('drill'):
            h = geometry(obj['drill']['outside'])
            if any(layer in obj['copper'] and cut.intersects(h) for layer, cut in cuts.items()):
                return dict(result, error='cut_intersects_plated_barrel', object_uuid=obj['uuid'],
                            complete_clamp_first_path_passes=False)
    before = make_graph(objects)
    bs, bt, bc = [groups_for_key(before, key) for key in [source, target, clamp]]
    connected = bool(bs & bt)
    reaches_source = bool(bs & bc)
    reaches_target = bool(bt & bc)
    # Remove the physical clamp pad object entirely. ERROR_OUTSIDE and
    # ERROR_INSIDE are different approximations of that same object; retaining
    # their subtraction would fabricate tiny curved-corner copper remnants.
    # The conservative ERROR_INSIDE cut still applies to every OTHER object.
    after = make_graph([x for x in objects if x['uuid'] != actual['uuid']], cuts)
    gs, gt = [groups_for_key(after, key) for key in [source, target]]
    separated = bool(gs and gt and not (gs & gt))
    hits = []
    for ids in [gs, gt]:
        hits.append(any(group_geometry(after, ids, layer).distance(cut.boundary) <= NUMERIC_EPS_MM
                        for layer, cut in cuts.items() if not group_geometry(after, ids, layer).is_empty))
    gaps = []
    for layer in snapshot['copper_layers']:
        left, right = [group_geometry(after, ids, layer) for ids in [gs, gt]]
        gap = None if left.is_empty or right.is_empty else left.distance(right)
        points = None if gap is None else [list(pt.coords[0]) for pt in nearest_points(left, right)]
        gaps.append({'layer': layer, 'gap_outside_actual_pad_mm': gap,
                     'overlap_outside_actual_pad_mm2': 0 if gap is None else left.intersection(right).area,
                     'closest_points_mm': points})
    numbers = [g['gap_outside_actual_pad_mm'] for g in gaps if g['gap_outside_actual_pad_mm'] is not None]
    min_gap = min(numbers) if numbers else None
    gap_ok = min_gap is not None and min_gap + NUMERIC_EPS_MM >= contract['minimum_gap_required_mm']
    requires_pad = connected and reaches_source and reaches_target and separated and all(hits)
    result.update(before_cut={'groups': pad_groups(before), 'source_target_connected': connected,
                              'source_reaches_clamp': reaches_source, 'target_reaches_clamp': reaches_target},
                  after_cut_pad_groups=pad_groups(after),
                  source_target_physically_disconnected_after_removing_actual_pad_copper=separated,
                  source_group_reaches_actual_pad_boundary=hits[0], target_group_reaches_actual_pad_boundary=hits[1],
                  all_connections_require_actual_pad_region=requires_pad,
                  gap_requirement_passes=gap_ok, minimum_gap_measured_mm=min_gap,
                  complete_clamp_first_path_passes=requires_pad and gap_ok, layer_gaps=gaps,
                  source_objects=sorted({n['object']['uuid'] for i in gs for n in after[i]}),
                  target_objects=sorted({n['object']['uuid'] for i in gt for n in after[i]}))
    return result


def check_snapshot(snapshot, contracts):
    if snapshot['schema'] != 'kicad-native-copper/v1' or snapshot['maximum_polygon_error_mm'] > 0.00001:
        raise ValueError('Unsupported or insufficiently precise native geometry')
    if snapshot['copper_error_location'] != 'ERROR_OUTSIDE' or snapshot['pad_cut_error_location'] != 'ERROR_INSIDE':
        raise ValueError('Required conservative approximation directions are absent')
    checks = [run_check(snapshot, c) for c in contracts['checks']]
    return {'schema': 'f722-physical-protection-checks/v1', 'board_sha256': snapshot['board_sha256'],
            'native_version': snapshot['native_version'], 'method': contracts['method'],
            'numeric_contact_epsilon_mm': NUMERIC_EPS_MM, 'profile': contracts['profile'],
            'source_unchanged': snapshot.get('source_unchanged', False), 'checks': checks,
            'passed': sum(c['complete_clamp_first_path_passes'] for c in checks), 'total': len(checks),
            'all_pass': all(c['complete_clamp_first_path_passes'] for c in checks)}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--geometry', type=Path, required=True)
    ap.add_argument('--contracts', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    a = ap.parse_args()
    result = check_snapshot(json.loads(a.geometry.read_text()), json.loads(a.contracts.read_text()))
    result['geometry_sha256'] = hashlib.sha256(a.geometry.read_bytes()).hexdigest()
    result['contracts_sha256'] = hashlib.sha256(a.contracts.read_bytes()).hexdigest()
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: result[k] for k in ['board_sha256', 'profile', 'passed', 'total', 'all_pass']}))
    raise SystemExit(0 if result['all_pass'] else 1)


if __name__ == '__main__':
    main()
