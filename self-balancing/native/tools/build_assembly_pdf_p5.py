#!/usr/bin/python3
"""Read-only native CAD to dimensioned assembly drawing and technical QA manifest."""
import os
os.environ.setdefault('KICAD_CONFIG_HOME','/tmp/controller-r3-kicad')
import argparse,collections,csv,datetime,hashlib,json,math,pathlib
import pcbnew as pcb
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4,landscape
from reportlab.lib.units import mm
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph,Table,TableStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

for name,file in [('DrawingSans','DejaVuSans.ttf'),('DrawingSans-Bold','DejaVuSans-Bold.ttf')]:pdfmetrics.registerFont(TTFont(name,'/usr/share/fonts/truetype/dejavu/'+file))
pdfmetrics.registerFontFamily('DrawingSans',normal='DrawingSans',bold='DrawingSans-Bold',italic='DrawingSans',boldItalic='DrawingSans-Bold')
ap=argparse.ArgumentParser();ap.add_argument('--board',type=pathlib.Path,required=True);ap.add_argument('--project',type=pathlib.Path,required=True);ap.add_argument('--out',type=pathlib.Path,required=True);ap.add_argument('--revision',default='Stage 39');ap.add_argument('--frozen',action='store_true');a=ap.parse_args();a.out.mkdir(parents=True,exist_ok=True)
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def xy(pt):return(pcb.ToMM(pt.x),pcb.ToMM(pt.y))
sourcehash=sha(a.board);b=pcb.LoadBoard(str(a.board));fps={f.GetReference():f for f in b.GetFootprints()};parts=json.loads((a.project/'review/design-netmap.json').read_text());fitted={q['Reference']:q for q in parts if q.get('LCSC') and not q.get('DNP')};assert len(fps)==151 and len(fitted)==79 and b.GetCopperLayerCount()==6;assert xy(b.GetDesignSettings().GetAuxOrigin())==(0,38)
for r,q in fitted.items():
 for field,key in [('LCSC','LCSC'),('Manufacturer_Part_Number','MPN')]:assert fps[r].GetFieldByName(field).GetText()==q[key],r+' identity drift'
def pose(f):return(*xy(f.GetPosition()),f.GetOrientationDegrees()%360,'Bottom' if f.GetLayer()==pcb.B_Cu else 'Top')
counts=collections.Counter(pose(fps[r])[3] for r in fitted)
prior=pathlib.Path(__file__).parent/'fitted-79-native-placements.csv';pose_diffs=[]
if prior.exists():
 for q in csv.DictReader(prior.open()):
  now=pose(fps[q['Reference']]);old=(float(q['Native_X_mm']),float(q['Native_Y_mm']),float(q['Native_angle_deg']),q['Side'])
  if now!=old:pose_diffs.append({'reference':q['Reference'],'prior':old,'current':now})
profile=json.loads((a.project/'review/manufacturing-profile.json').read_text());assert profile['stack_id']=='JLC06161H-3313'
critical=['U1','U2','U3','U4','U6','U8','U10','U11','U12','U13','Q1','Q2','D4','J2','J3','J4','J5'];critset=set(critical)
INK=colors.HexColor('#173d58');BLACK=colors.HexColor('#151d29');GRAY=colors.HexColor('#788493');LIGHT=colors.HexColor('#eef1f4');PAD=colors.HexColor('#dcc78f');PIN=colors.HexColor('#bd3338');FAB=colors.HexColor('#bfc7ce');SILK=colors.HexColor('#8b782d');BLUE=colors.HexColor('#365e82')
W,H=landscape(A4);output=a.out/('controller-r3s-assembly-manufacturing.pdf' if a.frozen else 'controller-r3s-assembly-manufacturing-PROVISIONAL.pdf');c=canvas.Canvas(str(output),pagesize=(W,H),pageCompression=1);date=datetime.datetime.now(datetime.timezone.utc).strftime('D:%Y%m%d%H%M%SZ');c.setDateFormatter(lambda *args:date);c.setTitle('Controller R3-S6-P5 assembly and manufacturing drawing');c.setAuthor('Controller engineering review');c.setSubject('Six layer native assembly drawing; provisional routing status' if not a.frozen else 'R3-S6-P5; ASSEMBLY NOT CLEARED; supplier model alignment and hardware qualification pending')
base=ParagraphStyle('Base',fontName='DrawingSans',fontSize=9,leading=12.2,textColor=BLACK);small=ParagraphStyle('Small',parent=base,fontSize=7.7,leading=9.8);cell=ParagraphStyle('Cell',parent=base,fontSize=7.4,leading=9);hc=ParagraphStyle('HeaderCell',parent=cell,fontName='DrawingSans-Bold',textColor=colors.white)
page=0;warnings=[]
def text(s,x,y,size=9,bold=False,color=BLACK,align='left'):
 c.setFillColor(color);c.setFont('DrawingSans-Bold' if bold else 'DrawingSans',size);getattr(c,{'left':'drawString','center':'drawCentredString','right':'drawRightString'}[align])(x*mm,y*mm,s)
