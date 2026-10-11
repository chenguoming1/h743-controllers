#!/usr/bin/env python3
"""Exact native7 U15 IO4 paired SOURCE PLAN. Host only; never writes CAD.

--write-plan writes JSON only. --check proves a plan equals the deterministic
source-derived declaration. No pcbnew/shapely, subprocess, router, or CAD writer.
"""
import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import xml.etree.ElementTree as ET

SCHEMA = 'f722-native7-U15-IO4-paired-source-plan/v1'
CP = 'repo/f722-heli/layout-revision/checkpoints/joint-native7-20261010'
SRC = 'recovered-native7/ordinary-routing/tests/native13-access/joint-native-import11-v1/candidates/published-reference02'
PARSER = 'repo/f722-heli/layout-revision/scripts/patch_metadata.py'
ASSESSMENT = 'ordinary-routing/tests/native13-access/native7-U15-IO4-RX-channel-assessment-v1.json'
COMMON = 'ordinary-routing/tests/native13-access/native7-common-planning-packet-v1.json'
COPPER_SCOPE = 'recovered-native7/recovery-importer/native7-U15-IO4-copper-scope-v1.json'
OLD = 'TPD4E05U06_RoutePads_NC9_NC10'
NEW = 'TPD4E05U06_RoutePads_NC6_NC9'
RX = 'PORT_C_RX_EXT'
PIN_NETS = {'1': 'unconnected-(U15-IO1-Pad1)', '10': 'unconnected-(U15-NC10-Pad10)', '5': RX, '6': RX}
PINS = {'1': '76401567-1405-4a22-b70c-0a7f2502777e', '10': '85f6ae89-da40-4223-9e1c-51ee8cc2f22f', '5': 'dddece5c-5254-4426-8e4c-1fb5f9e85655', '6': 'af34758d-03d4-4898-8fb1-2be5765ea280'}
BOUND = {
    PARSER: 'e8ef0b33dcbb6c056564f3f78e0d5d8502208c52439fa66b2b1485cd3d60c636',
    CP + '/MANIFEST.json': 'b9ec58e295f6e6d566973a9c3e5d21a05bf5ac4e7e15200e79b7d38048076d9d',
    CP + '/evidence/paired.net': '4b364b3bdc0d04a078441c96326e2e1a181accf9e21da0c29c0313d00bf1a38b',
    CP + '/repro/logical-route-map.json': 'a1175806ea39f0212f67e13b760782838c858dbaf285f6e4ac8919994e7364c0',
    CP + '/evidence/contracts/joint-native11-actual_io-contracts-v1.json': '573842a98c339006f1cc1045106f8243be39038edb8458606884051f274e0753',
    CP + '/evidence/contracts/joint-native11-candidate-contracts-v1.json': 'd68e7f36e76a183703843762ac45f6de701192c04aa8e1dd8c0190aee823f82e',
    SRC + '/f722-heli.kicad_pcb': 'a7355c26018a7bea66b77ccdc5201c2042a96b8e6820179fc5684dc72e170b4f',
    SRC + '/f722-heli.native.json': '53ddf869c36da4a026880c6b3346dd1ddb304aaabaa948b20f1e66fc3db62505',
    ASSESSMENT: 'e2d974e25031857531de5427c06f5929a9631e6c9801bb1f02ad2c672e0d3f8d',
    COMMON: 'b161ae1c4df8632c38bea543c4ddb07e5dcb67afd734f86ef4d931cc1584a051',
    COPPER_SCOPE: '072f788ef6dd5f758033754a6ab7a0d8124e8a7b0a632ad1c1a94ea624221096',
}
MOVES = [
    ('wire', '085d2b8a-d551-528d-ac09-b0dd65cc82af', '163.83', '173.99', 'RX actual IO1 to IO4'),
    ('global_label', '2a3b190b-0a65-587d-8ec3-ef742c151959', '163.83', '173.99', 'RX actual IO1 to IO4'),
    ('wire', '0b0c1e62-5dd3-5bc6-8c97-b16db4a68f12', '186.69', '176.53', 'RX routing land NC10 to NC6'),
    ('global_label', '673af37b-8f20-5585-a189-320aafd481ad', '186.69', '176.53', 'RX routing land NC10 to NC6'),
    ('no_connect', '0fd0688e-5843-562e-a15c-082cb8c8d7f4', '173.99', '163.83', 'unused mark IO4 to IO1'),
    ('no_connect', '43cdc723-be7a-54ab-a4dc-b7c46d22f9c4', '176.53', '186.69', 'unused mark NC6 to NC10'),
]


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode()


