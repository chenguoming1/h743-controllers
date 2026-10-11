# Native7 IO4 contact and protection validation, version 1

This is a sealed, source-only validator for the exact **eleven-cut** native7 IO4 proposal. That routing scope failed mutual RX first-via packing: its available center-domain diameter was at most 0.194599 mm against a required 0.577010 mm separation. No complete candidate exists. No native import or actual-board contact audit was performed. The bound importer independently disables native execution for this rejected scope. A later donor scope requires a separately reviewed version, with exact new cuts and preservation obligations.

## Fixed scope

The source PCB is `a7355c26018a7bea66b77ccdc5201c2042a96b8e6820179fc5684dc72e170b4f`; its native export is `53ddf869c36da4a026880c6b3346dd1ddb304aaabaa948b20f1e66fc3db62505`. Eleven full native record cuts comprise four old RX entrance tracks, three U15 GND records, and four FLASH_HOLD_N records. The source-scope v2 SHA is `815df90a2ae84d774acc993b100d110405db7b3d4e9a5f965450943cc4aed487`.

Only these pad-net identities change, with every native pad contour and all 156 poses fixed:

- U15.1 → `unconnected-(U15-IO1-Pad1)`
- U15.10 → `unconnected-(U15-NC10-Pad10)`
- U15.5 and U15.6 → `PORT_C_RX_EXT`

The physical RX clamp is bonded IO4, U15.5. U15.6 is an upstream routing land; no internal NC bond is assumed. TX remains on U15.2/NC9. The numerical native net codes may be reallocated only through the importer's verified global name/code bijection. All other native record fields, original C12/R3/IMU/TX/power, footprints, pad shapes, and board structure are exact.

## Validation gates

`audit_native7_IO4_final_contacts_v1.py` replaces the old 90-cut/IO1 input and acceptance scope. It reuses only the hash-pinned version-2 native contour/contact kernels. It does not call the old 90-cut loader or audit acceptance function.

1. Pure input validation binds fourteen files, the exact paired source plan, eleven full removal records, four canonical pad names, complete recipe centerlines, native UUID provenance, the role sidecar, native board/export hashes, and fresh paired netlist.
2. Every original positive-area native component is preserved. Fragment identities are retained, so a new physical drill splitting an unchanged UUID is detected. Original opens are checked component by component; closing the five unrelated opens is not a condition or a claimed result of this narrow change.
3. Actual RX and FLASH_HOLD_N must each form a complete positive-area component. Every original GND component, including retained U15 GND and saved planes, must survive, and all new GND records need measured contacts. GND routes retain the original minimum 0.25 mm width through the paired importer.
4. All actual protection rows are evaluated from final native copper. Only published-06 changes its clamp from U15.1 to U15.5; the other 21 actual rows and the other 17 candidate rows remain semantically exact. The final native is also tested against the historical IO1 expectation, whose failure is preserved separately rather than treated as a new acceptance requirement.
5. Removing the actual bonded pad's copper must disconnect source and target. The two resulting physical branches require at least 0.127 mm plus the exported polygon-error bound outside the pad. RX additions carry explicit upstream/downstream roles. Both roles need positive-area full-width contact to U15.5; NC6 belongs only to the upstream component.
6. Exact physical drill contours are subtracted from all affected objects and nets. Same-layer joins require positive area; vertical joins require declared plated layers and actual drill-boundary contact. New or changed joins require a full-width straight-track section or complete annular-land coverage. Actual recipe endpoints also require finite native contact.
7. The inherited version-2 width rule permits a narrow T branch on a wider retained track only with exact unchanged primary data, unchanged conductive shape, and a continuous full-width interior strip. It does not excuse a narrow serial replacement. Numeric net-code remapping alone does not mark a primary as geometrically changed.

No source contour is repaired, snapped, simplified, or normalized. Width witnesses explicitly retain the native exporter error of 0.00001 mm, with a two-boundary nominal-width tolerance of 0.00002 mm. Original inherited width findings are reported separately and are not silently waived.

## Files and execution

- `native7-IO4-contact-validation-plan-v1.json` states the exact scope and input requirements.
- `native7-IO4-contact-request-v1.template.json` is an intentionally incomplete request template. No real final native, plan, or constructor receipt is supplied because routing failed.
- `native7-IO4-contact-lease-v1.template.json` is inactive. A real-board audit must bind the exact request, this validator, the output path, and a bounded serialized runtime.
- `test_audit_native7_IO4_final_contacts_v1.py` contains 20 synthetic/JSON controls. It uses fabricated shapes only.

From the rebuild root, reproduce the bounded host tests with:

```sh
env PYTHONPATH=python-deps:recovered-native7/recovery-importer python -m unittest discover -s recovered-native7/recovery-importer -p test_audit_native7_IO4_final_contacts_v1.py -v
```

The pure input API is `load_bound_inputs(request_path)`. Actual geometry runs only through `audit_final_native_contacts(request_path, lease_path, new_absolute_output_path)` or the equivalent CLI `--request ... --lease ... --out ...`. `--check-inputs` performs no geometry or CAD execution.

The importer manifest lists further paired-source and parser inputs; those dependencies are not embedded here. The source native export is reproducible from the published native7 checkpoint. The old common 90-cut proposal and historical raw graph receipts are not runtime inputs to this validator.

## Acceptance limits

A successful contact report would establish the stated native contact/protection topology only. DRC/clearance, ERC, paired source parity, final plane necks, saved-fill changes, return/reference continuity, ESD behavior, current distribution, VCAP impedance, and manufacturing checks remain distinct gates. Power evidence remains stale. A saved ground-plane DC contact does not establish ESD or AC performance.

The five pre-existing ordinary opens are FLASH_SCK, FLASH_MISO, FLASH_MOSI, PORT_C_RX_MCU, and PORT_C_TX_MCU. They are neither silently required to close nor claimed closed by this narrow validator. No geometry outcome is inferred from the passing synthetic tests.
