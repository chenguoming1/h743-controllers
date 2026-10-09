#!/usr/bin/env python3
"""Check v7 compact packets and optionally replay their native, add-only imports.

--base-project is the immutable accepted62 paired project. --historical-workspace
supplies independent historical native exports for exact geometry comparison.
No Java, router, refill, loaded solve, or native DRC is launched.
"""
import argparse,collections,hashlib,json,os,shutil,subprocess,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p):return json.loads(Path(p).read_text())
def write(p,d):p.write_text(json.dumps(d,indent=2)+'\n')
def run(args,ok=True):
 p=subprocess.run([str(x)for x in args],cwd=ROOT,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'),capture_output=True,text=True)
 assert (p.returncode==0)==ok,(args,p.stdout,p.stderr)
 return p

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--base-project',type=Path,required=True);ap.add_argument('--historical-workspace',type=Path,required=True);ap.add_argument('--kicad-python',type=Path);a=ap.parse_args()
 maps=load(ROOT/'checks/v7-portable-projections.json')['files'];rows=[]
 with tempfile.TemporaryDirectory(prefix='v7-replay-',dir=ROOT.parent)as temp:
  tmp=Path(temp)
  for c,opens in [(20,65),(21,63),(22,62)]:
   packet=ROOT/f'sessions/accepted{opens}';identity=load(packet/'source-identity.json');source=tmp/f'source{c-1}'
   run([sys.executable,'-B','sessions/recovery62/rebuild_historical_source.py','project','--base-project',a.base_project,'--source',f'candidate{c-1}','--out',source])
   board=source/'f722-heli.kicad_pcb';assert sha(board)==identity['board_sha256']
   verify=tmp/f'packet{c}.json';run([sys.executable,'-B','tests/verify_session_packet.py','--packet',packet,'--out',verify]);result=load(verify)
   for filename,hkey,pkey in [('original-import-contract.json','historical_original_import_contract_sha256','original_import_contract_sha256'),('input-proposal.json','historical_input_proposal_sha256','input_proposal_sha256')]:
    entry=maps[str((packet/filename).relative_to(ROOT))]
    assert entry['historical_file_sha256']==identity[hkey]
    assert entry['portable_file_sha256']==identity[pkey]==sha(packet/filename)
   original=load(packet/'original-import-contract.json');contract=load(packet/'import-contract.json');report=load(packet/'engine-report.json')
   assert all(original[k]==v for k,v in contract.items())
   assert contract['mutable_source_ids']==contract['regenerable_reference_zones']==[]
   assert report['route_solver_used']is False
   assert result['mutable_route_segments']==identity['new_tracks']and result['mutable_route_vias']==0
   if c>20:
    construction=load(packet/'historical-construction.json')
    assert construction['proposal_sha256']==identity['historical_input_proposal_sha256']
    assert construction['preparer_sha256']==sha(ROOT/'prepare_screened_local.py')
    assert construction['model_sha256']==identity['model_sha256']and construction['session_sha256']==identity['session_sha256']
   projection=tmp/f'projection{c}'
   run([sys.executable,'-B','prepare_session_replay.py','--packet',packet,'--source-board',board,'--out',projection])
   projected=load(projection/'model.json');projected_report=load(projection/'engine-report.json')
   assert projected_report['model_sha256']==sha(projection/'model.json')
   assert projected_report['origin_model_sha256']==identity['model_sha256']
   assert projected_report['origin_engine_report_sha256']==identity['engine_report_sha256']
   wrong=tmp/f'wrong{c}.kicad_pcb';wrong.write_bytes(board.read_bytes()+b'\n')
   run([sys.executable,'-B','prepare_session_replay.py','--packet',packet,'--source-board',wrong,'--out',tmp/f'wrong{c}'],False)
   tampered=tmp/f'tamper{c}';shutil.copytree(packet,tampered);(tampered/'session.ses').write_bytes((tampered/'session.ses').read_bytes()+b'\n')
   run([sys.executable,'-B','prepare_session_replay.py','--packet',tampered,'--source-board',board,'--out',tmp/f'tamper-out{c}'],False)
   result.update(packet=f'sessions/accepted{opens}',recovery_exact=True,projection_rebind_verified=True,wrong_source_rejected=True,tampered_session_rejected=True,portable_hash_mapping_verified=True,scope='Packet identity, SES/report geometry, exact source recovery and importer projection; native replay only when explicitly reported.')
   if a.kicad_python:
    dest=tmp/f'native{c}';shutil.copytree(source,dest);out=dest/'f722-heli.kicad_pcb'
    run([a.kicad_python,'-B','import_session.py','--model',projection/'model.json','--session',packet/'session.ses','--engine-report',projection/'engine-report.json','--out',out])
    imported=load(out.with_suffix('.import.json'));native=load(out.with_suffix('.native.json'));expected=load(a.historical_workspace/f'candidate{c}/f722-heli.native.json')
    oldmap=contract['source_logical_nets'];newids=set(imported['logical_route_map'])-set(oldmap);expectedids=set(load(a.historical_workspace/f'candidate{c}/f722-heli.logical-route-map.json')['logical_route_map'])-set(oldmap)
    assert len(newids)==len(expectedids)==identity['new_tracks']
    def canon(objects,ids):return collections.Counter(json.dumps({k:v for k,v in o.items()if k!='uuid' or o['uuid']not in ids},sort_keys=True,separators=(',',':'))for o in objects)
    assert canon(native['objects'],newids)==canon(expected['objects'],expectedids)
    for key in ['zones','footprints','edge_cuts','copper_layers','copper_layer_ids','board_thickness_mm','outline_with_npth']:assert native[key]==expected[key],key
    assert all(imported['logical_route_map'][k]==v for k,v in oldmap.items())
    assert imported['routes_removed']==0 and not imported['reference_plane_refill_performed']
    result.update(native_replay_executed=True,replayed_board_sha256=sha(out),replayed_native_sha256=sha(out.with_suffix('.native.json')),native_import_receipt_sha256=sha(out.with_suffix('.import.json')),fixed_source_objects_preserved=imported['fixed_objects_preserved'],reference_refill_performed=False,native_geometry_equal_ignoring_only_new_route_UUIDs=True,existing_logical_route_UUIDs_and_nets_exact=True,all_saved_zones_footprints_outline_layers_exact=True,native_drc_reexecuted=False)
   write(ROOT/f'checks/accepted{opens}-v7-replay-verified.json',result);rows.append(result)
   print(json.dumps({'accepted':opens,'passed':True,'native_replay':bool(a.kicad_python)}),flush=True)
 write(ROOT/'checks/v7-replay-controls.json',{'passed':True,'verifier_source_sha256':sha(__file__),'packets':[r['packet']for r in rows],'wrong_source_controls':3,'tampered_session_controls':3,'exact_source_recoveries':3,'native_imports_reexecuted':len(rows)if a.kicad_python else 0,'no_JVM_router_refill_DRC_or_loaded_solve':True})
if __name__=='__main__':main()