def digest(value):
    return sha(canonical(value))


def load_sources(root):
    root = Path(root)
    raw = {}
    for path, expected in BOUND.items():
        raw[path] = (root / path).read_bytes()
        require(sha(raw[path]) == expected, 'source identity: ' + path)
    manifest = json.loads(raw[CP + '/MANIFEST.json'])
    hardware = {k[9:]: v for k, v in manifest['files'].items() if k.startswith('hardware/')}
    require(len(hardware) == 61, 'exact paired hardware inventory')
    for name, row in hardware.items():
        path = SRC + '/' + name
        raw[path] = (root / path).read_bytes()
        require(sha(raw[path]) == row['sha256'] and len(raw[path]) == row['bytes'], 'hardware identity: ' + name)
    spec = importlib.util.spec_from_file_location('u15_pinned_parser', root / PARSER)
    parser = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(parser)
    return raw, hardware, parser


def pins_of(m, node):
    return {m.val(m.child(p, 'number')): p for s in m.children(node, 'symbol') for p in m.children(s, 'pin')}


def clone_variant(m, text, node):
    """Only symbol/nested names and the two explicitly declared pin types vary."""
    original = text[node.start:node.end]
    tree = m.parse(original)
    edits = []
    for s in [tree] + m.children(tree, 'symbol'):
        atom = s.items[1]
        require(OLD in atom.value, 'variant name prefix')
        edits.append((atom.start, atom.end, json.dumps(atom.value.replace(OLD, NEW))))
        atom.value = atom.value.replace(OLD, NEW)
    pins = pins_of(m, tree)
    require(set(pins) == {str(i) for i in range(1, 11)}, 'exact ten physical pins')
    for pin, before, after in [('6', 'no_connect', 'passive'), ('10', 'passive', 'no_connect')]:
        atom = pins[pin].items[1]
        require(atom.value == before, 'variant pin type source')
        edits.append((atom.start, atom.end, after))
        atom.value = after
    result = m.replace(original, edits)
    require(m.shape(m.parse(result)) == m.shape(tree), 'variant changed unrelated syntax')
    return result


def metadata_preview(raw, m):
    """Return in-memory strings and exact operation ledger; no CAD output API."""
    name = 'io-ports.kicad_sch'
    text = raw[SRC + '/' + name].decode()
    root = m.parse(text)
    symbol, snap = m.symbol_snapshot(root, 'U15')
    require(snap['uuid'] == '8a547080-a99f-5b6e-a7bc-e04ebba85e43', 'U15 schematic UUID')
    libid = m.child(symbol, 'lib_id').items[1]
    require(libid.value == 'F722_Heli:' + OLD, 'U15 source variant')
    edits, ledger = [], []
    for kind, uid, before_y, after_y, purpose in MOVES:
        nodes = [x for x in m.children(root, kind) if m.val(m.child(x, 'uuid')) == uid]
        require(len(nodes) == 1, 'schematic object identity')
        node = nodes[0]
        before = text[node.start:node.end]
        local = m.parse(before)
        positions = m.children(m.child(local, 'pts'), 'xy') if kind == 'wire' else m.children(local, 'at')
        if kind == 'global_label':
            require(m.val(local) == RX, 'RX label source')
            positions += [m.child(x, 'at') for x in m.children(local, 'property')]
        changes = []
        for pos in positions:
            a = pos.items[2]
            require(a.value == before_y, 'schematic position source')
            changes.append((a.start, a.end, after_y))
            a.value = after_y
        after = m.replace(before, changes)
        require(m.shape(m.parse(after)) == m.shape(local), 'schematic move syntax')
        edits.append((node.start, node.end, after))
        ledger.append(dict(kind=kind, uuid=uid, purpose=purpose, before=before, after=after))
    edits.append((libid.start, libid.end, json.dumps('F722_Heli:' + NEW)))
    ledger.append(dict(kind='instance_lib_id', uuid=snap['uuid'], before=libid.value, after='F722_Heli:' + NEW))
    embedded = m.child(root, 'lib_symbols')
    old = next(x for x in m.children(embedded, 'symbol') if m.val(x) == 'F722_Heli:' + OLD)
    require(not any(m.val(x) == 'F722_Heli:' + NEW for x in m.children(embedded, 'symbol')), 'variant already present')
    new = clone_variant(m, text, old)
    edits.append((embedded.end - 1, embedded.end - 1, '\n' + new + '\n'))
    ledger.append(dict(kind='append_embedded_variant', name='F722_Heli:' + NEW, source_sha256=sha(text[old.start:old.end].encode()), after=new))
    preview = {name: m.replace(text, edits)}
    name = 'library/F722_Heli.kicad_sym'
    text = raw[SRC + '/' + name].decode()
    root = m.parse(text)
    old = next(x for x in m.children(root, 'symbol') if m.val(x) == OLD)
    require(not any(m.val(x) == NEW for x in m.children(root, 'symbol')), 'library variant already present')
    new = clone_variant(m, text, old)
    preview[name] = m.replace(text, [(root.end - 1, root.end - 1, '\n' + new + '\n')])
    ledger.append(dict(kind='append_library_variant', name=NEW, source_sha256=sha(text[old.start:old.end].encode()), after=new))
    # Independent structural check: reverse only the six declared moves and lib_id,
    # remove only newly appended variants, then prove the entire original syntax.
    verify_metadata_preview(raw, preview, m)
    return preview, ledger, snap


