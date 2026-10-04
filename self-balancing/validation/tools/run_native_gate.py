#!/usr/bin/python3
"""Exact-hash P6 CAD gate. Source project stays read-only; CLI uses a clone.

No release/fabrication/export acceptance is claimed. Results cannot pass until
all independent numerical checks pass; rendered visual review remains separate.
"""
import argparse,concurrent.futures,hashlib,json,os,pathlib,shutil,subprocess,time
ap=argparse.ArgumentParser();ap.add_argument('--baseline',type=pathlib.Path,required=True);ap.add_argument('--project',type=pathlib.Path,required=True);ap.add_argument('--sha256',required=True);ap.add_argument('--out',type=pathlib.Path,required=True);ap.add_argument('--pruning-proof',type=pathlib.Path);ap.add_argument('--approved-pruning',type=pathlib.Path);ap.add_argument('--exceptions',type=pathlib.Path);ap.add_argument('--routing-patch',type=pathlib.Path,action='append',default=[]);ap.add_argument('--selfcheck',action='store_true');a=ap.parse_args();A=a.baseline.resolve();B=a.project.resolve();O=a.out.resolve();O.mkdir(parents=True,exist_ok=True);T=pathlib.Path(__file__).resolve().parent;C=O/'cli-snapshot';F=T/'frozen-tools';PY='/usr/bin/python3';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();P5='6e2031b040ce8f3a534c2f73abb0091e25b3e6adcab982463264ad8898d65cf8'
assert sha(A/'controller.kicad_pcb')==P5 and sha(B/'controller.kicad_pcb')==a.sha256
assert a.selfcheck or a.sha256!=P5,'P5 baseline cannot certify a P6 cleanup'
packet_hashes={str(q.resolve()):sha(q) for q in a.routing_patch+([a.exceptions] if a.exceptions else [])+([a.approved_pruning,a.pruning_proof] if a.approved_pruning else [])}
tool_hashes={str(q):sha(q) for q in list(T.glob('*.py'))+[r for r in F.iterdir() if r.is_file()]}
assert not C.exists(),'Use a new output directory for immutable audit evidence'
C.mkdir();paths=list(B.glob('*.kicad*'))+[B/'fp-lib-table',B/'sym-lib-table']
for sub in ['library','inputs','tools']:
 paths += [q for q in (B/sub).rglob('*') if q.is_file() and '__pycache__' not in q.parts]
for rel in ['design-netmap.json','controller-netlist.xml','controller-r3s-independent-expectations.json','bom-draft.csv','manufacturing-profile.json','sourcing/controller-r3s-bom-source-status.json','sourcing/controller-r3s-bom-source-status.csv']:
 paths.append(B/'review'/rel)
source_hashes={str(q):sha(q) for q in paths}
for q in paths:
 dest=C/q.relative_to(B);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(q,dest)
cli=['sh',str(F/'kicad_cli.sh')];env=os.environ.copy();env.update(KICAD_CONFIG_HOME='/tmp/controller-r3-kicad',XDG_CACHE_HOME='/tmp/controller-r3-cache',XDG_DATA_HOME='/tmp/controller-r3-data')
cmds={
 'geometry':[PY,str(T/'check_revision_geometry.py'),'--baseline',str(A),'--project',str(B),'--sha256',a.sha256,'--out',str(O)]+(['--exceptions',str(a.exceptions)] if a.exceptions else [])+(['--selfcheck'] if a.selfcheck else []),
 'topology':[PY,str(T/'check_connectivity_topology.py'),'--baseline',str(A/'controller.kicad_pcb'),'--candidate',str(B/'controller.kicad_pcb'),'--sha256',a.sha256,'--out',str(O/'topology.json')]+(['--exceptions',str(a.exceptions)] if a.exceptions else [])+(['--selfcheck'] if a.selfcheck else []),
 'copper-census':[PY,str(F/'audit_width_spacing.py'),str(B/'controller.kicad_pcb'),'--sha256',a.sha256,'--out',str(O/'uncapped-copper-census.json')],
 'advisories':[PY,str(T/'check_advisories.py'),'--candidate',str(C/'controller.kicad_pcb'),'--sha256',a.sha256,'--out',str(O/'advisories')],
 'current-geometry':[PY,str(F/'check_current_geometry.py'),'--project',str(B),'--out',str(O/'current-geometry'),'--approved-small-vias',str(B/'review/approved-small-vias.json')],
 'refill':[PY,str(T/'check_refill.py'),'--candidate',str(B/'controller.kicad_pcb'),'--sha256',a.sha256,'--out',str(O/'refill-verification.json')],
 'erc':cli+['sch','erc','--format','json','--severity-all','--output',str(O/'erc.json'),str(C/'controller.kicad_sch')],
 'drc':cli+['pcb','drc','--format','json','--severity-all','--all-track-errors','--schematic-parity','--output',str(O/'drc.json'),str(C/'controller.kicad_pcb')],
 'native-audit':[PY,str(F/'audit_native.py'),'--project',str(B),'--cli-project',str(C),'--out',str(O)],
 'route-replay':[PY,str(T/'check_route_replay.py'),'--baseline',str(A/'controller.kicad_pcb'),'--candidate',str(B/'controller.kicad_pcb'),'--sha256',a.sha256,'--out',str(O/'route-replay.json')]+[v for q in a.routing_patch for v in ['--patch',str(q)]]+(['--approved-pruning',str(a.approved_pruning),'--pruning-proof',str(a.pruning_proof)] if a.approved_pruning else [])+(['--exceptions',str(a.exceptions)] if a.exceptions else [])+(['--selfcheck'] if a.selfcheck else []),
 'route-quality':[PY,str(T/'audit_route_quality.py'),'--baseline',str(A/'controller.kicad_pcb'),'--candidate',str(B/'controller.kicad_pcb'),'--sha256',a.sha256,'--out',str(O/'route-quality')],
 'render':[PY,str(T/'render_native_review.py'),'--candidate',str(C/'controller.kicad_pcb'),'--sha256',a.sha256,'--out',str(O/'renders')],
}
def run(item):
 name,cmd=item;start=time.time()
 with (O/(name+'-run.log')).open('w') as f:proc=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,env=env)
 row={'command':cmd,'returncode':proc.returncode,'elapsed_seconds':time.time()-start};print(json.dumps({'stage':name,**row}),flush=True);return name,row
