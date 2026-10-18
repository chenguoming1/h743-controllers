from pathlib import Path
import sys,json,hashlib,collections,csv,zipfile,xml.etree.ElementTree as ET
sys.path.insert(0,str(Path.cwd()/'tools'))
import sexpr as s,design
from apply_header_interface import first,ref
root=Path.cwd();out=root/'docs/validation/reviews/order-fixes-2026-10-17';baseline=Path('/tmp/nexus-order-fixes-20261017/owner-saved-baseline/hardware')
hash=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
report={}
for name,rel in [('main','nexus-style-fc'),('child','header-board/nexus-header-board')]:
 a=s.parse((baseline/(rel+'.kicad_pcb')).read_text());b=s.parse((root/'hardware'/(rel+'.kicad_pcb')).read_text());delta={}
 for kind in ['segment','arc','via','footprint']:
  get=lambda tree:{s.text(first(q,'uuid')[1]):q for q in s.find(tree,kind)}
  aa,bb=get(a),get(b);changed=[k for k in aa.keys()&bb.keys() if aa[k]!=bb[k]]
  delta[kind]={'added':len(bb.keys()-aa.keys()),'removed':len(aa.keys()-bb.keys()),'changed':len(changed)}
  if kind=='footprint':delta[kind]['changed_refs']=[ref(bb[k]) for k in changed]
 assert first(first(a,'setup'),'stackup')==first(first(b,'setup'),'stackup')
 assert first(a,'general')==first(b,'general')
 if name=='main':
  usb=lambda tree:[q for q in tree if isinstance(q,list) and q[0] in ['segment','arc','via'] and first(q,'net') and s.text(first(q,'net')[-1]) in ['USB_DP','USB_DN','USB_DM']]
  assert usb(a)==usb(b),'USB objects changed'
  all5v=lambda tree:[q for q in tree if isinstance(q,list) and q[0] in ['segment','arc','via'] and first(q,'net') and s.text(first(q,'net')[-1])=='5V_BUCK']
  assert all5v(a)==all5v(b),'User 5V_BUCK changed'
 report[name]={'old_sha256':hash(baseline/(rel+'.kicad_pcb')),'new_sha256':hash(root/'hardware'/(rel+'.kicad_pcb')),'stackup_unchanged':True,**delta}
parts={p['ref']:p for p in design.get_main_parts()};b=s.parse((root/'hardware/nexus-style-fc.kicad_pcb').read_text());fps={ref(f):f for f in s.find(b,'footprint')};assert set(parts)==set(fps)
for r,p in parts.items():
 f=fps[r];assert s.text(f[1])==p['fp'],(r,'footprint')
 prop={s.text(q[1]):s.text(q[2]) for q in s.find(f,'property')};assert prop['Value']==p['value'],(r,'value');assert prop.get('LCSC','')==(p.get('lcsc') or ''),(r,'lcsc',prop.get('LCSC'),p.get('lcsc'))
 for pad in s.find(f,'pad'):
  num=s.text(pad[1]);net=next(iter(s.find(pad,'net')),None);actual=s.text(net[-1]) if net else None;assert actual==p['pins'].get(num) or (p['pins'].get(num) is None and (actual or '').startswith('unconnected-')),(r,num,actual,p['pins'].get(num))
xml=ET.parse('/tmp/nexus-order-fixes-20261017/final-netlist.xml').getroot();actual={}
for net in xml.findall('./nets/net'):
 for n in net.findall('node'):actual[(n.get('ref'),n.get('pin'))]=net.get('name')
for r in ['U1','C9','R23','D4']:
 for pin,net in parts[r]['pins'].items():
  if net is not None:assert actual[(r,pin)]==net,(r,pin,actual.get((r,pin)),net)
files={}
for p in [root/'hardware/nexus-style-fc.kicad_pcb',root/'hardware/nexus-style-fc.kicad_sch',root/'hardware/header-board/nexus-header-board.kicad_pcb',root/'hardware/header-board/nexus-header-board.kicad_sch',*sorted((root/'manufacturing').glob('*/*.zip')),*sorted((root/'manufacturing').glob('*/*-jlc.csv'))]:files[str(p.relative_to(root))]=hash(p)
for name,expected in [('nexus-style-fc',16),('nexus-header-board',14)]:
 folder=root/'manufacturing'/name
 with zipfile.ZipFile(folder/(name+'-gerbers.zip')) as z:
  assert z.testzip() is None;assert len(z.namelist())==expected
  for member in z.namelist():assert z.read(member)==(folder/'gerbers'/member).read_bytes()
 bom=list(csv.DictReader((folder/(name+'-bom-jlc.csv')).open()));cpl=list(csv.DictReader((folder/(name+'-cpl-jlc.csv')).open()));bomrefs=[r for row in bom for r in row['Designator'].split(',')];assert set(bomrefs)=={row['Designator'] for row in cpl}
 report[name]={'BOM_groups':len(bom),'parts':len(bomrefs),'CPL_placements':len(cpl),'ZIP_members':expected}
report['files']=files;report['main']['usb_routes_unchanged']=True;report['main']['owner_5V_BUCK_preserved']=True
(out/'candidate-delta.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
