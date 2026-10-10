#!/usr/bin/env python3
"""Freeze bounded V17 evidence over immutable V16; no native execution."""
import difflib, hashlib, json, lzma, shutil
from pathlib import Path
W=Path(__file__).resolve().parent.parent
B=W/'ordinary-routing/public-source-ready-v16'; S=W/'ordinary-routing/public-source-ready-v17'
F=W/'ordinary-routing/v17-helper-freeze'
BASE_ZIP='1f3cccf99ad6d3cb593954c68afa145a695a6256054ea511cf7228f4fda5e5aa'
BASE_MANIFEST='7f665e9a4871b578affd4e37e05d281c5818fe8d46367053f3f01c76c86e5b8a'
BOARDS={'candidate45':'9881a992b12fed90f17131ed627f12af77680cc2ddf95030adf8c564aaa24eb2','candidate46':'87c5ced471edaf2e0ace382d4236bc1787efb869b7ae759c53d87ee76165c0cb','candidate47':'f7d5731bb0bf1ad314aca6d507da004993671bce413fbdeba545083168e28161'}
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def info(p):return {'sha256':sha(p),'bytes':p.stat().st_size}
def read(p):return json.loads(Path(p).read_bytes())
def write(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2,sort_keys=True)+'\n')
assert sha(W/'ordinary-routing/routing-source-v16-delta.zip')==BASE_ZIP
assert sha(B/'FILES.sha256.json')==BASE_MANIFEST
assert not S.exists()
shutil.copytree(B,S)
for name in ['README.md','REPRODUCE.md','SOURCE_EVIDENCE.md','EXCLUDED_INPUTS.md','EVIDENCE_INDEX.json','status.json']:
 dest=S/'docs/historical-v16'/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(B/name,dest)
for name in ['FILES.sha256.json','PUBLIC_SOURCE_ALLOWLIST.json']:shutil.copy2(B/name,S/'checks'/('v16-original-'+name))
packet=S/'tests/checkpoint47';packet.mkdir();rec=S/'sessions/recovery-v17';rec.mkdir()
selected={};excluded={};recovered={}
required={name:info(W/'ordinary-routing/candidate45'/name) for name in read(B/'sessions/recovery-v16/paired-files.json')['required_base_files']}
def add(name):
 p=F/name if (F/name).is_file() else W/name
 assert p.is_file(),name
 if name.startswith('ordinary-routing/candidate') and '/'.join(name.split('/')[2:]) in required:
  recovered[name]=info(p)
 elif p.name in {'f722-heli.native.json','owner-native.json','native-geometry.json','owner-mechanical-geometry.json'}:
  excluded[name]=dict(info(p),reason='Large native/mechanical export omitted. Restore or regenerate with the paired board, pinned exporter and KiCad 10, then match this exact hash before native replay. Portable checks do not rerun geometry, finite pad/annular cuts, DRC, refill or power.')
 else:selected[name]=p
def tree(folder):
 for p in sorted((W/folder).rglob('*')):
  if p.is_file() and p.suffix in {'.json','.py','.md','.log'} and '__pycache__' not in p.parts:add(str(p.relative_to(W)))
for number,checkpoint in [(46,33),(47,32)]:
 c=f'ordinary-routing/candidate{number}/';h=f'ordinary-routing/tests/hv{number-1}/'
 assert sha(W/c/'f722-heli.kicad_pcb')==BOARDS[f'candidate{number}']
 assert sha(W/h/'candidate01/f722-heli.kicad_pcb')==BOARDS[f'candidate{number}']
 for name in read(W/c/'route-handoff.json')['files']:add(c+name)
 tree(c);tree(f'checkpoint{checkpoint}-review')
 for name in read(W/c/'input-hashes.json'):add(name)
 for name in ['rpm-F-final-proposal.json','rpm-F-route.json','refinement-history.json'] if number==46 else ['complete-joint-proposal.json','complete-joint-refined.json','local-repair-results.json','refined-local-repair-results.json','planned_adc_obstacles.json']:
  add(h+name)
 for name in ['construct.log','extra-gates.log']:
  if (W/h/name).exists():add(h+name)
