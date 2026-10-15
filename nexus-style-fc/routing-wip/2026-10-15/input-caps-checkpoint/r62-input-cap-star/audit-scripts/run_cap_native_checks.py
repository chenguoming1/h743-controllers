from pathlib import Path
import json,hashlib,shutil,subprocess,datetime,collections
R=Path('/workspace/scratch/8a35c1f26232/nexus-recovery-20261015');O=R/'routing-continuation/r62-input-cap-star';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();cli=R/'runtime/kicad-cli';py=R/'runtime/python';receipt=[]
def run(n,cmd,expected):
 st=datetime.datetime.now(datetime.timezone.utc).isoformat()
 with (O/(n+'.log')).open('w') as f:p=subprocess.run(['timeout','--signal=INT','--kill-after=5s','150s']+list(map(str,cmd)),stdout=f,stderr=subprocess.STDOUT)
 receipt.append({'name':n,'command':list(map(str,cmd)),'started_utc':st,'finished_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'exit_code':p.returncode});(O/'native-check-execution.json').write_text(json.dumps(receipt,indent=2)+'\n');print(n,p.returncode,flush=True);assert p.returncode==expected
run('post-refill-source-scope',[py,R/'routing-continuation/scripts/preflight_cap_star.py',O],0)
run('fresh-erc',[cli,'sch','erc','--format','json','--severity-all','--exit-code-violations','-o',O/'native-erc.json',O/'hardware/nexus-style-fc.kicad_sch'],0)
run('fresh-netlist',[cli,'sch','export','netlist','-o',O/'final-netlist.xml',O/'hardware/nexus-style-fc.kicad_sch'],0)
D=O/'all-visible';assert not D.exists();shutil.copytree(O/'hardware',D/'hardware');pp=D/'hardware/nexus-style-fc.kicad_pro';pro=json.loads(pp.read_text());rs=pro['board']['design_settings']['rule_severities'];changes={}
for n,v in rs.items():
 if v=='ignore':changes[n]=['ignore','warning'];rs[n]='warning'
pp.write_text(json.dumps(pro,indent=2)+'\n');run('all-visible',[cli,'pcb','drc','--all-track-errors','--schematic-parity','--refill-zones','--save-board','--severity-all','--format','json','--exit-code-violations','-o',D/'native-drc.json',D/'hardware/nexus-style-fc.kicad_pcb'],5);assert sha(D/'hardware/nexus-style-fc.kicad_pcb')==sha(O/'hardware/nexus-style-fc.kicad_pcb');j=json.loads((D/'native-drc.json').read_text());out={'candidate_board_sha256':sha(O/'hardware/nexus-style-fc.kicad_pcb'),'changed_diagnostic_severities':changes,'counts':dict(collections.Counter(x['type']+':'+x['severity'] for x in j['violations'])),'opens':len(j['unconnected_items']),'parity':j['schematic_parity'],'drc_sha256':sha(D/'native-drc.json')};(D/'diagnostic-receipt.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out),flush=True)
for label,Q in [('before',R/'routing-continuation/r61-six-clearances'),('after',O)]:
 out=O/'mask-paste'/label;out.mkdir(parents=True);run('mask-'+label,[cli,'pcb','export','gerbers','--layers','F.Mask,B.Mask,F.Paste,B.Paste','-o',str(out)+'/',Q/'hardware/nexus-style-fc.kicad_pcb'],0)
