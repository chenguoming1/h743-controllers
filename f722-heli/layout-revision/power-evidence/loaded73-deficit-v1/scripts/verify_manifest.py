#!/usr/bin/env python3
"""Verify this compact package without any external source or solver dependency."""
import hashlib
import json
from pathlib import Path

root=Path(__file__).resolve().parents[1]
sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
expected=(root/'MANIFEST.sha256').read_text().split()[0]
assert sha(root/'MANIFEST.json')==expected, 'Manifest hash mismatch'
manifest=json.loads((root/'MANIFEST.json').read_text())
for row in manifest['files']:
    path=root/row['path']
    assert path.is_file() and sha(path)==row['sha256'], 'File hash mismatch: '+row['path']
for row in json.loads((root/'ORIGINAL-PROVENANCE.json').read_text())['originals']:
    assert sha(root/row['packaged_path'])==row['source_sha256']==row['packaged_sha256'], 'Original receipt changed'
print(json.dumps({'status':'verified','manifest_sha256':expected,'files':len(manifest['files']),'external_inputs_checked':False,'FEM_run':False}))
