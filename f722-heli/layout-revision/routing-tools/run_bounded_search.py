"""Run a recoverable local search with explicit time and connection budgets.

The supervisor only selects search work and requests the existing cooperative
stop. It never kills the JVM or changes a physical/electrical constraint.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time

ap = argparse.ArgumentParser(description=__doc__)
ap.add_argument('--model', type=Path, required=True)
ap.add_argument('--prefix', type=Path, required=True)
ap.add_argument('--seconds', type=float, default=300)
ap.add_argument('--successes', type=int, default=3)
ap.add_argument('--connection-ms', type=int, required=True)
ap.add_argument('--slow-tree', action='store_true')
ap.add_argument('--nets', required=True)
a = ap.parse_args()
assert a.seconds > 0 and a.successes > 0 and a.connection_ms > 0
assert not any(Path(str(a.prefix) + ext).exists()
               for ext in ['.log', '.progress.json', '.stop', '.ses', '.after.json'])
source_hash = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
env = dict(os.environ, F722_ONLY_NETS=a.nets,
           F722_CONNECTION_BUDGET_MS=str(a.connection_ms),
           F722_CHECKPOINT_AFTER_ROUTED=str(a.successes),
           F722_CHECKPOINT_EVERY_ROUTED='1', F722_INSERT_DIAGNOSTICS='1',
           F722_FORCE_SLOW_TREE='1' if a.slow_tree else '0')
started, requested, last = time.monotonic(), False, None
with Path(str(a.prefix) + '.log').open('w') as log:
    process = subprocess.Popen(['./run_local.sh', str(a.model), str(a.prefix), '1'],
                               stdout=log, stderr=subprocess.STDOUT, env=env)
    while process.poll() is None:
        elapsed = time.monotonic() - started
        if elapsed >= a.seconds and not requested:
            Path(str(a.prefix) + '.stop').write_text(
                'Cooperative wall-clock budget reached; preserve successful geometry.\n')
            requested = True
            print(json.dumps({'cooperative_stop_requested': True,
                              'elapsed_seconds': elapsed}), flush=True)
        progress = Path(str(a.prefix) + '.progress.json')
        if progress.exists():
            try:
                state = json.loads(progress.read_text())
            except (OSError, json.JSONDecodeError):
                state = None
            if state and state.get('sequence') != last:
                last = state.get('sequence')
                print(json.dumps({k: state.get(k) for k in
                                  ['sequence', 'elapsed_seconds', 'route_counters',
                                   'attempt', 'checkpoint', 'pending_route_geometry']}),
                      flush=True)
        time.sleep(.5)
receipt = dict(exit_code=process.returncode, wall_seconds=time.monotonic() - started,
               cooperative_stop_after_seconds=a.seconds, stop_file_requested=requested,
               success_stop_count=a.successes, connection_budget_ms=a.connection_ms,
               search_tree='stock_slow' if a.slow_tree else 'stock_fast_45_degree',
               model_sha256=hashlib.sha256((a.model / 'model.json').read_bytes()).hexdigest(),
               supervisor_sha256=source_hash,
               supervisor_source_unchanged=source_hash == hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
               no_forced_termination=True, physical_or_electrical_constraints_changed=False)
Path(str(a.prefix) + '.bounded-run.json').write_text(json.dumps(receipt, indent=2) + '\n')
print(json.dumps(receipt), flush=True)
raise SystemExit(process.returncode)
