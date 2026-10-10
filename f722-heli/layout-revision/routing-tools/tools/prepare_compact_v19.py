#!/usr/bin/env python3
"""Capture bounded accepted PORT_A checkpoint evidence over immutable V18."""
import difflib, hashlib, json, lzma, shutil
from pathlib import Path
W=Path(__file__).resolve().parent.parent
B=W/'ordinary-routing/public-source-ready-v18';S=W/'ordinary-routing/public-source-ready-v19';F=W/'ordinary-routing/v19-helper-freeze'
BASE_ZIP='aa92e9f54083491d16d361f15ab0be522c1804b2959e9e1e1466c7f5f80b023b'
BASE_MANIFEST='c92ec914f36f2bb31eb134f55f6c2cdd3d163d6ad89a1d078243207a7f619256'
BOARDS={'candidate48':'dcdd0e5655d098ceaffa7f40b6a21f1ca101429ac8eb142c50fa96df86697e68','candidate49':'15499b28bb63a8c2326c8c7e73dbac4198b8333b05325ab35653825848ae9069'}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def info(p):return {'sha256':sha(p),'bytes':p.stat().st_size}
def read(p):return json.loads(Path(p).read_bytes())
def write(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2,sort_keys=True)+'\n')
assert sha(W/'ordinary-routing/routing-source-v18-delta.zip')==BASE_ZIP
assert sha(B/'FILES.sha256.json')==BASE_MANIFEST
assert not S.exists() and not F.exists()
shutil.copytree(B,S);F.mkdir()
for name in ['README.md','REPRODUCE.md','SOURCE_EVIDENCE.md','EXCLUDED_INPUTS.md','EVIDENCE_INDEX.json','status.json']:
 dest=S/'docs/historical-v18'/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(B/name,dest)
for name in ['FILES.sha256.json','PUBLIC_SOURCE_ALLOWLIST.json']:shutil.copy2(B/name,S/'checks'/('v18-original-'+name))
packet=S/'tests/checkpoint49';packet.mkdir();rec=S/'sessions/recovery-v19';rec.mkdir()
selected={};excluded={};recovered={};frozen={};aliases={}
required={name:info(W/'ordinary-routing/candidate48'/name) for name in read(B/'sessions/recovery-v18/paired-files.json')['required_base_files']}
def add(name,override=None):
 p=Path(override) if override else W/name
 assert p.is_file(),name
 if name.startswith('ordinary-routing/candidate') and '/'.join(name.split('/')[2:]) in required:
  recovered[name]=info(p)
 elif p.name in {'f722-heli.native.json','owner-native.json','native-geometry.json','owner-mechanical-geometry.json'} or p.suffix in {'.kicad_pcb','.pdf','.kicad_prl'}:
  excluded[name]=dict(info(p),reason='Raw native export, duplicate accepted PCB, vendor PDF or local application preferences omitted. Digest retained; native replay requires separately restored/regenerated hash-matching dependencies. No native geometry/refill/DRC/power replay is claimed.')
 else:
  if p.suffix=='.py':
   dest=F/name;dest.parent.mkdir(parents=True,exist_ok=True)
   if dest.exists():assert dest.read_bytes()==p.read_bytes(),name
   else:shutil.copy2(p,dest)
   frozen[name]=info(dest);selected[name]=dest
  else:selected[name]=p
  if override:aliases[name]=str(p.relative_to(W))
def tree(folder):
 for p in sorted((W/folder).rglob('*')):
  if p.is_file() and p.suffix in {'.json','.py','.md','.log','.png','.svg'} and '__pycache__' not in p.parts:add(str(p.relative_to(W)))
c='ordinary-routing/candidate49/';worker='ordinary-routing/tests/port-a48/'
assert sha(W/c/'f722-heli.kicad_pcb')==sha(W/worker/'candidate01/f722-heli.kicad_pcb')==BOARDS['candidate49']
for name,digest in read(W/c/'route-handoff.json')['files'].items():
 assert sha(W/c/name)==digest and sha(W/worker/'candidate01'/name)==digest,name
 add(c+name)
tree(c);tree('checkpoint29-review')
for p in sorted((W/c).glob('*.used.py')):add(worker+p.name.replace('.used.py','.py'),p)
for name in ['proposal.json','compact-mcu-proposal.json','rx-centered-In2.Cu.json','pad-access-comparison.json']:add(worker+name,W/c/name)
for name in ['f722-heli.kicad_pcb','f722-heli.native.json','f722-heli.logical-route-map.json','fixed-explicit-native-ids.json','poses-native.json','power-audit.json','project-input-preservation.json','protection-actual-io.json','adc-electrical-screen.json','owner-drc.json','reference-snapshot/native-geometry.json','reference-snapshot/native-signals.json','reference-snapshot/critical-reference.json']:add('ordinary-routing/candidate48/'+name)
for name in ['adopt_verified.py','refresh_accepted_checkpoint.py','review_ordinary_checkpoint.py','validate_checkpoint.py','check_coordinated_integration.py','verify_support_adoption.py','verify_reference_window_classification.py']:
 add('integrated-routing/'+name)
