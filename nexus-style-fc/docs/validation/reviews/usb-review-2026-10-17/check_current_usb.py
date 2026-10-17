"""Read-only native USB topology and endpoint-graph geometric path screen.

Lengths follow track/arc centerlines and straight taper axes. Endpoint
offsets up to 0.005 mm in overlapping copper are joined by straight distance.
Via links have
zero planar length. Pad links use straight center-to-endpoint distance within
the pad. This is not electrical delay, impedance, or an eye-diagram analysis.
"""
import collections
import hashlib
import heapq
import itertools
import json
import math
import sys
from pathlib import Path

import pcbnew as k

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[3]
sys.path.insert(0, str(ROOT/'tools'))
from sexpr import parse, find, text
SRC = ROOT / 'hardware/nexus-style-fc.kicad_pcb'
before = hashlib.sha256(SRC.read_bytes()).hexdigest()
b = k.LoadBoard(str(SRC))
names = ('USB_DP', 'USB_DN')
layers = list(b.GetEnabledLayers().CuStack())
stack = find(find(parse(SRC.read_text()), 'setup')[0], 'stackup')[0]
depth = 0; centers = {}; thicknesses = {}
for item in find(stack, 'layer'):
    name = text(item[1]); thickness = find(item, 'thickness')
    thickness = float(thickness[0][1]) if thickness else 0
    if name.endswith('.Cu'):
        centers[name] = depth + thickness/2; thicknesses[name] = thickness
    if name.endswith('.Cu') or name.startswith('dielectric'):
        depth += thickness
xy = lambda p: (p.x, p.y)
mm = lambda p: [p.x / 1e6, p.y / 1e6]
result = dict(source=str(SRC), sha256=before, native_version=k.GetBuildVersion(),
              mcu=next(f.GetValue() for f in b.GetFootprints() if f.GetReference() == 'U1'),
              method=__doc__, nets={})
