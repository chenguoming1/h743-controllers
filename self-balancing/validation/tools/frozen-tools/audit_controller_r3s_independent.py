#!/usr/bin/python3
"""Read-only reconstructed/routed R3-S check. Requires KiCad's pcbnew Python module.

Usage: /usr/bin/python3 audit_controller_r3s_independent.py PATH_TO_NATIVE_PROJECT [BOARD_SNAPSHOT [EXPECTED_JSON]]
Expected data lives beside this script; no source-project imports are used.
"""
import collections, hashlib, json, pathlib, sys, xml.etree.ElementTree as ET
import pcbnew

def main():
    if len(sys.argv) not in (2, 3, 4):
        raise SystemExit(__doc__)
    project = pathlib.Path(sys.argv[1])
    source = pathlib.Path(sys.argv[3]) if len(sys.argv) == 4 else pathlib.Path(__file__).with_name('controller-r3s-independent-expectations.json')
    spec = json.loads(source.read_text())
    expected = {(ref, pin): net for ref, pins in spec['components'].items() for pin, net in pins.items()}
    xml_path = project / 'review/controller-netlist.xml'
    map_path = project / 'review/design-netmap.json'
    pcb_path = pathlib.Path(sys.argv[2]) if len(sys.argv) >= 3 else project / 'controller.kicad_pcb'
    xml = ET.parse(xml_path).getroot()
    xml_parts = {c.get('ref'): {'Value': c.findtext('value'),
                              **{f.get('name'): f.text for f in c.findall('fields/field')}}
                 for c in xml.find('components')}
    names = collections.defaultdict(set)
    exported = {}
    for net in xml.find('nets'):
        raw = net.get('name')
        name = raw.rsplit('/', 1)[-1]
        names[name].add(raw)
        for node in net:
            exported[(node.get('ref'), node.get('pin'))] = None if raw.startswith('unconnected-') else name
    collisions = {name: sorted(v) for name, v in names.items() if len(v) > 1}
    if collisions:
        raise ValueError(('Ambiguous hierarchical name normalization', collisions))
    parts = {c['Reference']: c for c in json.loads(map_path.read_text())}
    intended = {(ref, str(pin)): net for ref, c in parts.items() for pin, net in c['nets'].items()}
    board = pcbnew.LoadBoard(str(pcb_path))
    native = {}
    pcb_parts = {f.GetReference(): {v.GetName(): v.GetText() for v in f.GetFields()}
                 for f in board.GetFootprints()}
    for footprint in board.GetFootprints():
        for pad in footprint.Pads():
            if not pad.GetNumber():
                continue
            raw = pad.GetNetname()
            name = None if not raw or raw.startswith('unconnected-') else raw.rsplit('/', 1)[-1]
            key = (footprint.GetReference(), pad.GetNumber())
            if key in native and native[key] != name:
                raise ValueError(('Conflicting duplicate pad number', key))
            native[key] = name
    errors = []
    for label, data in [('XML', exported), ('MAP', intended), ('PCB', native)]:
        errors += [(label, ref, pin, net, data.get((ref, pin), 'MISSING'))
                   for (ref, pin), net in expected.items() if data.get((ref, pin), 'MISSING') != net]
    extra = sorted(key for key in intended if key not in expected)
    for ref, prefix in spec['value_prefixes'].items():
        for label, data in [('MAP', parts), ('XML', xml_parts), ('PCB', pcb_parts)]:
            if not data.get(ref, {}).get('Value', '').startswith(prefix):
                errors.append((label, 'VALUE', ref, prefix, data.get(ref, {}).get('Value')))
    for ref, (mpn, code) in spec['selected_parts'].items():
        for field, want in [('MPN', mpn), ('LCSC', code)]:
            if parts.get(ref, {}).get(field) != want:
                errors.append(('MAP', field, ref, want, parts.get(ref, {}).get(field)))
        for label, data in [('XML', xml_parts), ('PCB', pcb_parts)]:
            for field, want in [('Manufacturer_Part_Number', mpn), ('LCSC', code)]:
                if data.get(ref, {}).get(field) != want:
                    errors.append((label, field, ref, want, data.get(ref, {}).get(field)))
    for ref in spec['absent_obsolete_refs']:
        if ref in parts:
            errors.append(('OBSOLETE_PRESENT', ref))
    output = {
        'expected_components': len(spec['components']),
        'expected_pin_entries': len(expected),
        'expected_connected_entries': sum(net is not None for net in expected.values()),
        'independent_value_checks': len(spec['value_prefixes']),
        'selected_part_identity_checks': len(spec['selected_parts']),
        'errors': errors, 'unexpected_map_entries': extra,
        'file_sha256': {str(p): hashlib.sha256(p.read_bytes()).hexdigest()
                        for p in [source, xml_path, map_path, pcb_path]},
        'scope_limit': 'Net assignments and selected identities/values only. Not copper connectivity, ERC/DRC, routing, impedance, thermal, mechanical or hardware qualification.'
    }
    print(json.dumps(output, indent=2))
    return 1 if errors or extra else 0

if __name__ == '__main__':
    sys.exit(main())