def para(s,x,y,width,style=base):
 q=Paragraph(s,style);w,h=q.wrap(width*mm,1000);q.drawOn(c,x*mm,y*mm-h);return y-h/mm

def header(title,subtitle):
 global page
 page+=1;text('CONTROLLER R3S',14,199,9,True,INK);text(title,14,190,17,True);text(subtitle,14,183.5,9,color=GRAY)
 status='PROVISIONAL - ROUTING IN PROGRESS - NOT FOR FABRICATION' if not a.frozen else 'R3-S6-P5 - ASSEMBLY NOT CLEARED';text(status,283,199,8.2,True,PIN,'right')
 c.setStrokeColor(colors.HexColor('#cfd5da'));c.setLineWidth(.4);c.line(14*mm,15*mm,283*mm,15*mm);text(a.revision+' | Native source SHA-256 '+sourcehash,14,10,6.7,color=GRAY);text(f'{page} / 6',283,10,7.5,color=GRAY,align='right')

def polygon(points,tr,fill,stroke=None):
 if not points:return
 q=c.beginPath();x,y=tr(points[0]);q.moveTo(x,y)
 for pt in points[1:]:x,y=tr(pt);q.lineTo(x,y)
 q.close();c.setFillColor(fill);c.setStrokeColor(stroke or fill);c.setLineWidth(.1*mm);c.drawPath(q,stroke=bool(stroke),fill=1)
def contours(poly):
 for i in range(poly.OutlineCount()):
  line=poly.Outline(i);outer=[xy(line.CPoint(j)) for j in range(line.PointCount())];holes=[]
  for k in range(poly.HoleCount(i)):
   hole=poly.Hole(i,k);holes.append([xy(hole.CPoint(j)) for j in range(hole.PointCount())])
  yield outer,holes

