"""Run one local routing batch and request a cooperative wall-clock stop.

The deadline creates the existing runner's stop file. It never kills the JVM;
the active connection/checkpoint can finish and final fixed-object checks remain.
"""
import argparse,hashlib,json,os,subprocess,time
from pathlib import Path
ap=argparse.ArgumentParser();ap.add_argument('--model',type=Path,required=True);ap.add_argument('--prefix',type=Path,required=True);ap.add_argument('--seconds',type=float,default=120);ap.add_argument('--successes',type=int,default=3);ap.add_argument('--nets',required=True);a=ap.parse_args();assert a.seconds>0 and a.successes>0
assert not any(Path(str(a.prefix)+ext).exists()for ext in ['.log','.progress.json','.stop','.ses','.after.json'])
env=dict(os.environ,F722_ONLY_NETS=a.nets,F722_CONNECTION_BUDGET_MS='10000',F722_CHECKPOINT_AFTER_ROUTED=str(a.successes),F722_CHECKPOINT_EVERY_ROUTED='1',F722_INSERT_DIAGNOSTICS='1')
started=time.monotonic();requested=False;last=None
with Path(str(a.prefix)+'.log').open('w')as log:
 process=subprocess.Popen(['./run_local.sh',str(a.model),str(a.prefix),'1'],stdout=log,stderr=subprocess.STDOUT,env=env)
 while process.poll()is None:
  elapsed=time.monotonic()-started
  if elapsed>=a.seconds and not requested:
   Path(str(a.prefix)+'.stop').write_text('Cooperative wall-clock budget reached; preserve successful geometry.\n');requested=True;print(json.dumps({'cooperative_stop_requested':True,'elapsed_seconds':elapsed}),flush=True)
  progress=Path(str(a.prefix)+'.progress.json')
  if progress.exists():
   try:state=json.loads(progress.read_text())
   except (OSError,json.JSONDecodeError):state=None
   if state and state.get('sequence')!=last:
    last=state.get('sequence');print(json.dumps({k:state.get(k)for k in ['sequence','elapsed_seconds','route_counters','attempt','checkpoint','pending_route_geometry']}),flush=True)
  time.sleep(.5)
 elapsed=time.monotonic()-started
receipt=dict(exit_code=process.returncode,wall_seconds=elapsed,cooperative_stop_after_seconds=a.seconds,stop_file_requested=requested,success_stop_count=a.successes,model_sha256=hashlib.sha256((a.model/'model.json').read_bytes()).hexdigest(),supervisor_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),no_forced_termination=True)
Path(str(a.prefix)+'.bounded-run.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt),flush=True);raise SystemExit(process.returncode)
