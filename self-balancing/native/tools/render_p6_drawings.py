#!/usr/bin/python3
"""Generate and render P6 presentation artifacts without modifying native sources.

The owner must supply an agreed frozen PCB hash. This script checks all seven
native schematic revision labels and all local gate counts, then records exact
source and output hashes. Visual QA remains pending until every image is read.
Run the PDF artifact marker before this authoring command, exactly once.
"""
from pathlib import Path
import argparse
import datetime
import hashlib
import json
import re
import subprocess

D = Path(__file__).resolve().parents[1]
O = D / 'review'
ap = argparse.ArgumentParser(description=__doc__)
ap.add_argument('--expected-board-sha256', required=True)
a = ap.parse_args()

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def snapshot():
    paths = set(D.glob('*.kicad_*'))
    for pattern in ('library/**/*', '*.kicad_sym', 'inputs/**/*', '*-lib-table'):
        paths.update(p for p in D.glob(pattern) if p.is_file())
    for rel in ('review/design-netmap.json', 'review/manufacturing-profile.json',
        'review/approved-small-vias.json', 'review/assembly-cpl-overrides.json',
        'review/green-routing-targets.json', 'release/assembly/JLC_CPL.csv',
        'release/assembly/JLC_CPL_NATIVE_AUDIT.csv', 'tools/build_assembly_pdf.py',
        'tools/build_assembly_pdf_p5.py', 'tools/export_copper_review.py',
        'tools/export_release.py', 'tools/audit_native.py', 'tools/validate_release.py'):
        p = D / rel
        if p.exists():
            paths.add(p)
    return {str(p.relative_to(D)): sha(p) for p in sorted(paths) if p.is_file()}

def run(args, log):
    with (O / log).open('w') as stream:
        subprocess.run(args, check=True, stdout=stream, stderr=subprocess.STDOUT, cwd=D)

before = snapshot()
assert before['controller.kicad_pcb'] == a.expected_board_sha256, 'Owner freeze hash mismatch'
schematics = sorted(D.glob('*.kicad_sch'))
assert len(schematics) == 7
for p in schematics:
    assert re.findall(r'\(rev "([^"]+)"\)', p.read_text()) == ['R3-S6-P6'], f'Wrong schematic revision: {p.name}'
assert before['inputs/user-corrected-JLC_CPL.csv'] == before['release/assembly/JLC_CPL.csv'], 'Supplier CPL not exact'
started = datetime.datetime.now(datetime.timezone.utc).isoformat()
integrity = {'started_utc': started, 'revision': 'R3-S6-P6', 'source_sha256_before': before,
    'expected_native_board_sha256': a.expected_board_sha256, 'status': 'EXPORT IN PROGRESS'}
integrity_path = O / 'p6-presentation-source-integrity.json'
integrity_path.write_text(json.dumps(integrity, indent=2) + '\n')
try:
    run(['/usr/bin/python3', str(D / 'tools/export_copper_review_p6.py'),
        '--expected-board-sha256', a.expected_board_sha256], 'p6-copper-render.log')
    run(['/usr/bin/python3', str(D / 'tools/build_assembly_pdf_p6.py'), '--board', str(D / 'controller.kicad_pcb'),
        '--project', str(D), '--out', str(O / 'assembly-drawing'), '--revision', 'R3-S6-P6', '--frozen'], 'p6-assembly-authoring.log')
    schematic_pdf = O / 'controller-r3s-p6-schematic.pdf'
    run(['sh', str(D / 'tools/kicad_cli.sh'), 'sch', 'export', 'pdf', '--output', str(schematic_pdf),
        str(D / 'controller.kicad_sch')], 'p6-schematic-export.log')
    documents = {'assembly': (O / 'assembly-drawing/controller-r3s-assembly-manufacturing.pdf', 6),
        'schematic': (schematic_pdf, 7)}
    outputs = {}
    render_hashes = {}
    for name, (pdf, count) in documents.items():
        info = subprocess.check_output(['pdfinfo', str(pdf)], text=True)
        assert int(re.search(r'^Pages:\s+(\d+)', info, re.M).group(1)) == count
        content = subprocess.check_output(['pdftotext', '-layout', str(pdf), '-'], text=True)
        assert 'R3-S6-P6' in content, f'P6 revision is absent: {name}'
        assert 'R3-S6-P5' not in content, f'Stale P5 title: {name}'
        assert len([page for page in content.split('\f') if page.strip()]) == count
        render_dir = O / 'p6-pdf-qa' / name
        render_dir.mkdir(parents=True, exist_ok=True)
        run(['pdftoppm', '-r', '150', '-png', str(pdf), str(render_dir / 'page')], f'p6-{name}-render.log')
        pages = sorted(render_dir.glob('page-*.png'))
        assert len(pages) == count
        render_hashes[name] = {p.name: sha(p) for p in pages}
        outputs[str(pdf.relative_to(D))] = sha(pdf)
    outputs.update({str(p.relative_to(D)): sha(p) for p in O.glob('controller-r3s-*.svg')
        if 'copper' in p.name or '-In' in p.name})
    outputs.update({str(p.relative_to(D)): sha(p) for p in O.glob('controller-r3s-*.png')
        if 'copper' in p.name or '-In' in p.name})
    pending = {'status': 'PENDING visual inspection', 'revision': 'R3-S6-P6',
        'native_board_sha256': a.expected_board_sha256, 'pages_rendered': {'assembly': 6, 'schematic': 7},
        'pages_visually_reviewed': {'assembly': [], 'schematic': []},
        'copper_pngs_visually_reviewed': [], 'rendered_page_hashes': render_hashes,
        'output_sha256': outputs, 'source_files_unchanged': None,
        'user_CPL_rows_exact': True, 'assembly_cleared': False,
        'qualification_boundary': 'Routed prototype CAD only; supplier acceptance, assembly process and hardware validation remain pending.'}
    (O / 'p6-presentation-qa.json').write_text(json.dumps(pending, indent=2) + '\n')
finally:
    after = snapshot()
    changed = {p: {'before': before.get(p), 'after': after.get(p)} for p in before.keys() | after.keys()
        if before.get(p) != after.get(p)}
    integrity.update({'completed_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'source_sha256_after': after, 'changed_sources': changed, 'source_files_unchanged': not changed,
        'status': 'PASS source integrity' if not changed else 'FAIL source integrity'})
    integrity_path.write_text(json.dumps(integrity, indent=2) + '\n')
    assert not changed, json.dumps(changed, indent=2)
print(json.dumps({'status': 'Generated; visual inspection pending', 'native_sha256': a.expected_board_sha256,
    'source_files_unchanged': True, 'rendered_pages': render_hashes}, indent=2))
