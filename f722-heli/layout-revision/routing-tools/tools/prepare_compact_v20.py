#!/usr/bin/env python3
"""Freeze accepted 50/51/52 source evidence over immutable V19; no native execution."""
import difflib, hashlib, json, lzma, os, shutil, subprocess
from pathlib import Path

W=Path(__file__).resolve().parent.parent
B=W/'ordinary-routing/public-source-ready-v19'
S=W/'ordinary-routing/public-source-ready-v20'
BASE_MANIFEST='30ef631b771d66f4b46979237b7e9a603bfbe23ca3feda5ac29050411d4ba22a'
BASE_ZIP='1826d411c57ca1e891c0d8f5c9da0e052ecf92b2a20d191892f170cff0192015'
BOARDS={'candidate49':'15499b28bb63a8c2326c8c7e73dbac4198b8333b05325ab35653825848ae9069',
 'candidate50':'cbb9a1f0b43dc612718baf1277302c9ac0767474cc7fa13f5d8c0a2428f2b787',
 'candidate51':'80eb38da7100fd677862b8d3bc161329b278c410614f3b15460b5a5c863a75e6',
 'candidate52':'71d33748909bb960c5829973642272460607d8521831a6212975f7de6790d660'}
PROJECTS={k:'ordinary-routing/'+k for k in BOARDS}
PROJECTS.update(B03='ordinary-routing/tests/port-b48/candidate03',A04='ordinary-routing/tests/port-a48/candidate04')
WORKERS={'candidate50':'ordinary-routing/tests/servo48/candidate03','candidate51':'ordinary-routing/tests/port-a48/candidate05','candidate52':'ordinary-routing/tests/sbus-nrst49/candidate02'}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def info(p):return {'sha256':sha(p),'bytes':Path(p).stat().st_size}
def read(p):return json.loads(Path(p).read_bytes())
def write(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,indent=2,sort_keys=True)+'\n')
assert sha(B/'FILES.sha256.json')==BASE_MANIFEST
assert sha(W/'ordinary-routing/routing-source-v19-delta.zip')==BASE_ZIP
assert not S.exists()
initial={'index_sha256':sha(W/'repo/.git/index'),'head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=W/'repo',text=True).strip(),'canonical_board':info(W/'repo/f722-heli/layout-revision/hardware/f722-heli.kicad_pcb')}
assert initial['head']=='635dc37d0c4b0dfc8d33359112db4c873a03b921'
assert initial['canonical_board']['sha256']==BOARDS['candidate52']
shutil.copytree(B,S,copy_function=os.link)
# Detach every inherited file that this version will rewrite. Historical files remain hardlinks.
for name in ['README.md','REPRODUCE.md','SOURCE_EVIDENCE.md','EXCLUDED_INPUTS.md','EVIDENCE_INDEX.json','status.json','FILES.sha256.json','PUBLIC_SOURCE_ALLOWLIST.json','checks/source-package-validation.json']:
 p=S/name
 if p.exists():p.unlink()
for name in ['README.md','REPRODUCE.md','SOURCE_EVIDENCE.md','EXCLUDED_INPUTS.md','EVIDENCE_INDEX.json','status.json']:
 p=S/'docs/historical-v19'/name;p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(B/name,p)
for name in ['FILES.sha256.json','PUBLIC_SOURCE_ALLOWLIST.json']:shutil.copy2(B/name,S/'checks'/('v19-original-'+name))
packet=S/'tests/checkpoint52';packet.mkdir();rec=S/'sessions/recovery-v20';rec.mkdir()
required={n:info(W/'ordinary-routing/candidate49'/n) for n in read(B/'sessions/recovery-v19/paired-files.json')['required_base_files']}
selected={};excluded={};recovered={};frozen={};aliases={};seals={}
def add(name,override=None):
 p=Path(override) if override else W/name
 assert p.is_file(),name
 for project in PROJECTS.values():
  prefix=project+'/'
  if name.startswith(prefix) and name[len(prefix):] in required:
   recovered[name]=info(p);return
 if p.name in {'f722-heli.native.json','owner-native.json','native-geometry.json','owner-mechanical-geometry.json','model.json'} or p.suffix in {'.kicad_pcb','.kicad_prl','.pdf'}:
  excluded[name]=dict(info(p),reason='Raw native export, duplicate board, local preferences or vendor PDF excluded; hash retained. Native replay needs separately regenerated/restored exact dependencies and is not claimed.')
  return
 if name in selected:assert selected[name].read_bytes()==p.read_bytes(),name
 selected[name]=p
 if p.suffix=='.py':frozen[name]=info(p)
 if override:aliases[name]=str(p.relative_to(W))
def tree(folder):
 for p in sorted((W/folder).rglob('*')):
  if p.is_file() and '__pycache__' not in p.parts and p.suffix not in {'.pyc','.pyo'}:add(str(p.relative_to(W)))
for label,folder in PROJECTS.items():
 h=sha(W/folder/'f722-heli.kicad_pcb')
 if label in BOARDS:assert h==BOARDS[label]
 else:BOARDS[label]=h
 if label!='candidate49':tree(folder)
for label,worker in WORKERS.items():
 c='ordinary-routing/'+label;h=read(W/c/'route-handoff.json')
 assert sha(W/worker/'f722-heli.kicad_pcb')==BOARDS[label]
 assert (W/c/'route-handoff.json').read_bytes()==(W/worker/'route-handoff.json').read_bytes()
 for name,digest in h['files'].items():
  assert sha(W/c/name)==digest==sha(W/worker/name),(label,name)
 seals[label]={'files':len(h['files']),'manifest':info(W/c/'route-handoff.json'),'worker':worker}
 for p in sorted((W/c).glob('*.used.py')):add(str(Path(worker).parent/(p.stem.removesuffix('.used')+'.py')),p)
# B03 retains its own original worker-file seal and frozen constructor dependencies.
bp='ordinary-routing/tests/port-b48/candidate03';bs=read(W/bp/'WORKER-FILES.sha256.json')
for row in bs['files']:assert sha(W/bp/row['path'])==row['sha256']
seals['B03']={'files':len(bs['files']),'manifest':info(W/bp/'WORKER-FILES.sha256.json'),'worker':bp}
for p in (W/bp/'worker-receipt-sources').glob('*.py'):add('ordinary-routing/tests/port-b48/'+p.name,p)
for folder in ['checkpoint27-review','checkpoint19-owner-review','checkpoint17-owner-review','checkpoint19-review','checkpoint19-final-placement-reproduction','checkpoint19-final-placement-preview','checkpoint17-placement-reproduction','checkpoint17-placement-preview']:tree(folder)
for name in ['checkpoint27-review-run.log','checkpoint19-final-placement-reproduction.log','checkpoint19-final-placement-preview.log','checkpoint17-placement-reproduction.log','checkpoint17-placement-preview.log']:
 if (W/name).is_file():add(name)
for name in ['adopt_verified.py','verify_adoption_integration.py','verify_reference_runtime_indices.py','test_reference_runtime_indices.py','runtime-index-v2-compatibility.json','declared-transforms50-to51.json','refresh_accepted_checkpoint.py','review_ordinary_checkpoint.py','validate_checkpoint.py','check_coordinated_integration.py','verify_support_adoption.py','verify_reference_window_classification.py','reproduce_placement_checkpoint.py']:
 add('integrated-routing/'+name)
for name in ['native-tools/export_native_copper.py','native-tools/exact_native_contours.py','native-tools/check_protection_paths.py','tests/mpn-parity/apply_metadata_copy.py','dsm40-audits/audit_dsm40_entries_return.py','dsm41-audits/audit_dsm41_entries_return.py','servo23-audits/audit_rewritten_entries.py']:
 add('ordinary-routing/'+name)
# Canonical review receipts only; their sources are frozen to the accepted boards above.
for name in ['checkpoint27-owner-review.json','checkpoint19-owner-review.json','checkpoint17-owner-review.json','current-status.json']:
 p='repo/f722-heli/layout-revision/checks/'+name
 if (W/p).is_file():add(p)
for p in (W/'repo/f722-heli/layout-revision/signal-review/native').glob('*.py'):add(str(p.relative_to(W)))
for p in (W/'repo/f722-heli/layout-revision/placement-build').glob('*.py'):add(str(p.relative_to(W)))
# Selected recipe inputs are fixed final source copies, never drifting route searches.
for name,source in {
 'ordinary-routing/tests/servo48/complete-proposal49-v3.json':'ordinary-routing/candidate50/proposal.json',
 'ordinary-routing/tests/servo48/signal-review/tail-path-comparison.json':'ordinary-routing/candidate50/conditional-signal-review/tail-path-comparison.json',
 'ordinary-routing/tests/port-b48/rx-reference-repair-on-A04.json':'ordinary-routing/candidate51/shared-B-return-patch.json',
 'ordinary-routing/tests/sbus-nrst49/final19-proposal.json':'ordinary-routing/candidate52/final19-proposal.json',
 'ordinary-routing/tests/sbus-nrst49/final19-screen.json':'ordinary-routing/candidate52/final19-screen.json',
 'ordinary-routing/tests/sbus-nrst49/reference-corrected-sbus19-proposal.json':'ordinary-routing/candidate52/reference-corrected-sbus19-proposal.json',
}.items():add(name,W/source)
for name in ['f722-heli.native.json','f722-heli.logical-route-map.json','fixed-explicit-native-ids.json','poses-native.json','power-audit.json','project-input-preservation.json','protection-actual-io.json','reference-snapshot/native-geometry.json','reference-snapshot/native-signals.json','reference-snapshot/critical-reference.json']:add('ordinary-routing/candidate49/'+name)
manifest={'schema':'f722-historical-paired-files/v1','base_label':'candidate49 / immutable V19 recovered candidate49','required_base_files':required,'sources':{}}
def delta(bp,tp,dest):
 before,after=bp.read_bytes(),tp.read_bytes();lines=before.splitlines(keepends=True);target=after.splitlines(keepends=True);offsets=[0]
 for line in lines:offsets.append(offsets[-1]+len(line))
 ops=[]
 for tag,i,j,k,l in difflib.SequenceMatcher(None,lines,target,autojunk=True).get_opcodes():
  if tag=='equal':ops.append([offsets[i],offsets[j]-offsets[i]])
  elif tag in {'insert','replace'}:ops.append(b''.join(target[k:l]).decode())
 write(dest,{'schema':'f722-historical-source-copy-delta/v1','base_sha256':sha(bp),'target_sha256':sha(tp),'target_bytes':len(after),'operations':ops})
for label,folder in PROJECTS.items():
 entries={}
 for name,row in required.items():
  p=W/folder/name;assert p.is_file(),str(p)
  if sha(p)!=row['sha256']:
   assert name=='f722-heli.kicad_pcb',(label,name)
   d=label+'.'+name+'.delta.json';delta(W/'ordinary-routing/candidate49'/name,p,rec/d);entries[name]={'file':d,'sha256':sha(rec/d)}
  recovered[folder+'/'+name]=info(p)
 manifest['sources'][label]={'board_sha256':BOARDS[label],'deltas':entries,'workspace_path':folder}
write(rec/'paired-files.json',manifest)
src=(B/'sessions/recovery-v19/rebuild_historical_source.py').read_text().replace('candidate48 project recovered by V18','candidate49 project recovered by V19').replace("choices=('candidate48', 'candidate49')","choices="+repr(tuple(PROJECTS)))
(rec/'rebuild_historical_source.py').write_text(src)
index={'schema':'f722-selected-evidence/v2','files':{},'excluded_files':dict(sorted(excluded.items())),'recovered_files':dict(sorted(recovered.items())),'frozen_alias_sources':aliases,'scope':'Accepted candidate50/27,51/19,52/17 only. B03 and A04 are required construction lineage, not separately adopted milestones. Wrong-incremental checkpoint19-review refusal and raw earlier failures preserved. Later isolated15/RPM/flash/PORT_C trials excluded.'}
for name,p in sorted(selected.items()):
 data=p.read_bytes();row=info(p)
 if len(data)>100000:
  target='blobs/'+row['sha256']+'.xz';dest=packet/target;dest.parent.mkdir(parents=True,exist_ok=True)
  if not dest.exists():dest.write_bytes(lzma.compress(data,preset=1))
  row.update(compressed_file=target,compressed_sha256=sha(dest))
 else:
  target='files/'+name;dest=packet/target;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data);row['file']=target
 index['files'][name]=row
