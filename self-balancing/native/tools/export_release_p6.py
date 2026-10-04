#!/usr/bin/python3
"""Export P6 only from the exact source with complete copper-attachment proof.

This generates submission files. Visual, export-parity, supplier and final-package
acceptance remain separate release gates. It cannot confer physical qualification.
"""
from pathlib import Path
import hashlib
import json

PROJECT = Path(__file__).resolve().parents[1]
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
guard_path = PROJECT / 'review/p6-qualified-export-guard.json'
guard = json.loads(guard_path.read_text())
qualification_path = PROJECT / guard['qualification_report']
assert sha(qualification_path) == guard['qualification_report_sha256']
qualification = json.loads(qualification_path.read_text())
expected = guard['native_sha256']
assert sha(PROJECT / 'controller.kicad_pcb') == expected
assert qualification['candidate_sha256'] == expected
assert qualification['status'] == 'PASS FINAL SOURCE CAD AND COMPLETE COPPER-ATTACHMENT QUALIFICATION'
assert qualification['errors'] == []
assert all(v == 0 for v in qualification['native_counts'].values())
assert qualification['copper_joins']['all_narrow_local_join_flags'] == 0
assert qualification['via_attachments']['new_or_worsened_shallow_groups'] == 0
assert qualification['via_attachments']['inherited_or_improved_shallow_groups'] == 0
assert qualification['pad_attachments']['counts']['failed_groups'] == 0
assert qualification['pad_attachments']['unresolved_functional_nominal_advisories'] == 0
assert qualification['ground_plane_attachments']['reference_plane_terminal_attachment_checks'] == 303
assert qualification['reference_dispositions']['true_new_foreign_gap_net_layers'] == 0
assert qualification['functional_vias']['unresolved_count'] == 0
assert qualification['pad_anchored_dead_trees']['unresolved_count'] == 0

def verify_files():
    for collection in ['qualified_source_files', 'qualification_evidence_files']:
        for relative, checksum in guard[collection].items():
            path = PROJECT / relative
            assert path.is_file() and sha(path) == checksum, 'Qualification no longer matches: ' + relative

verify_files()
producer = PROJECT / 'tools/export_release.py'
assert sha(producer) == guard['qualified_source_files']['tools/export_release.py']
source = producer.read_text()
needle = "['pcb','drc','--format','json','--severity-all','--schematic-parity'"
assert source.count(needle) == 1
source = source.replace(needle, "['pcb','drc','--format','json','--severity-all','--all-track-errors','--schematic-parity'")
executed_hash = hashlib.sha256(source.encode()).hexdigest()
producer_namespace = {'__file__': str(producer), '__name__': '__main__', '__builtins__': __builtins__}
exec(compile(source, str(producer), 'exec'), producer_namespace)
verify_files()
assert sha(PROJECT / 'controller.kicad_pcb') == expected
(PROJECT / 'review/p6-export-guard-result.json').write_text(json.dumps({
    'status': 'PASS EXACT-SOURCE ACTUAL-COPPER EXPORT GUARD',
    'native_sha256': expected,
    'qualification_report_sha256': sha(qualification_path),
    'guard_sha256': sha(guard_path),
    'original_producer_sha256': sha(producer),
    'executed_producer_sha256': executed_hash,
    'producer_delta': 'Add --all-track-errors to the unchanged producer DRC invocation',
    'source_and_evidence_files_stable': True,
    'scope': 'Submission export only; final visual, exported-file, supplier and package acceptance are still required'
}, indent=2) + '\n')