def verify_metadata_preview(raw, preview, m):
    require(set(preview) == {'io-ports.kicad_sch', 'library/F722_Heli.kicad_sym'}, 'metadata file scope')
    for name, result in preview.items():
        before = m.parse(raw[SRC + '/' + name].decode())
        after = m.parse(result)
        parent = m.child(after, 'lib_symbols') if name.endswith('.kicad_sch') else after
        variant_name = ('F722_Heli:' if name.endswith('.kicad_sch') else '') + NEW
        new = [x for x in m.children(parent, 'symbol') if m.val(x) == variant_name]
        require(len(new) == 1, 'one new variant')
        old_parent = m.child(before, 'lib_symbols') if name.endswith('.kicad_sch') else before
        old_name = variant_name.replace(NEW, OLD)
        old = next(x for x in m.children(old_parent, 'symbol') if m.val(x) == old_name)
        expected = clone_variant(m, raw[SRC + '/' + name].decode(), old)
        require(m.shape(new[0]) == m.shape(m.parse(expected)), 'new variant exact scope')
        parent.items.remove(new[0])
        if name.endswith('.kicad_sch'):
            instance, _ = m.symbol_snapshot(after, 'U15')
            a = m.child(instance, 'lib_id').items[1]
            require(a.value == 'F722_Heli:' + NEW, 'instance new variant')
            a.value = 'F722_Heli:' + OLD
            for kind, uid, by, ay, _ in MOVES:
                node = next(x for x in m.children(after, kind) if m.val(m.child(x, 'uuid')) == uid)
                positions = m.children(m.child(node, 'pts'), 'xy') if kind == 'wire' else m.children(node, 'at')
                if kind == 'global_label':
                    positions += [m.child(x, 'at') for x in m.children(node, 'property')]
                for p in positions:
                    require(p.items[2].value == ay, 'declared move missing')
                    p.items[2].value = by
        require(m.shape(before) == m.shape(after), 'unrelated metadata syntax changed: ' + name)


def netlist_model(data):
    root = ET.fromstring(data)
    rows = {}
    codes = set()
    for net in root.findall('./nets/net'):
        name = net.get('name')
        require(name not in rows, 'duplicate named net')
        code = net.get('code')
        require(code is not None and code.isdecimal() and int(code) > 0 and int(code) not in codes, 'duplicate or invalid XML net code')
        codes.add(int(code))
        nodes = sorted((dict(x.attrib) for x in net.findall('node')), key=lambda x: (x['ref'], x['pin']))
        rows[name] = dict(net_class=net.get('class'), nodes=nodes)
    require(rows, 'missing XML netlist')
    return rows


def expected_netlist(data):
    rows = netlist_model(data)
    for pin, dest in PIN_NETS.items():
        hits = [(name, node) for name, net in rows.items() for node in net['nodes'] if (node['ref'], node['pin']) == ('U15', pin)]
        require(len(hits) == 1, 'unique source U15 netlist pin')
        src, node = hits[0]
        rows[src]['nodes'].remove(node)
        if dest not in rows:
            rows[dest] = dict(net_class='Default', nodes=[])
        node['pintype'] = {'1': 'passive+no_connect', '10': 'no_connect', '5': 'passive', '6': 'passive'}[pin]
        rows[dest]['nodes'].append(node)
    rows = {k: v for k, v in rows.items() if v['nodes']}
    for row in rows.values():
        row['nodes'].sort(key=lambda x: (x['ref'], x['pin']))
    return rows


