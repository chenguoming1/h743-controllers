#!/usr/bin/env python3
"""Owner-leased fresh netlist/ERC/DRC and complete source-bound paired parity gates.

This writes new candidate-local reports only. Physical cuts, reference/return,
mechanical and numerical electrical qualification remain separate required gates.
"""
from __future__ import annotations

import argparse
import copy
import json
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

from common_joint11 import HERE, ROOT, read, require, sha, validate_lease, write


def xml_shape(element):
    return (element.tag, dict(element.attrib), (element.text or '').strip(), [xml_shape(c) for c in element])


def verify_netlist(netlist, source_netlist, spec):
    root = ET.parse(netlist).getroot()
    original = ET.parse(source_netlist).getroot()
    expectation = spec['netlist_expectations']
    expected_components = {c['ref']: c for c in expectation['complete_expected_component_identities']}
    components = {c.attrib['ref']: c for c in root.findall('./components/comp')}
    source_components = {c.attrib['ref']: c for c in original.findall('./components/comp')}
    require(len(components) == len(root.findall('./components/comp')) == 156, 'Fresh netlist component inventory differs')
    require(set(components) == set(expected_components) == set(source_components), 'Fresh netlist component IDs differ')
    for ref, c in components.items():
        identity = {'ref': ref, 'value': c.findtext('value'), 'footprint': c.findtext('footprint'),
                    'tstamps': c.findtext('tstamps'), 'sheetpath': dict(c.find('sheetpath').attrib),
                    'libsource': dict(c.find('libsource').attrib)}
        require(identity == expected_components[ref], f'Fresh component identity mismatch: {ref}')
        expected = copy.deepcopy(source_components[ref])
        if ref == 'U15':
            expected.find('libsource').set('part', spec['symbol_variant']['new_name'])
        require(xml_shape(c) == xml_shape(expected), f'Unexpected component fields/properties/pins changed: {ref}')
    nets = {}
    assigned = {}
    for n in root.findall('./nets/net'):
        name = n.attrib['name']
        require(name not in nets, 'Duplicate fresh net name')
        nodes = [dict(x.attrib) for x in n.findall('node')]
        nodes.sort(key=lambda x: (x['ref'], x['pin']))
        nets[name] = {'net_class': n.attrib['class'], 'nodes': nodes}
        for node in nodes:
            key = node['ref'] + '.' + node['pin']
            require(key not in assigned, f'Duplicate assigned schematic node: {key}')
            assigned[key] = name
    expected_nets = copy.deepcopy(expectation['complete_expected_nets'])
    for n in expected_nets.values():
        n['nodes'].sort(key=lambda x: (x['ref'], x['pin']))
    require(nets == expected_nets, 'Fresh full net inventory/pin names/electrical types differ from exact paired plan')
    require(len(nets) == 127 and len(assigned) == 506, 'Fresh netlist 127-net/506-node counts differ')
    libparts = [n for n in root.findall('./libparts/libpart') if n.attrib.get('lib') == 'F722_Heli' and
                n.attrib.get('part') == spec['symbol_variant']['new_name']]
    require(len(libparts) == 1, 'Fresh netlist lacks the separately named NC9/10 symbol variant')
    pins = {pin.attrib['num']: pin.attrib['type'] for pin in libparts[0].findall('./pins/pin')}
    require(pins == expectation['expected_libpart_new_variant_pin_types'], 'Unexpected variant pin electrical types')
    return assigned, {'components': 156, 'assigned_nodes': 506, 'nets': 127,
                      'all_component_fields_preserved_except_U15_libsource_part': True,
                      'full_net_pinfunction_pintype_inventory_exact': True,
                      'source_netlist_sha256': sha(source_netlist), 'netlist_sha256': sha(netlist)}