def fp(ref,side,tr,labels=True,numbers=False):
 f=fps[ref];body=pcb.B_Fab if side=='Bottom' else pcb.F_Fab;silk=pcb.B_SilkS if side=='Bottom' else pcb.F_SilkS;cu=pcb.B_Cu if side=='Bottom' else pcb.F_Cu
 for layer,color in [(body,FAB),(silk,SILK)]:
  for g in f.GraphicalItems():
   if g.GetClass()!='PCB_SHAPE' or g.GetLayer()!=layer:continue
   poly=pcb.SHAPE_POLY_SET();g.TransformShapeToPolygon(poly,layer,0,1000,pcb.ERROR_OUTSIDE)
   for outer,holes in contours(poly):polygon(outer,tr,color)
 # Co-located USB A1/B12 must leave the highlighted A1 visible.
 for pad in sorted(f.Pads(),key=lambda p:p.GetNumber()==('A1' if ref=='J2' else '1')):
  if not pad.IsOnLayer(cu):continue
  pin1=ref in critset and pad.GetNumber()==('A1' if ref=='J2' else '1');npth=pad.GetAttribute()==pcb.PAD_ATTRIB_NPTH;poly=pcb.SHAPE_POLY_SET();pad.TransformShapeToPolygon(poly,cu,0,1000,pcb.ERROR_OUTSIDE)
  for outer,holes in contours(poly):
   polygon(outer,tr,colors.white if npth else PIN if pin1 else PAD,GRAY if npth else None)
   for hole in holes:polygon(hole,tr,colors.white)
  if any(xy(pad.GetDrillSize())):
   poly=pcb.SHAPE_POLY_SET();pad.TransformHoleToPolygon(poly,0,1000,pcb.ERROR_OUTSIDE)
   for outer,holes in contours(poly):polygon(outer,tr,colors.white,GRAY)
  if numbers and pad.GetNumber() and not(ref=='J2' and pad.GetNumber().startswith('B')):
   x,y=tr(xy(pad.GetPosition()));text(pad.GetNumber(),x/mm,y/mm-.85,6.3,True,colors.white if pin1 else BLACK,'center')
 if labels and ref in fitted:
  x,y=xy(f.GetPosition());x+=-.45 if ref in ['J3','J4'] else .45 if ref=='J5' else 0;x,y=tr((x,y));size=7 if ref[0] in ['C','R'] else 8;width=pdfmetrics.stringWidth(ref,'DrawingSans-Bold',size);c.setFillColor(colors.white);c.rect(x-width/2-1,y-3.6,width+2,size+1,fill=1,stroke=0);text(ref,x/mm,(y-1.6)/mm,size,True,BLACK,'center')

def arrow(x1,y1,x2,y2):
 c.setStrokeColor(BLUE);c.setFillColor(BLUE);c.setLineWidth(.22*mm);c.line(x1*mm,y1*mm,x2*mm,y2*mm);angle=math.atan2(y2-y1,x2-x1);q=c.beginPath();q.moveTo(x2*mm,y2*mm)
 for off in [2.7,-2.7]:q.lineTo((x2+1.5*math.cos(angle+off))*mm,(y2+1.5*math.sin(angle+off))*mm)
 q.close();c.drawPath(q,stroke=0,fill=1)
def dimh(x1,x2,y,label):
 c.setLineWidth(.15*mm);c.setStrokeColor(GRAY);c.line(x1*mm,y*mm,x2*mm,y*mm)
 for x in [x1,x2]:c.line(x*mm,(y-1.7)*mm,x*mm,(y+1.7)*mm)
 text(label,(x1+x2)/2,y+1.8,7.5,align='center')
def dimv(x,y1,y2,label):
 c.setLineWidth(.15*mm);c.setStrokeColor(GRAY);c.line(x*mm,y1*mm,x*mm,y2*mm)
 for y in [y1,y2]:c.line((x-1.7)*mm,y*mm,(x+1.7)*mm,y*mm)
 c.saveState();c.translate((x-2.2)*mm,(y1+y2)/2*mm);c.rotate(90);c.setFont('DrawingSans',7.5);c.setFillColor(BLACK);c.drawCentredString(0,0,label);c.restoreState()
def table(rows,x,y,widths,height=5,font=7.5):
 q=Table(rows,colWidths=[v*mm for v in widths],rowHeights=[height*mm]*len(rows));q.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),INK),('TEXTCOLOR',(0,0),(-1,0),colors.white),('FONTNAME',(0,0),(-1,0),'DrawingSans-Bold'),('FONTNAME',(0,1),(-1,-1),'DrawingSans'),('FONTSIZE',(0,0),(-1,-1),font),('GRID',(0,0),(-1,-1),.3,colors.HexColor('#d9d9d9')),('VALIGN',(0,0),(-1,-1),'MIDDLE'),('LEFTPADDING',(0,0),(-1,-1),4),('RIGHTPADDING',(0,0),(-1,-1),3)]));w,h=q.wrap(0,0);q.drawOn(c,x*mm,y*mm-h);return y-h/mm

