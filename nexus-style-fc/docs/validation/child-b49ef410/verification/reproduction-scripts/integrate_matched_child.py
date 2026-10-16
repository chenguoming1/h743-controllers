"""Guarded isolated child integration; preserves compact power prototype and stage10.
9.3mm physical tabs, unchanged electrical X registration, pad tops0.8mm.
Only writes the explicitly named unfinished candidate, no source/external edits.
"""
from pathlib import Path
import sys,hashlib,json,uuid
R=Path(__file__).resolve().parents[1]; S=R/'candidate-compact-two-layer-unfinished'; C=R/'candidate-compact-matched-fit-unfinished'
sys.path.insert(0,str(C/'tools'));import sexpr as sx
P=C/'hardware/header-board/nexus-header-board.kicad_pcb';src=S/'hardware/header-board/nexus-header-board.kicad_pcb'
assert hashlib.sha256(src.read_bytes()).hexdigest()=='31340ed282ebbbea055806e7202a78dc51ebfc305f4dc800054c1522ae7d7357'
geo=C/'tools/header_interface_geometry.py';t=geo.read_text();t=t.replace('TABS = ((1.4, 9.8), (12.6, 21.0))','TABS = ((0.95, 10.25), (12.15, 21.45))\n# Contact registration stays at the routed baseline, independently of enlarged tabs.\nCONTACT_TABS = ((1.4, 9.8), (12.6, 21.0))\nCHILD_PAD_TOP, CHILD_PAD_BOTTOM = 0.8, 2.346')
t=t.replace('= 10.1, 2.2, 0.5, 0.5','= 9.8, 2.1, 0.5, 0.5').replace('zip(TABS,INNER)','zip(CONTACT_TABS,INNER)')
t=t.replace('SLOT_ROUTE_KEEPOUT_X, SLOT_ROUTE_KEEPOUT_Y = 0.45, 0.3','SLOT_ROUTE_KEEPOUT_X, SLOT_ROUTE_KEEPOUT_Y = 0.60, 0.35')
a=t.index('def tab_outline():');b=t.index('\ndef kicad_shape(',a)
t=t[:a]+'''def tab_outline():
    """Continuous physical contour; 270-degree R0.5 relief at each root.
    Split arcs keep explicit native start/mid/end and avoid ambiguous major arcs.
    """
    result=[];x=0.;r=ROOT_RADIUS;d=r/sqrt(2)
    for a,b in TABS:
        result += [('line',(x,0),(a-r,0)),
                   ('arc',(a-r,0),(a,-r),(a+r,0)),
                   ('arc',(a+r,0),(a+d,d),(a,r)),
                   ('line',(a,r),(a,TAB_LENGTH)),
                   ('line',(a,TAB_LENGTH),(b,TAB_LENGTH)),
                   ('line',(b,TAB_LENGTH),(b,r)),
                   ('arc',(b,r),(b-d,d),(b-r,0)),
                   ('arc',(b-r,0),(b,-r),(b+r,0))]
        x=b+r
    return result+[('line',(x,0),(WIDTH,0))]
''' + t[b:]
t=t.replace('UNFINISHED root-aware header candidate','UNFINISHED matched-pair compact header candidate')
geo.write_text(t)
mf=C/'tools/make_footprints.py';t=mf.read_text();t=t.replace('PAD_ABOVE = 0.0','PAD_ABOVE = -hig.CHILD_PAD_TOP').replace('STRIP_TOP = 0.0','STRIP_TOP = -hig.CHILD_PAD_TOP')
t=t.replace('widths = sorted({round(b - a - 2 * STRIP_INSET, 3) for a, b in BARS_CHILD})','widths = [hig.CHILD_STRIP_WIDTH]  # Electrical strip unchanged when physical tabs widen')
t=t.replace('2 routed 10.1 x 2.2 mm R0.5','2 routed 9.8 x 2.1 mm R0.5');mf.write_text(t)
dh=C/'tools/design_header.py';t=dh.read_text().replace('w = round(b - a - 2 * mf.STRIP_INSET, 3)','w = mf.hig.CHILD_STRIP_WIDTH  # Keep matched electrical strip registration');dh.write_text(t)
import header_interface_geometry as g
one=lambda n,k:sx.find(n,k)[0]
ref=lambda f:next(sx.text(p[2]) for p in sx.find(f,'property') if sx.text(p[1])=='Reference')
b=sx.parse(src.read_text());old=sx.parse(src.read_text());oldedges=[];kept=[]
for n in b:
 if isinstance(n,list) and n[0] in ('gr_line','gr_arc') and sx.text(one(n,'layer')[1])=='Edge.Cuts' and all(float(one(n,k)[2])>=108.4-1e-6 for k in ('start','end')):
  oldedges.append(n)
 else:kept.append(n)
