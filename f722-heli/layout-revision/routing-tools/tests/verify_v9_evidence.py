#!/usr/bin/env python3
"""Verify V9 portable provenance and exact bytes, without PCB, JVM or solver work."""
import argparse
import ast
import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPECTED = {
    26: '697555207280b8d67714a0011a51ec355321f21f551d6a1486a786c38a671949',
    27: '940c9443957e2d059c0f46bb64dfb6833104c5c62abbdc75c30a48d763b0993f',
    28: '3afc574bdd766292932323c54fd198cc2cb88ab93617a434fe5d104ab01838d2'}

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def load(path):
    return json.loads(Path(path).read_bytes())

def run(args, ok=True):
    result = subprocess.run([str(x) for x in args], cwd=ROOT,
        env=dict(os.environ, PYTHONDONTWRITEBYTECODE='1'), capture_output=True, text=True)
    assert (result.returncode == 0) == ok, (args, result.stdout, result.stderr)
    return result

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base-project', type=Path, required=True,
        help='Exact candidate22/accepted62 functional paired source required by V8')
    parser.add_argument('--historical-workspace', type=Path)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    base_project = args.base_project.resolve()
    historical = args.historical_workspace.resolve() if args.historical_workspace else None
    projections = load(ROOT / 'checks/v9-portable-projections.json')['files']
    sources = load(ROOT / 'checks/v9-source-identity.json')
    assert sources['unfinished_source28_filtered03_excluded']
    assert sources['java_sources_byte_identical_to_v8_and_live']
    assert not sources['heavy_execution_performed']
    for name, row in projections.items():
        assert sha(ROOT / name) == row['portable_file_sha256'], name
        assert '/workspace/' not in (ROOT / name).read_text(), name
        if historical:
            assert sha(historical / row['historical_path']) == row['historical_file_sha256'], name
    for name, row in sources['sources'].items():
        assert sha(ROOT / row.get('package_source', name)) == row['sha256'], name
        if historical:
            assert sha(historical / row['historical_path']) == row['sha256'], name
    for name, digest in sources['java_sources_sha256'].items():
        assert sha(ROOT / name) == digest
        if historical:
            assert sha(historical / name) == digest

    def receipt(name):
        return load(ROOT / 'checks' / name)

    for candidate, opens in [(27, 56), (28, 55)]:
        handoff = receipt(f'candidate{candidate}-route-handoff.json')
        owner = receipt(f'candidate{candidate}-owner-summary.json')
        endpoint = receipt(f'candidate{candidate}-endpoint-audit.json')
        via = receipt(f'candidate{candidate}-existing-via-entry.json')
        power = receipt(f'candidate{candidate}-power-revalidation-required.json')
        assert handoff['board_sha256'] == owner['board_sha256'] == EXPECTED[candidate]
        assert handoff['drc'] == dict(unconnected=opens, errors=0, warnings=0, strict_schematic_parity=0)
        assert owner['drc'] == owner['drc-all'] == dict(unconnected=opens, errors=0, warnings=0)
        assert endpoint['passed'] and endpoint['source_board_sha256'] == EXPECTED[26]
        assert endpoint['candidate_board_sha256'] == EXPECTED[candidate]
        assert endpoint['existing_object_records_unchanged']
        assert not endpoint['pad_failures'] and not endpoint['via_failures'] and not endpoint['unresolved_contacts']
        assert endpoint['summary']['pad_terminations_verified'] == candidate - 26
        assert endpoint['summary']['full_width_actual_annular_strip_count'] == 2
        assert endpoint['audit_script_sha256'] == sha(ROOT / 'tests/routing-checkpoint55/audit_native_endpoints.py')
        assert via['passed'] and via['existing_via_endpoint_count'] == 1
        assert via['audit_source_sha256'] == sha(ROOT / 'tests/routing-checkpoint55/audit_existing_via_entries.py')
        assert all(row['passed'] and row['drill_void_subtracted'] and row['existing_via_unchanged'] for row in via['contacts'])
        assert power['numerical_applicability'] is False
        assert power['new_reference_holes_per_plane_since26'] == 1
        assert power['source27_fill_geometry_preserved'] == (candidate == 28)
        for gate in ['process', 'mechanical', 'parity', 'firmware']:
            assert owner[gate]['passed'] and owner[gate]['board_sha256'] == EXPECTED[candidate]
        assert owner['critical']['connected_nets'] == owner['critical']['total_nets'] == 16
        assert not owner['critical']['missing_ground_returns'] and not owner['critical']['faults']
    adopted = receipt('candidate28-owner-adoption.json')
    assert adopted['board_sha256'] == EXPECTED[28] and adopted['native_unfinished_connections'] == 55
    assert adopted['numerical_applicability'] is False
    for key, name in [('native_gate_receipt_sha256', 'owner-summary.json'),
                      ('additive_receipt_sha256', 'owner-additive-integration.json'),
                      ('actual_io_receipt_sha256', 'owner-actual-io22.json'),
                      ('reference_comparison_sha256', 'critical-reference-comparison.json')]:
        assert adopted[key] == projections['checks/candidate28-' + name]['historical_file_sha256']
    io = receipt('candidate28-owner-actual-io22.json')
    passed = [row for row in io['checks'] if row['complete_clamp_first_path_passes']]
    assert len(passed) == adopted['actual_io_complete_cases'] == 7 and len(io['checks']) == 22
    port = [row for row in passed if row['net'] == 'PORT_B_RX_EXT' and row['clamp'] == 'U14.4']
    assert len(port) == 1 and port[0]['source'] == 'J10.1' and port[0]['target'] == 'R32.1'
    assert abs(port[0]['minimum_gap_measured_mm'] - 0.3275132250445282) < 1e-12
    assert all(row['overlap_outside_actual_pad_mm2'] == 0 for row in port[0]['layer_gaps'])
    shared = receipt('candidate28-shared-pad-entry.json')
    assert shared['passed'] and shared['board_sha256'] == EXPECTED[28]
    assert shared['logical_net'] == 'PORT_B_RX_EXT::P2' and shared['pad'] == 'U14.4'
    assert shared['full_width_transverse_entry_length_mm'] > 0.089
    assert shared['audit_source_sha256'] == sha(ROOT / 'tests/routing-checkpoint55/audit_shared_pad_entry.py')
    unchanged = receipt('candidate28-unchanged-wip27-power-reference.json')
    assert unchanged['passed'] and unchanged['all_footprints_poses_saved_zones_drills_and_power_domains_exact']
    assert unchanged['new_tracks'] == 3 and unchanged['new_vias'] == 0
    reference = receipt('candidate28-critical-reference-comparison.json')
    assert reference['before_board_sha256'] == EXPECTED[26] and reference['after_board_sha256'] == EXPECTED[28]
    assert reference['critical_object_geometry_identical'] and not reference['critical_object_differences']
    assert all(value == 0 for row in reference['net_numeric_deltas_after_minus_before'].values() for value in row.values())
    assert all(row['lost_GND_overlap_with_trace_width_mm2'] == 0
        for layer in reference['ground_fill_changes'].values() for row in layer['critical_trace_proximity'].values())
    handoff = receipt('candidate28-route-handoff.json')
    assert handoff['ordinary_fully_connected_physical_nets'] == 14
    assert handoff['new_fully_connected_physical_nets'] == ['PORT_B_RX_EXT']
    assert handoff['engine_successful_connections'] == 0 and handoff['native_constructed_connections'] == 1

    zero = receipt('source28-zero-parity.json')
    zero_import = receipt('source28-imported-zero.import.json')
    fixed = receipt('source28-fixed-explicit-native-ids.json')
    fixed_contract = receipt('source28-fixed-preservation-contract.json')
    assert zero['passed'] and not zero['errors'] and zero['board_sha256'] == EXPECTED[28]
    assert zero_import['passed'] and zero_import['source_sha256'] == zero_import['output_sha256'] == EXPECTED[28]
    assert zero_import['routes_added'] == zero_import['routes_removed'] == 0
    assert len(fixed) == 5 and set(fixed).isdisjoint(fixed_contract['mutable_source_ids'])
    assert len([uid for uid in fixed if fixed_contract['source_logical_nets'][uid] == 'PORT_B_RX_EXT::P2']) == 3
    assert set(receipt('source26-fixed-pad-entry-ids.json')).issubset(fixed)
    risk = load(ROOT / 'tests/shared-pad-predicate-risk/control.json')
    assert risk['passed'] and risk['synthetic_only'] and not risk['route_solver_used']
    assert not risk['whole_transaction_executed'] and risk['stock_rejects_fixed_foreign_trace']
    assert risk['direct_stock_cutout_removed_user_fixed_source'] and risk['after'][0]['fixed'] == 'NOT_FIXED'

    recovery_path = ROOT / 'sessions/recovery55/rebuild_historical_source.py'
    spec = importlib.util.spec_from_file_location('v9_recovery', recovery_path)
    recovery = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(recovery)
    negative, recovered, packets = [], [], []

    def reject(label, operation):
        try:
            operation()
        except (ValueError, KeyError, FileNotFoundError, AssertionError):
            negative.append(label)
        else:
            raise AssertionError('Bad input accepted: ' + label)

    with tempfile.TemporaryDirectory(prefix='v9-evidence-') as temp:
        tmp = Path(temp)
        source26 = tmp / 'candidate26'
        run([sys.executable, '-B', ROOT / 'sessions/recovery57/rebuild_historical_source.py',
             'project', '--base-project', base_project, '--source', 'candidate26', '--out', source26])
        assert sha(source26 / 'f722-heli.kicad_pcb') == EXPECTED[26]
        recovered.append({'candidate': 26, 'board_sha256': EXPECTED[26], 'functional_paired_files': 62})
        for c in [27, 28]:
            output = tmp / f'candidate{c}'
            run([sys.executable, '-B', recovery_path, 'project', '--base-project', source26,
                 '--source', f'candidate{c}', '--out', output])
            assert sha(output / 'f722-heli.kicad_pcb') == EXPECTED[c]
            count = len([p for p in output.rglob('*') if p.is_file()])
            assert count == 62
            recovered.append({'candidate': c, 'board_sha256': EXPECTED[c], 'functional_paired_files': count})
        for c, source, name in [(27, 26, 'engine56'), (28, 27, 'accepted55')]:
            packet = ROOT / 'sessions' / name
            identity = load(packet / 'source-identity.json')
            assert identity['board_sha256'] == EXPECTED[source] and identity['candidate_sha256'] == EXPECTED[c]
            assert sha(ROOT / identity['importer_source_path']) == identity['importer_source_sha256']
            funcs = {'parse', 'children', 'child', 'ses_routes', 'nm', 'key', 'from_snapshot'}
            def parser_ast(path):
                return [ast.dump(node, include_attributes=False) for node in ast.parse(path.read_text()).body
                        if isinstance(node, ast.FunctionDef) and node.name in funcs]
            assert parser_ast(ROOT / 'import_session.py') == parser_ast(ROOT / identity['importer_source_path'])
            result_path = tmp / f'packet{c}.json'
            run([sys.executable, '-B', ROOT / 'tests/verify_session_packet.py', '--packet', packet, '--out', result_path])
            packet_result = load(result_path)
            contract = load(packet / 'import-contract.json')
            report = load(packet / 'engine-report.json')
            native = receipt(f'candidate{c}-f722-heli.import.json')
            assert native['source_sha256'] == EXPECTED[source] and native['output_sha256'] == EXPECTED[c]
            assert native['session_sha256'] == identity['session_sha256'] and native['model_sha256'] == identity['model_sha256']
            assert native['routes_added'] == identity['new_tracks'] + identity['new_vias']
            assert native['routes_removed'] == 0 and native['reference_plane_refill_performed'] == (c == 27)
            if c == 27:
                receipt27 = load(packet / 'selected-checkpoint-receipt.json')
                lineage = receipt('candidate27-engine-lineage.json')
                assert receipt27['session_sha256'] == lineage['engine_session_sha256'] == identity['session_sha256']
                assert receipt27['report_sha256'] == identity['historical_engine_report_sha256']
                assert receipt27['route_counters']['routed_count'] == report['route_counters']['routed_count'] == 1
                assert lineage['selected_engine_connections'] == ['NRST: existing U1.7/C10.1 group to R1.2']
                assert set(receipt('source26-fixed-pad-entry-ids.json')).isdisjoint(contract['mutable_source_ids'])
            else:
                construction = load(packet / 'native-construction.json')
                original_contract = load(packet / 'original-import-contract.json')
                proposal = load(ROOT / 'tests/located-portb-rx26/proposal-on27.json')
                original_proposal = load(ROOT / 'tests/located-portb-rx26/proposal.json')
                refusal = load(ROOT / 'tests/located-portb-rx26/located-receipt.json')
                log_records = [json.loads(line[len('INSERT_DIAGNOSTIC '):]) for line in
                    (ROOT / 'tests/located-portb-rx26/captured-engine.log').read_text().splitlines()]
                assert log_records == refusal['records']
                assert proposal['source_identity']['engine_log']['sha256'] == projections['tests/located-portb-rx26/captured-engine.log']['historical_file_sha256']
                assert not construction['engine_routing_performed'] and not report['route_solver_used']
                assert not construction['source_objects_removal_allowed'] and not construction['refill_allowed']
                assert construction['new_tracks'] == 3 and construction['new_vias'] == 0
                assert construction['model_sha256'] == identity['model_sha256']
                assert construction['session_sha256'] == identity['session_sha256']
                assert construction['preparer_sha256'] == sha(ROOT / 'prepare_screened_local.py')
                assert construction['proposal_sha256'] == projections['tests/located-portb-rx26/proposal-on27.json']['historical_file_sha256']
                assert all(original_contract[key] == value for key, value in contract.items())
                assert not contract['mutable_source_ids'] and not contract['regenerable_reference_zones']
                assert original_contract['all_source_copper_fixed']
                assert proposal['source_identity']['screen']['sha256'] == sha(ROOT / 'prepare_located_branch_continuation.py')
                assert proposal['board_sha256'] == EXPECTED[27] and original_proposal['board_sha256'] == refusal['board_sha256'] == EXPECTED[26]
                assert proposal['proposals'] == original_proposal['proposals']
                assert proposal['engine_provenance']['additional_native_copper_and_drills_rechecked']
                assert proposal['engine_provenance']['source_model_is_topology_template_only']
                assert any(row['stage'] == 'failed_forced_trace_polyline' and row['failing_obstacle']['fixed'] == 'USER_FIXED'
                           and row['failing_obstacle']['nets'] == ['PORT_B_RX_EXT::P1'] for row in refusal['records'])
                assert all(row['net'] == 'PORT_B_RX_EXT::P2' for row in refusal['records'])
                assert packet_result['mutable_route_segments'] == 3 and packet_result['mutable_route_vias'] == 0
                assert all(route['nets'] == ['PORT_B_RX_EXT::P2'] and route['layer'] == 'F.Cu' for route in report['routes'])
            if historical:
                full_model = load(historical / identity['historical_model_path'])
                assert sha(historical / identity['historical_model_path']) == identity['model_sha256']
                assert all(full_model[key] == value for key, value in contract.items())
            board = tmp / f'candidate{source}/f722-heli.kicad_pcb'
            replay = tmp / f'projection{c}'
            run([sys.executable, '-B', ROOT / 'prepare_session_replay.py', '--packet', packet,
                 '--source-board', board, '--out', replay])
            bound = load(replay / 'engine-report.json')
            assert bound['model_sha256'] == sha(replay / 'model.json')
            assert bound['origin_engine_report_sha256'] == identity['engine_report_sha256']
            wrong = tmp / f'wrong{c}.kicad_pcb'
            wrong.write_bytes(board.read_bytes() + b'\n')
            run([sys.executable, '-B', ROOT / 'prepare_session_replay.py', '--packet', packet,
                 '--source-board', wrong, '--out', tmp / f'bad-source{c}'], False)
            negative.append(f'candidate{c}:wrong source board')
            for filename in ['session.ses', 'engine-report.json', 'import-contract.json']:
                altered = tmp / f'tampered{c}-{filename}'
                shutil.copytree(packet, altered)
                (altered / filename).write_bytes((altered / filename).read_bytes() + b'\n')
                run([sys.executable, '-B', ROOT / 'prepare_session_replay.py', '--packet', altered,
                     '--source-board', board, '--out', tmp / f'bad{c}-{filename}'], False)
                negative.append(f'candidate{c}:tampered {filename}')
            packets.append({'packet': 'sessions/' + name, 'ses_report_geometry_equal': True,
                'projection_rebinding_verified': True, 'exact_paired_source_recovered': True,
                'new_tracks': identity['new_tracks'], 'new_vias': identity['new_vias'],
                'engine_insertion_succeeded': identity['engine_insertion_succeeded'], 'native_replay_executed': False})
        delta = load(ROOT / 'sessions/recovery55/candidate28.f722-heli.kicad_pcb.delta.json')
        base = (source26 / 'f722-heli.kicad_pcb').read_bytes()
        for label, bad_base, bad_delta in [
            ('wrong recovery board', base + b'\n', delta),
            ('wrong target hash', base, dict(delta, target_sha256='0' * 64)),
            ('out-of-range copy', base, dict(delta, operations=[[0, len(base) + 1]])),
            ('invalid operation', base, dict(delta, operations=[{'exec': 'forbidden'}])),
            ('unsupported transform', base, dict(delta, base_transform='forbidden'))]:
            reject(label, lambda b=bad_base, d=bad_delta: recovery.reconstruct(b, d))
        bad_project = tmp / 'bad-paired'
        shutil.copytree(source26, bad_project)
        target = bad_project / 'f722-heli.kicad_pro'
        target.write_bytes(target.read_bytes() + b'\n')
        reject('tampered paired project file', lambda: recovery.prepare_project(bad_project, 'candidate28', ROOT / 'sessions/recovery55'))
        for path in ['../escape', '/absolute', 'safe/../escape', 'windows\\escape']:
            reject('unsafe recovery path:' + path, lambda p=path: recovery.relative_path(p))
    result = {'passed': True, 'verifier_source_sha256': sha(__file__),
        'scope': 'Portable identity, historical receipt binding, exact paired byte recovery, actual engine and explicit construction packet parsing; no fresh native qualification.',
        'base_manifest_sha256': sources['base_manifest_sha256'], 'recovered_projects': recovered,
        'packets': packets, 'negative_controls_passed': len(negative), 'negative_controls': negative,
        'original_source_hash_checks_performed': bool(historical),
        'native_replay_reexecuted': False, 'native_DRC_reexecuted': False,
        'endpoint_geometry_reexecuted': False, 'JVM_router_refill_or_power_solve_executed': False,
        'numerical_power_and_VCAP_applicability': False, 'native_open_connections': 55,
        'native_errors': 0, 'native_warnings': 0}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))

if __name__ == '__main__':
    main()