def view(side):
 rear=side=='Bottom';header('Rear assembly view' if rear else 'Front assembly view','Component-side view | 4:1 at 100% print | Dimensions in mm | Component envelopes are native Fab geometry');X,Y,S=20,24,4
 def tr(pt):x,y=pt;return((X+(38-x if rear else x)*S)*mm,(Y+(38-y)*S)*mm)
 c.setFillColor(colors.HexColor('#fafbfc'));c.setStrokeColor(BLACK);c.setLineWidth(.35*mm);c.roundRect(X*mm,Y*mm,152*mm,152*mm,8*mm,stroke=1,fill=1)
 for ref,f in fps.items():
  if ref.startswith('H') or (ref not in fitted and pose(f)[3]==side):fp(ref,side,tr,labels=False)
 for ref in fitted:
  if pose(fps[ref])[3]==side:fp(ref,side,tr)
 dimh(X,X+152,Y-5,'38.00');dimv(X-6,Y,Y+152,'38.00');dimh(X+15,X+137,Y+137,'30.50 mount pitch')
 x,y=tr((0,38));c.setStrokeColor(BLUE);c.setLineWidth(.25*mm);c.line(x-3*mm,y,x+3*mm,y);c.line(x,y-3*mm,x,y+3*mm);text('A',x/mm+(-3 if rear else 3),y/mm+3,9,True,BLUE,'right' if rear else 'left')
 c.setStrokeColor(BLACK);c.setLineWidth(.7*mm);c.line(193*mm,28*mm,213*mm,28*mm);text('5 mm board length',203,23,7.5,align='center')
 x,y=191,173;y=para(f'<b>{counts[side]} '+('bottom-side' if rear else 'top-side')+' fitted parts</b>',x,y,91)-3;y=para('Red lands identify pin 1, A1 or the diode cathode. Gold shows component lands; grey shows Fab outlines; ochre shows native silk. Reference text is an assembly overlay.',x,y,91)-4
 if rear:
  notes=['<b>Rear is mirrored for human inspection</b><br/>X_view = 38 - X_native<br/>Y_view = Y_native<br/>North stays at the top. Turn the board about a vertical axis to obtain this view.','<b>Do not copy this mirror into CPL</b><br/>The native audit uses X = X_native and Y = 38 - Y_native on both faces. Datum A therefore appears at the lower-right in this rear view.','U11 pin 1 is upper-left at native 180 degrees. Q2 Gate1 is lower-left at native 90 degrees; its custom footprint has no silk pin-1 cue. J3/J4 mouths face right here; J5 faces left.']
 else:
  notes=['<b>Datum A</b><br/>Native CAD (0,38) = CPL (0,0), the virtual outline bounding corner. CPL X points right and CPL Y points up. The datum is common to Gerbers, drills and both placement sides.','38 x 38 board with 2 mm corner radii, four diameter 2.20 mm NPTH mounts and 30.5 x 30.5 mm mount spacing. Mounts are product mounting holes, not approved assembly tooling holes.','J2 mouth faces the native east edge. Four plated shell slots require explicit solder-process coverage. All 67 wire pads are PCB features, excluded from the 79-part assembly BOM/CPL.']
 for note in notes:y=para(note,x,y,91)-4
 y=para('<b>Viewing limits</b><br/>Routing is omitted from these assembly views. Stencil, fabrication, cable fit and supplier placement approval remain separate checks. ASSEMBLY NOT CLEARED: residual supplier model/process findings remain. These views use native poses; page 6 records the supplier CPL corrections.',x,y,91)
 if y<40:warnings.append('Page '+str(page)+' notes near scale bar')
 c.showPage()

