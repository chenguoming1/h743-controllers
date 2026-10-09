"""Copy hash-bound successful snapshots without touching a running router."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import time

ap = argparse.ArgumentParser(description=__doc__)
ap.add_argument('--prefix', type=Path, required=True)
a = ap.parse_args()
prefix = a.prefix.resolve()
root = Path(str(prefix) + '.successes')
root.mkdir(exist_ok=True)


def sha(p):
    h = hashlib.sha256()
    with p.open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def capture(state, name):
    dst = root / name
    if dst.exists():
        return
    tmp = root / (name + '.copying')
    tmp.mkdir(exist_ok=True)
    checkpoint = Path(state['checkpoint'])
    for ext in ['.ses', '.after.json']:
        shutil.copyfile(Path(str(checkpoint) + ext), tmp / ('snapshot' + ext))
    if (sha(tmp / 'snapshot.ses') != state['session_sha256'] or
            sha(tmp / 'snapshot.after.json') != state['report_sha256']):
        return
    (tmp / 'receipt.json').write_text(json.dumps(state, indent=2) + '\n')
    tmp.rename(dst)
    print(json.dumps({'preserved': name, 'route_counters': state['route_counters']}), flush=True)


while True:
    try:
        state = json.loads(Path(str(prefix) + '.progress.json').read_text())
        count = state['route_counters']['routed_count']
        if count and not state.get('pending_route_geometry', True):
            capture(state, 'count' + str(count))
        if Path(str(prefix) + '.bounded-run.json').exists():
            if count and not state.get('pending_route_geometry', True):
                capture(state, 'final')
            break
    except (OSError, KeyError, json.JSONDecodeError):
        pass
    time.sleep(1)
