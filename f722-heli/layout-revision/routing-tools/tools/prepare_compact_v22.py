#!/usr/bin/env python3
"""Capture accepted55 source and review evidence over immutable V21; no native run."""
import argparse,difflib,hashlib,json,lzma,os,shutil,subprocess
from pathlib import Path
BASE_MANIFEST='0080c59b78db5cf77e87dc644771882d8aaa95be7b77a9ee53acceddfb39b865'
BASE_ZIP='6d2d242e6d82d8ed56d5b7c96e790622fa3aa6d24ab506e659921a06adf47f6b'
PROJECTS={'candidate54':'ordinary-routing/candidate54','sealed55':'ordinary-routing/tests/joint-flash-group/small-candidate01','candidate55':'ordinary-routing/candidate55'}
BEFORE='24121b0e46d9a71207cd21e7cf599412c00796d48eb9af5f63ffcf92e5f2ca42'
AFTER='14dea1df09ea9d800bf66a6d74eb5f0dac33a8705161e9ed1a02f2e11f3b58b8'
BOARDS={'candidate54':BEFORE,'sealed55':AFTER,'candidate55':AFTER}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def info(p):return {'sha256':sha(p),'bytes':Path(p).stat().st_size}
def read(p):return json.loads(Path(p).read_bytes())
def write(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,indent=2,sort_keys=True)+'\n')
ap=argparse.ArgumentParser();ap.add_argument('--workspace',type=Path,required=True);a=ap.parse_args()
W=a.workspace.resolve();B=W/'ordinary-routing/public-source-ready-v21';S=W/'ordinary-routing/public-source-ready-v22'
assert sha(B/'FILES.sha256.json')==BASE_MANIFEST and sha(W/'ordinary-routing/routing-source-v21-delta.zip')==BASE_ZIP
assert all(sha(B/n)==h for n,h in read(B/'FILES.sha256.json').items())
assert not S.exists()
initial={'index_sha256':sha(W/'repo/.git/index'),'head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=W/'repo',text=True).strip(),'canonical_board':info(W/'repo/f722-heli/layout-revision/hardware/f722-heli.kicad_pcb')}
assert initial['canonical_board']['sha256']==AFTER
shutil.copytree(B,S,copy_function=os.link)
replace=['README.md','REPRODUCE.md','SOURCE_EVIDENCE.md','EXCLUDED_INPUTS.md','EVIDENCE_INDEX.json','status.json','FILES.sha256.json','PUBLIC_SOURCE_ALLOWLIST.json','checks/source-package-validation.json']
for n in replace:(S/n).unlink()
for n in replace[:6]:
 p=S/'docs/historical-v21'/n;p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(B/n,p)
for n in ['FILES.sha256.json','PUBLIC_SOURCE_ALLOWLIST.json']:shutil.copy2(B/n,S/'checks'/('v21-original-'+n))
P=S/'tests/checkpoint55';P.mkdir();REC=S/'sessions/recovery-v22';REC.mkdir()
required={n:info(W/PROJECTS['candidate54']/n)for n in read(B/'sessions/recovery-v21/paired-files.json')['required_base_files']}
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
 if label!='candidate54':tree(folder)
sealed=W/PROJECTS['sealed55'];accepted=W/PROJECTS['candidate55'];hand=read(sealed/'route-handoff.json')
assert len(hand['files'])==132 and sha(accepted/'route-handoff.json')==sha(sealed/'route-handoff.json')
for n,h in hand['files'].items():
 assert sha(sealed/n)==h
 assert sha(accepted/('power-audit-sealed-original.json'if n=='power-audit.json'else n))==h,n
for p in sealed.glob('*.used.py'):
 if p.name=='construct.used.py':continue
 n='ordinary-routing/tests/'+('servo48/validate_checkpoint.py'if p.name=='validate_checkpoint.used.py'else 'joint-flash-group/'+p.stem.removesuffix('.used')+'.py')
 add(n,str(p.relative_to(W)))
add('ordinary-routing/tests/joint-flash-group/small-GREEN-complete-proposal54.json',str((sealed/'proposal.json').relative_to(W)))
for folder in ['checkpoint13-owner-review','checkpoint13-placement-reproduction-native','checkpoint13-placement-preview','ordinary-routing/tests/small-signal-review54']:tree(folder)
# Preserve every source used by the current classifier and all-net summary.
for receipt in ['checkpoint13-owner-review/reference-region/owner/reference-classification.json','checkpoint13-owner-review/all-net-reference-summary.json']:
 for n,h in read(W/receipt)['source_hashes'].items():assert sha(W/n)==h;add(n)
# Current signal review plus its explicit older GREEN context; the old 66.98 mm recipe is historical only.
for receipt in ['ordinary-routing/tests/small-signal-review54/source-index.json','ordinary-routing/tests/green-electrical54/source-index.json']:
 add(receipt)
 for row in read(W/receipt)['files']:
  n=row.get('local_path',row.get('path'));assert sha(W/n)==row['sha256'],n;add(n)
for p in (W/'ordinary-routing/candidate53/conditional-signal-review').iterdir():
 if p.is_file() and ('license'in p.name.lower() or 'readme'in p.name.lower()):add(str(p.relative_to(W)))
# Constructors and validation tools are frozen at their exact runtime paths.
for folder in ['integrated-routing','ordinary-routing/native-tools','repo/f722-heli/layout-revision/scripts','repo/f722-heli/layout-revision/signal-review/native','repo/f722-heli/layout-revision/protection-review/tools']:
 for p in sorted((W/folder).glob('*.py')):add(str(p.relative_to(W)))
for n in ['ordinary-routing/tests/mpn-parity/apply_metadata_copy.py','ordinary-routing/dsm40-audits/audit_dsm40_entries_return.py','ordinary-routing/dsm41-audits/audit_dsm41_entries_return.py','repo/f722-heli/layout-revision/checks/bind_stock_spi_review.py','repo/f722-heli/layout-revision/checks/reconstructed.net','repo/f722-heli/layout-revision/checks/protection/candidate-contracts.json','repo/f722-heli/layout-revision/checks/protection/supplemental-contracts.json','repo/f722-heli/validation/firmware-pinmap.json','repo/f722-heli/layout-revision/signal-review/native/model-inputs.template.json','repo/f722-heli/layout-revision/signal-review/final-native-i2c-requirements.json','repo/f722-heli/layout-revision/signal-review/stock-i2c-calculations.json']:add(n)
tree('repo/f722-heli/layout-revision/protection-review/contracts');tree('repo/f722-heli/layout-revision/spi-review')
for n in ['f722-heli.native.json','f722-heli.logical-route-map.json','fixed-explicit-native-ids.json','poses-native.json','power-audit.json','project-input-preservation.json','protection-actual-io.json','reference-snapshot/native-geometry.json','reference-snapshot/native-signals.json','reference-snapshot/critical-reference.json','owner-summary.json']:add(PROJECTS['candidate54']+'/'+n)
for n in ['repo/f722-heli/README.md','repo/f722-heli/layout-revision/README.md','repo/f722-heli/layout-revision/source.json','repo/f722-heli/layout-revision/placement-build.json','repo/f722-heli/layout-revision/placement.json','repo/f722-heli/layout-revision/routing-build.json','repo/f722-heli/layout-revision/checks/current-status.json','repo/f722-heli/layout-revision/checks/checkpoint13-owner-review.json','repo/f722-heli/layout-revision/checks/placement13-reproduction.json','repo/f722-heli/layout-revision/checks/transform-placement13.json']:add(n)
tree('repo/f722-heli/layout-revision/checks/checkpoint55-integration')
# Exact 61-file paired recovery. Sealed and accepted55 have identical native projects.
manifest={'schema':'f722-historical-paired-files/v1','base_label':'candidate54 / immutable V21 recovery','required_base_files':required,'sources':{}}
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
   assert n=='f722-heli.kicad_pcb';d='candidate55.'+n+'.delta.json'
   if not (REC/d).exists():delta(W/PROJECTS['candidate54']/n,p,REC/d)
   entries[n]={'file':d,'sha256':sha(REC/d)}
  recovered[folder+'/'+n]=info(p)
 manifest['sources'][label]={'board_sha256':BOARDS[label],'deltas':entries,'workspace_path':folder,'status':'sealed construction alias; owner adoption separate'if label=='sealed55'else'accepted geometric checkpoint'}
write(REC/'paired-files.json',manifest)
src=(B/'sessions/recovery-v21/rebuild_historical_source.py').read_text().replace('candidate52 project recovered by V20','candidate54 project recovered by V21').replace("choices=('candidate52', 'SERVO15', 'RPM14', 'candidate54')","choices="+repr(tuple(PROJECTS))).replace('Exact historical replay project; not adopted layout','Exact paired project bytes; electrical qualification remains separate')
(REC/'rebuild_historical_source.py').write_text(src)
index={'schema':'f722-selected-evidence/v2','files':{},'excluded_files':dict(sorted(excluded.items())),'recovered_files':dict(sorted(recovered.items())),'frozen_alias_sources':aliases,'scope':'Accepted54 to accepted55; original sealed55 source and owner adapter remain distinct. Source-bound owner reference/signal/placement evidence; all V21 lineage preserved.'}
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
(P/'materialize.py').write_text((B/'tests/checkpoint54/materialize.py').read_text().replace('recovery-v21','recovery-v22').replace('recovery_v21','recovery_v22'))
identity={'schema':'f722-v22-frozen-source-identity/v1','base_v21_manifest_sha256':BASE_MANIFEST,'base_v21_zip_sha256':BASE_ZIP,'expected_boards':BOARDS,'projects':PROJECTS,'sealed_worker_manifest':{'files':132,'manifest':info(sealed/'route-handoff.json'),'path':PROJECTS['sealed55']},'owner_adapter':{'path':PROJECTS['candidate55']+'/power-audit.json',**info(accepted/'power-audit.json'),'original':info(accepted/'power-audit-sealed-original.json')},'frozen_helpers':frozen,'frozen_alias_sources':aliases,'selected_files':len(selected),'selected_unique_payloads':len(content_targets),'excluded_raw_files':len(excluded),'initial_immutability':initial,'native_replay_inputs_complete':False,'native_JVM_FEM_or_router_execution_performed':False}
write(S/'checks/v22-source-identity.json',identity);write(S/'checks/v22-frozen-helpers.json',frozen);shutil.copy2(Path(__file__),S/'tools/prepare_compact_v22.py')
assert sha(B/'FILES.sha256.json')==BASE_MANIFEST and sha(W/'repo/.git/index')==initial['index_sha256']
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=W/'repo',text=True).strip()==initial['head']
print(json.dumps({'staging':str(S),'selected':len(selected),'unique_payloads':len(content_targets),'excluded':len(excluded),'paired_projects':len(PROJECTS),'helpers':len(frozen)}))