def xml_shape(element):
    return [element.tag, dict(sorted(element.attrib.items())), (element.text or '').strip(),
            [xml_shape(x) for x in element]]


def expected_netlist_components_and_libraries(data):
    root = ET.fromstring(data)
    components = root.find('components')
    for comp in components:
        if comp.get('ref') == 'U15':
            lib = comp.find('libsource')
            require(lib.get('part') == OLD, 'source netlist component variant')
            lib.set('part', NEW)
    libraries = root.find('libparts')
    hits = [x for x in libraries if x.get('lib') == 'F722_Heli' and x.get('part') == OLD]
    require(len(hits) == 1, 'source netlist library variant')
    lib = hits[0]
    lib.set('part', NEW)
    pins = {p.get('num'): p for p in lib.findall('./pins/pin')}
    require(pins['6'].get('type') == 'no_connect' and pins['10'].get('type') == 'passive', 'source netlist pin types')
    pins['6'].set('type', 'passive')
    pins['10'].set('type', 'no_connect')
    return dict(components_sha256=digest(xml_shape(components)), libparts_sha256=digest(xml_shape(libraries)))


def verify_netlist(candidate_xml, expected, expected_identities):
    require(netlist_model(candidate_xml) == expected, 'fresh netlist complete semantic parity')
    root = ET.fromstring(candidate_xml)
    comps = [x for x in root.findall('./components/comp') if x.get('ref') == 'U15']
    require(len(comps) == 1 and comps[0].find('libsource').get('part') == NEW, 'fresh U15 symbol libsource')
    require({key + '_sha256': digest(xml_shape(root.find(key))) for key in ['components', 'libparts']} == expected_identities,
            'fresh component/library identities differ beyond exact variant changes')
    return True


def verify_pad_metadata(source_native, candidate_native):
    """Future input-only check; verifies all 558 pad geometries and semantic nets.

    Numerical codes may be regenerated. The entire candidate object/zone net-code
    map must be bijective, and every pad must use its declared semantic net. This
    does not validate route copper, poses, construction provenance, or clearances.
    """
    source = {o['uuid']: o for o in source_native['objects'] if o['kind'] == 'pad'}
    require(source_native['footprints'] == candidate_native['footprints'], 'all footprint metadata and poses fixed')
    rows = [o for o in candidate_native['objects'] if o['kind'] == 'pad']
    candidate = {o['uuid']: o for o in rows}
    require(len(rows) == len(candidate) and set(source) == set(candidate), 'pad UUID inventory')
    names, codes = {}, {}
    for obj in candidate_native['objects'] + candidate_native.get('zones', []):
        if 'net_code' not in obj:
            continue
        name, code = obj['net'], obj['net_code']
        require(isinstance(code, int) and not isinstance(code, bool), 'integer net code')
        require(code >= 0 and ((code == 0) == (name == '')), 'native code zero reserved for empty net')
        require(name not in names or names[name] == code, 'net name has multiple codes')
        require(code not in codes or codes[code] == name, 'net code aliases names')
        names[name], codes[code] = code, name
    changed = []
    for uid, src in source.items():
        got = candidate[uid]
        expected = copy.deepcopy(src)
        if src.get('ref') == 'U15' and src.get('number') in PIN_NETS:
            require(PINS[src['number']] == uid, 'changed pad exact identity')
            expected['net'] = PIN_NETS[src['number']]
            changed.append(uid)
        expected['net_code'] = names[expected['net']]
        require(expected == got, 'pad geometry or net mismatch: ' + src.get('key', uid))
    require(set(changed) == set(PINS.values()), 'exact four pad changes')
    return dict(changed_pad_uuids=sorted(changed), untouched_pads=len(source) - 4, net_codes_by_name=names)


