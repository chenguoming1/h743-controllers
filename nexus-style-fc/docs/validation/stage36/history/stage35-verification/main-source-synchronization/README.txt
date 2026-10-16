Stage35 source/placement/assembly consistency: PASS

Bound routed PCB SHA256: bf9a10563839b18071dedd1c4a71af60c25ac19e94f392adb1917955b1f4e95d
Project SHA256: ac4eb6dea52f66417f12afe9a23ee7a8ff2ff9872cee20164a383bf3e61b2066
Bound tools/design.py SHA256: 2ce4d96fe38166232206ae2b9ff0b7716ba0f6aa0c83505f7f9ab5f6a2faff78
Runtime: official KiCad 10.0.7.

- 89 main footprints and 356 pads regenerated with zero differences against stage35, including pad net names, dimensions, shape, roundrect radius, copper layers and mask/paste membership. Position tolerance: 0.000002 mm.
- All footprint poses and pad geometry are unchanged from sealed32. The only pad-net-name change is the exact, electrically equivalent USB_DM -> USB_DN alias.
- All 88 legacy parts and 89 approved main selections are identical to sealed32 after that exact alias. Every other identity, pin role, value, LCSC number, note and placement is preserved. Project JSON likewise differs only by that alias.
- BOM and CPL are byte-for-byte identical to sealed32: 48 BOM rows and 83 assembly parts/placements.
- Stage35 PCB, schematic and project were not changed. Frozen32 inputs stayed unchanged. Only stage35 design.py PCB/placement provenance comments were rebound after verification passed.

main-regenerated-floorplan.kicad_pcb is an UNROUTED comparison artifact. It must not replace the routed hardware board or be used for fabrication. This proof does not replace native electrical, mechanical or manufacturing-output reviews and is not manufacturing approval.

The old global courtyard normalizer without the required stock model files is not the verified path. Isolated main-floorplan generation is the demonstrated reproducibility result; no full build, refill or routing overwrite was run here.

verification-report.json contains the full checks and protected-input hashes. light-source-comparison.json records the earlier pre-binding source comparison. The two Python helpers preserve the verification procedure; verify_usb_successor.py refuses an existing generated floorplan output, so reproduction requires a separate fresh copy of the successor verification directory.
