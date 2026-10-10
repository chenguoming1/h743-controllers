"""Integer-nanometre route reconciliation, independent of the KiCad API.

Preserves unchanged native segments even when SES coalesces/splits collinear
segments. Duplicate native copper is retained deliberately when covered by the
result. Only uncovered portions become new objects; absent old geometry is
removed. Geometry equality is a union, with duplicate retention reported.
"""
from collections import defaultdict
from math import gcd

def nm(v):return round(v*1e6)
def line(o):
 (x1,y1),(x2,y2)=[tuple(map(nm,p))for p in [o['start'],o['end']]];dx,dy=x2-x1,y2-y1;g=gcd(dx,dy)
 if not g:raise ValueError('Zero-length segment')
 ux,uy=dx//g,dy//g
 if ux<0 or (ux==0 and uy<0):ux,uy=-ux,-uy
 c=ux*y1-uy*x1;t1=ux*x1+uy*y1;t2=ux*x2+uy*y2
 return (o['logical_net'],o['layer'],nm(o['width']),ux,uy,c),tuple(sorted((t1,t2)))
def merge(intervals):
 result=[]
 for lo,hi in sorted(intervals):
  if result and lo<=result[-1][1]:result[-1]=(result[-1][0],max(result[-1][1],hi))
  else:result.append((lo,hi))
 return result

def subtract(intervals,remove):
 result=[];lo,hi=remove
 for a,b in intervals:
  if b<=lo or a>=hi:result.append((a,b));continue
  if a<lo:result.append((a,lo))
  if b>hi:result.append((hi,b))
 return result

def via_key(o):return(o['logical_net'],*map(nm,o['xy']),nm(o['width']),nm(o['drill']))
def geometry(routes):
 tracks=defaultdict(list);vias=set()
 for o in routes:
  if o['kind']=='track':k,i=line(o);tracks[k].append(i)
  else:vias.add(via_key(o))
 return {k:merge(v)for k,v in tracks.items()},vias

def track(k,interval):
 name,layer,w,ux,uy,c=k;norm=ux*ux+uy*uy
 def point(t):
  xx,yy=ux*t-uy*c,uy*t+ux*c
  if xx%norm or yy%norm:raise ValueError('Non-integral native route split')
  return [xx//norm/1e6,yy//norm/1e6]
 return {'kind':'track','logical_net':name,'layer':layer,'width':w/1e6,'start':point(interval[0]),'end':point(interval[1])}

def reconcile(desired,old):
 """old: UUID -> normalized native route. Return preserved UUIDs, new routes."""
 target,via_target=geometry(desired);uncovered={k:list(v)for k,v in target.items()};uncovered_vias=set(via_target);kept=[]
 for uid,o in old.items():
  if o['kind']=='track':
   k,i=line(o)
   if any(a<=i[0] and i[1]<=b for a,b in target.get(k,[])):
    kept.append(uid);uncovered[k]=subtract(uncovered[k],i)
  else:
   k=via_key(o)
   if k in via_target:kept.append(uid);uncovered_vias.discard(k)
 added=[track(k,i)for k,intervals in uncovered.items()for i in intervals]
 for o in desired:
  if o['kind']=='via'and via_key(o)in uncovered_vias:added.append(o);uncovered_vias.remove(via_key(o))
 assert geometry([old[k]for k in kept]+added)==geometry(desired)
 return kept,added

if __name__=='__main__':
 a={'kind':'track','logical_net':'N','layer':'F.Cu','width':.127,'start':[1,1],'end':[2,1]};b=dict(a,start=[2,1],end=[3,1]);whole=dict(a,end=[3,1]);extra=dict(a,start=[3,1],end=[4,1])
 kept,added=reconcile([whole],{'a':a,'duplicate':a,'b':b});assert set(kept)=={'a','duplicate','b'}and not added
 kept,added=reconcile([a,extra],{'a':a,'b':b});assert kept==['a']and len(added)==1
 assert geometry([a,b])==geometry([whole])
 print('PASS: coalescence, duplicate preservation, unchanged UUID selection, removed and newly added spans')