def build(root):
    raw, hardware, m = load_sources(root)
    native = json.loads(raw[SRC + '/f722-heli.native.json'])
    assessment = json.loads(raw[ASSESSMENT])
    objects = {o['uuid']: o for o in native['objects']}
    u15 = [o for o in native['objects'] if o.get('ref') == 'U15']
    require(len(u15) == 10, 'ten U15 physical pads')
    for row in assessment['component']['pins']:
        require(digest(objects[row['uuid']]) == row['full_native_record_sha256'], 'assessment full record')
    preview, edits, snap = metadata_preview(raw, m)
    net_expected = expected_netlist(raw[CP + '/evidence/paired.net'])
    source_pads = [o for o in native['objects'] if o['kind'] == 'pad']
    require(len(source_pads) == 558 and len(native['footprints']) == 156, 'fixed hardware physical inventory')
    for pin in ['5', '6']:
        pad = objects[PINS[pin]]
        require([o['uuid'] for o in native['objects'] if o['net'] == pad['net']] == [pad['uuid']], 'retired unused net has other members')
    common = json.loads(raw[COMMON])['removed_native_ids']
    restore = assessment['copper_scope']['restore_original_R3_signal_leaves']
    extra = assessment['copper_scope']['remove_and_replace_complete_original_RX_prefixes']
    cuts = (set(common) - {x['uuid'] for x in restore}) | {x['uuid'] for x in extra}
    require(len(common) == 90 and len(cuts) == 92, 'exact preliminary cut arithmetic')
    for row in restore + extra:
        require(digest(objects[row['uuid']]) == row['full_native_record_sha256'], 'cut/restore full record')
    scope = json.loads(raw[COPPER_SCOPE])
    require(set(scope['common_original_cut_ids']) == set(common), 'copper scope original common cuts')
    addback_ids = {x['uuid'] for x in scope['common_addbacks']}
    require(len(addback_ids) == 26 and addback_ids <= set(common), 'exact common addbacks')
    require({x['uuid'] for x in scope['additional_old_RX_prefix_cuts']} == {x['uuid'] for x in extra}, 'exact RX prefix removals')
    cuts = (set(common) - addback_ids) | {x['uuid'] for x in extra}
    require(len(cuts) == 68 and cuts == {x['uuid'] for x in scope['resulting_removals']}, 'exact current 68 removal set')
    for row in scope['common_addbacks'] + scope['additional_old_RX_prefix_cuts'] + scope['resulting_removals']:
        require(digest(objects[row['uuid']]) == row['full_native_record_sha256'], 'current cut/addback source record')
    contracts = []
    for suffix in ['candidate', 'actual_io']:
        path = CP + '/evidence/contracts/joint-native11-' + suffix + '-contracts-v1.json'
        source = json.loads(raw[path])
        checks = copy.deepcopy(source['checks'])
        rx = [x for x in checks if x['id'] == 'published-06']
        require(len(rx) == 1 and rx[0]['clamp'] == 'U15.1', 'source actual RX clamp')
        rx[0]['clamp'] = 'U15.5'
        contracts.append(dict(source_path=path, source_sha256=BOUND[path], profile='native7-U15-IO4-' + suffix + '-planned-v1', board_sha256=None,
            binding_status='UNBOUND: future exact constructed PCB/native/paired-plan hashes required', checks=checks,
            checks_sha256=digest(checks), U15_routing_land_assignments={'U15.6': RX, 'U15.9': 'PORT_C_TX_EXT'},
            U15_actual_clamps={RX: 'U15.5', 'PORT_C_TX_EXT': 'U15.2'}, package_internal_NC_conduction=False))
    pad_delta = []
    for pin in ['1', '10', '5', '6']:
        obj = objects[PINS[pin]]
        pad_delta.append(dict(key='U15.' + pin, uuid=obj['uuid'], source_record_sha256=digest(obj), before_net=obj['net'],
            before_net_code=obj['net_code'], after_net=PIN_NETS[pin], after_net_code=None, xy=obj['xy'], angle=obj['angle'], geometry_changed=False))
    manifest = json.loads(raw[CP + '/MANIFEST.json'])
    reproduction_inputs = []
    for name in [
        'repro/import-spec.json', 'repro/DEPENDENCIES.json',
        'repro/importer/common_joint11.py', 'repro/importer/construct_joint_native11_v1.py',
        'repro/importer/validate_physical_joint11_v1.py', 'repro/importer/check_full_support_joint11_v1.py',
        'repro/importer/validate_paired_joint11_v1.py',
        'repro/source-inputs/actual-tvs-coverage-review/audit_coverage.py',
    ]:
        row = manifest['files'][name]
        require(sha((Path(root)/CP/name).read_bytes()) == row['sha256'], 'reproduction input identity: ' + name)
        reproduction_inputs.append(dict(path=CP+'/'+name, sha256=row['sha256'], purpose='Pinned historical reference; requires narrow successor, not directly runnable for IO4.'))
    plan = dict(schema=SCHEMA, status='source_only_unselected_unrouted_no_CAD_application',
        producer=dict(path='recovered-native7/recovery-importer/prepare_native7_u15_io4_pair_v1.py', sha256=sha(Path(__file__).read_bytes())),
        source={k: v for k, v in BOUND.items()}, paired_hardware_count=61,
        hardware_inventory_sha256=digest(hardware), component=dict(footprint_uuid=assessment['component']['footprint_uuid'],
        ref='U15', xy=[25.5, 17.6], angle=0, side='F.Cu', mpn='TPD4E05U06DQAR', schematic=snap),
        pad_net_delta=pad_delta, physical_pad_numbers_UUIDs_and_geometry_fixed=True,
        schematic=dict(symbol_before='F722_Heli:' + OLD, symbol_after='F722_Heli:' + NEW,
            operations=edits, source_only_memory_preview={name: dict(before_sha256=sha(raw[SRC + '/' + name]), after_sha256=sha(value.encode()), bytes=len(value.encode())) for name, value in preview.items()}),
        netlist=dict(source_path=CP + '/evidence/paired.net',
            exact_affected_expected_named_nets={name: net_expected[name] for name in sorted(set(PIN_NETS.values()))},
            expected_components=156, expected_named_nets=len(net_expected), expected_assigned_nodes=sum(len(v['nodes']) for v in net_expected.values()),
            complete_expected_named_nets_sha256=digest(net_expected), fresh_export_required=True,
            complete_expected_components_and_libraries=expected_netlist_components_and_libraries(raw[CP + '/evidence/paired.net']),
            numeric_codes='Unbound until fresh paired export and explicitly recorded board name/code allocation; no stale source-code identity assumption.',
            retired_names=['unconnected-(U15-IO4-Pad5)', 'unconnected-(U15-NC6-Pad6)'],
            created_names=['unconnected-(U15-IO1-Pad1)', 'unconnected-(U15-NC10-Pad10)']),
        preservation=dict(source_pad_count=len(source_pads), unaffected_pad_count=len(source_pads)-4,
            all_footprint_poses_fixed=156, source_all_pad_records_sha256=digest(sorted(source_pads,key=lambda o:o['uuid'])),
            source_footprints_sha256=digest(native['footprints']), untouched_endpoint_records=assessment['unchanged_external_and_MCU_endpoints'],
            U15_ground_native_record_hashes=assessment['held_ground_return']['pads'] + assessment['held_ground_return']['records'],
            native7_C12_R3_original=True, unrelated_net_names_memberships_and_attributes_fixed=True,
            parts_json_unchanged=True, project_and_all_other_schematics_unchanged=True),
        planned_contract_successors=contracts,
        actual_IO_inventory=dict(manufacturer_bonded_U15=['1','2','4','5'], manufacturer_NC_U15=['6','7','9','10'],
            active_U15=['U15.2','U15.5'], unused_bonded_before=['U13.4','U15.4','U15.5'], unused_bonded_after=['U13.4','U15.1','U15.4'],
            used_NC_roles={'U15.6':'RX_upstream_only','U15.9':'TX_upstream_only'}, no_internal_NC_edges=True),
        terminal_group_delta=dict(
            substitutions=[dict(before='U15.1', before_uuid=PINS['1'], after='U15.5', after_uuid=PINS['5'], role='actual_RX_clamp'),
                           dict(before='U15.10', before_uuid=PINS['10'], after='U15.6', after_uuid=PINS['6'], role='upstream_RX_land')],
            required_external_RX_group=['J11.1','U15.6','U15.5','R34.1'], required_RX_MCU_group=['R34.2','U1.28'],
            required_external_TX_group=['J11.2','U15.9','U15.2','R35.1'], required_TX_MCU_group=['R35.2','U1.29'],
            retired_RX_terminals=['U15.1','U15.10'],
            legacy_raw_result='Preserve the blind old-terminal/group failure as expected under this declared reassignment; do not require now-unused pads to remain on RX.',
            unchanged_terminals='Every other original physical terminal and complete connected group is preserved; use explicit substitution only for these two RX terminals.'),
        copper_scope=dict(status='exact_current_removal_set_no_additions_not_importable', common_count=90,
            original_assessment_before_addbacks_count=92, source_scope_path=COPPER_SCOPE, source_scope_sha256=BOUND[COPPER_SCOPE],
            restored_original_records=scope['common_addbacks'], added_RX_prefix_cuts=extra, removal_count=68,
            removal_records=[dict(uuid=uid,kind=objects[uid]['kind'],net=objects[uid]['net'],full_native_record_sha256=digest(objects[uid])) for uid in sorted(cuts)],
            removal_uuid_set_sha256=digest(sorted(cuts)), new_recipes=[],
            further_add_backs='Only a separately pinned complete routing successor may change this set; every retained/restored group must be enumerated.'),
        required_physical_gates=[
            'Full-width positive-area upstream J11.1 through NC6 and explicit PCB copper into actual IO4/pad5; no internal NC bond.',
            'Full-width positive-area downstream actual IO4/pad5 to R34.1; keep TX actual IO2/pad2 foreign while routing RX and conversely.',
            'Subtract actual IO4 ERROR_INSIDE copper from complete fresh native graph; J11.1 and R34.1 disconnect with >=0.127 mm outside-pad gap and declared drill/barrel connectivity.',
            'NC6 remains upstream only after actual-pad cut; old U15.1/10 unused pads have no residual RX copper contact.',
            'Apply the exact two declared RX terminal substitutions; preserve all unchanged original complete connected groups, seven inherited opens as obligations, and all cut-induced donor restoration obligations under the new explicit cut set.',
            'Fresh native construction/refill/export, DRC, ERC and full paired-netlist/pad parity; ground return, coupling and ESD electrical review remain required.'
        ],
        reproduction=dict(current_importers_and_final_contact_v2_incompatible=True,
            pinned_historical_inputs=reproduction_inputs,
            required_successor_changes=[
                'Apply exact paired schematic/library operations on a fresh 61-file candidate copy; never reapply historical U13 cycle or old U15 translation.',
                'Export candidate paired netlist first; bind complete ref/pin/net/pinfunction/pintype map and explicit candidate net-name/code allocation.',
                'A new native constructor must change only these four pad nets, keep all 156 footprints/all 558 pad geometries, remove only full source records in the final declared set, and add complete source-bound recipes.',
                'Update candidate-bound branch-view RX BONDED from U15.1 to U15.5 and upstream NC10 to NC6; bind the new role sidecar to final serialized routing plan and construction provenance.',
                'Bind versioned 18/22 contracts to final candidate board/native and this paired plan; published-06 changes clamp, published-07 remains IO2.',
                'Version coverage and review unused set; preserve manufacturer NC classification despite passive schematic types.',
                'Final-contact successor must explicitly admit this four-pad semantic delta, exact 68-cut inventory and two RX terminal substitutions; preserve inherited/raw findings and fixed geometries. Any later cut change requires a new reviewed source-bound scope.'
            ], historical_mapping_plan_context_only=assessment['bindings']['historical_mapping_plan']),
        execution=dict(CAD_written=False,native_run=False,geometry_run=False,route_complete=False,acceptance_claimed=False),
        manufacturer_evidence=assessment['manufacturer_evidence'][0],
        application_gate='No construction entrypoint. A complete jointly checked route, exact additions/removals, regenerated paired netlist, reviewed versioned constructor/contact gate and explicit bounded native owner lease are still required.')
    return plan, preview, native


def validate(plan, expected):
    require(plan == expected, 'plan differs from exact source-derived U15 IO4 declaration')
    return True


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--root', type=Path, required=True)
    group = ap.add_mutually_exclusive_group(required=True)
    group.add_argument('--write-plan', type=Path)
    group.add_argument('--check', type=Path)
    args = ap.parse_args()
    plan, _, _ = build(args.root)
    if args.write_plan:
        require(args.write_plan.suffix == '.json', 'JSON source plan only')
        require(not args.write_plan.exists(), 'refuse overwrite of frozen plan')
        args.write_plan.write_text(json.dumps(plan, indent=2, ensure_ascii=False, allow_nan=False) + '\n')
    else:
        validate(json.loads(args.check.read_text()), plan)
    print(json.dumps(dict(status='source_plan_valid', CAD_written=False, native_run=False, geometry_run=False,
        pad_net_changes=4, all_footprint_poses_fixed=156, declared_cuts=68, route_complete=False)))


if __name__ == '__main__':
    main()
