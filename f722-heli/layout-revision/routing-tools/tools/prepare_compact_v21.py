#!/usr/bin/env python3
"""Capture bounded accepted54 evidence over immutable V20 after owner readiness."""
import argparse,difflib,hashlib,json,lzma,os,shutil,subprocess
from pathlib import Path
W=Path(__file__).resolve().parent.parent;B=W/'ordinary-routing/public-source-ready-v20';S=W/'ordinary-routing/public-source-ready-v21'
BASE_MANIFEST='96187ae69afc1f7136982eb16a63673cef8f639a4ee67cfadef8a56d61f6f7fe'
BASE_ZIP='7c5fda16f2f1dc4cddd15212879e5a0205f4d9e0e036844261c17272e88da88f'
PROJECTS={'candidate52':'ordinary-routing/candidate52','SERVO15':'ordinary-routing/tests/servo48/candidate04','RPM14':'ordinary-routing/tests/rpm17/candidate01','candidate54':'ordinary-routing/candidate54'}
BOARDS={'candidate52':'71d33748909bb960c5829973642272460607d8521831a6212975f7de6790d660','SERVO15':'755545e8198e9a3649c0e07533c23e67010d91ab6a8b09556d7463e064ac89eb','RPM14':'73dbae05954b8edec4143d91248bf38c40537f83e8f5f3fed51744105169d6c7','candidate54':'24121b0e46d9a71207cd21e7cf599412c00796d48eb9af5f63ffcf92e5f2ca42'}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def info(p):return {'sha256':sha(p),'bytes':Path(p).stat().st_size}
def read(p):return json.loads(Path(p).read_bytes())
def write(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,indent=2,sort_keys=True)+'\n')
ap=argparse.ArgumentParser();ap.add_argument('--owner-ready',action='store_true',required=True);ap.parse_args()
assert sha(B/'FILES.sha256.json')==BASE_MANIFEST and sha(W/'ordinary-routing/routing-source-v20-delta.zip')==BASE_ZIP
assert all(sha(B/n)==h for n,h in read(B/'FILES.sha256.json').items())
assert not S.exists()
initial={'index_sha256':sha(W/'repo/.git/index'),'head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=W/'repo',text=True).strip(),'canonical_board':info(W/'repo/f722-heli/layout-revision/hardware/f722-heli.kicad_pcb')}
assert initial['head']=='635dc37d0c4b0dfc8d33359112db4c873a03b921' and initial['canonical_board']['sha256']==BOARDS['candidate54']
shutil.copytree(B,S,copy_function=os.link)
for name in ['README.md','REPRODUCE.md','SOURCE_EVIDENCE.md','EXCLUDED_INPUTS.md','EVIDENCE_INDEX.json','status.json','FILES.sha256.json','PUBLIC_SOURCE_ALLOWLIST.json','checks/source-package-validation.json']:
 p=S/name
 if p.exists():p.unlink()
for name in ['README.md','REPRODUCE.md','SOURCE_EVIDENCE.md','EXCLUDED_INPUTS.md','EVIDENCE_INDEX.json','status.json']:
 p=S/'docs/historical-v20'/name;p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(B/name,p)
for name in ['FILES.sha256.json','PUBLIC_SOURCE_ALLOWLIST.json']:shutil.copy2(B/name,S/'checks'/('v20-original-'+name))
packet=S/'tests/checkpoint54';packet.mkdir();rec=S/'sessions/recovery-v21';rec.mkdir()
required={n:info(W/PROJECTS['candidate52']/n) for n in read(B/'sessions/recovery-v20/paired-files.json')['required_base_files']}
selected={};excluded={};recovered={};frozen={};aliases={};seals={}
def add(name,source=None):
 p=W/(source or name);assert p.is_file(),name
 for project in PROJECTS.values():
  prefix=project+'/'
  if name.startswith(prefix) and name[len(prefix):] in required:recovered[name]=info(p);return
 if p.name in {'f722-heli.native.json','owner-native.json','native-geometry.json','owner-mechanical-geometry.json','model.json'} or p.suffix in {'.kicad_pcb','.kicad_prl','.pdf'}:
  excluded[name]=dict(info(p),reason='Omitted raw native export, duplicate board, local preferences or vendor PDF; original hash retained. Native recipe replay needs exact restored/regenerated dependencies and is not claimed.');return
 if name in selected:assert selected[name].read_bytes()==p.read_bytes(),name
 selected[name]=p
 if p.suffix=='.py':frozen[name]=info(p)
 if source:aliases[name]=source
def tree(folder):
 for p in sorted((W/folder).rglob('*')):
  if p.is_file() and '__pycache__'not in p.parts and p.suffix not in {'.pyc','.pyo'}:add(str(p.relative_to(W)))
for label,folder in PROJECTS.items():
 assert sha(W/folder/'f722-heli.kicad_pcb')==BOARDS[label]
 if label=='candidate52':continue
 tree(folder);handoff=read(W/folder/'route-handoff.json')
 for n,h in handoff['files'].items():assert sha(W/folder/n)==h,(label,n)
 seals[label]={'files':len(handoff['files']),'manifest':info(W/folder/'route-handoff.json'),'path':folder,'adopted_in_its_own_right':label=='candidate54'}
 helperroot=Path(folder).parent if label!='candidate54'else Path('ordinary-routing/tests/servo48')
 for p in (W/folder).glob('*.used.py'):
  if p.name not in {'construct.used.py','validate_checkpoint.used.py'}:add(str(helperroot/(p.stem.removesuffix('.used')+'.py')),str(p.relative_to(W)))
# Independently bind canonical copies and worker originals without duplicating their large exports.
for canonical,worker in [('ordinary-routing/candidate53',PROJECTS['SERVO15']),(PROJECTS['candidate54'],'ordinary-routing/tests/servo48/candidate06')]:
 assert sha(W/canonical/'route-handoff.json')==sha(W/worker/'route-handoff.json')
 for n,h in read(W/canonical/'route-handoff.json')['files'].items():assert sha(W/canonical/n)==sha(W/worker/n)==h
for folder in ['checkpoint15-owner-review','checkpoint14-owner-review','checkpoint14-ground-owner-review','checkpoint14-ground-placement-reproduction','checkpoint14-ground-placement-preview']:tree(folder)
for n in ['owner-summary.json','owner-drc.json','owner-drc-all.json','owner-drc.log','owner-drc-all.log','proposal.json']:add('ordinary-routing/tests/servo48/candidate05/'+n)
for name in ['adopt_verified.py','verify_adoption_integration.py','verify_reference_runtime_indices.py','refresh_accepted_checkpoint.py','review_ordinary_checkpoint.py','validate_checkpoint.py','check_coordinated_integration.py','check_additive_integration.py','verify_support_adoption.py','verify_reference_window_classification.py','verify_footprint_transforms.py','verify_footprint_translations.py','verify_intentional_i2c_review.py','reproduce_placement_checkpoint.py']:add('integrated-routing/'+name)
for name in ['native-tools/export_native_copper.py','native-tools/exact_native_contours.py','native-tools/check_protection_paths.py','tests/mpn-parity/apply_metadata_copy.py','dsm40-audits/audit_dsm40_entries_return.py','dsm41-audits/audit_dsm41_entries_return.py','servo23-audits/audit_rewritten_entries.py']:add('ordinary-routing/'+name)
for p in (W/'repo/f722-heli/layout-revision/signal-review/native').glob('*.py'):add(str(p.relative_to(W)))
for name in ['rebuild_placement.py','patch_metadata.py','check_native_parity.py']:add('repo/f722-heli/layout-revision/scripts/'+name)
add('repo/f722-heli/layout-revision/source.json')
for n in ['current-status.json','checkpoint14-ground-owner-review.json']:
 p='repo/f722-heli/layout-revision/checks/'+n
 if (W/p).is_file():add(p)
tree('repo/f722-heli/layout-revision/checks/checkpoint54-integration')
for name in ['repo/f722-heli/README.md','repo/f722-heli/layout-revision/README.md','repo/f722-heli/layout-revision/placement-build.json','repo/f722-heli/layout-revision/placement.json','repo/f722-heli/layout-revision/routing-build.json']:add(name)
for name,source in {
 'ordinary-routing/tests/servo48/servo1-complete17-proposal.json':PROJECTS['SERVO15']+'/proposal.json',
 'ordinary-routing/tests/servo48/servo1-complete-geometry17.json':PROJECTS['SERVO15']+'/proposal-geometry-screen.json',
 'ordinary-routing/tests/rpm17/complete-layer-proposal.json':PROJECTS['RPM14']+'/complete-layer-proposal.json',
 'ordinary-routing/tests/rpm17/preconstruction-screen.json':PROJECTS['RPM14']+'/preconstruction-screen.json',
 'ordinary-routing/tests/servo48/dedicated-u12-ground15/separated-returns14-proposal.json':PROJECTS['candidate54']+'/proposal.json',
 'ordinary-routing/tests/servo48/dedicated-u12-ground15/quiet-return-alternatives14.json':PROJECTS['candidate54']+'/conditional-support-review/quiet-return-alternatives14.json',
}.items():add(name,source)
bindings=read(W/PROJECTS['RPM14']/'receipt-source-bindings.json')
for n,h in bindings['existing_helpers'].items():assert sha(W/n)==h;add(n)
for name in ['f722-heli.native.json','f722-heli.logical-route-map.json','fixed-explicit-native-ids.json','poses-native.json','power-audit.json','project-input-preservation.json','protection-actual-io.json','reference-snapshot/native-geometry.json','reference-snapshot/native-signals.json','reference-snapshot/critical-reference.json']:add(PROJECTS['candidate52']+'/'+name)
# Datasheet byte identities remain explicit; only the already existing text is included.
for name in ['independent-core-voltage-review/sources/TPS25947.pdf','independent-core-voltage-review/sources/TPS25947.txt']:add(name)
manifest={'schema':'f722-historical-paired-files/v1','base_label':'candidate52 / immutable V20 recovered candidate52','required_base_files':required,'sources':{}}
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
   d=label+'.'+name+'.delta.json';delta(W/PROJECTS['candidate52']/name,p,rec/d);entries[name]={'file':d,'sha256':sha(rec/d)}
  recovered[folder+'/'+name]=info(p)
 manifest['sources'][label]={'board_sha256':BOARDS[label],'deltas':entries,'workspace_path':folder,'status':'accepted checkpoint'if label in {'candidate52','candidate54'}else'historical unadopted construction lineage'}
write(rec/'paired-files.json',manifest)
src=(B/'sessions/recovery-v20/rebuild_historical_source.py').read_text().replace('candidate49 project recovered by V19','candidate52 project recovered by V20').replace("choices=('candidate49', 'candidate50', 'candidate51', 'candidate52', 'B03', 'A04')","choices="+repr(tuple(PROJECTS)))
assert 'choices='+repr(tuple(PROJECTS)) in src
(rec/'rebuild_historical_source.py').write_text(src)
index={'schema':'f722-selected-evidence/v2','files':{},'excluded_files':dict(sorted(excluded.items())),'recovered_files':dict(sorted(recovered.items())),'frozen_alias_sources':aliases,'scope':'Accepted52→54 with historical unadopted SERVO15 and RPM14 construction lineage. Rejected R52 candidate05 clearance receipts retained. Later flash/GREEN/BOOT/PORT_C work excluded.'}
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
(packet/'materialize.py').write_text((B/'tests/checkpoint52/materialize.py').read_text().replace('recovery-v20','recovery-v21').replace('recovery_v20','recovery_v21'))
identity={'schema':'f722-v21-frozen-source-identity/v1','base_v20_manifest_sha256':BASE_MANIFEST,'base_v20_zip_sha256':BASE_ZIP,'expected_boards':BOARDS,'projects':PROJECTS,'sealed_worker_manifests':seals,'frozen_helpers':frozen,'frozen_alias_sources':aliases,'selected_files':len(selected),'excluded_raw_files':len(excluded),'initial_immutability':initial,'source_aliases':{'ordinary-routing/candidate53':PROJECTS['SERVO15'],'ordinary-routing/tests/servo48/candidate06':PROJECTS['candidate54']},'native_replay_inputs_complete':False,'native_JVM_FEM_or_router_execution_performed':False}
write(S/'checks/v21-source-identity.json',identity);write(S/'checks/v21-frozen-helpers.json',frozen);shutil.copy2(Path(__file__),S/'tools/prepare_compact_v21.py')
assert sha(B/'FILES.sha256.json')==BASE_MANIFEST and sha(W/'repo/.git/index')==initial['index_sha256']
print(json.dumps({'staging':str(S),'selected':len(selected),'excluded':len(excluded),'recovered_paths':len(recovered),'paired_projects':len(PROJECTS),'frozen_helpers':len(frozen),'seals':seals}))
