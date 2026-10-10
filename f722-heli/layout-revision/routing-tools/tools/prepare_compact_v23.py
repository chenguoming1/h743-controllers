#!/usr/bin/env python3
"""Capture accepted55 source and review evidence over immutable V22; no native run."""
import argparse,difflib,hashlib,json,lzma,os,shutil,subprocess
from pathlib import Path
BASE_MANIFEST='a5bad034de1e93f23d78b86bfac94ab9ce474d7dfa728940dccfe0f4cf430a4a'
BASE_ZIP='c86634257a5c5a6ffa6a09a3f6679b8a4406832c3bdcdce406880e3b3955defb'
PROJECTS={'candidate55':'ordinary-routing/candidate55','sealed56':'ordinary-routing/tests/native13-access/candidate02','candidate56':'ordinary-routing/candidate56'}
BEFORE='14dea1df09ea9d800bf66a6d74eb5f0dac33a8705161e9ed1a02f2e11f3b58b8'
AFTER='9d9f2f39c2b200f2c928dd3123f098797eb86ba56cb943d7f6e3fe89bf264a7e'
BOARDS={'candidate55':BEFORE,'sealed56':AFTER,'candidate56':AFTER}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def info(p):return {'sha256':sha(p),'bytes':Path(p).stat().st_size}
def read(p):return json.loads(Path(p).read_bytes())
def write(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,indent=2,sort_keys=True)+'\n')
ap=argparse.ArgumentParser();ap.add_argument('--workspace',type=Path,required=True);a=ap.parse_args()
W=a.workspace.resolve();B=W/'ordinary-routing/public-source-ready-v22';S=W/'ordinary-routing/public-source-ready-v23'
assert sha(B/'FILES.sha256.json')==BASE_MANIFEST and sha(W/'ordinary-routing/routing-source-v22-delta.zip')==BASE_ZIP
assert all(sha(B/n)==h for n,h in read(B/'FILES.sha256.json').items())
assert not S.exists()
initial={'index_sha256':sha(W/'repo/.git/index'),'head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=W/'repo',text=True).strip(),'canonical_board':info(W/'repo/f722-heli/layout-revision/hardware/f722-heli.kicad_pcb')}
assert initial['canonical_board']['sha256']==AFTER
shutil.copytree(B,S,copy_function=os.link)
replace=['README.md','REPRODUCE.md','SOURCE_EVIDENCE.md','EXCLUDED_INPUTS.md','EVIDENCE_INDEX.json','status.json','FILES.sha256.json','PUBLIC_SOURCE_ALLOWLIST.json','checks/source-package-validation.json']
for n in replace:(S/n).unlink()
for n in replace[:6]:
 p=S/'docs/historical-v22'/n;p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(B/n,p)
for n in ['FILES.sha256.json','PUBLIC_SOURCE_ALLOWLIST.json']:shutil.copy2(B/n,S/'checks'/('v22-original-'+n))
P=S/'tests/checkpoint56';P.mkdir();REC=S/'sessions/recovery-v23';REC.mkdir()
required={n:info(W/PROJECTS['candidate55']/n)for n in read(B/'sessions/recovery-v22/paired-files.json')['required_base_files']}
selected={};excluded={};recovered={};frozen={};aliases={}
def add(n,source=None):
 p=W/(source or n);assert p.is_file(),n
 for folder in PROJECTS.values():
  if n.startswith(folder+'/') and n[len(folder)+1:] in required:recovered[n]=info(p);return
 if p.name in {'f722-heli.native.json','owner-native.json','native-geometry.json','owner-mechanical-geometry.json','model.json'} or p.suffix in {'.kicad_pcb','.kicad_prl','.pdf'}:
  excluded[n]=dict(info(p),reason='Hash-pinned raw native export, duplicate board, local preference or vendor PDF omitted. Exact project recovery is separate; native replay requires omitted inputs and is not claimed.');return
 if n in selected:assert selected[n].read_bytes()==p.read_bytes(),n
 selected[n]=p
 if p.suffix=='.py':frozen[n]=info(p)
 if source:aliases[n]=source
def tree(folder):
 for p in sorted((W/folder).rglob('*')):
  if p.is_file() and '__pycache__' not in p.parts and p.suffix not in {'.pyc','.pyo'}:add(str(p.relative_to(W)))
for label,folder in PROJECTS.items():
 assert sha(W/folder/'f722-heli.kicad_pcb')==BOARDS[label]
 if label!='candidate55':tree(folder)
sealed=W/PROJECTS['sealed56'];accepted=W/PROJECTS['candidate56'];hand=read(sealed/'route-handoff.json')
assert len(hand['files'])==133 and sha(accepted/'route-handoff.json')==sha(sealed/'route-handoff.json')
for n,h in hand['files'].items():
 assert sha(sealed/n)==h
 assert sha(accepted/('power-audit-sealed-original.json'if n=='power-audit.json'else n))==h,n
for p in sealed.glob('*.used.py'):
 if p.name=='construct.used.py':continue
 n='ordinary-routing/tests/'+('servo48/validate_checkpoint.py'if p.name=='validate_checkpoint.used.py'else 'native13-access/'+p.stem.removesuffix('.used')+'.py')
 add(n,str(p.relative_to(W)))
add('ordinary-routing/tests/native13-access/R4-pullup-complete-proposal55-v2.json',str((sealed/'proposal.json').relative_to(W)))
for folder in ['checkpoint12-owner-review','checkpoint12-R4-placement-reproduction','checkpoint12-R4-placement-preview','ordinary-routing/tests/native13-access/electrical-review02']:tree(folder)
for p in (sealed/'bound-receipts').glob('*.json'):add('ordinary-routing/tests/native13-access/'+p.name,str(p.relative_to(W)))
# Exact prior snapshot required by the independent reference comparison.
for name in ['native-geometry.json','native-signals.json','critical-reference.json']:add('checkpoint13-owner-review/snapshot/'+name)
# Constructors and validation tools are frozen at their exact runtime paths.
for folder in ['integrated-routing','ordinary-routing/native-tools','repo/f722-heli/layout-revision/scripts','repo/f722-heli/layout-revision/signal-review/native','repo/f722-heli/layout-revision/protection-review/tools']:
 for p in sorted((W/folder).glob('*.py')):add(str(p.relative_to(W)))
for n in ['ordinary-routing/tests/mpn-parity/apply_metadata_copy.py','ordinary-routing/dsm40-audits/audit_dsm40_entries_return.py','ordinary-routing/dsm41-audits/audit_dsm41_entries_return.py','repo/f722-heli/layout-revision/checks/bind_stock_spi_review.py','repo/f722-heli/layout-revision/checks/reconstructed.net','repo/f722-heli/layout-revision/checks/protection/candidate-contracts.json','repo/f722-heli/layout-revision/checks/protection/supplemental-contracts.json','repo/f722-heli/validation/firmware-pinmap.json','repo/f722-heli/layout-revision/signal-review/native/model-inputs.template.json','repo/f722-heli/layout-revision/signal-review/final-native-i2c-requirements.json','repo/f722-heli/layout-revision/signal-review/stock-i2c-calculations.json']:add(n)
tree('repo/f722-heli/layout-revision/protection-review/contracts');tree('repo/f722-heli/layout-revision/spi-review')
for n in ['f722-heli.native.json','f722-heli.logical-route-map.json','fixed-explicit-native-ids.json','poses-native.json','power-audit.json','project-input-preservation.json','protection-actual-io.json','reference-snapshot/native-geometry.json','reference-snapshot/native-signals.json','reference-snapshot/critical-reference.json','owner-summary.json']:add(PROJECTS['candidate55']+'/'+n)
tree('repo/f722-heli/layout-revision/checks/checkpoint56-integration')
# Exact 61-file paired recovery. Sealed and accepted55 have identical native projects.
manifest={'schema':'f722-historical-paired-files/v1','base_label':'candidate55 / immutable V22 recovery','required_base_files':required,'sources':{}}
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
 for n,row in required.items():
  p=W/folder/n;assert p.is_file()
  if sha(p)!=row['sha256']:
   assert n=='f722-heli.kicad_pcb';d='candidate56.'+n+'.delta.json'
   if not (REC/d).exists():delta(W/PROJECTS['candidate55']/n,p,REC/d)
   entries[n]={'file':d,'sha256':sha(REC/d)}
  recovered[folder+'/'+n]=info(p)
 manifest['sources'][label]={'board_sha256':BOARDS[label],'deltas':entries,'workspace_path':folder,'status':'sealed construction alias; owner adoption separate'if label=='sealed56'else'accepted geometric checkpoint'}
write(REC/'paired-files.json',manifest)
src=(B/'sessions/recovery-v22/rebuild_historical_source.py').read_text().replace('candidate54 project recovered by V21','candidate55 project recovered by V22').replace("choices=('candidate54', 'sealed55', 'candidate55')","choices="+repr(tuple(PROJECTS)))
(REC/'rebuild_historical_source.py').write_text(src)
index={'schema':'f722-selected-evidence/v2','files':{},'excluded_files':dict(sorted(excluded.items())),'recovered_files':dict(sorted(recovered.items())),'frozen_alias_sources':aliases,'scope':'Accepted55 to accepted56; original sealed56 source and owner adapter remain distinct. Source-bound owner reference/signal/placement evidence; all V22 lineage preserved.'}
content_targets={}
for n,p in sorted(selected.items()):
 data=p.read_bytes();row=info(p);h=row['sha256']
 if h in content_targets:row.update(content_targets[h])
 elif len(data)>100000:
  target='blobs/'+h+'.xz';dest=P/target;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(lzma.compress(data,preset=1));row.update(compressed_file=target,compressed_sha256=sha(dest));content_targets[h]={k:row[k]for k in ('compressed_file','compressed_sha256')}
 else:
  target='files/'+n;dest=P/target;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data);row['file']=target;content_targets[h]={'file':target}
 index['files'][n]=row
