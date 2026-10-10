#!/usr/bin/env python3
"""Prepare bounded V16 TP5/NRST evidence over immutable V15; no native execution."""
import difflib, hashlib, json, lzma, shutil
from pathlib import Path
W=Path(__file__).resolve().parent.parent
B=W/'ordinary-routing/public-source-ready-v15'; S=W/'ordinary-routing/public-source-ready-v16'
BASE_ZIP='8fca33afdf93c3dd0df5c21a87e18c40d54406b70e82398cdb5abbd94a100285'
BASE_MANIFEST='f3a51c6ba4ed04a51a48b77c1789a8de5d693f72b97cb40b5c65869732a09b93'
C44='ordinary-routing/candidate44/';C45='ordinary-routing/candidate45/'
F=W/'ordinary-routing/v16-owner-helper-freeze'
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def info(p):return {'sha256':sha(p),'bytes':p.stat().st_size}
def read(p):return json.loads(Path(p).read_bytes())
def write(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2,sort_keys=True)+'\n')
assert sha(W/'ordinary-routing/routing-source-v15-delta.zip')==BASE_ZIP
assert sha(B/'FILES.sha256.json')==BASE_MANIFEST
assert not S.exists()
shutil.copytree(B,S)
for name in ['README.md','REPRODUCE.md','SOURCE_EVIDENCE.md','EXCLUDED_INPUTS.md','EVIDENCE_INDEX.json','status.json']:
 dest=S/'docs/historical-v15'/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(B/name,dest)
for name in ['FILES.sha256.json','PUBLIC_SOURCE_ALLOWLIST.json']:shutil.copy2(B/name,S/'checks'/('v15-original-'+name))
packet=S/'tests/checkpoint45';packet.mkdir();rec=S/'sessions/recovery-v16';rec.mkdir()
selected={};excluded={};recovered={}
required={name:info(W/C44/name) for name in read(B/'sessions/recovery44/paired-files.json')['required_base_files']}
paired=set(required)
def add(name):
 p=W/name
 if name.startswith('integrated-routing/') and (F/Path(name).name).is_file():p=F/Path(name).name
 assert p.is_file(),name
 suffix=Path(name).suffix
 if suffix=='.kicad_pcb' or any(name==prefix+n for prefix in [C44,C45] for n in paired):recovered[name]=info(p)
 elif Path(name).name in {'f722-heli.native.json','owner-native.json','native-geometry.json','owner-mechanical-geometry.json','debug-native.json'}:
  excluded[name]=dict(info(p),reason='Large native/mechanical geometry omitted; exact hash required after regeneration with the paired board and pinned exporters/KiCad. Portable checks preserve receipts and do not rerun raw geometry, finite-width/probe/native transform/DRC controls or original runtime-index proof.')
 else:selected[name]=p

def tree(folder):
 for p in sorted((W/folder).rglob('*')):
  if p.is_file() and p.suffix in {'.json','.py','.md','.log','.png','.svg'} and '__pycache__' not in p.parts:add(str(p.relative_to(W)))
assert sha(W/C45/'f722-heli.kicad_pcb')=='9881a992b12fed90f17131ed627f12af77680cc2ddf95030adf8c564aaa24eb2'
assert sha(W/'ordinary-routing/tests/debug-testpoint44/candidate01/f722-heli.kicad_pcb')==sha(W/C45/'f722-heli.kicad_pcb')
for n in read(W/C45/'route-handoff.json')['files']:add(C45+n)
tree(C45);tree('checkpoint34-review')
for p in (W/'ordinary-routing/tests/debug-testpoint44').iterdir():
 if p.is_file() and p.suffix in {'.json','.py','.md','.log'}:add(str(p.relative_to(W)))
for n in read(W/C45/'input-hashes.json'):add(n)
for n in ['f722-heli.kicad_pcb','f722-heli.logical-route-map.json','fixed-explicit-native-ids.json','owner-mechanical-geometry.json','reference-snapshot/native-geometry.json','reference-snapshot/native-signals.json','reference-snapshot/critical-reference.json']:add(C44+n)
for n in ['verify_reference_runtime_indices.py','test_reference_runtime_indices.py','refresh_accepted_checkpoint.py','review_ordinary_checkpoint.py','adopt_verified.py','check_coordinated_integration.py','verify_support_adoption.py','verify_footprint_transforms.py','test_footprint_transforms.py','footprint-transform-controls.json']:add('integrated-routing/'+n)
for n in ['native-tools/export_native_copper.py','native-tools/exact_native_contours.py','tests/mpn-parity/apply_metadata_copy.py']:add('ordinary-routing/'+n)
for n in ['check_signal_geometry.py','compare_reference_geometry.py']:add('repo/f722-heli/layout-revision/signal-review/native/'+n)
for folder in ['repro-34-placement','checkpoint34-placement-preview']:
 for p in sorted((W/folder).rglob('*')):
  if p.is_file() and 'hardware' not in p.relative_to(W/folder).parts and p.suffix in {'.json','.py','.log','.png','.svg'}:add(str(p.relative_to(W)))
