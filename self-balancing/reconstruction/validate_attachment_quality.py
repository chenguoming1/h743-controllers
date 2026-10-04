#!/usr/bin/python3
"""Mandatory hash-bound attachment-quality acceptance gate; no CAD writes.

Electrical connectivity or nominal segment widths alone cannot approve a board.
This gate requires actual native copper throat, finite-width pad entry, and via
annulus-contact checks. An unresolved or changed review disposition fails closed.
"""
import pathlib,json,hashlib,subprocess,sys,argparse,os
D=pathlib.Path(__file__).resolve().parent
ap=argparse.ArgumentParser();ap.add_argument('--out',type=pathlib.Path,default=D/'attachment-validation');a=ap.parse_args();a.out.mkdir(parents=True,exist_ok=True)
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest();board=D/'controller.kicad_pcb';baseline=D/'input-p5/controller.kicad_pcb';delta=json.loads((D/'source-delta.json').read_text());expected=delta['candidate_sha256'];assert sha(board)==expected;assert sha(baseline)==delta['source_sha256']
manifest_path=D/'attachment-dispositions.json';manifest=json.loads(manifest_path.read_text()) if manifest_path.exists() else {};errors=[]
if manifest.get('candidate_sha256')!=expected:errors.append('Missing or stale exact-source attachment disposition manifest')
commands=[['audit_copper_join_throats.py','--candidate',str(board),'--sha256',expected,'--out',str(a.out/'join-throats.json')],['audit_pad_attachments.py','--board',str(board),'--sha256',expected,'--out',str(a.out/'pad-floor.json')],['audit_pad_attachments.py','--board',str(board),'--sha256',expected,'--nominal-width','--out',str(a.out/'pad-nominal.json')],['audit_via_attachments.py','--include-ground','--baseline',str(baseline),'--candidate',str(board),'--sha256',expected,'--out',str(a.out/'via-attachments.json')]]
commands += [[name,'--candidate',str(board),'--sha256',expected,'--out',str(a.out/output)] for name,output in [('audit_via_functional_layers.py','via-functional-layers.json'),('audit_pad_anchored_dead_trees.py','pad-anchored-dead-trees.json'),('audit_ground_plane_attachments.py','ground-plane-attachments.json'),('audit_reference_retirement.py','reference-retirement.json')]]
for name in ['audit_single_terminal_copper.py']:
 if manifest.get('audit_script_sha256',{}).get(name)!=sha(D/'validation'/name):errors.append('Unreviewed audit dependency: '+name)
for command in commands:
 tool=D/'validation'/command[0]
 if manifest.get('audit_script_sha256',{}).get(command[0])!=sha(tool):errors.append('Unreviewed audit implementation: '+command[0])
 result=subprocess.run([sys.executable,str(tool)]+command[1:],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True);(a.out/(pathlib.Path(command[0]).stem+'.log')).write_text(result.stdout)
 if result.returncode:errors.append('Attachment audit execution failed: '+command[0])
if not any('execution failed' in e for e in errors):
 joins=json.loads((a.out/'join-throats.json').read_text());pads=json.loads((a.out/'pad-floor.json').read_text());nominal=json.loads((a.out/'pad-nominal.json').read_text());vias=json.loads((a.out/'via-attachments.json').read_text())
 if joins['narrow_local_join_flags']:errors.append('Actual copper has unresolved narrow local track joins')
 if pads['counts']['failed_groups']:errors.append('Functional pad copper does not satisfy minimum .130mm passage screen')
 if vias['new_or_worsened_shallow_groups']:errors.append('New or worsened shallow via contacts remain')
 reference=json.loads((a.out/'reference-retirement.json').read_text())
 if reference['status']!='PASS EXACT SIX-VIA REFILL ORACLE':errors.append('Exact six-via reference refill cannot be reproduced')
 roles=json.loads((a.out/'via-functional-layers.json').read_text());trees=json.loads((a.out/'pad-anchored-dead-trees.json').read_text());ground=json.loads((a.out/'ground-plane-attachments.json').read_text())
 if roles['one_layer_or_zero_layer_review'] or roles['via_count']!=manifest['expected_final_vias'] or roles['ground_vias']!=manifest['expected_ground_vias']:errors.append('Redundant or unexpected via layer function/count remains')
 if trees['review_trees']:errors.append('Exposed pad-anchored dead copper tree remains')
 if ground['errors'] or ground['verified_reference_plane_terminal_attachments']!=manifest['expected_reference_plane_terminal_attachments']:errors.append('Ground-plane actual terminal attachment is unqualified')
 # Exceptions preserve exact reviewed contact geometry, not just net names or counts.
 canonical=lambda x:json.dumps(x,sort_keys=True,separators=(',',':'))
 actual_vias=[{'via_uuid':r['via_uuid'],'layer':r['layer'],'net':r['net'],'tracks':r['candidate']['tracks']} for r in vias['inherited_or_improved_shallow_groups']]
 allowed_vias=[r['contact'] for r in manifest.get('reviewed_incidental_via_contacts',[])]
 if sorted(map(canonical,actual_vias))!=sorted(map(canonical,allowed_vias)):errors.append('Inherited via contact dispositions are missing or changed')
 actual_pads=[{'pad_uuid':r.get('pad_uuid',r.get('uuid')),'net':r['net'],'layer':r['layer'],'tracks':g['tracks']} for r in nominal['profiles'] for g in r['groups'] if not g['local_finite_width_pass']]
 allowed_pads=[r['contact'] for r in manifest.get('reviewed_above_floor_pad_contacts',[])]
 if sorted(map(canonical,actual_pads))!=sorted(map(canonical,allowed_pads)):errors.append('Above-floor nominal pad entry dispositions are missing or changed')
assert sha(board)==expected and sha(baseline)==delta['source_sha256']
report={'candidate_sha256':expected,'baseline_sha256':delta['source_sha256'],'status':'PASS ATTACHMENT QUALITY' if not errors else 'FAIL ATTACHMENT QUALITY','errors':errors,'mandatory_for_export_and_acceptance':True,'limits':'This gate supplements native DRC, source-width/current-path preservation, topology, reference coverage, and complete visual review; it does not replace them.'};(a.out/'attachment-quality-gate.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2));sys.exit(1 if errors else 0)
