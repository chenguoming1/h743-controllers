Final main-board source and assembly consistency checks

Bound PCB SHA256: f214f8141e8f21a7e0983c8eb4f2be89634e3b69d0d2b168a1ac3153f28a83de
Approved project SHA256: b34415304c2bd364fed7f2f22231db9a893f4a0a4810e0c9300f54499674ba5b
Runtime: official KiCad 10.0.7.

PASS: 89 generated main footprints and 356 pads match the bound routed PCB in reference, part identity, position, side, rotation, pad number/net, size, shape, roundrect radius, copper layers and mask/paste membership. Position tolerance is 0.000002 mm for float-to-integer quantization. Legacy PARTS and sibling selections are unchanged. The only documented footprint-identity exception from the approved baseline is U10's dedicated TI DBV0005A variant; its TPS70933DBVR / C89347 identity, symbol, pin roles, center and angle are preserved.

PASS: 48 BOM rows cover 83 assembly parts. All 83 CPL rows match the bound PCB and existing auxiliary origin (99.95, 133.15 mm). Test pads and the non-purchased header joint remain excluded. The U10 BOM footprint field now names the dedicated variant.

The regenerated floorplan here is an UNROUTED generator comparison artifact. Do not replace the routed hardware/nexus-style-fc.kicad_pcb with it or fabricate from it. This evidence is not a fabrication/assembly qualification or a replacement for the separate native DRC, schematic parity, mechanical integration and output reviews.

Source integration:
- tools/design.py applies all 89 final main placements after approved component selection.
- tools/build_floorplan.py invokes the standalone U10 variant generator.
- tools/generate_u10_ti_variant.py creates only that dedicated variant and refuses mismatched existing content.
- tools/fix_courtyards.py exempts only the named generated variant.
- Shared tools/make_footprints.py and the generic U10 library source remain unchanged.

Read u10-source-integration-check.json for the staged-tree missing-model caveat affecting the pre-existing global courtyard normalizer. The isolated main-floorplan generation exercised here does not run that global rewrite.

Reproduction helper: synchronize_main.py. Run it with approved KiCad 10.0.7 Python, --source-root PROJECT_ROOT, --pcb PROJECT_ROOT/hardware/nexus-style-fc.kicad_pcb, a fresh external --output directory, --approved-baseline-root BASELINE_ROOT, --expected-pcb-sha256 matching the above, --verify-floorplan, --bom-cpl, and --kicad-cli pointing to the same approved runtime. The helper writes a separate source overlay and unrouted comparison board; it never refills, runs DRC, or overwrites its inputs. Recheck project and PCB hashes before and after any later native operation.
