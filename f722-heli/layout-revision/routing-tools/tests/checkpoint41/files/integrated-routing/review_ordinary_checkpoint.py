"""Read-only owner review of sealed ordinary-route candidates; no acceptance or qualification."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import argparse,json,hashlib,subprocess,os,sys
if sys.flags.optimize:raise RuntimeError('Validation requires Python assertions enabled')
R=Path(__file__).resolve().parents[1];N=R/'repo/f722-heli/layout-revision';K=R.parent/'kicad10-runtime';T=N/'signal-review/native'
p=argparse.ArgumentParser();p.add_argument('candidate',type=Path);p.add_argument('previous',type=Path);p.add_argument('previous_review',type=Path);p.add_argument('review',type=Path);p.add_argument('--net',action='append',required=True);p.add_argument('--coordinated',action='store_true');p.add_argument('--footprint-translations',type=Path);a=p.parse_args()
assert not a.footprint_translations or a.coordinated,'Translations require declared coordinated integration';D=a.candidate.resolve();O=a.previous.resolve();S=a.review.resolve();P=a.previous_review.resolve();S.mkdir(exist_ok=True)
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
b=D/'f722-heli.kicad_pcb';h=sha(b);old=sha(O/'f722-heli.kicad_pcb');n=read(D/'owner-summary.json')['drc']['unconnected'];prior=read(O/'owner-summary.json')['drc']['unconnected'];handoff=read(D/'route-handoff.json');assert handoff['board_sha256']==h
for name,digest in handoff.get('files',{}).items():assert sha(D/name)==digest,name
summary=read(D/'owner-summary.json');assert summary['board_sha256']==h and summary['drc']==summary['drc-all'] and summary['drc']['errors']==summary['drc']['warnings']==0
assert not read(D/'owner-drc-parity.json')['schematic_parity']
for key in ['process','mechanical','parity','firmware']:assert summary[key]['passed'] and summary[key]['board_sha256']==h
assert not summary['critical']['faults'] and summary['critical']['connected_nets']==summary['critical']['total_nets']==16
assert read(D/'endpoint-audit.json').get('passed') is True
E=dict(os.environ,PYTHONPATH=str(R/'python-deps'))
def run(label,args,allowed=(0,)):
 with (S/(label+'.log')).open('w') as f:q=subprocess.run([str(v) for v in args],stdout=f,stderr=subprocess.STDOUT,env=E)
 if q.returncode not in allowed:raise RuntimeError((label,q.returncode))
 return {'command':label,'exit_code':q.returncode}
run('export',[K/'python',T/'export_signal_snapshot.py','--board',b,'--native-tools-dir',N/'scripts','--out',S/'snapshot'])
integration_kind='coordinated' if a.coordinated else 'additive'
add=[K/'python',R/f'integrated-routing/check_{integration_kind}_integration.py',O/'f722-heli.kicad_pcb',b,'--out',S/f'owner-{integration_kind}-integration.json']
for net in a.net:add+=['--net',net]
if a.footprint_translations:add+=['--footprint-translations',a.footprint_translations]
checks=[(integration_kind,add,(0,)),('reference',[sys.executable,T/'check_critical_reference.py','--board',b,'--snapshot',S/'snapshot','--out',S/'snapshot/critical-reference.json'],(0,)),('i2c',[sys.executable,T/'check_signal_geometry.py','--board',b,'--snapshot',S/'snapshot','--out',S/'current-review.json','--profile',T/'model-inputs.template.json','--critical-check',D/'owner-critical.json','--requirements',N/'signal-review/final-native-i2c-requirements.json','--calculations',N/'signal-review/stock-i2c-calculations.json'],(0,2)),('actual-io22',[sys.executable,N/'protection-review/tools/check_protection_paths.py','--geometry',D/'owner-native.json','--contracts',N/'protection-review/contracts/actual-io22.json','--out',S/'actual-io22.json'],(0,1)),('spi',[K/'python',N/'checks/bind_stock_spi_review.py','--board',b,'--parts',D/'parts.json','--packet',N/'spi-review','--out',S/'stock-spi-binding.json'],(0,))]
with ThreadPoolExecutor(max_workers=3) as ex:results=list(ex.map(lambda x:run(*x),checks))
run('comparison',[sys.executable,T/'compare_reference_geometry.py','--before',P/'snapshot','--after',S/'snapshot','--before-board',O/'f722-heli.kicad_pcb','--after-board',b,'--out',S/f'comparison-{prior}-to-{n}.json'])
assert sha(b)==h and sha(O/'f722-heli.kicad_pcb')==old
for name in ['current-review.json','actual-io22.json','stock-spi-binding.json']:assert read(S/name)['board_sha256']==h
r={'board_sha256':h,'previous_board_sha256':old,'native_count':n,'sealed_native_receipts_verified':True,'commands':results,'scope':'Read-only review. I2C/protection refusal codes may be expected on incomplete routes; owner must assess outputs before adoption. No numerical power or physical qualification.'};(S/'owner-review-run.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r))
