"""Audit the finite full-width departure of one branch at a shared SMD pad."""
import argparse
import hashlib
import json
import math
from pathlib import Path
from shapely.affinity import translate
from shapely.geometry import Point, LineString
from audit_native_endpoints import geom, section_at

ap = argparse.ArgumentParser(description=__doc__)
ap.add_argument('--candidate', type=Path, required=True)
ap.add_argument('--pad', required=True)
ap.add_argument('--logical-net', required=True)
ap.add_argument('--out', type=Path, required=True)
a = ap.parse_args()
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
n = json.loads((a.candidate / 'f722-heli.native.json').read_text())
lm = json.loads((a.candidate / 'f722-heli.logical-route-map.json').read_text())
assert n['board_sha256'] == lm['board_sha256'] == sha(a.candidate / 'f722-heli.kicad_pcb')
pads = [o for o in n['objects'] if o.get('key') == a.pad]
assert len(pads) == 1 and pads[0]['smd'] and not pads[0]['drill']
pad = pads[0]
tracks = [o for o in n['objects'] if lm['logical_route_map'].get(o['uuid']) == a.logical_net
          and o['kind'] == 'track' and pad['xy'] in [o['start'], o['end']]]
assert len(tracks) == 1
t = tracks[0]
assert t['net'] == pad['net'] and len(t['copper']) == 1 and t['width'] == .127
layer = next(iter(t['copper']))
p = geom(pad['inside'][layer])
x, y = (t['start'], t['end']) if t['start'] == pad['xy'] else (t['end'], t['start'])
length = math.dist(x, y)
normal = [-(y[1] - x[1]) / length, (y[0] - x[0]) / length]
half = t['width'] / 2
section = section_at(x, normal, half)
guarded = p.buffer(-.000001)
allowed = translate(guarded, normal[0] * half, normal[1] * half).intersection(
    translate(guarded, -normal[0] * half, -normal[1] * half))
entry = LineString([x, y]).intersection(allowed)
assert p.contains(Point(x)) and section.difference(p).length <= 1e-8 and entry.length > 0
out = dict(passed=True, board_sha256=n['board_sha256'],
           native_sha256=sha(a.candidate / 'f722-heli.native.json'),
           audit_source_sha256=sha(__file__),
           geometry_helper_sha256=sha(Path(__file__).with_name('audit_native_endpoints.py')),
           pad=a.pad, pad_uuid=pad['uuid'], logical_net=a.logical_net,
           track_uuid=t['uuid'], layer=layer, endpoint_mm=x,
           actual_full_width_section_mm=list(section.coords),
           full_width_transverse_entry_length_mm=entry.length,
           full_width_transverse_entry_wkt=entry.wkt,
           endpoint_depth_mm=Point(x).distance(p.boundary),
           full_round_cap_containment_reserve_mm=Point(x).distance(p.boundary) - half,
           physical_source_pad_shape_sha256=hashlib.sha256(json.dumps(pad, sort_keys=True).encode()).hexdigest(),
           scope='Explicit shared-pad departure, supplementing the degree-one termination audit. The complete actual-pad cut and outside-pad gap remain separate mandatory gates.')
a.out.write_text(json.dumps(out, indent=2) + '\n')
print(json.dumps(out))
