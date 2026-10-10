"""Pure source/transaction validation and exact paired-source patching. No pcbnew import."""
from __future__ import annotations

import copy
import datetime as dt
import hashlib
import importlib.util
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
DEFAULT_SPEC = HERE / 'joint-native11-import-spec-v1.json'


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def write(path, value):
    path = Path(path)
    require(not path.exists(), f'Refusing to overwrite receipt: {path}')
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')


def physical(record):
    return {k: v for k, v in record.items() if k != 'net_code'}


def validate_bindings(spec):
    for name, expected in spec['source_bindings'].items():
        require(sha(ROOT / name) == expected, f'Source binding changed: {name}')
    for name, expected in spec['helper_bindings'].items():
        require(sha(ROOT / name) == expected, f'Helper binding changed: {name}')
    prior = spec['historical_metadata_plan']
    require(sha(ROOT / prior['path']) == prior['sha256'], 'Historical plan changed')
    source = ROOT / spec['source_project_directory']
    native = read(source / 'f722-heli.native.json')
    require(sha(source / 'f722-heli.kicad_pcb') == spec['source_board_sha256'], 'Wrong source PCB')
    require(sha(source / 'f722-heli.native.json') == spec['source_native_sha256'], 'Wrong source native export')
    require(native['board_sha256'] == spec['source_board_sha256'], 'Stale source native export')
    require(len(native['footprints']) == 156, 'Source footprint inventory is not 156')
    require(sum(o['kind'] == 'pad' for o in native['objects']) == 558, 'Source pad inventory is not 558')
    for row in read(source / 'project-input-preservation.json')['files']:
        require(sha(source / row['path']) == row['sha256'], f'Project input changed: {row["path"]}')
    return source, native


def unique(records, key='uuid'):
    result = {r[key]: r for r in records}
    require(len(result) == len(records), f'Duplicate {key} in records')
    return result


def numbers(values):
    return all(isinstance(x, (float, int)) and not isinstance(x, bool) and math.isfinite(x) for x in values)


