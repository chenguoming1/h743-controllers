#!/bin/bash
# Read-only checks of the authoritative routed projects; writes reports only.
set -euo pipefail
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
K=${KICAD_CLI:-kicad-cli}
PY=${KICAD_PYTHON:-python3}
OUT=${1:-$(mktemp -d "${TMPDIR:-/tmp}/nexus-validation.XXXXXX")}
mkdir -p "$OUT"
OUT=$(CDPATH= cd -- "$OUT" && pwd)
case "$OUT/" in
  "$ROOT/hardware/"*|"$ROOT/tools/"*|"$ROOT/manufacturing/"*)
    echo "Choose a report directory outside source/manufacturing folders." >&2; exit 2 ;;
esac
case "$("$K" --version)" in
  10.*) ;;
  *) echo "KiCad 10 is required; no native checks were run." >&2; exit 1 ;;
esac
"$PY" "$ROOT/tools/check_project_paths.py"
for target in nexus-style-fc header-board/nexus-header-board; do
  name=${target##*/}
  "$K" sch erc --format json --severity-all \
    -o "$OUT/$name-erc.json" "$ROOT/hardware/$target.kicad_sch"
  # Preserve all warnings in reports and count errors separately below.
  # Never refill/save/rewrite the source board.
  "$K" pcb drc --format json --all-track-errors --schematic-parity --severity-all \
    -o "$OUT/$name-drc.json" "$ROOT/hardware/$target.kicad_pcb"
done
"$PY" - "$OUT" <<'PY'
import json, sys
from pathlib import Path
errors = 0
for path in sorted(Path(sys.argv[1]).glob('*-*.json')):
    data = json.loads(path.read_text())
    findings = data.get('violations', []) + data.get('unconnected_items', []) + data.get('schematic_parity', [])
    findings += [v for sheet in data.get('sheets', []) for v in sheet.get('violations', [])]
    counts = {level: sum(v.get('severity') == level for v in findings) for level in ('error', 'warning')}
    errors += counts['error']
    print(f'{path.name}: {counts}; excluded/ignored settings are unchanged and remain in the reports.')
print(f'Reports: {sys.argv[1]}. These checks are not fabrication, assembly or flight approval.')
sys.exit(bool(errors))
PY
