"""Bind an explicitly reviewed own-window classification without strengthening it.

This does not compute geometry or turn unresolved actual-hole predicates into passes.
The source-bound classifier and its independent owner review remain mandatory.
"""
from pathlib import Path
import hashlib
import json


def verify(path, before_sha, after_sha, comparison, root):
    def require(value, message):
        if not value:
            raise ValueError(message)

    def sha(p):
        return hashlib.sha256(Path(p).read_bytes()).hexdigest()

    rr = json.loads(Path(path).read_text())
    require(rr['before_board_sha256'] == before_sha, 'Wrong before board')
    require(rr['after_board_sha256'] == after_sha, 'Wrong after board')
    for key in ('source_binding_verified', 'critical_copper_identical',
                'unchanged_critical_own_via_windows_verified',
                'all_changed_critical_projection_geometry_inside_unchanged_own_windows',
                'all_changed_critical_projection_residuals_outside_unchanged_own_windows_empty'):
        require(rr[key] is True, 'Reference classification failed: ' + key)
    root = Path(root).resolve()
    sources = rr['source_hashes']
    require(sha(comparison) in sources.values(), 'Unbound owner comparison')
    for name, expected in sources.items():
        source = (root / name).resolve()
        require(source.is_relative_to(root), 'Source outside project')
        require(sha(source) == expected, 'Changed classification input: ' + name)
    require(rr['rejection_controls'] and all(x['rejected'] is True for x in rr['rejection_controls']),
            'Reference rejection controls did not pass')
    return {
        'classification_sha256': sha(path),
        'source_binding_verified': True,
        'changed_critical_geometry_within_unchanged_own_via_windows': True,
        'missing_centerline_geometries_exactly_equal': rr['missing_centerline_geometries_exactly_equal'],
        'actual_hole_containment': rr['all_changed_critical_projection_geometry_inside_actual_hole_window_intersections'],
        'actual_hole_predicate_disagreements': rr['exact_containment_predicate_disagreement_count'],
        'classification_status': rr['classification_status'],
        'scope': 'Geometric WIP review only. All numerical differences and actual-hole predicate limitations retained. No impedance, timing, power or physical qualification.',
    }
