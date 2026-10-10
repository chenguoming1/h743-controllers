#!/usr/bin/env python3
"""Exact C12-only translation plus one frozen coordinated routing scope.

Host --check-inputs is geometry-free. Native construction requires a new exact
owner lease. This successor never claims contact or electrical acceptance.
"""
from __future__ import annotations
import copy
import import_native7_incremental_v1 as base
from import_native7_incremental_v1 import *

BASE_SHA = 'cf783fd61fd229927f89aa2741d88500d598a445f306ab1031fca9ef49232653'
PLAN_SCHEMA = 'f722-native7-c12-translation-routing-plan/v1'
LEASE_SCHEMA = 'f722-native7-c12-translation-owner-lease/v1'
STAGE = 'c12_translate_construct_refill_export'
SCOPE_PATH = HERE / 'native7-c12-translation-import-scope-v1.json'
SCOPE_SHA = 'd61a12ef0d3ff88156c4a8f9df12cb74c21c9ca740dc850f17007773275fa87d'
PACKET_PATH = ROOT / 'ordinary-routing/tests/native13-access/native7-common-planning-packet-v1.json'
LEDGER_PATH = ROOT / 'ordinary-routing/tests/native13-access/native7-shared-restoration-obligations-v1.json'
POSE_HELPERS = {
    'recovered-native7/integrated-routing/verify_footprint_transforms.py': 'bcb10917d77b74aa3d18250e37de4b208cdc32fe68a3984fa5446ce52b369df8',
    'recovered-native7/ordinary-routing/tests/mpn-parity/apply_metadata_copy.py': '747aecf908d0503d7ef28a9f046fcaf3630d9cb196af1caf0f0bc35029c8c5dc',
}
C12_UUID = '66888241-01b1-4318-a456-84eb74a889fb'
PAD_IDS = {'556e7d4e-1f2d-4918-9c23-f3b2fe429a7a', '618eefa7-fbe0-4cd8-9143-bf32b70af2a1'}
KEEP = {'296bfec5-72b7-4194-9568-a88d79de25ed', '8a55abc3-716e-448f-887e-c4ef9f2907bd'}
EXTRA = {'97832e7d-4506-4ec6-bf89-d2db05e3cda8', 'fb8288a2-c699-4368-a7ab-e4e79f4d7fa4',
         'd7e5189c-e93c-4dd6-81a5-792b677fafb4', 'c8bef21f-ce0a-449d-b34b-a063ce5e7c32',
         '3d128062-54a3-4fd3-ab3d-818e4ec84e57', 'da1f25da-e0ad-4065-9e0c-44670c3de5fa'}
RETAINED = KEEP | {'d9731330-cda6-44f0-811a-9cdea7ea0676', '3a66a0d8-a4b0-4282-9936-fdae79b412fc'}


