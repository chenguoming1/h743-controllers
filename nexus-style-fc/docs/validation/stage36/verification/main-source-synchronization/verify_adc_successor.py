#!/usr/bin/env python3
"""Verify and bind only the four accepted ADC placements in an isolated successor."""
import argparse
import csv
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sys

import pcbnew

EXPECTED_POSES = {
    'C29': {'position_mm': [111.0, 119.2], 'orientation_deg': 270.0, 'side': 'F'},
    'R16': {'position_mm': [111.4, 121.15], 'orientation_deg': 90.0, 'side': 'F'},
    'C30': {'position_mm': [114.39, 114.16], 'orientation_deg': 0.0, 'side': 'F'},
    'R17': {'position_mm': [111.4, 123.2], 'orientation_deg': 270.0, 'side': 'F'},
}
NOTICE = ('# PREPARED STAGE36 OVERLAY ONLY: four ADC placements await final native acceptance.\n'
          '# Provenance hashes below still describe stage35 and must be rebound before use.\n')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def csv_by_ref(path):
    rows = list(csv.DictReader(path.open()))
    by_ref = {row['Designator']: row for row in rows}
    assert len(by_ref) == len(rows)
    return by_ref


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--root', type=Path, required=True)
    ap.add_argument('--previous-root', type=Path, required=True)
    ap.add_argument('--stage32-root', type=Path, required=True)
    ap.add_argument('--expected-pcb-sha256', required=True)
    ap.add_argument('--expected-project-sha256', required=True)
    ap.add_argument('--kicad-cli', type=Path, required=True)
    args = ap.parse_args()
    root, previous = args.root.resolve(), args.previous_root.resolve()
    evidence = root / 'verification/main-source-synchronization'
    prev_evidence = previous / 'verification/main-source-synchronization'
    source, prior_source = root / 'tools/design.py', previous / 'tools/design.py'
    prepared_path = evidence / 'prepared-design.py'
    pcb = root / 'hardware/nexus-style-fc.kicad_pcb'
    project, schematic = pcb.with_suffix('.kicad_pro'), pcb.with_suffix('.kicad_sch')
    assert pcbnew.Version() == '10.0.7', pcbnew.Version()
    protected = [pcb, project, schematic, root / 'tools/make_footprints.py',
                 root / 'hardware/library/NexusFC.pretty/TPS70933DBVR_TI_DBV0005A.kicad_mod', prior_source]
    for folder in (previous, args.stage32_root):
        protected.extend(folder / ('hardware/nexus-style-fc.' + extension)
                         for extension in ('kicad_pcb', 'kicad_sch', 'kicad_pro'))
    before = {str(path): sha(path) for path in protected}
    assert before[str(pcb)] == args.expected_pcb_sha256
    assert before[str(project)] == args.expected_project_sha256 == sha(previous / 'hardware/nexus-style-fc.kicad_pro')
    assert sha(previous / 'hardware/nexus-style-fc.kicad_pcb') == 'bf9a10563839b18071dedd1c4a71af60c25ac19e94f392adb1917955b1f4e95d'
    assert sha(prior_source) == '2ce4d96fe38166232206ae2b9ff0b7716ba0f6aa0c83505f7f9ab5f6a2faff78'
    assert sha(args.stage32_root / 'hardware/nexus-style-fc.kicad_pcb') == 'f214f8141e8f21a7e0983c8eb4f2be89634e3b69d0d2b168a1ac3153f28a83de'
    assert source.read_bytes() == prior_source.read_bytes(), 'Active source changed after overlay preparation'
    initial_source_hash = sha(source)
    sync = load(Path(__file__).with_name('synchronize_main.py'), 'placement_sync')
    old = load(prior_source, 'stage35_design')
    prepared = load(prepared_path, 'stage36_prepared_design')
    assert old.PARTS == prepared.PARTS
    assert sync.identity(old.get_main_parts()) == sync.identity(prepared.get_main_parts())
    old_parts = {part['ref']: part for part in old.get_main_parts()}
    new_parts = {part['ref']: part for part in prepared.get_main_parts()}
    changed_refs = {ref for ref in old_parts if old_parts[ref]['place'] != new_parts[ref]['place']}
    assert changed_refs == set(EXPECTED_POSES), changed_refs
    board = pcbnew.LoadBoard(str(pcb))
    actual = sync.board_snapshot(board)
    sync.verify_identities_and_nets(prepared.get_main_parts(), actual)
    old_snapshot = json.loads((prev_evidence / 'placement-pad-snapshot.json').read_text())
    assert set(actual) == set(old_snapshot)
    pose_delta = {}
    for ref in actual:
        current, original = actual[ref], old_snapshot[ref]
        if ref not in EXPECTED_POSES:
            assert sync.near_equal(current, original), ('Unexpected footprint or pad change', ref)
            continue
        for key, value in EXPECTED_POSES[ref].items():
            assert sync.near_equal(current[key], value), (ref, key, current[key], value)
        for key in ('footprint', 'value', 'lcsc', 'side'):
            assert current[key] == original[key], (ref, key)
        previous_pads = {pad['number']: pad for pad in original['pads']}
        current_pads = {pad['number']: pad for pad in current['pads']}
        assert set(previous_pads) == set(current_pads) and len(current_pads) == len(current['pads'])
        for number, pad in current_pads.items():
            old_pad = previous_pads[number]
            for key in pad:
                if key not in ('position_mm', 'orientation_deg'):
                    assert sync.near_equal(pad[key], old_pad[key]), (ref, number, key)
            assert sync.norm_angle(pad['orientation_deg'] - current['orientation_deg']) == sync.norm_angle(old_pad['orientation_deg'] - original['orientation_deg'])
        pose_delta[ref] = {'before': {key: original[key] for key in EXPECTED_POSES[ref]},
                          'after': {key: current[key] for key in EXPECTED_POSES[ref]}}
    sys.path.insert(0, str(root / 'tools'))
    import build_floorplan
    import pcbutil
    import export_fab
    build_floorplan.design = prepared
    sys.modules['design'] = prepared
    generated_path = evidence / 'main-regenerated-floorplan.kicad_pcb'
    assert not generated_path.exists(), 'Use fresh output to avoid stale verification'
    build_floorplan.OUT = str(generated_path)
    pcbutil.STOCK = '/usr/share/kicad/footprints'
    build_floorplan.main()
    generated = sync.board_snapshot(pcbnew.LoadBoard(str(generated_path)))
    differences = sync.compare_floorplan(actual, generated)
    assert not differences, ('Regenerated floorplan mismatch', differences)
    assembly = evidence / 'bom-cpl'
    assembly.mkdir(exist_ok=False)
    export_fab.K = str(args.kicad_cli)
    export_fab.bom_cpl('nexus-style-fc', str(pcb), 'design', str(assembly))
    assembly_checks = sync.verify_bom_cpl(assembly, prepared.get_main_parts(), board, actual)
    bom_name, cpl_name = 'nexus-style-fc-bom-jlc.csv', 'nexus-style-fc-cpl-jlc.csv'
    assert (assembly / bom_name).read_bytes() == (prev_evidence / 'bom-cpl' / bom_name).read_bytes()
    new_rows = csv_by_ref(assembly / cpl_name)
    old_rows = csv_by_ref(prev_evidence / 'bom-cpl' / cpl_name)
    assert set(new_rows) == set(old_rows)
    cpl_changes = {ref: {'before': old_rows[ref], 'after': new_rows[ref]} for ref in new_rows if new_rows[ref] != old_rows[ref]}
    assert set(cpl_changes) == set(EXPECTED_POSES), cpl_changes
    for path, expected in before.items():
        assert sha(path) == expected, ('Protected input changed', path)
    assert sha(source) == initial_source_hash
    text = prepared_path.read_text()
    assert text.count(NOTICE) == 1
    text = text.replace(NOTICE, '')
    text, first = re.subn(r'^# Source PCB SHA256: [0-9a-f]{64}$', '# Source PCB SHA256: ' + args.expected_pcb_sha256, text, flags=re.M)
    text, second = re.subn(r'^# Footprint/pad placement SHA256: [0-9a-f]{64}$', '# Footprint/pad placement SHA256: ' + sync.stable_hash(actual), text, flags=re.M)
    assert (first, second) == (1, 1)
    compile(text, str(source), 'exec')
    source.write_text(text)
    bound = load(source, 'stage36_bound_design')
    assert bound.PARTS == old.PARTS and bound.get_main_parts() == prepared.get_main_parts()
    report = {
        'status': 'PASS: bounded ADC source/placement/assembly synchronization; not manufacturing approval',
        'kicad_version': pcbnew.Version(), 'source_pcb_sha256': args.expected_pcb_sha256,
        'source_project_sha256': args.expected_project_sha256, 'source_schematic_sha256': sha(schematic),
        'previous_design_sha256': initial_source_hash, 'bound_design_sha256': sha(source),
        'legacy_parts_identical_to_stage35': True, 'main_identities_pins_notes_identical_to_stage35': True,
        'source_placement_changes': sorted(changed_refs), 'physical_pose_delta': pose_delta,
        'other_85_footprints_and_pads_unchanged': True, 'usb_alias_and_pin_roles_unchanged': True,
        'changed_parts_pad_geometry_and_nets_unchanged': True,
        'footprint_count': len(actual), 'pad_count': sum(len(fp['pads']) for fp in actual.values()),
        'regenerated_floorplan_difference_count': len(differences), 'coordinate_tolerance_mm': 0.000002,
        'bom_byte_identical_to_stage35': True, 'cpl_changed_only_for_four_intended_refs': True,
        'cpl_changes': cpl_changes, 'assembly_checks': assembly_checks,
        'csv_sha256': {name: sha(assembly / name) for name in (bom_name, cpl_name)},
        'protected_inputs_unchanged': True, 'protected_input_hashes': before,
        'scope': 'Only four stage36 main source poses and provenance comments bound. Frozen stages32/35 and the routed board, schematic/project are unchanged. No refill or full build.',
        'full_build_caveat': 'The old global courtyard normalizer without the required stock model files is not the verified path. Isolated main-floorplan generation is the demonstrated reproducibility result.'
    }
    (evidence / 'verification-report.json').write_text(json.dumps(report, indent=2) + '\n')
    (evidence / 'placement-pad-snapshot.json').write_text(json.dumps(actual, indent=2, sort_keys=True) + '\n')
    print(json.dumps({key: report[key] for key in ('status', 'source_pcb_sha256', 'bound_design_sha256', 'source_placement_changes', 'footprint_count', 'pad_count', 'regenerated_floorplan_difference_count', 'bom_byte_identical_to_stage35', 'cpl_changed_only_for_four_intended_refs', 'protected_inputs_unchanged')}, indent=2))


if __name__ == '__main__':
    main()
