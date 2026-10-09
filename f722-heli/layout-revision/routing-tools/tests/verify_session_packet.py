#!/usr/bin/env python3
"""Check a compact session without pcbnew, Java, or a full routing model."""
import argparse
import ast
import collections
import hashlib
import json
import re
from pathlib import Path


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--packet', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    args = ap.parse_args()
    root = Path(__file__).resolve().parents[1]
    packet = args.packet
    identity = json.loads((packet / 'source-identity.json').read_text())
    for key, name in [('session_sha256', 'session.ses'),
                      ('engine_report_sha256', 'engine-report.json'),
                      ('import_contract_sha256', 'import-contract.json')]:
        assert sha(packet / name) == identity[key], name
    contract = json.loads((packet / 'import-contract.json').read_text())
    report = json.loads((packet / 'engine-report.json').read_text())
    assert report['board_sha256'] == contract['board_sha256'] == identity['board_sha256']
    assert report['model_sha256'] == identity['model_sha256']

    # Execute the importer's actual pure parsing functions. Loading pcbnew or
    # duplicating the route parser here could conceal a parser disagreement.
    names = {'parse', 'children', 'child', 'ses_routes', 'nm', 'key', 'from_snapshot'}
    source = ast.parse((root / 'import_session.py').read_text())
    funcs = [node for node in source.body if isinstance(node, ast.FunctionDef) and node.name in names]
    assert {node.name for node in funcs} == names
    namespace = {'Path': Path, 'json': json, 're': re}
    exec(compile(ast.Module(body=funcs, type_ignores=[]), 'import_session.py:pure-functions', 'exec'), namespace)
    session_routes = namespace['ses_routes'](packet / 'session.ses')
    report_routes = namespace['from_snapshot'](report)
    key = namespace['key']
    assert collections.Counter(map(key, session_routes)) == collections.Counter(map(key, report_routes))
    assert all(contract['aliases'][r['logical_net']] in contract['ordinary_nets'] for r in session_routes)
    result = {
        'passed': True,
        'scope': 'Pure-Python packet identity and SES/report geometry; no native import, refill, DRC, or route search.',
        'source_board_sha256': identity['board_sha256'],
        'origin_model_sha256': identity['model_sha256'],
        'session_sha256': identity['session_sha256'],
        'engine_report_sha256': identity['engine_report_sha256'],
        'import_contract_sha256': identity['import_contract_sha256'],
        'importer_source_sha256': sha(root / 'import_session.py'),
        'verifier_source_sha256': sha(__file__),
        'mutable_route_segments': sum(r['kind'] == 'track' for r in session_routes),
        'mutable_route_vias': sum(r['kind'] == 'via' for r in session_routes),
        'native_replay_executed': False,
    }
    if (packet / 'retention.json').exists():
        retention = json.loads((packet / 'retention.json').read_text())
        for digest_key, filename in [('session_sha256', 'session.ses'),
                                     ('engine_report_sha256', 'engine-report.json'),
                                     ('original_session_sha256', 'original-engine-session.ses'),
                                     ('original_engine_report_sha256', 'original-engine-report.json')]:
            assert sha(packet / filename) == retention[digest_key], filename
        original = namespace['ses_routes'](packet / 'original-engine-session.ses')
        original_report = json.loads((packet / 'original-engine-report.json').read_text())
        assert collections.Counter(map(key, original)) == collections.Counter(map(key, namespace['from_snapshot'](original_report)))
        excluded = set(retention['excluded_new_logical_nets'])
        assert collections.Counter(map(key, session_routes)) == collections.Counter(key(r) for r in original if r['logical_net'] not in excluded)
        if retention.get('source_routes_discarded'):
            proof = retention['accepted_source_proof']
            assert proof['all_accepted_native_objects_retained_in_working_source']
            assert proof['excluded_nets_have_no_accepted_route_copper']
            removed = proof['removed_unaccepted_working_source_uuids']
            assert all(contract['source_logical_nets'][uid] in excluded for uid in removed)
            assert set(removed) <= set(contract['mutable_source_ids'])
            result['historical_retained_source_exclusion_proof_bound'] = True
            result['retained_source_proof_reexecuted_natively'] = False
        result.update(retention_exact_subset_verified=True, excluded_logical_nets=sorted(excluded))
    construction_path = packet / 'construction.json'
    if construction_path.exists() and json.loads(construction_path.read_text())['kind'] == 'explicit_native_short_local_construction':
        construction = json.loads(construction_path.read_text())
        assert construction['engine_routing_performed'] is False
        assert report['route_solver_used'] is False
        assert sha(root / identity['constructor_source_path']) == construction['constructor_sha256']
        assert construction['model_sha256'] == identity['model_sha256']
        assert construction['session_sha256'] == identity['session_sha256']
        projections = json.loads((root / identity['portable_path_projections']).read_text())['files']
        for filename, historical_key, current_key in [
            ('original-import-contract.json', 'historical_original_import_contract_sha256', 'original_import_contract_sha256'),
            ('input-proposal.json', 'historical_input_proposal_sha256', 'input_proposal_sha256'),
        ]:
            entry = projections[str((packet / filename).resolve().relative_to(root))]
            assert entry['historical_file_sha256'] == identity[historical_key]
            assert entry['portable_file_sha256'] == identity[current_key] == sha(packet / filename)
        assert construction['proposal_sha256'] == identity['historical_input_proposal_sha256']
        proposal = json.loads((packet / 'input-proposal.json').read_text())
        assert proposal['proof_receipt']['sha256'] == construction['proof_sha256']
        assert proposal['source_identity']['board_sha256'] == identity['board_sha256']
        original_contract = json.loads((packet / 'original-import-contract.json').read_text())
        assert all(value == original_contract[k] for k, value in contract.items())
        assert not contract['mutable_source_ids'] and not contract['regenerable_reference_zones']
        assert result['mutable_route_segments'] == construction['new_tracks'] == 2
        assert result['mutable_route_vias'] == construction['new_vias'] == 0
        assert all(r['logical_net'] == 'ADC_BUS' and r['layer'] == 'F.Cu' for r in session_routes)
        result.update(explicit_native_short_local_construction_verified=True,
                      stock_engine_insertion_succeeded=False, portable_paths_and_historical_provenance_verified=True,
                      original_contract_geometry_fields_preserved=True, existing_source_objects_all_immutable=True,
                      new_drills_or_reference_refill_requested=False)
    elif construction_path.exists() and json.loads(construction_path.read_text())['kind'] == 'explicit_native_network_construction':
        construction = json.loads(construction_path.read_text())
        assert construction['engine_routing_performed'] is False
        assert construction['engine_insertion_succeeded'] is False
        assert sha(root / identity['constructor_source_path']) == construction['construction_source_sha256']
        if identity.get('portable_path_projections'):
            projections = json.loads((root / identity['portable_path_projections']).read_text())
            for name, versions in projections['files'].items():
                assert sha(root / name) == versions['portable_file_sha256'], name
                projected_file = json.loads((root / name).read_text())
                assert projected_file['portable_projection']['historical_file_sha256'] == versions['historical_file_sha256']
                assert '/workspace/' not in json.dumps(projected_file)
            contract_versions = projections['files'][str((packet / 'original-import-contract.json').resolve().relative_to(root))]
            proposal_versions = projections['files'][str((packet / 'input-construction.json').resolve().relative_to(root))]
            assert contract_versions['historical_file_sha256'] == construction['import_contract_sha256'] == identity['historical_original_import_contract_sha256']
            assert contract_versions['portable_file_sha256'] == identity['original_import_contract_sha256']
            assert proposal_versions['historical_file_sha256'] == construction['proposal_sha256'] == identity['historical_input_construction_sha256']
            assert proposal_versions['portable_file_sha256'] == identity['input_construction_sha256']
            proposal = json.loads((packet / 'input-construction.json').read_text())
            assert sha(root / proposal['proposal_receipt']['path']) == proposal['proposal_receipt']['sha256']
            result['portable_paths_and_historical_provenance_verified'] = True
        else:
            assert sha(packet / 'original-import-contract.json') == construction['import_contract_sha256']
            assert sha(packet / 'input-construction.json') == construction['proposal_sha256']
        assert sha(packet / 'session.ses') == construction['session_sha256']
        assert sha(packet / 'engine-report.json') == construction['report_sha256']
        embedded = {k: v for k, v in construction.items() if k not in {'session_sha256', 'report_sha256'}}
        assert report['route_construction'] == embedded
        original_contract = json.loads((packet / 'original-import-contract.json').read_text())
        assert all(value == original_contract[k] for k, value in contract.items())
        assert contract['mutable_source_ids'] == []
        assert all(route['logical_net'] == construction['new_net'] for route in session_routes)
        assert result['mutable_route_segments'] == construction['new_tracks']
        assert result['mutable_route_vias'] == construction['new_vias']
        result.update(stock_engine_insertion_succeeded=False,
                      explicit_native_construction_verified=True,
                      original_contract_geometry_fields_preserved=True,
                      existing_source_objects_all_immutable=True,
                      native_collinear_union_object_count_not_reexecuted=True)
    elif construction_path.exists():
        construction = json.loads((packet / 'construction.json').read_text())
        assert construction['engine_insertion_succeeded'] is False
        for key_name, file_name in [
            ('construction_source_sha256', 'construct_located_session.used.py'),
            ('diagnostic_log_sha256', 'located-path-diagnostics.log'),
            ('base_session_sha256', 'base-session.ses'),
            ('output_session_sha256', 'session.ses'),
            ('output_report_sha256', 'engine-report.json'),
        ]:
            assert sha(packet / file_name) == construction[key_name], key_name
        embedded = dict(construction)
        embedded.pop('output_session_sha256')
        embedded.pop('output_report_sha256')
        assert report['route_construction'] == embedded
        assert construction['explicit_waypoint_adjustment']['offset_file_sha256'] == sha(packet / 'waypoint-offsets.json')
        diagnostics = [json.loads(line[len('INSERT_DIAGNOSTIC '):])
                       for line in (packet / 'located-path-diagnostics.log').read_text().splitlines()
                       if line.startswith('INSERT_DIAGNOSTIC ')]
        located = [v for v in diagnostics if v['net'] == construction['net'] and v['stage'] == 'located_trace']
        assert located[construction['selected_located_path_index']]['requested_corners_mm'] == construction['original_points_mm']
        base = namespace['ses_routes'](packet / 'base-session.ses')
        base_counter = collections.Counter(map(key, base))
        actual_counter = collections.Counter(map(key, session_routes))
        assert not (base_counter - actual_counter), 'Existing session routes were lost'
        new_routes = actual_counter - base_counter
        assert sum(new_routes.values()) == 6
        assert all(k[0] == 'track' and k[1] == 'D2_A' for k in new_routes)
        result.update(stock_engine_insertion_succeeded=False, constructed_new_segments=6,
                      constructed_new_vias=0, base_routes_preserved=True,
                      original_located_path_verified=True, nominal_outward_adjustment_mm=0.025)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result))


if __name__ == '__main__':
    main()
