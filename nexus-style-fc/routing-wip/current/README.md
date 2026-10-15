# Current integrated experimental Nexus project

Open **[nexus-style-fc.kicad_pro](hardware/nexus-style-fc.kicad_pro)**,
[main PCB](hardware/nexus-style-fc.kicad_pcb), [matching schematic](hardware/nexus-style-fc.kicad_sch),
or [matching child board](hardware/header-board/nexus-header-board.kicad_pcb).

The integrated main and redesigned child both have zero native geometric errors and opens.
Main electrical parity and dangling findings are zero. Main warnings: 4 footprint_type_mismatch, 3 silk_edge_clearance, 19 silk_over_copper, 32 silk_overlap, 11 track_not_centered_on_via.
Child retains 11 courtyard and 11 footprint-filter advisories; its physical pin/net map is exact.
[Exact diagnostics, return checks and fit limits](../2026-10-15/integrated-interface-checkpoint/README.md).

This complete project combines the approved C27/C31 capacitors and D5 move with the redesigned
10.10 × 2.20 mm slots, matching child contacts/model and repaired return routing.
Assembly-annotation cleanup applied: no; existing warnings remain visible.
PCB SHA256 `ccd8865f6785fd1cdec0214a08fe409faed4d47bb01e8474f09264ee36acab99`; schematic `7a133c241ba24a688d2d2490ae423ff74d26f57cf6578f871cc757093584de42`.

- [Full schematic PDF](docs/connected.pdf)
- [Functional-circuit review PDF](docs/nexus-connected-circuits-review.pdf)
- [Exact integrated source archive](docs/nexus-integrated-project-source.zip)
- [Actual WIP BOM/CPL](manufacturing-wip/README.md)

Nominal model fit passes; finished tolerances, deliberate contact alignment and narrow-rail strength
remain unqualified. USB actual-stack impedance/electrical compliance, BEC/input-loop and power/current/thermal tests, ordinary tented via-in-paste process, and physical assembly/strength remain open. **Do not fabricate, assemble or fly.**

The root `hardware/` is an older coherent canonical reference. No unrelated project is changed.
Existing model files are retained for relative-path usability, with the new child model source-bound;
standard KiCad 10 models remain a system dependency. The committed native PCB is authoritative.
Do not run historical build/floorplan scripts over it expecting to reproduce the accepted routing.
