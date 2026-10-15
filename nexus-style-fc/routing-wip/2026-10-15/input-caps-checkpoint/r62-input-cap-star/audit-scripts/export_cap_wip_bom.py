from pathlib import Path
import sys,importlib.util,json,hashlib
R=Path('/workspace/scratch/8a35c1f26232/nexus-recovery-20261015');O=R/'routing-continuation/r62-input-cap-star';label=sys.argv[1];T=O/'tools' if label=='candidate' else Path('/workspace/scratch/8a35c1f26232/nexus-c27-parallel-successor/baseline/nexus-style-fc/tools');P=O/'hardware/nexus-style-fc.kicad_pcb' if label=='candidate' else R/'routing-continuation/r61-six-clearances/hardware/nexus-style-fc.kicad_pcb';
if label=='source':
 binding=json.loads((R/'current-main-binding-15.json').read_text())
 for n in ['design.py','export_fab.py']:
  ref=next(q for q in binding['files'] if q['path']=='nexus-style-fc/tools/'+n);assert hashlib.sha256((T/n).read_bytes()).hexdigest()==ref['sha256']
D=O/'wip-bom-cpl'/label;D.mkdir(parents=True,exist_ok=False);sys.path.insert(0,str(T));spec=importlib.util.spec_from_file_location('export_fab',T/'export_fab.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);m.K=str(R/'runtime/kicad-cli');m.bom_cpl('nexus-style-fc',str(P),'design',str(D));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();(D/'source-binding.json').write_text(json.dumps({'board':str(P),'board_sha256':sha(P),'exporter_sha256':sha(T/'export_fab.py'),'design_sha256':sha(T/'design.py'),'runtime_cli':m.K,'method':'Exact reviewed bom_cpl implementation; only executable path points to approved Linux KiCad 10.0.7 wrapper. Real native position export, no stub; BOM/CPL diagnostic only, no release CAM.'},indent=2)+'\n')
