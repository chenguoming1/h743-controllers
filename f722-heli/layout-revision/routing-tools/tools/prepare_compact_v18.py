#!/usr/bin/env python3
"""Freeze bounded accepted ADC checkpoint evidence over immutable V17."""
import difflib, hashlib, json, lzma, shutil
from pathlib import Path
W=Path(__file__).resolve().parent.parent
B=W/'ordinary-routing/public-source-ready-v17'; S=W/'ordinary-routing/public-source-ready-v18'
F=W/'ordinary-routing/v18-helper-freeze'
BASE_ZIP='d87f7e9a0e9ab14de4668fe09031d01e272073b4a827c755a465866ae3d002c8'
BASE_MANIFEST='cad265201d7fa7e4260bb66d83e5027cce81ea0ee8e4d2c04d4b0204e503ca6e'
BOARDS={'candidate47':'f7d5731bb0bf1ad314aca6d507da004993671bce413fbdeba545083168e28161','candidate48':'dcdd0e5655d098ceaffa7f40b6a21f1ca101429ac8eb142c50fa96df86697e68'}
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def info(p):return {'sha256':sha(p),'bytes':p.stat().st_size}
def read(p):return json.loads(Path(p).read_bytes())
def write(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2,sort_keys=True)+'\n')
assert sha(W/'ordinary-routing/routing-source-v17-delta.zip')==BASE_ZIP
assert sha(B/'FILES.sha256.json')==BASE_MANIFEST
assert not S.exists()
shutil.copytree(B,S)
for name in ['README.md','REPRODUCE.md','SOURCE_EVIDENCE.md','EXCLUDED_INPUTS.md','EVIDENCE_INDEX.json','status.json']:
 dest=S/'docs/historical-v17'/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(B/name,dest)
for name in ['FILES.sha256.json','PUBLIC_SOURCE_ALLOWLIST.json']:shutil.copy2(B/name,S/'checks'/('v17-original-'+name))
packet=S/'tests/checkpoint48';packet.mkdir();rec=S/'sessions/recovery-v18';rec.mkdir()
selected={};excluded={};recovered={}
required={name:info(W/'ordinary-routing/candidate47'/name) for name in read(B/'sessions/recovery-v17/paired-files.json')['required_base_files']}
def add(name):
 p=F/name if (F/name).is_file() else W/name
 assert p.is_file(),name
 if name.startswith('ordinary-routing/candidate') and '/'.join(name.split('/')[2:]) in required:
  recovered[name]=info(p)
 elif p.name in {'f722-heli.native.json','owner-native.json','native-geometry.json','owner-mechanical-geometry.json'} or p.suffix in {'.kicad_pcb','.pdf'}:
  excluded[name]=dict(info(p),reason='Raw native/placement export or original vendor PDF excluded; exact digest retained. Native replay requires separately restored or regenerated hash-matching inputs and KiCad 10. PDF extracted text and source URL are included. Portable checks do not rerun native geometry, finite cuts, DRC, refill or power.')
 else:selected[name]=p
def tree(folder):
 for p in sorted((W/folder).rglob('*')):
  if p.is_file() and p.suffix in {'.json','.py','.md','.log','.png','.svg'} and '__pycache__' not in p.parts:add(str(p.relative_to(W)))
c='ordinary-routing/candidate48/';worker='ordinary-routing/tests/adc-bus45/'
assert sha(W/c/'f722-heli.kicad_pcb')==sha(W/worker/'candidate01/f722-heli.kicad_pcb')==BOARDS['candidate48']
for name in read(W/c/'route-handoff.json')['files']:add(c+name)
tree(c);tree('checkpoint30-review')
for name in read(W/c/'input-hashes.json'):add(name)
for name in ['proposal.json','trunk-In3.Cu46.json','proposal.log','construct47.log','audit47.log','electrical47.log','extra47.log','classification47.log','seal47.log','plot-final.log']:
 add(worker+name)
for name in ['f722-heli.kicad_pcb','f722-heli.native.json','f722-heli.logical-route-map.json','fixed-explicit-native-ids.json','poses-native.json','power-audit.json','project-input-preservation.json','protection-actual-io.json','reference-snapshot/native-geometry.json','reference-snapshot/native-signals.json','reference-snapshot/critical-reference.json']:
 add('ordinary-routing/candidate47/'+name)
for name in ['adopt_verified.py','refresh_accepted_checkpoint.py','review_ordinary_checkpoint.py','validate_checkpoint.py','check_coordinated_integration.py','verify_support_adoption.py','verify_footprint_transforms.py','verify_reference_window_classification.py','reproduce_placement_checkpoint.py','render_placement_previews.py','test_footprint_transforms.py','footprint-transform-controls.json','transform-integration-controls.json','reference-window-binding-controls.json','test_support_adoption.py','support-adoption-controls.json']:
 add('integrated-routing/'+name)
