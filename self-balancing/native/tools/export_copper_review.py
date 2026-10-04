#!/usr/bin/python3
"""Render actual filled native copper with explicit local-check status."""
from pathlib import Path
import subprocess,json,hashlib,os
from PIL import Image,ImageDraw,ImageFont
D=Path(__file__).resolve().parents[1];O=D/'review';b=D/'controller.kicad_pcb';cli=['sh',str(D/'tools/kicad_cli.sh')];report=json.loads((O/'routing-drc.json').read_text());opens=len(report['unconnected_items']);clean=not any(report[k] for k in ['violations','unconnected_items','schematic_parity']);sha=hashlib.sha256(b.read_bytes()).hexdigest()
erc=json.loads((O/'erc.json').read_text());check_counts={'erc':sum(len(s['violations']) for s in erc['sheets']),'physical_drc':len(report['violations']),'parity':len(report['schematic_parity']),'unconnected':opens};clean=all(v==0 for v in check_counts.values())
env=os.environ.copy();env['XDG_CONFIG_HOME']='/tmp/controller-r3-inkscape-config';env['XDG_CACHE_HOME']='/tmp/controller-r3-cache';Path(env['XDG_CONFIG_HOME']).mkdir(exist_ok=True)
revision=json.loads((O/'green-routing-targets.json').read_text())['revision']
font=lambda s:ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',s)
for face,layer,silk in [('front','F.Cu','F.SilkS'),('rear','B.Cu','B.SilkS')]:
 svg=O/f'controller-r3s-{face}-copper.svg';raw=O/f'controller-r3s-{face}-copper-raw.png';png=O/f'controller-r3s-{face}-copper.png'
 cmd=cli+['pcb','export','svg','--mode-single','--layers',','.join([layer,silk,'Edge.Cuts']),'--fit-page-to-board','--exclude-drawing-sheet','--drill-shape-opt','2','--output',str(svg)]
 if face=='rear':cmd+=['--mirror']
 subprocess.run(cmd+[str(b)],check=True,stdout=subprocess.DEVNULL)
 subprocess.run(['inkscape',str(svg),'--export-type=png','--export-filename='+str(raw),'--export-width=1700','--export-background=white','--export-background-opacity=1'],env=env,check=True,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
 im=Image.open(raw).convert('RGB');w,h=im.size;canvas=Image.new('RGB',(w+160,h+260),'#0b1923');canvas.paste(im,(80,150));draw=ImageDraw.Draw(canvas)
 draw.text((80,28),f'{revision} H743 | {face.upper()} actual copper',font=font(42),fill='#f4faf8')
 state='Routed prototype CAD; hardware validation pending' if clean else f'Routing in progress | {opens} open connections | not for fabrication'
 draw.text((80,88),f'38 x 38 mm | six layers | {state}',font=font(23),fill='#83d8bd')
 draw.text((80,h+173),'Rear is mirrored for human inspection' if face=='rear' else 'Native top view; actual copper, holes and printed silkscreen',font=font(22),fill='#e3ece9')
 draw.text((80,h+207),f'PCB SHA256 {sha[:20]}... | Drawing is not to print scale; physical qualification remains open',font=font(19),fill='#b7c9c3');canvas.save(png);raw.unlink()
for layer in ['In1.Cu','In2.Cu','In3.Cu','In4.Cu']:
 subprocess.run(cli+['pcb','export','svg','--mode-single','--layers',layer+',Edge.Cuts','--fit-page-to-board','--exclude-drawing-sheet','--drill-shape-opt','2','--output',str(O/('controller-r3s-'+layer.replace('.','-')+'.svg')),str(b)],check=True,stdout=subprocess.DEVNULL)
assert hashlib.sha256(b.read_bytes()).hexdigest()==sha, 'Native source changed during preview export'
files=[O/f'controller-r3s-{face}-copper.{ext}' for face in ['front','rear'] for ext in ['png','svg']]+[O/f'controller-r3s-In{i}-Cu.svg' for i in range(1,5)]
manifest={'native_sha256':sha,'check_counts':check_counts,'file_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in files},'visual_QA':{'status':'PENDING','reviewed_files':[],'no_provisional_markers':False,'matches_actual_native_copper':False},'qualifications':['Routed prototype CAD only; hardware validation and supplier acceptance remain pending'],'rear_view':'Mirrored for human inspection only; CPL remains unmirrored'}
(O/'copper-review-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps({'native_sha256':sha,'open_connections':opens,'all_local_drc_fields_empty':clean,'views':'actual front/rear copper PNG+SVG and four inner-layer SVGs'},indent=2))
