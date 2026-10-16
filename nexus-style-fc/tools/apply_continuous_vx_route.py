#!/usr/bin/env python3
"""Reproduce the reviewed V2 routing delta from the exact V1 matched-fit PCB.
Never edits the input. Output must not exist; refill and native checks are required.
This is the source-bound routed-board generator step, not a new autorouter.
"""
from pathlib import Path
import argparse,hashlib,uuid
import sexpr as s
ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--input',required=True);ap.add_argument('--output',required=True);args=ap.parse_args()
src=Path(args.input);P=Path(args.output);assert not P.exists(), 'Output exists; preserve rollback'
assert hashlib.sha256(src.read_bytes()).hexdigest()=='624e53e3de157331bd17a444e6f9c813a1ef21cab0b007a02c1a87fb11f8d869', 'Source is not the reviewed matched V1'
P.parent.mkdir(parents=True,exist_ok=True)
b=s.parse(src.read_text());one=lambda n,k:s.find(n,k)[0];net=lambda n:s.text(one(n,'net')[-1]);uid=lambda n:s.text(one(n,'uuid')[1]);q=lambda v:('s',v)
remove={'52fcbd80-6632-4a6b-afda-c029bcd74a10','5e204930-1a49-4cb9-8804-772684912cce','bab4ace0-e97a-4223-b188-4f425d204e84','c7529157-fdb0-4a19-9332-597f8a0fab2b','3c9361c0-bd79-4ae1-854a-1afbcbd154c4'}
removed=[];moved=[]
for n in b:
 if not isinstance(n,list):continue
 if n[0] in ('segment','via'):
  if uid(n) in remove:removed.append(uid(n))
  elif n[0]=='segment' and net(n)=='ESC' and s.text(one(n,'layer')[1])=='F.Cu':one(n,'layer')[1]=q('B.Cu');moved.append(uid(n))
  elif n[0]=='segment' and uid(n)=='f9db54a0-0228-48db-8cfe-34254eb9cbaa':one(n,'layer')[1]=q('F.Cu')
  elif n[0]=='segment' and uid(n)=='2dc968c3-652e-419f-bcaf-cdf4575152a0':one(n,'start')[1:]=['115.1','104.95'];one(n,'width')[1]='0.6'
assert set(removed)==remove and len(moved)==6
b=[n for n in b if not(isinstance(n,list) and n[0] in ('segment','via') and uid(n) in remove)]
ns=uuid.UUID('2b654f3b-9ca6-43e9-a384-5100ba8fde43');newid=lambda v:str(uuid.uuid5(ns,v));vias=[(114.5,104.35),(114.5,104.95),(115.1,104.95)]
for i,(x,y) in enumerate(vias):b.append(s.parse(f'(via (at {x} {y}) (size 0.6) (drill 0.3) (layers "F.Cu" "B.Cu") (net "VX") (uuid "{newid("via-"+str(i))}"))'))
for i,(a,c) in enumerate(zip(vias,vias[1:])):b.append(s.parse(f'(segment (start {a[0]} {a[1]}) (end {c[0]} {c[1]}) (width 0.6) (layer "B.Cu") (net "VX") (uuid "{newid("branch-"+str(i))}"))'))
for z in s.find(b,'zone'):z[:]=[n for n in z if not(isinstance(n,list) and n[0] in ('filled_polygon','fill_segments'))]
P.write_text(s.dump(b)+'\n')
print('Wrote unfinished output; native refill/DRC and source binding are required:',P)
