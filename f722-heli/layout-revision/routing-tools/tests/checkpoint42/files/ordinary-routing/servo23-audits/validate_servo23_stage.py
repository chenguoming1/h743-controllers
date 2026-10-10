#!/usr/bin/env python3
"""Strict sealed-source SERVO2/3 stage validation; no net-wide exemptions.

This is a separate change contract, not an extension of the ordinary-rewrite
validator. Native snapshots, plan, screen, constructor, and construction receipt
are pinned. A successor can preserve this exact stage and add an explicitly
hash-bound manifest, but it cannot change any source or constructed object.
"""
import argparse
import collections
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE_SHA = '2a73d9b7dad3a14b0d00c80e81e0ba8a817b50179c15692aad39fde9920c2115'
SOURCE_NATIVE_SHA = '7c8386f8aee7b1b01fd14265b0dc778d600a6e6d3aeeba6ac12a13c740859f24'
SOURCE_MAP_SHA = 'e5d3b86b638fa7774cfa0e2698ff9eacbcb4cbe2622bd829886463f02735a9ba'
STAGE_SHA = 'f2bfe89ba27b147fd07ecf2cf5fa433688403294a9fb332e3c2da171b6a6deff'
STAGE_NATIVE_SHA = '1d3160d4df55e5bff51a92b49abb738987d79bd0b7820597af90e33ea80c0298'
STAGE_MAP_SHA = '650fcc36111cff7f45a79a4e4efda6cf30ff92228cfbf294a05dbfc0f7d78982'
PLAN_SHA = '1c359be7580340a182738f556cb9becb22106d66d88b06b011de61a263c81f88'
SCREEN_SHA = '8c72c56fd3f766620c42c8ff717f30a487896f2aab7c64ea62aff25f0cd02101'
RECEIPT_SHA = '21564e728b99a13b08d268f37d0a3664559bbb6a0d015e5f7a5c3ed5df5275ee'
CONSTRUCTOR_SHA = 'dd74ed348171de0c76aca75c2acb8e721c36a12a6e100da292a16425cff53589'
BINDINGS = {
    'stage37': dict(source_board=SOURCE_SHA, source_native=SOURCE_NATIVE_SHA, source_map=SOURCE_MAP_SHA,
                    stage_board=STAGE_SHA, stage_native=STAGE_NATIVE_SHA, stage_map=STAGE_MAP_SHA,
                    receipt=RECEIPT_SHA, constructor=CONSTRUCTOR_SHA),
    'stage38': dict(
        source_board='95bb984bf046fef2d96c6e59d9e00696f504d35f89e3340fdf076cd7c9249c9f',
        source_native='4acfc65f6090f155a5a7a4365374d78bb7ad074a82fff319d1c0fd05d725daff',
        source_map='263131b8568e9c44383ab353845f1d096774b57b5c43da311c287e397577da53',
        stage_board='e93f1a1814f8b2bfd6341be9522a053a71db2706d7d81ee2984f6bd82a6c8aa5',
        stage_native='48dbb11a929a4913056a7a948e7ae498a4995e53f01e98164f240522cfeee638',
        stage_map='aafacbdbeb652b9b3a120160e7cf823c278ada147b8420cff0a3fb26b209835d',
        receipt='d0a88fdc2d6503c711ad5e5f1816d658ac0a812c6a19ed470d0d3f00fd39c4ae',
        constructor='eb56827d150f73ab3389133530e1e218f53ec72beacabc7fbd75f67fb60641fe'),
}
CONTINUATION38_SHA = '1db7ce99761b43a3761ec1410cdab8250120770a2d4a4754e4355c445fd84e86'
CONTINUATION38_HELPER_SHA = '590ba88ff6fad0c32d5341e86dd0ccd0e8b42d4510ccf79c87f3a1ca12c523dd'
ORDINARY_OWNER_CONTRACT_SHA = '8227145e6f335215ccb0a0381a058c7c58a909dab831078c7b0b01b392bba2e1'
GROUND_ALLOW = frozenset({'4bdbc594-f503-4ac4-887a-602087e810a5',
                          '651dd4bb-367c-4146-91ab-c7b2cafdcd9c',
                          '7aa57d39-de74-4e59-ae7e-b321426a2b13'})
