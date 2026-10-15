"""Integrate a frozen readable schematic and run source-bound native EN checks."""
from pathlib import Path
import argparse,datetime,hashlib,json,shutil,subprocess,sys
p=argparse.ArgumentParser();p.add_argument('schematic',type=Path);p.add_argument('sha256');a=p.parse_args()
R=Path('/workspace/scratch/8a35c1f26232/nexus-recovery-20261015');L=R/'pcb-lane';S=Path(__file__).parent;sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();assert sha(a.schematic)==a.sha256
cli=str(R/'runtime/kicad-cli');py=str(R/'runtime/python');validator=R/'latest-main/nexus-style-fc/tools/validate_nexus_reroute.py'
def run(argv,log):
 start=datetime.datetime.now(datetime.timezone.utc).isoformat()
 with log.open('w') as f:r=subprocess.run(argv,stdout=f,stderr=subprocess.STDOUT)
 return {'argv':argv,'exit_code':r.returncode,'started_utc':start,'finished_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'log':str(log),'log_sha256':sha(log)}
for tag in ['canonical','experimental']:
 O=L/(tag+'-en');B=L/('rollback-'+tag);pcb=O/'hardware/nexus-style-fc.kicad_pcb';sch=O/'hardware/nexus-style-fc.kicad_sch';pre=O/'final-pre-refill';pre.mkdir(exist_ok=True)
 assert not (O/'native-execution-receipt.json').exists(),'Refuse uncertain duplicate final run; inspect receipt and exact file state first'
 shutil.copy2(pcb,pre/pcb.name);shutil.copy2(a.schematic,sch);assert sha(sch)==a.sha256
 receipt={'source_main_commit':'866afe8f44523b0c8f3dc4360f83fdee599c77c9','source_pcb_sha256':sha(B/'hardware/nexus-style-fc.kicad_pcb'),'pre_refill_pcb_sha256':sha(pcb),'schematic_sha256':sha(sch),'project_sha256':sha(O/'hardware/nexus-style-fc.kicad_pro'),'rules_sha256':sha(O/'hardware/nexus-style-fc.kicad_dru')}
 receipt['erc']=run(['timeout','--signal=INT','--kill-after=5s','150s',cli,'sch','erc','--severity-all','--format','json','--exit-code-violations','-o',str(O/'native-erc.json'),str(sch)],O/'native-erc.log');assert receipt['erc']['exit_code']==0,receipt['erc']
 receipt['netlist']=run(['timeout','--signal=INT','--kill-after=5s','150s',cli,'sch','export','netlist','--format','kicadxml','-o',str(O/'final-netlist.xml'),str(sch)],O/'native-netlist.log');assert receipt['netlist']['exit_code']==0,receipt['netlist']
 receipt['drc']=run(['timeout','--signal=INT','--kill-after=5s','150s',cli,'pcb','drc','--all-track-errors','--schematic-parity','--refill-zones','--save-board','--severity-all','--format','json','--exit-code-violations','-o',str(O/'native-drc.json'),str(pcb)],O/'native-drc.log');receipt['saved_board_sha256']=sha(pcb);(O/'native-execution-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');assert receipt['drc']['exit_code']==5,receipt['drc']
 geometry=run(['timeout','--signal=INT','--kill-after=5s','150s',py,str(S/'verify_en_native.py'),str(B/'hardware/nexus-style-fc.kicad_pcb'),str(pcb),str(O/'hardware/nexus-style-fc.en-transaction.json'),str(O/'final-en-geometry.json'),'--validator',str(validator)],O/'final-en-geometry.log');assert geometry['exit_code']==0,geometry;receipt['geometry']=geometry;(O/'native-execution-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
 d=json.loads((O/'native-drc.json').read_text());print(json.dumps({'state':tag,'pcb_sha256':sha(pcb),'errors':sum(z['severity']=='error' for z in d['violations']),'warnings':sum(z['severity']=='warning' for z in d['violations']),'opens':len(d['unconnected_items']),'parity':len(d['schematic_parity'])}),flush=True)
assert sha(a.schematic)==a.sha256
result=run([sys.executable,str(S/'seal_integrated_en.py')],L/'final-seal.log');assert result['exit_code']==0,result
print((L/'final-summary.json').read_text(),flush=True)
