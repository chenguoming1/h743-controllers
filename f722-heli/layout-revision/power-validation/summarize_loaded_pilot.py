#!/usr/bin/env python3
"""Summarize completed loaded pilot evidence without meshing or solving a board."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def canonical(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                    ensure_ascii=True, allow_nan=False).encode()).hexdigest()


def summarize(result_path, freeze_path, ledger_path):
    result = json.loads(result_path.read_text())
    freeze = json.loads(freeze_path.read_text())
    ledger = json.loads(ledger_path.read_text())
    assert result['freeze_sha256'] == sha(freeze_path)
    assert result['ledger_sha256'] == sha(ledger_path)
    assert ledger['freeze_manifest_sha256'] == sha(freeze_path)
    assert result['board_sha256'] == freeze['files']['board']['sha256']
    for row in freeze['files'].values():
        assert sha(freeze_path.parent / row['path']) == row['sha256']
    for name, expected in freeze['analysis_source_sha256'].items():
        assert sha(freeze_path.parent / 'solver-source' / name) == expected
    assert [r['spacing_mm'] for r in result['runs']] == ledger['mesh_spacings_mm']
    expected_cases = [c['name'] for c in ledger['cases']]
    definition_by_name = {c['name']: c for c in ledger['cases']}
    for case in ledger['cases']:
        assert canonical({k: v for k, v in case.items() if k != 'case_definition_sha256'}) == case['case_definition_sha256']
    for run in result['runs']:
        assert [c['case'] for c in run['cases']] == expected_cases
        assert [b['net'] for b in run['ports']] == [n['net'] for n in ledger['networks']]
        for case in run['cases']:
            assert case['case_definition_sha256'] == definition_by_name[case['case']]['case_definition_sha256']
            assert set(case['fields']) == set(definition_by_name[case['case']]['nets'])
    certs = result['geometry_certificates']
    certificate_hashes = {name: canonical(cert) for name, cert in certs.items()}
    reference_count = 0
    for run in result['runs']:
        blocks = run['ports'] + [field for case in run['cases'] for field in case['fields'].values()]
        for block in blocks:
            for reference in block['native_edge_noding_refs'].values():
                assert reference['sha256'] == certificate_hashes[reference['certificate_key']]
                reference_count += 1
    fine = result['runs'][-1]
    margins = result['voltage_margin_checks']
    fields = [f for run in result['runs'] for c in run['cases'] for f in c['fields'].values()]
    linear = [f['linear_solver_diagnostics'] for f in fields]
    assert all(d['last_direct_solve']['converged'] for d in linear)
    cases_all = [c for run in result['runs'] for c in run['cases']]

    def family(name):
        for prefix in ['classic_BEC', 'capacity_BEC', 'usb_configuration', 'same_BEC']:
            if name.startswith(prefix):
                return prefix
        raise AssertionError('Unexpected case family: ' + name)

    def extrema(cases, category):
        grouped = {}
        for case in cases:
            for probe in case[category]:
                grouped.setdefault(probe['name'], []).append((probe['voltage_V'], case['case']))
        return {name: {'minimum_V': min(rows)[0], 'minimum_case': min(rows)[1],
                       'maximum_V': max(rows)[0], 'maximum_case': max(rows)[1]}
                for name, rows in grouped.items()}

    families = {}
    for name in sorted({family(c['case']) for c in fine['cases']}):
        cases = [c for c in fine['cases'] if family(c['case']) == name]
        families[name] = {'cases': len(cases), 'static_probe_pass_cases': sum(c['static_probe_pass'] for c in cases),
                          'acceptance_probes': extrema(cases, 'probes'),
                          'report_only_probes': extrema(cases, 'report_only_probes')}
    sample = next(c for c in fine['cases'] if c['case'] == 'classic_BEC5_AB_mcu_vdd19_baseline')
    v = sample['voltage_V']
    bec = sample['fields']['+5V_BEC']
    representatives = []
    for c in fine['cases']:
        if family(c['case']) == 'same_BEC':
            representatives.append({'case': c['case'],
               'lead_current_A': {r['name']: r['current_A'] for r in c['resistors'] if 'lead_contact' in r['name']},
               'servo_pad_voltage_V': {p['name']: p['voltage_V'] for p in c['probes'] if 'servo_board_pad' in p['name']},
               'probes': c['probes'], 'report_only_probes': c['report_only_probes'], 'power_W': c['power_W']})
    return {
        'schema': 'f722-loaded-pilot-summary/v1',
        'status': 'completed numerical diagnostic; locked conditional screen failed',
        'board_sha256': result['board_sha256'], 'result_sha256': sha(result_path),
        'freeze_sha256': sha(freeze_path), 'ledger_sha256': sha(ledger_path),
        'summarizer_sha256': sha(__file__),
        'scope': result['scope'], 'scope_is_final_board': False,
        'conditional_static_screen_pass': result['conditional_static_screen_pass'],
        'thermal_or_flight_qualification': False,
        'verification': {'frozen_input_hashes_checked': len(freeze['files']),
                         'runtime_source_hashes_checked': len(freeze['analysis_source_sha256']),
                         'geometry_certificate_references_checked': reference_count,
                         'case_definition_hashes_checked': len(cases_all)},
        'mesh_spacings_mm': ledger['mesh_spacings_mm'], 'material': result['material'],
        'convergence_requirements': ledger['convergence'],
        'cases_per_grid': len(expected_cases), 'networks_per_grid': len(ledger['networks']),
        'contacts': sum(len(n['contacts']) for n in ledger['networks']),
        'impedance_sensitivity': result['impedance_sensitivity'],
        'voltage_checks': {'total': len(margins),
            'negative_threshold_margin_count': sum(m['margin_V'] < 0 for m in margins),
            'grid_change_over_locked_tolerance_count': sum(m['change_V'] > ledger['convergence']['absolute_voltage_V'] for m in margins),
            'failed_combined_checks': sum(not m['pass'] for m in margins),
            'maximum_grid_change_V': max(m['change_V'] for m in margins),
            'negative_margin_by_probe': dict(Counter(m['probe'] for m in margins if m['margin_V'] < 0)),
            'over_tolerance_by_probe': dict(Counter(m['probe'] for m in margins if m['change_V'] > ledger['convergence']['absolute_voltage_V']))},
        'families_fine_grid': families,
        'representative_peripheral_path': {
            'case': sample['case'], 'U6_output_absolute_V': v['U6.OUT_7_8'],
            'R54_sense_top_absolute_V': v['R54.1'], 'U7_input_absolute_V': v['U7.3'],
            'BEC_copper_source_to_U7_drop_V': v['U6.OUT_7_8'] - v['U7.3'],
            'U7_explicit_device_drop_V': v['U7.3'] - v['U7.2'],
            'peripheral_positive_copper_to_J9_drop_V': v['U7.2'] - v['J9.3'],
            'J9_return_above_source_V': v['J9.4'],
            'J9_differential_pad_V': v['J9.3'] - v['J9.4'],
            'BEC_copper_loss_W': bec['copper_loss_W'],
            'BEC_layer_sheet_loss_W': bec['layer_sheet_loss_W'],
            'all_net_copper_loss_W': {n: f['copper_loss_W'] for n, f in sample['fields'].items()},
            'converters': sample['converters'], 'power_W': sample['power_W']},
        'same_BEC_illustrations_fine_grid': representatives,
        'observed_numerical_extrema': {
            'maximum_condensed_mesh_equations': max(f['nodes'] for f in fields),
            'maximum_triangles': max(f['triangles'] for f in fields),
            'maximum_field_KCL_residual_A': max(f['KCL_max_residual_A'] for f in fields),
            'maximum_field_energy_error_W': max(abs(f['copper_loss_W'] - f['port_power_W']) for f in fields),
            'maximum_linear_residual_to_required_ratio': max(d['last_direct_solve']['residual_norm_history_A'][-1] / d['last_direct_solve']['required_residual_norm_A'] for d in linear),
            'maximum_refinement_steps': max(d['last_direct_solve']['refinement_steps'] for d in linear),
            'maximum_circuit_equation_residual': max(c['equation_residual_max'] for c in cases_all),
            'maximum_circuit_power_balance_error_W': max(abs(c['power_W']['balance_error']) for c in cases_all),
            'maximum_reciprocity_error_ohm': max(b['reciprocity_error_ohm'] for r in result['runs'] for b in r['ports']),
            'maximum_factor_stored_array_bytes': max(d['factorization']['factor_stored_array_bytes'] for d in linear),
            'maximum_factor_nonzeros': max(d['factorization']['factor_nonzeros'] for d in linear),
            'maximum_recorded_process_peak_RSS_bytes': max(d['factorization']['process_peak_RSS_bytes'] for d in linear)},
        'geometry': {'certificates': len(certs),
            'native_vertices_changed': sum(c['native_vertices_changed'] for c in certs.values()),
            'maximum_derived_vertex_displacement_mm': max(c['maximum_derived_vertex_displacement_mm'] for c in certs.values()),
            'retained_single_line_subdivisions': sum(c['retained_single_line_subdivisions'] for c in certs.values()),
            'positive_area_elements_discarded': sum(f['element_geometry']['positive_area_elements_discarded'] for f in fields)},
        'limitations': result['limitations'] + [
            'Voltage sensitivity exceeds the locked 1 mV tolerance; no completed voltage convergence or acceptance is claimed.',
            'Large peripheral deficits are provisional route diagnostics, not qualified device voltage predictions.',
            'Modeled harness profiles are illustrative; measured harness remains unset.',
            'High servo DC illustrations exceed the stated source continuous capability and have no assigned duration.',
            'USB configuration has external DSM, ABC and servo loads disconnected; input below 4.3 V does not establish receiver regulation.',
            'This subset omits broader converter efficiency, leakage, effective on-resistance, line/load, 12.6 V and upper-corner reviews.',
            'Dependent weakest-allocation slices remain disabled pending an accepted source-bound baseline.']}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ['result', 'freeze', 'ledger', 'out']:
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    summary = summarize(args.result, args.freeze, args.ledger)
    args.out.write_text(json.dumps(summary, indent=2, allow_nan=False) + '\n')
    print(json.dumps({'summary_sha256': sha(args.out), 'bytes': args.out.stat().st_size,
                      'result_sha256': summary['result_sha256'], 'voltage_checks': summary['voltage_checks']}))
