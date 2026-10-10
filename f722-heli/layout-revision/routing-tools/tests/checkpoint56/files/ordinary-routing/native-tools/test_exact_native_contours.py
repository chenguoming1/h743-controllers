"""Coordinate-exact fractured-fill controls; no KiCad installation required."""
import json
from pathlib import Path
from exact_native_contours import decode_fractured_contour, doubled_area

def check_fixture():
    scale = 1000000
    outer = [(0, 0), (10, 0), (10, 10), (0, 10)]
    holes = [[(2, 2), (2, 4), (4, 4), (4, 2)],
             [(6, 6), (6, 8), (8, 8), (8, 6)]]
    # Exact zero-width bridge from the same exterior vertex to each hole.
    fractured = [outer[0]]
    for hole in holes:
        fractured += hole + [hole[0], outer[0]]
    fractured += outer[1:]
    fractured = [(x * scale, y * scale) for x, y in fractured]
    decoded, proof = decode_fractured_contour(fractured)
    assert len(decoded['holes']) == 2
    assert proof['removed_zero_area_directed_edges'] == 4
    assert proof['doubled_area_before_nm2'] == 184 * scale * scale
    assert proof['doubled_area_before_nm2'] == proof['doubled_area_after_nm2']
    assert set(decoded['outer']) == {(x * scale, y * scale) for x, y in outer}
    assert {frozenset(h) for h in decoded['holes']} == {frozenset((x * scale, y * scale) for x, y in h) for h in holes}
    # A separate ordinary outline stays independent and coordinate-identical.
    island = [(20 * scale, 0), (21 * scale, 0), (21 * scale, scale), (20 * scale, scale)]
    unchanged, island_proof = decode_fractured_contour(island)
    assert unchanged['outer'] == island and not unchanged['holes']
    assert island_proof['removed_zero_area_directed_edges'] == 0
    # Two loops sharing one vertex are ambiguous; they are not fracture bridges.
    ambiguous = [(0, 0), (3, 0), (3, 3), (0, 0), (-3, 0), (-3, -3)]
    try:
        decode_fractured_contour(ambiguous)
    except ValueError:
        pass
    else:
        raise AssertionError('Touching cycles were guessed instead of rejected')
    return {'passed': True, 'synthetic_fractured_contour_nm': fractured,
            'synthetic_disconnected_outline_nm': island, 'proof': proof,
            'ambiguous_touching_cycles_rejected': True,
            'disconnected_outline_preserved': True}

if __name__ == '__main__':
    print(json.dumps(check_fixture(), indent=2))