def bound_scope(native):
    require(sha(base.__file__) == BASE_SHA and sha(SCOPE_PATH) == SCOPE_SHA, 'Frozen importer/scope changed')
    for path, digest in POSE_HELPERS.items():
        require(sha(ROOT / path) == digest, 'Independent pose helper changed: ' + path)
    scope = read(SCOPE_PATH)
    require(scope['schema'] == 'f722-native7-c12-translation-import-scope/v1' and scope['source'] == SOURCE_BINDINGS,
            'Wrong C12 source scope')
    require(sha(PACKET_PATH) == scope['base_common_packet_sha256'] and sha(LEDGER_PATH) == scope['historical_ledger_sha256'],
            'Wrong common cut/terminal evidence')
    old = unique(native['objects'])
    common = set(read(PACKET_PATH)['removed_native_ids'])
    trial_pin = scope['coordinated_trial_scope']
    require(sha(ROOT / trial_pin['path']) == trial_pin['sha256'], 'Coordinated C12 trial scope changed')
    trial = read(ROOT / trial_pin['path'])
    require(trial['mode'] == trial_pin['mode'] == 'MISO_retained' and trial['additional_proposal_cut_ids'] == [] and
            trial['native7_sha256'] == SOURCE_BINDINGS['native_sha256'] and
            set(trial['common_cut_ids']) == common and set(trial['restore_common_cut_ids']) == KEEP and
            set(trial['additional_native_cut_ids']) == EXTRA and
            set(trial['retained_required_native_ids']) == RETAINED - KEEP and
            trial['all_four_complete_branches_required'] is True, 'Unexpected coordinated trial cut/keep scope')
    for pin in trial['source_files']:
        require(sha(ROOT / pin['path']) == pin['sha256'], 'Coordinated trial prerequisite changed: ' + pin['path'])
    proposal_path = ROOT / 'ordinary-routing/tests/native13-access/native7-coordinated-engineering-proposal-v1.json'
    common_ground = [dict(row, kind='track', logical_net='GND') for row in read(proposal_path)['proposed_common_routes']
                     if row['net'] == 'GND']
    require(scope['required_common_ground_recipes'] == common_ground and
            {r['name'] for r in common_ground} == {'recovered-U2-9-ground-0', 'recovered-U2-9-ground-1'},
            'Common source-bound ground restoration differs')
    require(set(scope['restored_common_cut_UUIDs']) == KEEP and KEEP <= common and
            set(scope['additional_removed_track_UUIDs']) == EXTRA and not EXTRA & common,
            'C12 common keep/extra-cut scope differs')
    expected = (common - KEEP) | EXTRA
    declared = unique(scope['expected_removed_record_hashes'])
    require(set(declared) == expected, 'Incomplete or extra coordinated removal identities')
    for uid, row in declared.items():
        require(row['full_record_sha256'] == record_sha(old[uid]) and old[uid]['kind'] in ('track', 'via', 'arc'),
                'Coordinated source record changed: ' + uid)
    retained = unique(scope['required_retained_record_hashes'])
    require(set(retained) == RETAINED and not RETAINED & expected, 'Required retained donor scope differs')
    require(all(row['full_record_sha256'] == record_sha(old[uid]) for uid, row in retained.items()), 'Retained donor changed')
    pose = scope['declared_footprint_transform']
    require(pose['reference'] == 'C12' and pose['footprint_uuid'] == C12_UUID and
            pose['before'] == [26.0625, 12, -90, 'F.Cu'] and pose['after'] == [26.3125, 12, -90, 'F.Cu'] and
            pose['flip_left_right'] is None, 'Only exact C12 +.25 mm X translation is permitted')
    footprints = unique(native['footprints'])
    fp = footprints[C12_UUID]
    require([*fp['xy'], fp['angle'], fp['side']] == pose['before'] and fp['ref'] == 'C12' and
            fp['value'] == '100nF / 16V / X7R' and fp['fpid'] == 'F722_Heli:C_0402_1005Metric' and
            record_sha(fp) == pose['source_footprint_record_sha256'], 'Wrong source C12 footprint')
    pads = unique(pose['source_pad_record_hashes'])
    require(set(pads) == PAD_IDS and {r['uuid'] for r in old.values() if r.get('ref') == 'C12'} == PAD_IDS,
            'Wrong C12 pad inventory')
    require(all(record_sha(old[uid]) == row['full_record_sha256'] for uid, row in pads.items()), 'Wrong C12 source pad')
    for netrow in read(LEDGER_PATH)['nets']:
        for group in netrow['source_terminal_components']:
            require(group and len(group) == len(set(group)) and
                    all(uid in old and old[uid]['net'] == netrow['net'] for uid in group), 'Stale original terminal group')
    group, = scope['additional_terminal_groups']
    require(group['net'] == '+3V3_IMU' and set(group['all_original_pad_UUIDs']) ==
            {uid for uid, r in old.items() if r['kind'] == 'pad' and r['net'] == '+3V3_IMU'}, 'Incomplete supply terminal group')
    evidence = group['source_group_evidence']
    require(sha(ROOT / evidence['path']) == evidence['sha256'], 'Supply source-group evidence changed')
    source_group = read(ROOT / evidence['path'])
    require(source_group['source_component_count'] == 1 and source_group['exclusive_R3_load_confirmed'] is True,
            'Supply source-group proof missing')
    for obligation in scope['restoration_obligations']:
        for terminal in obligation['terminals']:
            record = old[terminal['uuid']]
            require(record['net'] == obligation['net'] and terminal['source_full_record_sha256'] == record_sha(record),
                    'Restoration terminal identity mismatch')
            xy(terminal['xy'])
            if terminal['uuid'] in PAD_IDS:
                require(xy(terminal['xy']) == [xy(record['xy'])[0] + 250000, xy(record['xy'])[1]],
                        'Moved terminal does not follow exact C12 translation')
            elif record['kind'] in ('pad', 'via'):
                require(terminal['xy'] == record['xy'], 'Retained terminal position differs')
            else:
                require(terminal['xy'] in (record['start'], record['end']), 'Retained donor endpoint differs')
    required_widths = {'C12_U2_feed': ('U2_VDD_feed', .2), 'C12_C11_feed': ('C11_C12_feed', .2),
                       'C12_GND_return': ('C12_GND', .2), 'C12_R3_exclusive_leaf': ('R3_pullup', .127)}
    require({r['name'] for r in scope['restoration_obligations']} == set(required_widths), 'Missing restoration branch')
    for row in scope['restoration_obligations']:
        key, width = required_widths[row['name']]
        require(row['minimum_track_width_mm'] == trial['required_branch_widths_mm'][key] == width,
                'Restoration width obligation differs')
    return scope


