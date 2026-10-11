# U15 RX channel reassignment: same-pose IO4 proposal

Use the unused IO4 (physical pin 5) for PORT_C_RX_EXT, with NC6 only as an upstream PCB routing land. Keep U15 at F(25.5, 17.6), 0 degrees; TX remains on actual IO2/NC9. This moves the real RX source 2.0 mm south without changing connector or MCU pin assignments. No new route or finite source escape is proved.

TI's [SLVSBO7O datasheet, revised August 2024](https://www.ti.com/lit/ds/symlink/tpd4e05u06.pdf?ts=1755070916604), section 7.2.1.2.1, identifies four equivalent protection channels. Table 4-2 distinguishes actual I/O pins from unbonded NC routing lands. Section 7.3 confirms there is no clamp bias supply. These support channel equivalence, not qualification of the proposed PCB geometry.

Native7 and the common proposal use actual IO1 at (25.0825, 16.6). The current C start (24.65, 16.1) comes from its two-segment downstream copper prefix; it is not an internally connected NC land. New IO4 is (25.0825, 18.6), UUID dddece5c-5254-4426-8e4c-1fb5f9e85655; NC6 is (25.9175, 18.6), UUID af34758d-03d4-4898-8fb1-2be5765ea280. Both source nets contain only their own unused pad.

The complete scope is four pad-net metadata changes, four old RX prefix removals and reconstruction of both J11.1-to-IO4 and IO4-to-R34.1 paths. Restore the original R3 signal leaves and retain the original C12/R3 supply topology. All previous common donor obligations remain. A paired schematic/symbol/netlist and versioned actual-IO/branch-role contract are required; the existing copper-only importer cannot apply this metadata change.

The held 0.25 mm ground return runs down x=24.5 and then to (25.287, 19.1104). It may trap IO4. Translating the old prefix to (24.65, 18.6) would violate clearance: the required center setback from that wall is 0.3155 mm. Derive access from the actual pad instead. The IO4-to-retained-R34-via straight-line lower bound is 4.481176 mm versus IO1's 5.748324 mm; neither is a routed length.

Acceptance requires actual full-width contacts and a physical IO4-pad cut proving no connector-to-series-resistor bypass. Preserve all TX, ground, SPI/B/C-source peers, then complete all C and donor functions and run paired native/DRC/ERC/parity, plane/reference and ESD-return checks. NC6 must never be treated as internally bonded.

The JSON includes complete UUIDs, exact source/file/record hashes, old mapping history and scope. Earlier IO3/IO4 plans are referenced in a restored historical metadata plan, but their full geometry receipts were not restored; this proposal makes no claim about their feasibility.
