#!/bin/bash
# Regenerate the power module from tools/design_power.py (parts from ../../nexus-style-fc/tools/design.py),
# then run the checks. The PCB is placed, not routed.
set -euo pipefail
cd "$(dirname "$0")"
PY=/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3
K=/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli
NEXUS=../../nexus-style-fc/tools
B=../hardware/nexus-style-fc-power-module

PYTHONPATH=. python3 "$NEXUS/gen_schematic.py" design_power "$B.kicad_sch" nexus-style-fc-power-module
$PY build_power_module.py 2>&1 | grep -v "assert\|wxApp"
$K sch erc --severity-error --exit-code-violations -o /dev/null "$B.kicad_sch" 2>&1 | grep Found
$K pcb drc --schematic-parity --severity-error -o /dev/null "$B.kicad_pcb" 2>&1 | grep Found
$K sch export pdf -o ../docs/schematic.pdf "$B.kicad_sch" >/dev/null 2>&1
$K pcb render --side top --width 1600 --height 1400 --zoom 1 -o ../docs/pcb-top.png "$B.kicad_pcb" >/dev/null 2>&1
echo "done"
