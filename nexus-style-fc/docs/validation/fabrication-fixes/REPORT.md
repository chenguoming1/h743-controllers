# Fabrication cleanup checkpoint

Base: merged consolidation commit `63e48c739e70bb4c09dcf502f92ee0f2819101ea`. Changes are in the canonical project root. **Not released for fabrication, assembly or flight.**

## Fixed and verified

- Corrected five full-width track endpoints at three existing vias (3V3, GND, DSM_TX), and removed two tiny redundant stubs wholly inside their same-net via copper. All via positions, sizes and drills remain unchanged. Seven centering warnings are gone.
- Corrected mixed-technology J6 to through-hole classification in the PCB and its local footprint. It still appears in the unchanged 83-row main CPL; factory assembly-method review remains required.
- Transferred 21 conflicting connector/passive outline elements to the corresponding Fab layer. No text or diode polarity artwork was changed. Front soldermask/silkscreen preview was visually inspected. All 53 native silk warnings are gone. Main-only artwork footprint variants preserve shared/sibling footprint definitions; source, schematic and BOM identities match.
- Added exact allowed footprint identities to the reviewed inductor symbol and a reviewed child-contact symbol. Pin definitions and connectivity are unchanged. Child's 11 footprint-filter mismatches are gone; its 11 missing-courtyard warnings remain visible for bare joint contacts, not populated component bodies. No invented courtyard envelopes or suppressed checks.

## Final verification

KiCad 10.0.7, complete native checks with all severities and schematic parity:

- Main: ERC 0; DRC 0 errors, 0 warnings, 0 opens, 0 parity findings. Previously 61 DRC warnings.
- Child: ERC 0; DRC 0 errors, 0 opens, 0 parity findings; 11 documented bare-contact courtyard warnings. Previously 22 warnings including parity.
- Four inherited ERC ignore settings remain unchanged; no DRC exclusions or rule relaxations were introduced.
- Read-only source/native regression: all 89 main footprints and 356 pad geometries, drills, pad layers, pin nets, placements and selected parts match the accepted predecessor, allowing only declared artwork footprint names. Main still has 83 BOM/CPL parts; artwork names split 48 predecessor BOM groups into 51. CPL bytes are unchanged. Child's 12 footprints/32 pads, pin nets and BOM/CPL pass; child PCB and CAM remain unchanged.
- Main CAM regenerated from this PCB, including drill and all six copper layers. Files and hashes are in [INPUT-BINDING.json](INPUT-BINDING.json).
- Main PCB SHA-256: `7a5abe70f1c7f0ac5693cfa4a3156432f6321f5907bbcb0e0892687da51a5d60`. Child PCB SHA-256: `b49ef4108ab0b85d4cd96fac22553e3bc16b214f5acde148a8680e1212097ee6`.

Reproduce checks from the project root using `tools/validate_project.sh` with KiCad 10 and `python docs/validation/fabrication-fixes/check_sources.py` with its matching pcbnew Python. The latter uses pinned read-only comparison helpers, never their generation entrypoints.

## Remaining manufacturing and engineering gates

- Predecessor stage36 JLCDFM completed PCB and SMT screening on 16 October; it is **not a check of these new CAM bytes**. Its six positive pad-spacing danger counts describe Gerber apertures without nets. Native positive pad-to-via gaps below 0.127 mm are all same-net; do not report them as confirmed shorts or blindly move fanouts. Exact aperture correlation and new-input screening remain open.
- Drill/paste proximity is a real assembly concern. The native screen finds 14 via-hole intersections with pasted pad copper (tenting flags do not guarantee a reliable mask barrier inside a pad opening). A bounded 0.5 mm relocation search for five untracked ground stitching vias found no accepted local candidate; no forced move or route change was kept. Fill/cap/tenting/stencil process qualification or a separately reviewed placement/routing change is still required. The screen uses actual pad polygons with zero paste margins in these hits; it is not a factory stencil approval.
- J6 shell slots remain 0.849986 × 0.599998 mm. JLCDFM's generic 24 mil width flag is stricter than [published JLC multilayer slot capability](https://jlcpcb.com/capabilities/pcb-capabilities/), but the short-slot length/width rule and finished tolerance still require process acceptance. No arbitrary hole enlargement was made.
- U10 remains the TI TPS70933DBVR land pattern and verified pin mapping. Predecessor SMT still flags missing/overlapping model leads; a model-orientation mismatch is unproven. Do not rotate the part/CPL without a physical pin-1/model comparison.
- C10/NRST remains remote; no passing local reroute is included. Actual six-layer stack, USB 90-ohm qualification, SI/PI/EMI, thermal/transient and physical tests remain open.
- C9 C69335 is Samsung CL10A475KA8NQNC. [ST DS11853](https://www.st.com/resource/en/datasheet/stm32f722ie.pdf) requires 4.7 uF and 0.1–0.2 ohm ESR for LQFP64; [Samsung's exact part information](https://product.samsungsem.com/mlcc/CL10A475KA8NQN.do) does not establish that ESR window. DF is not ESR. Do not blindly add resistance or substitute the shared C5/C9 BOM group.
- D4 SMF13A's [catalog clamp](https://jlcpcb.com/partdetail/329064-SMF13A/C353315) is 21.5 V at its rated test pulse, versus [TPS629210 VIN/EN absolute maximum](https://www.ti.com/lit/ds/symlink/tps629210.pdf) of 18 V. This is a protection-coordination gate, not proof of actual BEC overshoot. Qualify maximum normal VX, source impedance/energy, tolerance and wiring overshoot before selecting a different TVS.
- The [pinned Rotorflight ICM initializer](https://github.com/rotorflight/rotorflight-firmware/blob/ba6c7e3/src/main/drivers/accgyro/accgyro_spi_icm426xx.c) supports unused INT2 for U2 pin9 at cold boot. Preserve its no-connect; bind actual firmware/register state and verify axes on hardware.
- Matched 9.3 mm tabs and 9.8 × 2.10 mm R0.50 slots remain nominal-only fit. Standard servo plugs are retained. Header catalog rating remains 3 A/contact; no 10 A system or pulse-current rating is established. Supplier tolerances, harness/contact current sharing, temperature and mechanical tests remain required.