for name in ['f722-heli.kicad_pcb','f722-heli.native.json','f722-heli.logical-route-map.json','fixed-explicit-native-ids.json','poses-native.json','power-audit.json','reference-snapshot/native-geometry.json','reference-snapshot/native-signals.json','reference-snapshot/critical-reference.json']:
 add('ordinary-routing/candidate45/'+name)
helpers=['integrated-routing/'+x for x in ['adopt_verified.py','refresh_accepted_checkpoint.py','review_ordinary_checkpoint.py','validate_checkpoint.py','check_additive_integration.py','check_coordinated_integration.py','verify_support_adoption.py']]
helpers+=['ordinary-routing/'+x for x in ['native-tools/export_native_copper.py','native-tools/exact_native_contours.py','native-tools/check_protection_paths.py','tests/mpn-parity/apply_metadata_copy.py','servo23-audits/audit_rewritten_entries.py','dsm41-audits/input-hashes.json']]
helpers+=['repo/f722-heli/layout-revision/signal-review/native/'+x for x in ['check_signal_geometry.py','compare_reference_geometry.py','check_critical_reference.py','export_signal_snapshot.py','native_io_graph.py'] if (W/'repo/f722-heli/layout-revision/signal-review/native'/x).is_file()]
for name in helpers:add(name)
manifest={'schema':'f722-historical-paired-files/v1','base_label':'candidate45 / immutable V16 recovered candidate45','required_base_files':required,'sources':{}}
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
   d=label+'.'+name+'.delta.json';delta(W/'ordinary-routing/candidate45'/name,folder/name,rec/d);entries[name]={'file':d,'sha256':sha(rec/d)}
  recovered['ordinary-routing/'+label+'/'+name]=info(folder/name)
 manifest['sources'][label]={'board_sha256':sha(folder/'f722-heli.kicad_pcb'),'deltas':entries}
write(rec/'paired-files.json',manifest)
src=(B/'sessions/recovery-v16/rebuild_historical_source.py').read_text().replace('candidate44 project recovered by V15','candidate45 project recovered by V16').replace("choices=('candidate44', 'candidate45')","choices=('candidate45', 'candidate46', 'candidate47')")
(rec/'rebuild_historical_source.py').write_text(src)
index={'schema':'f722-selected-evidence/v2','files':{},'excluded_files':dict(sorted(excluded.items())),'recovered_files':dict(sorted(recovered.items())),'scope':'Exact accepted RPM candidate46/33 and coordinated SBUS candidate47/32 source/evidence. Candidate47 includes its sealed narrow planned-ADC compatibility dependency only; no isolated ADC, flash or PORT_C candidate is included. Stored native controls are preserved; portable verification does not rerun them.'}
for name,p in sorted(selected.items()):
 data=p.read_bytes();row=info(p)
 if len(data)>100_000:
  target='blobs/'+row['sha256']+'.json.xz';dest=packet/target;dest.parent.mkdir(parents=True,exist_ok=True)
  if not dest.exists():dest.write_bytes(lzma.compress(data,preset=1))
  row.update(compressed_file=target,compressed_sha256=sha(dest))
 else:
  target='files/'+name;dest=packet/target;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data);row['file']=target
 index['files'][name]=row
write(packet/'raw-evidence.json',index)
(packet/'materialize.py').write_text((B/'tests/checkpoint45/materialize.py').read_text().replace('recovery-v16','recovery-v17').replace('recovery_v16','recovery_v17'))
(S/'tools/capture_v17_evidence.py').write_text((B/'tools/capture_v16_evidence.py').read_text().replace('V16','V17').replace('checkpoint45','checkpoint47'))
write(S/'checks/v17-source-identity.json',{'base_v16_zip_sha256':BASE_ZIP,'base_v16_manifest_sha256':BASE_MANIFEST,'expected_boards':BOARDS,'sealed_handoffs':{str(n):info(W/f'ordinary-routing/candidate{n}/route-handoff.json') for n in (46,47)},'frozen_helpers':{n:row for n,row in read(F/'frozen-files.json').items() if n in selected},'selected_files':len(selected),'excluded_raw_files':len(excluded),'native_replay_inputs_complete':False,'I2C_electrical_status':'NOT_QUALIFIED'})
shutil.copy2(Path(__file__),S/'tools/prepare_compact_v17.py')
print(json.dumps({'staging':str(S),'selected':len(selected),'excluded':len(excluded),'recovered_paths':len(recovered),'paired_projects':3}))
