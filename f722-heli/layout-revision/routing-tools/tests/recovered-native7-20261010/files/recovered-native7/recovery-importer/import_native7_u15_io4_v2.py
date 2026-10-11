#!/usr/bin/env python3
"""Exact native7-only U15 IO4 constructor. Host preparation imports no CAD/geometry.

Eleven source cuts, four pad-net changes, fixed poses/pads and paired metadata.
Native execution requires an owner-issued exact-plan lease. No route acceptance.
"""
from __future__ import annotations

import argparse
import copy
import datetime as dt
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
DEPENDENCIES = {
    'import_native7_incremental_v1.py': 'cf783fd61fd229927f89aa2741d88500d598a445f306ab1031fca9ef49232653',
    'prepare_native7_u15_io4_pair_v1.py': '2833c8abd0e923bbfea0cc706661457baecb2e5eda1c2f9b98956f1ae0cf95f2',
}


def module(name, filename):
    import hashlib
    path = HERE / filename
    if hashlib.sha256(path.read_bytes()).hexdigest() != DEPENDENCIES[filename]:
        raise ValueError('Pinned dependency changed: ' + filename)
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


g = module('io4_ordinary_constructor', 'import_native7_incremental_v1.py')
p = module('io4_paired_semantics', 'prepare_native7_u15_io4_pair_v1.py')
require, sha, read, write = g.require, g.sha, g.read, g.write
SOURCE_BINDINGS = g.SOURCE_BINDINGS
SOURCE_PLAN_SCHEMA = 'f722-native7-U15-IO4-native-only-source-plan/v2'
PLAN_SCHEMA = 'f722-native7-U15-IO4-routing-plan/v2'
LEASE_SCHEMA = 'f722-native7-U15-IO4-owner-job-lease/v2'
STAGE = 'io4_paired_construct_refill_export'
SOURCE_PLAN_PATH = HERE / 'native7-U15-IO4-native-only-source-plan-v2.json'
CUT_SCOPE_PATH = ROOT / 'recovered-native7/recovery-C/native7-IO4-native-only-source-scope-v2.json'
CUT_SCOPE_SHA256 = '815df90a2ae84d774acc993b100d110405db7b3d4e9a5f965450943cc4aed487'
# The exact eleven-cut scope failed joint first-barrel capacity. Preserve this
# sealed constructor preparation; a reviewed source-bound successor is required.
NATIVE_EXECUTION_ENABLED = False
EXACT_CUT_IDS = {
    '00d3d778-abd5-4fa9-8b8f-9877e7b83803', '0704cc1e-3f63-51e7-b36b-26e4c9a347e5',
    '6e64820c-b464-5142-a228-ebb74be4b044', '7e53c88f-9a87-5ba3-9c32-455d9649a9f5',
    '84864ccd-ac78-5d94-bbdd-daebc37d1ceb', '8f22baac-a8ff-4219-8c6b-8d5695979bc7',
    '97282ff5-d6b5-415f-a3c4-0390df70f0ea', 'a08299df-6002-52fd-8f9e-27b83956263e',
    'bcf4a808-4cd6-5541-8d5e-f9545c5dc1a2', 'c577b646-60c8-5101-b044-be71979ecce8',
    'f30237b0-7063-45c1-947a-2b6d75ac6f88',
}
RETIRED_NETS = ['unconnected-(U15-IO4-Pad5)', 'unconnected-(U15-NC6-Pad6)']
NEW_NETS = ['unconnected-(U15-IO1-Pad1)', 'unconnected-(U15-NC10-Pad10)']
ROLES = {'upstream': p.RX, 'downstream': p.RX, 'ground': 'GND', 'hold': 'FLASH_HOLD_N'}
CLI_FILES = {'kicad-cli': '649ec77520a638c28750bb518ba706cd8c5b6a79cb7667f45e8e6ec4a5b65568',
             'root/usr/bin/kicad-cli': '8d0d9b2d13840b9aeb0aba900bcb9a25ad57cc883d8e17bdf354b4f3094a77f1'}


