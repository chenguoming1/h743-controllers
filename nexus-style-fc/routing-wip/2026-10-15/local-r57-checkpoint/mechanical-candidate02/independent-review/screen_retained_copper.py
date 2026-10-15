#!/usr/bin/env python3
"""Independent nominal screen only. No native runtime, fills or full DRC.
Samples trace centerlines at <=0.002 mm; observed minimum is an upper bound to
true minimum, with <=0.001 mm sampling uncertainty for continuous distance.
"""
import sys,json,math
from pathlib import Path
import numpy as np
sys.dont_write_bytecode=True
ROOT=Path('/workspace/scratch/8a35c1f26232/nexus-header-redesign-20261015');C=ROOT/'candidate-01/nexus-style-fc'
sys.path.insert(0,str(C/'tools'));import sexpr as s

def one(n,k):return s.find(n,k)[0]
def xy(n,k):return np.array(list(map(float,one(n,k)[1:3])))
def uuid(n):return s.text(one(n,'uuid')[1])
def ref(n):return next(s.text(p[2]) for p in s.find(n,'property') if s.text(p[1])=='Reference')
def net(n):return s.text(one(n,'net')[-1])
def samples(n):
 a,b=xy(n,'start'),xy(n,'end');count=max(2,int(math.ceil(np.linalg.norm(b-a)/.002))+1)
 return a+(b-a)*np.linspace(0,1,count)[:,None]
def slotdist(p):
 ds=[]
 for c in ((105.6,102.4),(116.8,102.4)):
  q=np.abs(p-c)-np.array([4.5,.55]);ds.append(np.linalg.norm(np.maximum(q,0),axis=1)+np.minimum(np.max(q,axis=1),0)-.5)
 return np.minimum(*ds)
def pointseg(p,a,b):
 d=b-a;t=np.clip(np.sum((p-a)*d,axis=1)/np.dot(d,d),0,1)
 return np.linalg.norm(p-a-t[:,None]*d,axis=1)
def childdist(p,edges):
 ds=[]
 for e in edges:
  a,b=xy(e,'start'),xy(e,'end')
  if e[0]=='gr_line':ds.append(pointseg(p,a,b))
  else:
   m=xy(e,'mid');mat=2*np.stack((m-a,b-a));rhs=np.array([np.dot(m,m)-np.dot(a,a),np.dot(b,b)-np.dot(a,a)]);center=np.linalg.solve(mat,rhs);rad=np.linalg.norm(a-center)
   ang=lambda v:np.arctan2(v[...,1],v[...,0])
   aa,ma,ba=ang(a-center),ang(m-center),ang(b-center);sweep=(ba-aa)%(2*np.pi);mid=(ma-aa)%(2*np.pi)
   if mid>sweep:aa,ba=ba,aa;sweep=(ba-aa)%(2*np.pi)
   theta=(ang(p-center)-aa)%(2*np.pi);d=np.minimum(np.linalg.norm(p-a,axis=1),np.linalg.norm(p-b,axis=1));onarc=theta<=sweep+1e-8
   d[onarc]=np.abs(np.linalg.norm(p[onarc]-center,axis=1)-rad);ds.append(d)
 minimum=np.min(np.stack(ds),axis=0)
 x,y=p[:,0],p[:,1]
 inside=(x>=100)&(x<=122.4)&(y>=100)&(y<=108.4)
 # Only samples with y>=107.9 are checked, so the upper body corners are immaterial.
 for cx in (100.9,110.3,112.1,121.5):inside &= ((x-cx)**2+(y-108.4)**2>=.25-1e-10)
 tabs=(y>=108.4)&(y<=111)&(((x>=101.4)&(x<=109.8))|((x>=112.6)&(x<=121)))
 return minimum*np.where(inside|tabs,1,-1)

result={'method':__doc__,'boards':{}}
for which,rel,floor in [('main','hardware/nexus-style-fc.kicad_pcb',.3),('child','hardware/header-board/nexus-header-board.kicad_pcb',.254)]:
 board=s.parse((C/rel).read_text());edges=[n for n in board if isinstance(n,list) and n[0] in ('gr_line','gr_arc') and s.text(one(n,'layer')[1])=='Edge.Cuts']
 bad=[]
 for n in s.find(board,'segment'):
  a,b=xy(n,'start'),xy(n,'end')
  if which=='main' and min(a[1],b[1])>104:continue
  if which=='child' and max(a[1],b[1])<107.7:continue
  p=samples(n)
  if which=='child':p=p[p[:,1]>=107.9]
  if not len(p):continue
  d=(slotdist(p) if which=='main' else childdist(p,edges))-float(one(n,'width')[1])/2
  i=np.argmin(d)
  if d[i]<floor-1e-7:bad.append({'uuid':uuid(n),'net':net(n),'layer':s.text(one(n,'layer')[1]),'start':a.tolist(),'end':b.tolist(),'width':float(one(n,'width')[1]),'observed_signed_clearance_upper_bound_mm':float(d[i]),'witness_point_mm':p[i].tolist()})
 vias=[]
 for n in s.find(board,'via'):
  p=xy(n,'at')[None,:]
  if which=='child' and p[0,1]<107.9:continue
  d=(slotdist(p) if which=='main' else childdist(p,edges))[0]-float(one(n,'size')[1])/2
  if d<floor-1e-7:vias.append({'uuid':uuid(n),'net':net(n),'observed_signed_clearance_mm':d,'at':p[0].tolist()})
 result['boards'][which]={'edge_clearance_floor_mm':floor,'definite_sampled_segment_conflicts':bad,'via_conflicts':vias}
print(json.dumps(result,indent=2))
