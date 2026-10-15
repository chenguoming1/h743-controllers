from pathlib import Path
import json,hashlib,subprocess,datetime,shutil
R=Path('/workspace/scratch/8a35c1f26232/nexus-recovery-20261015');O=R/'u10-metadata-integration';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();cli=str(R/'runtime/kicad-cli')
def run(D,name,args,expected):
 start=datetime.datetime.now(datetime.timezone.utc).isoformat()
 with (D/(name+'.log')).open('w') as f:r=subprocess.run(args,stdout=f,stderr=subprocess.STDOUT,timeout=150)
 end=datetime.datetime.now(datetime.timezone.utc).isoformat();assert r.returncode==expected,(name,r.returncode)
 return {'argv':args,'started_utc':start,'finished_utc':end,'exit_code':r.returncode,'log_sha256':sha(D/(name+'.log'))}
C=O/'canonical';E=O/'experimental-r51';assert sha(C/'hardware/nexus-style-fc.kicad_sch')==sha(E/'hardware/nexus-style-fc.kicad_sch')=='49f9e0571424d0610e294bdcd6b120a42d04db284ecda9e660428fc587e62699'
erc=run(C,'native-erc',[cli,'sch','erc','--severity-all','--format','json','--exit-code-violations','-o',str(C/'native-erc.json'),str(C/'hardware/nexus-style-fc.kicad_sch')],0)
net=run(C,'native-netlist',[cli,'sch','export','netlist','--format','kicadxml','-o',str(C/'final-netlist.xml'),str(C/'hardware/nexus-style-fc.kicad_sch')],0)
for n in ['native-erc.json','final-netlist.xml']:shutil.copy2(C/n,E/n)
for D in [C,E]:
 receipt={'role':D.name,'transaction':json.loads((D/'transaction.json').read_text()),'erc':erc,'netlist':net,'erc_netlist_basis':'Fresh canonical run bound to exact shared unchanged schematic bytes; carried byte-for-byte to experimental'}
 receipt['drc']=run(D,'native-drc',[cli,'pcb','drc','--all-track-errors','--schematic-parity','--refill-zones','--save-board','--severity-all','--format','json','--exit-code-violations','-o',str(D/'native-drc.json'),str(D/'hardware/nexus-style-fc.kicad_pcb')],5)
 receipt['post_native_pcb_sha256']=sha(D/'hardware/nexus-style-fc.kicad_pcb');(D/'native-execution-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(D.name,receipt['post_native_pcb_sha256'],flush=True)
 run(D,'geometry-verification',[str(R/'runtime/python'),str(O/'scripts/verify_metadata.py'),str(D)],0)