ALLOW = frozenset({'039a63ec-d4b3-4367-a89e-61ffdd1dd9ef',
    '099a20ee-ccb7-487c-aa08-047b49e9d92b', '25c69f42-1efb-412a-bb87-f081745cab23',
    '734de095-936a-4d15-b30d-c37b0f7663bb', '7af3595c-7d69-471b-9895-586d3b074e8b',
    '8113afab-5370-4609-8346-a5e532efa35b', '9edf22b5-bde9-45f0-86ea-6aefaf3051b5',
    'c284754f-ab23-4ce9-ae72-2662dc7fce81', 'e3d66729-7dcf-4a0e-a0c5-5720860b1f0a',
    'f0ab58ba-6fac-49f0-aa28-85653a9eb251'}) | GROUND_ALLOW
OMITTED = ['S3P1-inner-exit-only']


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def checked(path, digest):
    assert sha(path) == digest, f'Wrong sealed input: {path}'
    return read(path)


def index(objects):
    result = {o['uuid']: o for o in objects}
    assert len(result) == len(objects), 'Duplicate object UUID'
    return result


def fixed_contract(before, after):
    for key in ['schema', 'maximum_polygon_error_mm', 'copper_error_location',
                'pad_cut_error_location', 'footprints', 'edge_cuts', 'copper_layers',
                'copper_layer_ids', 'board_thickness_mm', 'outline_with_npth']:
        assert before[key] == after[key], f'Changed fixed contract: {key}'
    assert after['maximum_polygon_error_mm'] <= .00001
    old_z, new_z = index(before['zones']), index(after['zones'])
    assert old_z.keys() == new_z.keys(), 'Changed zone UUID set'
    for uid, previous in old_z.items():
        current = new_z[uid]
        refill = not previous['rule'] and previous['net'] == 'GND' and set(previous['layers']) <= {'In1.Cu', 'In4.Cu'}
        omit = {'filled', 'fill_representation'} if refill else set()
        assert {k: v for k, v in previous.items() if k not in omit} == {
            k: v for k, v in current.items() if k not in omit}, f'Changed zone contract: {uid}'
        if refill:
            assert set(current['filled']) == set(previous['filled'])
            assert all(current['filled'][layer] for layer in current['layers'])


def shape_signature(obj):
    if obj['kind'] == 'track':
        return ('track', obj['net'], tuple(obj['copper']), tuple(obj['start']), tuple(obj['end']), obj['width'])
    assert obj['kind'] == 'via'
    return ('via', obj['net'], tuple(obj['xy']), obj['width'], obj['drill']['width'])


def planned_signatures(row):
    if row['kind'] == 'track':
        return [('track', row['physical_net'], (row['layer'],), tuple(a), tuple(b), row['width_mm'])
                for a, b in zip(row['points_mm'], row['points_mm'][1:])]
    return [('via', row['physical_net'], tuple(row['xy_mm']), row['diameter_mm'], row['drill_mm'])]


