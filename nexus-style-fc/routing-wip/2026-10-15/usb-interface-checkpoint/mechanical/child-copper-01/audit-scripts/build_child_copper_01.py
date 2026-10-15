from pathlib import Path
import pcbnew as k, json,hashlib,shutil,sys,importlib.util
sys.path.insert(0,'/workspace/shared/nexus-recovery-evidence');from apply_en_cut import children,field
R=Path('/workspace/scratch/8a35c1f26232/nexus-recovery-20261015');O=R/'mechanical-integration/child-copper-01';Q=Path('/workspace/scratch/8a35c1f26232/nexus-header-redesign-20261015/child-routing-proposal-20261015');sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();assert sha(Q/'complete-transaction.json')=='0b130c0700b6adcbead837aaded342dc6d73d6f7301f4b9bbeeb1928c40dc6d9';tr=json.loads((Q/'complete-transaction.json').read_text());P=Path(tr['source']['path']);S=P.parents[2];assert sha(P)==tr['source']['sha256']=='de56d5e4a066ff03a8c16d7e0501f45ca651ebf177c45ba12667488162010f38';assert not O.exists()
spec=importlib.util.spec_from_file_location('V',R/'latest-main/nexus-style-fc/tools/validate_nexus_reroute.py');V=importlib.util.module_from_spec(spec);spec.loader.exec_module(V)
s=P.read_text();nodes={field(s[a:z],'uuid').strip(chr(34)):s[a:z] for a,z in children(s) if s[a:z].startswith('(segment')};oldids=[];newids=[]
for route in tr['routes']:
 for old in route['source_donor_segments']:
  u=old['uuid'];oldids.append(u);assert V.canonical(V.parse_sexpr(nodes[u]))==V.canonical(V.parse_sexpr(old['native_record'])),u
 for new in route['replacement_segments']:newids.append(new['uuid'])
 for i,old in enumerate(route['source_donor_segments']):s=s.replace(nodes[old['uuid']],'\n\t'.join(x['native_record'] for x in route['replacement_segments']) if i==0 else '')
assert len(oldids)==6 and len(newids)==9 and len(set(newids))==9
shutil.copytree(S/'hardware/header-board',O/'hardware/header-board');shutil.copytree(S/'hardware/library',O/'hardware/library');shutil.copytree(Q,O/'source-review');shutil.copytree(S/'hardware/header-board',O/'rollback/header-board');B=O/'hardware/header-board/nexus-header-board.kicad_pcb';B.write_text(s);minimal=O/'minimal-pre-refill.kicad_pcb';shutil.copy2(B,minimal)
b=k.LoadBoard(str(B));assert len([x for x in b.GetTracks() if not isinstance(x,k.PCB_VIA)])==73 and len([x for x in b.GetTracks() if isinstance(x,k.PCB_VIA)])==3
for z in b.Zones():z.UnFill()
k.SaveBoard(str(B),b)
tr.update({'native_trial_status':'UNFINISHED separate mechanical child copper transaction','source_directory':str(S),'source_schematic_sha256':sha(P.with_suffix('.kicad_sch')),'removed_or_replaced_uuids':oldids,'replacement_uuids':newids,'minimal_pre_refill_sha256':sha(minimal),'all_cached_zone_fills_invalidated':True,'stopping_bound':'One exact reviewed six-donor/nine-segment transaction, no component/outline/rule changes. Reject any new native errors, missing physical ports or width reduction.'});(O/'transaction.json').write_text(json.dumps(tr,indent=2)+'\n');shutil.copy2(R/'current-main-binding-13.json',O/'current-main-binding.json');print(json.dumps({'output':str(O),'source_sha256':sha(P),'native_input_sha256':sha(B)},indent=2))
