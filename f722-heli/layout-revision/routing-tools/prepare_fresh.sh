#!/bin/sh
# Export/preparation only; zero/load/route commands require the owner's heavy slot.
set -eu
cd "$(dirname "$0")"
if [ "$#" -lt 2 ]; then echo 'Usage: KICAD_PY=/path/to/kicad-python ./prepare_fresh.sh BOARD MODEL_DIR [prepare_model options]' >&2; exit 2; fi
board=$1
model_dir=$2
shift 2
mkdir -p "$model_dir"
exporter=native-tools/export_native_copper.py
if [ ! -f "$exporter" ]; then exporter=../protection-checks/export_native_copper.py; fi
if [ ! -f "$exporter" ]; then echo 'Native exporter is missing' >&2; exit 2; fi
"${KICAD_PY:?Set KICAD_PY to the verified KiCad 10 Python wrapper}" "$exporter" --board "$board" --out "$model_dir/native.json"
"${ANALYSIS_PY:-python3}" prepare_model.py --board "$board" --native "$model_dir/native.json" --out "$model_dir" "$@"
