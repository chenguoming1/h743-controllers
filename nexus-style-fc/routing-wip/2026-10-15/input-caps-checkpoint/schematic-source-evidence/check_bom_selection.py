"""Verify BOM selector only; stub position export, never generate CAM or real CPL."""
from pathlib import Path
import importlib.util,types,csv,tempfile,json
P=Path(__file__).parent
def load(n,p):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
out=[]
for tree in ('baseline','work'):
 t=P/tree/'nexus-style-fc/tools';d=load('d',t/'design.py');e=load('e',t/'export_fab.py');e.importlib=types.SimpleNamespace(import_module=lambda name:d)
 def fake_run(*args):
  assert args[:3]==('pcb','export','pos'),args
  Path(args[args.index('-o')+1]).write_text('Ref,PosX,PosY,Side,Rot\n')
 e.run=fake_run
 with tempfile.TemporaryDirectory(dir=P) as temp:
  e.bom_cpl('nexus-style-fc','NO_REAL_PCB','design',temp)
  rows=list(csv.DictReader(open(Path(temp)/'nexus-style-fc-bom-jlc.csv')))
  out.append({ref:row for row in rows for ref in row['Designator'].split(',')})
a,b=out;assert set(b)-set(a)=={'C31'}
for ref in a:
 if ref=='C27':continue
 assert {k:v for k,v in a[ref].items() if k!='Designator'}=={k:v for k,v in b[ref].items() if k!='Designator'}
for r in ('C27','C31'):
 assert b[r]['Comment']=='22uF' and b[r]['Footprint']=='C_0805_2012Metric_Samsung_CL21_MinLand' and b[r]['LCSC Part #']=='C602037'
(P/'bom-selection-test.json').write_text(json.dumps({'result':'PASS','C27_C31':{r:b[r] for r in ('C27','C31')},'all_other_BOM_values_preserved':True,'position_export_stubbed':True,'no_CAM_or_actual_CPL_generated':True},indent=2)+'\n')