assert len(oldedges)==13,len(oldedges)
for i,shape in enumerate(g.tab_outline()):kept.append(sx.parse(g.kicad_shape(shape,'gr',(100,108.4),str(uuid.uuid5(uuid.UUID('76fc26ee-25f2-483d-9fd7-5600b86b9fd9'),f'child-bottom-{i}')))))
b=kept;changes=[]
for f in sx.find(b,'footprint'):
 if ref(f)=='J1':continue
 pads=sx.find(f,'pad');assert len(pads)==1
 p=pads[0];assert [float(v) for v in one(p,'at')[1:3]]==[0,1.173]
 assert abs(float(one(p,'size')[2])-2.346)<1e-8
 one(p,'at')[2]='1.573';one(p,'size')[2]='1.546'
 changes.append({'ref':ref(f),'pad_top':.8,'pad_bottom':2.346,'width':float(one(p,'size')[1]),'net':sx.text(one(p,'net')[-1])})
 if sx.find(f,'descr'):one(f,'descr')[1]=('s','UNFINISHED matched-pair joint contact; top0.8 bottom2.346mm; X registration unchanged')
for z in sx.find(b,'zone'):z[:]=[n for n in z if not(isinstance(n,list) and n[0] in ('filled_polygon','fill_segments'))]
for typ in ('segment','via','setup','general','net'):assert sx.find(b,typ)==sx.find(old,typ),typ
assert next(f for f in sx.find(b,'footprint') if ref(f)=='J1')==next(f for f in sx.find(old,'footprint') if ref(f)=='J1')
P.write_text(sx.dump(b)+'\n')
# Generate only the affected child footprint libraries and matched main-joint definition.
import make_footprints as m
for name,fn,args in [('ChildBoard_TabPad_Sig',m.fp_tabpad,('ChildBoard_TabPad_Sig',1.2)),('ChildBoard_TabPad_Pwr',m.fp_tabpad,('ChildBoard_TabPad_Pwr',1.6)),('ChildBoard_TabStrip_W7.892',m.fp_tabstrip,('ChildBoard_TabStrip_W7.892',7.892)),('HeaderBoard_Joint',m.fp_joint,())]:
 lines=[];fn(lines,*args);m.write(name,lines)
# Native helper's initial rules must agree with the selected manufacturer option.
p=C/'tools/build_header_board.py';t=p.read_text().replace('nc.SetClearance(b.mm(0.15))','nc.SetClearance(b.mm(0.16))').replace('nc.SetTrackWidth(b.mm(0.25))','nc.SetTrackWidth(b.mm(0.20))');p.write_text(t)
(C/'verification/child-fit-transaction.json').write_text(json.dumps({'status':'UNFINISHED; refill/native validation required','source_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'pre_refill_sha256':hashlib.sha256(P.read_bytes()).hexdigest(),'changed_pads':changes,'physical_tabs':g.TABS,'native_bottom_segments':len(g.tab_outline()),'electrical_contact_tabs':g.CONTACT_TABS,'preserved':['all tracks and vias','all header pins/polarity/locations','all pad X/net/pin/UUID','copper stack and design rules','schematic'],'generator_updates':['header_interface_geometry.py','make_footprints.py','design_header.py','build_header_board.py']},indent=2)+'\n')
print(P)
