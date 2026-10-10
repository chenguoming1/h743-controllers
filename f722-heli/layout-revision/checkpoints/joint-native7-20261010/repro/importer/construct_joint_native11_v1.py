#!/usr/bin/env python3
"""Import a complete recorded joint transaction into a NEW isolated paired project.

Pure --check-inputs needs no lease. Native work always needs a current owner lease
and the pinned official KiCad Python wrapper. This file never routes or fixes a
transaction, infers missing poses, rewrites source CAD, or claims acceptance.
"""
from __future__ import annotations

import argparse
import copy
import json
import os
import shutil
import sys
import uuid
from pathlib import Path

from common_joint11 import (DEFAULT_SPEC, HERE, ROOT, physical, prepare_paired_texts,
                            read, require, sha, unique, validate_bindings,
                            validate_lease, validate_poses, validate_transaction,
                            parser_helper, write)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--transaction', type=Path, required=True)
    ap.add_argument('--poses', type=Path)
    ap.add_argument('--output', type=Path)
    ap.add_argument('--lease', type=Path)
    ap.add_argument('--spec', type=Path, default=DEFAULT_SPEC)
    ap.add_argument('--check-inputs', action='store_true')
    args = ap.parse_args()
    spec = read(args.spec)
    require(spec['schema'] == 'f722-joint-native-import-spec/v1', 'Unsupported import specification')
    source, before = validate_bindings(spec)
    transaction = read(args.transaction)
    validation = validate_transaction(transaction, before, spec)
    require(args.poses is not None, 'An exact final pose ledger is required')
    ledger = read(args.poses)
    changes = validate_poses(ledger, args.transaction, before, validation, spec)
    texts, paired_proof = prepare_paired_texts(source, spec)
    if args.check_inputs:
        print(json.dumps({'input_validation_passed': True, 'segments': validation['segments'],
                          'vias': validation['vias'], 'pads': 558, 'footprints': 156,
                          'paired_source_patch_verified_in_memory': True,
                          'native_work_performed': False, 'candidate_created': False}))
        return
    require(args.output is not None and args.lease is not None, '--output and --lease are required for native work')
    output = args.output.resolve()
    require(output.is_relative_to(HERE / 'candidates') and output != HERE / 'candidates',
            'Candidates must be new named directories under this versioned importer/candidates/')
    require(not output.exists(), 'Candidate already exists; use a new directory, retain the failed attempt')
    lease = validate_lease(args.lease, 'construct_refill_export', args.transaction, output, spec)
    runtime = Path(spec['runtime']['directory'])
    require(Path(os.environ.get('KICAD_CONFIG_HOME', '/nonexistent')).resolve() == runtime / 'config',
            'Run through the pinned official KiCad Python wrapper')
    # All source, completeness, pose, metadata and lease gates precede this import.
    import pcbnew as p
    require(p.Version() == spec['runtime']['native_version'] and p.GetBuildVersion() == spec['runtime']['native_build'], 'Unexpected native runtime')
    sys.path.insert(0, str(ROOT / 'ordinary-routing/native-tools'))
    from export_native_copper import export
    h = parser_helper(spec)
    source_hash = spec['source_board_sha256']
    transaction_hash = sha(args.transaction)
    iu = lambda v: round(v * 1e6)
    point = lambda xy: p.VECTOR2I(*map(iu, xy))
    rounded = lambda xy: [iu(v) / 1e6 for v in xy]
    output.mkdir(parents=True, exist_ok=False)
    project = read(source / 'project-input-preservation.json')
    for row in project['files']:
        path = Path(row['path'])
        require(not path.is_absolute() and '..' not in path.parts, 'Unsafe project relative path')
        target = output / path
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source / path, target)
    for name, text in texts.items():
        require((output / name).is_file(), f'Paired project file missing: {name}')
        (output / name).write_text(text)
    write(output / 'paired-source-proof.json', {**paired_proof, 'source_board_sha256': source_hash,
        'files': {name: {'source_sha256': sha(source / name), 'candidate_sha256': sha(output / name)} for name in texts}})
    for source_path, target_name in [(args.transaction, 'selected-transaction.json'), (args.poses, 'selected-poses.json'),
                                     (args.spec, 'import-spec.json'), (args.lease, 'owner-lease-at-start.json'),
                                     (Path(__file__), 'construct.used.py'), (HERE / 'common_joint11.py', 'common.used.py')]:
        shutil.copy2(source_path, output / target_name)
    if not (output / 'parts.json').exists():
        shutil.copy2(source / 'parts.json', output / 'parts.json')

    def apply_declared_footprints(board):
        fps = {f.GetReference(): f for f in board.GetFootprints()}
        require(len(fps) == 156, 'Native footprint count mismatch')
        for ref, declaration in changes.items():
            f = fps[ref]
            old, new = declaration['before'], declaration['after']
            require(f.GetPosition() == point(old[:2]) and (f.GetOrientationDegrees() - old[2]) % 360 == 0 and
                    f.GetLayerName() == old[3], f'Native source pose mismatch: {ref}')
            if old[3] != new[3]:
                f.Flip(f.GetPosition(), declaration['flip_left_right'])
            f.SetOrientationDegrees(new[2])
            f.SetPosition(point(new[:2]))
            require(f.GetLayerName() == new[3], f'Failed native flip: {ref}')
        pads = {a.m_Uuid.AsString(): a for f in fps.values() for a in f.Pads()}
        require(len(pads) == 558, 'Native pad UUID inventory mismatch')
        for key, net_change in spec['approved_pad_net_changes'].items():
            pad = pads[net_change['uuid']]
            require(pad.GetNetname() == net_change['before'], f'Unexpected source net: {key}')
            require(pad.GetNumber() == key.split('.')[1], f'Unexpected native pin number: {key}')
            net = board.FindNet(net_change['after'])
            require(net is not None, f'Missing approved target net: {key}')
            pad.SetNet(net)
        return fps

    board = p.LoadBoard(str(source / 'f722-heli.kicad_pcb'))
    apply_declared_footprints(board)
    source_tracks = {t.m_Uuid.AsString(): t for t in board.GetTracks()}
    for uid in validation['removed']:
        require(uid in source_tracks, f'Source cut is not native track/via/arc: {uid}')
        board.Remove(source_tracks[uid])
    original_map = read(source / 'f722-heli.logical-route-map.json')
    require(original_map['board_sha256'] == source_hash, 'Source logical map is stale')
    logical = {uid: net for uid, net in original_map['logical_route_map'].items() if uid not in validation['removed']}
    held = []  # Retain SWIG references throughout mutation/save.
    additions = []
    existing_ids = set(validation['old'])

    def add(item, recipe, segment=None):
        suffix = recipe['name'] + ('/via' if segment is None else '/segment/' + str(segment))
        uid = str(uuid.uuid5(uuid.NAMESPACE_URL, source_hash + '/' + transaction_hash + '/' + suffix))
        require(uid not in existing_ids, 'Deterministic UUID collision')
        existing_ids.add(uid)
        item.SetUuid(p.KIID(uid))
        item.SetNet(board.FindNet(recipe['net']))
        board.Add(item)
        held.append(item)
        logical[uid] = recipe['net']
        additions.append({'uuid': uid, 'recipe_name': recipe['name'], 'segment_index': segment,
                          'recipe': recipe})

    for row in transaction['added_copper']:
        recipe = row['recipe']
        if recipe['kind'] == 'track':
            for i, (a, b) in enumerate(zip(recipe['points'], recipe['points'][1:])):
                require(point(a) != point(b), f'Polyline segment collapses at native resolution: {recipe["name"]}/{i}')
                track = p.PCB_TRACK(board)
                track.SetLayer(board.GetLayerID(recipe['layer']))
                track.SetWidth(iu(recipe['width']))
                track.SetStart(point(a))
                track.SetEnd(point(b))
                add(track, recipe, i)
        else:
            via = p.PCB_VIA(board)
            via.SetPosition(point(recipe['xy']))
            via.SetWidth(iu(.45))
            via.SetDrill(iu(.20))
            via.SetViaType(p.VIATYPE_THROUGH)
            via.SetLayerPair(p.F_Cu, p.B_Cu)
            via.SetFrontTentingMode(p.TENTING_MODE_TENTED)
            via.SetBackTentingMode(p.TENTING_MODE_TENTED)
            add(via, recipe)
    pcb_path = output / 'f722-heli.kicad_pcb'
    p.SaveBoard(str(pcb_path), board)
    validate_lease(args.lease, 'construct_refill_export', args.transaction, output, spec)
    board = p.LoadBoard(str(pcb_path))
    manager = p.GetSettingsManager()
    require(manager.LoadProject(str(output / 'f722-heli.kicad_pro')), 'Cannot load copied project')
    board.SetProject(manager.GetProject(str(output / 'f722-heli.kicad_pro')))
    board.SynchronizeNetsAndNetClasses(False)
    board.BuildConnectivity()
    require(p.ZONE_FILLER(board).Fill(board.Zones()), 'Native zone refill failed')
    p.SaveBoard(str(pcb_path), board)
    validate_lease(args.lease, 'construct_refill_export', args.transaction, output, spec)
    after = export(pcb_path)
    old = validation['old']
    now = unique(after['objects'])
    new_ids = {a['uuid'] for a in additions}
    require(set(old) - set(now) == set(validation['removed']), 'Actual native removals differ from exact cuts')
    require(set(now) - set(old) == new_ids, 'Unexpected/missing actual native additions')
    actual_changed = {uid for uid in set(old) & set(now) if physical(old[uid]) != physical(now[uid])}
    require(actual_changed == set(validation['changed']), 'Actual changed-pad inventory differs from selected transaction')
    mismatches = {uid: [key for key in set(now[uid]) | set(planned) if key != 'net_code' and now[uid].get(key) != planned.get(key)]
                  for uid, planned in validation['changed'].items() if physical(now[uid]) != physical(planned)}
    # Save full mismatch evidence and stop. Never silently loosen geometric comparison.
    if mismatches:
        write(output / 'native-pad-mismatch.json', {'board_sha256': sha(pcb_path), 'mismatches': mismatches,
              'actual': [now[uid] for uid in mismatches], 'planned': [validation['changed'][uid] for uid in mismatches],
              'acceptance_claimed': False})
        raise ValueError('Actual full pad geometry differs from recorded transaction; inspect native-pad-mismatch.json')
    require(sum(o['kind'] == 'pad' for o in now.values()) == 558 and len(after['footprints']) == 156, 'Lost footprint/pad')
    for item in additions:
        record, recipe = now[item['uuid']], item['recipe']
        require(record['kind'] == recipe['kind'] and record['net'] == recipe['net'], 'Imported copper identity differs')
        if recipe['kind'] == 'track':
            i = item['segment_index']
            require(record['start'] == rounded(recipe['points'][i]) and record['end'] == rounded(recipe['points'][i + 1]) and
                    record['width'] == iu(recipe['width']) / 1e6 and record['width_by_layer'] == {recipe['layer']: iu(recipe['width']) / 1e6},
                    f'Native segment differs or bend dropped: {recipe["name"]}/{i}')
        else:
            require(record['xy'] == rounded(recipe['xy']) and record['width'] == .45 and record['drill']['width'] == .20 and
                    record['via_type'] == p.VIATYPE_THROUGH and record['barrel_layers'] == before['copper_layers'] and
                    record['top_layer'] == 'F.Cu' and record['bottom_layer'] == 'B.Cu' and
                    record['tented'] == {'F.Mask': True, 'B.Mask': True} and not record['mask'],
                    f'Actual through-via drill/tenting/layers differ: {recipe["name"]}')
    for key in ('edge_cuts', 'outline_with_npth', 'copper_layers', 'copper_layer_ids', 'board_thickness_mm'):
        require(before[key] == after[key], f'Undeclared board structure change: {key}')
    zone = lambda z: {k: v for k, v in z.items() if k not in ('filled', 'fill_representation', 'net_code')}
    require(list(map(zone, before['zones'])) == list(map(zone, after['zones'])), 'Zone settings/outline changed')

    # Independently reload the source and apply ONLY declared poses and approved nets.
    # Compare entire footprint syntax, including local graphics/text/paste/custom pads.
    predicted = p.LoadBoard(str(source / 'f722-heli.kicad_pcb'))
    apply_declared_footprints(predicted)
    proof_path = output / 'footprints-predicted-only.kicad_pcb'
    p.SaveBoard(str(proof_path), predicted)

    def footprint_shapes(path):
        tree = h.parse(path.read_text())
        return {h.props(f)['Reference']: h.shape(f) for f in h.children(tree, 'footprint')}

    source_shapes = footprint_shapes(source / 'f722-heli.kicad_pcb')
    predicted_shapes = footprint_shapes(proof_path)
    actual_shapes = footprint_shapes(pcb_path)
    require(set(source_shapes) == set(predicted_shapes) == set(actual_shapes) and len(actual_shapes) == 156, 'Full footprint inventory differs')
    require(actual_shapes == predicted_shapes, 'Full native footprint structures differ from declared poses and net edits')
    require({ref for ref in source_shapes if source_shapes[ref] != actual_shapes[ref]} == set(changes), 'Undeclared native footprint mutation')
    for uid, net in logical.items():
        require(uid in now, f'Logical map has missing object: {uid}')
        require(now[uid]['net'] == net.split('::')[0], f'Logical map physical-net mismatch: {uid}')
    require({uid: net for uid, net in logical.items() if uid not in new_ids} ==
            {uid: net for uid, net in original_map['logical_route_map'].items() if uid not in validation['removed']}, 'Retained logical map changed')
    candidate_hash = sha(pcb_path)
    (output / 'f722-heli.native.json').write_text(json.dumps(after, separators=(',', ':')) + '\n')
    write(output / 'f722-heli.logical-route-map.json', {'schema': 'f722-logical-route-map/v1', 'board_sha256': candidate_hash,
          'source_sha256': source_hash, 'logical_route_map': logical})
    fixed = set(read(source / 'fixed-explicit-native-ids.json'))
    write(output / 'fixed-explicit-native-ids.json', sorted((fixed - set(validation['removed'])) | new_ids))
    poses = read(source / 'poses-native.json')
    for f in after['footprints']:
        poses[f['ref']] = f['xy'] + [f['angle'], f['side']]
    write(output / 'poses-native.json', poses)
    project_rows = []
    for row in project['files']:
        expected = sha(output / row['path'])
        require(row['path'] in texts or expected == row['sha256'], f'Unapproved project input modification: {row["path"]}')
        project_rows.append({'path': row['path'], 'source_sha256': row['sha256'], 'sha256': expected,
                             'changed': expected != row['sha256']})
    write(output / 'project-input-preservation.json', {'source_board_sha256': source_hash, 'board_sha256': candidate_hash,
          'all_other_non_board_project_inputs_byte_identical': True, 'paired_changed_files': sorted(texts), 'files': project_rows})
    for successor in spec['versioned_contract_successors']['expected_successor_contracts']:
        content = copy.deepcopy(successor['expected_content'])
        original_contract = read(ROOT / content['source_contract']['path'])
        require(content['checks'] == original_contract['checks'], 'Actual bonded-cut checks changed')
        content['board_sha256'] = candidate_hash
        write(output / successor['candidate_relative_path'], content)
    receipt = {'schema': 'f722-joint-native-construction/v1', 'source_board_sha256': source_hash,
        'board_sha256': candidate_hash, 'source_native_sha256': spec['source_native_sha256'],
        'transaction_sha256': transaction_hash, 'pose_ledger_sha256': sha(args.poses), 'spec_sha256': sha(args.spec),
        'constructor_sha256': sha(__file__), 'lease_id': lease['lease_id'], 'native_build': p.GetBuildVersion(),
        'segments': validation['segments'], 'vias': validation['vias'], 'added_native_records': [now[a['uuid']] for a in additions],
        'recipe_to_native_UUIDs': [{k: v for k, v in a.items() if k != 'recipe'} for a in additions],
        'removed_source_records': list(validation['removed'].values()),
        'changed_pad_records': [{'before': old[uid], 'after': now[uid]} for uid in sorted(actual_changed)],
        'footprint_changes': changes, 'all_156_full_footprints_match_declared_native_operations': True,
        'all_558_pad_UUIDs_preserved': True, 'actual_pad_records_match_planning_records_except_net_code': True,
        'all_other_source_native_objects_exact_except_net_code': len(set(old) & set(now)) - len(actual_changed),
        'native_refill_performed': True, 'logical_map_verified': True, 'paired_source_patch_applied': True,
        'fresh_netlist_ERC_DRC_and_all_physical_electrical_gates_pending': True,
        'electrical_acceptance_claimed': False, 'adoption_claimed': False}
    write(output / 'construction-provenance.json', receipt)
    require(sha(source / 'f722-heli.kicad_pcb') == source_hash, 'Source PCB changed during construction')
    print(json.dumps({k: receipt[k] for k in ('board_sha256', 'segments', 'vias', 'electrical_acceptance_claimed', 'adoption_claimed')}))


if __name__ == '__main__':
    try:
        main()
    except (ValueError, KeyError) as error:
        raise SystemExit(str(error)) from error