def validate_records(before, after, before_map, after_map, plan, screen, receipt, binding_name='stage37'):
    """Pure record checks, also used by in-memory mutation controls."""
    assert binding_name in BINDINGS, 'Unapproved construction basis'
    binding = BINDINGS[binding_name]
    source_sha, stage_sha = binding['source_board'], binding['stage_board']
    assert before['board_sha256'] == source_sha, 'Wrong source board'
    assert after['board_sha256'] == stage_sha, 'Wrong constructed stage board'
    assert receipt['schema'] == 'f722-isolated-servo23-native-stage/v1'
    assert receipt['source_board_sha256'] == source_sha and receipt['board_sha256'] == stage_sha
    assert receipt['plan_sha256'] == PLAN_SHA and receipt['screen_sha256'] == SCREEN_SHA
    assert receipt['constructor_sha256'] == binding['constructor']
    assert screen['source_board_sha256'] == SOURCE_SHA and screen['all_nominal_screens_pass']
    assert not plan['construction_complete'] and not plan['changed_footprint_poses']
    assert receipt['omitted_plan_rows'] == OMITTED
    assert not receipt['adoption_requested']
    old, now = index(before['objects']), index(after['objects'])
    removals = index(plan['remove_exact_objects'])
    assert set(removals) == ALLOW == set(old) - set(now), 'Not the exact 13 removals'
    recorded_removals = index(receipt['removed_source_objects'])
    assert set(recorded_removals) == ALLOW
    assert before_map['board_sha256'] == source_sha and after_map['board_sha256'] == stage_sha
    bm, am = before_map['logical_route_map'], after_map['logical_route_map']
    for uid in ALLOW:
        obj, row = old[uid], removals[uid]
        assert obj == recorded_removals[uid], f'Wrong removed record: {uid}'
        assert obj['net'] == ('GND' if uid in GROUND_ALLOW else 'SERVO2_MCU')
        assert obj['kind'] in {'track', 'via'}
        for key in ['kind', 'net', 'start', 'end', 'width']:
            assert obj[key] == row[key], (uid, key)
        assert list(obj['copper']) == row['layers']
        assert bm.get(uid) == row['logical_owner'], f'Wrong removed logical owner: {uid}'
    assert all(now.get(uid) == obj for uid, obj in old.items() if uid not in ALLOW), 'Moved or edited existing object'
    declared = index(receipt['added_objects'])
    assert set(now) - set(old) == set(declared), 'Undeclared added object'
    expected_map = {uid: owner for uid, owner in bm.items() if uid not in ALLOW}
    rows = {r['name']: r for r in plan['replacement_and_new_routes']}
    expected_rows = set(rows) - set(OMITTED)
    assert {r['plan_name'] for r in declared.values()} == expected_rows
    for name in expected_rows:
        row = rows[name]
        members = [r for r in declared.values() if r['plan_name'] == name]
        assert collections.Counter(shape_signature(now[r['uuid']]) for r in members) == collections.Counter(planned_signatures(row)), f'Wrong constructed geometry: {name}'
        for member in members:
            obj = now[member['uuid']]
            assert member['net'] == obj['net'] == row['physical_net']
            assert member['logical_net'] == row['logical_net'], f'Wrong constructed owner: {name}'
            assert obj['net_code'] == next(o['net_code'] for o in before['objects'] if o['net'] == obj['net'])
            if obj['kind'] == 'via':
                assert obj['plated'] and obj['barrel_layers'] == after['copper_layers']
                assert obj['top_layer'] == 'F.Cu' and obj['bottom_layer'] == 'B.Cu'
                assert obj['tented'] == {'F.Mask': True, 'B.Mask': True}
                assert obj['start'] == obj['end'] == obj['xy']
                assert all(w == .45 for w in obj['width_by_layer'].values())
            else:
                assert obj['width'] == (.25 if obj['net'] == 'GND' else .127)
            if obj['net'] != 'GND':
                expected_map[obj['uuid']] = row['logical_net']
    assert am == expected_map, 'Wrong logical owner or undeclared owner-map change'
    fixed_contract(before, after)
    return {'passed': True, 'source_board_sha256': source_sha, 'stage_board_sha256': stage_sha,
            'exact_removed_uuids': sorted(ALLOW), 'ground_removed_uuids': sorted(GROUND_ALLOW),
            'actual_added_uuids': sorted(declared), 'source_objects_outside_allowance_exact': len(old) - len(ALLOW),
            'removed_ordinary_count': 10, 'removed_dedicated_ground_count': 3,
            'added_object_count': len(declared), 'all_old_owners_outside_allowance_exact': True,
            'all_constructed_geometry_and_owners_match_sealed_plan': True,
            'all_poses_pads_outline_layers_and_zone_contracts_exact': True,
            'omitted_plan_rows': OMITTED, 'adoption_claimed': False}


