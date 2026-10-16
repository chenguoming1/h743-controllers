"""Read-only semantic and geometric parity checks for the isolated matched prototype."""
from pathlib import Path
import sys,json,hashlib,math,collections
R=Path(__file__).resolve().parents[1];C=R/'candidate-continuous-vx-unfinished';S=R/'candidate-compact-two-layer-unfinished';sys.path.insert(0,str(C/'tools'))
import sexpr as s,header_interface_geometry as g,make_footprints as m,design_header as d
one=lambda n,k:s.find(n,k)[0]
txt=s.text
ref=lambda f:next(txt(p[2]) for p in s.find(f,'property') if txt(p[1])=='Reference')
xy=lambda n,k:tuple(float(v) for v in one(n,k)[1:3])
bs={name:s.parse((C/path).read_text()) for name,path in [('child','hardware/header-board/nexus-header-board.kicad_pcb'),('main','hardware/nexus-style-fc.kicad_pcb')]}
old={name:s.parse((S/path).read_text()) for name,path in [('child','hardware/header-board/nexus-header-board.kicad_pcb'),('main','hardware/nexus-style-fc.kicad_pcb')]}
contract=json.loads((C/'verification/geometry-contract.json').read_text())
def edge(n):return isinstance(n,list) and n[0] in ('gr_line','gr_arc','fp_line','fp_arc') and txt(one(n,'layer')[1])=='Edge.Cuts'
def sig(n):return (n[0].split('_')[-1],*[tuple(round(v,6) for v in xy(n,k)) for k in (('start','mid','end') if n[0].endswith('arc') else ('start','end'))])
def canonical(shapes):return sorted((v[0],*[tuple(round(x,6) for x in p) for p in v[1:]]) for v in shapes)
def checkclosed(es,expected):
 graph=collections.defaultdict(list)
 for n in es:
  a,b=tuple(round(v,6) for v in xy(n,'start')),tuple(round(v,6) for v in xy(n,'end'));assert a!=b;graph[a].append(b);graph[b].append(a)
 assert all(len(v)==2 for v in graph.values())
 unseen=set(graph);components=0
 while unseen:
  components+=1;todo=[next(iter(unseen))]
  while todo:
   p=todo.pop()
   if p in unseen:unseen.remove(p);todo.extend(graph[p])
 assert components==expected,components
 return len(es)
mainjoint=next(f for f in s.find(bs['main'],'footprint') if ref(f)=='J1')
mainedges=[n for n in mainjoint if edge(n)]
assert sorted(map(sig,mainedges))==canonical(contract['main_slots']['native_local_geometry'])
childedges=[n for n in bs['child'] if edge(n)];bottom=[n for n in childedges if all(xy(n,k)[1]>=108.4-1e-6 for k in ('start','end'))]
expected=[(v[0],*[(p[0]+100,p[1]+108.4) for p in v[1:]]) for v in contract['child']['native_bottom_contour']]
assert sorted(map(sig,bottom))==canonical(expected)
assert canonical(g.tab_outline())==canonical(contract['child']['native_bottom_contour'])
assert canonical([v for c in g.SLOT_CENTERS for v in g.rounded_slot(*c)])==canonical(contract['main_slots']['native_local_geometry'])
checkclosed(childedges,1);checkclosed(mainedges,2)
def psig(p):return txt(p[1]),xy(p,'at'),xy(p,'size'),tuple(txt(v) for v in one(p,'layers')[1:])
lib=s.parse((C/'hardware/library/NexusFC.pretty/HeaderBoard_Joint.kicad_mod').read_text())
assert sorted(map(psig,s.find(mainjoint,'pad')))==sorted(map(psig,s.find(lib,'pad')))
assert sorted(map(sig,mainedges))==sorted(map(sig,[n for n in lib if edge(n)]))
records=[]
for f in s.find(bs['child'],'footprint'):
 r=ref(f);part=next(p for p in d.PARTS if p['ref']==r);px,py=part['place'][1:3]
 assert abs(xy(f,'at')[0]-(100+px))<1e-6 and abs(xy(f,'at')[1]-(108.4+py))<1e-6,(r,xy(f,'at'),part['place'])
 assert txt(f[1])==part['fp']
 for p in s.find(f,'pad'):assert txt(one(p,'net')[-1])==part['pins'][txt(p[1])]
 if r=='J1':continue
 p=one(f,'pad');fpname=txt(f[1]).split(':')[1];lf=s.parse((C/'hardware/library/NexusFC.pretty'/f'{fpname}.kicad_mod').read_text());assert psig(p)==psig(one(lf,'pad'))
 pc=next(p for p in contract['child']['pads'] if p['ref']==r);assert xy(p,'at')==tuple(pc['proposed_pad_at']);assert xy(p,'size')==tuple(pc['proposed_size'])
 x,y=xy(f,'at');a,b=xy(p,'at');w,h=xy(p,'size');box=[x+a-w/2-100,y+b-h/2-108.4,x+a+w/2-100,y+b+h/2-108.4]
 assert max(abs(v-u) for v,u in zip(box,pc['new_box']))<1e-6
 records.append({'ref':r,'box':box,'native_to_library_and_generator':True})
