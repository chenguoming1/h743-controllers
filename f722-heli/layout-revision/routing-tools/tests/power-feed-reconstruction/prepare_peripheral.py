"""Retreat tight proposed widths while retaining useful peripheral rail widening."""
import copy, hashlib, json, math
from pathlib import Path
from shapely.geometry import Polygon, LineString
from shapely.ops import unary_union

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
src = ROOT / 'peripheral-feed-plan/proposal.json'
native = ROOT / 'ordinary-routing/candidate16/f722-heli.native.json'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
p = json.loads(src.read_text())
n = json.loads(native.read_text())
assert p['board_sha256'] == n['board_sha256']
poly = lambda ps: unary_union([Polygon(v['outer'], v.get('holes', [])) for v in ps])
raw = [(o, {l: poly(ps) for l, ps in o['copper'].items()}, poly(o['drill']['outside']) if o.get('drill') else None) for o in n['objects'] if o['net'] != '+5V_PERIPH']
outline = poly(n['outline_with_npth']['polygons'])
roles = ['additive_local_output', 'replace_shared_j9_j10', 'replace_j9_branch', 'optional_replace_j11_branch']
out = copy.deepcopy(p)
receipts = []
for role in roles:
    r = out[role]
    changes = []
    for i, s in enumerate(r['segments']):
        line = LineString([s['start'], s['end']])
        copper = sorted((line.distance(gs[r['layer']]), o['uuid']) for o, gs, _ in raw if r['layer'] in gs)
        holes = sorted((line.distance(h), o['uuid']) for o, _, h in raw if h is not None)
        # 0.140 is a bounded nominal planning preference; native rule remains 0.127.
        assert outline.covers(line)
        allowed = min(2 * (copper[0][0] - .140), 2 * (holes[0][0] - .210), 2 * (line.distance(outline.boundary) - .264))
        new_width = min(s['width'], math.floor(allowed * 1000) / 1000)
        assert new_width >= s['width'] - .08, (role, i, new_width, s['width'])
        if new_width < s['width']:
            changes.append(dict(index=i, old_width=s['width'], new_width=new_width))
            s['width'] = new_width
    shape = unary_union([LineString([s['start'], s['end']]).buffer(s['width'] / 2, quad_segs=128) for s in r['segments']])
    copper = sorted((shape.distance(gs[r['layer']]), o['uuid']) for o, gs, _ in raw if r['layer'] in gs)
    holes = sorted((shape.distance(h), o['uuid']) for o, _, h in raw if h is not None)
    edge_gap = shape.distance(outline.boundary)
    assert copper[0][0] >= .140 and holes[0][0] >= .210 and edge_gap >= .264 and outline.covers(shape)
    r['squares'] = sum(math.dist(s['start'], s['end']) / s['width'] for s in r['segments'])
    receipts.append(dict(role=role, changes=changes, squares=r['squares'], min_copper_mm=copper[0][0], nearest_copper_uuid=copper[0][1], min_hole_mm=holes[0][0], nearest_hole_uuid=holes[0][1], min_edge_npth_gap_mm=edge_gap))
out['status'] = 'Geometry planning only; shared trunk may be replaced for coordinated BEC via access; no native or loaded qualification.'
out['planning_preference_copper_mm'] = .140
out['planning_preference_hole_mm'] = .210
out['source_proposal_sha256'] = sha(src)
target = HERE / 'peripheral-margin-proposal.json'
target.write_text(json.dumps(out, indent=2) + '\n')
receipt = dict(board_sha256=n['board_sha256'], native_sha256=sha(native), source_proposal_sha256=sha(src), proposal_sha256=sha(target), source_sha256=sha(Path(__file__)), checks=receipts)
(HERE / 'peripheral-margin-receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
print(json.dumps(receipt))