for net in names:
    ts = [t for t in b.GetTracks() if t.GetNetname() == net]
    vias = [t for t in ts if isinstance(t, k.PCB_VIA)]
    pads = [(f, p) for f in b.GetFootprints() for p in f.Pads() if p.GetNetname() == net]
    polys = [d for d in b.GetDrawings() if hasattr(d, 'GetNetname') and d.GetNetname() == net]
    graph = collections.defaultdict(list)
    endpoints = set()
    def connect(a, z, length, tag):
        graph[a].append((z, length, tag))
        graph[z].append((a, length, tag))
    counts = collections.defaultdict(float)
    for t in ts:
        if isinstance(t, k.PCB_VIA):
            continue
        a, z = (t.GetLayer(), *xy(t.GetStart())), (t.GetLayer(), *xy(t.GetEnd()))
        connect(a, z, t.GetLength()/1e6, ('track', t.m_Uuid.AsString()))
        endpoints.update([a, z])
        counts[f'{b.GetLayerName(t.GetLayer())} width {t.GetWidth()/1e6:.3f}'] += t.GetLength()/1e6
    for a, z in itertools.combinations(endpoints, 2):
        distance = math.dist(a[1:], z[1:])
        if a[0] == z[0] and 0 < distance <= 5000:
            connect(a, z, distance/1e6, ('overlapping_endpoint_offset', ''))
    for via in vias:
        nodes = [(layer, *xy(via.GetPosition())) for layer in layers if via.IsOnLayer(layer)]
        for a, z in itertools.combinations(nodes, 2):
            connect(a, z, 0, ('via', via.m_Uuid.AsString()))
    for poly in polys:
        shape = poly.GetEffectiveShape(poly.GetLayer())
        hits = [e for e in endpoints if e[0] == poly.GetLayer() and shape.Collide(k.VECTOR2I(e[1], e[2]), 1)]
        assert len(hits) == 2, ('Unexpected taper endpoint count', hits)
        connect(*hits, math.dist(hits[0][1:], hits[1][1:])/1e6, ('taper', poly.m_Uuid.AsString()))
    contacts = []
    for f, pad in pads:
        node = ('pad', f.GetReference(), pad.GetNumber())
        layer = f.GetLayer()
        shape = pad.GetEffectiveShape(layer)
        for endpoint in endpoints:
            if endpoint[0] == layer and shape.Collide(k.VECTOR2I(endpoint[1], endpoint[2]), 1):
                connect(node, endpoint, math.dist(xy(pad.GetPosition()), endpoint[1:])/1e6, ('pad', pad.GetNumber()))
        touching = [t.m_Uuid.AsString() for t in ts if t.IsOnLayer(layer) and
                    shape.Collide(t.GetEffectiveShape(layer), 0)]
        assert touching and graph[node], (net, node, 'missing physical track contact')
        contacts.append(dict(reference=f.GetReference(), pad=pad.GetNumber(), xy_mm=mm(pad.GetPosition()), tracks=touching))
    def shortest(start, end):
        q = [(0, 0, start)]; seq = itertools.count(1); dist = {start: 0}; prev = {}
        while q:
            cost, _, node = heapq.heappop(q)
            if cost != dist[node]:
                continue
            if node == end:
                edges = []
                while node != start:
                    earlier, length, tag = prev[node]
                    edges.append(dict(start=earlier, end=node, length_mm=length, tag=tag))
                    node = earlier
                edges.reverse()
                return dict(planar_centerline_mm=cost,
                            used_vias=len({e['tag'][1] for e in edges if e['tag'][0] == 'via'}), edges=edges)
            for nxt, length, tag in graph[node]:
                candidate = cost + length
                if candidate < dist.get(nxt, math.inf):
                    dist[nxt] = candidate; prev[nxt] = (node, length, tag)
                    heapq.heappush(q, (candidate, next(seq), nxt))
        raise AssertionError(('No endpoint-graph path', start, end))
    pin = '45' if net == 'USB_DP' else '44'
    starts = ('A6', 'B6') if net == 'USB_DP' else ('A7', 'B7')
    paths = {start: shortest(('pad', 'J6', start), ('pad', 'U1', pin)) for start in starts}
    for path in paths.values():
        path['used_barrel_centerline_mm'] = sum(
            abs(centers[b.GetLayerName(edge['start'][0])] - centers[b.GetLayerName(edge['end'][0])])
            for edge in path['edges'] if edge['tag'][0] == 'via')
    input_pin, output_pin = ('3', '4') if net == 'USB_DP' else ('1', '6')
    protection_bridge = shortest(('pad', 'U7', input_pin), ('pad', 'U7', output_pin))
    bridge_tracks = {edge['tag'][1] for edge in protection_bridge['edges'] if edge['tag'][0] == 'track'}
    cut_reachability = {}
    for start in starts:
        reached = {('pad', 'J6', start)}; pending = list(reached)
        while pending:
            for nxt, _, tag in graph[pending.pop()]:
                if tag[0] == 'track' and tag[1] in bridge_tracks:
                    continue
                if nxt not in reached:
                    reached.add(nxt); pending.append(nxt)
        cut_reachability[start] = ('pad', 'U1', pin) in reached
    assert not any(cut_reachability.values()), 'Unexpected physical protection bypass'
    returns = []
    ground_vias = [v for v in b.GetTracks() if isinstance(v, k.PCB_VIA) and v.GetNetname() == 'GND']
    for via in vias:
        nearest = min(ground_vias, key=lambda v: math.dist(xy(v.GetPosition()), xy(via.GetPosition())))
        returns.append(dict(signal_via=via.m_Uuid.AsString(), signal_xy_mm=mm(via.GetPosition()),
                            nearest_gnd_via=nearest.m_Uuid.AsString(), gnd_xy_mm=mm(nearest.GetPosition()),
                            center_distance_mm=math.dist(xy(via.GetPosition()), xy(nearest.GetPosition()))/1e6))
    result['nets'][net] = dict(partner=b.DpCoupledNet(b.FindNet(net)).GetNetname(),
                             track_arc_items=len(ts)-len(vias), via_count=len(vias), taper_count=len(polys),
                             trace_inventory_mm=dict(counts), pad_contacts=contacts,
                             protection_bridge=protection_bridge,
                             reaches_mcu_with_external_bridge_cut=cut_reachability,
                             connector_to_mcu_paths=paths, nearest_ground_vias=returns)
result['orientation_planar_difference_mm'] = {
    label: result['nets']['USB_DP']['connector_to_mcu_paths'][pp]['planar_centerline_mm'] -
           result['nets']['USB_DN']['connector_to_mcu_paths'][pn]['planar_centerline_mm']
    for label, pp, pn in [('A', 'A6', 'A7'), ('B', 'B6', 'B7')]}
result['declared_stack'] = dict(copper_center_z_mm=centers, copper_thickness_mm=thicknesses,
                              copper_dielectric_sum_mm=depth, manufacturer_stack_verified=False)
assert hashlib.sha256(SRC.read_bytes()).hexdigest() == before
(OUT/'current-usb.json').write_text(json.dumps(result, indent=2))
print(json.dumps({key: value for key, value in result.items() if key != 'nets'}, indent=2))
for net in names:
    print(net, {pin: {key: value for key, value in data.items() if key != 'edges'}
                for pin, data in result['nets'][net]['connector_to_mcu_paths'].items()})
