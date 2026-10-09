# Source and evidence boundaries

This is unfinished routing work. Accepted77 is native board `1ff8ee645bd5fea7bbbc30cd4e5269aab76a2032efe3e2c4e77a0becd85e9edf`, with 77 opens, zero errors/warnings, and eight complete ordinary nets. The original protection checks pass 1/18 cases and supplemental checks 5/7. The retained process, mechanical, firmware and schematic parity gates pass; all-net connectivity and electrical/reference qualification remain open.

## Current source

The top-level Python/shell and Java adapter sources are the current snapshot. They include conservative full-width native target shapes, 0.10 mm extra target depth for plated contacts, explicit empty-target handling, copied native contact identity, statistics reuse restricted to proven no-op early returns, insertion diagnostics, and experimental 18-unit planning reserve / stock slow-tree selection. The paired full-board zero model identity in `checks/current77-source-identity.json` matches every packaged Java source hash. Current zero import reproduces the accepted77 board bytes exactly. Four subsequent slow-tree attempts fail and the output session is identical to the zero session; there is no current-source successful-route proof.

## Historical native routing receipts

- Immutable v3 receipts and session packets are retained byte-for-byte except the staging overview, manifest and status files. Their original hashes and source/model identities remain authoritative. The v3 manifest SHA is `26609ee1487baa1ef61367309f8e8833f687412f3d1f2eaa99a445d743712e3e`.
- Accepted79 and accepted78 handoffs retain their historical adapter hashes and endpoint evidence. The accepted79 SERVO3 endpoint extension is explicit postprocessing. Accepted78 D1_A has no session postprocessing.
- Accepted77 D2_A uses explicit native construction from a path located by a failed stock insertion. The selected path is normalized, then four waypoints are moved outward by the recorded 0.025 mm detour. The six new segments contain no via; all fourteen prior ordinary segments are retained. Nominal nearest foreign-copper gap is 0.152040 mm. This is nominal geometry, not manufacturing margin.
- The exact accepted77 constructor used is `sessions/accepted77/construct_located_session.used.py`, SHA `125c196d13ea3cda61c34ae8b944f0b0aa1081a96c57c989c0bf5fc28eedbb5c`. The current top-level constructor is separately manifested and must not replace that historical identity.
- Accepted77 compact packet geometry and importer-only projection have passed pure-Python checks. A new native replay has not been run. Native acceptance receipts came from the original full-model import. Source candidate06 board and paired project are external prerequisites for native replay.

## Control versions

`checks/target-era-source-identity.json` binds the preserved full-board copy and zero controls to historical model `a8e2d8b1b305b9f1ddbb7a63443e6c928c104da7270bf82180b07259e04f06bb`; these do not prove the whole current binary set was used. Target-positive and empty-target receipts bind fixture, source and loaded class hashes. The current contact source is the tested target source, while the empty-target maze class hash predates recompiling the planning constant. The separate margin18 proof verifies all five inlined call sites in the four intended current consumer classes.

The insertion fixture establishes the failure threshold and successful isolated straight-segment insertion without changing physical guard geometry or the clearance matrix. It is not a complete-route claim. Clearance-audit reports bind their source boards and loaded classes; the four accepted through-via sites do not demonstrate a complete multilayer route. Tiny generated geometry fixtures, native geometry/models, JVM binaries and caches are excluded and must be regenerated from the exact inputs before rerunning these historical controls.

`EVIDENCE_INDEX.json` provides hashes for the relevant preserved receipts and current source identities. The base manifest, current full manifest and external delta metadata distinguish unchanged historical evidence from new or changed payload files.