for name in ['native-tools/export_native_copper.py','native-tools/exact_native_contours.py','native-tools/check_protection_paths.py','tests/mpn-parity/apply_metadata_copy.py','dsm40-audits/audit_dsm40_entries_return.py','dsm41-audits/audit_dsm41_entries_return.py','servo23-audits/audit_rewritten_entries.py']:
 add('ordinary-routing/'+name)
for report,key in [(c+'adc-electrical-screen.json','sources'),(c+'reference-region-review/reference-classification.json','source_hashes')]:
 for name,digest in read(W/report)[key].items():
  assert sha(W/name)==digest,(report,name)
  add(name)
for name in ['checkpoint29-review-run.log']:
 if (W/name).is_file():add(name)
for name in ['checkpoint29-owner-review.json','current-status.json']:
 p='repo/f722-heli/layout-revision/checks/'+name
 if (W/p).is_file():add(p)
manifest={'schema':'f722-historical-paired-files/v1','base_label':'candidate48 / immutable V18 recovered candidate48','required_base_files':required,'sources':{}}
def delta(bp,tp,dest):
 before,after=bp.read_bytes(),tp.read_bytes();lines=before.splitlines(keepends=True);target=after.splitlines(keepends=True);offsets=[0]
 for line in lines:offsets.append(offsets[-1]+len(line))
 ops=[]
 for tag,i,j,k,l in difflib.SequenceMatcher(None,lines,target,autojunk=True).get_opcodes():
  if tag=='equal':ops.append([offsets[i],offsets[j]-offsets[i]])
  elif tag in {'insert','replace'}:ops.append(b''.join(target[k:l]).decode())
 write(dest,{'schema':'f722-historical-source-copy-delta/v1','base_sha256':sha(bp),'target_sha256':sha(tp),'target_bytes':len(after),'operations':ops})
for label in BOARDS:
 folder=W/'ordinary-routing'/label;entries={}
 for name,row in required.items():
  assert (folder/name).is_file()
  if sha(folder/name)!=row['sha256']:
   assert name=='f722-heli.kicad_pcb',name
   d=label+'.'+name+'.delta.json';delta(W/'ordinary-routing/candidate48'/name,folder/name,rec/d);entries[name]={'file':d,'sha256':sha(rec/d)}
  recovered['ordinary-routing/'+label+'/'+name]=info(folder/name)
 manifest['sources'][label]={'board_sha256':sha(folder/'f722-heli.kicad_pcb'),'deltas':entries}
write(rec/'paired-files.json',manifest)
src=(B/'sessions/recovery-v18/rebuild_historical_source.py').read_text().replace('candidate47 project recovered by V17','candidate48 project recovered by V18').replace("choices=('candidate47', 'candidate48')","choices=('candidate48', 'candidate49')")
(rec/'rebuild_historical_source.py').write_text(src)
index={'schema':'f722-selected-evidence/v2','files':{},'excluded_files':dict(sorted(excluded.items())),'recovered_files':dict(sorted(recovered.items())),'frozen_alias_sources':aliases,'scope':'Accepted candidate48 to49/29-open PORT_A MCU reconstruction only. Original138-file worker seal and separate owner extensions preserved. Historical raw native receipts are checked, not reexecuted. Unaccepted experimental routes are excluded.'}
for name,p in sorted(selected.items()):
 data=p.read_bytes();row=info(p)
 if len(data)>100_000:
  target='blobs/'+row['sha256']+'.xz';dest=packet/target;dest.parent.mkdir(parents=True,exist_ok=True)
  if not dest.exists():dest.write_bytes(lzma.compress(data,preset=1))
  row.update(compressed_file=target,compressed_sha256=sha(dest))
 else:
  target='files/'+name;dest=packet/target;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data);row['file']=target
 index['files'][name]=row
write(packet/'raw-evidence.json',index);write(F/'frozen-files.json',frozen)
(packet/'materialize.py').write_text((B/'tests/checkpoint48/materialize.py').read_text().replace('recovery-v18','recovery-v19').replace('recovery_v18','recovery_v19'))
(S/'tools/capture_v19_evidence.py').write_text((B/'tools/capture_v18_evidence.py').read_text().replace('V18','V19').replace('checkpoint48','checkpoint49'))
write(S/'checks/v19-source-identity.json',{'base_v18_zip_sha256':BASE_ZIP,'base_v18_manifest_sha256':BASE_MANIFEST,'expected_boards':BOARDS,'sealed_handoff':info(W/c/'route-handoff.json'),'sealed_worker_files':len(read(W/c/'route-handoff.json')['files']),'owner_extensions':info(W/c/'owner-receipt-extensions.json'),'freeze_manifest_sha256':sha(F/'frozen-files.json'),'frozen_helpers':frozen,'frozen_alias_sources':aliases,'selected_files':len(selected),'excluded_raw_files':len(excluded),'native_replay_inputs_complete':False,'I2C_electrical_status':'NOT_QUALIFIED','ADC_functional_qualification':False})
shutil.copy2(F/'frozen-files.json',S/'checks/v19-frozen-helpers.json');shutil.copy2(Path(__file__),S/'tools/prepare_compact_v19.py')
print(json.dumps({'staging':str(S),'selected':len(selected),'excluded':len(excluded),'recovered_paths':len(recovered),'paired_projects':2,'frozen_helpers':len(frozen)}))