for name in ['native-tools/export_native_copper.py','native-tools/exact_native_contours.py','native-tools/check_protection_paths.py','tests/mpn-parity/apply_metadata_copy.py','servo23-audits/audit_rewritten_entries.py','dsm41-audits/input-hashes.json']:
 add('ordinary-routing/'+name)
for report,key in [(c+'adc-electrical-screen.json','sources'),(c+'reference-region-review/reference-classification.json','source_hashes'),('checkpoint30-review/reference-region/owner/reference-classification.json','source_hashes')]:
 for name,digest in read(W/report)[key].items():
  assert sha(W/name)==digest,(report,name)
  add(name)
# Preserve complete placement reproduction and previews, without native preview boards.
tree('repro-30-placement/scripts')
for name in ['source.json','placement.json','placement-build.json','metadata-changes.json','parity.json','placement-reproduction.json','build.log','metadata.log','parity.log','hardware/f722-heli.kicad_pcb']:
 add('repro-30-placement/'+name)
tree('checkpoint30-placement-preview');add('checkpoint30-placement-preview/preview.kicad_pcb')
for name in ['checkpoint30-owner-review.json','current-status.json','routing-build.json']:
 p='repo/f722-heli/layout-revision/checks/'+name
 if (W/p).is_file():add(p)
for name in ['checkpoint30-reference-classification.log','checkpoint30-refresh.log','checkpoint30-placement-preview.log','repro-30-placement-launch.log']:add(name)
manifest={'schema':'f722-historical-paired-files/v1','base_label':'candidate47 / immutable V17 recovered candidate47','required_base_files':required,'sources':{}}
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
   d=label+'.'+name+'.delta.json';delta(W/'ordinary-routing/candidate47'/name,folder/name,rec/d);entries[name]={'file':d,'sha256':sha(rec/d)}
  recovered['ordinary-routing/'+label+'/'+name]=info(folder/name)
 manifest['sources'][label]={'board_sha256':sha(folder/'f722-heli.kicad_pcb'),'deltas':entries}
write(rec/'paired-files.json',manifest)
src=(B/'sessions/recovery-v17/rebuild_historical_source.py').read_text().replace('candidate45 project recovered by V16','candidate47 project recovered by V17').replace("choices=('candidate45', 'candidate46', 'candidate47')","choices=('candidate47', 'candidate48')")
(rec/'rebuild_historical_source.py').write_text(src)
index={'schema':'f722-selected-evidence/v2','files':{},'excluded_files':dict(sorted(excluded.items())),'recovered_files':dict(sorted(recovered.items())),'scope':'Accepted candidate48/30-open ADC_BUS construction and owner adoption over paired candidate47. Preserves full finite entry/support/topology proof, electrical source screen, fresh classifier and placement receipts. No isolated flash/PORT_C hypotheses. Native reports are preserved, not reexecuted.'}
for name,p in sorted(selected.items()):
 data=p.read_bytes();row=info(p)
 if len(data)>100_000:
  target='blobs/'+row['sha256']+'.xz';dest=packet/target;dest.parent.mkdir(parents=True,exist_ok=True)
  if not dest.exists():dest.write_bytes(lzma.compress(data,preset=1))
  row.update(compressed_file=target,compressed_sha256=sha(dest))
 else:
  target='files/'+name;dest=packet/target;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data);row['file']=target
 index['files'][name]=row
write(packet/'raw-evidence.json',index)
(packet/'materialize.py').write_text((B/'tests/checkpoint47/materialize.py').read_text().replace('recovery-v17','recovery-v18').replace('recovery_v17','recovery_v18'))
(S/'tools/capture_v18_evidence.py').write_text((B/'tools/capture_v17_evidence.py').read_text().replace('V17','V18').replace('checkpoint47','checkpoint48'))
write(S/'checks/v18-source-identity.json',{'base_v17_zip_sha256':BASE_ZIP,'base_v17_manifest_sha256':BASE_MANIFEST,'expected_boards':BOARDS,'sealed_handoff':info(W/c/'route-handoff.json'),'isolated_accepted_board_byte_identity':info(W/worker/'candidate01/f722-heli.kicad_pcb'),'freeze_manifest_sha256':sha(F/'frozen-files.json'),'frozen_helpers':{n:row for n,row in read(F/'frozen-files.json').items() if n in selected},'selected_files':len(selected),'excluded_raw_files':len(excluded),'native_replay_inputs_complete':False,'I2C_electrical_status':'NOT_QUALIFIED','ADC_functional_qualification':False})
shutil.copy2(F/'frozen-files.json',S/'checks/v18-frozen-helpers.json')
shutil.copy2(Path(__file__),S/'tools/prepare_compact_v18.py')
print(json.dumps({'staging':str(S),'selected':len(selected),'excluded':len(excluded),'recovered_paths':len(recovered),'paired_projects':2}))