def semantic_inputs():
    raw = {p.SRC + '/' + name: (g.SOURCE / name).read_bytes()
           for name in ['io-ports.kicad_sch', 'library/F722_Heli.kicad_sym']}
    for path in [p.CP + '/evidence/paired.net'] + [p.CP + '/evidence/contracts/joint-native11-' + kind + '-contracts-v1.json' for kind in ['candidate', 'actual_io']]:
        require(sha(ROOT / path) == p.BOUND[path], 'Paired semantic source changed: ' + path)
        raw[path] = (ROOT / path).read_bytes()
    return raw, g.parser_helper()


def derive_source_plan(native=None, hardware=None):
    if native is None:
        native, _, hardware = g.source_inputs()
    raw, parser = semantic_inputs()
    preview, operations, symbol = p.metadata_preview(raw, parser)
    require(sha(CUT_SCOPE_PATH) == CUT_SCOPE_SHA256, 'Exact eleven-cut source scope changed')
    scope = read(CUT_SCOPE_PATH)
    require(scope['source']['board_sha256'] == SOURCE_BINDINGS['board_sha256'] and
            scope['source']['native_sha256'] == SOURCE_BINDINGS['native_sha256'], 'Cut scope source differs')
    objects = g.unique(native['objects'])
    cuts = g.unique(scope['inventory']['removed_native_records'])
    require(set(cuts) == EXACT_CUT_IDS, 'Only exact eleven native7 cuts are admitted')
    require(all(row == objects[uid] for uid, row in cuts.items()), 'Eleven-cut full source records differ')
    require(sorted(row['net'] for row in cuts.values()) == sorted([p.RX] * 4 + ['GND'] * 3 + ['FLASH_HOLD_N'] * 4), 'Exact cut net inventory')
    delta = []
    for pin, name in p.PIN_NETS.items():
        row = objects[p.PINS[pin]]
        require(row['key'] == 'U15.' + pin and row['number'] == pin, 'Physical U15 pin identity')
        delta.append({'uuid': row['uuid'], 'key': row['key'], 'before_net': row['net'],
                      'after_net': name, 'source_record_sha256': g.record_sha(row)})
    for name in RETIRED_NETS:
        members = [o for o in native['objects'] if o['net'] == name]
        require(len(members) == 1 and members[0]['uuid'] in p.PINS.values(), 'Retired net is not a singleton unused pad')
    declared = {r['before']['uuid']: r for r in scope['inventory']['pad_net_delta']}
    require(set(declared) == set(p.PINS.values()), 'C scope four-pad inventory differs')
    for row in delta:
        external = declared[row['uuid']]
        require(external['before'] == objects[row['uuid']], 'C scope source pad differs')
        expected = copy.deepcopy(external['before'])
        expected['net'] = row['after_net']
        # C's route model is semantic only; numeric codes are allocated by native export.
        actual = copy.deepcopy(external['after'])
        expected.pop('net_code', None); actual.pop('net_code', None)
        require(expected == actual, 'C scope changed pad geometry or an undeclared semantic field')
    net_source = raw[p.CP + '/evidence/paired.net']
    nets = p.expected_netlist(net_source)
    contracts = []
    for kind in ['candidate', 'actual_io']:
        path = p.CP + '/evidence/contracts/joint-native11-' + kind + '-contracts-v1.json'
        old = json.loads(raw[path]); checks = copy.deepcopy(old['checks'])
        hits = [c for c in checks if c['id'] == 'published-06']
        require(len(hits) == 1 and hits[0]['clamp'] == 'U15.1', 'Source RX contract identity')
        hits[0]['clamp'] = 'U15.5'
        contracts.append({'kind': kind, 'source_path': path, 'source_sha256': p.BOUND[path], 'checks': checks})
    plan = {'schema': SOURCE_PLAN_SCHEMA, 'status': 'SOURCE_ONLY_NO_ROUTING_SELECTION_OR_NATIVE_EXECUTION',
        'source': SOURCE_BINDINGS, 'paired_hardware_count': len(hardware), 'hardware_inventory_sha256': g.record_sha(hardware),
        'cut_scope': {'path': str(CUT_SCOPE_PATH.relative_to(ROOT)), 'sha256': CUT_SCOPE_SHA256},
        'removed_native_records': [{'record': cuts[uid], 'full_record_sha256': g.record_sha(cuts[uid])} for uid in sorted(cuts)],
        'pad_net_delta': delta, 'schematic_operations': operations,
        'metadata_outputs': {name: {'before_sha256': p.sha(raw[p.SRC + '/' + name]), 'after_sha256': p.sha(text.encode())} for name, text in preview.items()},
        'netlist': {'source_path': p.CP + '/evidence/paired.net', 'source_sha256': p.BOUND[p.CP + '/evidence/paired.net'],
            'expected_named_nets': len(nets), 'expected_assigned_nodes': sum(len(r['nodes']) for r in nets.values()),
            'expected_semantic_sha256': p.digest(nets), 'expected_components_and_libraries': p.expected_netlist_components_and_libraries(net_source),
            'retired_names': RETIRED_NETS, 'new_names': NEW_NETS, 'numeric_codes': 'Fresh explicit bijection; never infer identity from numeric codes.'},
        'contract_templates': contracts,
        'preservation': {'footprint_count': 156, 'pad_count': 558, 'pad_geometries_fixed': 558, 'unchanged_pad_nets': 554,
            'footprints_sha256': g.record_sha(native['footprints']), 'all_poses_fixed': True, 'all_unremoved_copper_retained': True,
            'original_C12_R3_IMU_TX_power_retained': True, 'stock_MCU_connector_pinout_retained': True},
        'terminal_substitutions': {'U15.1': 'U15.5', 'U15.10': 'U15.6'},
        'required_functions': scope['required_complete_functions'],
        'actual_IO': {'active_U15': ['U15.2', 'U15.5'], 'unused_bonded': ['U13.4', 'U15.1', 'U15.4'],
                      'NC6_upstream_only': True, 'internal_NC_conduction': False},
        'limits': {'layers': native['copper_layers'], 'min_width_clearance_mm': .127, 'via_diameter_drill_mm': [.45, .20],
                   'via_tented_both_faces': True, 'drill_to_all_SMT_masks_both_faces_mm': .20, 'drill_gap_mm': .25, 'edge_NPTH_mm': .254},
        'acceptance_claimed': False, 'route_complete': False, 'native_execution_eligible': NATIVE_EXECUTION_ENABLED,
        'routing_blocker': 'Exact eleven-cut first-barrel domains cannot pack both RX barrels; reviewed additional donor scope required.',
        'power_evidence_stale': True}
    return plan, preview, raw


