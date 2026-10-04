#!/usr/bin/python3
"""Package the frozen P4 and its verified review evidence; no diagnostic Gerbers."""
from pathlib import Path
import hashlib,json,shutil,zipfile
D=Path(__file__).resolve().parents[1];ROOT=D.parent
O=Path('/workspace/scratch/8a35c1f26232/p4-output');O.mkdir(exist_ok=True)
E=ROOT/'research/controller-r3s-p4-independent-validation/final'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
NATIVE='b2532487feab1cfd68047b27999651e6c35cae959b0d115ef2762de5341bdb7a'
assert sha(D/'controller.kicad_pcb')==NATIVE
gate=json.loads((D/'review/green-routing-targets.json').read_text())
assert gate['full_layer_geometry_audit_pass'] and gate['supplier_trace_green_confirmed']
assert gate['supplier_trace_width_red_yellow']==gate['supplier_trace_spacing_red_yellow']==[0,0]
assert gate['supplier_SMT_red_yellow']==[24,6]
for n in ['routing-drc.json','p4-pin-audit.json']:
 doc=json.loads((D/'review'/n).read_text())
 assert not any(doc.get(k) for k in ['violations','unconnected_items','schematic_parity','errors','unexpected_map_entries'])
summary=json.loads((E/'final-independent-summary.json').read_text());assert summary['native_sha256']==NATIVE
assert summary['release_manifest_sha256']==sha(D/'release/SHA256_MANIFEST.json')
manifest=json.loads((D/'release/SHA256_MANIFEST.json').read_text())
assert all(sha(D/'release'/n)==h for n,h in manifest.items())
assert json.loads((D/'review/assembly-drawing/assembly-drawing-manifest.json').read_text())['visual_QA']['status']=='PASS'
assert json.loads((D/'review/copper-review-manifest.json').read_text())['visual_QA']['status']=='PASS'
assert json.loads((D/'review/dfm-report-visual-qa.json').read_text())['status'].startswith('PASS')
entries={}
def add(src,dst):
 src=Path(src);assert src.is_file(),src;assert dst not in entries,dst;entries[dst]=src.read_bytes()
def tree(src,dst,exclude=(),skip_vendor_pdf=False):
 src=Path(src)
 for p in sorted(src.rglob('*')):
  rel=p.relative_to(src)
  if not p.is_file() or any(x in rel.parts for x in exclude) or p.suffix in ['.pyc','.kicad_prl','.log'] or p.name.endswith('.lck'):continue
  if skip_vendor_pdf and p.suffix.lower()=='.pdf':continue
  assert 'DIAGNOSTIC-ONLY' not in p.name and p.suffix.lower()!='.zip',(src,p)
  add(p,dst+'/'+str(rel))
for p in D.iterdir():
 if p.is_file() and (p.suffix in ['.kicad_pcb','.kicad_pro','.kicad_sch','.kicad_dru'] or p.name in ['fp-lib-table','sym-lib-table','README.md']):add(p,'native/'+p.name)
tree(D/'library','native/library');tree(D/'tools','native/tools',('__pycache__','history-P3'))
tree(D/'inputs','native/inputs')
review_names=['audit_controller_r3s_independent.py','controller-r3s-independent-expectations.json','controller-netlist.xml','design-netmap.json','bom-draft.csv','approved-small-vias.json','historical-P2-via-inventory.json','assembly-cpl-overrides.json','manufacturing-profile.json','h743-pin-map.json','edge-pad-map.json','printed-pad-legend.json','pad-wiring-map.csv','green-routing-targets.json','erc.json','routing-drc.json','p4-pin-audit.json','p4-revision-intent.json','p4-front-slot-changes.json','p4-freeze-metadata-change.json','p4-d4-rectangle-change.json','p4-revision-geometry.json','p4-uncapped-copper-census.json','p4-refill-verification.json','generated-gerber-job-original.json','gerber-job-normalization.json','dfm-report-visual-qa.json','schematic-pdf-visual-qa.json','copper-review-manifest.json']
for n in review_names:add(D/'review'/n,'native/review/'+n)
tree(D/'review/sourcing','native/review/sourcing')
tree(D/'release','release')
tree(E,'validation/independent',('__pycache__','native-gerber-comparison'))
add(ROOT/'research/controller-r3s-p4-independent-validation/check_revision_geometry.py','validation/check_revision_geometry.py')
for n in ['proof.json','pad-partitions.json','README.md','local-route-review.png']:
 add(ROOT/'research/controller-r3s-p4-usb-slot-route'/n,'validation/local-slot-route/'+n)
