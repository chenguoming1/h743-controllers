# Stage35 final DFM and USB verification

**PASS: the saved PCB, fresh Gerbers and plated drill export contain the final v2 repair.**

PCB SHA256: `bf9a10563839b18071dedd1c4a71af60c25ac19e94f392adb1917955b1f4e95d`.

- Exact SW replacement remains 0.25 mm B.Cu: `(103.55,110.15)` → `(103.55,110.65)` → `(102.6,111.675)`. All three U5 SW pins retain connected physical witnesses to L1.1.
- Actual Gerber path-to-U5.3 gap is **0.235 mm**, including complete strokes and circular endcaps (diagonal alone: 0.247864551 mm). U5.3 copper, mask and paste use identical 0.28 × 0.85 mm oval apertures. The former 0.00869647 mm sliver-producing diagonal is absent.
- All four front sensor dead-leaf segments, its bottom branch, its six-layer via flashes and its plated drill are absent from the fresh exports. All 15 3V3_SENS pads remain connected, all six retained sensor vias retain their exact contacts, and no front 0.25 mm free endpoint remains.
- The accepted native DRC receipt reads **0 errors, 0 opens, 0 schematic parity issues, 56 warnings**. Its copper-sliver and dangling-track warnings are absent. The remaining warnings are 30 silk overlap, 15 silk over copper, 7 track-not-centered-on-via, 3 silk-edge clearance and 1 footprint-type mismatch. This verification did not rerun DRC or refill.
- Final saved USB verification preserves native USB_DP ↔ USB_DN recognition (codes 22/23), all ten pad contacts, 102 routing items, four tapers and all four 0.08 mm bevels. Both ~13.133 mm In3 paired trunks and all four bevels have zero sampled In4 center/edge gaps. Every measured reference-coverage row matches stage33 exactly. Nonuniform closer In2 coverage and existing launch projection gaps remain recorded; these projections do not establish field-solved impedance or continuous return impedance.

## Evidence

- `saved-stage35-native-proof.json`: exact routing delta, all pad identities, sensor/SW connectivity, local foreign-copper checks and retained via contacts.
- `gerber-proof.json`: strict modal aperture/primitive parsing, exact coordinates and line numbers, analytic full-path gap, old geometry absence, via/drill absence, and manufacturing hashes.
- `final-verification-summary.json`: binds the native accepted-run receipt and all checks to the final source hash.
- `../usb/saved-stage35-native-proof.json`, `../usb/saved-stage35-reference-projections.json`, `../usb/reference-preservation-comparison.json`: final USB proofs.
- `../usb/USB-POST-REFILL-VERIFICATION.md`: preserved full-speed 12 Mbit/s mismatch disposition and remaining signal-integrity qualification. Approximately 2.57 mm geometric mismatch alone remains no established mandatory meander repair.
- Reproducible read-only verifier scripts and logs are stored beside these receipts. `apply_dfm_leaf_and_sw_fix.py` is a copy of the guarded historical delta, not an action taken during final verification.

All board/manufacturing reads left source hashes unchanged. This closes the bounded local geometry findings; it is not a new JLC report, assembler acceptance, impedance certification or fabrication/flight release.
