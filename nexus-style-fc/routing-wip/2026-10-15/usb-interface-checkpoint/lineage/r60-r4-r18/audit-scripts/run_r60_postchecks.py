from pathlib import Path
import json,hashlib,shutil,subprocess,datetime,collections
R=Path('/workspace/scratch/8a35c1f26232/nexus-recovery-20261015');O=R/'routing-continuation/r60-r4-r18';S=R/'routing-continuation/r59-usb170-trial';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();cli=str(R/'runtime/kicad-cli');py=str(R/'runtime/python');receipt=[]
def run(name,cmd):
 st=datetime.datetime.now(datetime.timezone.utc).isoformat()
 with (O/(name+'.log')).open('w') as f:p=subprocess.run(['timeout','--signal=INT','--kill-after=5s','150s']+cmd,stdout=f,stderr=subprocess.STDOUT)
 r={'name':name,'command':cmd,'started_utc':st,'finished_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'exit_code':p.returncode};receipt.append(r);(O/'postcheck-execution.json').write_text(json.dumps(receipt,indent=2)+'\n');print(name,p.returncode,flush=True);return p.returncode
run('ldo-returns',[py,str(R/'routing-continuation/scripts/check_ldo_continuity.py'),str(O)])
run('shield-returns',[py,str(R/'routing-continuation/scripts/check_cc1_continuity.py'),str(R/'routing-continuation/r50-cc1-spoke-preserved'),str(O),str(O/'routing-return-continuity')])
D=O/'all-visible';assert not D.exists();shutil.copytree(O/'hardware',D/'hardware');p=D/'hardware/nexus-style-fc.kicad_pro';j=json.loads(p.read_text());rs=j['board']['design_settings']['rule_severities'];changes={}
for n,v in rs.items():
 if v=='ignore':changes[n]=['ignore','warning'];rs[n]='warning'
p.write_text(json.dumps(j,indent=2)+'\n');assert run('all-visible',[cli,'pcb','drc','--all-track-errors','--schematic-parity','--refill-zones','--save-board','--severity-all','--format','json','--exit-code-violations','-o',str(D/'native-drc.json'),str(D/'hardware/nexus-style-fc.kicad_pcb')])==5
assert sha(D/'hardware/nexus-style-fc.kicad_pcb')==sha(O/'hardware/nexus-style-fc.kicad_pcb');a,b=[json.loads(p.read_text()) for p in [S/'all-visible/native-drc.json',D/'native-drc.json']];sig=lambda z:(z['type'],z['severity'],tuple(sorted(x['uuid'] for x in z['items'])));ca,cb=[collections.Counter(sig(z) for z in d['violations']) for d in [a,b]];d={'candidate_board_sha256':sha(O/'hardware/nexus-style-fc.kicad_pcb'),'changed_diagnostic_severities':changes,'counts':dict(collections.Counter(z['type']+':'+z['severity'] for z in b['violations'])),'new_findings':list((cb-ca).elements()),'removed_findings':list((ca-cb).elements()),'opens':b['unconnected_items'],'parity':b['schematic_parity'],'native_drc_sha256':sha(D/'native-drc.json'),'accepted_project_unchanged':sha(S/'hardware/nexus-style-fc.kicad_pro')==sha(O/'hardware/nexus-style-fc.kicad_pro')};(D/'diagnostic-receipt.json').write_text(json.dumps(d,indent=2)+'\n')
for label,Q in [('before',S),('after',O)]:
 out=O/'mask-paste'/label;out.mkdir(parents=True);assert run('export-mask-'+label,[cli,'pcb','export','gerbers','--layers','F.Mask,B.Mask,F.Paste,B.Paste','-o',str(out)+'/',str(Q/'hardware/nexus-style-fc.kicad_pcb')])==0
C=O/'diagnostic-in3-cam';C.mkdir();assert run('export-in3',[cli,'pcb','export','gerbers','--layers','In3.Cu','-o',str(C)+'/',str(O/'hardware/nexus-style-fc.kicad_pcb')])==0
print(json.dumps({'all_visible':d,'postchecks':receipt},indent=2))