def validated_source_plan(native, hardware):
    expected, preview, raw = derive_source_plan(native, hardware)
    require(read(SOURCE_PLAN_PATH) == expected, 'Paired source plan differs from exact source-derived declaration')
    return expected, preview, raw


def validate_plan(plan, native, logical, source_plan=None, require_complete=True):
    g.exact_keys(plan, ['schema', 'source', 'paired_source_plan_sha256', 'cut_scope_sha256',
                        'removed_native_records', 'added_copper', 'recipe_roles'], 'IO4 plan')
    require(plan['schema'] == PLAN_SCHEMA and plan['source'] == SOURCE_BINDINGS, 'IO4 routing source/schema mismatch')
    require(plan['paired_source_plan_sha256'] == sha(SOURCE_PLAN_PATH) and plan['cut_scope_sha256'] == CUT_SCOPE_SHA256,
            'IO4 paired-plan/cut-scope binding mismatch')
    source_plan = source_plan or read(SOURCE_PLAN_PATH)
    require(plan['removed_native_records'] == source_plan['removed_native_records'] and
            {x['record']['uuid'] for x in plan['removed_native_records']} == EXACT_CUT_IDS, 'Exact eleven full-record cuts required')
    ordinary = {k: plan[k] for k in ['source', 'removed_native_records', 'added_copper']}
    ordinary['schema'] = g.PLAN_SCHEMA
    validation = g.validate_plan(ordinary, native, logical)
    recipes = {r['name']: r for r in plan['added_copper']}
    roles = g.unique(plan['recipe_roles'], 'name')
    require(set(recipes) == set(roles), 'Exactly one explicit role per added recipe')
    for name, row in roles.items():
        g.exact_keys(row, ['name', 'net', 'logical_net', 'role'], 'recipe role')
        require(row['role'] in ROLES and row['net'] == ROLES[row['role']], 'Recipe role/net scope')
        require(row['net'] == recipes[name]['net'] and row['logical_net'] == recipes[name]['logical_net'], 'Role/recipe identity mismatch')
        if row['role'] == 'ground' and recipes[name]['kind'] == 'track':
            require(g.iu(recipes[name]['width']) >= 250000, 'Restore U15 GND at source .25 mm minimum width')
    if require_complete:
        require({r['role'] for r in roles.values()} == set(ROLES), 'Both RX branches and complete GND/HOLD recipes required')
    validation['roles'] = roles
    return validation


