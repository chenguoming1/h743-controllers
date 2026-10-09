#!/usr/bin/env python3
"""Capture bounded candidate27/28 provenance; never run native tools or Java."""
import argparse
import difflib
import hashlib
import json
import shutil
from pathlib import Path

BASE_MANIFEST = '13f0fa03eaf62d3ae16635109877499976843e7289f97372cb4e2143cdd180e6'
BASE_ZIP = '5566e05ad8e58e9bdaad815bcf066db6883a33f685066a6af4aed4eff298e96b'

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + '\n')

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--workspace', type=Path, required=True)
    args = ap.parse_args()
    root = args.workspace.resolve()
    stage = Path(__file__).resolve().parents[1]
    base = root / 'public-source-ready-v8'
    assert sha(base / 'FILES.sha256.json') == BASE_MANIFEST
    assert sha(root / 'routing-source-v8-delta.zip') == BASE_ZIP
    projections, sources = {}, {}

    def portable(value):
        if isinstance(value, dict):
            return {portable(k): portable(v) for k, v in value.items()}
        if isinstance(value, list):
            return [portable(v) for v in value]
        if isinstance(value, str):
            value = value.replace(str(root) + '/', '').replace(str(root.parent) + '/', '')
            assert '/workspace/' not in value, value
        return value

    def copy(src, dst):
        source, target = root / src, stage / dst
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        sources[dst] = {'historical_path': src, 'sha256': sha(source)}

    def project(src, dst, transform=None, scope=None):
        source, target = root / src, stage / dst
        value = portable(json.loads(source.read_bytes()))
        if transform:
            value = transform(value)
        write(target, value)
        projections[dst] = {
            'historical_path': src,
            'historical_file_sha256': sha(source),
            'historical_bytes': source.stat().st_size,
            'portable_file_sha256': sha(target),
            'projection': scope or 'JSON values unchanged except historical paths made relative; whitespace normalized.'}
        return value

    # Reuse exact V8 source dependencies, including frozen importer. Do not
    # replace its older root importer or Java sources used by prior receipts.
    used = {
        'candidate27/import_session.used.py': 'import_session_v8.py',
        'candidate28/import_session.used.py': 'import_session_v8.py',
        'candidate28/route_geometry.used.py': 'route_geometry.py',
        'candidate28/prepare_screened_local.used.py': 'prepare_screened_local.py',
        'candidate28/audit_support_connectivity.used.py': 'audit_support_connectivity.py',
        'run_bounded_local.py': 'run_bounded_local.py',
        'prepare_located_branch.py': 'prepare_located_branch.py',
    }
    for src, dst in used.items():
        assert sha(root / src) == sha(stage / dst), (src, dst)
        sources[src] = {'package_source': dst, 'historical_path': src, 'sha256': sha(root / src)}
    copy('candidate28/prepare_located_branch_continuation.used.py', 'prepare_located_branch_continuation.py')
    for name in ['audit_native_endpoints', 'audit_existing_via_entries', 'audit_shared_pad_entry']:
        copy('candidate28/' + name + '.used.py', 'tests/routing-checkpoint55/' + name + '.py')
    common = ['route-handoff.json', 'engine-lineage.json', 'endpoint-audit.json',
              'existing-via-entry.json', 'f722-heli.import.json', 'f722-heli.logical-route-map.json',
              'power-audit.json', 'power-revalidation-required.json', 'protection-actual-io.json',
              'route-analysis.json', 'owner-summary.json', 'owner-critical.json',
              'owner-drc-all.json', 'owner-drc-parity.json', 'owner-drc.json',
              'owner-firmware.json', 'owner-mechanical.json', 'owner-parity.json',
              'owner-process.json', 'owner-protection.json', 'owner-supplemental.json']
    for c in [27, 28]:
        for name in common:
            project(f'candidate{c}/' + name, f'checks/candidate{c}-' + name)
    for name in ['owner-adoption.json', 'owner-additive-integration.json', 'owner-actual-io22.json',
                 'shared-pad-entry.json', 'unchanged-wip27-power-reference.json']:
        project('candidate28/' + name, 'checks/candidate28-' + name)
    project('../checkpoint55-review/comparison-57-to-55.json', 'checks/candidate28-critical-reference-comparison.json')
    for name in ['zero-parity.json', 'imported-zero.import.json', 'router-readiness.json', 'summary.json',
                 'fixed-explicit-native-ids.json']:
        project('model-candidate28-ready/' + name, 'checks/source28-' + name)
    # Compact continuation safety contract, not a routing model.
    model28 = json.loads((root / 'model-candidate28-ready/model.json').read_bytes())
    write(stage / 'checks/source28-fixed-preservation-contract.json', {
        'historical_model_sha256': sha(root / 'model-candidate28-ready/model.json'),
        'board_sha256': model28['board_sha256'],
        'mutable_source_ids': model28['mutable_source_ids'],
        'source_logical_nets': model28['source_logical_nets'],
        'full_model_included': False})

    fields = ['board_sha256', 'aliases', 'ordinary_nets', 'routable_layers',
              'mutable_source_ids', 'source_logical_nets', 'regenerable_reference_zones']
    for c, source, packet, model_src, session_src, report_src in [
        (27, 26, 'engine56', 'model-candidate26-ready/model.json',
         'model-candidate26-ready/filtered02.successes/final/snapshot.ses',
         'model-candidate26-ready/filtered02.successes/final/snapshot.after.json'),
        (28, 27, 'accepted55', 'tests/located-portb-rx26/prepared-on27/native-construction-model.json',
         'tests/located-portb-rx26/prepared-on27/constructed.ses',
         'tests/located-portb-rx26/prepared-on27/constructed-report.json')]:
        folder = 'sessions/' + packet
        model = json.loads((root / model_src).read_bytes())
        copy(session_src, folder + '/session.ses')
        project(report_src, folder + '/engine-report.json',
                (lambda d: dict(d, areas=[])) if c == 27 else None,
                'All route geometry and metadata retained; fixed guard areas omitted.' if c == 27 else None)
        write(stage / folder / 'import-contract.json', {k: model[k] for k in fields})
        identity = {
            'kind': 'actual_engine_NRST_insertion' if c == 27 else 'explicit_native_PORT_B_RX_EXT_P2_construction_after_insertion_refusal',
            'board_sha256': model['board_sha256'], 'native_sha256': model['native_sha256'],
            'candidate_sha256': sha(root / f'candidate{c}/f722-heli.kicad_pcb'),
            'model_sha256': sha(root / model_src), 'historical_model_path': model_src,
            'session_sha256': sha(stage / folder / 'session.ses'),
            'engine_report_sha256': sha(stage / folder / 'engine-report.json'),
            'historical_engine_report_sha256': sha(root / report_src),
            'import_contract_sha256': sha(stage / folder / 'import-contract.json'),
            'import_contract_fields': fields, 'full_model_included': False,
            'source_candidate': f'candidate{source}', 'candidate': f'candidate{c}',
            'importer_source_path': 'import_session_v8.py',
            'importer_source_sha256': sha(stage / 'import_session_v8.py'),
            'import_arguments': [] if c == 27 else ['--preserve-unaffected-fills'],
            'historical_native_import_receipt': f'checks/candidate{c}-f722-heli.import.json',
            'new_tracks': 6 if c == 27 else 3, 'new_vias': 1 if c == 27 else 0,
            'engine_insertion_succeeded': c == 27, 'native_replay_reexecuted_for_v9': False,
            'numerical_power_and_VCAP_applicability': False,
            'portable_path_projections': 'checks/v9-portable-projections.json'}
        write(stage / folder / 'source-identity.json', identity)
    project('model-candidate26-ready/filtered02.successes/final/receipt.json', 'sessions/engine56/selected-checkpoint-receipt.json')
    # Preserve only the exact relevant refusal, proposals and construction.
    for name in ['located-receipt.json', 'proposal.json', 'proposal-on27.json']:
        project('tests/located-portb-rx26/' + name, 'tests/located-portb-rx26/' + name)
    log_name = 'tests/located-portb-rx26/captured-engine.log'
    raw_log = root / log_name
    lines = [line for line in raw_log.read_text().splitlines()
             if line.startswith('INSERT_DIAGNOSTIC ')
             and json.loads(line[len('INSERT_DIAGNOSTIC '):])['net'] == 'PORT_B_RX_EXT::P2']
    (stage / log_name).write_text('\n'.join(lines) + '\n')
    projections[log_name] = {'historical_path': log_name,
        'historical_file_sha256': sha(raw_log), 'historical_bytes': raw_log.stat().st_size,
        'portable_file_sha256': sha(stage / log_name),
        'projection': 'Exact unchanged INSERT_DIAGNOSTIC lines for PORT_B_RX_EXT::P2 only; unrelated attempts/progress omitted.'}
    for src, dst in [('construction.json', 'native-construction.json'),
                     ('native-construction-model.json', 'original-import-contract.json')]:
        project('tests/located-portb-rx26/prepared-on27/' + src, 'sessions/accepted55/' + dst)
    assert sha(root / 'candidate28/engine-insertion-refusal.json') == sha(root / 'tests/located-portb-rx26/located-receipt.json')
    assert sha(root / 'candidate28/native-construction.json') == sha(root / 'tests/located-portb-rx26/prepared-on27/construction.json')
    # Small negative finding only; live adapters remain byte-identical to V8.
    copy('staged-shared-pad-predicates-20261009/REVIEW.md', 'tests/shared-pad-predicate-risk/REVIEW.md')
    for name in ['control.json', 'source-manifest.json']:
        project('staged-shared-pad-predicates-20261009/' + name, 'tests/shared-pad-predicate-risk/' + name)

    # Two byte-copy deltas anchored to the exact candidate26 recovered by V8.
    rec = stage / 'sessions/recovery55'
    rec.mkdir(exist_ok=True)
    script = (stage / 'sessions/recovery57/rebuild_historical_source.py').read_text()
    script = script.replace('("candidate22", "candidate23", "candidate24", "candidate25", "candidate26")',
                            '("candidate26", "candidate27", "candidate28")')
    script = script.replace('hash-pinned accepted62 project', 'hash-pinned candidate26 project recovered by V8')
    (rec / 'rebuild_historical_source.py').write_text(script)
    manifest = json.loads((stage / 'sessions/recovery57/paired-files.json').read_bytes())
    manifest['sources'] = {}
    manifest['required_base_files']['f722-heli.kicad_pcb'] = {
        'sha256': sha(root / 'candidate26/f722-heli.kicad_pcb'),
        'bytes': (root / 'candidate26/f722-heli.kicad_pcb').stat().st_size}
    manifest['base_recovery'] = {'script': 'sessions/recovery57/rebuild_historical_source.py',
        'source': 'candidate26', 'required_external_project': 'hash-pinned candidate22/accepted62 paired project',
        'immutable_v8_manifest_sha256': BASE_MANIFEST}
    base_bytes = (root / 'candidate26/f722-heli.kicad_pcb').read_bytes()
    lines = base_bytes.splitlines(keepends=True)
    offsets = [0]
    for line in lines:
        offsets.append(offsets[-1] + len(line))
    for c in [26, 27, 28]:
        for name, info in manifest['required_base_files'].items():
            if name != 'f722-heli.kicad_pcb':
                assert sha(root / f'candidate{c}' / name) == info['sha256'], (c, name)
        target = (root / f'candidate{c}/f722-heli.kicad_pcb').read_bytes()
        entries = {}
        if c != 26:
            target_lines, operations = target.splitlines(keepends=True), []
            for tag, i, j, k, l in difflib.SequenceMatcher(None, lines, target_lines, autojunk=True).get_opcodes():
                if tag == 'equal':
                    operations.append([offsets[i], offsets[j] - offsets[i]])
                elif tag in ['replace', 'insert']:
                    operations.append(b''.join(target_lines[k:l]).decode())
            name = f'candidate{c}.f722-heli.kicad_pcb.delta.json'
            write(rec / name, {'schema': 'f722-historical-source-copy-delta/v1',
                'base_sha256': hashlib.sha256(base_bytes).hexdigest(),
                'target_sha256': hashlib.sha256(target).hexdigest(),
                'target_bytes': len(target), 'operations': operations})
            entries['f722-heli.kicad_pcb'] = {'file': name, 'sha256': sha(rec / name)}
        manifest['sources'][f'candidate{c}'] = {'source_label': f'candidate{c}',
            'purpose': 'Exact paired byte recovery only; no new native or electrical qualification.',
            'board_sha256': hashlib.sha256(target).hexdigest(), 'board_bytes': len(target),
            'unchanged_paired_files': len(manifest['required_base_files']) - 1, 'deltas': entries}
    write(rec / 'paired-files.json', manifest)
    overwritten = []
    for c in [27, 28]:
        handoff = json.loads((root / f'candidate{c}/route-handoff.json').read_bytes())
        for name, old in handoff['files'].items():
            source = root / f'candidate{c}' / name
            if source.exists() and sha(source) != old:
                overwritten.append({'candidate': c, 'filename': name,
                    'historical_handoff_sha256': old, 'current_owner_file_sha256': sha(source),
                    'historical_bytes_retained': False})
    write(stage / 'checks/v9-historical-receipt-status.json', {
        'historical_handoffs_preserved_except_path_projection': True,
        'later_owner_receipts_recorded_separately': True,
        'candidate27_has_no_standalone_owner_adoption': True,
        'adoption_scope': 'candidate28 owner adoption covers the cumulative26-to28 change;27 is the validated intermediate.',
        'overwritten_historical_receipts': overwritten})
    write(stage / 'checks/v9-portable-projections.json', {'schema': 'f722-portable-path-projections/v1',
        'files': projections, 'historical_dependency_hashes_unchanged': True})
    java = {str(p.relative_to(stage)): sha(p) for p in (stage / 'src').rglob('*.java')}
    assert all(sha(base / name) == value == sha(root / name) for name, value in java.items())
    write(stage / 'checks/v9-source-identity.json', {
        'schema': 'f722-v9-source-selection/v1', 'base_manifest_sha256': BASE_MANIFEST,
        'base_zip_sha256': BASE_ZIP, 'sources': sources, 'java_sources_sha256': java,
        'java_sources_byte_identical_to_v8_and_live': True,
        'selected27_checkpoint': 'model-candidate26-ready/filtered02.successes/final',
        'selected28_packet': 'tests/located-portb-rx26/prepared-on27',
        'unfinished_source28_filtered03_excluded': True, 'heavy_execution_performed': False})
    print(json.dumps({'projected_files': len(projections), 'source_receipts': len(sources), 'stage': stage.name}))

if __name__ == '__main__':
    main()
