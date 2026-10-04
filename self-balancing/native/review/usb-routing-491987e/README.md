# Native DRC repair from main 491987e

**Native design-review result, not a manufacturing release or USB compliance test.**

- Base: `491987ef141ab32f39821675928d32dd1ad8e66f` (2026-10-04, “added library and differential rules”)
- KiCad: official 10.0.6 portable runtime
- Final PCB SHA-256: `89886cf0ecfdb62a90a56810d75ac765d837435076423a0c173a33a3647a4579`
- Baseline: 17 DRC findings, 0 opens, 0 schematic-parity findings, ERC 0
- Final: DRC 0 at all severities, opens 0, schematic parity 0, ERC 0

## Physical changes

1. Swapped the USB-C duplicate-contact bridge sides and improved the connector escape. Retained the same two 0.45/0.20 mm USB crossover vias and their identities; moved them to (32.0,14.4) and (33.1,14.4). The B.Cu crossover is 1.10 mm rather than 1.80 mm. No new vias, via-in-pad process, or component movement.
2. Routed the ESD N leg alongside P through the 45-degree bend at the nominal pair spacing, and shortened its resistor escape. Shortened the unnecessary MCU N corner while retaining full pad entry.
3. Re-anchored the B.Cu starts of EXT_SPI_CS track `aa0ba152-3bbf-4d1d-9151-525360cf5b28` and FLASH_MOSI track `a7e38858-484a-4082-a6a2-05c65e9d18b3` to their current via centers. These were genuine shallow functional contacts after earlier via moves. The user's via positions remain unchanged.
4. Removed two redundant exposed B.Cu GND tail segments near (32.029385,29.763507); retained the ground stitch and all its reference-plane attachments.

All 151 footprint placements and pad geometries, schematic/project files, local libraries, pin/net assignments, 79-placement CPL and 35-group BOM are preserved. All 406 via identities and dimensions remain; all 97 GND stitches remain. See the exact preservation and contact ledgers.

## Pair rules and justified escapes

The 0.1392 mm width, nominal 0.160 mm pair gap, strict 0.155–0.165 mm main-pair window, 2 mm main-group uncoupled cap and 1 mm per-net skew checks remain. Manufacturing clearance, drill and annulus rules were not reduced. No DRC exclusions or severity suppressions were added. The unchanged project already ignores seven diagnostic categories: `footprint_filters_mismatch`, `footprint_type_mismatch`, `missing_courtyard`, `npth_inside_courtyard`, `pth_inside_courtyard`, `track_not_centered_on_via`, and `tuning_profile_track_geometries`. These inherited ignored diagnostics were not re-enabled or counted as separately passed; actual via contacts were checked independently.

Five finite exceptions apply only to straight USB tracks whose **two endpoints** are inside the specified native-coordinate box. Tracks are split at escape boundaries, so a long trunk cannot inherit a local escape rule. Ordinary 0.160 mm track-to-track clearance remains effective everywhere.

| Physical escape | X range / Y range (mm) | Max gap (mm) | Local uncoupled cap (mm) |
|---|---|---:|---:|
| USB-C alternating duplicate contacts | 29.1–32.95 / 19.25–20.85 | 0.365 | 5.5 |
| U4 input pads and two-via crossover | 31.5–33.2 / 11.45–14.85 | 1.765 | 4.25 |
| U4 output pad escape | 28.35–29.45 / 11.45–13.45 | 1.765 | 2.9 |
| R7/R8 pad escape | 28.3–29.3 / 16.5–18.1 | 1.365 | 2.2 |
| MCU-to-resistor fixed-pad fanout | 25.55–27.5 / 16.4–18.1 | 0.365 | 2.2 |

The limits reflect the fixed 0.5 mm USB/MCU pin pitch, 1.9 mm U4 channel pitch, 1.5 mm resistor separation, and local branched copper. They are not claims that all fanout copper is 90 ohms. The connector's strict paired trunk is between Y=14.85 and 19.25 mm; the ESD strict region is between Y=13.45 and 16.5 mm, including its paired bend.

Negative controls confirm the exceptions do not merely hide the original routing: the original copper still fails with the new rules, and deliberately increasing the ESD trunk gap to 0.190 mm is rejected. These tests are isolated copies; the delivered board is unchanged.

## Fully enabled diagnostic cross-check

The seven inherited ignored categories were separately enabled as warnings in an isolated full-project copy. This did **not** change the delivered project settings. Results:

