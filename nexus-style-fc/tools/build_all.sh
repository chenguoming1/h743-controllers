#!/bin/bash
# Regenerate everything from tools/design.py and tools/design_header.py, then run the checks.
set -euo pipefail
cd "$(dirname "$0")"
PY=/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3
K=/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli
HW=../hardware

python3 make_footprints.py >/dev/null
python3 fix_courtyards.py
python3 gen_schematic.py design "$HW/nexus-style-fc.kicad_sch" nexus-style-fc
python3 gen_schematic.py design_header "$HW/header-board/nexus-header-board.kicad_sch" nexus-header-board
$PY build_header_board.py 2>&1 | grep -v "assert\|wxApp"
$PY build_floorplan.py 2>&1 | grep -v "assert\|wxApp"
# 6-layer stackup, JLC rules, GND planes, Freerouting, GND pours (needs FREEROUTING_JAR and Java 25+)
if [ -n "${FREEROUTING_JAR:-}" ]; then
  $PY route_board.py 2>&1 | grep -v "assert\|wxApp\|memory leak"
  $PY route_board.py header 2>&1 | grep -v "assert\|wxApp\|memory leak"
  $PY build_header_board.py --vrml 2>&1 | grep -v "assert\|wxApp"
else
  echo "FREEROUTING_JAR not set: board left unrouted"
fi
$PY floorplan_svg.py 2>&1 | grep -v "assert\|wxApp"
python3 joint_section.py

for b in "$HW/nexus-style-fc" "$HW/header-board/nexus-header-board"; do
  echo "== $(basename "$b")"
  $K sch erc --severity-error --exit-code-violations -o /dev/null "$b.kicad_sch" 2>&1 | grep Found
  $K pcb drc --schematic-parity --severity-error -o /dev/null "$b.kicad_pcb" 2>&1 | grep Found
done

$K sch export pdf -o ../docs/schematic-main.pdf "$HW/nexus-style-fc.kicad_sch" >/dev/null 2>&1
$K sch export pdf -o ../docs/schematic-header-board.pdf "$HW/header-board/nexus-header-board.kicad_sch" >/dev/null 2>&1
mkdir -p ../manufacturing
for b in nexus-style-fc:main header-board/nexus-header-board:header-board; do
  $K sch export bom --fields 'Reference,Value,Footprint,LCSC,${QUANTITY}' \
    --labels 'Designator,Value,Footprint,LCSC Part #,Quantity' --group-by 'Value,Footprint,LCSC' \
    -o "../manufacturing/bom-${b##*:}.csv" "$HW/${b%%:*}.kicad_sch" >/dev/null 2>&1
done
python3 export_fab.py
echo "done"
