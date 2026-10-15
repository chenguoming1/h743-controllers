from pathlib import Path
import json,hashlib,sys,importlib.util,shutil
import pcbnew as k
R=Path('/workspace/scratch/8a35c1f26232/nexus-recovery-20261015');O=Path(sys.argv[1]);tr=json.loads((O/'transaction.json').read_text());S=Path(tr['source_directory']);sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();binding=json.loads((O/'current-main-binding.json').read_text())
def load(name,p):
 spec=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m
files={f['path']:f for f in binding['files']};design=files['nexus-style-fc/tools/design.py'];export=files['nexus-style-fc/tools/export_fab.py']
for f in [design,export]:assert sha(Path(f['local_path']))==f['sha256']
d=load('current_design',design['local_path']);M=load('current_export',export['local_path']);M.K=str(R/'runtime/kicad-cli');assert next(p['lcsc'] for p in d.PARTS if p['ref']=='C19')=='C19702'
boards=[k.LoadBoard(str(X/'hardware/nexus-style-fc.kicad_pcb')) for X in [S,O]]
def selected(b):return sorted((f.GetReference(),f.GetValue(),str(f.GetFPID().GetLibNickname())+':'+str(f.GetFPID().GetLibItemName()),f.GetField('LCSC').GetText() if f.HasField('LCSC') else '') for f in b.GetFootprints())
assert selected(boards[0])==selected(boards[1]);assert next(t for t in selected(boards[1]) if t[0]=='U10')[1:]==('TPS70933DBVR','NexusFC:SOT-23-5_L3.0-W1.7-P0.95-LS2.8-BL','C89347')
for label,D in [('before',S),('after',O)]:
 out=O/'export-equality'/label;out.mkdir(parents=True,exist_ok=True);M.bom_cpl('nexus-style-fc',str(D/'hardware/nexus-style-fc.kicad_pcb'),'current_design',str(out))
proof=[]
for n in ['nexus-style-fc-bom-jlc.csv','nexus-style-fc-cpl-jlc.csv']:
 a=O/'export-equality/before'/n;b=O/'export-equality/after'/n;assert a.read_bytes()==b.read_bytes();proof.append({'file':n,'before_sha256':sha(a),'after_sha256':sha(b),'byte_equal':True})
out={'status':'PASS: exact selected-part fields and source-bound BOM/CPL exports unchanged','source_pcb_sha256':sha(S/'hardware/nexus-style-fc.kicad_pcb'),'candidate_pcb_sha256':sha(O/'hardware/nexus-style-fc.kicad_pcb'),'design_source':design,'exporter_source':export,'selected_parts_equal':True,'selected_parts':selected(boards[1]),'exports':proof,'scope':'BOM/CPL equality check only; no Gerbers or manufacturing release created.'};(O/'export-equality.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'status':out['status'],'exports':proof},indent=2))