- 48 `track_not_centered_on_via` warnings, exactly identical to baseline. All 48 map to independently passing annulus-contact groups: 35 single-track and 13 connected multi-track groups; zero shallow, zero unmapped, zero involving changed items. Minimum penetration in these groups is 59.95%, above the audit's 50% floor. Centering is a heuristic rather than a requirement that every valid track must reach a via center.
- 134 `footprint_filters_mismatch` selector advisories, exactly identical to baseline: 67 Controller_R2, 61 H743_Board, four Controller_R3 and two Storm32_Review. Their custom footprint names do not fit the symbols' generic chooser patterns (for example `H743_Board:C3_C_0603_1608Metric` versus `C_*`). Local libraries are accessible; these are not library-loading failures, changed footprint copper, or electrical pin/net mismatches.
- Zero findings in the other five re-enabled categories, zero opens, and no new advisory records.

Thus **configured DRC/parity are zero; fully enabled diagnostics are not zero**. The inherited advisories are explicitly recorded and physically dispositioned rather than hidden or represented as independently empty. See `all-enabled-audit-summary.json` and the complete warning/contact evidence.

## Measured path lengths and qualification

The independent graph calculation uses actual pad-center routes and the actual 1.5384 mm board thickness for each via barrel. Internal ESD/resistor/package/connector and cable propagation delays are excluded. Values below are geometrical path lengths, not measured electrical delays.

| External-copper segment | P (mm) | N (mm) | N−P (mm) |
|---|---:|---:|---:|
| Connector A6/A7 to U4 | 14.267498 | 13.552825 | −0.714673 |
| Connector B6/B7 to U4 | 10.857498 | 13.752825 | +2.895327 |
| U4 to R8/R7 | 6.553038 | 6.007060 | −0.545978 |
| R8/R7 to MCU | 1.715000 | 2.176076 | +0.461076 |
| **Orientation A, connector to MCU** | **22.535536** | **21.735962** | **−0.799574** |
| **Orientation B, connector to MCU** | **19.125536** | **21.935962** | **+2.810426** |

KiCad's total-net skew is not an active USB-C path measurement: it sums branched copper. The native 1 mm net-skew checks pass, but orientation B is **not matched to 1 mm end-to-end**. The physical branch values are deliberately reported instead of hiding that distinction.

For context, TI's [SLLU149E, section 5.3](https://www.ti.com/lit/ug/sllu149e/sllu149e.pdf) gives 150 mil (3.81 mm) mismatch guidance for its TUSB73x0 USB high-speed routing. This is a comparative USB 2.0 layout guideline, **not an STM32H743-specific limit or certification**. The present link uses the STM32 full-speed interface. Retaining the verified two-via routing was judged preferable to a three-via/via-in-pad alternative that required four unrelated net reroutes and worsened ground-return proximity.

The stackup/width/gap retain the existing calculated 90-ohm basis. Full trace-width reference coverage is preserved outside each signal via's own antipad transition. The widened crossover leaves approximately 0.35 mm of In1 GND beneath P between the antipads; its local discontinuity is still not a field-solver-verified 90-ohm structure. Reference-plane continuity is not an assertion of uniform impedance through pad escapes or via barrels. No foreign reference-plane split was found under the paired trunks. Hardware enumeration/data transfer in both orientations, electrical validation and any required USB compliance testing remain necessary.

## Independent physical checks

The exact final SHA is checked for:

- Connected terminal partitions on all 85 routed nets; no new padless or terminal-free copper components
- Full-width joins, pad-entry floors, and via annulus attachment; zero narrow joins or shallow via groups
- All 406 vias have functional multilayer use; all 303 plated-terminal attachments to the three GND reference planes pass
- No exposed dead trees; exact preservation of the 97 GND stitches
- Refill consistency using the matching project/rules/library context
- Reference changes bounded to exact, isolated own-via antipads; zero new exposure outside those voids
- Two unchanged nominal-pad advisory geometries match their historical, specifically reviewed non-bottleneck dispositions; this comparison does not reissue the old full-board qualification

`physical-check-summary.json` retains the raw audit status requiring reference review. `validation-summary.json` records that final polygon/visual review separately; it does not rewrite raw evidence.

## Recheck and manufacturing status

Open `controller.kicad_pro` with KiCad 10.0.6 or compatible newer KiCad, using the included local library tables. Run DRC with all severities, all-track errors and schematic parity, and ERC with all severities. The supplied `measure_usb_paths.py` runs under KiCad's `pcbnew` Python environment:

```
python3 measure_usb_paths.py /path/to/controller.kicad_pcb usb-path-lengths.json
```

The repository's historical P6 release Gerbers, supplier checks, manifests and exact-source export guard still describe the old qualified source. They were **not** overwritten, recertified or bypassed. Do not fabricate from stale exports or treat this native-only DRC repair as a released manufacturing package. A separately verified regeneration/qualification is required before fabrication. No push, merge, order or external CAD upload was performed.
