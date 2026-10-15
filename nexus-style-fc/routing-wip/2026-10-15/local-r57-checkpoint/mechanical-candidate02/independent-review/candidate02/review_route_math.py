#!/usr/bin/env python3
"""Execute only extracted joint_copper with lightweight arithmetic stubs.
This checks routing helper calculations, not the native KiCad API or autorouter.
"""
import sys,ast,json,types,contextlib,io
from pathlib import Path
sys.dont_write_bytecode=True
R=Path('/workspace/scratch/8a35c1f26232/nexus-header-redesign-20261015');C=R/'candidate-02/nexus-style-fc';sys.path.insert(0,str(C/'tools'));import sexpr as s;import header_interface_geometry as hig
mm=lambda v:round(v*1000000)
class Vec:
 def __init__(self,x,y):self.x,self.y=x,y
class Box:
 def __init__(self,p,d):self.p,self.d=p,d
 def GetX(self):return self.p.x
 def GetY(self):return self.p.y
 def GetRight(self):return self.p.x+self.d.x
 def GetBottom(self):return self.p.y+self.d.y
 def GetCenter(self):return Vec(self.p.x+self.d.x//2,self.p.y+self.d.y//2)
class Poly:
 def __init__(self):self.points=[]
 def NewOutline(self):pass
 def Append(self,x,y):self.points.append([x,y])
class Item:
 kind='item'
 def __init__(self,b):self.properties={};self.poly=Poly()
 def __getattr__(self,n):
  if n.startswith('Set'):return lambda *v:self.properties.__setitem__(n,v)
  raise AttributeError(n)
 def Outline(self):return self.poly
class Via(Item):kind='via'
class Track(Item):kind='track'
class Zone(Item):kind='zone'
def one(n,k):return s.find(n,k)[0]
def pt(n,k):return [float(v) for v in one(n,k)[1:3]]
board=s.parse((C/'hardware/nexus-style-fc.kicad_pcb').read_text());j=next(f for f in s.find(board,'footprint') if any(s.text(v[1])=='Reference' and s.text(v[2])=='J1' for v in s.find(f,'property')))
class Pad:
 def __init__(self,p):self.p=p
 def GetAttribute(self):return 1
 def IsOnLayer(self,l):return l==31
 def GetNetname(self):return s.text(one(self.p,'net')[-1])
 def GetBoundingBox(self):
  x,y=pt(self.p,'at');ox,oy=pt(j,'at');w,h=pt(self.p,'size');return Box(Vec(mm(ox+x-w/2),mm(oy+y-h/2)),Vec(mm(w),mm(h)))
class Joint:
 rotation=0;layer=0
 def Pads(self):return [Pad(p) for p in s.find(j,'pad')]
 def GetOrientationDegrees(self):return self.rotation
 def GetLayer(self):return self.layer
 def GetPosition(self):return Vec(*[mm(v) for v in pt(j,'at')])
class Board:
 def __init__(self):self.items=[];self.j=Joint()
 def FindFootprintByReference(self,r):assert r=='J1';return self.j
 def GetNetInfo(self):return self
 def GetNetItem(self,n):return n
 def Add(self,i):self.items.append(i)
fake=types.SimpleNamespace(BOX2I=Box,VECTOR2I=Vec,PCB_VIA=Via,PCB_TRACK=Track,ZONE=Zone,PAD_ATTRIB_NPTH=0,F_Cu=0,B_Cu=31,In1_Cu=1,In2_Cu=2,In3_Cu=3,In4_Cu=4,LSET=types.SimpleNamespace(AllCuMask=lambda:'all_copper'),ToMM=lambda x:x/1000000)
code=ast.parse((C/'tools/route_board.py').read_text());fn=next(n for n in code.body if isinstance(n,ast.FunctionDef) and n.name=='joint_copper');ns={'pcbnew':fake,'hig':hig,'mm':mm,'VIA_DIA':.45,'VIA_DRILL':.2,'LINK_W':.18};exec(compile(ast.Module(body=[fn],type_ignores=[]),'extracted_joint_copper','exec'),ns)
b=Board()
with contextlib.redirect_stdout(io.StringIO()):ns['joint_copper'](b)
zones=[i for i in b.items if i.kind=='zone'];records=[]
for z in zones:records.append({'polygon_mm':[[x/1e6,y/1e6] for x,y in z.poly.points],'permissions':z.properties})
expected=[[[100.1,101.05],[111.1,101.05],[111.1,103.75],[100.1,103.75]],[[111.3,101.05],[122.3,101.05],[122.3,103.75],[111.3,103.75]]]
r={'method':__doc__,'generated_item_counts':{k:sum(i.kind==k for i in b.items) for k in ('zone','track','via')},'keepouts':records,'generated_keepout_polygons_equal_native':[v['polygon_mm'] for v in records]==expected,'guards':{}}
for name,rotation,layer in [('rotated',90,0),('back_side',0,31)]:
 b=Board();b.j.rotation=rotation;b.j.layer=layer
 try:ns['joint_copper'](b);refused=False
 except SystemExit:refused=True
 r['guards'][name+'_refused_before_any_item_added']=refused and not b.items
print(json.dumps(r,indent=2))
