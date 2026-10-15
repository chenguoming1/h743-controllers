"""Export a local, explicitly unreleased review package from a sealed project.
No upload, ordering, quoting or external service access. The exact repository
exporter is invoked with its native CLI binding and captured subprocess logs.
"""
from pathlib import Path
import sys,json,hashlib,importlib.util,subprocess,datetime,shutil
R=Path('/workspace/scratch/8a35c1f26232/nexus-recovery-20261015');C=Path(sys.argv[1]).resolve();O=Path(sys.argv[2]).resolve();assert not O.exists();assert (C/'FINAL-SEAL.json').is_file()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();seal=json.loads((C/'FINAL-SEAL.json').read_text());assert seal['status'].startswith('ACCEPTED')
sys.path.insert(0,str(C/'tools'));spec=importlib.util.spec_from_file_location('source_bound_review_exporter',C/'tools/export_fab.py');E=importlib.util.module_from_spec(spec);spec.loader.exec_module(E)
assert sha(C/'tools/export_fab.py')==sha(R/'mechanical-integration/main-signal-slot-08/tools/export_fab.py'),'Exporter unexpectedly changed'
K=R/'runtime/kicad-cli';E.K=str(K);O.mkdir();receipts=[];sources=[]
for p in sorted((C/'hardware').rglob('*')):
 if p.is_file() and '__pycache__' not in p.parts:sources.append({'path':str(p.relative_to(C)),'sha256':sha(p)})
for p in sorted((C/'tools').glob('*.py')):sources.append({'path':str(p.relative_to(C)),'sha256':sha(p)})
def run(*args):
 i=len(receipts);start=datetime.datetime.now(datetime.timezone.utc).isoformat();p=subprocess.run([str(K),*map(str,args)],text=True,capture_output=True,timeout=120);log=f'native-{i:02d}.log';(O/log).write_text(p.stdout+p.stderr);receipts.append({'command':[str(K),*map(str,args)],'started_utc':start,'finished_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'exit_code':p.returncode,'log':log});assert p.returncode==0,(args,p.returncode,p.stderr)
E.run=run
for name,relative,mod,ncu in E.BOARDS:
 out=O/name;out.mkdir();gdir=out/'gerbers';gdir.mkdir();board=C/relative;E.export_gerbers(name,str(board),ncu,str(out),str(gdir));E.bom_cpl(name,str(board),mod,str(out));print('exported',name,flush=True)
for row in sources:assert sha(C/row['path'])==row['sha256'],('Source mutation',row['path'])
sys.path.insert(0,str(R/'assembly-annotation-cleanup'));import guarded_cleanup as G
boards=[]
for name,relative,mod,ncu in E.BOARDS:
 b=G.parse((C/relative).read_text());setup=b.one('setup');stack=setup.children('stackup');aux=setup.children('aux_axis_origin');boards.append({'project':name,'board_path':relative,'board_sha256':sha(C/relative),'copper_layers':ncu,'general':b.one('general').value(),'stackup':stack[0].value() if stack else None,'aux_axis_origin':aux[0].value() if aux else None,'setup_exact':setup.value(),'exported_layers':E.layers(ncu)})
settings=[]
for p in sorted((C/'hardware').rglob('*')):
 if p.suffix in ['.kicad_pro','.kicad_dru']:
  dest=O/'declared-source-settings'/p.relative_to(C/'hardware');dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest);settings.append({'source':str(p.relative_to(C)),'sha256':sha(p),'copy':str(dest.relative_to(O))})
shutil.copy2(C/'manufacturing-project.kicad_pro',O/'declared-source-settings/manufacturing-project.kicad_pro')
manifest={'status':'UNRELEASED local manufacturing review package; export only, no ordering or fabrication approval inferred','sealed_source':str(C),'seal_sha256':sha(C/'FINAL-SEAL.json'),'source_manifest_sha256':sha(C/'evidence-manifest.json'),'exporter_sha256':sha(C/'tools/export_fab.py'),'native_version':subprocess.check_output([str(K),'--version'],text=True).strip(),'source_files_unchanged':sources,'boards':boards,'settings':settings,'receipts':receipts,'export_options':'Source exporter: RS-274X, no X2/netlist attributes, mask subtracted from silk, Gerber 4.6 mm default, drill/place auxiliary origin, decimal-mm Excellon, independent PTH/NPTH, oval route mode. Copper zones are already native-refilled in the sealed source; no export-time refill.','qualifications':['Manufacturing tolerances, actual stack and USB impedance need vendor confirmation.','16 main pasted-via locations, thermal-pad processing and under-body tenting remain unqualified.','Slot/tab strength, fixture registration and solder/current qualification remain open.','Power/transient/HF/thermal and assembly polarity/process require review; this output is not a fabrication release.']}
(O/'source-and-settings.json').write_text(json.dumps(manifest,indent=2)+'\n');shutil.copy2(__file__,O/Path(__file__).name);print(json.dumps({'status':manifest['status'],'path':str(O),'boards':[q['board_sha256'] for q in boards]},indent=2))