view('Top');view('Bottom')
header('Side socket pin numbering','Rear component-side views | 7:1 at 100% print | Numbers are PCB pad numbers, not an unqualified mating-cable convention')
for idx,ref in enumerate(['J3','J4','J5']):
 f=fps[ref];cx,cy=xy(f.GetPosition());bodyx=cx+(-.45 if ref in ['J3','J4'] else .45);center=[52,149,246][idx];Y=127;S=7
 def tr(pt):x,y=pt;return((center-(x-bodyx)*S)*mm,(Y-(y-cy)*S)*mm)
 fp(ref,'Bottom',tr,labels=False,numbers=True);text(ref+'  '+{'J3':'MOTOR 6-wire','J4':'External SPI sensor','J5':'GPS UART4'}[ref],center,174,11,True,align='center');text(fitted[ref]['MPN'],center,168,7.8,color=GRAY,align='center');sign=1 if ref in ['J3','J4'] else -1;arrow(center+sign*20,Y,center+sign*31,Y);text('MOUTH',center+sign*28,Y-5,7.2,True,BLUE,'center');x,y=tr((cx,cy));c.setStrokeColor(BLUE);c.line(x-2*mm,y,x+2*mm,y);c.line(x,y-2*mm,x,y+2*mm)
 rows=[['Pad','Signal']]
 for pad in sorted([p0 for p0 in f.Pads() if p0.GetNumber().isdigit()],key=lambda q:int(q.GetNumber())):rows.append([pad.GetNumber(),pad.GetNetname().rsplit('/',1)[-1]])
 rows.append(['MP','GND shell lands']);table(rows,center-39.5,80,[11,68])
para('Blue crosses mark native footprint anchors. Each socket body centre is offset 0.45 mm from its anchor. The native audit retains these anchors; the supplier CPL applies the user-provided corrections listed on page 6. J3 cavity numbering, housing/contact/wire compatibility and its fixture remain unqualified; the JST mounting-surface numbering evidence applies to J4/J5 only.',14,28,269,small);c.showPage()

header('Placement datum and pin one reference','All coordinates below are native top-plan coordinates or the common CPL frame | Never use rear-view X as CPL X')
y=para('<b>Common file frame:</b> native datum (0,38) mm; CPL X = native X and CPL Y = 38 - native Y. Bottom is side metadata; X is never negated. Angles below are native KiCad angles modulo 360. This table documents the native geometry; page 6 records the different user-supplied supplier angles and pickup offset. A supplier preview mark is not a universal guarantee of pin 1.',14,174,269)-5
rows=[['Ref','Exact manufacturer part','Side','Angle','Native anchor X,Y','Native audit CPL X,Y','Pin 1 / A1 native X,Y','Datum net']]
for r in critical:
 f=fps[r];x,y0,angle,side=pose(f);pad=next(p0 for p0 in f.Pads() if p0.GetNumber()==('A1' if r=='J2' else '1'));px,py=xy(pad.GetPosition());net=pad.GetNetname().rsplit('/',1)[-1];net='NC (PE2)' if net.startswith('unconnected-') else net;rows.append([r,fitted[r]['MPN'],side,f'{angle:g}',f'{x:g}, {y0:g}',f'{x:g}, {38-y0:g}',f'{px:g}, {py:g}',net])
widths=[10,49,16,14,42,41,48,49];widths=[v*269/sum(widths)*mm for v in widths];data=[[Paragraph(str(v),hc if i==0 else cell) for v in row] for i,row in enumerate(rows)];tab=Table(data,colWidths=widths,rowHeights=[9*mm]+[5.8*mm]*17);tab.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),INK),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,LIGHT]),('GRID',(0,0),(-1,-1),.3,colors.HexColor('#d9d9d9')),('VALIGN',(0,0),(-1,-1),'MIDDLE'),('LEFTPADDING',(0,0),(-1,-1),4),('RIGHTPADDING',(0,0),(-1,-1),3)]));w,h=tab.wrap(0,0);tab.drawOn(c,14*mm,y*mm-h);y-=h/mm+6;para('<b>Example:</b> U11 bottom anchor is native (20.55,20.375), so CPL is (20.55,17.625). Its mirrored rear-view anchor appears at X_view = 17.45. That 17.45 is a drawing coordinate only. U8 has no silk pin-1 cue; use its Fab cue and this table. Q2 DMN2310UW-7 has no dedicated silk/Fab pin-1 marker: Gate1 is native (19.4,27.375), lower-left in the rear component view; Source2 is GND and Drain3 is USB_SWITCH_ON. Use the red lands and this table in supplier orientation review.',14,y,269);c.showPage()

