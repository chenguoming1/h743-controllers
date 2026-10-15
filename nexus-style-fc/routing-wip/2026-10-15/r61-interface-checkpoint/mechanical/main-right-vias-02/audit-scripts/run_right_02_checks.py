from pathlib import Path
import subprocess,json,datetime
R=Path('/workspace/scratch/8a35c1f26232/nexus-recovery-20261015');L=R/'mechanical-integration';O=L/'main-right-vias-02';records=[]
def run(n,c):
 st=datetime.datetime.now(datetime.timezone.utc).isoformat()
 with (O/(n+'.log')).open('w') as f:p=subprocess.run(['timeout','--signal=INT','--kill-after=5s','150s']+list(map(str,c)),stdout=f,stderr=subprocess.STDOUT)
 records.append({'name':n,'command':list(map(str,c)),'started_utc':st,'finished_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'exit_code':p.returncode});(O/'postcheck-execution.json').write_text(json.dumps(records,indent=2)+'\n');print(n,p.returncode,flush=True);assert p.returncode==0
py=R/'runtime/python';cli=R/'runtime/kicad-cli'
run('ldo-returns',[py,L/'study/mechanical_check_ldo_continuity.py',O]);run('shield-returns',[py,R/'routing-continuation/scripts/check_cc1_continuity.py',R/'routing-continuation/r50-cc1-spoke-preserved',O,O/'routing-return-continuity']);run('usb-reference-returns',[py,L/'study/mechanical_check_usb_reference_returns.py',O])
for lab,S in [('before',L/'r61-replay/native-baseline'),('after',O)]:
 D=O/'mask-paste'/lab;D.mkdir(parents=True);run('mask-'+lab,[cli,'pcb','export','gerbers','--layers','F.Mask,B.Mask,F.Paste,B.Paste','-o',str(D)+'/',S/'hardware/nexus-style-fc.kicad_pcb'])