write(P/'raw-evidence.json',index)
(P/'materialize.py').write_text((B/'tests/checkpoint55/materialize.py').read_text().replace('recovery-v22','recovery-v23').replace('recovery_v22','recovery_v23'))
identity={'schema':'f722-v23-frozen-source-identity/v1','base_v22_manifest_sha256':BASE_MANIFEST,'base_v22_zip_sha256':BASE_ZIP,'expected_boards':BOARDS,'projects':PROJECTS,'sealed_worker_manifest':{'files':133,'manifest':info(sealed/'route-handoff.json'),'path':PROJECTS['sealed56']},'owner_adapter':{'path':PROJECTS['candidate56']+'/power-audit.json',**info(accepted/'power-audit.json'),'original':info(accepted/'power-audit-sealed-original.json')},'frozen_helpers':frozen,'frozen_alias_sources':aliases,'selected_files':len(selected),'selected_unique_payloads':len(content_targets),'excluded_raw_files':len(excluded),'initial_immutability':initial,'native_replay_inputs_complete':False,'native_JVM_FEM_or_router_execution_performed':False}
write(S/'checks/v23-source-identity.json',identity);write(S/'checks/v23-frozen-helpers.json',frozen);shutil.copy2(Path(__file__),S/'tools/prepare_compact_v23.py')
assert sha(B/'FILES.sha256.json')==BASE_MANIFEST and sha(W/'repo/.git/index')==initial['index_sha256']
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=W/'repo',text=True).strip()==initial['head']
print(json.dumps({'staging':str(S),'selected':len(selected),'unique_payloads':len(content_targets),'excluded':len(excluded),'paired_projects':len(PROJECTS),'helpers':len(frozen)}))