header('Six layer stack and assembly process','R3-S6-P5 | JLC06161H-3313 | ASSEMBLY NOT CLEARED: supplier placement alignment pending')
rows=[['Layer / dielectric','Role or material','Thickness mm'],['L1  F.Cu','Signals / components','0.0350'],['L1-L2','3313 prepreg, Dk 4.1','0.0994'],['L2  In1.Cu','GND, front reference','0.0152'],['L2-L3','FR4 core, Dk 4.6','0.5500'],['L3  In2.Cu','Signals / power','0.0152'],['L3-L4','2116 prepreg, Dk 4.16','0.1088'],['L4  In3.Cu','GND, L3 reference','0.0152'],['L4-L5','FR4 core, Dk 4.6','0.5500'],['L5  In4.Cu','GND, rear reference','0.0152'],['L5-L6','3313 prepreg, Dk 4.1','0.0994'],['L6  B.Cu','Signals / components','0.0350']]
assert [float(row[2]) for row in rows[1:]]==profile['layer_thickness_mm']
y=table(rows,14,174,[32,47,26],7,7.7)-5
for note in ['<b>Thickness:</b> order nominal 1.6 mm. Published finished thickness 1.54 mm +/-10%. Native copper/dielectric model totals 1.5384 mm; solder mask is unmodelled coating, not omitted.','<b>Finish:</b> 1 oz outer / 0.5 oz inner copper; green mask, white silk, ENIG.','<b>USB basis:</b> recorded JLC 90 ohm differential result W=0.1392 mm, gap=0.1600 mm, outer signal / adjacent GND, solder mask included. Final geometry and supplier controlled-impedance acceptance still apply.']:y=para(note,14,y,105,small)-4
y=174
notes=[('Stencil and hidden joints','U2 uses the local DSG footprint: eight 0.50 x 0.25 mm lead apertures and two 0.90 x 0.70 mm EP windows, all R0.05; rounded EP coverage 87.332%. U11 has four 1.37 x 1.73 mm EP windows. Keep via drill holes out of these apertures and inspect hidden joints.'),('Shared process acceptance','TI illustrates 0.125 mm stencil for U2 and 0.10 mm for U13. U13 aperture XY matches its DRL drawing. The assembler must accept the shared stencil thickness/local treatment and reflow process; matching XY is not qualification of solder volume or voiding. JLC six-layer ordering defaults to filled/capped vias; the actual quoted process remains an acceptance gate.'),('USB shell soldering','J2 has two front 0.60 x 1.40 mm plated slots and two rear 0.60 x 1.70 mm slots, with 0.20 mm copper rings. No shell paste apertures are provided. Explicitly include all four shell joints in the accepted assembly process. Do not treat contacts-only SMT reflow as proof of shell soldering. HRO specifies -30 to +80 C operation; this limits any whole-board temperature claim.'),('Panel and placements','The supplier CPL incorporates the user corrections; the unchanged native audit is supplied separately. Residual model/land/process warnings mean assembly is NOT CLEARED. Resolve each remaining warning and part orientation before approval. Use Standard double-sided PCBA with an accepted JLC carrier/panel. Approve connector access, rails, tooling, both-face fiducials and depaneling against the supplier drawing. No customer array is supplied; page 6 records the explicit supplier-CPL corrections.'),('Via geometry','Exactly seven documented through vias use 0.35 mm diameter / 0.20 mm drill and 0.075 mm radial annulus. All other vias retain at least 0.40 mm diameter. The exact UUID/net/position allowance accompanies the native package; supplier process acceptance is pending.'),('Qualification boundary','Exact J3 mating harness/fixture and 1 A combined input-path budget, TXC lot/HSE startup, stencil/reflow, thermal behaviour and production CAM remain open qualifications. Local CAD or file checks do not establish these physical results.')]
for title,note in notes:y=para('<b>'+title+'</b><br/>'+note,130,y,153,small)-4
y=para('<b>Primary process evidence:</b> <link href="https://www.ti.com/lit/ds/symlink/tps62160.pdf" color="#173d58">TI TPS6216x DSG</link> | <link href="https://www.ti.com/lit/ds/symlink/tps2116.pdf" color="#173d58">TI TPS2116 DRL</link> | <link href="https://jlc-prod-smt.oss-eu-central-1.aliyuncs.com/smtDataManualFile/8550723676065714176-C165948.pdf" color="#173d58">HRO USB drawing</link> | <link href="https://www.jst-mfg.com/product/pdf/eng/eSH.pdf" color="#173d58">JST SH</link> | <link href="https://jlcpcb.com/capabilities/pcb-assembly-capabilities" color="#173d58">JLC assembly</link> | <link href="https://jlcpcb.com/help/article/pcb-assembly-faqs-part-2" color="#173d58">JLC orientation</link>',130,y,153,small)
if y<20:warnings.append('Page5 notes overflow')
c.showPage()
header('Supplier CPL correction record','CPL corrections leave native lands and fitted poses unchanged | User file preserved | Residual assembly warnings remain')
overrides=json.loads((a.project/'review/assembly-cpl-overrides.json').read_text());supplied=a.project/'inputs/user-corrected-JLC_CPL.csv';assert sha(supplied)==overrides['source_sha256']
y=para('The user-provided placement file contains 79 unique references on the original sides. Its ten rotation changes and one USB pickup offset are reproduced below. A supplier rotation is a library-model convention; it does not rotate the native PCB lands. Native placement coordinates remain in the separate audit CSV.',14,174,269)-5
rows=[['Ref','Side','Native audit X,Y mm','Supplier X,Y mm','Native angle','Supplier angle']]
for q in overrides['overrides']:
 old=q['baseline_native_cpl'];new=q['user_corrected_cpl'];rows.append([q['reference'],new['Layer'],old['Mid X']+', '+old['Mid Y'],new['Mid X']+', '+new['Mid Y'],old['Rotation'],new['Rotation']])
