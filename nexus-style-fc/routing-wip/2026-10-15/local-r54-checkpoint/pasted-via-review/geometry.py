"""Source-bound LDO transaction proposal. Text/analytic geometry only.
Never imports KiCad, modifies a PCB, refills, runs DRC, solves routes or publishes.
"""
from pathlib import Path
import json, math, hashlib, re, collections
OUT=Path('/workspace/shared/nexus-pasted-via-review')
SOURCE=Path('/workspace/scratch/8a35c1f26232/nexus-recovery-20261015/routing-continuation/r53-cc2-bend/hardware/nexus-style-fc.kicad_pcb')
EXPECTED='3e0795a336cb3fd461b4c5a80025cc676028986f0b467ef331c10f505da8f842'
REVIEW=Path('/workspace/shared/nexus-boardlevel-review-recovery/fresh-batch35-geometry.json')
sha=lambda b:hashlib.sha256(b).hexdigest()
raw=SOURCE.read_bytes();assert sha(raw)==EXPECTED
s=raw.decode(); stack=[];spans={};root=None
for m in re.finditer(r'\(|\)|"(?:\\.|[^"\\])*"|[^\s()]+',s):
 t=m.group()
 if t=='(':
  n=[]
  if stack:stack[-1][0].append(n)
  stack.append((n,m.start()))
 elif t==')':
  n,i=stack.pop();spans[id(n)]=(i,m.end())
  if not stack:root=n
 else:stack[-1][0].append(t[1:-1] if t.startswith('"') else t)
assert root[0]=='kicad_pcb' and not stack
subs=lambda n,k:[x for x in n[1:] if isinstance(x,list) and x and x[0]==k]
def sub(n,k):return next(iter(subs(n,k)),None)
def val(n,k,d=None):
 x=sub(n,k);return x[1] if x and len(x)>1 else d
def xy(n,k):return [float(x) for x in sub(n,k)[1:3]]
def block(n):a,b=spans[id(n)];return s[a:b]
def canon(n):return sha(json.dumps(n,separators=(',',':'),ensure_ascii=False).encode())
def prop(n,key):return next((x[2] for x in subs(n,'property') if x[1]==key),None)
layers=[n[1] for n in sub(root,'layers')[1:] if isinstance(n,list) and n[1].endswith('.Cu')]
items={}; nodes={};footprints={};zones=[];unsupported=[]
def put(o,n):
 assert o['uuid'] not in items
 items[o['uuid']]=o;nodes[o['uuid']]=n;o['source_node_sha256']=sha(block(n).encode())
for n in root[1:]:
 if not isinstance(n,list) or not n:continue
 k=n[0]
 if k=='segment':
  o=dict(uuid=val(n,'uuid'),kind=k,net=val(n,'net',''),layers=[val(n,'layer')],start=xy(n,'start'),end=xy(n,'end'),width_mm=float(val(n,'width')))
  o['length_mm']=math.dist(o['start'],o['end']);put(o,n)
 elif k=='via':
  ends=sub(n,'layers')[1:];a,b=sorted(layers.index(l) for l in ends);tent=sub(n,'tenting')
  o=dict(uuid=val(n,'uuid'),kind=k,net=val(n,'net',''),at=xy(n,'at'),diameter_mm=float(val(n,'size')),drill_mm=float(val(n,'drill')),layer_endpoints=ends,layers=layers[a:b+1],via_type=next((x for x in n[1:] if isinstance(x,str)),'through'),tenting=dict(front=val(tent,'front') if tent else 'not_explicit',back=val(tent,'back') if tent else 'not_explicit'))
  put(o,n)
 elif k=='footprint':
  ref=prop(n,'Reference');footprints[ref]=n;fp=xy(n,'at');at=sub(n,'at');ang=float(at[3]) if len(at)>3 else 0;theta=math.radians(-ang)
  for p in subs(n,'pad'):
   loc=xy(p,'at');pa=sub(p,'at');ga=float(pa[3]) if len(pa)>3 else 0
   gp=[fp[0]+loc[0]*math.cos(theta)-loc[1]*math.sin(theta),fp[1]+loc[0]*math.sin(theta)+loc[1]*math.cos(theta)]
   ls=sub(p,'layers')[1:];ls=[l for l in layers if l in ls or '*.Cu' in ls or ('F&B.Cu' in ls and l in ['F.Cu','B.Cu'])]
   drill=sub(p,'drill');drillvals=[] if not drill else [float(x) for x in drill[1:] if isinstance(x,str) and re.fullmatch('[0-9.]+',x)]
   o=dict(uuid=val(p,'uuid'),kind='pad',net=val(p,'net',''),ref=ref,value=prop(n,'Value'),pin=p[1],pad_type=p[2],shape=p[3],at=gp,size_mm=xy(p,'size'),rotation_deg=ga,layers=ls,all_native_layers=sub(p,'layers')[1:],roundrect_rratio=float(val(p,'roundrect_rratio',0)),drill_mm=drillvals,footprint_uuid=val(n,'uuid'))
   if p[3]=='custom':
    prim=sub(p,'primitives');poly=sub(prim,'gr_poly') if prim else None
    if poly and len(prim)==2 and val(poly,'fill')=='yes':
     o['custom_polygon_local']=[[float(v) for v in x[1:3]] for x in sub(poly,'pts')[1:] if x[0]=='xy'];o['custom_polygon_width_mm']=float(val(poly,'width',0))
   put(o,p)
  for g in n[1:]:
   if isinstance(g,list) and g and g[0].startswith('fp_') and (val(g,'layer') or '').endswith('.Cu'):unsupported.append(dict(kind=g[0],uuid=val(g,'uuid'),ref=ref,layer=val(g,'layer')))
 elif k=='zone':
  z=dict(uuid=val(n,'uuid'),net=val(n,'net',''),layer=val(n,'layer'),fill_polygons=[],source_node_sha256=sha(block(n).encode()),is_rule_area=sub(n,'keepout') is not None)
  for j,p in enumerate(subs(n,'filled_polygon')):
   pts=[[float(v) for v in x[1:3]] for x in sub(p,'pts')[1:] if x[0]=='xy']
   z['fill_polygons'].append(dict(index=j,layer=val(p,'layer',z['layer']),points=pts,island='island' in p))
  zones.append(z)
 elif k=='arc':unsupported.append(dict(kind='arc',uuid=val(n,'uuid'),layer=val(n,'layer')))
 elif k.startswith('gr_') and (val(n,'layer') or '').endswith('.Cu'):unsupported.append(dict(kind=k,uuid=val(n,'uuid'),layer=val(n,'layer')))
