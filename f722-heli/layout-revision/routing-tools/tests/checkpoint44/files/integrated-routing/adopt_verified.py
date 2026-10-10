"""Adopt an independently checked partial board. README/previews still need refresh."""
import argparse,hashlib,json,shutil,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[1];N=R/'repo/f722-heli/layout-revision';C=N/'checks'
p=argparse.ArgumentParser();p.add_argument('candidate',type=Path);p.add_argument('poses',type=Path);p.add_argument('--progress',required=True);p.add_argument('--paired-metadata',action='store_true');a=p.parse_args();D=a.candidate.resolve()
def read(p):return json.loads(p.read_text())
def write(p,d):p.write_text(json.dumps(d,indent=2)+'\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
b=D/'f722-heli.kicad_pcb';h=sha(b);s=read(D/'owner-summary.json');assert s['board_sha256']==h
assert s['drc']['errors']==s['drc-all']['errors']==0 and s['drc']==s['drc-all']
if (D/'owner-drc-parity.json').is_file():
 strict=read(D/'owner-drc-parity.json');assert not strict['schematic_parity'] and not strict['violations'],'Strict native parity or DRC findings remain'
for k in ['process','mechanical','parity','firmware']:
 q=read(D/('owner-'+k+'.json'));assert q['board_sha256']==h and q['passed'] is True,k
critical=read(D/'owner-critical.json');assert critical['board_sha256']==h and not critical['faults'];assert all(x['complete'] for x in critical['fullnet_connectivity']);assert all(x['connected_to_ground_plane'] for x in critical['critical_ground_returns'])
assert read(D/'owner-mechanical.json')['input_hashes'][a.poses.name]==sha(a.poses)
poses=read(a.poses);assert len(poses)==156 and all(len(v)==4 and v[2]%90==0 for v in poses.values())
for n in ['owner-protection','owner-supplemental','power-audit']:assert read(D/(n+'.json'))['board_sha256']==h,n
oldh=sha(N/'hardware/f722-heli.kicad_pcb');parent=subprocess.check_output(['git','rev-parse','HEAD'],cwd=R/'repo',text=True).strip()
if (D/'f722-heli.import.json').is_file():
 imported=read(D/'f722-heli.import.json')
 if imported['source_sha256']!=oldh and h!=oldh:
  integration=read(D/'owner-additive-integration.json');assert integration['source_board_sha256']==oldh and integration['board_sha256']==h and integration['passed'] is True,'Candidate needs owner-verified integration onto current adopted source'
from verify_support_adoption import verify as verify_support
verify_support(read(D/'power-audit.json'),read(C/'power-pad-groups.json'),oldh,h,D)

for new_name,old_name in [('owner-protection','candidate-recheck'),('owner-supplemental','candidate-supplemental')]:
 prior=read(C/'protection'/(old_name+'.json'));new=read(D/(new_name+'.json'));assert prior['contracts_sha256']==new['contracts_sha256'],'Protection contract change requires explicit scoped review'
 prior_pass={x['id'] for x in prior['checks'] if x['complete_clamp_first_path_passes']};new_pass={x['id'] for x in new['checks'] if x['complete_clamp_first_path_passes']};assert prior_pass<=new_pass,'Previously completed protection path regressed'
if a.paired_metadata:
 metadata=read(D/'paired-metadata-changes.json');proof=read(D/'metadata-verification.json')
 assert metadata['board_sha256']==h and proof['destination_board_sha256']==h and proof['status']=='PASS'
 assert sha(D/'metadata-verification.json')==metadata['verification_sha256']
 assert proof['board_non_target_semantic_sha256_before']==proof['board_non_target_semantic_sha256_after']
 for key in ['native_physical_net_identity','native_schematic_pin_net_identity']:
  assert proof[key+'_before']==proof[key+'_after']
 assert proof['strict_native_schematic_parity_issues']==0
 for row in metadata['changed_schematics']:
  assert Path(row['file']).name==row['file'] and row['file'].endswith('.kicad_sch')
  assert sha(N/'hardware'/row['file'])==row['source_sha256'] and sha(D/row['file'])==row['output_sha256']
 erc=read(D/'owner-erc.json');assert sum(len(x.get('violations',[])) for x in erc.get('sheets',[]))==0
 for row in metadata['changed_schematics']:shutil.copy2(D/row['file'],N/'hardware'/row['file'])
 shutil.copy2(D/'metadata-native.net',C/'reconstructed.net')
 shutil.copy2(D/'owner-erc.json',C/'reconstructed-erc.json')
 write(C/'erc-source-binding.json',{'schematic_sha256':{p.name:sha(p) for p in sorted((N/'hardware').glob('*.kicad_sch'))},'violations':0,'report':'reconstructed-erc.json'})
 shutil.copy2(D/'metadata-drc-parity.json',C/'native-strict-schematic-parity.json')
 shutil.copy2(D/'paired-metadata-changes.json',C/'paired-metadata-changes.json')
shutil.copy2(b,N/'hardware/f722-heli.kicad_pcb')
if read(N/'placement.json')!=poses:write(N/'placement.json',poses)
for name,target in [('owner-drc','placement-drc'),('owner-drc-all','routing-drc-all'),('owner-mechanical','mechanical-report'),('owner-parity','native-schematic-parity'),('owner-firmware','firmware-pinmap'),('owner-process','via-process'),('owner-critical','critical-net-connectivity'),('power-audit','power-pad-groups'),('owner-summary','routing-checkpoint-summary'),('owner-protection','protection/candidate-recheck'),('owner-supplemental','protection/candidate-supplemental')]:shutil.copy2(D/(name+'.json'),C/(target+'.json'))
if (D/'owner-drc-parity.json').is_file():shutil.copy2(D/'owner-drc-parity.json',C/'native-strict-schematic-parity.json')
status=read(C/'current-status.json');status.update(board_sha256=h,unfinished_connections=s['drc']['unconnected'],drc_errors=0,drc_warnings=s['drc']['warnings'],changed_poses_from_published=sum(poses[k]!=read(N/'placement-build.json')['poses_before'][k] for k in poses),checkpoint_progress=a.progress,warning_scope='See placement-drc.json for exact unfinished-interface warnings.',protection_paths_passed=s['protection']['passed'],supplemental_protection_passed=s['supplemental']['passed']);write(C/'current-status.json',status)
source=read(N/'routing-build.json');source.update(board_sha256=h,placement_pose_sha256=sha(N/'placement.json'),prior_local_checkpoint=parent,prior_published_checkpoint=read(R/'ACTIVE-STATE.json')['publication']['remote_commit'],previous_routed_board_sha256=oldh,integration=a.progress);write(N/'routing-build.json',source)
ps=read(C/'protection/validation-summary.json');ps['board_sha256']['candidate']=h
for key,report in [('candidate_original_scope','owner-protection'),('candidate_supplemental_review','owner-supplemental')]:
 d=read(D/(report+'.json'));ps[key]={'passed':d['passed'],'total':d['total']}
for name in ps['files_sha256']:
 matches=[C/'protection'/name,N/'scripts'/name]
 matches=[v for v in matches if v.is_file()];assert len(matches)==1,name;ps['files_sha256'][name]=sha(matches[0])
write(C/'protection/validation-summary.json',ps)
print(json.dumps({'adopted_sha256':h,'unfinished':s['drc']['unconnected'],'remaining_checkpoint_tasks':['Rebuild and check placement recipe','Refresh README and previews','Review exact changed-path allowlist','Commit and publish']}))
