"""Exact immutable proposed native11 geometry, with no speculative transaction overlays."""
import hashlib
import json
import math
import sys
from pathlib import Path

H = Path(__file__).resolve().parent
ROOT = H.parents[1]
sys.path.insert(0, str(ROOT / 'tests/flash-candidate43-structural'))
import native44_geometry as s
from shapely.geometry import LineString, Point

SOURCE = H.parent / 'boot56/candidate01/f722-heli.native.json'
BOARD = SOURCE.with_name('f722-heli.kicad_pcb')
EXPECTED = '454b7bb2454695b49c039f3d97e5edefb1946912363bab00ef5ced6ba2b0ea16'
N = json.loads(SOURCE.read_text())
assert hashlib.sha256(BOARD.read_bytes()).hexdigest() == N['board_sha256'] == EXPECTED


def entry(o):
    return (o, {l: s.geom(ps) for l, ps in o['copper'].items()},
            {l: s.geom(m['polygons']) for l, m in o.get('mask', {}).items()}
            if o.get('smd') else {},
            s.geom(o['drill']['outside']) if o.get('drill') else None)


def track(net, layer, points, name, width=.127):
    return (dict(uuid=name, net=net, kind='track', width=width,
                 start=points[0], end=points[-1]),
            {layer: LineString(points).buffer(width / 2 / math.cos(math.pi / 512),
                                               quad_segs=128)}, {}, None)


def via(net, xy, name):
    return (dict(uuid=name, net=net, kind='via', xy=xy, width=.45,
                 barrel_layers=N['copper_layers']),
            {l: Point(xy).buffer(.225 / math.cos(math.pi / 512), quad_segs=128)
             for l in N['copper_layers']}, {},
            Point(xy).buffer(.1 / math.cos(math.pi / 512), quad_segs=128))


BASE = [entry(o) for o in N['objects']]
by = {o['uuid']: o for o in N['objects']}
pads = {}
for o in N['objects']:
    if o['kind'] == 'pad':
        pads.setdefault(o['key'], []).append(o)
s.N = N
s.SOURCE = SOURCE
s.BOARD = BOARD
s.EXPECTED = EXPECTED
s.ERROR = N['maximum_polygon_error_mm']
s.OUTLINE = s.geom(N['outline_with_npth']['polygons'])
s.OBJECTS = BASE
s.HALF = .0635
assert len(by) == len(BASE)
REMOVED_NATIVE_IDS = set()


def one_pad(key):
    rows = pads[key]
    assert len(rows) == 1, (key, len(rows))
    return rows[0]


def binding():
    return dict(board_sha256=EXPECTED,
                native_file=str(SOURCE.relative_to(ROOT)),
                native_sha256=hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
                context_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                geometry_helper_sha256=hashlib.sha256(Path(s.__file__).read_bytes()).hexdigest(),
                foreign_drill_to_track_copper_gap_mm=.20,
                all_native_objects_retained=True, speculative_overlays=[])
