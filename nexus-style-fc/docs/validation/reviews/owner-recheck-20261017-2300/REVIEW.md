# Owner routing update recheck — 17 October 2026, 23:00 SGT

**Fresh main PCB JLCDFM matches all 29 previous category triples. Native main ERC/DRC/opens/parity are zero.** New Gerbers and the complete order package include the owner's saved routing changes and one refreshed ground pour. Child source and manufacturing files are unchanged.

## Exact input and output

- Owner-saved main PCB before refill: `fadda7e3fd0d2508f010b96656ba0bb85a85304c5445a28c7dd9fc1671d517e5`.
- Current main PCB after native refill: `8f324006ba29d38dd2e8b8adcf8b9d2fb9a5b34a392e570476b47ba319ba8631`.
- Current main Gerber ZIP: `0075c2035c89f495c38b54ac08123801784e94e04218f2fd01e63c303b30abbc`.
- Full [source/export bindings](binding.json), [owner routing delta](source-delta.json), [main DRC](native/nexus-style-fc-drc.json), [main ERC](native/nexus-style-fc-erc.json).

The owner changed routing (47 segments added, 72 removed, five retained segment objects changed). Component footprints, positions, values and pads, all 228 vias, board outline, stack and USB/VCAP route objects match the preceding order-fixes revision exactly. The native refill changed only one GND zone's saved filled polygons; no non-zone objects changed. Project/rules and existing ERC ignored checks remain unchanged.

The saved schematic has zero ERC findings and matches PCB parity. Child checks were rerun: zero ERC/errors/opens/parity with the same 11 bare-contact courtyard warnings. The unchanged child did not need a new web upload. BOM/CPL remain **byte-identical**, 53 groups / 84 populated placements. Main Gerber ZIP integrity and loose/archive equality were checked; child CAM is untouched.

## Fresh PCB DFM

[Open the current result](https://jlcdfm.com/viewer?pcbUploadFileId=634379917344632834). Uploaded the regenerated main Gerber ZIP and explicitly ran DFM. [Category triples](pcb-dfm.json), [page text](pcb-dfm.txt), [screenshot](pcb-dfm.png).

All 29 triples exactly match the previous check, including zero danger/warning on trace width, spacing, pad spacing, corners, mask bridge, mask-to-trace, short-slot and slot-width checks. Displayed totals remain **257 danger / 188 warnings**; these include capped silk and generic PTH/via classifications and are not unique defect counts or a clean overall DFM pass. No new category counts appeared.

The prior assembly analysis was **not rerun**: component/pad/hole/outline geometry, sides, model part identities and the actual BOM/CPL are unchanged. Its earlier result remains historical evidence, not a new SMT check for this upload. The [order-fixes engineering review](../order-fixes-2026-10-17/REVIEW.md) documents the remaining USB shell soldering/alignment review, dense assembly tooling/stencil requirements and inherited component-edge/lead-to-hole/pin-edge flags. Those requirements are not cleared by this PCB rerouting check.

Fresh [USB ground projection](usb-reference.json) still shows continuous In4 ground under the two matched In3 trunks; USB/VCAP route objects themselves are unchanged. No new impedance or VCAP hardware certification is claimed.

## Current order files

Use the updated [manufacturing files/package](../../../../manufacturing/README.md). The order ZIP was rebuilt with current main Gerbers, the unchanged child Gerbers/BOM/CPL and current instructions/manifest. Source hashes were rechecked after export. Continue to require the named stacks, 90 Ω main USB production process, POFV for all 228 main vias, matched fit and factory USB shell-joint acceptance. No purchase or supplier acceptance occurred.
