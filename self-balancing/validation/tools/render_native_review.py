#!/usr/bin/python3
"""Whole-board native six-layer render for independent human visual review."""
import argparse,hashlib,json,pathlib,subprocess,os
from PIL import Image,ImageDraw,ImageFont
ap=argparse.ArgumentParser();ap.add_argument('--candidate',type=pathlib.Path,required=True);ap.add_argument('--sha256',required=True);ap.add_argument('--out',type=pathlib.Path,required=True);a=ap.parse_args();a.out.mkdir(parents=True,exist_ok=True)
sha=lambda q:hashlib.sha256(q.read_bytes()).hexdigest();assert sha(a.candidate)==a.sha256
here=pathlib.Path(__file__).resolve().parent;cli=['sh',str(here/'frozen-tools/kicad_cli.sh')];env=os.environ.copy();env['XDG_CONFIG_HOME']='/tmp/controller-r3-inkscape-config';env['XDG_CACHE_HOME']='/tmp/controller-r3-cache';pathlib.Path(env['XDG_CONFIG_HOME']).mkdir(exist_ok=True)
images=[];files=[]
for layer in ['F.Cu','In1.Cu','In2.Cu','In3.Cu','In4.Cu','B.Cu']:
 stem=layer.replace('.','-');svg=a.out/(stem+'.svg');png=a.out/(stem+'.png');display_layers=layer+',Edge.Cuts'
 if layer=='F.Cu':display_layers+=',F.SilkS'
 if layer=='B.Cu':display_layers+=',B.SilkS'
 cmd=cli+['pcb','export','svg','--mode-single','--layers',display_layers,'--fit-page-to-board','--exclude-drawing-sheet','--drill-shape-opt','2','--output',str(svg)]
 if layer=='B.Cu':cmd+=['--mirror']
 subprocess.run(cmd+[str(a.candidate)],check=True,stdout=subprocess.DEVNULL)
 subprocess.run(['inkscape',str(svg),'--export-type=png','--export-filename='+str(png),'--export-width=2200','--export-background=white','--export-background-opacity=1'],check=True,env=env,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
 im=Image.open(png).convert('RGB');im.thumbnail((1000,1000));images.append((layer,im.copy()));files+=[svg,png]
canvas=Image.new('RGB',(3100,2210),'#101e27');draw=ImageDraw.Draw(canvas);font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',28)
for i,(label,im) in enumerate(images):
 x=25+(i%3)*1025;y=90+(i//3)*1070;canvas.paste(im,(x,y));draw.text((x,y-40),label+(' mirrored underside' if label=='B.Cu' else ' native top view'),font=font,fill='white')
draw.text((25,2170),'Candidate '+a.sha256+' | Independent review pending',font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',22),fill='white');montage=a.out/'whole-board-six-layer.png';canvas.save(montage);files.append(montage)
assert sha(a.candidate)==a.sha256
(a.out/'render-manifest.json').write_text(json.dumps({'source':str(a.candidate),'sha256':a.sha256,'files':{q.name:sha(q) for q in files},'visual_review':'PENDING; an export alone is not a visual pass'},indent=2)+'\n');print(str(montage))