def validate_transaction(transaction, native, spec):
    """Reject missing pads before loading pcbnew or creating any candidate directory."""
    t = transaction
    require(t['schema'] == 'f722-recorded-joint-planning-transaction/v1', 'Unsupported transaction')
    require(t['source_board_sha256'] == spec['source_board_sha256'], 'Transaction source PCB mismatch')
    require(t['source_native_sha256'] == spec['source_native_sha256'], 'Transaction native hash mismatch')
    old = unique(native['objects'])
    removed = unique(t['removed_native_records'])
    missing = sorted(o['key'] for o in removed.values() if o['kind'] == 'pad')
    require(t.get('complete_pad_inventory') is True and not t.get('missing_actual_pad_keys') and not missing,
            'Incomplete pad inventory; missing actual pads: ' + ', '.join(sorted(set(missing + t.get('missing_actual_pad_keys', [])))))
    require(t.get('constructor_argument_capture') is True, 'No original constructor arguments')
    require(t.get('all_selected_new_shapes_match_recorded_constructor_bytes') is True, 'Unverified recorded constructor geometry')
    retained = t['retained_native_ids']
    require(len(set(retained)) == len(retained), 'Duplicate retained native ID')
    require(set(retained).isdisjoint(removed), 'Retained/cut UUID overlap')
    require(set(retained) | set(removed) == set(old), 'Source object inventory is incomplete or contains foreign UUIDs')
    for uid, row in removed.items():
        require(row == old[uid] and row['kind'] in ('track', 'via', 'arc'), f'Unapproved source removal: {uid}')
    changed = {}
    net_changes = {}
    # Geometry fields may change only as a full-footprint pose operation, proved natively later.
    mutable = {'xy', 'angle', 'copper', 'inside', 'mask', 'all_layers', 'shape_by_layer', 'drill', 'barrel_layers', 'net', 'net_code'}
    for pair in t['changed_pad_records']:
        before, after = pair['before'], pair['after']
        uid = before['uuid']
        require(uid not in changed and uid in retained, f'Duplicate or absent changed pad: {uid}')
        require(before == old[uid] and before['kind'] == after['kind'] == 'pad', f'Pad source mismatch: {uid}')
        require(set(before) == set(after), f'Pad record fields changed: {before["key"]}')
        require({k: v for k, v in before.items() if k not in mutable} ==
                {k: v for k, v in after.items() if k not in mutable}, f'Package/pad identity change: {before["key"]}')
        require(before['ref'] in spec['allowed_changed_footprint_refs'], f'Unapproved footprint change: {before["ref"]}')
        if before['net'] != after['net']:
            net_changes[before['key']] = {'uuid': uid, 'before': before['net'], 'after': after['net']}
        changed[uid] = after
    require(net_changes == spec['approved_pad_net_changes'], 'Net edits differ from exact U15.9 TX / U15.10 RX approval')
    names = set()
    total_segments = total_vias = 0
    nets = {o['net'] for o in old.values()}
    for row in t['added_copper']:
        recipe, record = row['recipe'], row['selected_object_record']
        name = recipe['name']
        require(name not in names and name not in old, f'Duplicate or source-overlapping recipe name: {name}')
        names.add(name)
        require(record['uuid'] == name and record['net'] == recipe['net'] and record['kind'] == recipe['kind'], f'Recipe identity mismatch: {name}')
        require(recipe['net'] in nets and not recipe['net'].startswith('unconnected-'), f'Unapproved copper net: {name}')
        if recipe['kind'] == 'track':
            require(set(recipe) == {'kind', 'name', 'net', 'layer', 'points', 'width'}, f'Unexpected track fields: {name}')
            points = recipe['points']
            require(len(points) >= 2 and all(len(p) == 2 and numbers(p) for p in points), f'Invalid polyline: {name}')
            require(all(a != b for a, b in zip(points, points[1:])), f'Zero-length segment: {name}')
            require(numbers([recipe['width']]) and recipe['width'] >= .127, f'Invalid width: {name}')
            require(recipe['layer'] in native['copper_layers'], f'Unknown copper layer: {name}')
            require(record['start'] == points[0] and record['end'] == points[-1] and record['width'] == recipe['width'], f'Polyline end/width mismatch: {name}')
            total_segments += len(points) - 1
        elif recipe['kind'] == 'via':
            require(set(recipe) == {'kind', 'name', 'net', 'xy', 'diameter', 'drill', 'layers', 'tented_front', 'tented_back'}, f'Unexpected via fields: {name}')
            require(len(recipe['xy']) == 2 and numbers(recipe['xy']), f'Invalid via position: {name}')
            require(recipe['diameter'] == .45 and recipe['drill'] == .20 and recipe['layers'] == native['copper_layers'] and
                    recipe['tented_front'] is True and recipe['tented_back'] is True, f'Unapproved via construction: {name}')
            total_vias += 1
        else:
            raise ValueError(f'Unsupported added copper kind: {recipe["kind"]}')
    require(len({o['uuid'] for o in old.values() if o['kind'] == 'pad'} & set(retained)) == 558, 'Not all 558 original pads survive')
    return {'old': old, 'removed': removed, 'changed': changed, 'segments': total_segments, 'vias': total_vias}


