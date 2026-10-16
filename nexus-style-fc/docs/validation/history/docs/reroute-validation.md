# Native reroute verification

Use KiCad 10 with matching stock libraries. The validator uses native pcbnew and
the Python standard library. It is a source-invariant and regression gate, not
a manufacturing, power-current, USB or flight qualification.

Run native checks on the exact final source after every accepted routing edit:

    kicad-cli pcb drc --all-track-errors --schematic-parity --refill-zones --save-board --severity-all --format json --exit-code-violations -o final-drc.json hardware/nexus-style-fc.kicad_pcb
    kicad-cli sch erc --severity-all --format json --exit-code-violations -o final-erc.json hardware/nexus-style-fc.kicad_sch

An exit status of 5 can include the inherited silkscreen warnings. Inspect the
complete JSON; do not treat a missing report or a load failure as success.
Record the command, KiCad version and source SHA-256 before/after checks.

With an unchanged baseline board/project and its native report:

    python3 tools/validate_nexus_reroute.py --baseline ORIGINAL.kicad_pcb --candidate hardware/nexus-style-fc.kicad_pcb --baseline-project ORIGINAL.kicad_pro --baseline-drc original-drc.json --drc final-drc.json --erc final-erc.json --output validation.json

The Python interpreter must provide pcbnew 10. Gates include:
- Exact footprint/pad/net/placement, outline, physical stack and zone/keepout definitions.
- No trace below 0.127 mm; ordinary main vias exactly 0.45/0.20 mm.
- No new via drill intersection with pasted SMD copper, including same-net contacts.
- No added diagnostic suppression; zero native errors, opens and parity findings, with no new warnings.
- Named power-net minimum width must not fall below its original actual minimum or 0.127 mm, whichever is larger.

Generated zone-fill polygons are allowed to change. Retaining zone boundaries
does not establish equivalent connected GND returns; inspect the filled copper.
Likewise, an aggregate net minimum cannot establish branch-specific ampacity.
USB width/layer/via profiles are descriptive and do not establish impedance.
Inherited via-in-paste contacts remain counted and unresolved; they are not
grandfathered into a fabrication release.

## Regression tests

Fourteen native/parser regression tests were run against original main commit
dc1ea0c324b5f4a0bb3c8e250a31acdfe5793c4c. The original-as-candidate check intentionally
fails the manufacturing gate: 937 narrow traces and 18 existing drilled vias
intersecting pasted SMT copper (19 contact pairs).

To prepare independent fixtures, extract that commit's nexus-style-fc/hardware
directory into FIXTURE/baseline/hardware. Copy its original PCB to
FIXTURE/backups/main-before-rule-refill.kicad_pcb. Generate an all-severity native
DRC report against the original hardware path, with schematic parity, as
FIXTURE/reports/main-baseline-native.json, and its ERC report as
FIXTURE/reports/main-erc-libraries.json. Keep the original project under
FIXTURE/baseline/hardware/nexus-style-fc.kicad_pro and matching KiCad libraries
available. Then run:

    NEXUS_REROUTE_TEST_BASE=FIXTURE python3 tools/test_validate_nexus_reroute.py

Tests write only to a new temporary test directory. They cover unchanged and
moved footprints, stack/outline/pad/zone/keepout changes, permitted refill data,
minimum widths, power-width regression, new same/different-net pasted-land
drilling, missing native evidence, fresh violations and suppressed diagnostics.

## Router version hazards

For Freerouting 2.5.0, automatic pad necking, fixed-width retry and fanout micro-necking
are separate mechanisms. Use all three controls:

    --router.automatic_neckdown=false --router.neck_width_um=0 --router.fanout.enabled=false

A global neck_width_um=127 can silently shrink power classes to 0.127 mm even
when automatic_neckdown is false. Fanout can separately try 75%, 60% or 50% of
class width. Neither behavior is accepted without the actual imported-geometry
checks. These behaviors are documented by the tagged upstream
[retry implementation](https://github.com/freerouting/freerouting/blob/v2.5.0/src/main/java/app/freerouting/autoroute/pipeline/AutorouteConnectionRouter.java)
and [fanout/path implementation](https://github.com/freerouting/freerouting/blob/v2.5.0/src/main/java/app/freerouting/autoroute/path/FoundConnectionInserter.java).

Freerouting's conservative octagonal representation of circular vias can report
clearances that pass exact native circular geometry. Keep those exchange warnings
visible and resolve actual acceptance with native KiCad and exact geometry; do
not weaken the manufacturing rule to silence the router.
