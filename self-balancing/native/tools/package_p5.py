#!/usr/bin/python3
"""Package the frozen P5 native, fabrication and verified visual evidence."""
from pathlib import Path
import hashlib, json, shutil, zipfile

D = Path(__file__).resolve().parents[1]
ROOT = D.parent
O = Path('/workspace/scratch/8a35c1f26232/p5-output')
E = ROOT / 'research/controller-r3s-p5-independent-validation/final-6e2031b0'
REPLAY = ROOT / 'research/controller-r3s-p5-route-cleanup/final-refinement'
NATIVE = '6e2031b040ce8f3a534c2f73abb0091e25b3e6adcab982463264ad8898d65cf8'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(D / 'controller.kicad_pcb') == NATIVE
gate = json.loads((D / 'review/green-routing-targets.json').read_text())
assert gate['revision'] == 'R3-S6-P5'
assert gate['full_layer_geometry_audit_pass'] and gate['supplier_trace_green_confirmed']
assert gate['supplier_rerun_complete']
assert gate['supplier_trace_width_red_yellow'] == gate['supplier_trace_spacing_red_yellow'] == [0, 0]
for n in ['routing-drc.json', 'p5-pin-audit.json']:
    q = json.loads((D / 'review' / n).read_text())
    assert not any(q.get(k) for k in ['violations', 'unconnected_items', 'schematic_parity', 'errors', 'unexpected_map_entries'])
summary = json.loads((E / 'final-independent-summary.json').read_text())
assert summary['native_sha256'] == NATIVE and summary['status'].startswith('PASS')
assert summary['release_manifest_sha256'] == sha(D / 'release/SHA256_MANIFEST.json')
manifest = json.loads((D / 'release/SHA256_MANIFEST.json').read_text())
assert all(sha(D / 'release' / n) == h for n, h in manifest.items())
assert json.loads((D / 'review/assembly-drawing/assembly-drawing-manifest.json').read_text())['visual_QA']['status'] == 'PASS'
assert json.loads((D / 'review/copper-review-manifest.json').read_text())['visual_QA']['status'] == 'PASS'
assert json.loads((D / 'review/p5-report-visual-qa.json').read_text())['status'].startswith('PASS')
visual = json.loads((D / 'review/routing-visual-review/visual-review-manifest.json').read_text())
assert visual['final_sha256'] == NATIVE and visual['status'].startswith('VISUAL_ACCEPTED')
assert all(sha(D / 'review/routing-visual-review' / n) == h for n, h in visual['files'].items())

entries = {}
def add(src, dst):
    src = Path(src)
    assert src.is_file(), src
    assert dst not in entries, dst
    entries[dst] = src.read_bytes()

def tree(src, dst, exclude=(), skip_vendor_pdf=False):
    for p in sorted(Path(src).rglob('*')):
        rel = p.relative_to(src)
        if not p.is_file() or any(x in rel.parts for x in exclude) or p.suffix in ['.pyc', '.kicad_prl', '.log'] or p.name.endswith('.lck'):
            continue
        if skip_vendor_pdf and p.suffix.lower() == '.pdf':
            continue
        assert 'DIAGNOSTIC-ONLY' not in p.name and p.suffix.lower() != '.zip', p
        add(p, dst + '/' + str(rel))

for p in D.iterdir():
    if p.is_file() and (p.suffix in ['.kicad_pcb', '.kicad_pro', '.kicad_sch', '.kicad_dru'] or p.name in ['fp-lib-table', 'sym-lib-table', 'README.md']):
        add(p, 'native/' + p.name)
tree(D / 'library', 'native/library')
tree(D / 'tools', 'native/tools', ('__pycache__', 'history-P3'))
tree(D / 'inputs', 'native/inputs')
review_names = [
    'audit_controller_r3s_independent.py', 'controller-r3s-independent-expectations.json',
    'controller-netlist.xml', 'design-netmap.json', 'bom-draft.csv', 'approved-small-vias.json',
    'historical-P2-via-inventory.json', 'assembly-cpl-overrides.json', 'manufacturing-profile.json',
    'h743-pin-map.json', 'edge-pad-map.json', 'printed-pad-legend.json', 'pad-wiring-map.csv',
    'green-routing-targets.json', 'erc.json', 'routing-drc.json', 'p5-pin-audit.json',
    'p5-baseline.json', 'p5-integration.json', 'p5-final-refinement.json',
    'p5-revision-geometry.json', 'p5-uncapped-copper-census.json', 'p5-refill-verification.json',
    'p5-native-gate-summary.json', 'generated-gerber-job-original.json', 'gerber-job-normalization.json',
    'p5-report-visual-qa.json', 'schematic-pdf-visual-qa.json', 'copper-review-manifest.json',
    'p5-presentation-qa.json', 'p5-presentation-source-integrity.json', 'p5-presentation-geometry-proof.json',
    'p5-mask-advisory-disposition.json', 'p5-export-verification-before-supplier.json', 'p5-release-manifest-before-supplier.json'
]
for n in review_names:
    add(D / 'review' / n, 'native/review/' + n)
