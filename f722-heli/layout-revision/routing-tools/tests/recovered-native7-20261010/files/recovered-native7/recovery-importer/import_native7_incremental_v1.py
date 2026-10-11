#!/usr/bin/env python3
"""Source-bound ordinary routing import. Host --check-inputs never imports pcbnew.

Construction needs an owner-issued, hash-bound, unexpired native-job lease.
This tool proves a declared CAD edit, never physical/electrical acceptance.
"""
from __future__ import annotations

import argparse
import datetime as dt
from decimal import Decimal
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import shutil
import sys
import uuid

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SOURCE = ROOT / 'recovered-native7/ordinary-routing/tests/native13-access/joint-native-import11-v1/candidates/published-reference02'
CHECKPOINT = ROOT / 'repo/f722-heli/layout-revision/checkpoints/joint-native7-20261010'
RUNTIME = ROOT / 'kicad10-runtime'
STAGE = 'incremental_construct_refill_export'
PLAN_SCHEMA = 'f722-native7-incremental-routing-plan/v1'
LEASE_SCHEMA = 'f722-native7-owner-job-lease/v1'
LAYERS = ['F.Cu', 'In2.Cu', 'In3.Cu', 'B.Cu']
SOURCE_BINDINGS = {
    'board_sha256': 'a7355c26018a7bea66b77ccdc5201c2042a96b8e6820179fc5684dc72e170b4f',
    'native_sha256': '53ddf869c36da4a026880c6b3346dd1ddb304aaabaa948b20f1e66fc3db62505',
    'manifest_sha256': 'b9ec58e295f6e6d566973a9c3e5d21a05bf5ac4e7e15200e79b7d38048076d9d',
    'logical_map_sha256': 'a1175806ea39f0212f67e13b760782838c858dbaf285f6e4ac8919994e7364c0',
}
HELPERS = {
    'recovered-native7/ordinary-routing/native-tools/export_native_copper.py': 'd6f989ad9d7dc7e1264944cc2f334f70c5cae474b48843c3d1d6ee182716f19a',
    'recovered-native7/ordinary-routing/native-tools/exact_native_contours.py': 'd0fc0b3f55892ee5a58369da103fe62b7d9aa1789e36666696257fd644d02922',
    'repo/f722-heli/layout-revision/scripts/patch_metadata.py': 'e8ef0b33dcbb6c056564f3f78e0d5d8502208c52439fa66b2b1485cd3d60c636',
}
RUNTIME_FILES = {
    'python': '904e7f6fbcab80a18ce3faba2375d47d5850879056dbdb7b5fb63655d53c60f9',
    'runtime-env.sh': '1ab1e4472be591b4126ff812b08cd715692ef4d95a57e7f730184bfbe29f0699',
    'compat/sitecustomize.py': 'd6bed2f234e7474975bf2b5f4287b06492d0c8f8d65da8bf1646f1a5c6886666',
    'root/usr/lib/python3/dist-packages/pcbnew.py': 'dedb7b3535b71aa381c7ced85cd9ec6a2043f11494351ef658301894e106f4db',
    'root/usr/bin/_pcbnew.kiface': 'ed2771d60973c5338004c64c4b470424be466db39fc0ccc94156577fe6a2e5f9',
}


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False)


def record_sha(value):
    return hashlib.sha256(canonical(value).encode('utf-8')).hexdigest()


def read(path):
    def pairs(rows):
        result = {}
        for key, value in rows:
            require(key not in result, 'Duplicate JSON key: ' + key)
            result[key] = value
        return result
    def invalid(value):
        raise ValueError('Nonfinite JSON number: ' + value)
    return json.loads(Path(path).read_text(), object_pairs_hook=pairs, parse_constant=invalid)


def write(path, value, compact=False):
    with Path(path).open('x') as stream:
        json.dump(value, stream, indent=None if compact else 2,
                  separators=(',', ':') if compact else None, allow_nan=False)
        stream.write('\n')


def exact_keys(value, keys, name):
    require(isinstance(value, dict) and set(value) == set(keys), 'Unexpected/missing fields: ' + name)


def unique(rows, key='uuid'):
    require(isinstance(rows, list), 'Expected record list')
    result = {row[key]: row for row in rows}
    require(len(result) == len(rows), 'Duplicate ' + key)
    return result


