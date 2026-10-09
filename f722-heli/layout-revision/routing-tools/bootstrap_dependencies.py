#!/usr/bin/env python3
"""Retrieve only the pinned official local Java engine/compiler artifacts.
Never transmits a PCB. No server/API/cloud routing is started.
"""
from pathlib import Path
import hashlib,json,urllib.request
ROOT=Path(__file__).resolve().parent
p=json.loads((ROOT/'vendor/provenance.json').read_text())
files={'freerouting-2.1.0.jar':p['freerouting']['jar_url'],'ecj-3.41.0.jar':p['ecj']['url']}
for name,url in files.items():
 target=ROOT/'vendor'/name;expected=p[name]['sha256']
 if target.exists()and hashlib.sha256(target.read_bytes()).hexdigest()==expected:print('verified',name);continue
 temp=target.with_suffix('.download')
 with urllib.request.urlopen(url,timeout=60)as response,temp.open('wb')as out:
  while block:=response.read(1024*1024):out.write(block)
 actual=hashlib.sha256(temp.read_bytes()).hexdigest()
 if actual!=expected:
  temp.unlink();raise SystemExit('Digest mismatch for '+name+'; dependency was not installed')
 temp.replace(target);print('downloaded and verified',name)
