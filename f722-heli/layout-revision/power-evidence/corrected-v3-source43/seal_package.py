#!/usr/bin/env python3
"""Seal a completed local packet once; makes no external/canonical/Git changes."""
import hashlib,json
from pathlib import Path
root=Path(__file__).resolve().parent
manifest=root/'MANIFEST.json'
if manifest.exists():raise SystemExit('Refusing to overwrite an existing package seal')
files={}
for f in sorted(root.rglob('*')):
    if not f.is_file() or '__pycache__'in f.parts:continue
    files[f.relative_to(root).as_posix()]={'sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'bytes':f.stat().st_size}
obj={'schema':'f722-portable-corrected-power-evidence/v1','status':'LOCAL EXACT SOURCE43 CONDITIONAL EVIDENCE; NOT CURRENT SOURCE44 QUALIFICATION',
'board_sha256':'1ee7174a578dffe4d5ef3ae8b39d8dc88f28b80395539263a65f23be234c21e6',
'raw_result_sha256':'1466a094fc40cfbed24fbda76d5445bad9c06d951389e2440ed6b0cd3b13bac9',
'combined_summary_sha256':'030fa2ae528c45d9f0207eac4fb9b93c74cc84cf3296035f995d869bf0409550',
'raw_result_included':False,'raw_recovery_available_separately':True,'numerical_rerun_performed_by_packaging':False,
'files':files}
manifest.write_text(json.dumps(obj,indent=2,allow_nan=False)+'\n')
print(json.dumps({'manifest_sha256':hashlib.sha256(manifest.read_bytes()).hexdigest(),'files':len(files),'total_bytes':sum(r['bytes']for r in files.values())+manifest.stat().st_size}))
