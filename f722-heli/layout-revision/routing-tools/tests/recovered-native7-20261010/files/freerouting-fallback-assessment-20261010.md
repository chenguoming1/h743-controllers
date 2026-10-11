# F722 Freerouting / Specctra fallback assessment

Read-only assessment, 2026-10-10. No router, JVM application, KiCad native operation, solver, CAD mutation, dependency download, installation or external write was performed. Only this assessment and its seal were written.

## Decision

Stock Freerouting/Specctra is not a demonstrated drop-in alternative for completing all seven opens while preserving the present exact-native contract. The historical pipeline already uses Freerouting 2.1.0 with project-specific contacts, guards, logical branches and incremental import. Continue the current exact-geometry workflow and incremental importer. This finding is not a proof of global routing infeasibility or of universal Specctra unsuitability.

A later deliberately isolated five-net experiment could target PORT_C_RX_MCU, PORT_C_TX_MCU, FLASH_MISO, FLASH_MOSI and FLASH_SCK while freezing all other source copper, including PORT_C_RX_EXT. Its only potential new information would come from changed planning representation or search settings; changing the tool name would not introduce a new engine. No such experiment was run or authorized by this assessment.

## Source binding

- Board: recovered-native7/ordinary-routing/tests/native13-access/joint-native-import11-v1/candidates/published-reference02/f722-heli.kicad_pcb
- Verified board SHA-256: a7355c26018a7bea66b77ccdc5201c2042a96b8e6820179fc5684dc72e170b4f
- Adjacent f722-heli.native.json SHA-256: 53ddf869c36da4a026880c6b3346dd1ddb304aaabaa948b20f1e66fc3db62505
- Historical repository: chenguoming1/h743-controllers, commit fabc7f2213d4e1a200396a3229d23b305ef90d3d, tree 5e8748de94eb6da6057cae5e116cf3339083a014. Historical paths below are relative to f722-heli/layout-revision/routing-tools/.
- The checked checkpoint README records seven opens: two PORT_C_RX_EXT connections, one each on the five nets above. All actual U15 RX assignments remain the source IO1/pad1 + NC10 mapping. The proposed IO4/pad5 + NC6 change was not adopted or modified.

## Existing engine and historical attempts

