"""Verify a net-index-only export difference without altering the raw comparison."""
from pathlib import Path
import hashlib
import json
import sys
import ast

def verify(receipt, before_board, after_board, comparison, before_snapshot, after_snapshot):
    if sys.flags.optimize:
        raise RuntimeError('Validation requires assertions enabled')
    root = Path(__file__).resolve().parents[1]
    # This exact-record comparison needs no GEOS or PCB interpreter binary module.
    source = root/'repo/f722-heli/layout-revision/signal-review/native/check_signal_geometry.py'
    constants = {}
    for node in ast.parse(source.read_text()).body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name) and node.targets[0].id in {'CRITICAL','I2C'}:
            constants[node.targets[0].id] = ast.literal_eval(node.value)
    assert set(constants) == {'CRITICAL','I2C'}
    sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
    read = lambda p: json.loads(Path(p).read_text())
    def load(folder, board):
        gp, mp, rp = [folder/n for n in ['native-geometry.json','native-signals.json','critical-reference.json']]
        g, m, r = map(read, (gp, mp, rp))
        assert sha(gp) == m['geometry_sha256'] and m['source_unchanged'] is True
        assert g['board_sha256'] == m['board_sha256'] == r['board_sha256'] == sha(board)
        assert r['sources']['native-geometry.json'] == sha(gp) and r['sources']['native-signals.json'] == sha(mp)
        return g, m, r
    r, q = read(receipt), read(comparison)
    version = r['schema']
    assert version in {'f722-exact-reference-runtime-net-index-proof/v1',
                       'f722-critical-reference-runtime-net-index-proof/v2'} and r['passed'] is True
    assert r['before_board_sha256'] == q['before_board_sha256'] == sha(before_board)
    assert r['board_sha256'] == q['after_board_sha256'] == sha(after_board)
    assert r['raw_comparison_sha256'] == sha(comparison)
    for prefix, folder in [('before', Path(before_snapshot)), ('after', Path(after_snapshot))]:
        assert r[prefix+'_native_sha256'] == sha(folder/'native-geometry.json')
        assert r[prefix+'_report_sha256'] == sha(folder/'critical-reference.json')
    bg, bm, br = load(Path(before_snapshot), Path(before_board))
    ag, am, ar = load(Path(after_snapshot), Path(after_board))
    def mapping(g):
        names, codes = {}, {}
        for o in g['objects'] + g['zones']:
            n, c = o['net'], o['net_code']
            assert isinstance(c, int) and names.get(n,c) == c and codes.get(c,n) == n
            names[n], codes[c] = c, n
        return names
    assert set(mapping(bg)) == set(mapping(ag))
    wanted = set(constants['CRITICAL']) | set(constants['I2C'])
    def records(g):
        rows = [o for o in g['objects'] if o['net'] in wanted]
        d = {o['uuid']: o for o in rows}
        assert len(d) == len(rows)
        return d
    old, new = records(bg), records(ag)
    assert old.keys() == new.keys()
    changed = []
    for uid in old:
        fields = {k for k in old[uid].keys() | new[uid].keys() if old[uid].get(k) != new[uid].get(k)}
        assert fields <= {'net_code'}, (uid, fields)
        if fields:
            changed.append(uid)
    assert changed and sorted(changed) == q['critical_object_differences']
    assert q['critical_object_geometry_identical'] is False
    assert br['nets'] == ar['nets']
    assert all(v == 0 for row in q['net_numeric_deltas_after_minus_before'].values() for v in row.values())
    if version.endswith('/v1'):
        assert bg['zones'] == ag['zones']
        assert all(p['physical_GND_lost_mm2'] == p['physical_GND_gained_mm2'] == 0 for p in q['ground_fill_changes'].values())
    else:
        # Ordinary new vias can change ground antipads away from critical copper.
        # Preserve those exact changes and require the same zero critical-loss
        # condition as the default owner review; do not claim whole-plane equality.
        assert r['scope_kind'] == 'critical_records_and_reference_only_with_changed_ground'
        assert set(q['ground_fill_changes']) == {'In1.Cu', 'In4.Cu'}
        assert r['ground_fill_changes'] == q['ground_fill_changes']
        for plane in q['ground_fill_changes'].values():
            assert plane['physical_GND_lost_mm2'] >= 0 and plane['physical_GND_gained_mm2'] >= 0
            assert plane['critical_trace_proximity']
            assert all(x['lost_GND_overlap_with_trace_width_mm2'] == 0
                       for x in plane['critical_trace_proximity'].values())
    assert r['critical_record_count'] == len(old) and r['raw_difference_count'] == len(changed)
    required = {'reject_net_change','reject_width_change','reject_uuid_change','reject_start_change','reject_copper_polygon_change','reject_omitted_UUID'}
    if version.endswith('/v2'):
        required |= {'reject_reference_report_change', 'reject_nonzero_numeric_delta',
                     'reject_lost_critical_width', 'reject_altered_ground_change_receipt'}
    assert {c['name'] for c in r['negative_controls'] if c['rejected'] is True} == required
    result = {'passed': True, 'receipt_sha256': sha(receipt), 'comparison_sha256': sha(comparison),
            'source_board_sha256': sha(before_board), 'board_sha256': sha(after_board),
            'critical_records': len(old), 'net_index_only_differences': len(changed),
            'raw_critical_object_geometry_identical': False,
            'physical_records_and_saved_reference_exact': True,
            'scope': 'Recomputed exact source-bound physical equality excluding only transient net_code; raw false comparison retained. No electrical qualification.'}
    if version.endswith('/v2'):
        result.update(whole_saved_ground_planes_exact=bg['zones'] == ag['zones'],
                      ground_fill_changes=q['ground_fill_changes'],
                      scope='Recomputed exact source-bound critical physical records excluding only transient net_code and exact critical reference report records; raw false comparison and ground changes retained. Changed ground requires fresh power/return review. No electrical qualification.')
    return result