def template_plan(source_plan):
    return {'schema': PLAN_SCHEMA, 'source': SOURCE_BINDINGS, 'paired_source_plan_sha256': sha(SOURCE_PLAN_PATH),
            'cut_scope_sha256': CUT_SCOPE_SHA256, 'removed_native_records': source_plan['removed_native_records'],
            'added_copper': [], 'recipe_roles': []}


def verify_native(before, after, validation, additions):
    """Reuse the strict full-record comparator with only the declared net deltas.

    Numeric codes are allowed to reallocate on native serialization, but every
    record uses a single bijective name/code map; all actual geometry is compared.
    """
    parity = p.verify_pad_metadata(before, after)
    names = parity['net_codes_by_name']
    require(not set(RETIRED_NETS) & set(names) and set(NEW_NETS) <= set(names), 'Retired/new PCB net names differ')
    normalized = dict(before)
    normalized['objects'] = []
    for old in before['objects']:
        row = dict(old)
        if row['uuid'] in p.PINS.values():
            row['net'] = p.PIN_NETS[row['number']]
        row['net_code'] = names[row['net']]
        normalized['objects'].append(row)
    normalized['zones'] = [dict(z, net_code=names[z['net']]) for z in before['zones']]
    checked = dict(validation, old=g.unique(normalized['objects']))
    expected_additions = []
    for item in additions:
        record = dict(item['expected_native_record'], net_code=names[item['recipe']['net']])
        expected_additions.append(dict(item, expected_native_record=record))
    now, fills = g.verify_native(normalized, after, checked, expected_additions)
    return now, fills, parity


def expected_board_syntax(source_syntax):
    """Predict only four pad net atoms in the complete board syntax inventory."""
    result = copy.deepcopy(source_syntax)
    structures = [json.loads(row) for row in result['structures']]
    found = set()
    for structure in structures:
        if not isinstance(structure, list) or structure[0] != 'footprint':
            continue
        for pad in [n for n in structure if isinstance(n, list) and n and n[0] == 'pad']:
            uid = next(n[1] for n in pad if isinstance(n, list) and n[0] == 'uuid')
            if uid in p.PINS.values():
                pin = pad[1]; net = next(n for n in pad if isinstance(n, list) and n[0] == 'net')
                require(uid == p.PINS[pin] and len(net) == 2, 'Exact name-based KiCad10 pad syntax')
                net[1] = p.PIN_NETS[pin]; found.add(uid)
    require(found == set(p.PINS.values()), 'All four source pad net atoms required')
    result['structures'] = sorted(map(g.canonical, structures))
    return result


def verify_board_syntax(source_syntax, actual_syntax, removed_ids, addition_ids):
    expected = expected_board_syntax(source_syntax)
    require(expected['structures'] == actual_syntax['structures'], 'Undeclared non-route syntax beyond exact four pad nets')
    require(set(source_syntax['routes']) - set(actual_syntax['routes']) == set(removed_ids), 'Syntax removal inventory differs')
    require(set(actual_syntax['routes']) - set(source_syntax['routes']) == set(addition_ids), 'Syntax addition inventory differs')
    for uid in set(source_syntax['routes']) & set(actual_syntax['routes']):
        require(source_syntax['routes'][uid] == actual_syntax['routes'][uid], 'Retained complete route syntax changed: ' + uid)


