#!/usr/bin/env python3
"""Read-only source/terminal check and analytic series-copper lower bound. No FEM."""
import argparse
import hashlib
import json
import math
from collections import defaultdict, deque
from pathlib import Path
import shapely
from shapely.geometry import Polygon


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def poly(records):
    return shapely.union_all([Polygon(r['outer'], r.get('holes', [])) for r in records])

def pieces(geometry):
    if geometry.is_empty:
        return []
    if geometry.geom_type == 'Polygon':
        return [geometry]
    return [part for child in geometry.geoms for part in pieces(child)]

def run():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ['native','board','ledger','out']:
        parser.add_argument('--'+name,type=Path,required=True)
    args=parser.parse_args()
    expected=json.loads((Path(__file__).resolve().parents[1]/'receipts/independent-checks.original.json').read_text())
    for name in ['native','board','ledger']:
        assert sha(getattr(args,name)) == expected[name+'_sha256'], 'External source hash mismatch: '+name
    g=json.loads(args.native.read_text())
    ledger=json.loads(args.ledger.read_text())
    assert g['board_sha256']==sha(args.board) and g['source_unchanged']
    net = '+5V_BEC'
    objects = [o for o in g['objects'] if o.get('net') == net]
    outline = poly(g['outline_with_npth']['polygons'])
    domains = {}
    for layer in g['copper_layers']:
        copper = [poly(o['copper'].get(layer, [])) for o in objects]
        copper += [poly(z['filled'].get(layer, [])) for z in g['zones'] if z['net'] == net and not z['rule']]
        drills = [poly(o['drill']['outside']) for o in g['objects'] if o.get('drill') and layer in (o['barrel_layers'] if o['kind'] == 'via' else g['copper_layers'])]
        domains[layer] = shapely.union_all(copper).difference(shapely.union_all(drills)).intersection(outline)
    barrels = [o for o in objects if o.get('plated') and o.get('drill')]
    contact_specs = next(n for n in ledger['networks'] if n['net'] == net)['contacts']
    contacts = {}
    for name, spec in contact_specs.items():
        contact = shapely.union_all([poly(o.get('inside', o['copper']).get(spec['layer'], [])) for o in objects if o.get('key') in spec['pads']])
        contacts[name] = (spec['layer'], contact)

    def connected(current_domains):
        components = {layer: pieces(domain) for layer, domain in current_domains.items()}
        def hits(layer, land):
            return [(layer, i) for i, part in enumerate(components[layer]) if part.intersection(land).area > 0]
        adjacency = defaultdict(set)
        for barrel in barrels:
            previous = None
            for layer in barrel['barrel_layers']:
                land = poly(barrel['copper'].get(layer, [])).difference(poly(barrel['drill']['outside']))
                found = hits(layer, land)
                assert len(found) == 1, (barrel['uuid'], layer, found)
                node = found[0]
                if previous is not None:
                    adjacency[previous].add(node)
                    adjacency[node].add(previous)
                previous = node
        source = hits(*contacts['U6.OUT_7_8'])
        target = hits(*contacts['U7.3'])
        assert len(source) == len(target) == 1
        queue, seen = deque(source), set(source)
        while queue:
            node = queue.popleft()
            for other in adjacency[node] - seen:
                seen.add(other)
                queue.append(other)
        return target[0] in seen

    assert connected(domains)
    rho = 2.4210901105263158e-5
    thickness = 0.015
    trim = 1.0
    width_bound = 0.60004  # Native export allowance; verify every slab against it.
    accepted, rejected, windows, inventory = [], [], [], defaultdict(float)
    for o in objects:
        if o['kind'] != 'track':
            continue
        layer = next(iter(o['copper']))
        length = math.dist(o['start'], o['end'])
        inventory[(layer, o['width'])] += length
        if layer not in ['In2.Cu', 'In3.Cu'] or o['width'] != 0.6 or length <= 2 * trim:
            continue
        a, b = o['start'], o['end']
        ux, uy = (b[0] - a[0]) / length, (b[1] - a[1]) / length
        def rectangle(half_width):
            return Polygon([(a[0] + t * ux + q * -uy, a[1] + t * uy + q * ux) for t, q in [(trim, -half_width), (length-trim, -half_width), (length-trim, half_width), (trim, half_width)]])
        window = rectangle(1.0)
        narrow = rectangle(width_bound/2)
        copper = domains[layer].intersection(window)
        reasons = []
        if copper.difference(narrow).area > 1e-12:
            reasons.append('extra copper outside bounded width')
        if any(window.intersects(poly(v['copper'].get(layer, []))) for v in barrels):
            reasons.append('barrel in slab')
        if any(layer == other_layer and window.intersection(other).area > 1e-12 for other_layer, other in windows):
            reasons.append('slabs overlap')
        if not reasons:
            cut = dict(domains)
            cut[layer] = domains[layer].difference(window)
            if connected(cut):
                reasons.append('independent bypass exists')
        row = {'uuid': o['uuid'], 'layer': layer, 'native_start_mm': a, 'native_end_mm': b, 'native_length_mm': length, 'trim_each_end_mm': trim}
        if reasons:
            rejected.append({**row, 'reasons': reasons})
        else:
            slab_length = length - 2*trim
            accepted.append({**row, 'mandatory_slab_length_mm': slab_length, 'width_upper_bound_mm': width_bound, 'resistance_lower_bound_ohm': rho*slab_length/(thickness*width_bound)})
            windows.append((layer, window))
    resistance = sum(r['resistance_lower_bound_ohm'] for r in accepted)
    result = {
        'schema': 'f722-independent-analytic-power-review/v1',
        'board_sha256': sha(args.board), 'native_sha256': sha(args.native), 'ledger_sha256': sha(args.ledger),
        'script_sha256': sha(Path(__file__)),
        'method': 'Reconstruct exact native per-layer copper and fills minus all drills and outline. Cut mutually disjoint uniform-width interior slabs; independently rebuild finite connected copper components and plated barrel graph after each cut. Include a slab only if it disconnects U6.OUT_7_8 from U7.3, contains no barrel and all its copper lies within the stated width bound. Rayleigh/Cauchy-Schwarz energy bound: with at least 2 A through every accepted slab, total series R is at least sum(rho*L/(t*w_max)). Ends, bends, all other copper, contact and barrel losses are omitted, so the result is a conservative lower bound for the frozen uniform-material model, not a discretization estimate.',
        'material': {'rho_ohm_mm': rho, 'thickness_mm': thickness, 'temperature_C':105, 'conductivity_IACS':0.95, 'measured':False},
        'track_inventory': [{'layer': k[0], 'width_mm': k[1], 'summed_centerline_length_mm': v, 'naive_series_resistance_ohm':rho*v/(thickness*k[1])} for k,v in sorted(inventory.items())],
        'accepted_mandatory_slabs': accepted, 'excluded_slabs': rejected,
        'bound': {'slab_count':len(accepted), 'summed_slab_length_mm':sum(x['mandatory_slab_length_mm'] for x in accepted), 'series_resistance_lower_bound_ohm':resistance, 'current_A':2.0, 'copper_drop_lower_bound_V':2*resistance, 'copper_loss_lower_bound_W':4*resistance},
        'contact_regions': {name:{'layer':layer,'area_mm2':shape.area,'geometry_type':shape.geom_type,'bounds_mm':shape.bounds} for name,(layer,shape) in contacts.items()},
        'no_board_mutations':True, 'no_FEM_or_electrical_solver':True,
    }
    for key in ['bound','track_inventory','accepted_mandatory_slabs','excluded_slabs','contact_regions']:
        assert json.loads(json.dumps(result[key])) == expected[key], 'Reproduction differs from original: '+key
    result['portable_projection']={'original_receipt_sha256':sha(Path(__file__).resolve().parents[1]/'receipts/independent-checks.original.json'), 'exact_numeric_and_geometry_reproduction':True}
    output = args.out
    output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'output':str(output),'sha256':sha(output),'bound':result['bound'],'excluded_slabs':len(rejected)},indent=2))

if __name__ == '__main__':
    run()
