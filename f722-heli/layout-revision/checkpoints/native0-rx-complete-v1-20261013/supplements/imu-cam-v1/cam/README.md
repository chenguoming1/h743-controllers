# Internal CAM evidence and proposed precision correction

**INTERNAL WIP CAM REVIEW. finalrelease=false.** See REVIEW.md for measured results and REMAINING-GATES.md for unresolved manufacturing acceptance. Actual source PCB is 84229c571433bd72d410fb18d02cffa3a380c00a87fbe1270e3a73b63f8dd6cd.

This compact packet contains every generated Gerber/drill/map/report/CSV, the four official SVGs and nine-page PDF, targeted actual-aperture raster, numeric evidence, the original failed verifier result, and the separately reviewed exporter correction. Actual CAM/preview outputs and the original failure remain byte-exact. Public script/report copies normalize local absolute paths to declared tokens; their original SHA256 identities and string-normalized AST checks are recorded in NORMALIZATION.json. Numeric results and source/output hashes are unchanged. The original local bytes remain preserved outside this publication packet. No execution grants are published here.

The corrected exporter remains a proposed tool artifact in this packet. The publisher may adopt it under the separate reviewed adoption instruction after verifying the repository file's original d571a976… identity. This packet itself performs no repository modification or formal export. Source CAD/parts stay byte-exact.

## Reproduction

Run `python3 replay.py verify` to verify every packet file. `python3 replay.py controls --output /new/scratch/path` runs only the two existing matcher control sets plus the explicit floating-boundary check. It does not invoke KiCad or run a release gate.

The other host-only modes are `drill-csv`, `apertures`, and `u15-mask`. Supply `--hardware` pointing at the exact 61-file paired hardware and `--native` pointing at the SHA-bound after.native.json.gz. Geometry modes also require `--lock` pointing at the existing shared heavy-lane lock and optionally `--deps` pointing at the existing Shapely 2.2.0 installation. Always use a new `--output`; geometry retains the original bounded parser/resource checks. Do not run geometry while another owner holds that lane. The adapter changes only path bindings in new scratch copies, verifies input hashes and leaves the source packet and original local reports/scripts intact. No native export, refill or library/model change is performed.

Reference runtime for the host geometry: Python 3.12.14, Shapely 2.2.0, Pillow 12.3.0. Matcher checks use only Python standard library. The original KiCad output runtime was official 10.0.6. The shape parser intentionally handles only the observed plot subset; this is not a general CAM certification framework.

Under the planned checkpoint placement `supplements/imu-cam-v1/cam/`, native input is `../../../native/after.native.json.gz` (83a6c876…), while prior moved-part evidence uses `../../conditional-dc-v1/assembly/after-pad-settings.json` (ba62b0e6…). The latter is not read by the CAM replay. Hardware location is an explicit argument to avoid assuming repository layout. Exact external hashes and paired source file list are in MANIFEST.json and SOURCE-IDENTITY.json.

The original diagnostic's zero-epsilon proof and the reusable correction's 16-ULP arithmetic guard are deliberately separate. All final receipt/source/native/runtime checks retain identical ASTs; only the drill comparison in verify_fabrication changes. The raw rounded-bin failure and both U15 exact-contour mismatches remain preserved; neither is silently relabeled as an original-run pass.

Path tokens: @CAM@ maps to actual-cam/; @DIAGNOSTIC@ maps to evidence/ or the new replay output; @NATIVE_INPUTS@ is the adapter’s hash-checked native/hardware staging; @ORIGINAL_EXPORTER@ maps to original-exporter/native_export.py; @RUNTIME@ is a fresh scratch runtime binding. The replay adapter resolves these tokens. Lock naming is normalized to shared-replay.lock while the actual lock path remains an explicit argument.