def verify_recipe_obligations(plan, scope, native):
    """Endpoint/layer recipe graph only; explicitly not physical copper contact."""
    recipes = unique(plan['added_copper'], key='name')
    bindings = unique(plan['obligation_recipe_bindings'], key='name')
    required = unique(scope['restoration_obligations'], key='name')
    require(set(bindings) == set(required), 'Missing/extra C12 restoration recipe bindings')
    old, assigned = unique(native['objects']), set()
    for name, obligation in required.items():
        row = bindings[name]
        exact_keys(row, ['name', 'recipe_names'], 'obligation recipe binding')
        names = row['recipe_names']
        require(isinstance(names, list) and names and len(names) == len(set(names)) and set(names) <= set(recipes),
                'Missing/duplicate/unknown restoration recipes: ' + name)
        graph = {}
        def join(a, b):
            graph.setdefault(a, set()).add(b)
            graph.setdefault(b, set()).add(a)
        tracks = 0
        for recipe_name in names:
            recipe = recipes[recipe_name]
            require(recipe['net'] == obligation['net'], 'Wrong restoration recipe net')
            assigned.add(recipe_name)
            if recipe['kind'] == 'track':
                tracks += 1
                require(iu(recipe['width']) >= iu(obligation['minimum_track_width_mm']), 'Restoration track is too narrow')
                points = [(recipe['layer'], *xy(p)) for p in recipe['points']]
                for a, b in zip(points, points[1:]):
                    join(a, b)
            else:
                nodes = [(layer, *xy(recipe['xy'])) for layer in recipe['layers']]
                for node in nodes[1:]:
                    join(nodes[0], node)
        require(tracks > 0, 'Restoration needs complete track recipes')
        terminals = [{(layer, *xy(t['xy'])) for layer in old[t['uuid']]['copper']} for t in obligation['terminals']]
        starts = terminals[0] & set(graph)
        require(bool(starts), 'Restoration recipe omits its exact source endpoint')
        seen, todo = set(), [next(iter(starts))]
        while todo:
            node = todo.pop()
            if node not in seen:
                seen.add(node)
                todo.extend(graph[node] - seen)
        require(bool(seen & terminals[1]) and seen == set(graph), 'Disconnected or incomplete restoration recipe endpoint graph')
    common_ground = unique(scope['required_common_ground_recipes'], key='name')
    require(all(recipes.get(name) == row for name, row in common_ground.items()),
            'Missing/altered exact common U2.9 ground recipe')
    require(not set(common_ground) & assigned, 'Common ground recipe cannot replace a C12 obligation')
    require({r['name'] for r in recipes.values() if r['net'] in ('+3V3_IMU', 'GND')} <= assigned | set(common_ground),
            'Unassigned supply/return recipe outside C12 obligations')