def iu(value):
    require(type(value) in (int, float) and math.isfinite(value), 'Coordinate/width must be a finite number')
    scaled = Decimal(str(value)) * 1000000
    require(scaled == scaled.to_integral_value(), 'Coordinate/width is off the exact 1 nm native grid')
    require(abs(scaled) <= 2147483647, 'Coordinate/width exceeds native signed integer range')
    return int(scaled)


def xy(value):
    require(isinstance(value, list) and len(value) == 2, 'Expected explicit [x, y] coordinate')
    return [iu(v) for v in value]


def parser_helper():
    path = ROOT / 'repo/f722-heli/layout-revision/scripts/patch_metadata.py'
    require(sha(path) == HELPERS[str(path.relative_to(ROOT))], 'S-expression helper changed')
    spec = importlib.util.spec_from_file_location('native7_published_sexpr', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def source_inputs():
    require(sha(CHECKPOINT / 'MANIFEST.json') == SOURCE_BINDINGS['manifest_sha256'], 'Checkpoint manifest changed')
    manifest = read(CHECKPOINT / 'MANIFEST.json')
    require(manifest['schema'] == 'f722-joint-native7-public-manifest/v1', 'Wrong checkpoint manifest')
    hardware = {}
    for name, row in manifest['files'].items():
        if not name.startswith('hardware/'):
            continue
        relative = Path(name).relative_to('hardware')
        require(not relative.is_absolute() and '..' not in relative.parts, 'Unsafe hardware path')
        path = SOURCE / relative
        require(path.is_file() and path.resolve() == path, 'Missing/symlink hardware input: ' + str(relative))
        require(sha(path) == row['sha256'] and path.stat().st_size == row['bytes'], 'Hardware input changed: ' + str(relative))
        hardware[str(relative)] = row['sha256']
    require(len(hardware) == manifest['hardware_files'] == 61, 'Expected exactly 61 paired hardware inputs')
    require(hardware['f722-heli.kicad_pcb'] == SOURCE_BINDINGS['board_sha256'], 'Wrong source PCB')
    native_path = SOURCE / 'f722-heli.native.json'
    require(sha(native_path) == SOURCE_BINDINGS['native_sha256'], 'Wrong source native export')
    native = read(native_path)
    require(native['board_sha256'] == SOURCE_BINDINGS['board_sha256'], 'Stale native export')
    require(native['schema'] == 'kicad-native-copper/v1' and native['native_build'] == '10.0.6+dfsg-1', 'Unexpected native schema/build')
    require(native['copper_layers'] == ['F.Cu', 'In1.Cu', 'In2.Cu', 'In3.Cu', 'In4.Cu', 'B.Cu'], 'Unexpected source stack')
    require(len(native['footprints']) == 156 and sum(o['kind'] == 'pad' for o in native['objects']) == 558, 'Source footprint/pad inventory differs')
    logical_path = CHECKPOINT / 'repro/logical-route-map.json'
    require(sha(logical_path) == SOURCE_BINDINGS['logical_map_sha256'], 'Source logical map changed')
    logical = read(logical_path)
    require(logical['board_sha256'] == SOURCE_BINDINGS['board_sha256'], 'Stale logical map')
    old = unique(native['objects'])
    for uid, net in logical['logical_route_map'].items():
        require(uid in old and old[uid]['kind'] in ('track', 'via', 'arc'), 'Logical map has non-copper/missing UUID')
        require(old[uid]['net'] == net.split('::')[0], 'Logical map physical identity differs')
    for name, expected in HELPERS.items():
        require(sha(ROOT / name) == expected, 'Published helper changed: ' + name)
    return native, logical['logical_route_map'], hardware


def validate_plan(plan, native, logical):
    exact_keys(plan, ['schema', 'source', 'removed_native_records', 'added_copper'], 'plan')
    require(plan['schema'] == PLAN_SCHEMA and plan['source'] == SOURCE_BINDINGS, 'Plan source/schema mismatch')
    old = unique(native['objects'])
    removed = {}
    require(isinstance(plan['removed_native_records'], list), 'Removals must be a complete list')
    for row in plan['removed_native_records']:
        exact_keys(row, ['record', 'full_record_sha256'], 'removal')
        record = row['record']
        uid = record['uuid']
        require(uid not in removed and uid in old, 'Duplicate/foreign removal UUID: ' + uid)
        require(record == old[uid] and row['full_record_sha256'] == record_sha(old[uid]), 'Removal full-record identity mismatch: ' + uid)
        require(record['kind'] in ('track', 'via', 'arc'), 'Only native tracks/vias/arcs may be removed')
        if record['kind'] != 'via':
            require(set(record['width_by_layer']) <= set(LAYERS), 'Cannot remove signal geometry on plane layers')
        removed[uid] = record
    physical_nets = {o['net'] for o in old.values()} - {''}
    known_logical = set(logical.values())
    split_nets = {n.split('::')[0] for n in known_logical if '::' in n}
    names = set()
    segments = vias = 0
    require(isinstance(plan['added_copper'], list), 'Additions must be a complete list')
    for recipe in plan['added_copper']:
        require(isinstance(recipe, dict), 'Expected recipe object')
        kind, name = recipe['kind'], recipe['name']
        require(isinstance(name, str) and 0 < len(name) <= 160 and name not in names and name not in old,
                'Invalid/duplicate recipe name')
        names.add(name)
        net, logical_net = recipe['net'], recipe['logical_net']
        require(isinstance(net, str) and net in physical_nets and not net.startswith('unconnected-'), 'New/empty/unconnected physical net')
        require(isinstance(logical_net, str) and logical_net.split('::')[0] == net, 'Logical/physical net mismatch')
        require(logical_net in known_logical or (logical_net == net and net not in split_nets), 'Unknown logical identity; explicit canonical unsplit source net only')
        if kind == 'track':
            exact_keys(recipe, ['kind', 'name', 'net', 'logical_net', 'layer', 'points', 'width'], 'track recipe')
            require(recipe['layer'] in LAYERS, 'Track must use F/In2/In3/B ordinary layers')
            require(iu(recipe['width']) >= 127000, 'Track width below fixed .127 mm process minimum')
            points = recipe['points']
            require(isinstance(points, list) and len(points) >= 2, 'Polyline needs every point, at least two')
            points = list(map(xy, points))
            require(all(a != b for a, b in zip(points, points[1:])), 'Zero-length native polyline segment')
            segments += len(points) - 1
        elif kind == 'via':
            exact_keys(recipe, ['kind', 'name', 'net', 'logical_net', 'xy', 'diameter', 'drill', 'layers', 'tented_front', 'tented_back'], 'via recipe')
            xy(recipe['xy'])
            require(type(recipe['diameter']) in (int, float) and recipe['diameter'] == .45 and
                    type(recipe['drill']) in (int, float) and recipe['drill'] == .20 and
                    recipe['layers'] == native['copper_layers'] and recipe['tented_front'] is True and recipe['tented_back'] is True,
                    'Only .45/.20 mm fully tented through-vias are allowed')
            vias += 1
        else:
            raise ValueError('Only explicit track polyline and via recipes may be added')
    return {'old': old, 'removed': removed, 'segments': segments, 'vias': vias}


def native_uuid(plan_sha, name, segment):
    suffix = name + ('/via' if segment is None else '/segment/' + str(segment))
    return str(uuid.uuid5(uuid.NAMESPACE_URL, SOURCE_BINDINGS['board_sha256'] + '/' + plan_sha + '/' + suffix))


def prepare_additions(plan, plan_sha, syntax):
    additions = []
    existing = set(syntax['all_ids'])
    for recipe in plan['added_copper']:
        indices = range(len(recipe['points']) - 1) if recipe['kind'] == 'track' else [None]
        for index in indices:
            uid = native_uuid(plan_sha, recipe['name'], index)
            require(uid not in existing, 'Deterministic UUID collision')
            existing.add(uid)
            additions.append({'uuid': uid, 'recipe': recipe, 'segment_index': index})
    return additions


def validate_output(output):
    output = Path(output)
    require(output.is_absolute(), 'Output must be absolute and source-bound')
    require(output == output.resolve(), 'Output cannot contain symlinks or relative components')
    require(output.parent == HERE / 'candidates', 'Use a new direct child of recovery-importer/candidates')
    require(not output.exists(), 'Output already exists; preserve it and use a new candidate name')
    return output


def validate_lease(lease, plan_path, output, now=None):
    exact_keys(lease, ['schema', 'active', 'owner', 'lease_id', 'allowed_stages', 'source', 'plan_sha256',
                       'importer_sha256', 'candidate_directory', 'issued_utc', 'expires_utc'], 'owner lease')
    require(lease['schema'] == LEASE_SCHEMA and lease['active'] is True, 'No active owner job permission')
    require(lease['allowed_stages'] == [STAGE], 'Lease must allow this one bounded native stage')
    require(lease['source'] == SOURCE_BINDINGS and lease['plan_sha256'] == sha(plan_path), 'Lease source/plan mismatch')
    require(lease['importer_sha256'] == sha(__file__), 'Lease importer changed')
    require(lease['candidate_directory'] == str(output), 'Lease selected output mismatch')
    require(all(isinstance(lease[k], str) and lease[k].strip() for k in ('owner', 'lease_id')), 'Owner and lease ID are required')
    def timestamp(key):
        value = dt.datetime.fromisoformat(lease[key].replace('Z', '+00:00'))
        require(value.tzinfo is not None, 'Lease timestamps require timezone')
        return value
    issued, expires = timestamp('issued_utc'), timestamp('expires_utc')
    now = now or dt.datetime.now(dt.timezone.utc)
    require(issued <= now < expires and expires - issued <= dt.timedelta(hours=2), 'Lease expired, future, or over two hours')
    return lease


def syntax_inventory(path, helper):
    tree = helper.parse(Path(path).read_text())
    route = {}
    all_ids = []
    def shape(node):
        if not isinstance(node, helper.Node):
            return node.value
        kind = node.items[0].value
        if kind == 'uuid':
            all_ids.append(helper.val(node))
        values = node.items
        if kind == 'zone':
            values = [n for n in values if not isinstance(n, helper.Node) or n.items[0].value not in ('filled_polygon', 'fill_segments')]
        return [shape(n) for n in values]
    structures = []
    for node in tree.items:
        if isinstance(node, helper.Node) and node.items[0].value in ('segment', 'via', 'arc'):
            uid = helper.val(helper.child(node, 'uuid'))
            require(uid not in route, 'Duplicate route UUID in PCB syntax')
            route[uid] = shape(node)
        else:
            structures.append(shape(node))
    require(len(all_ids) == len(set(all_ids)), 'Duplicate UUID in full source board syntax')
    return {'routes': route, 'structures': sorted(map(canonical, structures)), 'all_ids': set(all_ids)}


def expected_new_record(addition, item, board, p, exporter):
    """Full recipe identity plus exact native API shapes, before save/refill.

    Reuse the pinned published exporter functions; never draw surrogate contours.
    The final independently reloaded export must equal this entire record.
    """
    recipe, index = addition['recipe'], addition['segment_index']
    via = recipe['kind'] == 'via'
    start = recipe['xy'] if via else recipe['points'][index]
    end = recipe['xy'] if via else recipe['points'][index + 1]
    layers = list(board.GetEnabledLayers().CuStack())
    names = [board.GetLayerName(layer) for layer in layers]
    record = {'uuid': addition['uuid'], 'kind': recipe['kind'], 'net': recipe['net'],
              'net_code': board.FindNet(recipe['net']).GetNetCode(), 'start': start, 'end': end,
              'width': .45 if via else recipe['width'], 'copper': {}, 'plated': via, 'mask': {},
              'drill': exporter.drill(item) if via else None,
              'barrel_layers': names if via else [],
              'width_by_layer': {layer: .45 for layer in names} if via else {recipe['layer']: recipe['width']}}
    if via:
        record.update(xy=recipe['xy'], via_type=p.VIATYPE_THROUGH, top_layer='F.Cu', bottom_layer='B.Cu',
                      tented={'F.Mask': True, 'B.Mask': True})
    for layer in layers:
        if item.IsOnLayer(layer) and (not via or item.FlashLayer(layer)):
            record['copper'][board.GetLayerName(layer)] = exporter.shape_polygons(item, layer)
    return record


def verify_native(before, after, validation, additions):
    old, now = validation['old'], unique(after['objects'])
    new_ids = {row['uuid'] for row in additions}
    require(set(old) - set(now) == set(validation['removed']), 'Native removals differ from declared full records')
    require(set(now) - set(old) == new_ids, 'Native additions differ from declared UUIDs')
    changed = [uid for uid in set(old) & set(now) if old[uid] != now[uid]]
    require(not changed, 'Undeclared full native object changes: ' + ', '.join(sorted(changed)[:10]))
    for key in ('footprints', 'edge_cuts', 'outline_with_npth', 'copper_layers', 'copper_layer_ids', 'board_thickness_mm',
                'native_version', 'native_build', 'maximum_polygon_error_mm', 'copper_error_location', 'pad_cut_error_location'):
        require(before[key] == after[key], 'Undeclared native board/footprint change: ' + key)
    for item in additions:
        record, recipe, index = now[item['uuid']], item['recipe'], item['segment_index']
        require(record == item['expected_native_record'], 'Full new native geometry differs from recipe/API snapshot: ' + recipe['name'])
        require(record['kind'] == recipe['kind'] and record['net'] == recipe['net'], 'Recipe identity mismatch')
        require({record['net_code']} == {o['net_code'] for o in old.values() if o['net'] == recipe['net']}, 'Added net code differs from source net identity')
        require(not record['mask'], 'Unexpected mask openings on new routing')
        if recipe['kind'] == 'track':
            require(record['start'] == recipe['points'][index] and record['end'] == recipe['points'][index + 1] and
                    record['width'] == recipe['width'] and record['width_by_layer'] == {recipe['layer']: recipe['width']} and
                    set(record['copper']) == {recipe['layer']} and not record['plated'] and record['drill'] is None and
                    record['barrel_layers'] == [], 'Native polyline segment differs from complete recipe')
        else:
            require(record['xy'] == recipe['xy'] == record['start'] == record['end'] and record['width'] == .45 and
                    record['drill']['width'] == .20 and record['drill']['start'] == recipe['xy'] == record['drill']['end'] and
                    record['via_type'] == 4 and record['plated'] is True and record['barrel_layers'] == before['copper_layers'] and
                    record['width_by_layer'] == {layer: .45 for layer in before['copper_layers']} and
                    record['top_layer'] == 'F.Cu' and record['bottom_layer'] == 'B.Cu' and
                    record['tented'] == {'F.Mask': True, 'B.Mask': True}, 'Native through-via differs from complete recipe')
    old_zones, zones = unique(before['zones']), unique(after['zones'])
    require(set(old_zones) == set(zones), 'Zone inventory changed')
    changes = []
    for uid in sorted(zones):
        previous, current = old_zones[uid], zones[uid]
        metadata = lambda z: {k: v for k, v in z.items() if k not in ('filled', 'fill_representation')}
        require(metadata(previous) == metadata(current), 'Zone outline/settings changed: ' + uid)
        for layer in sorted(set(previous['filled']) | set(current['filled']) |
                            set(previous['fill_representation']) | set(current['fill_representation'])):
            left, right = previous['filled'].get(layer), current['filled'].get(layer)
            left_repr, right_repr = previous['fill_representation'].get(layer), current['fill_representation'].get(layer)
            if left != right or left_repr != right_repr:
                changes.append({'zone_uuid': uid, 'net': current['net'], 'layer': layer,
                                'filled_geometry_changed': left != right, 'representation_changed': left_repr != right_repr,
                                'before_filled_sha256': record_sha(left), 'after_filled_sha256': record_sha(right),
                                'before_representation_sha256': record_sha(left_repr), 'after_representation_sha256': record_sha(right_repr)})
    return now, changes


def construct(args, plan, before, logical, hardware, validation):
    require(args.output is not None and args.lease is not None, 'Native execution requires --output and explicit --lease')
    output = validate_output(args.output)
    plan_hash = sha(args.plan)
    lease_hash = sha(args.lease)
    importer_hash = sha(__file__)
    def gate():
        require(sha(args.plan) == plan_hash and sha(args.lease) == lease_hash and sha(__file__) == importer_hash, 'Selected inputs changed during job')
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
    board_path = output / 'f722-heli.kicad_pcb'
    board = p.LoadBoard(str(board_path))
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
    require(source_syntax['structures'] == actual_syntax['structures'], 'Full non-route board/footprint/zone-metadata syntax changed')
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
    receipt = {'schema': 'f722-native7-incremental-import-receipt/v1', 'status': 'CONSTRUCTION_VERIFIED_NOT_ACCEPTED',
        'source': SOURCE_BINDINGS, 'board_sha256': sha(board_path), 'native_sha256': sha(output / 'f722-heli.native.json'),
        'plan_sha256': plan_hash, 'importer_sha256': importer_hash, 'lease_sha256': lease_hash, 'lease_id': lease['lease_id'],
        'stage': STAGE, 'native_build': p.GetBuildVersion(), 'hardware_input_count': len(hardware),
        'hardware_files': [{'path': name, 'source_sha256': expected, 'candidate_sha256': sha(output / name)}
                           for name, expected in sorted(hardware.items())],
        'paired_non_board_inputs_byte_identical': True, 'full_156_footprints_and_558_pads_unchanged': True,
        'retained_full_native_records_unchanged': len(set(validation['old']) & set(now)),
        'retained_full_route_syntax_unchanged': True, 'non_route_board_syntax_unchanged_except_zone_fills': True,
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