tree(D / 'review/sourcing', 'native/review/sourcing')
tree(D / 'release', 'release')
tree(E, 'validation/independent', ('__pycache__', 'cli-snapshot', 'fresh-native-gerbers', 'renders', 'advisory-native-gerbers', 'diagnostic-mask-exports'))
for p in sorted(E.parent.glob('*.py')):
    add(p, 'validation/tools/' + p.name)
tree(E.parent / 'frozen-tools', 'validation/tools/frozen-tools', ('__pycache__',))
for n in ['controller.kicad_pcb', 'controller.kicad_pro', 'controller.kicad_dru', 'source-delta.json',
          'replay_final.py', 'finalize_candidate.py', 'README.md', 'by-net-changes.csv',
          'refinement.json', 'width-transition-census.json', 'width-transition-applied.json', 'drc-all.json']:
    add(REPLAY / n, 'reconstruction/' + n)
tree(REPLAY / 'input-p4', 'reconstruction/input-p4')
add(REPLAY / 'reproduced/replay-result.json', 'reconstruction/replay-result.json')
tree(D / 'review/routing-visual-review', 'visual-review')
tree(D / 'review/supplier-p5-evidence', 'dfm/production-P5')
tree(D / 'review/supplier-p4-evidence', 'dfm/history-P4')
tree(D / 'review/smt-manufacturer-evidence', 'dfm/manufacturer-and-diagnostic-evidence', ('__pycache__',), skip_vendor_pdf=True)
for n in ['assembly-drawing/controller-r3s-assembly-manufacturing.pdf', 'assembly-drawing/assembly-drawing-manifest.json',
          'controller-r3s-p5-schematic.pdf', 'R3-S6-P5-Routing-Review.pdf', 'P5-Routing-Review.md',
          'controller-r3s-front-copper.png', 'controller-r3s-rear-copper.png']:
    add(D / 'review' / n, 'documents/' + Path(n).name)
for n in ['P4-DFM-Review.md', 'R3-S6-P4-DFM-Review.pdf', 'p4-front-slot-changes.json', 'p4-d4-rectangle-change.json']:
    add(D / 'review' / n, 'history/' + n)
for n in ['manufacturing-profile.json', 'approved-small-vias.json', 'assembly-cpl-overrides.json',
          'green-routing-targets.json', 'pad-wiring-map.csv', 'printed-pad-legend.json']:
    add(D / 'review' / n, 'fabrication-notes/' + n)
for p in (ROOT / 'recovery-p2-20261003/qualification').iterdir():
    if p.is_file():
        add(p, 'qualification/' + p.name)
add(D / 'README.md', 'README.md')
entries['ASSEMBLY_NOT_CLEARED.txt'] = (
    'P5 routing cleanup passes local native/export checks and the recorded supplier trace-width/spacing checks. '
    'Remaining SMT reports have documented package/process dispositions; supplier model/pin1, carrier, stencil/reflow, '
    'USB firmware policy and physical hardware qualification remain. Production U2/U11 split paste is intact. '
    'Diagnostic fabrication files are excluded. No order is authorized by this package.\n'
).encode()
entries['history/README.txt'] = b'P4 reports are preserved as component/DFM history. Use current native/, release/ and documents/. The exact P4 reconstruction baseline is under reconstruction/input-p4/.\n'
hashes = {n: hashlib.sha256(v).hexdigest() for n, v in entries.items()}
entries['SHA256_MANIFEST.json'] = (json.dumps(hashes, indent=2) + '\n').encode()
O.mkdir(exist_ok=True)
out = O / 'R3-S6-P5-Native-Fabrication-ASSEMBLY-HOLD.zip'
with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as z:
    for n, v in sorted(entries.items()):
        z.writestr(n, v)
with zipfile.ZipFile(out) as z:
    assert z.testzip() is None
    assert all(hashlib.sha256(z.read(n)).hexdigest() == h for n, h in hashes.items())
    assert not any('DIAGNOSTIC-ONLY' in n or n.lower().endswith('.zip') for n in z.namelist())
for src, name in [('review/R3-S6-P5-Routing-Review.pdf', 'R3-S6-P5-Routing-Review.pdf'),
                  ('review/assembly-drawing/controller-r3s-assembly-manufacturing.pdf', 'R3-S6-P5-Assembly.pdf'),
                  ('review/controller-r3s-p5-schematic.pdf', 'R3-S6-P5-Schematic.pdf'),
                  ('review/controller-r3s-front-copper.png', 'R3-S6-P5-Front-Copper.png'),
                  ('review/controller-r3s-rear-copper.png', 'R3-S6-P5-Rear-Copper.png')]:
    shutil.copy2(D / src, O / name)
result = {'native_sha256': NATIVE, 'package': str(out), 'package_sha256': sha(out),
          'package_bytes': out.stat().st_size, 'members': len(entries),
          'CRC_and_all_member_hashes': 'PASS', 'diagnostic_fabrication_files_included': False,
          'artifacts': {p.name: {'path': str(p), 'sha256': sha(p), 'bytes': p.stat().st_size}
                        for p in O.iterdir() if p.is_file() and p.suffix in ['.zip', '.csv', '.pdf', '.png']}}
(O / 'release-artifacts.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2))
