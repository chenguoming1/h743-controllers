"""Isolated V2: make the two-layer front VX sheet continuous across all seven ports.
Move ESC signal to B.Cu; replace obstructing B VX V-bridge with three ordinary
0.60/0.30mm plated vias and local0.60mm branches into the existing T2 feeder.
No plug/pinout/outline change; no filled/capped-via process is assumed.
"""
from pathlib import Path
import sys,shutil,uuid,hashlib,json
R=Path(__file__).resolve().parents[1];S=R/'candidate-compact-matched-fit-unfinished';C=R/'candidate-continuous-vx-unfinished';assert not C.exists()
shutil.copytree(S,C,ignore=shutil.ignore_patterns('verification','__pycache__'));(C/'verification').mkdir();sys.path.insert(0,str(C/'tools'));import sexpr as s
src=S/'hardware/header-board/nexus-header-board.kicad_pcb';assert hashlib.sha256(src.read_bytes()).hexdigest()=='624e53e3de157331bd17a444e6f9c813a1ef21cab0b007a02c1a87fb11f8d869'
P=C/'hardware/header-board/nexus-header-board.kicad_pcb';b=s.parse(src.read_text());one=lambda n,k:s.find(n,k)[0];net=lambda n:s.text(one(n,'net')[-1]);uid=lambda n:s.text(one(n,'uuid')[1]);q=lambda v:('s',v)
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
(C/'verification/continuous-vx-transaction.json').write_text(json.dumps({'status':'UNFINISHED: native refill/DRC/model pending','source_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'moved_ESC_segments_F_to_B':moved,'moved_GND_SBUSToRPM_segment_B_to_F':'f9db54a0-0228-48db-8cfe-34254eb9cbaa','removed_old_VX_bridge_and_unused_ESC_via':removed,'new_VX_vias':vias,'via_diameter_drill_mm':[.6,.3],'new_B_branch_width_mm':.6,'preserved':['all pad/net/pin assignments','standard servo plugs','matched-fit outline and contacts','main board exact bytes','nominal2ozstack/rules'],'no_filled_or_capped_via_assumed':True},indent=2)+'\n')
# Carry the fit contract into the new isolated validation package.
shutil.copy2(S/'verification/geometry-contract.json',C/'verification/geometry-contract.json')
print(P)
