#!/usr/bin/env python3
"""Check persisted geometry, real routing progress and observed stop provenance."""
import copy
import hashlib
import json
from pathlib import Path
import re
import shutil

ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parent.parent

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def read(path):
    return json.loads(path.read_text())

def canonical(rows):
    return sorted(json.dumps(row, sort_keys=True) for row in rows)

def retained(before, after):
    assert canonical(before['areas']) == canonical(after['areas']), 'Changed/missing fixed contact or guard'
    get_fixed = lambda state: canonical([r for r in state['routes'] if r['fixed'] == 'SYSTEM_FIXED'])
    assert get_fixed(before) == get_fixed(after), 'Changed/missing fixed trace or via'

def sexpr(text):
    tokens = re.findall(r'"(?:[^"\\]|\\.)*"|[()]|[^\s()]+', text)
    stack, result = [], None
    for token in tokens:
        if token == '(':
            row = []
            if stack:
                stack[-1].append(row)
            stack.append(row)
        elif token == ')':
            result = stack.pop()
        else:
            stack[-1].append(token.strip('"'))
    assert not stack and result[0] == 'session'
    return result

def children(node, key):
    return [v for v in node if isinstance(v, list) and v and v[0] == key]

def ses_tracks(path):
    routes = children(sexpr(path.read_text()), 'routes')[0]
    resolution = children(routes, 'resolution')[0]
    assert resolution == ['resolution', 'mm', '100000']
    found = []
    for net in children(children(routes, 'network_out')[0], 'net'):
        assert not children(net, 'via'), 'Unexpected routed via in tiny control'
        for wire in children(net, 'wire'):
            route = children(wire, 'path')[0]
            found.append({'net': net[1], 'layer': route[1], 'width_units': int(route[2]),
                          'points_units': [[int(route[i]), int(route[i+1])] for i in range(3, len(route), 2)]})
    return canonical(found)

def json_tracks(state):
    found = []
    for r in state['routes']:
        if r['fixed'] == 'SYSTEM_FIXED':
            continue
        assert r['kind'] == 'track' and r['nets'] == ['TEST']
        found.append({'net': r['nets'][0], 'layer': r['layer'], 'width_units': round(r['width']*100000),
                      'points_units': [[round(x*100000), -round(y*100000)] for x,y in r['points']]})
    return canonical(found)

