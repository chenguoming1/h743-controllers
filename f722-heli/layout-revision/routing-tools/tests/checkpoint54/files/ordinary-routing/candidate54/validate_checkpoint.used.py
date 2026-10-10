import subprocess,sys,os,json,hashlib
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
R=Path(__file__).resolve().parents[3];N=R/'repo/f722-heli/layout-revision';S=N/'scripts';K=R.parent/'kicad10-runtime';D=Path(sys.argv[1]).resolve();B=D/'f722-heli.kicad_pcb';before=hashlib.sha256(B.read_bytes()).hexdigest();poses=Path(sys.argv[2]).resolve() if len(sys.argv)>2 else R/'integrated-routing/trial27/poses-native.json';env=dict(os.environ,PYTHONPATH=str(R/'python-deps'),MPLCONFIGDIR='/tmp/f722-mpl')
def run(label,args):
 with (D/(label+'.log')).open('w') as f:r=subprocess.run([str(x) for x in args],stdout=f,stderr=subprocess.STDOUT,env=env)
 return label,r.returncode
native=[('owner-critical',[K/'python',S/'check_critical_connectivity.py',B,D/'owner-critical.json']),('owner-drc-all',[K/'kicad-cli','pcb','drc','--format','json','--all-track-errors','--severity-all','--output',D/'owner-drc-all.json',B]),('owner-drc',[K/'kicad-cli','pcb','drc','--format','json','--output',D/'owner-drc.json',B]),('owner-export',[K/'python',S/'export_native_copper.py','--board',B,'--out',D/'owner-native.json']),('owner-mechanical-export',[K/'python',S/'export_mechanical_geometry.py','--board',B,'--source',R/'repo/f722-heli/hardware/f722-heli.kicad_pcb','--out',D/'owner-mechanical-geometry.json']),('owner-parity',[K/'python',S/'check_native_parity.py','--board',B,'--netlist',N/'checks/reconstructed.net','--out',D/'owner-parity.json']),('owner-firmware',[K/'python',S/'check_firmware_pinmap.py','--board',B,'--contract',R/'repo/f722-heli/validation/firmware-pinmap.json','--out',D/'owner-firmware.json'])]
if (D/'f722-heli.kicad_sch').is_file():
 native.append(('owner-drc-parity',[K/'kicad-cli','pcb','drc','--format','json','--all-track-errors','--severity-all','--schematic-parity','--output',D/'owner-drc-parity.json',B]))
with ThreadPoolExecutor(max_workers=1) as ex:results=list(ex.map(lambda a:run(*a),native))
assert all(c==0 for n,c in results if n!='owner-critical'),results
analysis=[('owner-process',[sys.executable,S/'check_via_process.py','--geometry',D/'owner-native.json','--out',D/'owner-process.json']),('owner-mechanical',[sys.executable,S/'audit_mechanical_geometry.py','--geometry',D/'owner-mechanical-geometry.json','--poses',poses,'--out',D/'owner-mechanical.json']),('owner-protection',[sys.executable,S/'check_protection_paths.py','--geometry',D/'owner-native.json','--contracts',N/'checks/protection/candidate-contracts.json','--out',D/'owner-protection.json']),('owner-supplemental',[sys.executable,S/'check_protection_paths.py','--geometry',D/'owner-native.json','--contracts',N/'checks/protection/supplemental-contracts.json','--out',D/'owner-supplemental.json'])]
with ThreadPoolExecutor(max_workers=1) as ex:results+=list(ex.map(lambda a:run(*a),analysis))
assert hashlib.sha256(B.read_bytes()).hexdigest()==before
summary={'board_sha256':before,'commands':results}
for n in ['drc','drc-all','process','mechanical','parity','firmware','protection','supplemental']:
 d=json.load(open(D/('owner-'+n+'.json')))
 if n in ['drc','drc-all']:summary[n]={'unconnected':len(d['unconnected_items']),'errors':sum(x['severity']=='error' for x in d['violations']),'warnings':sum(x['severity']=='warning' for x in d['violations'])}
 else:summary[n]={k:d[k] for k in ['passed','total','board_sha256'] if k in d}
critical=json.load(open(D/'owner-critical.json'));summary['critical']={'board_sha256':critical['board_sha256'],'connected_nets':sum(x['complete'] for x in critical['fullnet_connectivity']),'total_nets':len(critical['fullnet_connectivity']),'missing_ground_returns':[x['pad'] for x in critical['critical_ground_returns'] if not x['connected_to_ground_plane']],'faults':critical['faults']}
(D/'owner-summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary))
