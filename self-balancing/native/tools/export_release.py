#!/usr/bin/python3
"""Export one-board fabrication/assembly data only after a clean native release check.
This intentionally refuses partial routing or warning exclusions. Manufacturer panel/CPL
approval and physical qualification are separate from these local file checks.
"""
from pathlib import Path
import json,csv,re,sys,subprocess,shutil,hashlib,zipfile,os
import pcbnew as p
from export_precise_decimal_drills import export as export_precise_drills
from normalize_gerber_job import normalize as normalize_gerber_job
D=Path(__file__).resolve().parents[1];OUT=D/'release';CHECK=D/'review';cli=['sh',str(D/'tools/kicad_cli.sh')]
targets=json.loads((CHECK/'green-routing-targets.json').read_text())
assert targets['supplier_boundary_confirmed'], 'P3 is work in progress: supplier green boundaries/USB calculation not yet verified'
assert (D/'controller.kicad_dru').exists(), 'P3 strengthened trace-width/spacing rules must be present before release'
assert targets.get('usb_geometry_implemented'), 'P3 verified USB geometry is not yet integrated'
assert targets.get('full_layer_geometry_audit_pass'), 'P3 uncapped six-layer width/spacing audit must pass before export'
def run(args):subprocess.run(cli+args,cwd=D,check=True)
def erc_count(doc):return sum(len(s.get('violations',[])) for s in doc.get('sheets',[]))
run(['sch','erc','--format','json','--severity-all','-o',str(CHECK/'erc.json'),str(D/'controller.kicad_sch')])
run(['pcb','drc','--format','json','--severity-all','--schematic-parity','-o',str(CHECK/'routing-drc.json'),str(D/'controller.kicad_pcb')])
erc=json.loads((CHECK/'erc.json').read_text());drc=json.loads((CHECK/'routing-drc.json').read_text())
assert erc_count(erc)==0, 'ERC is not clean'
assert not drc['violations'], 'DRC still contains violations/warnings; finish them before export'
assert not drc['unconnected_items'], 'Routing is incomplete'
assert not drc['schematic_parity'], 'Schematic/PCB parity is not clean'
project=json.loads((D/'controller.kicad_pro').read_text());assert not project['board']['design_settings'].get('drc_exclusions',[]), 'Unreviewed DRC exclusions present'
b=p.LoadBoard(str(D/'controller.kicad_pcb'));assert b.GetCopperLayerCount()==6;fps={f.GetReference():f for f in b.GetFootprints()};parts=json.loads((CHECK/'design-netmap.json').read_text());fitted={q['Reference']:q for q in parts if q.get('LCSC') and not q.get('DNP')};assert len(fitted)==79 and len(fps)==151
for ref,q in fitted.items():
 f=fps[ref]
 for field,expected in [('LCSC',q['LCSC']),('Manufacturer_Part_Number',q['MPN'])]:
  actual=f.GetFieldByName(field);assert actual and actual.GetText()==expected,(ref,field,expected)
 assert f.GetValue()==q['Value'],ref
assert not OUT.exists() or not any(OUT.iterdir()), 'Archive the previous release directory before exporting; stale output files are not permitted'
OUT.mkdir(exist_ok=True);fab=OUT/'single-board-gerbers';fab.mkdir(exist_ok=True);asm=OUT/'assembly';asm.mkdir(exist_ok=True)
run(['pcb','export','gerbers','--layers','F.Cu,In1.Cu,In2.Cu,In3.Cu,In4.Cu,B.Cu,F.Mask,B.Mask,F.SilkS,B.SilkS,F.Paste,B.Paste,Edge.Cuts','--precision','6','--subtract-soldermask','--use-drill-file-origin','--output',str(fab),str(D/'controller.kicad_pcb')])
gerber_job_proof=normalize_gerber_job(fab,CHECK,targets)
drill_coordinate_proof=export_precise_drills(D/'controller.kicad_pcb',fab)
raw=asm/'raw-kicad-placements.csv';run(['pcb','export','pos','--side','both','--format','csv','--units','mm','--use-drill-file-origin','--exclude-dnp','--output',str(raw),str(D/'controller.kicad_pcb')]);rows=list(csv.DictReader(raw.open()));assert {q['Ref'] for q in rows}==set(fitted)
origin=b.GetDesignSettings().GetAuxOrigin();ox,oy=p.ToMM(origin.x),p.ToMM(origin.y);assert (ox,oy)==(0,38)
cpl=[]
for q in rows:
 ref=q['Ref'];f=fps[ref];pos=f.GetPosition();x,y=p.ToMM(pos.x),p.ToMM(pos.y);assert abs(float(q['PosX'])-(x-ox))<1e-6;assert abs(float(q['PosY'])-(oy-y))<1e-6;angle=float(q['Rot'])%360;assert abs((angle-f.GetOrientationDegrees())%360)<1e-5 or abs((angle-f.GetOrientationDegrees())%360-360)<1e-5
 assert q['Side']==('bottom' if f.GetLayer()==p.B_Cu else 'top')
 cpl.append({'Designator':ref,'Mid X':f'{x-ox:.6f}','Mid Y':f'{oy-y:.6f}','Layer':'Bottom' if f.GetLayer()==p.B_Cu else 'Top','Rotation':f'{angle:.6f}'})
