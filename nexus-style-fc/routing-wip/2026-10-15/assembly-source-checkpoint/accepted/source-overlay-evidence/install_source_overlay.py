#!/usr/bin/env python3
"""Install exact reviewed source overlay onto a sole-lane stage08-derived candidate.
The caller owns the PCB and supplies its exact current SHA. This helper never edits it.
Requires all other hardware/tools inputs to match stage08; no stage09 helper retained.
"""
import argparse,hashlib,json,pathlib,sys
if not __debug__: raise SystemExit('Refusing optimized Python: active guards are required')
HERE=pathlib.Path(__file__).resolve().parent

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--candidate',required=True,type=pathlib.Path);p.add_argument('--expected-pcb-sha256',required=True);p.add_argument('--expected-transaction-sha256',required=True);a=p.parse_args()
C=a.candidate.resolve();S=HERE/'source-candidate-final';T=S/'source-variant-transaction.json';assert sha(T)==a.expected_transaction_sha256
r=json.loads(T.read_text());board='hardware/nexus-style-fc.kicad_pcb';assert C!=S.resolve() and C!=pathlib.Path(r['stage08_source']) and C!=pathlib.Path(r['stage09_artwork_source'])
assert sha(C/board)==a.expected_pcb_sha256
assert not (C/'tools/assembly_annotations.py').exists(),'Obsolete runtime annotation helper must not enter this stage08-derived source lane'
for rel,h in r['source_input_sha256'].items():
 if rel!=board:assert sha(C/rel)==h,('candidate is not exact stage08 source',rel)
for row in r['overlay_files']:
 rel=row['path'];assert rel!=board and sha(S/rel)==row['new_sha256']
 if row['source_sha256'] is None:assert not (C/rel).exists(),('unexpected existing variant',rel)
for row in r['overlay_files']:
 rel=row['path'];(C/rel).write_bytes((S/rel).read_bytes());assert sha(C/rel)==row['new_sha256']
assert sha(C/board)==a.expected_pcb_sha256
print(json.dumps({'status':'PASS exact source overlay installed; PCB unchanged','PCB_sha256':sha(C/board),'overlay_file_count':len(r['overlay_files']),'source_transaction_sha256':sha(T)},indent=2))