# Capsules, circles, rectangles, rounded rectangles and ovals as convex base + radius.
EPS=1e-9
cross=lambda a,b,c:(b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
def point_seg(p,a,b):
 dx,dy=b[0]-a[0],b[1]-a[1];den=dx*dx+dy*dy
 t=0 if den==0 else max(0,min(1,((p[0]-a[0])*dx+(p[1]-a[1])*dy)/den))
 return math.dist(p,[a[0]+t*dx,a[1]+t*dy])
def segdist(a,b,c,d):
 p,q,r,t=cross(a,b,c),cross(a,b,d),cross(c,d,a),cross(c,d,b)
 if p*q<0 and r*t<0:return 0.
 return min(point_seg(a,c,d),point_seg(b,c,d),point_seg(c,a,b),point_seg(d,a,b))
def edges(poly):return list(zip(poly,poly[1:]+poly[:1])) if len(poly)>2 else [(poly[0],poly[-1])]
def contains(p,poly):
 if len(poly)<3:return point_seg(p,poly[0],poly[-1])<=EPS
 inside=False
 for a,b in edges(poly):
  if point_seg(p,a,b)<=EPS:return True
  if (a[1]>p[1])!=(b[1]>p[1]) and p[0]<(b[0]-a[0])*(p[1]-a[1])/(b[1]-a[1])+a[0]:inside=not inside
 return inside
shape_cache={}
def shape(o):
 key=o['uuid']
 if key in shape_cache:return shape_cache[key]
 k=o['kind']
 if k=='segment':res=([o['start'],o['end']],o['width_mm']/2)
 elif k=='via':res=([o['at']],o['diameter_mm']/2)
 elif k=='pad':
  w,h=o['size_mm'];sh=o['shape'];r=0
  if sh=='circle':assert abs(w-h)<EPS;pts=[[0,0]];r=w/2
  elif sh=='oval':
   r=min(w,h)/2;pts=[[-(w/2-r),-(h/2-r)],[(w/2-r),(h/2-r)]]
  elif sh in ['rect','roundrect']:
   r=min(w,h)*o['roundrect_rratio'] if sh=='roundrect' else 0
   a,b=w/2-r,h/2-r;pts=[[-a,-b],[a,-b],[a,b],[-a,b]]
  elif sh=='custom' and 'custom_polygon_local' in o:
   pts=o['custom_polygon_local'];r=o['custom_polygon_width_mm']/2
   assert contains([0,0],pts) and min(point_seg([0,0],a,b) for a,b in edges(pts))>=max(w,h)/2, 'Custom anchor is not fully contained'
  else:raise ValueError('Unsupported pad '+key+' '+sh)
  t=math.radians(-o['rotation_deg']);x,y=o['at'];res=([[x+p[0]*math.cos(t)-p[1]*math.sin(t),y+p[0]*math.sin(t)+p[1]*math.cos(t)] for p in pts],r)
 else:raise ValueError(k)
 shape_cache[key]=res;return res
def bases_dist(a,b):
 if (len(a)>2 and contains(b[0],a)) or (len(b)>2 and contains(a[0],b)):return 0.
 return min(segdist(x,y,u,v) for x,y in edges(a) for u,v in edges(b))
def gap(a,b):
 x,r=shape(a);y,t=shape(b);return bases_dist(x,y)-r-t
for o in items.values():
 try:shape(o)
 except ValueError as e:unsupported.append(dict(uuid=o['uuid'],kind=o['kind'],error=str(e)))