def validate_source38_continuation(origin, current, origin_map, current_map):
    """Require the known accepted37-to38 additive source, not a net exemption."""
    assert origin['board_sha256'] == SOURCE_SHA
    assert current['board_sha256'] == BINDINGS['stage38']['source_board']
    old, now = index(origin['objects']), index(current['objects'])
    assert all(now.get(uid) == obj for uid, obj in old.items()), 'Continuation edited accepted37 object'
    added = {uid: obj for uid, obj in now.items() if uid not in old}
    assert len(added) == 21
    assert all(o['net'] == 'RPM_LV' and o['kind'] in {'track', 'via'} for o in added.values())
    assert current_map['logical_route_map'] == {**origin_map['logical_route_map'], **{uid: 'RPM_LV' for uid in added}}
    fixed_contract(origin, current)
    return {'passed': True, 'origin_board_sha256': SOURCE_SHA,
            'accepted38_board_sha256': current['board_sha256'],
            'all_accepted37_objects_exact': len(old), 'added_exact_rpm_uuids': sorted(added),
            'all_added_records_source_hash_bound': True, 'all_accepted37_logical_owners_exact': True}


def load_basis(source=ROOT / 'candidate37', stage=ROOT / 'servo23-native-stage37',
               plan_dir=ROOT / 'servo23-joint-plan', constructor=ROOT / 'stage_servo23_native.py',
               binding_name='stage37', origin_dir=ROOT / 'candidate37',
               continuation_helper=ROOT / 'recheck_servo23_continuation38.py'):
    source, stage, plan_dir, constructor = map(Path, [source, stage, plan_dir, constructor])
    binding = BINDINGS[binding_name]
    paths = {source / 'f722-heli.kicad_pcb': binding['source_board'],
             source / 'f722-heli.native.json': binding['source_native'],
             source / 'f722-heli.logical-route-map.json': binding['source_map'],
             stage / 'f722-heli.kicad_pcb': binding['stage_board'],
             stage / 'f722-heli.native.json': binding['stage_native'],
             stage / 'f722-heli.logical-route-map.json': binding['stage_map'],
             stage / 'construction-provenance.json': binding['receipt'],
             plan_dir / 'plan.json': PLAN_SHA, plan_dir / 'screen.json': SCREEN_SHA,
             constructor: binding['constructor']}
    origin_dir = Path(origin_dir) if binding_name == 'stage38' else source
    if binding_name == 'stage38':
        paths.update({origin_dir / 'f722-heli.kicad_pcb': SOURCE_SHA,
                      origin_dir / 'f722-heli.native.json': SOURCE_NATIVE_SHA,
                      origin_dir / 'f722-heli.logical-route-map.json': SOURCE_MAP_SHA,
                      stage / 'continuation-recheck.json': CONTINUATION38_SHA,
                      plan_dir / 'continuation38-recheck.json': CONTINUATION38_SHA,
                      Path(continuation_helper): CONTINUATION38_HELPER_SHA})
    for path, digest in paths.items():
        assert sha(path) == digest, f'Wrong sealed input: {path}'
    before, after = [read(p / 'f722-heli.native.json') for p in [source, stage]]
    bm, am = [read(p / 'f722-heli.logical-route-map.json') for p in [source, stage]]
    plan, screen = [read(plan_dir / p) for p in ['plan.json', 'screen.json']]
    receipt = read(stage / 'construction-provenance.json')
    report = validate_records(before, after, bm, am, plan, screen, receipt, binding_name)
    origin = read(origin_dir / 'f722-heli.native.json')
    origin_map = read(origin_dir / 'f722-heli.logical-route-map.json')
    continuation = None
    if binding_name == 'stage38':
        continuation = validate_source38_continuation(origin, before, origin_map, bm)
        proof = read(stage / 'continuation-recheck.json')
        assert proof['passed'] and proof['origin_source_board_sha256'] == SOURCE_SHA
        assert proof['current_source_board_sha256'] == binding['source_board']
        assert proof['plan_sha256'] == PLAN_SHA and proof['source_native_sha256'] == binding['source_native']
        assert proof['source_map_sha256'] == binding['source_map'] and proof['helper_sha256'] == CONTINUATION38_HELPER_SHA
        assert proof['checks'] and all(c['gap_mm'] >= c['required_mm'] for c in proof['checks'])
        assert receipt['origin_plan_source_board_sha256'] == SOURCE_SHA
        assert receipt['explicit_additive_continuation_recheck'] == 'continuation-recheck.json'
        report['accepted37_to38_exact_additive_continuation'] = continuation
    report['sealed_file_sha256'] = {str(p): h for p, h in paths.items()}
    return dict(before=before, stage=after, before_map=bm, stage_map=am, plan=plan,
                screen=screen, receipt=receipt, report=report, sealed_paths=paths,
                origin_before=origin, origin_map=origin_map, origin_dir=origin_dir,
                binding_name=binding_name, binding=binding, continuation=continuation)


