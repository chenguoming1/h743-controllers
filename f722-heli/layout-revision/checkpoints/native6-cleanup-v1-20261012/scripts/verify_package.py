#!/usr/bin/env python3
"""Verify every checkpoint payload byte against the immutable delivery manifest."""
import hashlib,json
from pathlib import Path
root=Path(__file__).resolve().parent.parent
manifest=json.loads((root/'delivery-manifest.json').read_text())
actual={str(p.relative_to(root)) for p in root.rglob('*') if p.is_file() and '__pycache__' not in p.parts}
expected={r['path'] for r in manifest['files']}
if actual != expected|{'delivery-manifest.json'}:raise SystemExit('Unexpected or missing files')
for row in manifest['files']:
 data=(root/row['path']).read_bytes()
 assert len(data)==row['bytes'],row['path']
 assert hashlib.sha256(data).hexdigest()==row['sha256'],row['path']
 assert hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()==row['git_blob_sha'],row['path']
print(json.dumps({'verified_files':len(expected),'all_size_SHA256_and_Git_blob_hashes_match':True}))
