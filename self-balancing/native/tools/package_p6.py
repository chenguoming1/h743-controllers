#!/usr/bin/env python3
"""Package an exact, independently closed P6 release; never generate CAD.

The owner supplies an explicit file inventory after the final checks. Every source
byte is fixed by that inventory, and every archived byte is checked after writing.
No diagnostic fabrication archive or prior release is included automatically.
"""
from pathlib import Path
import argparse, hashlib, json, zipfile

sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
p = argparse.ArgumentParser()
p.add_argument('--spec', required=True, type=Path)
a = p.parse_args()
spec_path = a.spec.resolve()
s = json.loads(spec_path.read_text())
project = Path(s['project']).resolve()
expected = s['native_sha256']
assert sha(project / 'controller.kicad_pcb') == expected
assert s['revision'] == 'R3-S6-P6'
assert s['supersedes_unsafe_prior_release'] is True
for item in s['required_evidence']:
    path = Path(item['path'])
    assert path.is_file() and sha(path) == item['sha256'], path
    if item.get('json_predicates'):
        document = json.loads(path.read_text())
        for dotted, wanted in item['json_predicates'].items():
            actual = document
            for key in dotted.split('.'):
                actual = actual[key]
            assert actual == wanted, (path, dotted, actual, wanted)

files = s['files']
assert files and len({x['archive_path'] for x in files}) == len(files)
contents = {}
for row in files:
    name = row['archive_path']
    assert not name.startswith('/') and '..' not in Path(name).parts
    assert not name.lower().endswith('.zip'), 'Nested manufacturing ZIPs are not allowed'
    assert not any(x in name.upper() for x in ['DIAGNOSTIC-NOT-FOR-MANUFACTURE', 'DIAGNOSTIC-ONLY'])
    source = Path(row['path'])
    assert source.is_file() and sha(source) == row['sha256'], source
    contents[name] = source.read_bytes()
assert hashlib.sha256(contents['native/controller.kicad_pcb']).hexdigest() == expected
for suffix, target in [('JLC_BOM.csv', s['bom_sha256']), ('JLC_CPL.csv', s['cpl_sha256'])]:
    name = 'release/assembly/' + suffix
    assert hashlib.sha256(contents[name]).hexdigest() == target
assert 'README.md' in contents
contents['PRODUCTION_READINESS.txt'] = s['production_readiness_text'].encode()
contents['history/BASELINE_NOT_FOR_FABRICATION.txt'] = (
    'P6 supersedes all earlier fabrication packages. P5 contained confirmed narrow copper joints. '
    'Any preserved baseline under reconstruction/ exists solely to reproduce and audit the corrected P6 source. '
    'Never fabricate it. Use only the current release/ files after the specified CAM selections and '
    'preassembly production-data approvals.\n'
).encode()
manifest = {n: hashlib.sha256(data).hexdigest() for n, data in contents.items()}
contents['SHA256_MANIFEST.json'] = (json.dumps(manifest, indent=2) + '\n').encode()
out = Path(s['output']).resolve()
out.parent.mkdir(parents=True, exist_ok=True)
assert not out.exists(), 'Preserve any prior package; do not overwrite it blindly'
with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as z:
    for name in sorted(contents):
        info = zipfile.ZipInfo(name, (2026, 10, 3, 0, 0, 0))
        info.compress_type = zipfile.ZIP_DEFLATED
        info.external_attr = 0o644 << 16
        z.writestr(info, contents[name])
with zipfile.ZipFile(out) as z:
    assert z.testzip() is None
    assert set(z.namelist()) == set(contents)
    assert all(hashlib.sha256(z.read(n)).hexdigest() == h for n, h in manifest.items())
assert sha(project / 'controller.kicad_pcb') == expected
for row in files:
    assert sha(Path(row['path'])) == row['sha256'], 'Source changed while packaging'
result = {'status': 'PASS EXACT PACKAGE BYTES AND CRC', 'revision': s['revision'],
          'native_sha256': expected, 'package': str(out), 'package_sha256': sha(out),
          'package_bytes': out.stat().st_size, 'members': len(contents),
          'spec_sha256': sha(spec_path), 'verified_member_hash_count': len(manifest),
          'assembly_production_approval_claimed': False,
          'historical_baseline_fabrication_prohibited': True}
Path(s['result']).write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2))
