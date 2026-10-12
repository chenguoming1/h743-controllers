# Native4 cleanup checkpoint: adopted geometric WIP

This checkpoint closes FLASH_SCK between U1.34 and U3.6 and preserves the adopted cleaned native4 hardware. It remains unfinished: four connections are open, full RX protection is incomplete, and current power, reference/SI, ESD and assembly qualification are pending. The separately investigated return-stitch and trim candidates are not included.

## Exact hardware and status

- Board SHA-256: `293631bc83f880a11bf5d5da2cd2d21cc3e1ecb12e8e95731ef2547a10bcc862`
- Native export after lossless decompression: `c98fd2e2f8c66b43c38897fecfc1263f855df0bcf8598f31b3a74a10a142f762`
- Original recipe SHA-256: `acc15655b6e25dfb7c90f3c3cab55349d3b27ffc352cd557ea8f2e8d833e7270`
- Original adoption receipt SHA-256: `9f8fc25321170a8228f65e6212c7b09b17fe3cfd2f1993161bf07e8a766e705d`

`hardware/` is the exact paired set of 61 KiCad hardware files. All 60 non-board files and all 558 pad identities and net assignments remain unchanged. Fresh construction/refill, netlist, ERC, full DRC with schematic parity and paired verification completed successfully. Native DRC reports four opens, zero geometric errors, zero parity issues and three historical MCU dangling-via warnings; ERC has zero violations.

The remaining connections are PORT_C_RX_EXT from J11.1 to its clamp, PORT_C_TX_MCU, PORT_C_RX_MCU and FLASH_MOSI. The SCK route is 49.649936 mm long and adds five signal vias.

Relative to native5, the exact transaction removes five records and adds 32 tracks, six vias and one 586-vertex VX copper polygon. All 2,411 retained native5 records and all native5 footprints remain exact, allowing only proven bijective integer net-code serialization differences. The cumulative source7 recipe contains 69 removals, 119 tracks, 15 vias and one polygon.

The cleanup changes the native removal policy on exactly two GND zones, removing only two isolated fill components. All 2,450 pre-cleanup objects, all footprints, both main-plane contours and GND pad partitions remain unchanged. The original native assessment repeated ordinary reopen/refill and reproduced the cleaned board exactly. The prior raw4 native export can be reconstructed losslessly from the candidate and the 5.5 KB reverse patch in `inputs/`; its exact SHA-256 is `beeb3c05b077e96465f0f553e301d0e3012cd4c08dbc3ed729aac4182ebeec2a`.

## Physical audit and narrow disposition

The independent audit reports zero lost pad pairs against native5, native6 and source7, complete CORE47/VX13/GND133 groups, preserved surviving fragments and pad-anchored new fragments. Twenty-one of 22 full actual-I/O cut cases pass. Full RX remains `INCOMPLETE_BEFORE_CUT`, with J11.1 isolated on F.Cu and the completed clamp/R34 component on B.Cu.

The raw physical aggregate is **false**. Its original partial-RX, RED retained-lead pairwise, VX terminal and CORE endpoint-support false predicates remain unchanged in `evidence/raw-physical-audit.json.gz`. The separate local review uses the exact same-net unions, full-width outer annular entries and source-preserved plated-barrel contacts. It satisfies only these source-bound attachment requirements, including the drilled VX terminal; it does not replace the original predicates or provide a general waiver. The partial-RX disposition likewise never turns incomplete full RX into a pass.

Twelve saved-contact controls and six actual-native-shape controls passed in the original review. The package replays the twelve saved-contact predicates and mutations without new geometry work; the original six shape-control results are preserved separately. Original raw audit SHA-256: `3597f3fbc390da57255a2ab7a45132bed5ddcf7360af5dec3cdea679c1f465f8`. Original contact disposition: `b46c7c3ea28e99587cd763aa22be79525fe715b776c8ac44eab318fe6f34515d`.

## Verification and reproduction

From this checkpoint directory in the repository checkout:

```sh
python3 -B runtime/verify_saved.py
python3 -B runtime/check_controls.py
```

The saved replay verifies exact compressed bytes, source7/native5 recipe deltas, native UUID/net/geometry identities, the raw polygon AST, the 12 narrowly bounded U15 representation contours, exact raw4 reconstruction and island removal, full schematic parity, native report counts and the separate contact disposition. It imports neither KiCad nor Shapely and performs no new routing or physical solve. Use `--repository-root /path/to/checkout` when the unchanged source7 board cannot be located in an ancestor checkout. Its Git blob is pinned in `INPUT-REFERENCES.json`.

Unique native exports and verification boards use lossless xz; reusable source inputs use their prior gzip bytes. `COMPRESSION-MANIFEST.json` binds exact decompressed sizes and hashes. The paired hardware can be opened directly in KiCad. The source7 and native5 evidence already exists in the preceding checkpoint and is reused byte-for-byte.

An optional portable rebuild is provided for the official KiCad `10.0.6+dfsg-1` Python environment:

```sh
python3 -B runtime/replay_native.py --output /tmp/f722-native4-replay
```

It applies the exact native mutation sequence, polygon and two-zone policy, refills, and compares the resulting geometry/UUIDs/net identities against the saved candidate. The portable wrapper was syntax-checked but **not re-executed during packaging**. The original native v3 assessment did run successfully. Byte-identical regeneration in a different runtime is not promised; any regenerated board requires fresh ERC, DRC and parity checks.

`SOURCE-PROVENANCE.json` separates original local hashes, exact bytes, reused frozen bytes and publication derivatives. Path-normalized reports and recipes retain numerical geometry/results but are not the original raw artifacts. Technical function extracts preserve the original mathematical checks; portable file lookup and decompression are identified separately. Earlier diagnostic records retain their original non-adoption flags; the later adoption receipt establishes geometric WIP status.

## Qualification still pending

The earlier native6 DC result is stale for the changed VX polygon, CORE paths, GND fills and U15 return. Narrowed-polygon current distribution requires a fresh source-bound solve. All 3.539623 mm of adjacent-GND-unsupported SCK centerline lies at its own via-antipad approaches; four reference transitions require return/SI review, with the weakest nearby ground barrel 3.798 mm away.

The tented RED via has increased nominal J11 body/drill projection overlap while remaining under U3. No paste overlap and passing drill/mask/courtyard findings do not establish assembly clearance. Shared C75 bulk-return ESD/transient behavior remains unqualified. The stock-I2C timing and 3.3 V sink-guarantee gap is unresolved. Manufacturing, thermal, flight and completed-board qualification are not established.
