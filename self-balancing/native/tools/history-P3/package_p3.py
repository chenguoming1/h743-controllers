#!/usr/bin/python3
from pathlib import Path
import json,hashlib,zipfile,shutil
D=Path(__file__).resolve().parents[1];R=D.parent;O=Path('/workspace/scratch/8a35c1f26232/p3-output');O.mkdir(exist_ok=True);sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(D/'controller.kicad_pcb')=='0850991d8aacd22138487804c24eefbae634a21ba218c18196f13fad795c3696'
for n in ['routing-drc.json','p3-pin-audit.json']:
 d=json.loads((D/'review'/n).read_text());assert not any(d.get(x) for x in ['violations','unconnected_items','schematic_parity','errors','unexpected_map_entries'])
census=json.loads((R/'research/controller-r3s-green-study/combined06/uncapped-copper-census.json').read_text());assert not census['narrow_tracks'] and not census['foreign_copper_pairs']
manifest=json.loads((D/'release/SHA256_MANIFEST.json').read_text());assert all(sha(D/'release'/n)==h for n,h in manifest.items())
entries={}
def add(src,dst):
 src=Path(src);assert src.is_file(),src;assert dst not in entries,dst;entries[dst]=src.read_bytes()
def tree(src,dst,exclude=()):
 src=Path(src)
 for p in sorted(src.rglob('*')):
  if not p.is_file() or any(x in p.relative_to(src).parts for x in exclude) or p.suffix in ['.pyc','.kicad_prl','.log'] or p.name.endswith('.lck'):continue
  add(p,dst+'/'+str(p.relative_to(src)))
for p in D.iterdir():
 if p.is_file() and (p.suffix in ['.kicad_pcb','.kicad_pro','.kicad_sch','.kicad_dru'] or p.name in ['fp-lib-table','sym-lib-table','README.md']):add(p,'native/'+p.name)
tree(D/'library','native/library');tree(D/'tools','native/tools',('__pycache__',));tree(D/'inputs','native/inputs');tree(D/'review','native/review',('historical-P2-previews','history-P3','assembly-drawing','supplier-p3-evidence','final-manufacturing-audit','final-geometry-audit'))
tree(D/'release','release');tree(R/'research/p3-independent-fabrication-review/final','validation/independent');tree(R/'research/p3-independent-fabrication-review/advisories','validation/advisories');tree(D/'review/final-manufacturing-audit','validation/native');tree(D/'review/final-geometry-audit','validation/geometry');tree(D/'review/supplier-p3-evidence','dfm/evidence')
for n in ['assembly-drawing/controller-r3s-assembly-manufacturing.pdf','assembly-drawing/assembly-drawing-manifest.json','controller-r3s-p3-schematic.pdf','R3-S6-P3-DFM-Review.pdf','P3-DFM-Review.md','controller-r3s-front-copper.png','controller-r3s-rear-copper.png','copper-review-manifest.json']:
 add(D/'review'/n,'documents/'+Path(n).name)
for n in ['edge-pad-map.json','printed-pad-legend.json','pad-wiring-map.csv','manufacturing-profile.json','approved-small-vias.json','assembly-cpl-overrides.json','green-routing-targets.json']:
 add(D/'review'/n,'fabrication-notes/'+n)
for p in (R/'recovery-p2-20261003/qualification').iterdir():
 if p.is_file():add(p,'qualification/'+p.name)
for name in ['controller.kicad_pcb','controller.kicad_pro']:add(R/'controller-r3s-dfm'/name,'history/P2-'+name)
for name in ['merge.json','drc-complete.json','uncapped-copper-census.json','pin-audit.json']:
 add(R/'research/controller-r3s-green-study/combined06'/name,'validation/cumulative-geometry/'+name)
for rel in ['controller-p2-wider-routing-feasibility/combined06-ordinary-final-review.json','controller-p2-wider-routing-feasibility/combined06-ordinary-geometry.json','controller-p2-wider-routing-feasibility/combined06-ordinary-reference-transitions.json','controller-r3s-green-fast-route/combined06-independent-reference-audit.json','controller-r3s-green-fast-route/combined06-fast-usb-spacing.json','controller-r3s-green-node-shift/front-final/combined06-spotcheck.json']:
 add(R/'research'/rel,'validation/returns/'+Path(rel).name)
entries['README.md']=(D/'README.md').read_bytes();entries['ASSEMBLY_NOT_CLEARED.txt']=b'Trace width and trace spacing are green in the final P3 JLCDFM run. Assembly retains25red/6yellow model/process reports. Do not approve assembly or assume flight readiness from these files. See documents/P3-DFM-Review.md and qualification/. No order has been placed.\n'
entries['history/README.txt']=b'P2 source remains preserved for comparison. Current files are native/ and release/. Historical P1 electrical layout notes in qualification are background; current P3 routing and return-path evidence is under validation/.\n'
hashes={n:hashlib.sha256(data).hexdigest() for n,data in entries.items()};entries['SHA256_MANIFEST.json']=(json.dumps(hashes,indent=2)+'\n').encode();out=O/'R3-S6-P3-Native-Fabrication-ASSEMBLY-HOLD.zip'
with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
 for n,data in sorted(entries.items()):z.writestr(n,data)
with zipfile.ZipFile(out) as z:
 assert z.testzip() is None;assert all(hashlib.sha256(z.read(n)).hexdigest()==h for n,h in hashes.items())
for src,name in [(D/'release/assembly/JLC_BOM.csv','R3-S6-P3-JLC-BOM.csv'),(D/'release/assembly/JLC_CPL.csv','R3-S6-P3-JLC-CPL-USER-CORRECTED.csv'),(D/'review/assembly-drawing/controller-r3s-assembly-manufacturing.pdf','R3-S6-P3-Assembly.pdf'),(D/'review/controller-r3s-p3-schematic.pdf','R3-S6-P3-Schematic.pdf'),(D/'review/R3-S6-P3-DFM-Review.pdf','R3-S6-P3-DFM-Review.pdf'),(D/'review/controller-r3s-front-copper.png','R3-S6-P3-Front-Copper.png'),(D/'review/controller-r3s-rear-copper.png','R3-S6-P3-Rear-Copper.png')]:shutil.copy2(src,O/name)
result={'native_sha256':sha(D/'controller.kicad_pcb'),'package':str(out),'package_sha256':sha(out),'package_bytes':out.stat().st_size,'members':len(entries),'CRC_and_all_member_hashes':'PASS','artifacts':{p.name:{'path':str(p),'sha256':sha(p),'bytes':p.stat().st_size} for p in O.iterdir() if p.is_file() and p.suffix in ['.zip','.csv','.pdf','.png']}};(O/'release-artifacts.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
