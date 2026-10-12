# Native5 cleanup geometric checkpoint: WIP

This checkpoint preserves the adopted native5 routing geometry and its exact paired KiCad hardware. It is an unfinished engineering checkpoint. Five connections remain open, one of the 22 full actual-I/O protection cases remains incomplete, and the revised power/ground geometry has no current DC or transient/ESD qualification.

## Exact candidate

- Board SHA-256: `01b115302e079c6c7a2b1370ef4a089c19c7c2b54fd13e73cf2341db2dffc133`
- Native export SHA-256 after lossless decompression: `46d0b78c82003a3042e68ea2258fa40e5032499b3c3dc864594519c9178821ea`
- Original local recipe SHA-256: `0dfd4ea5db3699d0e1bc94254ddeb24d4ad1f0a3063fea49476f0aa3e17c50f3`
- Original physical audit SHA-256: `26ca9d2fc020c0b6bb8d0346441cec2a21c99e560304572752e54d91bfa256e7`
- Original reviewed partial-progress disposition SHA-256: `be2dfb278ef81590a2cb8b2abd86f47a1b82875ab9a294c7467eafcec9470bae`

`hardware/` contains the exact 61 paired source files, including the candidate PCB. All 60 other hardware files and all 558 pad identities and net assignments are unchanged. The adoption receipt is `evidence/geometric-checkpoint-review.json`. Earlier diagnostic receipts retain their original non-adoption status; they describe the state at the time each check ran.

## Routing change and measured result

U15 moves to the back of the board at `(27.721926, 21.185113)`, native orientation 0 degrees, using the physical top/bottom reflection. The earlier planning label “B180” is preserved as historical provenance; the explicit pad coordinates and native B0 pose are authoritative. Original RX/TX channel identities are retained. R34.1 reaches the actual RX I/O pad, TX uses its explicitly constructed NC bridge on the connector branch, CORE is reshaped, and U15 GND shares the existing C75 bulk-return barrel.

The cleanup removes the unused 18.027 mm TX arm, two barrels, and two overhanging stubs. It adds two exact 0.127 mm trim tracks while retaining all 94 previous recipe additions. Relative to the source7 board, the cumulative recipe has 64 removals, 87 added tracks, and nine added vias. The B-side trim uses the existing native junction, 0.5 nm from the rational midpoint; its actual fixed geometry has separate clearance and contact evidence.

Fresh native stages passed: refill/construction, netlist, ERC, DRC with schematic parity and all-track errors, and full paired verification. DRC reports five unconnected items, zero geometric error entries, zero schematic-parity entries, and three historical dangling MCU-via warnings. ERC reports zero violations. The five unfinished connections are PORT_C_RX_EXT from J11.1 to the clamp, PORT_C_TX_MCU, PORT_C_RX_MCU, FLASH_MOSI, and FLASH_SCK.

The independent physical audit found zero lost pad pairs against source7, native6, and the pre-cleanup native5 candidate. All 47 CORE pads, 133 GND pads, the four TX pads, changed real-pad contacts, new track endpoints and new via annuli pass the applicable connectivity/support checks. All previous successful actual-I/O cut cases are preserved: 21 of 22 full cases pass.

Full RX remains `INCOMPLETE_BEFORE_CUT`: J11.1 is isolated on F.Cu while R34.1, U15.1 and U15.10 are joined on B.Cu. The raw audit's aggregate is **false**, and its partial-RX gate remains **false**. A separate reviewed disposition passes only the allowed partial-progress criteria. It proves the completely inventoried cut partitions have no common conductive layer, explaining the empty same-layer gap list; it does not turn the full RX case into a pass. The full raw numerical/contact fields are retained in the path-normalized physical-audit derivative.

## Original mask failure and narrow representation fix

The first native assessment failed the strict reflected-mask polygon comparison. `representation/original-native-failure.json`, `comparison.json`, the saved moved-pad export, and the custom-copper diagnostic retain that failure and its evidence. The actual board geometry was not changed to repair the comparison.

The unchanged `representation_equivalence.py` and policy allow only the ten exact reflected U15 mask contours and the two custom GND outer contours to differ by a continuous symmetric boundary distance of at most 23 nm. This bound derives from two 10 nm KiCad polygon approximations plus integer-grid rounding. Exact inverse analytic primitives, all 558 pad settings, inside contours, UUIDs, nets, layers, sizes, centers, angles, vertex counts, single-component topology and zero-hole topology are still required. It is a representation comparison bound, never a physical clearance allowance. KiCad implementation citations are in the policy.

## Reproduction and verification

Run these commands from this checkpoint directory in the repository checkout:

```sh
python3 -B runtime/verify_saved.py
python3 -B runtime/check_controls.py
```

The saved replay verifies lossless compressed originals, the exact source-to-candidate recipe, 2,306 retained native records, all 558 pad identities/nets, all 96 additions, full schematic parity, native report counts, and the narrow 12-contour representation proof. Controls retain the original mask failure and reject over-bound/topology changes, altered added UUID/net/width, invalid partial-RX claims, and unsupported trim endpoints/fragments. These commands perform no native refill, routing search, or new physical audit. They need Python 3; the saved replay caps address space at 1.5 GiB and CPU time at 60 seconds.

`INPUT-REFERENCES.json` pins the unchanged source-board Git blob in the earlier joint-native7 checkpoint. It also pins the prior native6 gzip export as a historical comparison input. Those bytes are reused from the repository. Pass `--repository-root /path/to/checkout` if running the verification from a detached copy. Unique source and candidate native exports and candidate inside-contour evidence use deterministic gzip. `COMPRESSION-MANIFEST.json` records decompressed byte counts and SHA-256 values; exact originals reconstruct without loss.

For an optional fresh native rebuild in a new directory, use the official KiCad `10.0.6+dfsg-1` Python environment:

```sh
python3 -B runtime/replay_native.py --output /tmp/f722-native5-replay
```

The construction wrapper contains the exact ordered native mutation loop from the checked adapter, with portable arguments replacing execution-specific plumbing. It checks geometry, UUIDs and net identities against the saved candidate after refill. Packaging verified the saved geometry and function provenance; this portable native wrapper was syntax-checked but **not re-executed**. Byte-identical regeneration is not promised. Run fresh KiCad netlist, ERC, full DRC and schematic-parity checks before using any regenerated board. The raw hardware and compressed saved exports are the byte-exact checkpoint artifacts.

`SOURCE-PROVENANCE.json` distinguishes original source hashes, exact-byte files, path-normalized publication derivatives, and exact technical function extracts. A normalized recipe/report is not the original raw artifact: its publication SHA differs. Normalization changes path strings and omits execution-only metadata; numerical geometry and engineering results remain unchanged. `CONTENT-MANIFEST.json` binds the published file set; the external publication manifest also binds the immutable payload and complete additive Git tree.

## Qualification still open

The earlier native6 conditional DC result is historical: changed CORE/GND routing, drilling and fill make it stale for this candidate. C75 is the 47 µF +5V_PERIPH bulk capacitor, and its shared GND land/barrel can couple a TVS pulse into the peripheral supply return. Connectivity and DC conductance do not establish transient/ESD equivalence. No qualified dedicated-return replacement is demonstrated by the saved alternatives.

Current/thermal qualification, complete timing and reference-return review, the unresolved stock-I2C guarantee gap, manufacturing/assembly review, and flight qualification remain open. This checkpoint provides no manufacturing or flight-ready claim.
