from pathlib import Path
import json,hashlib,shutil,datetime
R=Path('/workspace/scratch/8a35c1f26232/nexus-recovery-20261015');O=R/'u10-metadata-integration';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();summaries={}
cc=json.loads((O/'experimental-r51/routing-return-continuity/cc1-return-continuity.json').read_text());assert cc['status']=='PASS' and cc['all_existing_shield_spoke_copper_preserved'] and not cc['lost_spoke_copper']
for role in ['canonical','experimental-r51']:
 D=O/role;v=json.loads((D/'verification.json').read_text());e=json.loads((D/'export-equality.json').read_text());tr=json.loads((D/'transaction.json').read_text());S=Path(tr['source_directory']);assert v['candidate_board_sha256']==sha(D/'hardware/nexus-style-fc.kicad_pcb')==e['candidate_pcb_sha256'];assert v['source_board_sha256']==sha(S/'hardware/nexus-style-fc.kicad_pcb')==e['source_pcb_sha256']
 assert not any(v[k] for k in ['opens','parity_issues','erc_violations']);assert v['exact_net_pin_pairs']==347;assert v['native_error_count']==(627 if role=='canonical' else 18)
 assert sha(D/'hardware/nexus-style-fc.kicad_sch')=='49f9e0571424d0610e294bdcd6b120a42d04db284ecda9e660428fc587e62699'
 if role=='experimental-r51':assert cc['candidate_board_sha256']==v['candidate_board_sha256']
 A=D/'audit-scripts';A.mkdir(exist_ok=True)
 for p in (O/'scripts').glob('*.py'):shutil.copy2(p,A/p.name)
 shutil.copy2(R/'latest-main/nexus-style-fc/tools/validate_nexus_reroute.py',A/'validate_nexus_reroute.py');shutil.copy2('/workspace/shared/nexus-recovery-evidence/apply_en_cut.py',A/'apply_en_cut.py')
 H=D/'generator-proof';H.mkdir(exist_ok=True)
 for p in ['before-pcbutil.py','generator-handoff.json','generator-scope-tests.json','scope-test-result.json','test_generator_scope.py','tools/pcbutil.py']:
  src=R/'u10-metadata-cleanup'/p;dest=H/p;dest.parent.mkdir(exist_ok=True,parents=True);shutil.copy2(src,dest)
 for p in D.glob('helper-smoke-native.*'):shutil.move(str(p),str(H/p.name))
 B=D/'rollback';B.mkdir(exist_ok=True);shutil.copy2(S/'hardware/nexus-style-fc.kicad_pcb',B/'source.kicad_pcb');assert sha(B/'source.kicad_pcb')==tr['source_board_sha256']
 if role=='experimental-r51':
  L=D/'source-routing-review';L.mkdir(exist_ok=True)
  for n in ['verification.json','return-topology-comparison.json','geometry-verification.json','gap-audit.json','native-receipt.json','evidence-manifest.json']:shutil.copy2(S/n,L/n)
 v.update({'generator_helper_native_smoke_pass':True,'BOM_CPL_byte_equal':True,'export_equality_sha256':sha(D/'export-equality.json'),'all_metadata_source_filled_copper_exact':True,'source_main_binding_sha256':sha(D/'current-main-binding.json')})
 if role=='experimental-r51':v['r50_ground_and_shield_continuity_sha256']=sha(D/'routing-return-continuity/cc1-return-continuity.json')
 (D/'verification.json').write_text(json.dumps(v,indent=2)+'\n')
 files={str(p.relative_to(D)):sha(p) for p in sorted(D.rglob('*')) if p.is_file() and p.name!='evidence-manifest.json'}
 # A copied source manifest has the same basename; include it explicitly when it is not the root manifest.
 files.update({str(p.relative_to(D)):sha(p) for p in D.rglob('evidence-manifest.json') if p.parent!=D})
 m={'status':'Immutable source-bound U10 metadata-only integration; native manufacturing findings remain open','sealed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'files':files};(D/'evidence-manifest.json').write_text(json.dumps(m,indent=2)+'\n');assert all(sha(D/p)==h for p,h in files.items())
 summaries[role]={'directory':str(D),'board_sha256':v['candidate_board_sha256'],'schematic_sha256':v['schematic_sha256'],'project_sha256':v['project_sha256'],'rules_sha256':v['rules_sha256'],'native_drc_sha256':v['native_drc_sha256'],'native_erc_sha256':v['native_erc_sha256'],'native_error_count':v['native_error_count'],'native_errors_by_type':v['native_errors_by_type'],'opens':0,'parity':0,'ERC':0,'manifest_sha256':sha(D/'evidence-manifest.json'),'file_count':len(files),'minimum_clearance_mm':v['minimum_remaining_clearance_mm']}
h={'status':'SEALED for publisher review; no publication performed by repair lane','main_commit':'80a3f763d5031198b4622402bb73a532676b9be9','current_main_binding_sha256':sha(R/'current-main-binding-09.json'),'canonical_scope':'Exact U10 stale donor LCSC Part property removal and library-description replacement only; copper and fills unchanged. Canonical remains 627 errors.','experimental_scope':'r50 CC1 clearance improvement, freshly accepted r51 all-F output-loop replay, then exact U10 metadata cleanup. Current experimental state has 18 errors.','schematic_sha256':'49f9e0571424d0610e294bdcd6b120a42d04db284ecda9e660428fc587e62699','states':summaries,'routing_lineage':{name:{'directory':str(R/'routing-continuation'/name),'manifest_sha256':sha(R/'routing-continuation'/name/'evidence-manifest.json')} for name in ['r48-local-bends','r50-cc1-spoke-preserved','r51-ldo-output']},'inherited_open_gates':'18 ordinary pasted vias, USB differential/protection/return redesign, system power/thermal/transient/PSRR and effective-capacitance qualification, header 11 edge findings and mechanical interference, all remaining native clearances; no fabrication-ready claim.'};(O/'SEALED-HANDOFF.json').write_text(json.dumps(h,indent=2)+'\n');print(json.dumps({'handoff_sha256':sha(O/'SEALED-HANDOFF.json'),'states':summaries},indent=2))