def validate_plan(plan, native, logical):
    exact_keys(plan, ['schema', 'source', 'scope_contract_sha256', 'declared_footprint_transforms',
                      'removed_native_records', 'added_copper', 'obligation_recipe_bindings'], 'C12 plan')
    require(plan['schema'] == PLAN_SCHEMA and plan['source'] == SOURCE_BINDINGS and
            plan['scope_contract_sha256'] == SCOPE_SHA, 'Wrong C12 plan/source/scope')
    scope = bound_scope(native)
    require(plan['declared_footprint_transforms'] == [scope['declared_footprint_transform']], 'Undeclared or altered pose')
    ordinary = {key: plan[key] for key in ('source', 'removed_native_records', 'added_copper')}
    ordinary['schema'] = base.PLAN_SCHEMA
    result = base.validate_plan(ordinary, native, logical)
    require(set(result['removed']) == {r['uuid'] for r in scope['expected_removed_record_hashes']},
            'Plan must remove the exact coordinated source-record set')
    verify_recipe_obligations(plan, scope, native)
    result['scope'] = scope
    return result


def predict_translation(native):
    """Exact integer translation of existing native contours; no shape inference.

    Only used on real geometry inside the leased native stage. Tests use small
    fabricated records. Independent official export must match every byte field.
    """
    expected = copy.deepcopy(native)
    def point(p):
        x, y = xy(p)
        return [(x + 250000) / 1000000, y / 1000000]
    def polygons(rows):
        for row in rows:
            exact_keys(row, ['outer', 'holes'], 'native polygon')
            row['outer'] = [point(p) for p in row['outer']]
            row['holes'] = [[point(p) for p in hole] for hole in row['holes']]
    fps = unique(expected['footprints'])
    fp = fps[C12_UUID]
    fp['xy'] = point(fp['xy'])
    for graphic in fp['graphics']:
        for key in ('start', 'end', 'mid', 'center'):
            if key in graphic:
                graphic[key] = point(graphic[key])
        if 'polygons' in graphic:
            polygons(graphic['polygons'])
    for pad in expected['objects']:
        if pad['uuid'] not in PAD_IDS:
            continue
        require(pad['kind'] == 'pad' and pad['footprint_uuid'] == C12_UUID and pad['drill'] is None,
                'Only the two source undrilled C12 pads may translate')
        pad['xy'] = point(pad['xy'])
        for key in ('copper', 'inside'):
            for rows in pad[key].values():
                polygons(rows)
        for mask in pad['mask'].values():
            polygons(mask['polygons'])
    return expected


def verify_native(before, after, validation, additions):
    expected = predict_translation(before)
    result = base.verify_native(expected, after, dict(validation, old=unique(expected['objects'])), additions)
    changed = {uid for uid, row in unique(before['objects']).items()
               if uid in result[0] and row != result[0][uid]}
    require(changed == PAD_IDS, 'Exactly two declared C12 pads must change')
    old_fp, final_fp = unique(before['footprints']), unique(after['footprints'])
    require({uid for uid in old_fp if old_fp[uid] != final_fp[uid]} == {C12_UUID}, 'Exactly C12 must translate')
    require(len(old_fp) == 156 and sum(r['kind'] == 'pad' for r in before['objects']) == 558, 'Wrong source inventories')
    return result