def verify_paired_native(native, xml_bytes, raw):
    source = raw[p.CP + '/evidence/paired.net']
    expected = p.expected_netlist(source)
    p.verify_netlist(xml_bytes, expected, p.expected_netlist_components_and_libraries(source))
    assigned = {(n['ref'], n['pin']): name for name, row in expected.items() for n in row['nodes']}
    require(len(assigned) == 506 and len(expected) == 127, 'Paired source inventory')
    pads = {}
    for obj in native['objects']:
        if obj['kind'] == 'pad' and obj['number']:
            pads.setdefault((obj['ref'], obj['number']), []).append(obj)
    require(set(assigned) <= set(pads), 'Netlist has missing physical pad')
    require(all(all(pad['net'] == name for pad in pads[key]) for key, name in assigned.items()), 'Full fresh schematic/PCB semantic parity')
    return {'assigned_nodes': len(assigned), 'named_nets': len(expected), 'components': 156, 'all_assigned_nodes_match': True}


def bound_contracts(source_plan, board_sha, native_sha, plan_sha, netlist_sha):
    outputs = {}
    for template in source_plan['contract_templates']:
        contract = read(ROOT / template['source_path'])
        contract['checks'] = copy.deepcopy(template['checks'])
        contract.update(profile='native7-U15-IO4-native-only-' + template['kind'] + '-v2',
                        source_board_sha256=SOURCE_BINDINGS['board_sha256'], board_sha256=board_sha,
                        native_sha256=native_sha, plan_sha256=plan_sha,
                        paired_source_plan_sha256=sha(SOURCE_PLAN_PATH), paired_netlist_sha256=netlist_sha,
                        mapping_change='Native7 U15 RX actual clamp IO1/pad1 -> IO4/pad5; upstream NC10 -> NC6. TX remains IO2/NC9. All other native7 semantic nodes unchanged.',
                        U15_routing_land_assignments={'U15.6': p.RX, 'U15.9': 'PORT_C_TX_EXT'},
                        U15_actual_clamps={p.RX: 'U15.5', 'PORT_C_TX_EXT': 'U15.2'},
                        package_internal_NC_conduction=False)
        outputs[template['kind']] = contract
    return outputs


def validate_lease(lease, plan_path, output, now=None):
    g.exact_keys(lease, ['schema', 'active', 'owner', 'lease_id', 'allowed_stages', 'source', 'plan_sha256',
                        'importer_sha256', 'paired_source_plan_sha256', 'cut_scope_sha256', 'candidate_directory',
                        'issued_utc', 'expires_utc'], 'IO4 owner lease')
    require(lease['schema'] == LEASE_SCHEMA and lease['active'] is True, 'No active owner IO4 job permission')
    require(lease['allowed_stages'] == [STAGE], 'Lease must allow only bounded IO4 paired construction')
    require(lease['source'] == SOURCE_BINDINGS and lease['plan_sha256'] == sha(plan_path), 'Lease source/plan mismatch')
    require(lease['importer_sha256'] == sha(__file__) and lease['paired_source_plan_sha256'] == sha(SOURCE_PLAN_PATH) and
            lease['cut_scope_sha256'] == CUT_SCOPE_SHA256, 'Lease importer/paired scope mismatch')
    require(lease['candidate_directory'] == str(output), 'Lease selected output mismatch')
    require(all(isinstance(lease[k], str) and lease[k].strip() for k in ['owner', 'lease_id']), 'Owner and lease ID required')
    issued, expires = [dt.datetime.fromisoformat(lease[k].replace('Z', '+00:00')) for k in ['issued_utc', 'expires_utc']]
    require(issued.tzinfo is not None and expires.tzinfo is not None, 'Lease timestamps require timezone')
    now = now or dt.datetime.now(dt.timezone.utc)
    require(issued <= now < expires and expires - issued <= dt.timedelta(hours=2), 'Lease expired, future, or over two hours')
    return lease


