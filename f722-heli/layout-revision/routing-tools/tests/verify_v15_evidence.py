#!/usr/bin/env python3
"""Bounded standard-library V15 paired recovery and evidence checks; no native replay."""
import argparse
import ast
import contextlib
import copy
import hashlib
import importlib.util
import io
import json
import re
import runpy
import sys
import tempfile
import types
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def read(path):
    return json.loads(Path(path).read_bytes())

def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--base-project', type=Path, required=True)
    ap.add_argument('--historical-workspace', type=Path)
    ap.add_argument('--out', type=Path, required=True)
    args = ap.parse_args()
    ident = read(ROOT / 'checks/v15-source-identity.json')
    recovery = module('recovery44', ROOT / 'sessions/recovery44/rebuild_historical_source.py')
    raw = module('raw44', ROOT / 'tests/checkpoint44/materialize.py')
    negatives, recovered = [], []

    def reject(name, operation):
        try:
            operation()
        except (ValueError, KeyError, AssertionError, FileNotFoundError):
            negatives.append(name)
        else:
            raise AssertionError('Invalid input accepted: ' + name)

    with raw.Evidence() as evidence, tempfile.TemporaryDirectory(prefix='v15-evidence-') as td:
        tmp = Path(td)
        j, index = evidence.json, evidence.index['files']
        excluded, rec = evidence.index['excluded_files'], evidence.index['recovered_files']
        c43, c44 = 'ordinary-routing/candidate43/', 'ordinary-routing/candidate44/'

        def original(name):
            for group in [index, excluded, rec]:
                if name in group:
                    return group[name]['sha256']
            raise KeyError(name)

        for name in index:
            evidence.put(name, tmp)
            if args.historical_workspace:
                assert sha(args.historical_workspace / name) == index[name]['sha256'], name
        for name in excluded:
            reject('excluded raw bytes unavailable: ' + name, lambda name=name: evidence.bytes(name))
            if args.historical_workspace:
                assert sha(args.historical_workspace / name) == excluded[name]['sha256'], name
        for label, digest in ident['expected_boards'].items():
            outputs = recovery.prepare_project(args.base_project.resolve(), label, ROOT / 'sessions/recovery44')
            out = tmp / 'ordinary-routing' / label
            for relative, data in outputs.items():
                dest = out / relative
                dest.parent.mkdir(parents=True, exist_ok=True)
                if dest.exists():
                    assert dest.read_bytes() == data
                dest.write_bytes(data)
            assert len(outputs) == 61 and sha(out / 'f722-heli.kicad_pcb') == digest
            recovered.append({'source': label, 'board_sha256': digest, 'paired_files': len(outputs)})
        source, board = ident['expected_boards']['candidate43'], ident['expected_boards']['candidate44']
        handoff = j(c44 + 'route-handoff.json')
        assert original(c44 + 'route-handoff.json') == ident['sealed_handoff_sha256'] and len(handoff['files']) == 47
        for name, digest in handoff['files'].items():
            assert original(c44 + name) == digest, name
        assert handoff['all_156_footprints_exact'] and handoff['source_native_records_exact'] == 1902
        assert handoff['completed_net'] == 'DSM_RX_MCU' and handoff['completed_terminals'] == ['R38.2', 'R71.2', 'U1.43']
        assert (handoff['actual_io_passed'], handoff['actual_io_total'], handoff['actual_io_channels_passed'], handoff['actual_io_channels_total']) == (11, 22, 9, 20)
        native, adoption = j(c44 + 'owner-summary.json'), j(c44 + 'owner-adoption.json')
        assert native['drc'] == native['drc-all'] == dict(unconnected=35, errors=0, warnings=0)
        assert native['board_sha256'] == adoption['board_sha256'] == board
        assert adoption['native_unfinished_connections'] == 35 and not adoption['numerical_applicability']
        for field, name in [('native_gate_receipt_sha256', c44 + 'owner-summary.json'), ('integration_receipt_sha256', 'checkpoint35-review/owner-coordinated-integration.json'), ('reference_comparison_sha256', 'checkpoint35-review/comparison-37-to-35.json'), ('actual_io_receipt_sha256', c44 + 'protection-actual-io.json')]:
            assert adoption[field] == original(name)
        for section in ['process', 'mechanical', 'parity', 'firmware']:
            assert native[section]['passed'] and native[section]['board_sha256'] == board
        assert native['critical']['connected_nets'] == native['critical']['total_nets'] == 16
        assert not native['critical']['faults'] and not native['critical']['missing_ground_returns']
        actual = j('checkpoint35-review/actual-io22.json')
        assert actual['board_sha256'] == board and (actual['passed'], actual['total'], actual['all_pass']) == (11, 22, False)

        construction = j(c44 + 'construction-provenance.json')
        transaction = j(c44 + 'coordinated-change-receipt.json')
        proposal = j(c44 + 'complete-tree-proposal.json')
        assert construction['source_board_sha256'] == transaction['source_board_sha256'] == proposal['source_board_sha256'] == source
        assert construction['board_sha256'] == transaction['board_sha256'] == board
        assert construction['constructor_sha256'] == original(c44 + 'construct_dsm_tree44.used.py') == original('ordinary-routing/construct_dsm_tree44.py')
        assert construction['proposal_sha256'] == original(c44 + 'complete-tree-proposal.json')
        assert proposal['script_sha256'] == original('ordinary-routing/tests/dsm-mcu-candidate43/build_complete_proposal.py')
        for name, digest in proposal['input_sha256'].items():
            assert original('ordinary-routing/' + name) == digest
        assert proposal['all_nominal_geometry_passed'] and not proposal['footprint_changes']
        assert construction['removed_source_records'] == transaction['removed_source_records']
        assert {x['uuid']: x for x in construction['added_records']} == {x['uuid']: x for x in transaction['added_candidate_records']}
        assert len(construction['removed_source_records']) == 2 and len(construction['added_records']) == 37
        assert construction['changed_pad_records'] == construction['changed_footprint_records'] == []
        assert construction['all_other_source_native_objects_exact'] == transaction['all_other_source_objects_exact'] == 1902
        assert construction['all_156_footprints_exact'] and construction['all_existing_signal_objects_exact'] and construction['all_GND_native_objects_exact']
        assert construction['BEC_width_preserved_mm'] == .6 and not construction['engine_routing_succeeded']
        assert not transaction['engine_success_claimed'] and not transaction['numerical_power_VCAP_applicable']
        imported = j(c44 + 'f722-heli.import.json')
        for field, name in [('coordinated_change_receipt_sha256', 'coordinated-change-receipt.json'), ('construction_provenance_sha256', 'construction-provenance.json'), ('logical_route_map_sha256', 'f722-heli.logical-route-map.json')]:
            assert imported[field] == original(c44 + name)
        assert imported['source_sha256'] == source and imported['output_sha256'] == board and not imported['direct_engine_output']

        # Check stored full finite-width/native evidence, without substituting it for replay.
        audit = j(c44 + 'candidate44-entry-support.json')
        assert audit == j('ordinary-routing/dsm44-audits/candidate44-entry-support.json')
        assert audit['script_sha256'] == original('ordinary-routing/dsm44-audits/audit_dsm44_entries_support.py')
        assert audit['input_manifest_sha256'] == original('ordinary-routing/dsm44-audits/input-hashes.json')
        assert audit['input_hashes'] == j('ordinary-routing/dsm44-audits/input-hashes.json')
        for name, digest in audit['input_hashes'].items():
            assert original('ordinary-routing/' + name) == digest
        assert audit['passed'] and len(audit['gates']) == 12 and all(x is True for x in audit['gates'].values())
        assert len(audit['strict_pad_entries']) == 3 and {x['pad'] for x in audit['strict_pad_entries']} == {'R38.2', 'R71.2', 'U1.43'}
        assert not audit['direct_pad_entry_failures_preserved']
        for row in audit['strict_pad_entries']:
            assert row['passed'] and row['width_mm'] == .127 and row['transverse_entry_length_mm'] > 0
            assert row['finite_full_width_strips'] and all(x['length_mm'] > 0 and x['area_outside_actual_pad_mm2'] == 0 and x['boundary_reserve_mm'] > 0 for x in row['finite_full_width_strips'])
        assert len(audit['finite_actual_annular_entries']) == 10 and len(audit['signal_via_inventory']) == 5
        for row in audit['finite_actual_annular_entries']:
            assert row['passed'] and row['outward_drill_void_subtracted'] and row['actual_annular_centerline_length_mm'] > 0
            assert row['finite_full_width_annular_strips'] and all(x['full_width_actual_annulus_section'] and x['full_width_strip_length_mm'] > 0 and x['strip_area_outside_actual_annulus_mm2'] == 0 for x in row['finite_full_width_annular_strips'])
        assert len(audit['new_track_endpoint_classification']) == 64 and all(x['resolved'] for x in audit['new_track_endpoint_classification'])
        assert len(audit['BEC_replacement_retained_track_joins']) == 2
        assert all(x['passed'] and x['required_width_mm'] == .6 and x['retained_source_records_exact'] for x in audit['BEC_replacement_retained_track_joins'])
        assert all(x['passed'] for x in audit['full_width_signal_and_BEC_joins'])
        assert len(audit['negative_controls']) == 22 and all(x['rejected'] for x in audit['negative_controls'])
        assert audit['DSM_RX_MCU']['passed'] and len(audit['DSM_RX_MCU']['source_groups']) == 3
        assert audit['DSM_RX_MCU']['candidate_groups'][0]['pads'] == ['R38.2', 'R71.2', 'U1.43']
        assert len(audit['DSM_RX_MCU']['candidate_groups']) == 1
        assert audit['source_D7_cut_exactly_equal'] and audit['actual_D7_pad_cut']['complete_clamp_first_path_passes']

        # Keep the established owner adapter intact; full-entry binding is separate.
        support = module('support44', tmp / 'integrated-routing/verify_support_adoption.py')
        wrapper, prior = j(c44 + 'power-audit.json'), j(c43 + 'power-audit.json')
        compatibility = support.verify(wrapper, prior, source, board, tmp / c44)
        assert compatibility == {'passed': True, 'nets': 28, 'typed_audit_binding_checked': False}
        saved = j(c44 + 'support-wrapper-compatibility.json')
        assert saved['support_wrapper_sha256'] == original(c44 + 'power-audit.json')
        assert saved['verifier_sha256'] == original('integrated-routing/verify_support_adoption.py')
        assert all(saved[k] == v for k, v in compatibility.items())

        def full_binding(w, a):
            assert w['schema'] == 'f722-native-support-audit/v1' and w['passed'] is True
            assert w['board_sha256'] == a['board_sha256'] == board
            assert w['source_board_sha256'] == a['source_board_sha256'] == source
            assert w['native_sha256'] == a['candidate_native_sha256'] == original(c44 + 'f722-heli.native.json')
            assert w['source_native_sha256'] == a['source_native_sha256'] == original(c43 + 'f722-heli.native.json')
            assert w['audit'] == 'candidate44-entry-support.json'
            assert w['audit_sha256'] == original(c44 + 'candidate44-entry-support.json')
            assert w['source_audit_sha256'] == original(c43 + 'power-audit.json')
            assert w['audit_source_sha256'] == a['script_sha256'] == original(c44 + 'audit_dsm44_entries_support.py')
            assert a['passed'] is True and len(a['gates']) == 12 and all(v is True for v in a['gates'].values())
            assert w['numerical_power_VCAP_applicable'] is False and a['numerical_power_VCAP_applicable'] is False
            assert len(w['nets']) == len(a['nets']) == 28 and set(w['nets']) == set(a['nets']) == set(prior['nets'])
            for net, row in w['nets'].items():
                proof = a['nets'][net]
                assert proof['passed'] and proof['source_groups_match_prior_wrapper'] and proof['source_groups_exactly_preserved']
                assert row['groups'] == proof['groups'] == prior['nets'][net]['groups']
                assert row['pad_group_count'] == len(row['groups']) == 1
                assert row['complete'] is True and row['source_groups_exactly_preserved'] is True
            support.verify(w, prior, source, board, tmp / c44)

        full_binding(wrapper, audit)
        for name, field, value in [('wrong wrapper board', 'board_sha256', source), ('wrong wrapper native export', 'native_sha256', '0' * 64), ('stale full-entry receipt', 'audit_sha256', '0' * 64), ('wrong source audit', 'source_audit_sha256', '0' * 64), ('wrong audit script', 'audit_source_sha256', '0' * 64), ('numerical qualification escalation', 'numerical_power_VCAP_applicable', True)]:
            mutant = copy.deepcopy(wrapper)
            mutant[field] = value
            reject(name, lambda mutant=mutant: full_binding(mutant, audit))
        for name, field, value in [('missing derived support count', 'pad_group_count', 0), ('false derived support completion', 'complete', False), ('changed support partition', 'groups', [])]:
            mutant = copy.deepcopy(wrapper)
            mutant['nets']['+3V3_CORE'][field] = value
            reject(name, lambda mutant=mutant: full_binding(mutant, audit))
        mutant = copy.deepcopy(audit)
        mutant['gates']['all_three_direct_finite_full_width_pad_entries'] = False
        reject('failed full-entry gate', lambda: full_binding(wrapper, mutant))

        # Load only the exact pure KiCad parser; no pcbnew import or native operation.
        path = tmp / 'ordinary-routing/tests/mpn-parity/apply_metadata_copy.py'
        parsed_module = ast.parse(path.read_text())
        wanted = {'Atom', 'Node', 'parse', 'children', 'child', 'value', 'properties', 'shape'}
        nodes = [node for node in parsed_module.body if (isinstance(node, (ast.ClassDef, ast.FunctionDef)) and node.name in wanted) or (isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id == 'TOKEN' for target in node.targets))]
        parser = types.ModuleType('apply_metadata_copy')
        parser.__dict__.update(re=re, json=json)
        exec(compile(ast.Module(body=nodes, type_ignores=[]), str(path), 'exec'), parser.__dict__)
        sys.modules['apply_metadata_copy'] = parser
        parsed = {label: parser.parse((tmp / 'ordinary-routing' / label / 'f722-heli.kicad_pcb').read_text()) for label in ['candidate43', 'candidate44']}

        def copper(root):
            return {parser.value(node, 'uuid'): node for kind in ['segment', 'via', 'arc'] for node in parser.children(root, kind)}

        old, new = copper(parsed['candidate43']), copper(parsed['candidate44'])
        removed, added = set(old) - set(new), set(new) - set(old)
        assert removed == set(proposal['remove_copper_uuids']) == {x['uuid'] for x in construction['removed_source_records']}
        assert added == {x['uuid'] for x in construction['added_records']} and len(added) == 37
        assert len(set(old) & set(new)) == 1344 and all(parser.shape(old[k]) == parser.shape(new[k]) for k in set(old) & set(new))
        assert all(parser.value(old[k], 'net') == '+5V_BEC' and float(parser.value(old[k], 'width')) == .6 for k in removed)
        expected = {}
        for row in proposal['paths']:
            for i, (start, end) in enumerate(zip(row['points_mm'], row['points_mm'][1:])):
                label = row['label'] + '/' + str(i)
                uid = str(uuid.uuid5(uuid.NAMESPACE_URL, source + '/' + original(c44 + 'complete-tree-proposal.json') + '/' + label))
                node = new[uid]
                assert node.items[0].value == 'segment' and parser.value(node, 'net') == row['net']
                assert [float(v.value) for v in parser.child(node, 'start').items[1:]] == start
                assert [float(v.value) for v in parser.child(node, 'end').items[1:]] == end
                assert float(parser.value(node, 'width')) == row['width_mm'] == (.6 if row['net'] == '+5V_BEC' else .127)
                assert parser.value(node, 'layer') == row['layer']
                expected[uid] = {'uuid': uid, 'net': row['net'], 'proposal_record': label}
        for row in proposal['vias']:
            label = row['label'] + '/via'
            uid = str(uuid.uuid5(uuid.NAMESPACE_URL, source + '/' + original(c44 + 'complete-tree-proposal.json') + '/' + label))
            node = new[uid]
            assert node.items[0].value == 'via' and parser.value(node, 'net') == row['net'] == 'DSM_RX_MCU'
            assert [float(v.value) for v in parser.child(node, 'at').items[1:]] == row['xy_mm']
            assert float(parser.value(node, 'size')) == row['diameter_mm'] == .45
            assert float(parser.value(node, 'drill')) == row['drill_mm'] == .2
            assert parser.shape(parser.child(node, 'layers')) == ['layers', 'F.Cu', 'B.Cu']
            assert parser.shape(parser.child(node, 'tenting')) == ['tenting', ['front', 'yes'], ['back', 'yes']]
            expected[uid] = {'uuid': uid, 'net': row['net'], 'proposal_record': label}
        assert set(expected) == added and len(proposal['vias']) == 5
        assert {x['uuid']: x for x in construction['added_proposal_correspondence']} == expected
        footprints = {label: {parser.value(node, 'uuid'): parser.shape(node) for node in parser.children(root, 'footprint')} for label, root in parsed.items()}
        assert footprints['candidate43'] == footprints['candidate44'] and len(footprints['candidate44']) == 156
        pad_count = sum(len(parser.children(fp, 'pad')) for fp in parser.children(parsed['candidate44'], 'footprint'))
        assert pad_count == 558 and 1344 + pad_count == 1902
        before_map, after_map = j(c43 + 'f722-heli.logical-route-map.json'), j(c44 + 'f722-heli.logical-route-map.json')
        assert before_map['board_sha256'] == source and after_map['board_sha256'] == board and after_map['source_sha256'] == source
        wanted_map = {k: v for k, v in before_map['logical_route_map'].items() if k not in removed}
        wanted_map.update({k: v['net'] for k, v in expected.items() if v['net'] == 'DSM_RX_MCU'})
        assert after_map['logical_route_map'] == wanted_map
        assert set(j(c44 + 'fixed-explicit-native-ids.json')) == (set(j(c43 + 'fixed-explicit-native-ids.json')) - removed) | added
        assert original(c43 + 'poses-native.json') == original(c44 + 'poses-native.json')
        for row in j(c44 + 'project-input-preservation.json')['files']:
            assert sha(tmp / c43 / row['path']) == sha(tmp / c44 / row['path']) == row['sha256']

        # Reexecute the independent owner's pure parser transaction verifier.
        out = tmp / 'reexecuted-owner-transaction.json'
        argv = sys.argv
        sys.argv = ['check_coordinated_integration.py', str(tmp / c43 / 'f722-heli.kicad_pcb'), str(tmp / c44 / 'f722-heli.kicad_pcb'), '--net', 'DSM_RX_MCU', '--net', '+5V_BEC', '--out', str(out)]
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                runpy.run_path(str(tmp / 'integrated-routing/check_coordinated_integration.py'), run_name='__main__')
        finally:
            sys.argv = argv
        assert read(out) == j('checkpoint35-review/owner-coordinated-integration.json')
        assert sha(out) == original('checkpoint35-review/owner-coordinated-integration.json')
        sys.path.insert(0, str(tmp / 'integrated-routing'))
        with contextlib.redirect_stdout(io.StringIO()):
            runpy.run_path(str(tmp / 'integrated-routing/test_support_i2c_adoption.py'), run_name='__main__')
        controls = read(tmp / 'integrated-routing/support-i2c-adoption-controls.json')
        assert controls == j('integrated-routing/support-i2c-adoption-controls.json') and len(controls['controls']) == 7
        assert all(x['rejected'] for x in controls['controls'])
        negatives.extend('existing typed support: ' + x['name'] for x in controls['controls'])

        classification = j('checkpoint35-review/reference-region/owner/reference-classification.json')
        assert original('checkpoint35-review/reference-region/owner/reference-classification.json') == ident['owner_classification_sha256']
        for proof in [classification, j(c44 + 'reference-region-review/reference-classification.json')]:
            assert proof['before_board_sha256'] == source and proof['after_board_sha256'] == board
            for name, digest in proof['source_hashes'].items():
                assert original(name) == digest, name
            assert proof['source_binding_verified'] and proof['critical_copper_identical'] and proof['unchanged_critical_own_via_windows_verified']
            assert proof['missing_centerline_geometries_exactly_equal'] is False
            assert proof['all_changed_critical_projection_geometry_inside_unchanged_own_windows'] is True
            assert proof['all_changed_critical_projection_geometry_inside_actual_hole_window_intersections'] is False
            assert proof['exact_containment_predicate_disagreement_count'] == 4
            assert proof['classification_status'] == 'UNRESOLVED_ACTUAL_HOLE_BOUNDARY_PREDICATES'
            assert len(proof['rejection_controls']) == 7 and all(x['rejected'] for x in proof['rejection_controls'])
        accepted_classification = adoption['reference_window_classification']
        assert accepted_classification['classification_sha256'] == ident['owner_classification_sha256']
        assert accepted_classification['missing_centerline_geometries_exactly_equal'] is False and accepted_classification['actual_hole_containment'] is False
        assert accepted_classification['actual_hole_predicate_disagreements'] == 4
        comparison = j('checkpoint35-review/comparison-37-to-35.json')
        assert comparison['critical_object_geometry_identical'] is True
        deltas = comparison['net_numeric_deltas_after_minus_before']
        assert deltas['BARO_SCL']['physical_GND_centerline_missing_mm'] != 0 and deltas['USB_N']['physical_GND_centerline_missing_mm'] != 0
        assert all(row['native_planar_length_mm'] == 0 for row in deltas.values())
        geometry = j(c44 + 'i2c-geometry-review.json')
        assert geometry['I2C_final_status'] == 'NOT_QUALIFIED'
        for net in ['BARO_SCL', 'BARO_SDA']:
            topology = geometry['nets'][net]['topology']
            assert topology['supported'] and topology['component_count'] == 1 and topology['cycle_rank'] == 0
        assert not j(c44 + 'power-revalidation-required.json')['numerical_power_and_VCAP_applicability']
        status = read(ROOT / 'status.json')
        assert status['native_open_connections'] == 35 and not status['numerical_power_and_VCAP_applicability'] and not status['fabrication_ready']

        base = (args.base_project / 'f722-heli.kicad_pcb').read_bytes()
        delta = read(ROOT / 'sessions/recovery44/candidate44.f722-heli.kicad_pcb.delta.json')
        for name, bb, dd in [('wrong recovery source', base + b'\n', delta), ('wrong target digest', base, dict(delta, target_sha256='0' * 64)), ('invalid range', base, dict(delta, operations=[[0, len(base) + 1]])), ('invalid operation', base, dict(delta, operations=[{}]))]:
            reject(name, lambda bb=bb, dd=dd: recovery.reconstruct(bb, dd))
        for name in ['../escape', '/absolute', 'safe/../escape', 'windows\\escape']:
            reject('unsafe evidence path ' + name, lambda name=name: raw.safe(name))
    result = {'passed': True, 'verifier_source_sha256': sha(__file__), 'scope': 'Incremental exact source43/44 paired byte recovery, selected original evidence and sealed dependency binding, parsed 32-track/5-via proposal correspondence and exact transaction/156 footprints/558 pads, independent owner transaction verifier replay, established support adapter replay and separate full-entry/native/group binding checks. Stored native geometry/reference controls are preserved, not rerun.', 'recovered_projects': recovered, 'raw_files_verified': len(index), 'excluded_raw_files': len(excluded), 'negative_controls_passed': len(negatives), 'negative_controls': negatives, 'original_source_hash_checks_performed': bool(args.historical_workspace), 'sealed_handoff_byte_exact': True, 'sealed_dependency_digests_preserved': True, 'all_sealed_dependency_bytes_included': False, 'actual_owner_support_adapter_reexecuted': True, 'owner_coordinated_transaction_verifier_reexecuted': True, 'full_entry_wrapper_binding_separately_verified': True, 'established_wrapper_typed_audit_binding_checked': False, 'parsed_proposal_correspondence_rechecked': True, 'parsed_156_complete_footprints_and_558_pads_exact': True, 'preserved_native_source_objects': 1902, 'historical_full_width_geometric_controls_preserved': 22, 'historical_reference_controls_preserved': 7, 'native_replay_inputs_complete': False, 'real_reference_classifier_reexecuted': False, 'full_width_geometric_audit_reexecuted': False, 'native_DRC_reexecuted': False, 'JVM_router_refill_or_power_solve_executed': False, 'source43_numerical_results_inherited': False, 'numerical_power_and_VCAP_applicability': False, 'I2C_electrical_status': 'NOT_QUALIFIED', 'native_open_connections': 35, 'native_errors': 0, 'native_warnings': 0, 'missing_centerline_geometries_exactly_equal': False, 'actual_hole_containment': False, 'actual_hole_predicate_disagreements': 4}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))

if __name__ == '__main__':
    main()