def validate_successor_records(basis, after, amap, manifest, ordinary_owners):
    """Pure exact-record comparison; file binding is mandatory in its caller."""
    old, now = index(basis['stage']['objects']), index(after['objects'])
    expected = index(manifest['added_native_objects'])
    assert all(now.get(uid) == obj for uid, obj in old.items()), 'Successor changed stage object'
    assert set(now) - set(old) == set(expected), 'Undeclared successor object'
    assert all(now[uid] == obj for uid, obj in expected.items()), 'Successor differs from exact manifest'
    owners = manifest['added_logical_owners']
    assert set(owners) == set(expected)
    for uid, obj in expected.items():
        assert obj['kind'] in {'track', 'via'}, 'Non-route successor object'
        assert ordinary_owners.get(owners[uid]) == obj['net'], 'Nonordinary or invalid logical owner'
    assert amap['logical_route_map'] == {**basis['stage_map']['logical_route_map'], **owners}, 'Successor changed source owner'
    fixed_contract(basis['stage'], after)
    return sorted(expected)


def validate_additive_successor(basis, candidate, manifest_path, manifest_sha256):
    """Verify an explicit successor; this cannot authorize or qualify new copper.

    The separately reviewed manifest must enumerate every added native record and
    owner, carry both source hashes, and be pinned by the caller. No removals,
    source-owner edits, GND additions, or net-level exemptions are accepted.
    Geometry/process/connectivity and engine provenance remain independent gates.
    """
    candidate = Path(candidate)
    manifest = checked(manifest_path, manifest_sha256)
    assert manifest['schema'] == 'f722-servo23-exact-additive-successor/v1'
    assert manifest['accepted37_board_sha256'] == SOURCE_SHA
    assert manifest['stage_board_sha256'] == basis['binding']['stage_board']
    assert manifest['stage_native_sha256'] == basis['binding']['stage_native']
    after = checked(candidate / 'f722-heli.native.json', manifest['candidate_native_sha256'])
    amap = checked(candidate / 'f722-heli.logical-route-map.json', manifest['candidate_map_sha256'])
    assert sha(candidate / 'f722-heli.kicad_pcb') == manifest['candidate_board_sha256'] == after['board_sha256'] == amap['board_sha256']
    owner_contract = checked(Path(__file__).with_name('ordinary-owner-contract.json'), ORDINARY_OWNER_CONTRACT_SHA)
    assert owner_contract['source_board_sha256'] == SOURCE_SHA
    assert owner_contract['model_sha256'] == basis['plan']['source_hashes']['ordinary-routing/model-candidate37-ready/model.json']
    additions = validate_successor_records(basis, after, amap, manifest, owner_contract['ordinary_logical_owners'])
    # Bind all candidate inputs through the whole downstream read-only audit.
    basis['sealed_paths'].update({Path(manifest_path): manifest_sha256,
        candidate / 'f722-heli.kicad_pcb': manifest['candidate_board_sha256'],
        candidate / 'f722-heli.native.json': manifest['candidate_native_sha256'],
        candidate / 'f722-heli.logical-route-map.json': manifest['candidate_map_sha256'],
        Path(__file__).with_name('ordinary-owner-contract.json'): ORDINARY_OWNER_CONTRACT_SHA})
    return after, amap, {'passed': True, 'manifest_sha256': manifest_sha256,
                         'additional_native_uuids': additions,
                         'ordinary_owner_contract_sha256': ORDINARY_OWNER_CONTRACT_SHA,
                         'candidate_board_sha256': after['board_sha256'],
                         'stage_objects_and_owners_exact': True,
                         'scope': 'Exact manifest invariance only; independent ordinary additive gates required.'}


