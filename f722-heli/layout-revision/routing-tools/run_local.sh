#!/bin/sh
# Local-only execution. PASSES is a computational budget, not an electrical limit.
set -eu
cd "$(dirname "$0")"
if [ "$#" -ne 3 ]; then echo 'Usage: run_local.sh MODEL_DIR OUTPUT_PREFIX PASSES' >&2; exit 2; fi
python - "$1" "$3" <<'PY'
import json,sys,hashlib
from pathlib import Path
root=Path(sys.argv[1]);passes=int(sys.argv[2]);assert passes>=0
if passes:
 m=json.loads((root/'model.json').read_text());assert m['support_ready'],'Fixed support is not ready'
 z=json.loads((root/'zero-parity.json').read_text());assert z['passed'],'Zero control has not passed'
 assert z['model_sha256']==hashlib.sha256((root/'model.json').read_bytes()).hexdigest(),'Model changed after zero control'
 assert z['board_sha256']==m['board_sha256'],'Zero control source differs'
PY
exec java -Xmx3g -Djava.awt.headless=true -cp build:vendor/freerouting-2.1.0.jar LocalRouter "$1" "$2" "$3"
