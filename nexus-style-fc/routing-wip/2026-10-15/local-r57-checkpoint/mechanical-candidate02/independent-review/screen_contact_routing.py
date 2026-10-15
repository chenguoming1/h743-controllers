#!/usr/bin/env python3
"""Read-only sampled nominal contact-vs-retained-track screen; not connectivity/DRC."""
import sys,math,json
from pathlib import Path
import numpy as np
sys.dont_write_bytecode=True
ROOT=Path('/workspace/scratch/8a35c1f26232/nexus-header-redesign-20261015');C=ROOT/'candidate-01/nexus-style-fc';sys.path.insert(0,str(C/'tools'));import sexpr as s

def one(n,k):return s.find(n,k)[0]
def xy(n,k):return np.array(list(map(float,one(n,k)[1:3])))
def text(n,k):return s.text(one(n,k)[-1])
def ref(n):return next(s.text(p[2]) for p in s.find(n,'property') if s.text(p[1])=='Reference')
def ps(n):
 a,b=xy(n,'start'),xy(n,'end');q=max(2,math.ceil(np.linalg.norm(b-a)/.002)+1);return a+(b-a)*np.linspace(0,1,q)[:,None]
def rectdist(p,center,half):return np.linalg.norm(np.maximum(np.abs(p-center)-half,0),axis=1)
r={}
for which,rel in [('main','hardware/nexus-style-fc.kicad_pcb'),('child','hardware/header-board/nexus-header-board.kicad_pcb')]:
 b=s.parse((C/rel).read_text());records=[]
 for fp in s.find(b,'footprint'):
  rr=ref(fp)
  if (which=='main' and rr!='J1') or (which=='child' and rr=='J1'):continue
  assert len(one(fp,'at'))==3 or float(one(fp,'at')[3])==0
  for p in s.find(fp,'pad'):
   center=xy(fp,'at')+xy(p,'at');half=xy(p,'size')/2;layers=[s.text(l) for l in one(p,'layers')[1:] if s.text(l).endswith('.Cu')];pn=text(p,'net');same=1e99;shorts=[]
   for t in s.find(b,'segment'):
    if text(t,'layer') not in layers:continue
    a,z=xy(t,'start'),xy(t,'end');rad=float(one(t,'width')[1])/2
    # skip only geometrically distant unrelated segments
    if text(t,'net')!=pn and (np.any(np.maximum(a,z)<center-half-rad) or np.any(np.minimum(a,z)>center+half+rad)):continue
    dist=float(np.min(rectdist(ps(t),center,half)))-rad
    if text(t,'net')==pn:same=min(same,dist)
    elif dist<0:shorts.append({'track_uuid':text(t,'uuid'),'net':text(t,'net'),'nominal_overlap_mm':-dist})
   for v in s.find(b,'via'):
    if text(v,'net')==pn:same=min(same,float(rectdist(xy(v,'at')[None,:],center,half)[0])-float(one(v,'size')[1])/2)
   records.append({'ref':rr,'pad_number':s.text(p[1]),'pad_uuid':text(p,'uuid'),'net':pn,'minimum_same_net_track_or_via_gap_upper_bound_mm':same,'other_net_track_overlaps':shorts})
 r[which]=records
print(json.dumps(r,indent=2))
