#!/usr/bin/env python3
"""Activate or restore the exact diagnostic source in a separate source copy.

No compile or execution is performed. Run compile.sh afterward in the chosen
copy if a new runtime is needed; historical binary hashes are not regenerated.
"""
import argparse
import hashlib
import json
from pathlib import Path

PACKAGE=Path(__file__).resolve().parents[1]
RELATIVE='src/app/freerouting/autoroute/InsertFoundConnectionAlgo.java'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--root',type=Path,required=True);ap.add_argument('--restore-baseline',action='store_true');a=ap.parse_args();root=a.root.resolve()
    if root==PACKAGE:raise ValueError('Use a separate writable copy; sealed package is immutable')
    diag=PACKAGE/'tests/complete-path-diagnostics';baseline=json.loads((diag/'baseline-identity.json').read_text());overlay=diag/'InsertFoundConnectionAlgo.java';promotion=json.loads((diag/'promotion-identity.json').read_text());change=next(x for x in promotion['changed_files'] if x['path']==RELATIVE)
    assert sha(PACKAGE/RELATIVE)==change['before_sha256']==baseline[RELATIVE]
    assert sha(overlay)==change['after_sha256']
    for name,digest in baseline.items():
        if not name.startswith('src/'):continue
        expected=change['after_sha256'] if a.restore_baseline and name==RELATIVE else digest
        assert sha(root/name)==expected,'Unexpected source identity: '+name
    (root/RELATIVE).write_bytes((PACKAGE/RELATIVE if a.restore_baseline else overlay).read_bytes())
    print(json.dumps(dict(passed=True,source_sha256=sha(root/RELATIVE),diagnostics_overlay_active=not a.restore_baseline,compiled=False,runtime_executed=False)))

if __name__=='__main__':main()
