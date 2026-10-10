"""Verify only explicitly declared native footprint translations, never rotations/flips.

This checks identity, not placement feasibility. Native DRC, mechanical, support,
entry, reference and electrical checks remain independent requirements.
"""
from pathlib import Path
from decimal import Decimal
import argparse
import copy
import hashlib
import json
import sys

if sys.flags.optimize:
    raise RuntimeError('Validation requires assertions enabled')
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'ordinary-routing/tests/mpn-parity'))
from apply_metadata_copy import parse, children, child, properties, shape, value


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def check_nodes(before, after, changes):
    def keyed(root):
        rows = children(root, 'footprint')
        result = {properties(fp)['Reference'].items[2].value: fp for fp in rows}
        assert len(rows) == len(result) == 156
        return result
    old, new = keyed(before), keyed(after)
    assert set(old) == set(new)
    assert changes and set(changes) <= set(old)
    changed = []
    for ref in sorted(old):
        a, b = old[ref], new[ref]
        assert value(a, 'uuid') == value(b, 'uuid')
        if ref not in changes:
            assert shape(a) == shape(b), ('undeclared footprint change', ref)
            continue
        plan = changes[ref]
        assert set(plan) == {'before', 'after'}
        assert len(plan['before']) == len(plan['after']) == 4
        assert plan['before'][2:] == plan['after'][2:], ('rotation or flip forbidden', ref)
        assert Decimal(str(plan['before'][2])) % 90 == 0
        assert plan['before'][:2] != plan['after'][:2], ('declared translation is empty', ref)
        aa, bb = child(a, 'at'), child(b, 'at')
        assert len(aa.items) == len(bb.items) and len(aa.items) in (3, 4)
        assert [x.value for x in aa.items[3:]] == [x.value for x in bb.items[3:]]
        for fp, at, key in [(a, aa, 'before'), (b, bb, 'after')]:
            actual = [Decimal(at.items[1].value), Decimal(at.items[2].value),
                      Decimal(at.items[3].value) if len(at.items) == 4 else Decimal(0)]
            expected = [Decimal(str(v)) for v in plan[key][:3]]
            assert actual == expected and value(fp, 'layer') == plan[key][3], (ref, key)
        expected_fp = copy.deepcopy(a)
        child(expected_fp, 'at').items[1:3] = copy.deepcopy(bb.items[1:3])
        assert shape(expected_fp) == shape(b), ('non-translation footprint mutation', ref)
        changed.append({'reference': ref, 'uuid': value(a, 'uuid'), **plan})
    return changed


def verify(before, after, manifest):
    before, after, manifest = map(Path, (before, after, manifest))
    plan = json.loads(manifest.read_text())
    assert plan['schema'] == 'f722-declared-footprint-translations/v1'
    old, new = sha(before), sha(after)
    assert plan['source_board_sha256'] == old and plan['board_sha256'] == new
    changed = check_nodes(parse(before.read_text()), parse(after.read_text()), plan['changes'])
    assert sha(before) == old and sha(after) == new
    return {'schema': 'f722-verified-footprint-translations/v1', 'passed': True,
            'source_board_sha256': old, 'board_sha256': new,
            'declaration_sha256': sha(manifest), 'script_sha256': sha(__file__),
            'footprints': 156, 'exact_unchanged_footprints': 156 - len(changed),
            'translations': changed, 'all_other_footprint_structure_exact': True,
            'scope': 'Identity-only translation proof; no rotation, side flip, property, '
                     'pad, net, land, courtyard, graphics or 3D-model alteration allowed. '
                     'Does not establish mechanical, DRC or electrical acceptance.'}


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('before', type=Path)
    ap.add_argument('after', type=Path)
    ap.add_argument('manifest', type=Path)
    ap.add_argument('--out', type=Path, required=True)
    args = ap.parse_args()
    receipt = verify(args.before, args.after, args.manifest)
    args.out.write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps(receipt))