def validate_poses(ledger, transaction_path, native, validation, spec):
    require(ledger['schema'] == 'f722-joint-final-poses/v1' and ledger.get('complete') is True, 'Final pose ledger is incomplete')
    require(ledger['source_board_sha256'] == spec['source_board_sha256'] and ledger['transaction_sha256'] == sha(transaction_path), 'Pose ledger binding mismatch')
    fps = {f['ref']: f for f in native['footprints']}
    changed_refs = {o['ref'] for o in validation['changed'].values()}
    changes = ledger['changes']
    require(set(changes) == changed_refs, 'Declared poses must cover exactly the changed-pad footprints')
    require(set(changes) <= set(spec['allowed_changed_footprint_refs']), 'Unapproved pose reference')
    for ref, change in changes.items():
        require(set(change) == {'before', 'after', 'flip_left_right'}, f'Unexpected pose declaration fields: {ref}')
        before, after = change['before'], change['after']
        f = fps[ref]
        require(before == f['xy'] + [f['angle'], f['side']], f'Source pose mismatch: {ref}')
        require(len(after) == 4 and numbers(after[:3]) and after[2] % 90 == 0 and after[3] in ('F.Cu', 'B.Cu'), f'Invalid final pose: {ref}')
        require((change['flip_left_right'] is None) if before[3] == after[3] else type(change['flip_left_right']) is bool,
                f'Explicit flip direction required only for side changes: {ref}')
        require(before != after, f'No-op pose: {ref}')
        source_ids = {o['uuid'] for o in native['objects'] if o.get('ref') == ref}
        require(source_ids <= set(validation['changed']), f'Final pose lacks complete pad records: {ref}')
    require(changes['U15']['after'] == spec['physical_selection']['approved_U15_pose'], 'U15 final pose is not approved F(25.5,17.6),0')
    return changes


def validate_lease(path, stage, transaction_path, output, spec):
    """Owner supplies this file only after acquiring the serialized native-job lease."""
    lease = read(path)
    require(lease['schema'] == 'f722-owner-native-lease/v1' and lease.get('active') is True, 'No active owner native lease')
    require(stage in lease['allowed_stages'], f'Lease does not allow {stage}')
    require(lease['source_board_sha256'] == spec['source_board_sha256'] and lease['transaction_sha256'] == sha(transaction_path), 'Lease source/transaction mismatch')
    require(Path(lease['candidate_directory']).resolve() == Path(output).resolve(), 'Lease candidate directory mismatch')
    require(bool(lease.get('owner')) and bool(lease.get('lease_id')), 'Lease has no owner/ID')
    expiry = dt.datetime.fromisoformat(lease['expires_utc'].replace('Z', '+00:00'))
    require(expiry.tzinfo is not None and dt.datetime.now(dt.timezone.utc) < expiry, 'Native lease expired')
    runtime = Path(spec['runtime']['directory'])
    for name, expected in spec['runtime']['pinned_files'].items():
        require(sha(runtime / name) == expected, f'Pinned official runtime file changed: {name}')
    return lease


def parser_helper(spec):
    path = ROOT / 'repo/f722-heli/layout-revision/scripts/patch_metadata.py'
    require(sha(path) == spec['helper_bindings'][str(path.relative_to(ROOT))], 'S-expression helper changed')
    module_spec = importlib.util.spec_from_file_location('joint11_patch_metadata_helper', path)
    module = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(module)
    return module