write(packet/'raw-evidence.json',index)
(packet/'materialize.py').write_text((B/'tests/checkpoint49/materialize.py').read_text().replace('recovery-v19','recovery-v20').replace('recovery_v19','recovery_v20').replace("p=a.out/'ordinary-routing'/label/relative","p=a.out/recovery_manifest['sources'][label]['workspace_path']/relative").replace("projects={label:recovery.prepare_project", "recovery_manifest=json.loads((packet/'paired-files.json').read_bytes())\n   projects={label:recovery.prepare_project"))
identity={'schema':'f722-v20-frozen-source-identity/v1','base_v19_manifest_sha256':BASE_MANIFEST,'base_v19_zip_sha256':BASE_ZIP,'expected_boards':BOARDS,'projects':PROJECTS,'sealed_worker_manifests':seals,'frozen_helpers':frozen,'frozen_alias_sources':aliases,'selected_files':len(selected),'excluded_raw_files':len(excluded),'initial_immutability':initial,'native_replay_inputs_complete':False,'native_JVM_FEM_or_router_execution_performed':False}
write(S/'checks/v20-source-identity.json',identity);write(S/'checks/v20-frozen-helpers.json',frozen)
shutil.copy2(Path(__file__),S/'tools/prepare_compact_v20.py')
assert sha(B/'FILES.sha256.json')==BASE_MANIFEST
assert sha(W/'repo/.git/index')==initial['index_sha256']
print(json.dumps({'staging':str(S),'selected':len(selected),'excluded':len(excluded),'recovered_paths':len(recovered),'paired_projects':len(PROJECTS),'frozen_helpers':len(frozen),'seals':seals}))