[THIRD_PARTY.md](https://github.com/chenguoming1/h743-controllers/blob/fabc7f2213d4e1a200396a3229d23b305ef90d3d/f722-heli/layout-revision/routing-tools/THIRD_PARTY.md) identifies the Freerouting-derived Trace.java, NativeGuardFactory.java, NativePadContactArea.java and LocalRouter.java. The V19–V24 READMEs preserve the later candidate lineage; they do not establish a fresh stock-router success on this seven-open board.

[Official dependency identity](https://github.com/chenguoming1/h743-controllers/blob/fabc7f2213d4e1a200396a3229d23b305ef90d3d/f722-heli/layout-revision/routing-tools/vendor/provenance.json):
- Freerouting 2.1.0 JAR: https://github.com/freerouting/freerouting/releases/download/v2.1.0/freerouting-2.1.0.jar
- JAR SHA-256: 2c07d58f75dac03782664081e7a58b41c25400d871a9fcf166a2ea6fe60d5def
- Tagged source SHA-256: 6c635ddf3392ee40a8efddd938bfbd0eda31c284e2ea7b8b736a8d725acdada5
- ECJ 3.41.0 SHA-256: 47bda183cd94a8bdb704f5b35690224f75b7d2fb563c8b8f9bbcfab987c3029b

Java 21.0.12.1 is installed locally. No Freerouting JAR or DSN/SES file was found in the searched restored workspace, shared workspace, /opt or /tmp. Binaries are deliberately excluded from the published source packet.

Exact prior evidence:
- tests/shared-pad-alias21/REPRODUCE.md and located-path-inventory.json: one PORT_B_RX_EXT::P0 path located; final SES contained no new engine geometry. The successful native construction was explicitly not engine insertion.
- tests/located-portb-rx26/captured-engine.log, Git blob c204a526b33f5430523efdf5c081973cea654e60; located-receipt.json, blob 1d3d67b7c8bd9448112c87378d78ba5fd50e5987; proposal.json, blob dc9d173ac04cdf4b11769e88936ca5fa2602eecc. The review binds source26 PCB SHA 697555207280b8d67714a0011a51ec355321f21f551d6a1486a786c38a671949 and describes P2 insertion refusal at U14.4 against USER_FIXED P1.
- [tests/shared-pad-predicate-risk/REVIEW.md](https://github.com/chenguoming1/h743-controllers/blob/fabc7f2213d4e1a200396a3229d23b305ef90d3d/f722-heli/layout-revision/routing-tools/tests/shared-pad-predicate-risk/REVIEW.md): relaxing only two obstruction checks exposes a downstream cutout operation that can remove/reinsert a fixed foreign trace. Its synthetic control.json blob is 2e4151fa7590fe4f79e9a89e1b4aac1249a83cf7. This is an incomplete-patch hazard, not evidence that the retained stock rejection damaged a board.
- tests/INSERTION_GAP_CONTROL.md and compiled-planning-margin18-proof.json: the historical D2.1 fixture identified a locator/insertion safety-margin mismatch and verified an 18-unit planning allowance. It does not prove a whole-board route.

## What the format supports, and what still needs proof

1. Fixed copper: KiCad 10.0.6 exports locked tracks/vias as DSN type fix. The historical LocalRouter separately fingerprints SYSTEM_FIXED geometry. Fixed tags alone are not a substitute for native UUID/geometry retention checks. [KiCad exporter](https://github.com/KiCad/kicad-source-mirror/blob/10.0.6/pcbnew/specctra_import_export/specctra_export.cpp#L1486)
2. Layers and dimensions: retain six physical layers and exact 47.5 × 25.4 mm outline. Restrict signal routing to F.Cu, In2.Cu, In3.Cu and B.Cu; In1.Cu and In4.Cu remain GND planes. Freerouting supports class circuit use_layer; the existing LocalRouter already disables layers 1 and 4 in both classes and router settings. Through-vias still cross the planes and require their normal native clearance/refill checks. [Freerouting Network.java](https://github.com/freerouting/freerouting/blob/v2.1.0/src/main/java/app/freerouting/designforms/specctra/Network.java#L554)
3. Via-only guards: KiCad exports via_keepout; Freerouting ViaObstacleArea blocks vias without blocking traces. The historical prepare_model.py already creates face-specific guards around every actual SMT mask opening. With 0.225 mm via copper radius and 0.100 mm drill radius, mask expansion by 0.075 mm plus a zero-class via obstacle enforces a 0.300 mm center exclusion, hence the required 0.200 mm drill-to-mask gap. Keep its conservative polygon allowance and all drill/NPTH guards. Merely disabling via_at_smd does not prove the required clearance. Width/clearance remain 0.127 mm, new vias 0.45/0.20 mm. [ViaObstacleArea](https://github.com/freerouting/freerouting/blob/v2.1.0/src/main/java/app/freerouting/board/ViaObstacleArea.java#L38)
4. TVS ordering: Freerouting does parse DSN order/fromto into subnets. That establishes a possible representation, not the exact-native physical guarantee. Existing adapters distinguish logical connectivity from physical ownership at the same native pad. A stock export that merges aliases can bypass the actual clamp; naive duplicated terminals or virtual contacts can invent connectivity or trigger the known shared-pad rejection. Any future alternative must prove full-width actual-pad contact, both branches meeting only within the actual pad, and an actual IO cut that disconnects source from target. NC land contact alone is insufficient. [Freerouting ordered subnets](https://github.com/freerouting/freerouting/blob/v2.1.0/src/main/java/app/freerouting/designforms/specctra/Network.java#L1325)
5. DSN/SES availability: local pcbnew.py exposes ExportSpecctraDSN and ImportSpecctraSES at lines 9780–9796. Its verified SHA-256 is dedb7b3535b71aa381c7ced85cd9ec6a2043f11494351ef658301894e106f4db. APIs were inspected, not invoked.

## Import and acceptance boundary

KiCad's [10.0.6 FromSESSION implementation](https://github.com/KiCad/kicad-source-mirror/blob/10.0.6/pcbnew/specctra_import_export/specctra_import.cpp#L333) removes unlocked tracks/vias, preserves locked ones and can apply session placements. Its behavior is broader than the manual's simplified additive description. Do not use it as the exact-retention import gate. Keep the existing source-bound incremental importer, declare only selected new/replaced ordinary copper, enforce through-via size/tenting, reject signal tracks on either GND layer, and verify all untouched records.

Native acceptance must rerun applicable exact identity, net/parity, DRC, process, finite-contact, logical-partition, actual bonded-IO cut, critical/support connectivity and reference-plane checks against the resulting board. New vias may change saved GND fills after refill; preserve plane identities/outlines/rules, then assess real fill deltas rather than claiming byte-identical fills. Router completeness is not electrical qualification. Historical power/VCAP remains stale; no AC, ESD, timing, current-capacity, manufacturing or flight qualification follows from this assessment.