# Independent subprocesses only; each writes its own report. CLI project remains fixed.
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:results=dict(pool.map(run,cmds.items()))
# Regenerate XML using a separate clone after ERC/DRC complete; source XML is untouched.
netlist_cmd=cli+['sch','export','netlist','--format','kicadxml','--output',str(C/'review/controller-netlist.xml'),str(C/'controller.kicad_sch')]
results.update([run(('fresh-netlist',netlist_cmd))])
results.update([run(('pin-audit',[PY,str(F/'audit_controller_r3s_independent.py'),str(C),str(B/'controller.kicad_pcb'),str(A/'review/controller-r3s-independent-expectations.json')]))])
errors=[name+' process failed' for name,r in results.items() if r['returncode']]
def read(name):
 try:return json.loads((O/name).read_text())
 except Exception as e:errors.append(name+' unavailable: '+str(e));return {}
census=read('uncapped-copper-census.json');summary=census.get('summary',{})
for field in ['narrow_track_count','baseline_foreign_copper_pairs_below_target','filled_zone_item_hits_below_target_or_widening']:
 if summary.get(field)!=0:errors.append('Copper census '+field+' nonzero/missing')
usb=[q for q in census.get('items',{}).values() if q.get('protected_usb')]
if len(usb)!=27 or any(q['width_mm']!=.1392 for q in usb):errors.append('USB 0.1392mm exact width differs')
erc=read('erc.json');drc=read('drc.json');counts={'ERC':sum(len(s.get('violations',[])) for s in erc.get('sheets',[])),'DRC':len(drc.get('violations',[])),'opens':len(drc.get('unconnected_items',[])),'parity':len(drc.get('schematic_parity',[]))}
if any(counts.values()):errors.append('Fresh full native ERC/DRC/parity/opens not zero')
if not {'violations','unconnected_items','schematic_parity'}<=drc.keys() or 'sheets' not in erc:errors.append('Incomplete fresh native reports')
pin=read('pin-audit-run.log')
if pin.get('errors') or pin.get('unexpected_map_entries') or pin.get('expected_pin_entries')!=405:errors.append('Independent 405-pin map check failed')
for name in ['route-replay.json','revision-geometry.json','topology.json','refill-verification.json','native-audit.json','advisories/advisory-clearance-census.json','current-geometry/current-geometry-audit.json']:
 report=read(name)
 if report.get('errors'):errors.append(name+' contains errors')
source_stable=all(q.exists() and sha(q)==h for q,h in [(pathlib.Path(k),v) for k,v in source_hashes.items()])
if not source_stable:errors.append('Source project changed during checks')
if any(sha(pathlib.Path(q))!=h for q,h in tool_hashes.items()):errors.append('Validation tool changed during checks')
if any(sha(pathlib.Path(q))!=h for q,h in packet_hashes.items()):errors.append('Approved operation/exception evidence changed during checks')
report={'status':('BASELINE FULL HARNESS SELF-CHECK PASS; NOT P6 ACCEPTANCE' if a.selfcheck else 'PASS P6 NUMERICAL CAD GATE; VISUAL REVIEW PENDING') if not errors else 'NOT PASSED','baseline_sha256':P5,'candidate_sha256':a.sha256,'source_stable':source_stable,'errors':errors,'native_counts':counts,'copper_summary':summary,'protected_USB_tracks':len(usb),'independent_pin_entries':pin.get('expected_pin_entries'),'processes':results,'source_sha256':source_hashes,'validation_tools_sha256':tool_hashes,'operation_exception_packets_sha256':packet_hashes,'scope':'Read-only independent CAD validation. Whole-board rendered review is still required. Fabrication exports, supplier acceptance and physical hardware performance are separate.'}
(O/'native-gate-summary.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k not in ['source_sha256','validation_tools_sha256','processes']},indent=2));raise SystemExit(bool(errors))