def construct(args, plan, before, logical, hardware, validation, source_plan, preview, raw):
    require(NATIVE_EXECUTION_ENABLED, 'Sealed eleven-cut scope failed joint barrel capacity; no native execution is eligible')
    require(args.output is not None and args.lease is not None, 'Native execution requires owner output and lease')
    output = g.validate_output(args.output)
    plan_hash, lease_hash, importer_hash = sha(args.plan), sha(args.lease), sha(__file__)
    def gate():
        require(sha(args.plan) == plan_hash and sha(args.lease) == lease_hash and sha(__file__) == importer_hash, 'Selected job input changed')
        for name, expected in DEPENDENCIES.items():
            require(sha(HERE / name) == expected, 'Constructor dependency changed during job')
        require(sha(CUT_SCOPE_PATH) == CUT_SCOPE_SHA256, 'Cut scope changed during job')
        return validate_lease(read(args.lease), args.plan, output)
    lease = gate()
    for name, expected in {**g.RUNTIME_FILES, **CLI_FILES}.items():
        require(sha(g.RUNTIME / name) == expected, 'Pinned official runtime changed: ' + name)
    require(Path(os.environ.get('KICAD_CONFIG_HOME', '/nonexistent')).resolve() == g.RUNTIME / 'config', 'Use official kicad10-runtime/python wrapper')
    parser = g.parser_helper()
    source_syntax = g.syntax_inventory(g.SOURCE / 'f722-heli.kicad_pcb', parser)
    expected_board_syntax(source_syntax)
    additions = g.prepare_additions(plan, plan_hash, source_syntax)
    # All source, recipe, role, output, runtime and owner gates precede CAD import/write.
    import pcbnew as pcb
    require(pcb.Version() == '10.0.6' and pcb.GetBuildVersion() == '10.0.6+dfsg-1', 'Wrong native runtime')
    sys.path.insert(0, str(ROOT / 'recovered-native7/ordinary-routing/native-tools'))
    import export_native_copper as exporter
    output.mkdir(parents=True, exist_ok=False)
    for name, expected in hardware.items():
        target = output / name; target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(g.SOURCE / name, target)
        require(sha(target) == expected, 'Copied hardware identity differs')
    for original, name in [(args.plan, 'selected-plan.json'), (args.lease, 'owner-lease-at-start.json'),
                            (Path(__file__), 'importer.used.py'), (SOURCE_PLAN_PATH, 'paired-source-plan.json')]:
        shutil.copy2(original, output / name)
    write(output / 'construction-start.json', {'status': 'STARTED_NOT_ACCEPTED', 'source': SOURCE_BINDINGS, 'plan_sha256': plan_hash})
    for name, text in preview.items():
        (output / name).write_text(text)
    p.verify_metadata_preview(raw, {name: (output / name).read_text() for name in preview}, parser)
    gate()
    netlist_path = output / 'paired.net'
    with (output / 'paired-export.log').open('x') as log:
        result = subprocess.run([str(g.RUNTIME / 'kicad-cli'), 'sch', 'export', 'netlist', '--format', 'kicadxml',
                                 '--output', str(netlist_path), str(output / 'f722-heli.kicad_sch')], stdout=log, stderr=subprocess.STDOUT,
                                check=False, timeout=90)
    require(result.returncode == 0, 'Fresh paired export failed; inspect candidate log')
    source_xml = raw[p.CP + '/evidence/paired.net']
    p.verify_netlist(netlist_path.read_bytes(), p.expected_netlist(source_xml), p.expected_netlist_components_and_libraries(source_xml))
    gate()
    board_path = output / 'f722-heli.kicad_pcb'
    board = pcb.LoadBoard(str(board_path))
    tracks = {t.m_Uuid.AsString(): t for t in board.GetTracks()}
    require(set(tracks) == set(source_syntax['routes']), 'Native/syntax source route inventory differs')
    pads = {pad.m_Uuid.AsString(): pad for fp in board.GetFootprints() for pad in fp.Pads()}
    max_code = max(o['net_code'] for o in before['objects'])
    held = []
    for index, name in enumerate(NEW_NETS, 1):
        require(name not in {o['net'] for o in before['objects']}, 'New unused net already exists')
        net = pcb.NETINFO_ITEM(board, name, max_code + index); board.Add(net); held.append(net)
    for pin, name in p.PIN_NETS.items():
        pad = pads[p.PINS[pin]]
        require(pad.GetNumber() == pin and pad.GetParentFootprint().GetReference() == 'U15', 'Native pad physical identity')
        pad.SetNet(board.FindNet(name))
    for name in RETIRED_NETS:
        require(not any(pad.GetNetname() == name for pad in pads.values()), 'Retired net retains a physical pad')
        board.Remove(board.FindNet(name))
    for uid in validation['removed']:
        board.Remove(tracks[uid])
    point = lambda v: pcb.VECTOR2I(*g.xy(v))
    for addition in additions:
        recipe, index = addition['recipe'], addition['segment_index']
        if recipe['kind'] == 'track':
            item = pcb.PCB_TRACK(board); item.SetLayer(board.GetLayerID(recipe['layer'])); item.SetWidth(g.iu(recipe['width']))
            item.SetStart(point(recipe['points'][index])); item.SetEnd(point(recipe['points'][index + 1]))
        else:
            item = pcb.PCB_VIA(board); item.SetPosition(point(recipe['xy'])); item.SetWidth(450000); item.SetDrill(200000)
            item.SetViaType(pcb.VIATYPE_THROUGH); item.SetLayerPair(pcb.F_Cu, pcb.B_Cu)
            item.SetFrontTentingMode(pcb.TENTING_MODE_TENTED); item.SetBackTentingMode(pcb.TENTING_MODE_TENTED)
        net = board.FindNet(recipe['net']); require(net is not None and net.GetNetname() == recipe['net'], 'Native recipe net missing')
        item.SetUuid(pcb.KIID(addition['uuid'])); item.SetNet(net); board.Add(item); held.append(item)
        addition['expected_native_record'] = g.expected_new_record(addition, item, board, pcb, exporter)
    pcb.SaveBoard(str(board_path), board)
    gate()
    board = pcb.LoadBoard(str(board_path)); manager = pcb.GetSettingsManager()
    require(manager.LoadProject(str(output / 'f722-heli.kicad_pro')), 'Cannot load copied paired project')
    board.SetProject(manager.GetProject(str(output / 'f722-heli.kicad_pro')))
    board.SynchronizeNetsAndNetClasses(False); board.BuildConnectivity()
    require(pcb.ZONE_FILLER(board).Fill(board.Zones()), 'Native refill failed')
    pcb.SaveBoard(str(board_path), board)
    gate()
    after = exporter.export(board_path)
    write(output / 'f722-heli.native.json', after, compact=True)
    now, fills, pad_parity = verify_native(before, after, validation, additions)
    netlist_parity = verify_paired_native(after, netlist_path.read_bytes(), raw)
    verify_board_syntax(source_syntax, g.syntax_inventory(board_path, parser), validation['removed'], {a['uuid'] for a in additions})
    for name, expected in hardware.items():
        if name in preview:
            require((output / name).read_text() == preview[name], 'Paired metadata changed after exact recipe')
        elif name != 'f722-heli.kicad_pcb':
            require(sha(output / name) == expected, 'Undeclared paired hardware edit: ' + name)
    new_logical = {uid: net for uid, net in logical.items() if uid not in validation['removed']}
    new_logical.update({a['uuid']: a['recipe']['logical_net'] for a in additions})
    board_hash, native_hash, netlist_hash = sha(board_path), sha(output / 'f722-heli.native.json'), sha(netlist_path)
    write(output / 'f722-heli.logical-route-map.json', {'schema': 'f722-logical-route-map/v1', 'board_sha256': board_hash,
          'source_sha256': SOURCE_BINDINGS['board_sha256'], 'logical_route_map': new_logical})
    sidecar = {'schema': 'f722-native7-U15-IO4-recipe-roles/v2', 'source': SOURCE_BINDINGS, 'plan_sha256': plan_hash,
               'board_sha256': board_hash, 'native_sha256': native_hash, 'recipe_roles': plan['recipe_roles']}
    write(output / 'recipe-roles.json', sidecar)
    for kind, contract in bound_contracts(source_plan, board_hash, native_hash, plan_hash, netlist_hash).items():
        write(output / ('native7-IO4-' + kind + '-contracts-v2.json'), contract)
    g.source_inputs(); validated_source_plan(before, hardware); gate()
    receipt = {'schema': 'f722-native7-U15-IO4-import-receipt/v2', 'status': 'CONSTRUCTION_VERIFIED_NOT_ACCEPTED',
        'source': SOURCE_BINDINGS, 'board_sha256': board_hash, 'native_sha256': native_hash, 'plan_sha256': plan_hash,
        'importer_sha256': importer_hash, 'lease_sha256': lease_hash, 'lease_id': lease['lease_id'], 'stage': STAGE,
        'paired_source_plan_sha256': sha(SOURCE_PLAN_PATH), 'cut_scope_sha256': CUT_SCOPE_SHA256,
        'paired_netlist_sha256': netlist_hash, 'role_sidecar_sha256': sha(output / 'recipe-roles.json'), 'native_build': pcb.GetBuildVersion(),
        'hardware_files': [{'path': name, 'source_sha256': expected, 'candidate_sha256': sha(output / name)} for name, expected in sorted(hardware.items())],
        'pad_net_delta': source_plan['pad_net_delta'], 'all_156_poses_and_558_pad_geometries_fixed': True,
        'net_codes_by_name': pad_parity['net_codes_by_name'], 'paired_netlist_parity': netlist_parity,
        'retained_full_native_records_verified_except_declared_pad_nets_and_numeric_codes': True,
        'removed_native_records': list(validation['removed'].values()),
        'recipe_to_native_UUIDs': [{'name': a['recipe']['name'], 'segment_index': a['segment_index'], 'uuid': a['uuid'],
                                  'full_record_sha256': g.record_sha(now[a['uuid']])} for a in additions],
        'added_native_records': [now[a['uuid']] for a in additions], 'segments': validation['segments'], 'vias': validation['vias'],
        'native_refill_performed': True, 'changed_zone_fills': fills, 'all_source_inputs_unchanged': True,
        'native_DRC_ERC_and_physical_gates_performed': False, 'acceptance_claimed': False, 'adoption_claimed': False, 'power_evidence_stale': True}
    write(output / 'construction-provenance.json', receipt)
    return {k: receipt[k] for k in ['status', 'board_sha256', 'native_sha256', 'segments', 'vias', 'acceptance_claimed']}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--write-source-plan', action='store_true')
    ap.add_argument('--write-template', type=Path)
    ap.add_argument('--plan', type=Path)
    ap.add_argument('--check-inputs', action='store_true')
    ap.add_argument('--output', type=Path); ap.add_argument('--lease', type=Path)
    args = ap.parse_args()
    native, logical, hardware = g.source_inputs()
    if args.write_source_plan:
        require(args.plan is None and args.output is None and args.lease is None, 'Source plan is host-only')
        source_plan, _, _ = derive_source_plan(native, hardware); write(SOURCE_PLAN_PATH, source_plan)
    source_plan, preview, raw = validated_source_plan(native, hardware)
    if args.write_template:
        require(args.plan is None and args.output is None and args.lease is None, 'Template is host-only')
        write(args.write_template, template_plan(source_plan))
    if args.plan:
        plan = read(args.plan); validation = validate_plan(plan, native, logical, source_plan)
        if args.check_inputs:
            require(args.output is None and args.lease is None, 'Host validation uses no native output/lease')
            syntax = g.syntax_inventory(g.SOURCE / 'f722-heli.kicad_pcb', g.parser_helper())
            expected_board_syntax(syntax); g.prepare_additions(plan, sha(args.plan), syntax)
            result = {'input_validation_passed': True, 'removals': len(validation['removed']), 'segments': validation['segments'],
                      'vias': validation['vias'], 'native_work_performed': False, 'acceptance_claimed': False}
        else:
            result = construct(args, plan, native, logical, hardware, validation, source_plan, preview, raw)
    else:
        require(args.output is None and args.lease is None, 'Native execution needs an exact route plan')
        result = {'source_plan_verified': True, 'exact_cuts': 11, 'pad_net_changes': 4, 'native_work_performed': False,
                  'route_selection_pending': True, 'acceptance_claimed': False}
    print(json.dumps(result, allow_nan=False))


if __name__ == '__main__':
    try:
        main()
    except (ValueError, KeyError, TypeError, OSError, subprocess.TimeoutExpired) as error:
        raise SystemExit(str(error)) from error