def check(prefix, expect_reuse):
    before, after = read(Path(str(prefix)+'.before.json')), read(Path(str(prefix)+'.after.json'))
    progress, debug = read(Path(str(prefix)+'.progress.json')), read(Path(str(prefix)+'.debugger.json'))
    checkpoint = Path(progress['checkpoint'])
    success = read(Path(str(checkpoint)+'.after.json'))
    events = [json.loads(s.removeprefix('ROUTE_PROGRESS ')) for s in Path(str(prefix)+'.stdout.log').read_text().splitlines() if s.startswith('ROUTE_PROGRESS ')]
    assert len(events) == 3
    assert [e['route_counters']['queued_to_be_routed_count'] for e in events] == [2, 1, 0]
    assert [e['attempt'].get('result') for e in events] == [None, 'ROUTED', 'NO_UNCONNECTED_NETS']
    assert [e['route_counters']['routed_count'] for e in events] == [0, 1, 1]
    assert progress['route_counters']['failed_to_be_routed_count'] == 0
    assert progress['route_counters']['incomplete_count'] == 0
    assert progress['geometry_snapshot_reused'] is expect_reuse
    assert progress['pending_route_geometry'] is False
    assert debug['child_exit_code'] == 0 and debug['final_queue_stop_branch_observed']
    first_stop = debug['stop_invocations'][0]
    assert first_stop['published_progress'] == progress
    assert first_stop['stack'][1]['class'] == 'LocalRouter' and first_stop['stack'][1]['method'].startswith('lambda$')
    assert not first_stop['stop_flag_before'] and debug['stop_returns'][0]['stop_flag_after']
    assert not first_stop['stop_file_present'] and debug['configured_stop_after_routed'] == '5'
    assert all(e['fixed_geometry_sha256'] == events[0]['fixed_geometry_sha256'] for e in events)
    retained(before, after)
    assert len(before['areas']) == 4
    assert sorted(a['kind'] for a in before['areas']) == ['contact', 'contact', 'foreign_guard', 'foreign_guard']
    assert len(before['routes']) == 2 and sorted(r['kind'] for r in before['routes']) == ['track', 'via']
    assert all(r['fixed'] == 'SYSTEM_FIXED' for r in before['routes'])
    assert len(before['contact_partitions']) == 2 and len(after['contact_partitions']) == 1
    assert sorted(after['contact_partitions'][0]['contacts']) == ['SYNTHETIC_A:F.Cu', 'SYNTHETIC_B:F.Cu']
    assert after['routes'] == success['routes'] and after['contact_partitions'] == success['contact_partitions']
    generated = [r for r in after['routes'] if r['fixed'] != 'SYSTEM_FIXED']
    assert len(generated) == 1 and len(generated[0]['points']) >= 2
    assert generated[0]['points'][0] != generated[0]['points'][-1]
    final_ses, checkpoint_ses = Path(str(prefix)+'.ses'), Path(str(checkpoint)+'.ses')
    assert final_ses.read_bytes() == checkpoint_ses.read_bytes()
    assert sha(checkpoint_ses) == progress['session_sha256']
    assert sha(Path(str(checkpoint)+'.after.json')) == progress['report_sha256']
    assert ses_tracks(final_ses) == json_tracks(after), 'Final SES route differs from final snapshot'
    # Independent assertion controls: detectors must reject missing fixed geometry
    # and a displaced routed endpoint, even if all counters remain successful.
    corrupted = copy.deepcopy(after)
    corrupted['areas'].remove(next(a for a in corrupted['areas'] if a['kind'] == 'foreign_guard'))
    try:
        retained(before, corrupted)
    except AssertionError:
        guard_negative = True
    else:
        raise AssertionError('Missing-guard negative was accepted')
    corrupted = copy.deepcopy(after)
    next(r for r in corrupted['routes'] if r['fixed'] != 'SYSTEM_FIXED')['points'][-1][0] += .01
    endpoint_negative = ses_tracks(final_ses) != json_tracks(corrupted)
    assert endpoint_negative
    paths = [Path(str(prefix)+suffix) for suffix in ['.before.json','.after.json','.progress.json','.debugger.json','.ses','.stdout.log','.stderr.log']]
    paths += [Path(str(checkpoint)+'.after.json'), checkpoint_ses]
    return {'prefix': str(prefix.relative_to(PROJECT)), 'final_queue_stop_branch_observed': True,
            'child_exit_code': 0, 'actual_successful_connections': 1, 'queue_counts': [2,1,0],
            'final_geometry_snapshot_reused': expect_reuse, 'cooperative_stop_caller': first_stop['stack'][1],
            'fixed_contacts_retained': 2, 'fixed_guards_retained': 2, 'fixed_tracks_retained': 1, 'fixed_vias_retained': 1,
            'fixed_geometry_sha256': events[0]['fixed_geometry_sha256'],
            'connected_native_contact_partitions_before': 2, 'connected_native_contact_partitions_after': 1,
            'checkpoint_and_final_geometry_equal': True, 'checkpoint_and_final_ses_byte_identical': True,
            'final_ses_matches_final_snapshot': True, 'missing_guard_negative_rejected': guard_negative,
            'changed_endpoint_negative_rejected': endpoint_negative,
            'elapsed_seconds_at_final_queue': progress['elapsed_seconds'],
            'artifact_sha256': {str(p.relative_to(PROJECT)): sha(p) for p in paths}}

model = read(ROOT/'fixture/model.json')
source_hashes = model['adapter_sources']
for path, expected in source_hashes.items():
    assert sha(Path(path)) == expected, f'Production source changed during control: {path}'
cases = [check(ROOT/'positive-flush', False), check(ROOT/'positive-reuse', True)]
receipt = {'schema': 'end-queue-stop-control/v1', 'path_base': 'ordinary-routing',
           'synthetic_only': True, 'production_source_changed': False,
           'cases': cases, 'fixture_model_sha256': sha(ROOT/'fixture/model.json'),
           'fixture_dsn_sha256': sha(ROOT/'fixture/routing.dsn'),
           'seed_model': str(Path(model['seed_model']).relative_to(PROJECT)),
           'seed_model_sha256': model['seed_model_sha256'],
           'preserved_production_sources': str((ROOT/'source-used').relative_to(PROJECT)),
           'production_sources_sha256': {str(Path(p).relative_to(PROJECT)): h for p,h in source_hashes.items()},
           'production_class_sha256': {str(p.relative_to(PROJECT)): sha(p) for p in sorted((PROJECT/'build').rglob('*.class'))},
           'test_sources_sha256': {str(p.relative_to(PROJECT)): sha(p) for p in sorted(ROOT.glob('*')) if p.suffix in ('.java','.py')},
           'limitations': ['Synthetic small model, not a full-board or native DRC test.',
                           'Fixed contacts are intentionally removed after the final JSON snapshot for SES export; guards and fixed copper remain subject to production checks.',
                           'Read-only debugger observes production bytecode; it does not modify sources, bytecode, or routing state.']}
for path in source_hashes:
    source=Path(path);dest=ROOT/'source-used'/source.relative_to(PROJECT);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,dest)
(ROOT/'result.json').write_text(json.dumps(receipt, indent=2)+'\n')
print(json.dumps({'all_passed': True, 'cases': cases}, indent=2))
