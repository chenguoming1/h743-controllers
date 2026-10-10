#!/usr/bin/env python3
"""Read-only packet consistency using only the importer's pure SES functions."""
import ast,collections,hashlib,json,pathlib,re
HERE=pathlib.Path(__file__).resolve().parent;ROOT=HERE.parents[1]
sha=lambda p:hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
p=json.loads((HERE/'proposal.json').read_text());c=json.loads((HERE/'construction.json').read_text());m=json.loads((HERE/'native-construction-model.json').read_text());r=json.loads((HERE/'constructed-report.json').read_text())
assert all(sha(v['path'])==v['sha256'] for v in p['source_identity'].values())
assert all(sha(HERE/name)==c[key] for name,key in [('proposal.json','proposal_sha256'),('native-construction-model.json','model_sha256'),('constructed.ses','session_sha256'),('constructed-report.json','report_sha256')])
source=ROOT/'import_session.py';tree=ast.parse(source.read_text());names={'parse','children','child','ses_routes','nm','key','from_snapshot'};safe=ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names],type_ignores=[]);env={'re':re,'json':json,'Path':pathlib.Path};exec(compile(safe,str(source),'exec'),env)
ses=env['ses_routes'](HERE/'constructed.ses');snapshot=env['from_snapshot'](r);assert collections.Counter(map(env['key'],ses))==collections.Counter(map(env['key'],snapshot))
assert len(ses)==21 and sum(x['kind']=='via' for x in ses)==1
native=json.loads(pathlib.Path(m['physical_native']).read_text());objs={o['uuid']:o for o in native['objects']}
assert not m['mutable_source_ids'] and m['all_source_copper_fixed'] and native['board_sha256']==sha(m['physical_board'])==p['source_board_sha256']
assert all(objs[u]['net']==m['aliases'][n] for u,n in m['source_logical_nets'].items())
log=pathlib.Path(p['source_identity']['engine_log']['path']).read_text();progress=[json.loads(l[len('ROUTE_PROGRESS '):]) for l in log.splitlines() if l.startswith('ROUTE_PROGRESS ')]
failed=next(x for x in progress if x.get('attempt',{}).get('net')=='RPM_LV' and x['attempt'].get('contact_label')=='R39.1');assert failed['attempt']['result']=='FAILED' and failed['board_sha256']==p['source_board_sha256']
assert all(x['rejected'] for x in c['negative_controls'])
result={'passed':True,'packet_sha256':{n:sha(HERE/n) for n in ['proposal.json','native-construction-model.json','constructed.ses','constructed-report.json','construction.json']},'verifier_sha256':sha(__file__),'importer_sha256':sha(source),'native_runtime_loaded':False,'pure_importer_parser_matches_report_exactly':True,'new_segments':20,'new_vias':1,'fixed_existing_objects':len(objs),'existing_rpm_lv_nonpad_objects_retained':len([o for o in objs.values() if o['net']=='RPM_LV' and o['kind']!='pad']),'source_hashes_rechecked':True,'engine_actual_result':'FAILED','engine_partial_geometry_not_adopted':True,'native_acceptance_claimed':False}
(HERE/'packet-verification.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