def natural(ref):return(re.sub(r'\d+','',ref),int(re.search(r'\d+',ref).group()))
cpl.sort(key=lambda q:natural(q['Designator']))
native_cpl=[dict(q) for q in cpl]
with (asm/'JLC_CPL_NATIVE_AUDIT.csv').open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=['Designator','Mid X','Mid Y','Layer','Rotation']);w.writeheader();w.writerows(native_cpl)
overrides=json.loads((CHECK/'assembly-cpl-overrides.json').read_text())
source=D/'inputs/user-corrected-JLC_CPL.csv'
assert hashlib.sha256(source.read_bytes()).hexdigest()==overrides['source_sha256'], 'User-corrected CPL source changed'
byref={q['Designator']:q for q in cpl}
for item in overrides['overrides']:
 ref=item['reference'];q=byref[ref]
 assert q==item['baseline_native_cpl'], f'{ref}: native pose changed; revalidate supplier correction'
 q.update(item['user_corrected_cpl'])
assert cpl==list(csv.DictReader(source.open(newline=''))), 'Final supplier CPL must reproduce the structurally validated user file'
with (asm/'JLC_CPL.csv').open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=['Designator','Mid X','Mid Y','Layer','Rotation']);w.writeheader();w.writerows(cpl)
groups={}
for ref,q in fitted.items():groups.setdefault((q['MPN'],q['LCSC'],q['Footprint']),[]).append(ref)
bom=[]
for (mpn,code,fp),refs in sorted(groups.items()):bom.append({'Comment':mpn,'Designator':','.join(sorted(refs,key=natural)),'Footprint':fp,'LCSC Part #':code,'Manufacturer Part Number':mpn,'Quantity':len(refs)})
with (asm/'JLC_BOM.csv').open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(bom[0]));w.writeheader();w.writerows(bom)
assert sum(q['Quantity'] for q in bom)==79
for name in ['manufacturing-profile.json','printed-pad-legend.json','edge-pad-map.json','h743-pin-map.json','assembly-cpl-overrides.json']:shutil.copyfile(CHECK/name,OUT/name)
notes={'gerber_job_proof':gerber_job_proof,'drill_coordinate_proof':drill_coordinate_proof,'status':'Local single-board submission export; independent artifact review and manufacturer panel/placement approval still required','native_sha256':hashlib.sha256((D/'controller.kicad_pcb').read_bytes()).hexdigest(),'fitted_count':79,'bom_group_count':len(bom),'cpl_count':len(cpl),'excluded_feature_count':len(fps)-len(fitted),'origin_native_mm':[ox,oy],'cpl_coordinates':'Native audit:X=nativeX;Y=38-nativeY,same frame both faces,no bottomXmirror. Supplier CPL adds explicit user overrides; angles normalized modulo360.','cpl_supplier_alignment':'User-supplied corrections applied to11 references:10 rotation offsets and J2 pickup X−1.35mm. Actual PCB footprint poses are unchanged. Native audit CSV and exact override provenance accompany this export; final supplier model/pin1 acceptance remains separate.','cpl_override_source_sha256':overrides['source_sha256'],'cpl_override_count':len(overrides['overrides']),'panel_workflow':'Single-piece BOM/CPL, JLC-assisted panel/carrier subject to acceptance; no fabricated array data','gerber_layers':['F.Cu','In1.Cu','In2.Cu','In3.Cu','In4.Cu','B.Cu','F.Mask','B.Mask','F.SilkS','B.SilkS','F.Paste','B.Paste','Edge.Cuts']};(OUT/'export-verification.json').write_text(json.dumps(notes,indent=2))
manifest={str(q.relative_to(OUT)):hashlib.sha256(q.read_bytes()).hexdigest() for q in OUT.rglob('*') if q.is_file() and q.name!='SHA256_MANIFEST.json'};(OUT/'SHA256_MANIFEST.json').write_text(json.dumps(manifest,indent=2));print(json.dumps(notes,indent=2))
