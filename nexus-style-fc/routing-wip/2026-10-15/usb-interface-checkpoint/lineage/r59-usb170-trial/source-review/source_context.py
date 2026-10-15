"""Read-only S-expression + numerical geometry inspection. No KiCad imports, board writes, or routing solver."""
from pathlib import Path
import re, json, math, hashlib, collections, heapq, itertools, os
os.environ["MPLCONFIGDIR"]="/tmp/nexus-usb-mpl"
import numpy as np
from matplotlib.path import Path as MPath
S=Path('/workspace/scratch/8a35c1f26232/nexus-recovery-20261015/routing-continuation/r57-rpm-center/hardware/nexus-style-fc.kicad_pcb')
D=Path('/workspace/shared/nexus-usb-stack-review/r57-inner-pair')
H='583e73ba08c80e70d42bfd726ef1b440ab0ddf4d7309cef266de486fd03f461f'
assert hashlib.sha256(S.read_bytes()).hexdigest()==H
# All atoms kept as strings so no hidden native KiCad dependency.
def parse(s):
 stack=[]; root=None
 for t in re.findall(r'\(|\)|"(?:\\.|[^"\\])*"|[^\s()]+',s):
  if t=='(':
   n=[]
   if stack:stack[-1].append(n)
   stack.append(n)
  elif t==')':
   root=stack.pop()
  else:stack[-1].append(json.loads(t) if t.startswith('"') else t)
 assert not stack
 return root
b=parse(S.read_text())
def allc(n,key):return [x for x in n if isinstance(x,list) and x and x[0]==key]
def one(n,key,default=None):
 r=allc(n,key)
 return r[0] if r else default
def val(n,key,default=None):
 r=one(n,key)
 return r[1] if r and len(r)>1 else default
def vec(n,key):return list(map(float,one(n,key)[1:3]))
ls=[x[1] for x in one(b,'layers')[1:] if isinstance(x,list) and x[1].endswith('.Cu')]
pads=[];tracks=[];vias=[];fills=collections.defaultdict(list);fill_ids=collections.defaultdict(list)
for f in allc(b,'footprint'):
 ref=next(x[2] for x in allc(f,'property') if x[1]=='Reference');value=next(x[2] for x in allc(f,'property') if x[1]=='Value')
 at=one(f,'at')[1:];x,y=map(float,at[:2]);angle=float(at[2]) if len(at)>2 else 0
 c,s=math.cos(math.radians(angle)),math.sin(math.radians(angle))
 for p in allc(f,'pad'):
  px,py=vec(p,'at');pa=one(p,'at')[1:];a=float(pa[2]) if len(pa)>2 else 0
  pads.append(dict(kind='pad',ref=ref,value=value,pin=p[1],type=p[2],shape=p[3],net=val(p,'net'),at=[round(x+c*px+s*py,9),round(y-s*px+c*py,9)],size=vec(p,'size'),rotation=a,layer=val(f,'layer'),layers=one(p,'layers')[1:],uuid=val(p,'uuid')))
for s in allc(b,'segment'):
 tracks.append(dict(kind='segment',net=val(s,'net'),start=vec(s,'start'),end=vec(s,'end'),width=float(val(s,'width')),layer=val(s,'layer'),uuid=val(s,'uuid'),length_mm=math.dist(vec(s,'start'),vec(s,'end'))))
for s in allc(b,'via'):
 vias.append(dict(kind='via',net=val(s,'net'),at=vec(s,'at'),diameter=float(val(s,'size')),drill=float(val(s,'drill')),layers=one(s,'layers')[1:],uuid=val(s,'uuid')))
for z in allc(b,'zone'):
 if val(z,'net')!='GND':continue
 for fi,f in enumerate(allc(z,'filled_polygon')):
  pts=[list(map(float,x[1:3])) for x in one(f,'pts')[1:] if isinstance(x,list)]
  fills[val(f,'layer')].append(pts)
  fill_ids[val(f,'layer')].append({'zone_uuid':val(z,'uuid'),'filled_polygon_index_within_zone':fi,'layer':val(f,'layer'),'id':val(z,'uuid')+':'+str(fi)})
stack=[];dep=0;zcenters={}
for x in allc(one(one(b,'setup'),'stackup'),'layer'):
 r={'layer':x[1],'type':val(x,'type'),'thickness_mm':float(val(x,'thickness',0)),'epsilon_r':float(val(x,'epsilon_r',0)) or None,'material':val(x,'material')}
 stack.append(r)
 if x[1].endswith('.Cu') or x[1].startswith('dielectric'):
  if x[1].endswith('.Cu'):zcenters[x[1]]=dep+r['thickness_mm']/2
  dep+=r['thickness_mm']
usbtracks=[t for t in tracks if t['net'] in ('USB_DP','USB_DM')];usbvias=[v for v in vias if v['net'] in ('USB_DP','USB_DM')]
usbparts=[p for p in pads if p['ref'] in ('J6','U7','C25','C28') or p['net'] in ('USB_DP','USB_DM')]

if __name__ == "__main__":
 (D/"source-objects.json").write_text(json.dumps(dict(source=str(S),sha256=H,pads=pads,tracks=tracks,vias=vias,stack=stack,copper_center_z_mm=zcenters),indent=2)+"\n")
