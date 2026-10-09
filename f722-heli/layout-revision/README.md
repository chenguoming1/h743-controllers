# F722 layout revision — work in progress

**Partially routed checkpoint. Do not manufacture or fly this revision.**

This replacement placement moves components inward from the through-hole headers, spreads the side sockets, keeps the LEDs and switch beside the upward USB connector, and uses orthogonal component orientations. The converter and its support parts are grouped on the right, with servo/RPM/SBUS protection on the left. It retains six copper layers, the 47.5 × 25.4 mm overall assembly, the board outline and stock Nexus external/MCU pin assignments.

The paired project is `hardware/f722-heli.kicad_pro`. All 156 target poses are explicit in `placement.json`; 109 differ from the published source. R7/R8 are changed to 2.2 kΩ (UNI-ROYAL 0402WGF2201TCE, C25879), and U13 uses equivalent protection channels 3/6/1 for ESC/RPM/SBUS. Native PCB, schematics and parts metadata agree. Published U14 mapping is retained.

## Checked checkpoint

KiCad 10.0.6 reports **62 unfinished connections, 0 geometric errors, 0 warnings and 0 ERC violations**. All assigned native pad nets and component values match the paired schematic. Native strict schematic parity also reports zero findings after informational footprint/schematic fields were reconciled; part identities and physical/pin/net structure are unchanged. All 29 firmware pin checks pass. Sixteen critical clock, IMU, VCAP and USB nets are connected; all ground pads belong to one connected pad group. All 28 power/support nets are connected. Ordinary signals remain incomplete. The BEC/PERIPH feed has been rebuilt with a coordinated USB_RAW relocation. A fresh two-grid screen passes its 62 enumerated conditional voltage cases, five VCAP DC copper loops and numerical gates. Exact power geometry, contacts, materials and job definitions bind the result to this board. The original overall result remains false because one separate 18.56 A lost-feed illustration fails four servo voltage floors; broader source/circuit corners and hardware qualification remain open. C52 and C20 were rotated 180° in place; R67 and C68 received small interior adjustments to complete local routing while satisfying the via/mask and mechanical checks.

The native via/drill/mask process screen passes. The original 18 protection-path checks have two passes: one actual-clamp cut and one package-NC routing-pad cut. The latter is not a completed protected port. Five of seven supplemental checks pass, covering USB data and CC2; RPM/SBUS remain incomplete. The CC2 route was rebuilt to remove its inherited bypass and now has a 0.187102 mm outside-pad gap. The [complete bonded signal-I/O review](protection-review/README.md) adds the previously omitted D7 channel and reports 6/22 endpoint cases, or 4/20 distinct channels, complete. These four channels are USB data and CC; sixteen active signal-clamp channels remain unfinished. Historical and NC counts remain separate.
Fresh body/courtyard, bounded process, header-access, USB-keepout, edge and mounting-hole screens also pass. Some courtyard gaps remain very small (0.001 mm inherited U1–C4; 0.005 mm near R66); the physical-body/solder screen is bounded and does not establish assembly qualification.

These results establish partial connectivity and geometric consistency. Broader loaded-corner review, remaining routing, final signal timing/reference review and manufacturing exports are still outstanding. USB uses nominal manufacturer pair geometry, but nearby power pads and the connector crossover require qualification of the actual stackup and assembly. No controlled-impedance or flight qualification is claimed.

The native PCB is the authoritative routed source. The placement recipe below recreates the current component arrangement without its routing. The source-only local router and its recorded controls are under `routing-tools/`; accepted ordinary routes close ADC_BEC, ADC_DIV_MID, FLASH_WP_N, SWCLK, D1_A, D2_A, SERVO1_EXT, SERVO2_EXT, SERVO3_EXT, RPM_EXT and SBUS_EXT, with full-width native pad/annular entry. Later engine route claims remain subject to native connectivity and endpoint checks. Exact saved-ground contours and intended-net checks prevent stale antipads or accidental net reassignment during import. The finite-contact static power solver and its reproducible controls are under `power-validation/`. The [current conditional power review](power-validation/CANDIDATE19-COMBINED-REVIEW.md) preserves exact source/result hashes and all failed illustrative checks; [current-board applicability](checks/conditional-power-applicability.json) verifies the same 13 networks, 99 contacts, physical drills/fills, stackup, materials, cases and runtime. Worst ABC pad is 4.862249 V against the conditional 4.8 V floor, with 61.249 mV margin after the 1 mV numerical guard. Worst VCAP DC copper loop is 26.025318 mΩ against 35 mΩ, excluding R16, capacitor ESR and AC stability. Corrected BEC copper drop is 38.370 mV at the representative 2 A case, versus about 614 mV in the preserved failed diagnostic. The [old independent resistance bound](power-evidence/loaded73-deficit-v1/REPORT.md) describes the superseded long feed. The [BEC component/source bounds](bec-voltage-review/REPORT.md) distinguish full-temperature IC reference tolerance from resistor drift and explicitly unguaranteed line/load sensitivities. These are conditional modeled findings, not measured regulation, ampacity, production or flight qualification.

The [stock SPI review](spi-review/stock-spi-review.md) establishes the pinned source clocks of 13.5 MHz for the IMU and 27 MHz for flash; flash is at the MCU SPI2 frequency ceiling. Its [native identity binding](checks/stock-spi-binding.json) confirms the reviewed 103 pad identities and unchanged BOM on this source. Complete routing, fast-edge/loading/return review and actual hardware timing remain unqualified.

The [stock I2C review](signal-review/stock-i2c-review.md) preserves the existing firmware and 2.2 kΩ pull-ups, with provisional 50 pF loading and 100 ns edge targets; the [native signal screen](signal-review/native/README.md) records topology, saved-plane references and conditional loading assumptions. Its current I2C nets are incomplete, so final route estimation and device/bench qualification remain open. [Native export tools](export-tools/README.md) reproduce the previous published payload as a regression control and refuse unfinished candidates. Their historical results do not validate this board.

Machine-readable source identity and results are in `source.json`, `placement-build.json`, `routing-build.json` and `checks/current-status.json`. The original published `../hardware`, `../manufacturing` and electrical reports describe the previous layout; their routing and electrical results do not validate this candidate.

## Reproduce

Use KiCad 10.0.6 with a Python environment providing `pcbnew`. From this directory, rebuild the placement (routing deliberately excluded) into a new output directory:

```sh
python scripts/rebuild_placement.py --source ../hardware --out /path/to/new/hardware
python scripts/patch_metadata.py --hardware /path/to/new/hardware --report /path/to/metadata-changes.json --apply
kicad-cli sch export netlist --format kicadxml --output /path/to/reconstructed.net /path/to/new/hardware/f722-heli.kicad_sch
python scripts/check_native_parity.py --board /path/to/new/hardware/f722-heli.kicad_pcb --netlist /path/to/reconstructed.net --out /path/to/parity.json
kicad-cli pcb drc --format json --output /path/to/drc.json /path/to/new/hardware/f722-heli.kicad_pcb
kicad-cli sch erc --format json --output /path/to/erc.json /path/to/new/hardware/f722-heli.kicad_sch
```

The builder requires published board SHA256 `4da0708a4795662cc32b035a0783c70b9bdb85fc386bd4d39af33385b175667f` and refuses to reuse an output directory. Subsequent routing checkpoints will update this draft branch with their exact checks and remaining work.

## Placement previews

[Front placement](checks/placement-front.svg) · [Mirrored back placement](checks/placement-back.svg)
