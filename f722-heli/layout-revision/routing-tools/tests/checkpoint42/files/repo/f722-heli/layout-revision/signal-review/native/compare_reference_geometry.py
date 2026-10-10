#!/usr/bin/env python3
"""Compare two source-bound critical reference reports and saved-fill geometry."""
import argparse
import json
from pathlib import Path
from shapely.ops import unary_union, nearest_points
from check_signal_geometry import CRITICAL, I2C, copper_entries, poly, sha, validate_bindings
from check_critical_reference import REFERENCE, PLANES, ground_geometry


def load(snapshot, board):
    gp, mp, rp = [snapshot / x for x in ['native-geometry.json', 'native-signals.json', 'critical-reference.json']]
    g, m, r = [json.loads(x.read_text()) for x in [gp, mp, rp]]
    validate_bindings(g, m, sha(gp), sha(board))
    if r['board_sha256'] != m['board_sha256'] or r['sources']['native-geometry.json'] != sha(gp) or r['sources']['native-signals.json'] != sha(mp):
        raise ValueError('Report source binding mismatch')
    return g, m, r


def compare(before, after):
    bg, bm, br = before; ag, am, ar = after
    _, _, bgnd, _ = ground_geometry(bg, copper_entries(bg))
    _, _, agnd, _ = ground_geometry(ag, copper_entries(ag))
    nets = list(I2C) + CRITICAL
    bs = {x['uuid']: x for x in bg['objects'] if x['net'] in nets}
    ass = {x['uuid']: x for x in ag['objects'] if x['net'] in nets}
    numeric = ['native_planar_length_mm', 'physical_GND_centerline_missing_mm', 'physical_GND_trace_width_missing_mm2']
    delta = {n: {k: ar['nets'][n][k] - br['nets'][n][k] for k in numeric} for n in nets}
    planes = {}
    for l in PLANES:
        lost, gained = bgnd[l].difference(agnd[l]), agnd[l].difference(bgnd[l])
        traces = {}
        for n in CRITICAL:
            cu = unary_union([poly(o['copper'][layer]) for o in ag['objects'] if o['net'] == n and o['kind'] in ['track', 'arc']
                              for layer in o['copper'] if REFERENCE.get(layer) == l])
            traces[n] = {'lost_GND_overlap_with_trace_width_mm2': cu.intersection(lost).area,
                         'minimum_trace_width_distance_to_lost_GND_mm': cu.distance(lost) if not cu.is_empty and not lost.is_empty else None,
                         'closest_trace_and_lost_GND_points_mm': [list(p.coords[0]) for p in nearest_points(cu, lost)] if not cu.is_empty and not lost.is_empty else None}
        planes[l] = {'physical_GND_lost_mm2': lost.area, 'physical_GND_gained_mm2': gained.area,
                     'lost_bounds_mm': list(lost.bounds) if not lost.is_empty else None, 'critical_trace_proximity': traces}
    ids = {x['uuid'] for x in bg['objects']}
    added = [{k: v for k, v in o.items() if k in ['uuid','kind','net','xy','start','end','width','barrel_layers']} for o in ag['objects'] if o['uuid'] not in ids]
    return {'schema':'f722-critical-reference-comparison/v1', 'before_board_sha256': bm['board_sha256'],
            'after_board_sha256': am['board_sha256'], 'critical_object_geometry_identical': bs == ass,
            'critical_object_differences': sorted(k for k in bs.keys() | ass.keys() if bs.get(k) != ass.get(k)),
            'net_numeric_deltas_after_minus_before': delta, 'ground_fill_changes': planes, 'added_native_objects': added,
            'limits': 'Actual saved geometry comparison, with native drill subtraction. Small changes are retained without pass thresholds; this does not establish impedance, timing or AC behavior.'}


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    for name in ['before', 'after', 'before-board', 'after-board', 'out']:
        ap.add_argument('--'+name, type=Path, required=True)
    a=ap.parse_args()
    r=compare(load(a.before,a.before_board), load(a.after,a.after_board))
    r['sources']={'compare_reference_geometry.py':sha(__file__),
                  'before_report':sha(a.before/'critical-reference.json'), 'after_report':sha(a.after/'critical-reference.json')}
    a.out.write_text(json.dumps(r,indent=2)+'\n')
    print(json.dumps(r,indent=2))

if __name__ == '__main__': main()