y=table(rows,14,y,[17,22,66,66,49,49],7,8)-7
y=para('<b>Source integrity:</b> supplied CSV SHA-256 '+overrides['source_sha256'],14,y,269,small)-6
y=para('<b>Supplier rerun:</b> the corrected file cleared pin-without-pad, lead-to-hole, outer-lead and USB hole-alignment failures in the separate P2 geometry test. Residual U2/D4 land checks, the U11 bottom overlap finding and connector edge/process warnings remain. The P5-Routing-Review records the current review status; this page does not claim assembly clearance.',14,y,269)-6
para('<b>Required review:</b> confirm supplier model pin 1, actual package terminals and approved lands for every remaining finding, and accept the panel, stencil/reflow and shell-joint process before assembly. No purchase or assembly approval is implied by these files.',14,y,269)
c.showPage();c.save();assert sha(a.board)==sourcehash,'Native source changed during authoring' 
manifest={'status':'PROVISIONAL ROUTING IN PROGRESS' if not a.frozen else 'R3-S6-P5; ASSEMBLY NOT CLEARED; HARDWARE VALIDATION AND SUPPLIER ACCEPTANCE PENDING','board':str(a.board),'board_sha256':sourcehash,'revision':a.revision,'pdf':str(output),'pdf_sha256':sha(output),'pages':page,'page_size':'A4 landscape','scale_views':'Front/rear 4:1; socket details 7:1 at 100% print','fitted_count':79,'fitted_side_counts':dict(counts),'datum':'Native (0,38); CPL X=nativeX,Y=38-nativeY; common both faces','human_rear':'X_view=38-nativeX,Y_view=nativeY; human component-side mirror only','geometry_warnings':warnings,'visual_QA':'Pending rendered-page inspection','dimensions_mm':{'outline':[38,38],'corner_radius':2,'mount_pitch':[30.5,30.5],'mount_hole_diameter':2.2},'qualifications':['Supplier carrier/panel and exact-part placement alignment pending','Stencil/reflow and USB shell solder process acceptance pending','Harness, thermal, electrical and firmware prototype qualification pending']};(a.out/'assembly-drawing-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');print(json.dumps(manifest,indent=2))