for name in ('main','child'):
 for typ in ('segment','arc','via','setup','general','net'):
  # Native save may normalize setup but must preserve semantic PCB power stack and track objects.
  if typ!='setup':
   if name=='child' and typ in ('segment','via'):
    a={txt(one(n,'uuid')[1]):n for n in s.find(old[name],typ)};b={txt(one(n,'uuid')[1]):n for n in s.find(bs[name],typ)}
    deleted={'52fcbd80-6632-4a6b-afda-c029bcd74a10','5e204930-1a49-4cb9-8804-772684912cce','bab4ace0-e97a-4223-b188-4f425d204e84','c7529157-fdb0-4a19-9332-597f8a0fab2b'} if typ=='segment' else {'3c9361c0-bd79-4ae1-854a-1afbcbd154c4'}
    assert set(a)-set(b)==deleted
    assert len(set(b)-set(a))==(2 if typ=='segment' else 3)
    for uid in set(a)&set(b):
     expected=a[uid]
     if typ=='segment' and txt(one(expected,'net')[-1])=='ESC' and txt(one(expected,'layer')[1])=='F.Cu':one(expected,'layer')[1]=('s','B.Cu')
     if uid=='f9db54a0-0228-48db-8cfe-34254eb9cbaa':one(expected,'layer')[1]=('s','F.Cu')
     if uid=='2dc968c3-652e-419f-bcaf-cdf4575152a0':one(expected,'start')[1:]=['115.1','104.95'];one(expected,'width')[1]='0.6'
     assert expected==b[uid],uid
    for uid in set(b)-set(a):
     n=b[uid];assert txt(one(n,'net')[-1])=='VX'
     if typ=='via':assert float(one(n,'size')[1])==.6 and float(one(n,'drill')[1])==.3
     else:assert float(one(n,'width')[1])==.6 and txt(one(n,'layer')[1])=='B.Cu'
   else:assert s.find(bs[name],typ)==s.find(old[name],typ),(name,typ)
 for f in s.find(bs[name],'footprint'):
  of=next(v for v in s.find(old[name],'footprint') if ref(v)==ref(f))
  assert xy(f,'at')==xy(of,'at')
  for p,op in zip(s.find(f,'pad'),s.find(of,'pad')):
   for k in ('uuid','net','layers'):assert s.find(p,k)==s.find(op,k),(name,ref(f),k)
   assert p[1:4]==op[1:4]
   if name=='main' or ref(f)=='J1':assert psig(p)==psig(op)
 if name=='main':assert [n for n in bs[name] if edge(n)]==[n for n in old[name] if edge(n)]
 for ext in ('kicad_sch',):
  path='hardware/header-board/nexus-header-board.'+ext if name=='child' else 'hardware/nexus-style-fc.'+ext
  assert (C/path).read_bytes()==(S/path).read_bytes()
stack=one(one(bs['child'],'setup'),'stackup');layers=[n for n in s.find(stack,'layer') if s.find(n,'thickness')];assert abs(sum(float(one(n,'thickness')[1]) for n in layers)-1.6)<1e-9
assert [float(one(n,'thickness')[1]) for n in layers if txt(n[1]) in ('F.Cu','B.Cu')]==[.07,.07]
report={'status':'PASS: native/generated/library/schematic geometry and pin parity; not physical qualification','child_outline_segments':len(childedges),'main_slot_segments':len(mainedges),'all11_joint_contact_geometry':records,'source_contact_pinout_preserved':True,'reviewed_ESC_and_GND_layer_reroute_only':True,'main_body_unchanged':True,'child_stack_nominal_sum_mm':1.6,'child_copper_nominal_um_each':70,'physical_clearance_requires_actual_profile_inspection':True,'hashes':{str(p.relative_to(C)):hashlib.sha256(p.read_bytes()).hexdigest() for p in C.rglob('*') if p.is_file() and ('hardware' in p.parts or 'tools' in p.parts) and '__pycache__' not in p.parts}}
(C/'verification/semantic-parity.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k not in ('hashes','all11_joint_contact_geometry')},indent=2))
