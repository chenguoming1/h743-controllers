"""Verify full-width annular entries where new tracks end on existing vias."""
import argparse
import hashlib
import json
from pathlib import Path
from shapely.geometry import Point
from audit_native_endpoints import geom, annular_sections

ap = argparse.ArgumentParser(description=__doc__)
for name in ['source', 'candidate', 'out']:
    ap.add_argument('--' + name, type=Path, required=True)
a = ap.parse_args()
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
before = json.loads((a.source / 'f722-heli.native.json').read_text())
after = json.loads((a.candidate / 'f722-heli.native.json').read_text())
assert before['board_sha256'] == sha(a.source / 'f722-heli.kicad_pcb')
assert after['board_sha256'] == sha(a.candidate / 'f722-heli.kicad_pcb')
prior = {o['uuid']: o for o in before['objects']}
current = {o['uuid']: o for o in after['objects']}
assert all(current.get(uid) == o for uid, o in prior.items())
vias = [o for o in before['objects'] if o['kind'] == 'via']
tracks = [o for uid, o in current.items() if uid not in prior and o['kind'] == 'track']
rows = []
error = after['maximum_polygon_error_mm']
for track in tracks:
    for layer in track['copper']:
        for endpoint in ['start', 'end']:
            point = Point(track[endpoint])
            for via in vias:
                if via['net'] != track['net'] or layer not in via['copper']:
                    continue
                outside = geom(via['copper'][layer])
                if outside.distance(point) > track['width'] / 2 + error:
                    continue
                actual = outside.buffer(-error).difference(geom(via['drill']['outside']))
                witnesses, length = annular_sections(track, actual, error)
                rows.append(dict(net=track['net'], track_uuid=track['uuid'], layer=layer,
                                 endpoint=endpoint, xy_mm=track[endpoint], via_uuid=via['uuid'],
                                 via_xy_mm=via['xy'], existing_via_unchanged=True,
                                 drill_void_subtracted=True, outer_inward_reserve_mm=error,
                                 full_width_annular_witnesses=witnesses,
                                 centerline_actual_annulus_length_mm=length,
                                 passed=bool(witnesses)))
result = dict(schema='f722-new-track-existing-via-entry/v1',
              source_board_sha256=before['board_sha256'],
              board_sha256=after['board_sha256'],
              audit_source_sha256=sha(__file__),
              annular_helper_sha256=sha(Path(__file__).with_name('audit_native_endpoints.py')),
              existing_via_endpoint_count=len(rows), contacts=rows,
              passed=all(r['passed'] for r in rows),
              scope='New track endpoints touching preserved existing vias only. New vias and pads use the separate full endpoint audit; connectivity and DRC remain mandatory.')
a.out.write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps({k: v for k, v in result.items() if k != 'contacts'}))
raise SystemExit(0 if result['passed'] else 1)
