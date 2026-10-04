# Current native repair (2026-10-04)

This working native board is the DRC/physical-copper repair of main `491987e`. See [the current repair review](review/usb-routing-491987e/README.md) for exact source hash, checks, measured USB-C orientation skew, and bounded fanout rules.

**Native CAD checks pass, but this is not a regenerated manufacturing release.** Existing P6 Gerbers, supplier reports, manifests and source-hash export guard remain historical and unchanged. Do not fabricate from stale exports or bypass that guard. Component placement, CPL, BOM, schematics and local libraries are preserved.

---

## Historical P6 package description (not qualification of the current native hash)

# R3-S6-P6 controller

**Use this P6 package only. It supersedes all earlier fabrication packages. P5 contained confirmed narrow copper attachments and must not be fabricated.**

This is the final prototype PCB submission package for the 38 × 38 mm, six-layer H743 controller. Its current electrical map, component placement, 67 edge pads, side sockets, corrected supplier CPL and USB pair geometry are retained. Fabricate with the exact settings in `documents/P6-Production-Instructions.txt`; the assembly production approvals listed there must precede assembly.

The whole-board review covers all 85 routed nets and every copper layer. It simplifies coherent paths, removes unnecessary hooks and dead trees, repairs actual copper necks at joins/pads/vias, and retires six redundant signal vias. It retains justified obstacle escapes and the ground returns. The final source has 3,178 track segments and 406 vias, including all 97 ground stitches. It is 61.696 mm shorter than P5. Those counts supplement the actual geometry and visual evidence; they are not the acceptance test by themselves.

## What to use

The paths below are relative to the release ZIP root.

- `native/`: KiCad source, project libraries and the mandatory P6 export guard
- `release/single-board-gerbers/`: the current six-layer Gerbers, plated and nonplated drills, and job file
- `release/assembly/JLC_BOM.csv` and `JLC_CPL.csv`: 35 part groups and 79 placements; the CPL preserves the user's corrections
- `documents/`: schematic, assembly drawing, fabrication review and production instructions
- `native/review/routing-visual-review/index.html`: complete offline net-by-net visual atlas; unzip first, then open this file
- `validation/`: independent native, actual-copper, exported-file and supplier evidence
- `reconstruction/`: reproducible delta and historical input, for audit only; never fabricate that input

The ZIP manifest fixes every included byte. Final source SHA-256: `cf16a6f5ceae65aad217e29eef23a60dbc8f15af743b363df03aa5a42c9c71dc`. The final supplier project is https://jlcdfm.com/viewer?pcbUploadFileId=629361373570224129. Trace width and spacing are green; all three former hole-to-trace advisories cleared. The report gives the evidence-backed dispositions for remaining process/model alerts, including the unchanged 24 red / 6 yellow SMT records. These counts do not constitute assembly production approval.

## Readiness limits

Bare-PCB submission uses a specified supported process. Assembly still requires the supplier's final two-face placement/polarity drawing, a suitable carrier/support arrangement, an approved production stencil, and soldering all four USB shell anchors. The supplier regenerates its stencil, so the real U2/U11 split apertures must be requested explicitly. The package includes the concrete instructions; it does not claim an order or supplier production approval already exists.

First-article inspection and current-limited electrical, thermal, USB/firmware, connector and application tests remain necessary. Compilation and CAD checks do not establish flight readiness or a numerical probability of success.

## Regeneration

Use `native/tools/export_release_p6.py` only with its exact source/evidence guard. It refuses stale source and requires actual join, pad, via, plane and dangling-tree checks. `export_release.py` is the underlying producer, not an alternative release-acceptance path. Preserved older helpers and baselines are historical provenance.
