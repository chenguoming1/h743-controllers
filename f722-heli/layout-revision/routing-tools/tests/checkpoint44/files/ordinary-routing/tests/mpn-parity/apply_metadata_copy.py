#!/usr/bin/env python3
"""Apply the audited metadata plan to a NEW disposable paired-project copy.

Run with KiCad 10's Python wrapper. Source, authority, and manifest are read-only.
An explicit current board SHA256 is required, including for a later route candidate.
No native board save, refill, footprint update, or geometry reconstruction occurs.
"""
import argparse
import collections
import copy
import hashlib
import json
import re
import shutil
import subprocess
import uuid
import xml.etree.ElementTree as ET
from pathlib import Path

import pcbnew

TOKEN = re.compile(r'\(|\)|"(?:\\.|[^"\\])*"|[^\s()]+')


class Atom:
    def __init__(self, value, start, end):
        self.value, self.start, self.end = value, start, end


class Node:
    def __init__(self, start):
        self.items, self.start, self.end = [], start, None


def parse(text):
    stack, root = [], None
    for match in TOKEN.finditer(text):
        token = match.group()
        if token == '(':
            node = Node(match.start())
            if stack:
                stack[-1].items.append(node)
            stack.append(node)
        elif token == ')':
            node = stack.pop()
            node.end = match.end()
            if not stack:
                root = node
        else:
            value = json.loads(token) if token.startswith('"') else token
            stack[-1].items.append(Atom(value, match.start(), match.end()))
    assert root is not None and not stack
    return root


def children(node, key):
    return [n for n in node.items if isinstance(n, Node) and n.items[0].value == key]


def child(node, key):
    found = children(node, key)
    assert len(found) == 1, (key, len(found))
    return found[0]


def value(node, key):
    return child(node, key).items[1].value


def properties(node):
    result = {n.items[1].value: n for n in children(node, 'property')}
    assert len(result) == len(children(node, 'property'))
    return result


def shape(node):
    return [shape(x) if isinstance(x, Node) else x.value for x in node.items]


def sha(data):
    return hashlib.sha256(data).hexdigest()


def digest(data):
    return sha(json.dumps(data, ensure_ascii=False, separators=(',', ':')).encode())


def edit_text(text, edits):
    previous_start = len(text)
    for start, end, replacement in sorted(edits, reverse=True):
        assert 0 <= start <= end <= previous_start
        text = text[:start] + replacement + text[end:]
        previous_start = start
    return text


def without_fields(tree, kind, fields_by_ref):
    result = copy.deepcopy(tree)
    for node in children(result, kind):
        ref = properties(node)['Reference'].items[2].value
        names = fields_by_ref.get(ref, set())
        node.items[:] = [n for n in node.items if not (
            isinstance(n, Node) and n.items[0].value == 'property'
            and n.items[1].value in names)]
    return shape(result)


def native_identity(path):
    board = pcbnew.LoadBoard(str(path))
    footprints, pads, tracks = [], [], []
    for fp in board.GetFootprints():
        footprints.append({
            'ref': fp.GetReference(), 'uuid': fp.m_Uuid.AsString(),
            'symbol_path': fp.GetPath().AsString(), 'value': fp.GetValue(),
            'library_id': fp.GetFPID().GetUniStringLibId(),
            'xy_nm': [fp.GetPosition().x, fp.GetPosition().y],
            'angle_deg': fp.GetOrientationDegrees(), 'layer': fp.GetLayerName(),
            'attributes': int(fp.GetAttributes()),
        })
        for pad in fp.Pads():
            pads.append({
                'ref': fp.GetReference(), 'number': pad.GetNumber(),
                'uuid': pad.m_Uuid.AsString(), 'net': pad.GetNetname(),
                'netcode': pad.GetNetCode(),
                'xy_nm': [pad.GetPosition().x, pad.GetPosition().y],
                'size_nm': [pad.GetSize().x, pad.GetSize().y],
                'drill_nm': [pad.GetDrillSize().x, pad.GetDrillSize().y],
                'shape': int(pad.GetShape()), 'attribute': int(pad.GetAttribute()),
                'angle_deg': pad.GetOrientationDegrees(),
                'layers': str(pad.GetLayerSet().FmtHex()),
            })
    for track in board.GetTracks():
        is_via = isinstance(track, pcbnew.PCB_VIA)
        item = {
            'uuid': track.m_Uuid.AsString(), 'type': track.GetClass(),
            'net': track.GetNetname(), 'netcode': track.GetNetCode(),
            'start_nm': [track.GetStart().x, track.GetStart().y],
            'end_nm': [track.GetEnd().x, track.GetEnd().y],
            'width_nm': track.GetWidth(track.GetLayer()) if is_via else track.GetWidth(),
            'layer': track.GetLayerName(),
        }
        if is_via:
            item.update(drill_nm=track.GetDrillValue(),
                        layers=str(track.GetLayerSet().FmtHex()))
        tracks.append(item)
    footprints.sort(key=lambda x: x['ref'])
    pads.sort(key=lambda x: x['uuid'])
    tracks.sort(key=lambda x: x['uuid'])
    data = {'copper_layers': board.GetCopperLayerCount(), 'footprints': footprints,
            'pads': pads, 'tracks_and_vias': tracks}
    return {'sha256': digest(data), 'component_count': len(footprints),
            'physical_pad_count': len(pads), 'track_and_via_count': len(tracks),
            'data': data}