def validate_lease(lease, plan_path, output, now=None):
    exact_keys(lease, ['schema', 'active', 'owner', 'lease_id', 'allowed_stages', 'source', 'plan_sha256',
                       'scope_contract_sha256', 'importer_sha256', 'candidate_directory', 'issued_utc', 'expires_utc'], 'C12 owner lease')
    require(lease['schema'] == LEASE_SCHEMA and lease['active'] is True and lease['allowed_stages'] == [STAGE],
            'No exact owner C12 native-job permission')
    require(lease['source'] == SOURCE_BINDINGS and lease['scope_contract_sha256'] == SCOPE_SHA and
            lease['plan_sha256'] == sha(plan_path) and lease['importer_sha256'] == sha(__file__) and
            lease['candidate_directory'] == str(output), 'C12 lease binding mismatch')
    require(all(isinstance(lease[k], str) and lease[k].strip() for k in ('owner', 'lease_id')), 'Missing owner/lease ID')
    issued, expires = [dt.datetime.fromisoformat(lease[k].replace('Z', '+00:00')) for k in ('issued_utc', 'expires_utc')]
    now = now or dt.datetime.now(dt.timezone.utc)
    require(issued.tzinfo is not None and expires.tzinfo is not None and
            issued <= now < expires and expires - issued <= dt.timedelta(hours=2), 'Expired/future/unbounded C12 lease')
    return lease


def move_c12(board, p):
    matches = [f for f in board.GetFootprints() if f.m_Uuid.AsString() == C12_UUID]
    require(len(matches) == 1, 'Missing/duplicate native C12 footprint')
    fp = matches[0]
    require(fp.GetReference() == 'C12' and fp.GetLayerName() == 'F.Cu' and
            fp.GetOrientationDegrees() == -90 and [fp.GetPosition().x, fp.GetPosition().y] == [26062500, 12000000],
            'Native C12 does not match declared starting pose')
    fp.SetPosition(p.VECTOR2I(26312500, 12000000))
    require(fp.GetOrientationDegrees() == -90 and fp.GetLayerName() == 'F.Cu', 'Native C12 orientation/side changed')


def original_nonpose_syntax(path, helper):
    """Full original non-route syntax except exactly C12 and existing zone fills."""
    tree = helper.parse(Path(path).read_text())
    def shape(node):
        if not isinstance(node, helper.Node):
            return node.value
        children = node.items
        if children[0].value == 'zone':
            children = [c for c in children if not isinstance(c, helper.Node) or
                        c.items[0].value not in ('filled_polygon', 'fill_segments')]
        return [shape(c) for c in children]
    structures, omitted = [], 0
    for node in tree.items:
        if isinstance(node, helper.Node):
            kind = node.items[0].value
            if kind in ('segment', 'via', 'arc'):
                continue  # Routes have their own exact equality proof.
            if kind == 'footprint' and helper.val(helper.child(node, 'uuid')) == C12_UUID:
                omitted += 1
                continue  # Full C12 structure is proved by the independent pose helper.
        structures.append(shape(node))
    require(omitted == 1, 'Exactly one source-bound C12 footprint must be excluded')
    return sorted(map(canonical, structures))


def verify_original_nonpose_syntax(source, predicted, helper):
    require(original_nonpose_syntax(source, helper) == original_nonpose_syntax(predicted, helper),
            'Pose prediction changed original non-C12 board syntax')


def independent_native_prediction(output, before, source_syntax, h, p, exporter):
    board = p.LoadBoard(str(SOURCE / 'f722-heli.kicad_pcb'))
    move_c12(board, p)
    path = output / 'pose-prediction.kicad_pcb'
    p.SaveBoard(str(path), board)
    predicted = exporter.export(path)  # Independent save/reload of source-only transform.
    verify_native(before, predicted, {'old': unique(before['objects']), 'removed': {}}, [])
    syntax = syntax_inventory(path, h)
    require(syntax['routes'] == source_syntax['routes'] and syntax['all_ids'] == source_syntax['all_ids'],
            'Pose-only prediction changed routes or UUID inventory')
    verify_original_nonpose_syntax(SOURCE / 'f722-heli.kicad_pcb', path, h)
    write(output / 'pose-prediction.native.json', predicted, compact=True)
    return predicted, syntax


