#!/usr/bin/env python3
"""Bounded stage35 source/placement verification; never refills or replaces routing."""
import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sys

import pcbnew


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def alias(value):
    if isinstance(value, dict):
        return {key: alias(item) for key, item in value.items()}
    if isinstance(value, list):
        return [alias(item) for item in value]
    if isinstance(value, tuple):
        return tuple(alias(item) for item in value)
    return 'USB_DN' if value == 'USB_DM' else value


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--stage32-root', type=Path, required=True)
    parser.add_argument('--sealed32-evidence', type=Path, required=True)
    parser.add_argument('--expected-pcb-sha256', required=True)
    parser.add_argument('--expected-project-sha256', required=True)
    parser.add_argument('--kicad-cli', type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    evidence = root / 'verification/main-source-synchronization'
    evidence.mkdir(parents=True, exist_ok=True)
    assert pcbnew.Version() == '10.0.7', pcbnew.Version()
    pcb = root / 'hardware/nexus-style-fc.kicad_pcb'
    project = pcb.with_suffix('.kicad_pro')
    schematic = pcb.with_suffix('.kicad_sch')
    source = root / 'tools/design.py'
    frozen_pcb = args.stage32_root / 'hardware/nexus-style-fc.kicad_pcb'
    frozen_project = frozen_pcb.with_suffix('.kicad_pro')
    frozen_source = args.sealed32_evidence / 'source/tools/design.py'
    protected = [pcb, project, schematic, frozen_pcb, frozen_project, frozen_source,
                 root / 'tools/make_footprints.py', root / 'hardware/library/NexusFC.pretty/TPS70933DBVR_TI_DBV0005A.kicad_mod']
    before = {str(path): sha(path) for path in protected}
    assert before[str(pcb)] == args.expected_pcb_sha256, 'Successor PCB changed after native verification'
    assert before[str(project)] == args.expected_project_sha256, 'Successor project changed after native verification'
    assert before[str(frozen_pcb)] == 'f214f8141e8f21a7e0983c8eb4f2be89634e3b69d0d2b168a1ac3153f28a83de'
    assert before[str(frozen_project)] == 'b34415304c2bd364fed7f2f22231db9a893f4a0a4810e0c9300f54499674ba5b'
    assert before[str(frozen_source)] == '3f452b5b65fd12a53de9dab982322df4090fceda019f11a1960888a2aeb39298'
    assert alias(json.loads(frozen_project.read_text())) == json.loads(project.read_text()), 'Project differs beyond exact USB alias'
    sync = load(Path(__file__).with_name('synchronize_main.py'), 'placement_sync')
    old = load(frozen_source, 'sealed32_design')
    sys.path.insert(0, str(root / 'tools'))
    import design
    import build_floorplan
    import pcbutil
    import export_fab
    initial_source_hash = sha(source)
    assert alias(old.PARTS) == design.PARTS, 'Legacy parts differ beyond exact USB alias'
    assert alias(old.get_main_parts()) == design.get_main_parts(), 'Main parts differ beyond exact USB alias'
    assert old.MAIN_ROUTED_PLACEMENT == design.MAIN_ROUTED_PLACEMENT
    board = pcbnew.LoadBoard(str(pcb))
    actual = sync.board_snapshot(board)
    sync.verify_identities_and_nets(design.get_main_parts(), actual)
    sealed_snapshot = json.loads((args.sealed32_evidence / 'placement-pad-snapshot.json').read_text())
    delta = sync.compare_floorplan(alias(sealed_snapshot), actual)
    assert not delta, ('Footprint/pad change beyond USB alias', delta)
    output = evidence / 'main-regenerated-floorplan.kicad_pcb'
    assert not output.exists(), 'Use a fresh verification output'
    build_floorplan.OUT = str(output)
    pcbutil.STOCK = '/usr/share/kicad/footprints'
    build_floorplan.main()
    generated = sync.board_snapshot(pcbnew.LoadBoard(str(output)))
    differences = sync.compare_floorplan(actual, generated)
    assert not differences, ('Generated source parity failure', differences)
    assembly = evidence / 'bom-cpl'
    assembly.mkdir(exist_ok=False)
    export_fab.K = str(args.kicad_cli)
    export_fab.bom_cpl('nexus-style-fc', str(pcb), 'design', str(assembly))
    assembly_check = sync.verify_bom_cpl(assembly, design.get_main_parts(), board, actual)
    csv_hashes = {}
    for name in ('nexus-style-fc-bom-jlc.csv', 'nexus-style-fc-cpl-jlc.csv'):
        previous = args.sealed32_evidence / 'verification/bom-cpl' / name
        assert (assembly / name).read_bytes() == previous.read_bytes(), ('Assembly CSV changed', name)
        csv_hashes[name] = sha(assembly / name)
    for path, expected in before.items():
        assert sha(path) == expected, ('Protected input changed', path)
    assert sha(source) == initial_source_hash, 'Source changed during check'
    # Bind only provenance comments after all comparisons pass. Part data and
    # placements above are already verified and are not rewritten.
    text = source.read_text()
    text, first = re.subn(r'^# Source PCB SHA256: [0-9a-f]{64}$', '# Source PCB SHA256: ' + args.expected_pcb_sha256, text, flags=re.M)
    text, second = re.subn(r'^# Footprint/pad placement SHA256: [0-9a-f]{64}$', '# Footprint/pad placement SHA256: ' + sync.stable_hash(actual), text, flags=re.M)
    assert (first, second) == (1, 1)
    compile(text, str(source), 'exec')
    source.write_text(text)
    rebound = load(source, 'rebound_design')
    assert rebound.PARTS == design.PARTS and rebound.get_main_parts() == design.get_main_parts()
    report = {
        'status': 'PASS: bounded successor source/placement/assembly verification; not manufacturing approval',
        'kicad_version': pcbnew.Version(),
        'source_pcb_sha256': args.expected_pcb_sha256,
        'source_project_sha256': args.expected_project_sha256,
        'source_schematic_sha256': before[str(schematic)],
        'initial_design_sha256': initial_source_hash, 'bound_design_sha256': sha(source),
        'only_source_binding_edit': 'PCB and footprint/pad provenance comments',
        'allowed_electrically_identical_net_alias': {'from': 'USB_DM', 'to': 'USB_DN'},
        'legacy_parts_unchanged_except_exact_alias': True,
        'approved_main_selection_unchanged_except_exact_alias': True,
        'source_placements_unchanged_from_sealed32': True,
        'project_unchanged_except_exact_alias': True,
        'footprints_and_pads_unchanged_from_sealed32_except_exact_alias': True,
        'footprint_count': len(actual), 'pad_count': sum(len(fp['pads']) for fp in actual.values()),
        'regenerated_floorplan_difference_count': len(differences),
        'coordinate_tolerance_mm': 0.000002,
        'bom_and_cpl_byte_identical_to_sealed32': True,
        'csv_sha256': csv_hashes, 'assembly_checks': assembly_check,
        'protected_inputs_unchanged': True, 'protected_input_hashes': before,
        'canonical_or_frozen_source_outputs_modified': False,
        'scope': 'Isolated main floorplan and BOM/CPL only; no refill, routing overwrite or global full build',
        'full_build_caveat': 'The old global courtyard normalizer without the required stock model files is not the verified path. Isolated main-floorplan generation is the demonstrated reproducibility result.'
    }
    (evidence / 'verification-report.json').write_text(json.dumps(report, indent=2) + '\n')
    (evidence / 'placement-pad-snapshot.json').write_text(json.dumps(actual, indent=2, sort_keys=True) + '\n')
    print(json.dumps({key: report[key] for key in ('status', 'source_pcb_sha256', 'source_project_sha256', 'bound_design_sha256', 'footprint_count', 'pad_count', 'regenerated_floorplan_difference_count', 'bom_and_cpl_byte_identical_to_sealed32', 'protected_inputs_unchanged')}, indent=2))


if __name__ == '__main__':
    main()
