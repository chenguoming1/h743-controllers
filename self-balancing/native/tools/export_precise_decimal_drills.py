#!/usr/bin/python3
"""Export KiCad native 3:6 drills, then losslessly make X/Y explicit decimal mm.
KiCad9 metric DECIMAL_FORMAT truncates precision to three decimals. No PCB edits.
"""
import os
os.environ.setdefault('KICAD_CONFIG_HOME','/tmp/controller-r3-kicad')
import argparse,decimal,hashlib,json,pathlib,re,tempfile
import pcbnew as p
TOKEN=re.compile(r'([XY])([+-]?\d+)')
def convert(text):
 assert '; FORMAT={3:6/ absolute / metric / keep zeros}' in text and '\nMETRIC\n' in text
 original=[];converted=[];lines=[]
 for line in text.splitlines():
  if line.startswith(('X','Y','G00','G01','G85')):
   original.extend((axis,int(value)) for axis,value in TOKEN.findall(line))
   line=TOKEN.sub(lambda m:m[1]+format(decimal.Decimal(m[2])/decimal.Decimal(1000000),'.6f'),line)
   converted.extend((axis,int(decimal.Decimal(value)*1000000)) for axis,value in re.findall(r'([XY])([+-]?\d+\.\d+)',line))
  lines.append(line)
 assert original==converted,'Coordinate conversion was not exact'
 assert len(lines)==len(text.splitlines())
 for before,after in zip(text.splitlines(),lines):
  if before.startswith(('X','Y','G00','G01','G85')):assert TOKEN.sub(lambda m:m[1]+'#',before)==re.sub(r'([XY])([+-]?\d+\.\d+)',lambda m:m[1]+'#',after),'Non-coordinate motion/slot record changed'
  else:assert before==after,'Non-coordinate tool/header record changed'
 result='\n'.join(lines)+'\n';result=result.replace('; FORMAT={3:6/ absolute / metric / keep zeros}','; FORMAT={-:-/ absolute / metric / decimal}\n; Exact six-decimal mm coordinates converted losslessly from native KiCad 3:6')
 return result,len(original)
def export(boardpath,out):
 boardpath=pathlib.Path(boardpath);out=pathlib.Path(out);source=hashlib.sha256(boardpath.read_bytes()).hexdigest();b=p.LoadBoard(str(boardpath));out.mkdir(exist_ok=True,parents=True);records={}
 with tempfile.TemporaryDirectory(prefix='r3s-precise-drill-') as tmp:
  w=p.EXCELLON_WRITER(b);w.SetFormat(True,p.EXCELLON_WRITER.KEEP_ZEROS,3,6);w.SetOptions(False,False,b.GetDesignSettings().GetAuxOrigin(),False);w.SetRouteModeForOvalHoles(False);assert w.CreateDrillandMapFilesSet(tmp,True,False)
  paths=sorted(pathlib.Path(tmp).glob('*.drl'));assert len(paths)==2
  for f in paths:
   converted,tokens=convert(f.read_text());target=out/f.name;target.write_text(converted);records[f.name]={'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'exact_coordinate_tokens':tokens}
 assert hashlib.sha256(boardpath.read_bytes()).hexdigest()==source,'Board changed during drill export'
 return {'native_sha256':source,'status':'PASS EXACT NATIVE DRILL COORDINATES','format':'Metric absolute explicit decimal, six fractional digits; separate PTH/NPTH, G85 oval records','conversion':'Native KiCad 3:6 coordinate integers reformatted exactly, never rounded','files':records}
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--board',type=pathlib.Path);ap.add_argument('--out',type=pathlib.Path);ap.add_argument('--selftest',action='store_true');a=ap.parse_args()
 if a.selftest:
  fixture='M48\n; FORMAT={3:6/ absolute / metric / keep zeros}\nMETRIC\nT1C0.200\n%\nG90\nT1\nX020192500Y035122500\nX-000000500Y000000000\nX030000000Y001000000G85X031100000Y001000000\nG00X005000000Y006000000\nG01X005600000Y006000000\nM30\n';result,n=convert(fixture);assert n==12 and 'X20.192500Y35.122500' in result and 'X-0.000500Y0.000000' in result and 'G85X31.100000Y1.000000' in result;print('PASS: half-micron, negative, zero, G85 and route coordinate conversions are exact')
 else:assert a.board and a.out;print(json.dumps(export(a.board,a.out),indent=2))
