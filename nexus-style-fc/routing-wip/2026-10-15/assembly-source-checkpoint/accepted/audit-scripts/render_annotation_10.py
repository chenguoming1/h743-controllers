from pathlib import Path
import json,subprocess,hashlib,re,xml.etree.ElementTree as ET
R=Path('/workspace/scratch/8a35c1f26232/nexus-recovery-20261015');S=R/'mechanical-integration/main-signal-slot-08';C=R/'mechanical-integration/main-assembly-annotation-10';O=C/'visual-proof';assert not O.exists();O.mkdir();K=str(R/'runtime/kicad-cli');sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();commands=[]
def run(cmd,log):
 with (O/log).open('w') as f:p=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,timeout=90)
 commands.append({'command':cmd,'log':log,'exit_code':p.returncode});assert p.returncode==0,(cmd,p.returncode)
for label,source in [('before',S),('after',C)]:
 d=O/label;d.mkdir();sch=source/'hardware/nexus-style-fc.kicad_sch';run([K,'sch','export','pdf','-o',str(d/'nexus-schematic.pdf'),str(sch)],label+'-pdf.log');run([K,'sch','export','svg','-o',str(d/'svg'),str(sch)],label+'-svg.log');run(['pdftoppm','-scale-to','2200','-png','-singlefile',str(d/'nexus-schematic.pdf'),str(d/'schematic')],label+'-raster.log')
def vector(p):
 root=ET.parse(p).getroot()
 for elem in list(root):
  if elem.tag.split('}')[-1] in ['title','desc','metadata']:root.remove(elem)
 return ET.tostring(root)
a=list((O/'before/svg').glob('*.svg'));b=list((O/'after/svg').glob('*.svg'));assert len(a)==len(b)==1;assert vector(a[0])==vector(b[0]),'Rendered SVG geometry changed';assert (O/'before/schematic.png').read_bytes()==(O/'after/schematic.png').read_bytes(),'PDF raster changed'
run([K,'pcb','export','svg','--layers','F.Mask,F.SilkS,Edge.Cuts','--mode-single','--fit-page-to-board','--exclude-drawing-sheet','-o',str(O/'top-silk-mask.svg'),str(C/'hardware/nexus-style-fc.kicad_pcb')],'top-plot.log')
svg=(O/'top-silk-mask.svg').read_text();circles=ET.fromstring(svg).findall('.//{http://www.w3.org/2000/svg}circle');marks=[]
for ref,x in [('D1',7.2),('D2',13.6),('D3',10.4)]:
 matches=[q for q in circles if abs(float(q.attrib['cx'])-x)<1e-9 and abs(float(q.attrib['cy'])-26.25)<1e-9 and abs(float(q.attrib['r'])-.15)<1e-9];assert len(matches)==1,(ref,matches);marks.append({'ref':ref,'plot_center_mm':[x,26.25],'absolute_board_center_mm':[x+100,126.25],'outer_ink_diameter_mm':.3,'native_exported':True})
# High-contrast inspection derivative only; original native SVG remains exact.
preview=svg.replace('#F2EDA1','#4A4300').replace('viewBox="0.0000 0.0000 22.3774 33.0962"','viewBox="0.0000 20.0000 22.3774 13.0962"').replace('height="33.0962mm"','height="13.0962mm"');(O/'annotation-detail-inspection.svg').write_text(preview);run(['inkscape',str(O/'annotation-detail-inspection.svg'),'--export-type=png','--export-width=1800','--export-background=white','--export-filename='+str(O/'annotation-detail-inspection.png')],'annotation-render.log')
result={'status':'PASS native final PDF/vector/raster equivalence and printed cathode geometry','before_schematic_sha256':sha(S/'hardware/nexus-style-fc.kicad_sch'),'after_schematic_sha256':sha(C/'hardware/nexus-style-fc.kicad_sch'),'final_PDF':'after/nexus-schematic.pdf','final_PDF_sha256':sha(O/'after/nexus-schematic.pdf'),'SVG_geometry_byte_exact_after_removing_nonrendering_title_desc_metadata':True,'native_PDF_raster_byte_exact':True,'raster_sha256':sha(O/'after/schematic.png'),'markers':marks,'commands':commands,'qualification':'Marker orientation is additionally bound to the primary manufacturer drawings in the annotation handoff. High-contrast cropped inspection derivative is labeled; exact original native SVG is retained. Existing silk advisories remain.'};(O/'verification.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
