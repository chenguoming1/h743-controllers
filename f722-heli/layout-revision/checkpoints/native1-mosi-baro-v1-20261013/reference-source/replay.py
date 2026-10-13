"""Verify a preserved review or prepare a separate, unlaunched exact-input replay."""
from pathlib import Path
import argparse,hashlib,json,shlex,shutil
H=Path(__file__).resolve().parent

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())
def write(p,d):Path(p).write_text(json.dumps(d,indent=2)+'\n')

def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--verify',action='store_true');ap.add_argument('--prepare-run',type=Path);ap.add_argument('--native',type=Path);ap.add_argument('--pcb',type=Path);ap.add_argument('--aux',type=Path);ap.add_argument('--dependencies',type=Path);ap.add_argument('--shared-lock',type=Path);a=ap.parse_args()
 m=read(H/'MANIFEST.json')
 for row in m['files']:
  q=H/row['path'];assert q.is_file()and q.stat().st_size==row['bytes']and sha(q)==row['sha256'],('Package mismatch',row['path'])
 if not a.prepare_run:
  print(json.dumps({'status':'PACKAGE_HASHES_VERIFIED','files':len(m['files']),'manifest_sha256':sha(H/'MANIFEST.json'),'geometry_executed':False}));return
 assert not a.verify,'Use either --verify or --prepare-run'
 assert all([a.native,a.pcb,a.aux,a.dependencies,a.shared_lock]),'Native, PCB, auxiliary, dependencies and shared lock are required'
 assert a.dependencies.is_dir()and a.shared_lock.is_file()
 run=a.prepare_run.resolve();assert not run.exists(),'Replay directory must be new';assert run.parent.is_dir();assert shutil.disk_usage(run.parent).free>=128*1024**2+1024**2
 p=read(H/'actual-return/proposal.json');mapping=read(H/'replay-input-map.json');external={'candidate_native':a.native,'candidate_PCB':a.pcb,'candidate_auxiliary':a.aux}
 for key,b in mapping['inputs'].items():
  q=external[key].resolve()if b.get('external_required')else(H/b['package_path']).resolve();assert sha(q)==b['sha256'],('Replay input mismatch',key);p['inputs'][key]={'path':str(q),'sha256':b['sha256']}
 p['python_dependencies']=str(a.dependencies.resolve());p['shared_lock']=str(a.shared_lock.resolve());p['package_replay_provenance']={'manifest_sha256':sha(H/'MANIFEST.json'),'original_review_seal_sha256':sha(H/'actual-return/REVIEW-SEAL.json'),'normalization':'Only fields unused by unchanged script removed, as recorded in replay-input-map.json; no geometry values changed.'}
 run.mkdir();shutil.copyfile(H/'actual-return/review_actual.py',run/'review_actual.py');assert sha(run/'review_actual.py')==sha(H/'actual-return/review_actual.py');write(run/'proposal.json',p);seal={'schema':'f722-actual-return-seal/v1','script_sha256':sha(run/'review_actual.py'),'proposal_sha256':sha(run/'proposal.json'),'candidate_board_sha256':p['candidate']['board_sha256'],'derived_replay_preparation_only':True,'execution_authorization_not_inferred':True};write(run/'REVIEW-SEAL.json',seal)
 command=['timeout','--signal=TERM','--kill-after=2s','120s','python3',str(run/'review_actual.py'),'--execute','--seal-sha256',sha(run/'REVIEW-SEAL.json')]
 print(json.dumps({'status':'REPLAY_PREPARED_NOT_LAUNCHED','run_directory':str(run),'seal_sha256':sha(run/'REVIEW-SEAL.json'),'command_requires_execution_authorization':shlex.join(command),'geometry_executed':False},indent=2))
if __name__=='__main__':main()