def native_parity(candidate, assigned, spec, diagnostic=False):
    native = read(candidate / ('diagnostic-native-export.json' if diagnostic else 'f722-heli.native.json'))
    require(native['board_sha256'] == sha(candidate / 'f722-heli.kicad_pcb'), 'Stale candidate native export')
    pads = [o for o in native['objects'] if o['kind'] == 'pad']
    require(len(pads) == 558 and len({p['uuid'] for p in pads}) == 558 and len(native['footprints']) == 156, 'Native inventory lost')
    actual = {}
    for p in pads:
        if p['number'] and p['net']:
            require(p['key'] not in actual or actual[p['key']] == p['net'], 'Duplicate pad numbers disagree')
            actual[p['key']] = p['net']
    aliases = spec['netlist_expectations']['existing_U13_slash_encoding_alias_only']
    require(len(aliases) == 1, 'Only existing U13 slash encoding alias permitted')
    alias = aliases[0]
    key = alias['ref'] + '.' + alias['pad']
    require(actual.get(key) == alias['pcb'] and assigned.get(key) == alias['schematic'], 'Historical U13 name alias changed')
    actual[key] = alias['schematic']
    require(actual == assigned, 'Fresh full native/schematic assigned pin/net parity differs')
    return {'physical_pads': 558, 'assigned_nodes': len(actual), 'full_parity_passed': True,
            'only_alias': aliases, 'board_sha256': native['board_sha256']}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--candidate', required=True, type=Path)
    ap.add_argument('--lease', required=True, type=Path)
    ap.add_argument('--diagnostic', action='store_true', help='Use retained failed-import native export; never issue construction acceptance')
    args = ap.parse_args()
    candidate = args.candidate.resolve()
    require(candidate.is_relative_to(HERE / 'candidates'), 'Candidate must belong to this isolated importer version')
    spec = read(candidate / 'import-spec.json')
    transaction = candidate / 'selected-transaction.json'
    provenance_path = candidate / ('native-pad-structure-diagnostic.json' if args.diagnostic else 'construction-provenance.json')
    provenance = read(provenance_path)
    board = candidate / 'f722-heli.kicad_pcb'
    board_hash = sha(board)
    require(provenance['board_sha256'] == board_hash and provenance['transaction_sha256'] == sha(transaction), 'Stale construction receipt')
    validate_lease(args.lease, 'paired_native_gates', transaction, candidate, spec)
    runtime = Path(spec['runtime']['directory'])
    reports = candidate / ('paired-native-diagnostic-gates-v1' if args.diagnostic else 'paired-native-gates-v1')
    reports.mkdir(exist_ok=False)
    commands = []

    def run(name, argv):
        validate_lease(args.lease, 'paired_native_gates', transaction, candidate, spec)
        with (reports / (name + '.log')).open('x') as log:
            result = subprocess.run([str(a) for a in argv], stdout=log, stderr=subprocess.STDOUT, check=False)
        commands.append({'name': name, 'argv': [str(a) for a in argv], 'returncode': result.returncode,
                         'log_sha256': sha(reports / (name + '.log'))})
        require(result.returncode == 0, f'{name} failed; inspect retained log')
        require(sha(board) == board_hash, f'{name} unexpectedly changed candidate PCB')

    netlist = reports / spec['netlist_expectations']['planned_filename']
    run('export-netlist', [runtime / 'kicad-cli', 'sch', 'export', 'netlist', '--format', 'kicadxml',
                          '--output', netlist, candidate / 'f722-heli.kicad_sch'])
    assigned, netlist_result = verify_netlist(netlist, ROOT / spec['netlist_expectations']['source_netlist'], spec)
    parity = native_parity(candidate, assigned, spec, args.diagnostic)
    write(reports / 'fresh-netlist-parity.json', {'schema': 'f722-joint-paired-netlist-parity/v1',
          'passed': True, **netlist_result, **parity})
    run('erc-all', [runtime / 'kicad-cli', 'sch', 'erc', '--format', 'json', '--severity-all',
                    '--output', reports / 'erc-all.json', candidate / 'f722-heli.kicad_sch'])
    run('drc-all', [runtime / 'kicad-cli', 'pcb', 'drc', '--format', 'json', '--all-track-errors', '--severity-all',
                    '--output', reports / 'drc-all.json', board])
    run('drc-schematic-parity', [runtime / 'kicad-cli', 'pcb', 'drc', '--format', 'json', '--all-track-errors',
                                '--severity-all', '--schematic-parity', '--output', reports / 'drc-schematic-parity.json', board])
    erc = read(reports / 'erc-all.json')
    erc_violations = [v for sheet in erc.get('sheets', []) for v in sheet.get('violations', [])]
    erc_violations += erc.get('violations', [])
    # No inherited warning exclusions and no modification to custom design rules.
    drc_summary = {}
    for name in ('drc-all', 'drc-schematic-parity'):
        report = read(reports / (name + '.json'))
        drc_summary[name] = {key: len(report.get(key, [])) for key in ('violations', 'unconnected_items', 'schematic_parity')}
    clean = not erc_violations and all(not count for summary in drc_summary.values() for count in summary.values())
    result = {'schema': 'f722-joint-paired-native-gates/v1', 'board_sha256': board_hash,
              'source_receipt_sha256': sha(provenance_path), 'diagnostic_only': args.diagnostic,
              'full_fresh_netlist_parity_passed': True, 'erc_violation_count': len(erc_violations),
              'drc_counts': drc_summary, 'native_subset_clean': clean, 'commands': commands,
              'physical_bonded_cuts_reference_return_mechanical_power_AC_gates_pending': True,
              'electrical_acceptance_claimed': False, 'adoption_claimed': False}
    write(reports / 'paired-native-summary.json', result)
    print(json.dumps({key: result[key] for key in ('board_sha256', 'full_fresh_netlist_parity_passed', 'erc_violation_count', 'drc_counts', 'native_subset_clean')}))
    require(clean, 'Native/ERC/DRC subset has diagnostics; no acceptance claimed')


if __name__ == '__main__':
    try:
        main()
    except (ValueError, KeyError) as error:
        raise SystemExit(str(error)) from error
