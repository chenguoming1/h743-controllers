# Native7 C-interface structural plan

This plan starts from the recovered native7 board, not a missing composite overlay. The native JSON is bound by SHA256 `53ddf869c36da4a026880c6b3346dd1ddb304aaabaa948b20f1e66fc3db62505`. The recovered selected transaction is SHA256 `b7ca08e59b4316c8a88c0ff9d3c0fe3cffac4d0f0ad2b407028cd1ef3050f497`. Its 100 recipes have 233 deterministic native copper members. Full native records, actual pad contours, widths, via drill/tenting and split-segment provenance are authoritative.

The contact inventory is `native7-C-removal-restoration-inventory-v3.json`, produced by the adjacent read-only builder. It is a structural inventory, not a DRC or routing result. Positive-area contacts and endpoint cross-sections are recorded separately from whole-net physical connected components. Actual bonded-pad subtraction splits every surviving copper polygon; no net-label or package-internal edge is added.

## Open functions and complete donors

Four C functions remain open in native7: U1.28→R34.2, U1.29→R35.2, protected RX upstream→J11.1, and protected RX downstream→R34.1. Existing MCU source escapes, RX prefixes and R34 pad/via stubs are partial boundaries of these open functions. They must not be called complete end-to-end donors.

The native TX downstream function and TX upstream header function are complete. Removing any portion creates a full restoration obligation. The private R57.1–C72.1 VX leaf is also complete and must retain its .25 mm width, actual supply/decoupler contacts and every original same-net boundary contact.

The initial C-specific replacement scope for the proposed coordinated construction is:
1. Both old MCU source-entry groups: four native track segments and two native vias. Reconstruct actual U1.28/U1.29 source escapes with distinct .45/.20 tented vias and full .127 mm pad-entry witnesses. The proposed two-source recipe is conditional and must pass freshly against this exact native7 shared context.
2. Complete TX-down tail: eleven native track segments and two native vias across F/In2/B. Hold the one-segment bonded IO2 prefix initially. Restore actual U15.2→R35.1, not merely the old polyline endpoints.
3. Private VX leaf: five native F segments, width .25 mm, from actual R57.1 to C72.1. Preserve all original attached VX contacts. Fresh power qualification is required after any new route.
4. TX-up header tail: six native F segments, width .127 mm, between retained NC9/bonded-pad prefix and actual J11.2. Preserve the physical IO2 cut.

These are 30 native copper objects, before shared flash/B donor scope. The optional complete IO2-entry fallback adds the one `rotated-TX-down` native segment, bringing this C-specific scope to 31. It starts at the actual original finite pad-entry point [24.9,17.1] inside U15.2 and must reprove full-width contact and the no-bypass cut. The foreign U15 bonded pad and CORE via are never removed as a shortcut.

R34 and R35 retain their exact native7 poses/packages/pad identities in this first construction. RX downstream source prefix and R34 target stubs stay present; the missing route between them is constructed. A resistor move requires a separately bound actual-native pose and fresh mechanical/pad/mask checks.

## Bounded shared construction

Use the fresh adapter `ordinary-routing/tests/native13-access/native7_recovered_context_v3.py`, which retains native records unchanged and exposes native UUID-to-recipe/segment provenance. Treat protected branch role as separate metadata. For an active branch, only its actual bonded pad may receive that branch alias; the other channel's bonded pad remains foreign. Never carry the old recipe names as if they were native UUIDs.

First reconstruct or replay the common flash/B source and target access context against native7, preserving native source identities. The old v25 MISO-relief packet is a recovery hypothesis until its complete recipe/removal inventory has been rebound and checked. Its MISO MID barrel cannot be shared by another signal.

In a single bounded run, assess the RX-down graph with MID held and, only as an attribution control, with its barrel omitted. Restore and hold complete MISO geometry before constructing anything. Then release the exact full private VX/TX-up donor scope and complete TX-down tail, and inspect all actual C and donor endpoint graphs.

Construct real protected source and target accesses before long trunks. In particular, construct the full MCU-side R35 B entry before choosing the TX-down target barrel, so the second legal domain includes the first real path. Reserve both MCU targets, the independent protected RX branches and complete supply/header donor contacts before filling long corridors. Recheck all full graphs after these accesses coexist; a disconnected individual route is not a global impossibility claim.

If RX-down still fails at the initial gate, test the explicit full bonded IO2-entry reconstruction as a separately recorded fallback. Do not sweep target orders or move R35 before resolving the common current context and the actual constrained exit.

A successful conditional C packet must export every full track centerline and via, exact removed native records, original donor boundary contacts, actual pad-contact proofs, physical component proofs, both U15 actual-pad-cut/no-bypass checks, fresh finite width/clearance/drill/mask checks, and unchanged-peer identity checks. Full flash/B/local donor restoration is still required before selecting a board transaction. Native import/refill, unsuppressed DRC, parity/ERC, mechanical/ESD/ground, and fresh power/VCAP checks follow before adoption.

No routing or adoption has been performed. Fresh native construction, refill, DRC, electrical, mechanical, protection and power checks remain required.

Validated inventory v3 SHA256: `fcaaeeb6a8ae27ec3885ccb07ae760bf59ae92a558147ceaa46d99acde793fe7`. The inventory confirms one complete TX external component and one complete VX supply component; RX external has three components, RX MCU two, TX MCU two.

The generator verifies the exact native7, source11 native-export and selected-transaction hashes before reading geometry. It rejects invalid or empty native polygons and invalid copper unions without repair or tolerance changes.