def prepare_paired_texts(source, spec):
    """Return patched text and structural proof entirely in memory; never run historical patch_io."""
    h = parser_helper(spec)
    pairing, variant = spec['paired_schematic'], spec['symbol_variant']
    sch_path = source / pairing['target_relative_path']
    lib_path = source / variant['candidate_library_relative_path']
    sch, lib = sch_path.read_text(), lib_path.read_text()
    tree, libtree = h.parse(sch), h.parse(lib)
    instance, snapshot = h.symbol_snapshot(tree, 'U15')
    require(snapshot['uuid'] == pairing['symbol_instance_uuid'] and snapshot['at'] == pairing['symbol_instance_at'] and snapshot['properties'] == pairing['symbol_properties_unchanged'], 'U15 schematic identity mismatch')
    require({h.val(pin): h.val(h.child(pin, 'uuid')) for pin in h.children(instance, 'pin')} == pairing['preserved_pin_instance_uuids'], 'U15 pin UUID mismatch')
    embedded = h.child(tree, 'lib_symbols')

    def derive(container, old_name, new_name, expected_text):
        symbols = h.children(container, 'symbol')
        require(new_name not in [h.val(s) for s in symbols], 'Variant already exists')
        original = [s for s in symbols if h.val(s) == old_name]
        require(len(original) == 1, 'Missing original symbol')
        expected = copy.deepcopy(original[0])
        expected.items[1].value = new_name
        found = set()
        for nested in h.children(expected, 'symbol'):
            old_nested = h.val(nested)
            require(old_nested in variant['nested_symbol_names'], 'Unexpected nested symbol')
            nested.items[1].value = variant['nested_symbol_names'][old_nested]
            for pin in h.children(nested, 'pin'):
                num = h.val(h.child(pin, 'number'))
                if num in ('9', '10'):
                    require(pin.items[1].value == 'no_connect', f'Unexpected NC pin type: {num}')
                    pin.items[1].value = 'passive'
                    found.add(num)
        require(found == {'9', '10'}, 'Variant NC pins incomplete')
        candidate = h.parse(expected_text)
        require(h.shape(expected) == h.shape(candidate), 'Variant changes more than its name and NC9/10 electrical types')
        return candidate

    embedded_variant = derive(embedded, pairing['lib_id_before'], pairing['lib_id_after'], variant['expected_embedded_variant_sexpr'])
    library_variant = derive(libtree, variant['derive_from'], variant['new_name'], variant['expected_library_variant_sexpr'])
    libid = h.child(instance, 'lib_id').items[1]
    require(libid.value == pairing['lib_id_before'], 'U15 already has a different variant')
    edits = [(libid.start, libid.end, json.dumps(pairing['lib_id_after']))]
    libid.value = pairing['lib_id_after']
    edits.append((embedded.end - 1, embedded.end - 1, '\n' + variant['expected_embedded_variant_sexpr'] + '\n'))
    embedded.items.append(embedded_variant)
    additions = []
    removed = []
    for row in pairing['NC_routing_node_changes']:
        nc = row['remove_no_connect']
        nodes = [n for n in h.children(tree, 'no_connect') if h.val(h.child(n, 'uuid')) == nc['uuid']]
        require(len(nodes) == 1 and h.shape(nodes[0]) == nc['shape'], 'Unexpected NC mark')
        node = nodes[0]
        require(sch[node.start:node.end] == nc['exact_source'], 'NC source bytes changed')
        edits.append((node.start, node.end, ''))
        tree.items.remove(node)
        removed.append(nc['uuid'])
        for field in ('add_wire', 'add_global_label'):
            addition = row[field]
            require(addition['uuid'] not in sch and addition['uuid'] not in lib, 'New UUID collides with source')
            text = addition['exact_sexpr']
            node = h.parse(text)
            require(h.shape(node) == addition['shape'], 'Paired node text and declared shape differ')
            additions.append(text)
            tree.items.append(node)
    edits.append((tree.end - 1, tree.end - 1, '\n' + '\n'.join(additions) + '\n'))
    new_sch = h.replace(sch, edits)
    new_lib = h.replace(lib, [(libtree.end - 1, libtree.end - 1, '\n' + variant['expected_library_variant_sexpr'] + '\n')])
    libtree.items.append(library_variant)
    require(h.shape(tree) == h.shape(h.parse(new_sch)), 'Unplanned schematic structural change')
    require(h.shape(libtree) == h.shape(h.parse(new_lib)), 'Unplanned library structural change')
    for key, expected in spec['exact_patch_counts']['expected_io_ports_node_counts'].items():
        require(len(h.children(tree, key)) == expected, f'Wrong final schematic node count: {key}')
    return {pairing['target_relative_path']: new_sch, variant['candidate_library_relative_path']: new_lib}, {
        'schema': 'f722-joint-paired-source-proof/v1',
        'changed_instance': 'U15', 'instance_and_all_pin_UUIDs_preserved': True,
        'removed_no_connect_UUIDs': removed, 'added_wires': 2, 'added_global_labels': 2,
        'original_library_symbols_preserved': True,
        'new_variant': variant['new_name'], 'only_pin_type_changes': {'9': 'passive', '10': 'passive'},
        'manufacturer_NC_names_preserved': True, 'all_existing_bonded_pin_wires_labels_preserved': True,
        'exact_schematic_and_library_structural_delta_verified': True,
        'native_or_ERC_run': False, 'acceptance_claimed': False,
    }