def add_basis_arguments(parser):
    parser.add_argument('--basis', choices=sorted(BINDINGS), default='stage37')
    parser.add_argument('--source', type=Path, default=ROOT / 'candidate37')
    parser.add_argument('--stage', type=Path, default=ROOT / 'servo23-native-stage37')
    parser.add_argument('--plan-dir', type=Path, default=ROOT / 'servo23-joint-plan')
    parser.add_argument('--constructor', type=Path, default=ROOT / 'stage_servo23_native.py')
    parser.add_argument('--candidate', type=Path)
    parser.add_argument('--addition-manifest', type=Path)
    parser.add_argument('--addition-manifest-sha256')
    parser.add_argument('--origin', type=Path, default=ROOT / 'candidate37')
    parser.add_argument('--continuation-helper', type=Path, default=ROOT / 'recheck_servo23_continuation38.py')


def load_for_args(args):
    if args.basis == 'stage38':
        if args.source == ROOT / 'candidate37':
            args.source = ROOT / 'candidate38'
        if args.stage == ROOT / 'servo23-native-stage37':
            args.stage = ROOT / 'servo23-native-stage38'
        if args.constructor == ROOT / 'stage_servo23_native.py':
            args.constructor = ROOT / 'stage_servo23_native38.py'
    basis = load_basis(args.source, args.stage, args.plan_dir, args.constructor,
                       args.basis, args.origin, args.continuation_helper)
    if args.candidate and args.candidate.resolve() != args.stage.resolve():
        assert args.addition_manifest and args.addition_manifest_sha256, 'Successor needs exact pinned addition manifest'
        after, amap, extra = validate_additive_successor(basis, args.candidate, args.addition_manifest, args.addition_manifest_sha256)
    else:
        assert not args.addition_manifest and not args.addition_manifest_sha256
        after, amap, extra = basis['stage'], basis['stage_map'], None
    return basis, after, amap, extra


def recheck(basis):
    assert all(sha(p) == h for p, h in basis['sealed_paths'].items()), 'Sealed source changed during audit'


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    add_basis_arguments(ap)
    ap.add_argument('--out', type=Path, required=True)
    args = ap.parse_args()
    basis, after, _, extra = load_for_args(args)
    result = dict(basis['report'], candidate_board_sha256=after['board_sha256'],
                  additive_successor=extra, validator_sha256=sha(__file__))
    recheck(basis)
    args.out.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: result[k] for k in ['passed', 'removed_ordinary_count', 'removed_dedicated_ground_count', 'added_object_count']}))


if __name__ == '__main__':
    main()
