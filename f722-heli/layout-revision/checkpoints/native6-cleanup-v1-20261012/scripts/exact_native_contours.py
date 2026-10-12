"""Decode zero-width fracture bridges without moving native integer vertices.

KiCad can store a polygon with holes as one self-touching outline, visiting a
bridge once in each direction. Cancel only exact opposite directed edge pairs.
Ambiguous topology fails closed; no geometric repair, snapping or buffering.
"""
from collections import Counter
import hashlib
import json


def doubled_area(points):
    return sum(a[0] * b[1] - a[1] * b[0]
               for a, b in zip(points, points[1:] + points[:1]))


def decode_fractured_contour(points):
    points = [tuple(v) for v in points]
    if len(points) > 1 and points[0] == points[-1]:
        points = points[:-1]
    if len(points) < 3 or any(not isinstance(c, int) for p in points for c in p):
        raise ValueError('Expected a native integer contour with at least three vertices')
    edges = Counter(zip(points, points[1:] + points[:1]))
    removed = 0
    for a, b in list(edges):
        if a == b:
            removed += edges[a, b]
            edges[a, b] = 0
        elif a < b:
            count = min(edges[a, b], edges[b, a])
            edges[a, b] -= count
            edges[b, a] -= count
            removed += 2 * count
    boundary = {edge: count for edge, count in edges.items() if count}
    outgoing = Counter(a for a, b in boundary)
    incoming = Counter(b for a, b in boundary)
    if any(c != 1 for c in boundary.values()) or outgoing != incoming or any(c != 1 for c in outgoing.values()):
        raise ValueError('Native contour is not an unambiguous set of exact bridge-separated cycles')
    successor = {a: b for a, b in boundary}
    cycles = []
    while successor:
        start = next(iter(successor))
        current = start
        cycle = []
        while True:
            cycle.append(current)
            current = successor.pop(current)
            if current == start:
                break
        if len(cycle) < 3 or doubled_area(cycle) == 0:
            raise ValueError('Native boundary contains a degenerate non-bridge cycle')
        cycles.append(cycle)
    cycles.sort(key=lambda c: abs(doubled_area(c)), reverse=True)
    if not cycles:
        raise ValueError('Native contour has no nonzero-area exterior')
    exterior, holes = cycles[0], cycles[1:]
    sign = doubled_area(exterior) > 0
    if any((doubled_area(h) > 0) == sign for h in holes):
        raise ValueError('Native contour contains multiple exterior cycles; explicit topology review required')
    before = doubled_area(points)
    after = sum(doubled_area(c) for c in cycles)
    if before != after:
        raise AssertionError('Integer native area changed during contour decoding')
    decoded_edges = Counter(edge for c in cycles for edge in zip(c, c[1:] + c[:1]))
    if decoded_edges != Counter(boundary):
        raise AssertionError('Native boundary edge identity changed during contour decoding')
    return {'outer': exterior, 'holes': holes}, {
        'method': 'exact_opposite_integer_edge_cancellation',
        'input_sha256': hashlib.sha256(json.dumps(points, separators=(',', ':')).encode()).hexdigest(),
        'input_vertices': len(points),
        'output_vertices': sum(map(len, cycles)),
        'removed_zero_area_directed_edges': removed,
        'holes_recovered': len(holes),
        'doubled_area_before_nm2': before,
        'doubled_area_after_nm2': after,
        'boundary_edges_preserved_exactly': True,
        'maximum_coordinate_displacement_nm': 0,
    }


def native_filled_polygons(poly_set):
    polygons, receipts = [], []
    for index in range(poly_set.OutlineCount()):
        outline = poly_set.Outline(index)
        points = [(outline.CPoint(j).x, outline.CPoint(j).y) for j in range(outline.PointCount())]
        decoded, receipt = decode_fractured_contour(points)
        for hole_index in range(poly_set.HoleCount(index)):
            hole = poly_set.Hole(index, hole_index)
            decoded['holes'].append([(hole.CPoint(j).x, hole.CPoint(j).y) for j in range(hole.PointCount())])
        def mm(contour):
            return [[x / 1e6, y / 1e6] for x, y in contour]
        polygons.append({'outer': mm(decoded['outer']), 'holes': [mm(h) for h in decoded['holes']]})
        receipt['native_explicit_holes'] = poly_set.HoleCount(index)
        receipts.append(receipt)
    return polygons, receipts
