#!/bin/sh
set -eu
cd "$(dirname "$0")"
python3 - <<'PY'
from pathlib import Path
import subprocess
sources=sorted(Path('src').rglob('*.java'))
subprocess.run(['java','-jar','vendor/ecj-3.41.0.jar','-21','-nowarn','-cp','vendor/freerouting-2.1.0.jar','-d','build']+[str(p) for p in sources],check=True)
PY