def independent_pose_syntax_proof(board_path, output, scope):
    require(not sys.flags.optimize, 'Independent footprint verification requires assertions enabled')
    pose = scope['declared_footprint_transform']
    declaration = {'schema': 'f722-declared-footprint-transforms/v1',
                   'source_board_sha256': SOURCE_BINDINGS['board_sha256'], 'board_sha256': sha(board_path),
                   'changes': {'C12': {key: pose[key] for key in ('before', 'after', 'flip_left_right')}}}
    declaration_path = output / 'declared-footprint-transform.json'
    write(declaration_path, declaration)
    path = ROOT / 'recovered-native7/integrated-routing/verify_footprint_transforms.py'
    spec = importlib.util.spec_from_file_location('native7_independent_c12_pose_proof', path)
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    result = helper.verify(SOURCE / 'f722-heli.kicad_pcb', board_path, declaration_path)
    require(result['passed'] is True and result['exact_unchanged_footprints'] == 155, 'Independent full footprint syntax proof failed')
    write(output / 'footprint-transform-proof.json', result)
    return result


def construct(args, plan, before, logical, hardware, validation):
    require(args.output is not None and args.lease is not None, 'Native execution requires --output and explicit --lease')
    output = validate_output(args.output)
    plan_hash = sha(args.plan)
    lease_hash = sha(args.lease)
    importer_hash = sha(__file__)
    def gate():
        require(sha(args.plan) == plan_hash and sha(args.lease) == lease_hash and sha(__file__) == importer_hash, 'Selected inputs changed during job')
        bound_scope(before)
        return validate_lease(read(args.lease), args.plan, output)
    lease = gate()
    for name, expected in RUNTIME_FILES.items():
        require(sha(RUNTIME / name) == expected, 'Pinned official runtime changed: ' + name)
    require(Path(os.environ.get('KICAD_CONFIG_HOME', '/nonexistent')).resolve() == RUNTIME / 'config', 'Use pinned kicad10-runtime/python wrapper')
    h = parser_helper()
    source_syntax = syntax_inventory(SOURCE / 'f722-heli.kicad_pcb', h)
    additions = prepare_additions(plan, plan_hash, source_syntax)
    # Every host and lease gate precedes importing pcbnew or creating output.
    import pcbnew as p
    require(p.Version() == '10.0.6' and p.GetBuildVersion() == '10.0.6+dfsg-1', 'Wrong native runtime')
    require(p.VIATYPE_THROUGH == 4, 'Unexpected native through-via enum')
    sys.path.insert(0, str(ROOT / 'recovered-native7/ordinary-routing/native-tools'))
    import export_native_copper as exporter
    gate()
    output.mkdir(parents=True, exist_ok=False)
    for name, expected in hardware.items():
        target = output / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(SOURCE / name, target)
        require(sha(target) == expected, 'Copied hardware changed: ' + name)
    shutil.copy2(args.plan, output / 'selected-plan.json')
    shutil.copy2(args.lease, output / 'owner-lease-at-start.json')
    shutil.copy2(__file__, output / 'importer.used.py')
    write(output / 'construction-start.json', {'status': 'STARTED_NOT_ACCEPTED', 'source': SOURCE_BINDINGS,
          'plan_sha256': plan_hash, 'acceptance_claimed': False})
    predicted, predicted_syntax = independent_native_prediction(output, before, source_syntax, h, p, exporter)
    gate()
    board_path = output / 'f722-heli.kicad_pcb'
    board = p.LoadBoard(str(board_path))
    move_c12(board, p)
    native_tracks = {t.m_Uuid.AsString(): t for t in board.GetTracks()}
    require(set(native_tracks) == set(source_syntax['routes']), 'Native/syntax source route inventory differs')
    for uid in validation['removed']:
        require(uid in native_tracks, 'Removal is not a native route object')
        board.Remove(native_tracks[uid])
    point = lambda coordinates: p.VECTOR2I(*xy(coordinates))
    held = []
    for addition in additions:
        recipe, index = addition['recipe'], addition['segment_index']
        if recipe['kind'] == 'track':
            item = p.PCB_TRACK(board)
            item.SetLayer(board.GetLayerID(recipe['layer']))
            item.SetWidth(iu(recipe['width']))
            item.SetStart(point(recipe['points'][index]))
            item.SetEnd(point(recipe['points'][index + 1]))
        else:
            item = p.PCB_VIA(board)
            item.SetPosition(point(recipe['xy']))
            item.SetWidth(450000)
            item.SetDrill(200000)
            item.SetViaType(p.VIATYPE_THROUGH)
            item.SetLayerPair(p.F_Cu, p.B_Cu)
            item.SetFrontTentingMode(p.TENTING_MODE_TENTED)
            item.SetBackTentingMode(p.TENTING_MODE_TENTED)
        net = board.FindNet(recipe['net'])
        require(net is not None and net.GetNetname() == recipe['net'], 'Exact source net missing')
        item.SetUuid(p.KIID(addition['uuid']))
        item.SetNet(net)
        board.Add(item)
        held.append(item)
        addition['expected_native_record'] = expected_new_record(addition, item, board, p, exporter)
    p.SaveBoard(str(board_path), board)
    gate()
    board = p.LoadBoard(str(board_path))
    manager = p.GetSettingsManager()
    project_path = output / 'f722-heli.kicad_pro'
    require(manager.LoadProject(str(project_path)), 'Cannot load copied paired project')
    board.SetProject(manager.GetProject(str(project_path)))
    board.SynchronizeNetsAndNetClasses(False)
    board.BuildConnectivity()
    require(p.ZONE_FILLER(board).Fill(board.Zones()), 'Native refill failed')
    p.SaveBoard(str(board_path), board)
    gate()
    after = exporter.export(board_path)
    # Persist exact export even when subsequent verification fails; no approximation.
    write(output / 'f722-heli.native.json', after, compact=True)
    now, fill_changes = verify_native(before, after, validation, additions)
    actual_syntax = syntax_inventory(board_path, h)
    require(predicted_syntax['structures'] == actual_syntax['structures'], 'Non-route syntax differs from exact independent C12 prediction')
    pose_proof = independent_pose_syntax_proof(board_path, output, validation['scope'])
    require(set(source_syntax['routes']) - set(actual_syntax['routes']) == set(validation['removed']), 'Syntax removal inventory differs')
    require(set(actual_syntax['routes']) - set(source_syntax['routes']) == {a['uuid'] for a in additions}, 'Syntax addition inventory differs')
    for uid in set(source_syntax['routes']) & set(actual_syntax['routes']):
        require(source_syntax['routes'][uid] == actual_syntax['routes'][uid], 'Retained full route syntax changed: ' + uid)
    for name, expected in hardware.items():
        require(name == 'f722-heli.kicad_pcb' or sha(output / name) == expected, 'Paired hardware identity changed: ' + name)
    new_logical = {uid: net for uid, net in logical.items() if uid not in validation['removed']}
    new_logical.update({a['uuid']: a['recipe']['logical_net'] for a in additions})
    write(output / 'f722-heli.logical-route-map.json', {'schema': 'f722-logical-route-map/v1',
          'board_sha256': sha(board_path), 'source_sha256': SOURCE_BINDINGS['board_sha256'], 'logical_route_map': new_logical})
    source_inputs()  # Recheck all 61 inputs, native, logical evidence, and helpers.
    gate()
    receipt = {'schema': 'f722-native7-c12-translation-import-receipt/v1', 'status': 'CONSTRUCTION_VERIFIED_NOT_ACCEPTED',
        'source': SOURCE_BINDINGS, 'board_sha256': sha(board_path), 'native_sha256': sha(output / 'f722-heli.native.json'),
        'plan_sha256': plan_hash, 'importer_sha256': importer_hash, 'lease_sha256': lease_hash, 'lease_id': lease['lease_id'],
        'stage': STAGE, 'native_build': p.GetBuildVersion(), 'hardware_input_count': len(hardware),
        'hardware_files': [{'path': name, 'source_sha256': expected, 'candidate_sha256': sha(output / name)}
                           for name, expected in sorted(hardware.items())],
        'paired_non_board_inputs_byte_identical': True,
        'exact_unchanged_footprints': 155, 'exact_predicted_transformed_footprints': 1,
        'exact_unchanged_pads': 556, 'exact_predicted_transformed_pads': 2,
        'scope_contract_sha256': SCOPE_SHA, 'coordinated_trial_scope': validation['scope']['coordinated_trial_scope'],
        'declared_footprint_transforms': plan['declared_footprint_transforms'],
        'pose_prediction_board_sha256': sha(output / 'pose-prediction.kicad_pcb'),
        'pose_prediction_native_sha256': sha(output / 'pose-prediction.native.json'),
        'footprint_transform_proof_sha256': sha(output / 'footprint-transform-proof.json'),
        'declared_footprint_transform_sha256': sha(output / 'declared-footprint-transform.json'),
        'independent_pose_helpers': POSE_HELPERS,
        'expected_transformed_pad_records': [r for r in predicted['objects'] if r['uuid'] in PAD_IDS],
        'expected_transformed_footprint_record': unique(predicted['footprints'])[C12_UUID],
        'restoration_obligations': validation['scope']['restoration_obligations'],
        'required_common_ground_recipes': validation['scope']['required_common_ground_recipes'],
        'additional_terminal_groups': validation['scope']['additional_terminal_groups'],
        'historical_terminal_ledger_sha256': validation['scope']['historical_ledger_sha256'],
        'obligation_recipe_bindings': plan['obligation_recipe_bindings'],
        'recipe_endpoint_graph_checked_only': True, 'full_native_contact_restorations_proved': False,
        'retained_full_native_records_unchanged': len(set(validation['old']) & set(now)) - 2,
        'retained_full_route_syntax_unchanged': True, 'non_route_board_syntax_matches_exact_pose_prediction_except_zone_fills': True,
        'removed_native_records': list(validation['removed'].values()),
        'recipe_to_native_UUIDs': [{'name': a['recipe']['name'], 'segment_index': a['segment_index'], 'uuid': a['uuid'],
                                  'full_record_sha256': record_sha(now[a['uuid']])} for a in additions],
        'added_native_records': [now[a['uuid']] for a in additions], 'segments': validation['segments'], 'vias': validation['vias'],
        'native_refill_performed': True, 'zone_outlines_and_metadata_unchanged': True, 'changed_zone_fills': fill_changes,
        'all_source_inputs_unchanged': True, 'DRC_ERC_parity_physical_electrical_checks_performed': False,
        'acceptance_claimed': False, 'adoption_claimed': False}
    write(output / 'construction-provenance.json', receipt)
    return {k: receipt[k] for k in ('status', 'board_sha256', 'segments', 'vias', 'changed_zone_fills', 'acceptance_claimed')}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan', type=Path, required=True)
    parser.add_argument('--check-inputs', action='store_true')
    parser.add_argument('--output', type=Path)
    parser.add_argument('--lease', type=Path)
    args = parser.parse_args()
    before, logical, hardware = source_inputs()
    plan = read(args.plan)
    validation = validate_plan(plan, before, logical)
    if args.check_inputs:
        require(args.output is None and args.lease is None, 'Pure validation does not use output or lease')
        syntax = syntax_inventory(SOURCE / 'f722-heli.kicad_pcb', parser_helper())
        prepare_additions(plan, sha(args.plan), syntax)
        result = {'input_validation_passed': True, 'source': SOURCE_BINDINGS, 'plan_sha256': sha(args.plan),
                  'scope_contract_sha256': SCOPE_SHA, 'pose': 'C12 +.25 mm X only',
                  'recipe_endpoint_graph_checked_only': True, 'native_contact_acceptance_proved': False,
                  'removals': len(validation['removed']), 'segments': validation['segments'], 'vias': validation['vias'],
                  'hardware_input_count': len(hardware), 'native_work_performed': False, 'candidate_created': False,
                  'acceptance_claimed': False}
    else:
        result = construct(args, plan, before, logical, hardware, validation)
    print(json.dumps(result, allow_nan=False))


if __name__ == '__main__':
    try:
        main()
    except (ValueError, KeyError, TypeError, OSError) as error:
        raise SystemExit(str(error)) from error