def run_cli(cli, arguments, log):
    command = [str(cli), *map(str, arguments)]
    completed = subprocess.run(command, text=True, capture_output=True)
    log.write_text(completed.stdout + completed.stderr)
    assert completed.returncode == 0, (command, completed.returncode, log)
    return {'command': command, 'returncode': completed.returncode, 'log': str(log)}


def net_identity(root):
    """Compare native symbol/pin/net identities independently of metadata fields."""
    components = []
    for comp in root.findall('./components/comp'):
        components.append({
            'ref': comp.attrib['ref'], 'value': comp.findtext('value') or '',
            'footprint': comp.findtext('footprint') or '',
            'symbol_uuid': comp.findtext('tstamps'),
            'sheetpath': comp.find('sheetpath').attrib,
            'units': [{'name': unit.attrib['name'],
                       'pins': [pin.attrib for pin in unit.findall('./pins/pin')]}
                      for unit in comp.findall('./units/unit')],
            'assembly_flags': [p.attrib for p in comp.findall('property')
                               if p.attrib.get('name') in ('dnp', 'exclude_from_bom')],
        })
    nets = [{'name': net.attrib['name'],
             'nodes': sorted([node.attrib for node in net.findall('node')],
                             key=lambda x: (x['ref'], x['pin']))}
            for net in root.findall('./nets/net')]
    data = {'components': sorted(components, key=lambda x: x['ref']),
            'nets': sorted(nets, key=lambda x: x['name'])}
    return {'sha256': digest(data), 'data': data}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--source', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--authority', type=Path, required=True)
    ap.add_argument('--manifest', type=Path, required=True)
    ap.add_argument('--expected-board-sha256', required=True)
    ap.add_argument('--cli', type=Path, required=True)
    args = ap.parse_args()
    source, out, authority = args.source.resolve(), args.out.resolve(), args.authority.resolve()
    assert source.is_dir() and not out.exists(), 'Output must be a new directory'
    assert source != out and source not in out.parents and out not in source.parents
    assert authority != out and authority not in out.parents and out not in authority.parents
    manifest = json.loads(args.manifest.read_text())
    board_name = 'f722-heli.kicad_pcb'
    source_board = source / board_name
    assert sha(source_board.read_bytes()) == args.expected_board_sha256, 'Unexpected board hash'
    authority_parts = authority / 'parts.json'
    assert sha(authority_parts.read_bytes()) == manifest['source_guards']['parts']['sha256']
    for name, expected in manifest['source_guards']['paired_schematics'].items():
        assert sha((source / name).read_bytes()) == expected, ('Unexpected schematic hash', name)

    # Copy all native project inputs and bundled libraries, excluding prior run reports.
    selected = sorted(p for p in source.iterdir() if p.is_file() and (
        p.suffix in {'.kicad_pcb', '.kicad_sch', '.kicad_pro', '.kicad_dru'}
        or p.name in {'fp-lib-table', 'sym-lib-table', 'parts.json'}))
    selected_dirs = sorted(p for p in source.iterdir() if p.is_dir()
                           and (p.name == 'library' or p.name.endswith('.pretty')))
    source_files = selected + [p for d in selected_dirs for p in d.rglob('*') if p.is_file()]
    before_sources = {str(p): sha(p.read_bytes()) for p in source_files}
    before_sources[str(authority_parts)] = sha(authority_parts.read_bytes())
    native_before = native_identity(source_board)
    out.mkdir(parents=True)
    for path in selected:
        shutil.copy2(path, out / path.name)
    for directory in selected_dirs:
        shutil.copytree(directory, out / directory.name)
    if not (out / 'parts.json').exists():
        shutil.copy2(authority_parts, out / 'parts.json')
    assert sha((out / 'parts.json').read_bytes()) == manifest['source_guards']['parts']['sha256']

    board_path = out / board_name
    original = board_path.read_text()
    tree = parse(original)
    fps = {properties(f)['Reference'].items[2].value: f for f in children(tree, 'footprint')}
    assert len(fps) == len(children(tree, 'footprint')) == len(manifest['board_updates']) == 156
    all_uuids = set(re.findall(r'\(uuid\s+"?([0-9a-f-]{36})"?\)', original))
    edits, mutable, operations = [], {}, []
    for update in manifest['board_updates']:
        ref = update['ref']
        fp = fps[ref]
        props = properties(fp)
        assert value(fp, 'uuid') == update['footprint_uuid']
        assert value(fp, 'path') == update['symbol_path']
        assert fp.items[1].value == update['footprint_library_id']
        assert props['Value'].items[2].value == update['reference_value']
        mutable[ref] = {change['field'] for change in update['changes']}
        additions = []
        for change in update['changes']:
            field, new = change['field'], change['new_value']
            assert (field in props) == change['old_present'], (ref, field, 'presence')
            if field in props:
                old = props[field].items[2]
                assert old.value == change['old_value'], (ref, field, old.value)
                edits.append((old.start, old.end, json.dumps(new, ensure_ascii=False)))
            else:
                field_uuid = str(uuid.uuid5(uuid.UUID(update['footprint_uuid']),
                                           'f722-metadata-parity/' + field))
                assert field_uuid not in all_uuids
                all_uuids.add(field_uuid)
                layer = 'B.Fab' if value(fp, 'layer') == 'B.Cu' else 'F.Fab'
                additions.append(
                    '(property ' + json.dumps(field) + ' ' + json.dumps(new, ensure_ascii=False)
                    + ' (at 0 0 0) (layer ' + json.dumps(layer) + ') (hide yes)'
                    + ' (uuid ' + json.dumps(field_uuid) + ')'
                    + ' (effects (font (size 1 1) (thickness 0.15))))')
            operations.append({'ref': ref, **change})
        if additions:
            start = child(fp, 'path').start
            edits.append((start, start, '\n\t\t'.join(additions) + '\n\t\t'))
    modified = edit_text(original, edits)
    after_tree = parse(modified)
    before_physical = without_fields(tree, 'footprint', mutable)
    after_physical = without_fields(after_tree, 'footprint', mutable)
    assert before_physical == after_physical, 'Unexpected non-target board edit'
    board_path.write_text(modified)

    schematic_evidence = []
    groups = collections.defaultdict(list)
    for update in manifest['schematic_updates']:
        groups[update['schematic_filename']].append(update)
    for filename, updates in groups.items():
        path = out / filename
        text = path.read_text()
        sch = parse(text)
        symbols = {properties(n)['Reference'].items[2].value: n for n in children(sch, 'symbol')}
        edits, mutable = [], collections.defaultdict(set)
        for update in updates:
            ref, field = update['ref'], update['field']
            symbol = symbols[ref]
            assert value(symbol, 'uuid') == update['symbol_uuid']
            props = properties(symbol)
            assert (field in props) == update['old_property_present']
            mutable[ref].add(field)
            if field in props:
                atom = props[field].items[2]
                assert atom.value == update['old_explicit_value']
                edits.append((atom.start, atom.end, json.dumps(update['new_value'], ensure_ascii=False)))
            else:
                at = child(symbol, 'at')
                addition = '(property ' + json.dumps(field) + ' ' + json.dumps(update['new_value'], ensure_ascii=False)
                addition += ' (at ' + at.items[1].value + ' ' + at.items[2].value
                addition += ' 0) (effects (font (size 1 1)) (hide yes))) '
                start = child(symbol, 'instances').start
                edits.append((start, start, addition))
        replacement = edit_text(text, edits)
        guard_before = without_fields(sch, 'symbol', mutable)
        guard_after = without_fields(parse(replacement), 'symbol', mutable)
        assert guard_before == guard_after, ('Unexpected non-target schematic edit', filename)
        path.write_text(replacement)
        schematic_evidence.append({'filename': filename, 'before_sha256': sha(text.encode()),
                                   'after_sha256': sha(replacement.encode()),
                                   'non_target_semantic_sha256': digest(guard_before),
                                   'changes': updates})

    native_after = native_identity(board_path)
    assert native_before == native_after, 'Native physical/net identity changed'
    expected_fields = {ref: {field.items[1].value: field.items[2].value
                            for field in children(fp, 'property')}
                       for ref, fp in {properties(f)['Reference'].items[2].value: f
                                       for f in children(after_tree, 'footprint')}.items()}
    native_board = pcbnew.LoadBoard(str(board_path))
    for fp in native_board.GetFootprints():
        assert {field.GetName(): field.GetText() for field in fp.GetFields()} == expected_fields[fp.GetReference()]

    commands = []
    baseline_netpath = out / 'metadata-baseline-native.net'
    commands.append(run_cli(args.cli, ['sch', 'export', 'netlist', '--format', 'kicadxml',
                                      '--output', baseline_netpath, source / 'f722-heli.kicad_sch'],
                            out / 'metadata-baseline-netlist.log'))
    net_before = net_identity(ET.parse(baseline_netpath).getroot())
    netpath = out / 'metadata-native.net'
    commands.append(run_cli(args.cli, ['sch', 'export', 'netlist', '--format', 'kicadxml',
                                      '--output', netpath, out / 'f722-heli.kicad_sch'],
                            out / 'metadata-netlist.log'))
    netroot = ET.parse(netpath).getroot()
    net_after = net_identity(netroot)
    assert net_before == net_after, 'Native exported schematic/pin/net identity changed'
    parity = []
    for comp in netroot.findall('./components/comp'):
        ref = comp.attrib['ref']
        for field in comp.findall('./fields/field'):
            key, expected = field.attrib['name'], field.text or ''
            if key not in ('Reference', 'Value', 'Footprint', 'Component Class'):
                if key not in expected_fields[ref] or expected_fields[ref][key] != expected:
                    parity.append({'ref': ref, 'field': key})
    assert not parity
    drcpath = out / 'metadata-drc-parity.json'
    before_drc_hash = sha(board_path.read_bytes())
    commands.append(run_cli(args.cli, ['pcb', 'drc', '--format', 'json', '--schematic-parity',
                                      '--severity-all', '--output', drcpath, board_path],
                            out / 'metadata-drc-parity.log'))
    assert sha(board_path.read_bytes()) == before_drc_hash, 'DRC changed board bytes'
    drc = json.loads(drcpath.read_text())
    assert not drc['schematic_parity'], drc['schematic_parity']
    assert all(sha(Path(p).read_bytes()) == expected for p, expected in before_sources.items())
    paired_destinations = [out / p.name for p in selected]
    report = {
        'status': 'PASS', 'source': str(source), 'destination': str(out),
        'kicad_version': pcbnew.Version(), 'script_sha256': sha(Path(__file__).read_bytes()),
        'manifest_sha256': sha(args.manifest.read_bytes()),
        'source_board_sha256': args.expected_board_sha256,
        'destination_board_sha256': sha(board_path.read_bytes()),
        'board_metadata_change_count': len(operations),
        'schematic_metadata_change_count': sum(map(len, groups.values())),
        'board_non_target_semantic_sha256_before': digest(before_physical),
        'board_non_target_semantic_sha256_after': digest(after_physical),
        'native_physical_net_identity_before': native_before,
        'native_physical_net_identity_after': native_after,
        'native_schematic_pin_net_identity_before': net_before,
        'native_schematic_pin_net_identity_after': net_after,
        'strict_native_schematic_parity_issues': len(drc['schematic_parity']),
        'drc_unconnected_items': len(drc['unconnected_items']),
        'drc_other_violations': drc['violations'],
        'schematic_evidence': schematic_evidence, 'commands': commands,
        'source_files_unchanged': True, 'source_file_sha256': before_sources,
        'destination_file_sha256': {str(p): sha(p.read_bytes()) for p in paired_destinations},
        'parts_sha256': sha((out / 'parts.json').read_bytes()),
        'metadata_operations': operations,
    }
    (out / 'metadata-verification.json').write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n')
    print(json.dumps({key: report[key] for key in [
        'status', 'source', 'destination', 'source_board_sha256', 'destination_board_sha256',
        'board_metadata_change_count', 'schematic_metadata_change_count',
        'strict_native_schematic_parity_issues', 'drc_unconnected_items',
        'drc_other_violations', 'source_files_unchanged']}, indent=2))


if __name__ == '__main__':
    main()
