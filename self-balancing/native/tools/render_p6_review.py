from pathlib import Path
import re,html,hashlib,datetime,argparse
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,KeepTogether
from reportlab.lib.pagesizes import A4,landscape
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
D=Path(__file__).resolve().parents[1];R=D/'review';source=R/'P6-Routing-Review.md';out=R/'R3-S6-P6-Routing-Review.pdf'
ap=argparse.ArgumentParser();ap.add_argument('--expected-board-sha256',required=True);a=ap.parse_args()
source_hash=hashlib.sha256((D/'controller.kicad_pcb').read_bytes()).hexdigest();assert source_hash==a.expected_board_sha256, 'Owner freeze hash mismatch'
assert 'R3-S6-P6' in source.read_text(), 'Report is not labelled P6'
for n,f in [('ReportSans','DejaVuSans.ttf'),('ReportSans-Bold','DejaVuSans-Bold.ttf')]:pdfmetrics.registerFont(TTFont(n,'/usr/share/fonts/truetype/dejavu/'+f))
pdfmetrics.registerFontFamily('ReportSans',normal='ReportSans',bold='ReportSans-Bold',italic='ReportSans',boldItalic='ReportSans-Bold')
styles={'body':ParagraphStyle('body',fontName='ReportSans',fontSize=9,leading=12,spaceAfter=4),'title':ParagraphStyle('title',fontName='ReportSans-Bold',fontSize=21,leading=26,spaceAfter=12,textColor=colors.black),'heading':ParagraphStyle('heading',fontName='ReportSans-Bold',fontSize=13,leading=17,spaceBefore=11,spaceAfter=7,keepWithNext=True,textColor=colors.black),'cell':ParagraphStyle('cell',fontName='ReportSans',fontSize=8.1,leading=10.7),'headcell':ParagraphStyle('headcell',fontName='ReportSans-Bold',fontSize=8.2,leading=10.7,textColor=colors.white)}
def inline(t):
 t=html.escape(t);t=re.sub(r'\[([^\]]+)\]\(([^)]+)\)',r'<link href="\2" color="#245b89">\1</link>',t);t=re.sub(r'\*\*(.+?)\*\*',r'<b>\1</b>',t);t=re.sub(r'`([^`]+)`',r'\1',t);return t
lines=source.read_text().splitlines();story=[];i=0
while i<len(lines):
 line=lines[i].strip()
 if not line:i+=1;continue
 if line=='## Sources':i+=1;continue
 if re.match(r'^1\. \[',line):
  sources=[]
  while i<len(lines) and re.match(r'^\d+\. \[',lines[i].strip()):sources.append(lines[i].strip());i+=1
  story.append(Paragraph('<b>Sources:</b> '+' &nbsp; | &nbsp; '.join(inline(x) for x in sources),styles['cell']));continue
 if line.startswith('|'):
  rows=[]
  while i<len(lines) and lines[i].strip().startswith('|'):
   cells=[s.strip() for s in lines[i].strip().strip('|').split('|')]
   if not all(re.fullmatch(r'[:\- ]+',s) for s in cells):rows.append(cells)
   i+=1
  n=len(rows[0]);widths=([45,37,37,150] if len(rows)==6 else [47,68,58,96]) if n==4 else [58,211]
  data=[[Paragraph(inline(c),styles['headcell' if j==0 else 'cell']) for c in row] for j,row in enumerate(rows)]
  table=Table(data,colWidths=[x*mm for x in widths],repeatRows=1,hAlign='LEFT');table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#173d58')),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#f0f4f7')]),('VALIGN',(0,0),(-1,-1),'TOP'),('GRID',(0,0),(-1,-1),.3,colors.HexColor('#c5cfd6')),('LEFTPADDING',(0,0),(-1,-1),5),('RIGHTPADDING',(0,0),(-1,-1),5),('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5)]));story+=[table,Spacer(1,7)];continue
 if line.startswith('# '):story.append(Paragraph(inline(line[2:]),styles['title']))
 elif line.startswith('## '):story.append(Paragraph(inline(line[3:]),styles['heading']))
 else:story.append(Paragraph(inline(line),styles['body']))
 i+=1
W,H=landscape(A4)
def make_canvas(*args, **kwargs):
 c=canvas.Canvas(*args,**kwargs);stamp=datetime.datetime.now(datetime.timezone.utc).strftime('D:%Y%m%d%H%M%SZ');c.setDateFormatter(lambda *unused:stamp);return c
def footer(c,doc):
 c.setStrokeColor(colors.HexColor('#ccd5dd'));c.line(14*mm,14*mm,(W/mm-14)*mm,14*mm);c.setFont('ReportSans',7);c.setFillColor(colors.HexColor('#526879'));c.drawString(14*mm,9*mm,'R3-S6-P6 | PCBA production approval required | Native '+hashlib.sha256((D/'controller.kicad_pcb').read_bytes()).hexdigest()[:16]);c.drawRightString(W-14*mm,9*mm,str(doc.page))
SimpleDocTemplate(str(out),pagesize=(W,H),leftMargin=14*mm,rightMargin=14*mm,topMargin=14*mm,bottomMargin=17*mm,title='P6 Controller Routing Review',author='Controller engineering review').build(story,onFirstPage=footer,onLaterPages=footer,canvasmaker=make_canvas)
print(out)

assert hashlib.sha256((D/'controller.kicad_pcb').read_bytes()).hexdigest()==source_hash, 'Native source changed during report export'