tree(D/'review/supplier-p4-evidence','dfm/production-P4')
tree(D/'review/smt-manufacturer-evidence','dfm/manufacturer-and-diagnostic-evidence',('__pycache__',),skip_vendor_pdf=True)
for n in ['assembly-drawing/controller-r3s-assembly-manufacturing.pdf','assembly-drawing/assembly-drawing-manifest.json','controller-r3s-p4-schematic.pdf','R3-S6-P4-DFM-Review.pdf','P4-DFM-Review.md','controller-r3s-front-copper.png','controller-r3s-rear-copper.png']:
 add(D/'review'/n,'documents/'+Path(n).name)
for n in ['manufacturing-profile.json','approved-small-vias.json','assembly-cpl-overrides.json','green-routing-targets.json','pad-wiring-map.csv','printed-pad-legend.json']:
 add(D/'review'/n,'fabrication-notes/'+n)
for p in (ROOT/'recovery-p2-20261003/qualification').iterdir():
 if p.is_file():add(p,'qualification/'+p.name)
for n in ['controller.kicad_pcb','controller.kicad_pro']:
 add(ROOT/'controller-r3s-green'/n,'history/P3-'+n)
add(D/'README.md','README.md')
entries['ASSEMBLY_NOT_CLEARED.txt']=b'P4 width and spacing are green. Remaining24red/6yellowSMT reports are documented package/process exceptions; supplier model/pin1, carrier, stencil/reflow and hardware qualification remain. Production U2/U11 split paste is intact. Diagnostic Gerbers are deliberately absent. No order is authorized by this package.\n'
entries['history/README.txt']=b'P3 is retained only as comparison history. Use current native/ and release/. Prior P1 qualification records describe unchanged safety and bringup limits; current geometry evidence is validation/.\n'
entries['dfm/manufacturer-and-diagnostic-evidence/SOURCE_FILES.txt']=b'Manufacturer PDFs are linked in the source reports; complete third-party PDFs are not duplicated in this archive. Audited package drawing excerpts, calculated overlays, source hashes and controlled-analysis evidence are included. No diagnostic fabrication file is included.\n'
hashes={n:hashlib.sha256(v).hexdigest() for n,v in entries.items()}
entries['SHA256_MANIFEST.json']=(json.dumps(hashes,indent=2)+'\n').encode()
out=O/'R3-S6-P4-Native-Fabrication-ASSEMBLY-HOLD.zip'
with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
 for n,v in sorted(entries.items()):z.writestr(n,v)
with zipfile.ZipFile(out) as z:
 assert z.testzip() is None
 assert all(hashlib.sha256(z.read(n)).hexdigest()==h for n,h in hashes.items())
 assert not any('DIAGNOSTIC-ONLY' in n or n.lower().endswith('.zip') for n in z.namelist())
for src,name in [(D/'review/assembly-drawing/controller-r3s-assembly-manufacturing.pdf','R3-S6-P4-Assembly.pdf'),(D/'review/controller-r3s-p4-schematic.pdf','R3-S6-P4-Schematic.pdf'),(D/'review/R3-S6-P4-DFM-Review.pdf','R3-S6-P4-DFM-Review.pdf'),(D/'review/controller-r3s-front-copper.png','R3-S6-P4-Front-Copper.png'),(D/'review/controller-r3s-rear-copper.png','R3-S6-P4-Rear-Copper.png')]:shutil.copy2(src,O/name)
result={'native_sha256':NATIVE,'package':str(out),'package_sha256':sha(out),'package_bytes':out.stat().st_size,'members':len(entries),'CRC_and_all_member_hashes':'PASS','diagnostic_fabrication_files_included':False,'artifacts':{p.name:{'path':str(p),'sha256':sha(p),'bytes':p.stat().st_size} for p in O.iterdir() if p.is_file() and p.suffix in ['.zip','.csv','.pdf','.png']}}
(O/'release-artifacts.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
