# Final95 IMU geometry and qualification

Read-only native review, 2026-10-07. This report binds the existing IMU geometry findings to the frozen final95 PCB, SHA-256 `4da0708a4795662cc32b035a0783c70b9bdb85fc386bd4d39af33385b175667f`.

## Exact-board result

Native KiCad 10.0.6 freshly loaded final95 and the retained accepted1 baseline, SHA-256 `f56e26bd33974daeba215012b1adb77789b21c219e79c35de93aaf0bce5caa32`. The baseline native export reproduces the earlier retained export exactly after removing its source-path label.

U2 remains ICM-42688-P on F.Cu at (23.209999, 11.6) mm, orientation 0°. Its exported footprint identity, placement and pad geometry are unchanged. No changed pad, track or via intersects any of the four windows below above the 1e-9 mm² reporting threshold. Saved zone-fill symmetric-difference area is exactly 0.0 mm² in each window on every layer. There are no drill holes or via copper in any window. The mounting-face central window has no copper, and no foreign pad or mounting-face pour intersects any window. These are geometry findings, not vendor-compliance or sensor-performance certification.

Both ground references and the existing buried/bottom routing remain beneath the IMU. In1.Cu and In4.Cu each contain 7.5 mm² of GND inside the full nominal package body. The sensor-layout qualification question remains open.

## Measured windows and content

| Window | X limits (mm) | Y limits (mm) | Interpretation |
|---|---|---|---|
| Nominal body | 21.709999–24.709999 | 10.35–12.85 | 3.0 × 2.5 mm body |
| Maximum-profile screen | 21.659999–24.759999 | 10.30–12.90 | Inherited 3.10 × 2.60 mm screening envelope |
| Engineering reserve | 21.515499–24.904499 | 10.1466–13.0534 | Existing placement/rotation allowance; engineering assumption |
| Central between-land window | 22.359999–24.059999 | 11.00–12.20 | 1.7 × 1.2 mm audit window; not a verified die boundary |

| Layer | Copper within nominal body | Union area (mm²) |
|---|---|---:|
| F.Cu | U2 lands | 2.970515 |
| F.Cu | Local fanout tracks, including copper overlapping lands | 0.748347 |
| In1.Cu | GND fill | 7.500000 |
| In2.Cu | CORE, IMU rail, IMU_MOSI and LED_RED_K tracks | 2.541105 |
| In3.Cu | SERVO3 and Port C UART tracks | 0.918632 |
| In3.Cu | +5V_PERIPH fill | 0.039630 |
| In4.Cu | GND fill | 7.500000 |
| B.Cu | IMU_SCK, FLASH_CS and FLASH_MISO tracks | 0.795180 |

Areas are unions within each object category. Do not add the F.Cu pad and track figures because their copper overlaps. The central window also contains 2.04 mm² GND on each reference plane, 0.177051 mm² CORE track on In2 and 0.015864 mm² SERVO3 track on In3. All figures above are freshly measured on final95, not copied from an older board.

## Supplier guidance and unresolved qualification

The reviewed source is [TDK AN-000393 revision 2.4, dated 2026-02-09](https://d17t6iyxenbwp1.cloudfront.net/s3fs-public/2026-06/AN-000393%20TDK%20InvenSense%20IMU%20PCB%20Design%20and%20MEMS%20Assembly%20Guidelines%20v2.4.pdf?VersionId=0JJT_E0010fzx6pG58sIeAXICnPVAVgn). Section 2.1, p6 recommends avoiding under-device vias, traces and copper pour. Section 2.4, pp8–9 discusses mounting stress and shows outward fanout. Unlike the earlier revision 2.0 indexed wording, revision 2.4 omits the explicit all-layer phrase. Its revision history explains neither that omission nor an exception permitting buried copper. A clear mounting face therefore does not establish compliance with the broader recommendation. The reviewed guidance is not a measured sensor-fault result.

Retaining this geometry preserves its present ground references while leaving qualification unresolved. A conservative full-body multilayer implementation would require coordinated signal/power rerouting and local ground-plane apertures. Removing the plane copper beneath retained traces would remove their references. A central-only exclusion is partial, not full-body avoidance. Any corrective layout needs renewed native connectivity/DRC, all-layer body checks, ground-return and power review, and sensor/assembly qualification. No sensor-noise, stress, assembly-yield or flight-performance guarantee is claimed.

The reviewed [ICM-42688-P datasheet, DS-000347 revision 1.9](https://d17t6iyxenbwp1.cloudfront.net/s3fs-public/2026-06/DS-000347%20ICM-42688-P%20v1.9.pdf?VersionId=XL060vOv88u6zsKx9dkBVJEyV452m0eq), §10.2 pp54–55, provides the nominal body dimensions. The larger screens above remain explicitly labeled engineering screening windows. Reviewed vendor PDF hashes and URLs are in [source-manifest.json](source-manifest.json); the PDFs, extracted vendor text and vendor page images are not redistributed.

## Evidence and reproduction

- [carryover.json](carryover.json): exact input hashes and machine-checked conclusions
- [candidate/audit.json](candidate/audit.json): final95 per-object, per-layer intersections and drill checks
- [candidate/six-layer-audit.png](candidate/six-layer-audit.png): plot of the exported native copper and audit windows
- [comparison.json](comparison.json): all nearby added, removed and modified objects and zone differences
- [source-preservation.json](source-preservation.json): original hardware/firmware byte preservation

The exporter is read-only. It exports saved fill polygons plus pads/tracks/vias whose bounds intersect x19–28/y8–16 mm, fully enclosing the audit windows. Copper shapes use a 0.00001 mm outside polygon approximation. The analysis reports positive intersections above 1e-9 mm². There was no SaveBoard, refill, rule edit, project edit, firmware edit or part edit. The geometric plane-cut screen in the detailed audit is only a hypothetical geometric calculation, not a refill, connectivity proof or return-current assessment.

This compact public packet retains the checked conclusions, source attribution, numerical intersections and six-layer plot. Full fresh native exports and portable export/analyze/rebind scripts are preserved in the recovery evidence; they are omitted here to keep the public evidence concise. Reproduction requires the exact accepted1/final95 boards, KiCad 10.0.6 Python and Shapely 2.1.2. The private recovery packet records the read-only procedure and source bindings.
