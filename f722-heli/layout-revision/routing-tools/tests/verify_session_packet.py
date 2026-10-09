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
    if (packet / 'construction.json').exists():
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
