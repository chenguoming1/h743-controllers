# Isolated U10 TI DBV land-pattern and local routing delta

Status: complete guarded proposal, locally checked in official KiCad 10.0.7. No refill or full DRC was run on this isolated branch. Integrate with the IMU repair, then run native refill, full DRC, schematic parity, and final mechanical joint proof before acceptance.

## Integrate

Use `python apply_guarded_delta.py INPUT.kicad_pcb OUTPUT.kicad_pcb`. The script requires exact matches for all eleven old top-level objects, checks every object before writing, writes a separate output, and refuses overwrite. It permits unrelated parent changes, including zone refill. The exact same script handles `.kicad_sch`, using `guarded-schematic-delta.json`; that patch changes only U10's Footprint property, guarded by the entire original U10 symbol block. The board source before refill was SHA256 c7e4e8a2021b05de2f7d88b8b9e8c2de39b14f030ecea3cd1bce25c1b0826a3e. Guard tests also succeeded against the parent's later-refilled stage29.

Copy `TPS70933DBVR_TI_DBV0005A.kicad_mod` into the main library, or invoke the standalone `generate_u10_ti_variant.py PATH/TO/hardware/library/NexusFC.pretty`. It writes the dedicated variant only. It neither changes the generic SOT-23-5 footprint nor edits any board/source generator. Repeated generation is idempotent and refuses to overwrite a different variant.

Main-only source-sync hook: call `generate(main_hardware_library_dir)` from the main build path, and override only U10's footprint identity in `get_main_parts` to `NexusFC:TPS70933DBVR_TI_DBV0005A`. Preserve the existing U10 part, LCSC ID, symbol, pin-role map, center, and angle. Do not modify the sealed shared `tools/make_footprints.py` or the child interface generator. The main-only source worker should bind this identity in board and schematic emission.

## Exact scope

- U10 center (109.4,107.05), front side, angle0 unchanged; TPS70933DBVR / C89347 unchanged.
- Pads1–3 at x−.95/0/+.95,y+1.30; pads4–5 at x+.95/−.95,y−1.30. All .60×1.10mm roundrect with .05mm radius. Existing F.Cu/F.Paste/F.Mask membership preserved.
- Pad roles unchanged:1VSYS,2GND,3floating EN,4NC,5 3V3_SENS. No blind rotation or net reassignment.
- Dedicated footprint ID and description updated. X courtyard bounds remain±1.656; Y bounds become±2.00, retaining an explicit .15mm dense-layout land margin. This is not an IPC .25mm courtyard or qualified placement-tolerance envelope. With the parent’s main coordinate mapping, U10's top courtyard is main-local Y5.05; J1's preserved reserve endsY5.00, so the nominal gap is.05mm. Final joint proof must verify it.
- SCK via f740a49a… moves from(110.957383,107.736094) to(110.987383,107.726094), delta(+.03,−.01). Its B.Cu and In2.Cu incident endpoints move together.
- MOSI via7ca855e7… moves from(111.488508,108.00173) to(111.528508,108.03173), delta(+.04,+.03). Its B.Cu, In2.Cu, and pre-existing short In3.Cu endpoint move together. The B.Cu elbow moves from(111.375508,107.88873) to(111.415508,107.91873), including the upstream B.Cu segment endpoint. Via sizes/drills/layer pairs and track widths/layers/nets are preserved.
- The C19 3V3_SENS elbow moves from(107.895,108.95) to(107.865,108.95); only tracks9b50f9bd… and bc65af68… change. The active IMU worker confirmed neither is in its replacement branch.
- No IMU_CS, B_RX, FLASH_CS, sensor-feed branch, C9, other footprint, zone, net, or origin edit is included.

## Local native evidence

`local-validation.json` and `validate-local.log` check every changed track/via and all five U10 pads against native foreign-net copper on all six layers, excluding stale fills. Minimum changed-object copper gap is.131717mm versus.127mm rule; no copper violation. Every relevant via-hole/foreign-copper pair is at least.20mm. Neither moved via is within.10mm of any front/back pad, regardless of net. Copper/routing changes introduce no new via or paste intersection.

The widened VSYS pad1-to-C19-feed gap improves to.141387mm after the elbow shift. Existing U10 pin1/2/5 path entries remain full-width, centered inside their new lands; EN andNC remain unrouted. Explicit native layer contacts remain SCK B.Cu/In2.Cu and MOSI B.Cu/In2.Cu/In3.Cu. The tiny MOSI In3 endpoint segment was already contained inside its via; this proposal preserves it and does not claim it provides an independent external branch.

`check-library.log` confirms the board and dedicated source library match on all five pad numbers, local centers, sizes, shape, radius, and copper/paste/mask layer membership. The generic library is unchanged.

No complete connectivity, post-refill clearance, silkscreen/courtyard DRC, or updated factory-model alignment claim is made here. The TI example is a documented land-pattern improvement, not proof of the unexplained JLCDFM model-overlay cause. Full native verification and final combined mechanical proof remain the acceptance gate.