# Preserve exact handoff pose-reference target without duplicating the full worker project.
add('ordinary-routing/tests/debug-testpoint44/candidate01/poses-native.json')
manifest={'schema':'f722-historical-paired-files/v1','base_label':'candidate44 / immutable V15 accepted44','required_base_files':required,'sources':{}}
def delta(bp,tp,dest):
 before,after=bp.read_bytes(),tp.read_bytes();lines=before.splitlines(keepends=True);target=after.splitlines(keepends=True);offsets=[0]
 for line in lines:offsets.append(offsets[-1]+len(line))
 ops=[]
 for tag,i,j,k,l in difflib.SequenceMatcher(None,lines,target,autojunk=True).get_opcodes():
  if tag=='equal':ops.append([offsets[i],offsets[j]-offsets[i]])
  elif tag in {'insert','replace'}:ops.append(b''.join(target[k:l]).decode())
 write(dest,{'schema':'f722-historical-source-copy-delta/v1','base_sha256':sha(bp),'target_sha256':sha(tp),'target_bytes':len(after),'operations':ops})
for label in ['candidate44','candidate45']:
 folder=W/'ordinary-routing'/label;entries={}
 for name,row in required.items():
  assert (folder/name).is_file()
  if sha(folder/name)!=row['sha256']:
   assert name=='f722-heli.kicad_pcb',name
   d=label+'.'+name+'.delta.json';delta(W/C44/name,folder/name,rec/d);entries[name]={'file':d,'sha256':sha(rec/d)}
  recovered['ordinary-routing/'+label+'/'+name]=info(folder/name)
 manifest['sources'][label]={'board_sha256':sha(folder/'f722-heli.kicad_pcb'),'deltas':entries}
write(rec/'paired-files.json',manifest)
src=(B/'sessions/recovery44/rebuild_historical_source.py').read_text().replace('candidate43 project recovered by V14','candidate44 project recovered by V15').replace("choices=('candidate43', 'candidate44')","choices=('candidate44', 'candidate45')")
(rec/'rebuild_historical_source.py').write_text(src)
index={'schema':'f722-selected-evidence/v2','files':{},'excluded_files':dict(sorted(excluded.items())),'recovered_files':dict(sorted(recovered.items())),'scope':'Exact candidate44-to-adopted45/34 TP5/NRST source/evidence only. Original raw comparator false and all83 net_code differences preserved beside separate153-record physical-equality proof. Five owner source-refusal, six worker physical-mutation and five finite/probe controls preserved; raw/native reruns require omitted hash-bound inputs.'}
for name,p in sorted(selected.items()):
 data=p.read_bytes();row=info(p)
 if len(data)>1_000_000:
  target='blobs/'+row['sha256']+'.json.xz';dest=packet/target;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(lzma.compress(data,preset=1));row.update(compressed_file=target,compressed_sha256=sha(dest))
 else:
  target='files/'+name;dest=packet/target;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data);row['file']=target
 index['files'][name]=row
write(packet/'raw-evidence.json',index)
(packet/'materialize.py').write_text((B/'tests/checkpoint44/materialize.py').read_text().replace('recovery44','recovery-v16').replace("spec_from_file_location('recovery-v16'","spec_from_file_location('recovery_v16'"))
(S/'tools/capture_v16_evidence.py').write_text((B/'tools/capture_v15_evidence.py').read_text().replace('V15','V16').replace('checkpoint44','checkpoint45'))
write(S/'checks/v16-source-identity.json',{'base_v15_zip_sha256':BASE_ZIP,'base_v15_manifest_sha256':BASE_MANIFEST,'expected_boards':{k:v['board_sha256'] for k,v in manifest['sources'].items()},'sealed_handoff_sha256':sha(W/C45/'route-handoff.json'),'sealed_dependencies':len(read(W/C45/'route-handoff.json')['files']),'owner_review_sha256':sha(W/'checkpoint34-review/owner-runtime-index-verification.json'),'frozen_owner_helpers':read(F/'frozen-files.json'),'selected_files':len(selected),'excluded_raw_files':len(excluded),'native_replay_inputs_complete':False,'raw_critical_object_geometry_identical':False,'raw_net_index_differences':83,'separate_physical_reference_records':153,'I2C_electrical_status':'NOT_QUALIFIED'})
shutil.copy2(Path(__file__),S/'tools/prepare_compact_v16.py')
print(json.dumps({'staging':str(S),'selected':len(selected),'excluded':len(excluded),'recovered_paths':len(recovered),'paired_projects':2}))
