#!/usr/bin/env python3
"""Compare regenerated, pinned historical control against published output."""
import argparse
import csv
import json
from pathlib import Path
import re
from native_export import (HISTORICAL_PARTS, HISTORICAL_PCB, LAYERS, require, sha, read_csv,
                           write_json, parse_drill, drill_key)
from collections import Counter


def normalized_gerber(text):
    # Only timestamp comments/attributes and the Debian packaging suffix differ.
    # All drawing commands, aperture definitions and net attributes are retained.
    return '\n'.join(line.replace('10.0.6+dfsg-1', '10.0.6') for line in text.splitlines()
                     if not (line.startswith('%TF.CreationDate,') or
                             line.startswith('G04 Created by KiCad (PCBNEW ')))


def run(published, rebuilt):
    old = json.loads((published/'export-manifest.json').read_text())
    new = json.loads((rebuilt/'export-manifest.json').read_text())
    require(old['source_pcb_sha256'] == new['source_pcb_sha256'] == HISTORICAL_PCB, 'Control PCB identity mismatch')
    require(old['source_parts_sha256'] == new['source_parts_sha256'] == HISTORICAL_PARTS, 'Control parts identity mismatch')
    require(new['mode'] == 'historical-control', 'Comparison only supports explicitly historical control')
    result = {'status': 'HISTORICAL CONTROL REPRODUCED; NOT CURRENT LAYOUT OR RELEASE',
              'source_pcb_sha256': HISTORICAL_PCB, 'assembly_csvs': {}, 'gerbers': {}, 'drills': {},
              'normalization': 'Gerber timestamp attribute/comment omitted and exact 10.0.6+dfsg-1 packaging suffix normalized to 10.0.6. No geometry, aperture, polarity, or attribute commands omitted.'}
    for p in sorted((published/'assembly').glob('*.csv')):
        q = rebuilt/'assembly'/p.name
        a, b = read_csv(p), read_csv(q)
        require(a == b, f'Historical CSV data mismatch: {p.name}')
        result['assembly_csvs'][p.name] = {'rows': len(a), 'exact_csv_data_match': True,
                                           'byte_match': p.read_bytes() == q.read_bytes(), 'rebuilt_sha256': sha(q)}
    for layer, ext in LAYERS.items():
        name = f'f722-heli-{layer.replace(".", "_")}.{ext}'
        p, q = published/'gerbers'/name, rebuilt/'gerbers'/name
        require(normalized_gerber(p.read_text()) == normalized_gerber(q.read_text()), f'Historical Gerber commands mismatch: {name}')
        result['gerbers'][layer] = {'all_commands_and_apertures_match_after_declared_metadata_normalization': True,
                                    'rebuilt_sha256': sha(q)}
    for kind in ['PTH', 'NPTH']:
        p, q = published/'drill'/f'f722-heli-{kind}.drl', rebuilt/'drill'/f'f722-heli-{kind}.drl'
        a, ta = parse_drill(p, kind)
        b, tb = parse_drill(q, kind)
        require(ta == tb and Counter(map(drill_key, a)) == Counter(map(drill_key, b)), f'Historical drill mismatch: {kind}')
        result['drills'][kind] = {'features': len(a), 'tools_and_hole_slot_geometry_match': True, 'rebuilt_sha256': sha(q)}
    for key in ['gerber_files','gerber_job_files','drill_files','drill_maps','all_physical_native_pad_objects','outline_centerline_size_mm','usb_contact_paste_flashes','usb_shell_paste_flashes']:
        require(new['fabrication'][key] == old['fabrication'][key], f'Historical fabrication total mismatch: {key}')
    for key in ['board_footprints','populated_procurement_refs','procurement_groups','smt_cpl_refs','smt_bom_groups','smt_side_counts','manual_tht_refs','excluded_bare_test_pads']:
        require(new['assembly'][key] == old['assembly'][key], f'Historical assembly total mismatch: {key}')
    inventory = []
    for line in (rebuilt/'SHA256SUMS').read_text().splitlines():
        expected, name = line.split('  ', 1)
        require(sha(rebuilt/name) == expected, f'Rebuilt file hash mismatch: {name}')
        inventory.append(name)
    result['rebuilt_hash_inventory_verified_files'] = len(inventory)
    result['source_unchanged'] = new['source_unchanged']
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--published', type=Path, required=True)
    parser.add_argument('--rebuilt', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    result = run(args.published, args.rebuilt)
    write_json(args.report, result)
    print(json.dumps({'status': result['status'], 'csv_files': len(result['assembly_csvs']),
                      'gerber_layers': len(result['gerbers']), 'drill_files': len(result['drills']),
                      'hashes_verified': result['rebuilt_hash_inventory_verified_files']}))
