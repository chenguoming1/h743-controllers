"""Hand-drafted circuit presentation; original component identities retained."""
import copy, math
import sexpr as sx
G=1.27
class Draft:
 def __init__(self,sch,design,project,parts=None):
  from gen_schematic import uid,S,glabel
  self.uid,self.S,self.glabel=uid,S,glabel;self.project=project;self.sch=sch;self.design=design
  self.parts={p['ref']:p for p in (design.PARTS if parts is None else parts)};self.defs={sx.text(n[1]):n for n in sx.find(sch,'lib_symbols')[0][1:]};self.orig={sx.text(sx.find(n,'property')[0][2]):n for n in sx.find(sch,'symbol')};self.items=[];self.pins={};self.used=set();self.connected=set();self.count=0;self.offset=(0,0);self.grounds={}
  from gen_schematic import pinned_stock_symbols
  sx.find(sch,'lib_symbols')[0].append(copy.deepcopy(pinned_stock_symbols()['power:GND']))
 def snap(self,x):return round(round(x/G)*G,4)
 def xy(self,p):return tuple(self.snap(a+b) for a,b in zip(p,self.offset))
 def id(self,kind):self.count+=1;return self.uid(self.project,'draft',kind,self.count)
 def text(self,t,x,y,size=1.5,bold=False):
  f=['font',['size',size,size]]+([['bold','yes']] if bold else [])
  self.items.append(['text',self.S(t),['exclude_from_sim','no'],['at',*self.xy((x,y)),0],['effects',f,['justify','left']],['uuid',self.id('text')]])
 def panel(self,title,x,y,w,h,note):
  self.offset=(0,0);self.items.append(['polyline',['pts',*[['xy',*self.xy(p)] for p in [(x,y),(x+w,y),(x+w,y+h),(x,y+h),(x,y)]]],['stroke',['width',0.254],['type','dash']],['fill',['type','none']],['uuid',self.id('panel')]])
  self.offset=(x,y);self.text(title,5,7,2.2,True);self.text(note,5,14,1.4)
 def place(self,ref,x,y,rot=0):
  assert ref not in self.used,ref
  self.used.add(ref);n=copy.deepcopy(self.orig[ref]);x,y=self.xy((x,y));sx.find(n,'at')[0][1:]=[x,y,rot];sym=self.defs[sx.text(sx.find(n,'lib_id')[0][1])];pp=sx.symbol_pins(sym);passive=ref[0] in 'RCL' and len(pp)==2
  xa,ya,xb,yb=sx.symbol_bbox(sym);rad=math.radians(rot)
  top=min(y-px*math.sin(rad)-py*math.cos(rad) for px in (xa,xb) for py in (ya,yb))
  points=[(px*math.cos(rad)-py*math.sin(rad),-px*math.sin(rad)-py*math.cos(rad)) for px,py,*_ in pp.values()]
  vertical=len(points)==2 and abs(points[0][0]-points[1][0])<0.01
  for prop in sx.find(n,'property'):
   a=sx.find(prop,'at')[0];a[1:]=[x,y,rot%180]
   if sx.text(prop[1]) in ('Reference','Value'):
    isref=sx.text(prop[1])=='Reference';eff=sx.find(prop,'effects')[0];eff[:]=[e for e in eff if not isinstance(e,list) or e[0]!='justify']
    if vertical:
     a[1:]=[self.snap(x+4),self.snap(y+(-1.27 if isref else 1.27)),rot%180];eff.append(['justify','right' if rot==180 else 'left'])
    else:a[1:]=[x,self.snap(top-(5 if isref else 2)),rot%180]
  self.items.append(n)
  for num,(px,py,ang,length,name) in pp.items():
   r=math.radians(rot);pt=(self.snap(x+px*math.cos(r)-py*math.sin(r)),self.snap(y-px*math.sin(r)-py*math.cos(r)));self.pins[ref,num]=(pt,(ang+rot)%360)
   net=self.net(ref,num)
   if net is None:self.items.append(['no_connect',['at',*pt],['uuid',self.uid(self.project,'nc',ref,num)]]);self.connected.add((ref,num))
  return n
 def net(self,ref,num):return self.parts[ref]['pins'][str(num)] if ref in self.parts else self.design.PWR_FLAGS[int(ref[-2:])-1]
 def p(self,ref,num):
  key=(ref,str(num));self.connected.add(key);a=self.pins[key][0];return tuple(self.snap(v-o) for v,o in zip(a,self.offset))
 def wire(self,*points):
  for a,b in zip(points,points[1:]):
   a,b=self.xy(a),self.xy(b)
   if a==b:continue
   assert a[0]==b[0] or a[1]==b[1],(a,b)
   self.items.append(['wire',['pts',['xy',*a],['xy',*b]],['stroke',['width',0],['type','default']],['uuid',self.id('wire')]])
 def dot(self,p):self.items.append(['junction',['at',*self.xy(p)],['diameter',0],['color',0,0,0,0],['uuid',self.id('dot')]])
 def label(self,net,p,angle=0):
  if net=='GND':
   q=self.xy(p)
   if q in self.grounds:return
   gr=180 if angle==90 else 0; sign=-1 if gr else 1
   ref=f'#PWR{len(self.grounds)+1:03d}';self.grounds[q]=ref;root=sx.find(self.sch,'uuid')[0][1]
   props=[]
   for name,value,dy,hide in [('Reference',ref,6.35,True),('Value','GND',3.81,False),('Footprint','',0,True),('Datasheet','',0,True)]:
    eff=['effects',['font',['size',1.27,1.27]]]+([['hide','yes']] if hide else [])
    props.append(['property',self.S(name),self.S(value),['at',q[0],self.snap(q[1]+sign*dy),0],eff])
   self.items.append(['symbol',['lib_id',self.S('power:GND')],['at',*q,gr],['unit',1],['exclude_from_sim','no'],['in_bom','no'],['on_board','no'],['dnp','no'],['uuid',self.uid(self.project,'draft-ground',ref)],*props,['pin',self.S('1'),['uuid',self.uid(self.project,'draft-ground-pin',ref)]],['instances',['project',self.S(self.project),['path',self.S('/'+sx.text(root)),['reference',self.S(ref)],['unit',1]]]]]);return
  if angle in (90,270):angle=0
  self.items.append(self.glabel(net,*self.xy(p),angle,'left' if angle==0 else 'right',self.id('label')))
 def stub(self,ref,num,length=7.62):
  p=self.p(ref,num);ang=self.pins[ref,str(num)][1];r=math.radians(ang+180);q=(self.snap(p[0]+round(math.cos(r))*length),self.snap(p[1]-round(math.sin(r))*length));self.wire(p,q);self.label(self.net(ref,num),q,int((ang+180)%360))
 def ground(self,ref,num,dx=0,drop=7.62):
  p=self.p(ref,num);q=(self.snap(p[0]+dx),p[1]);b=(q[0],self.snap(q[1]+drop));self.wire(p,q,b);self.label('GND',b,270)
 def finish(self):
  self.offset=(0,0)
  for ref,num in self.pins:
   if (ref,num) not in self.connected:self.stub(ref,num)
  assert self.used==set(self.orig),(set(self.orig)-self.used)
  keep=[n for n in self.sch if not isinstance(n,list) or n[0] not in ('symbol','wire','global_label','no_connect','text','junction','polyline')]
  return keep+self.items

def arrange(sch,design,project,parts=None):
 d=Draft(sch,design,project,parts=parts)
 d.text('NEXUS-STYLE FLIGHT CONTROLLER  |  CIRCUIT SCHEMATIC',20,20,3,True)
 d.text('POWER  /  COMPUTE + SENSORS  /  INTERFACES. Named boundaries connect between functional circuits.',20,28,1.8)
 d.text('UNFINISHED PCB CHECKPOINT - NOT RELEASED FOR FABRICATION. X = intentionally unconnected pin.',20,35,1.6)
 import draft_power,draft_compute,draft_interfaces
 for module in (draft_power,draft_compute,draft_interfaces):module.draw(d)
 return d.finish()
