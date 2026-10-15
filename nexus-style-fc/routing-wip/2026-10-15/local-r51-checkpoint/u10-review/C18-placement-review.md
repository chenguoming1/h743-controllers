# C18 local relocation review

Status: **No complete, defensible minimum C18 relocation is established.** No footprint, PCB, schematic, repository, or native trial was changed. The strongest concrete near-feasible pose below is a placement/routing review target, not an implementation recommendation or a proof that the entire local region is unroutable.

## Engineering significance

This is an optional layout-improvement review, not a mandatory input-capacitor stability repair. The parallel input-capacitor qualification review reports that TPS709 Rev H §8.1.1 does not require input capacitance for stability, recommends 0.1–2.2 µF for the applicable source/transient conditions, and requires input capacitance when line transients exceeding 10 V are anticipated. The 1.5 µF effective minimum is output-only. A material C18 relocation is not justified by a reference-coverage percentage alone. Do not change C18 value or claim that retaining its present placement is unstable on the evidence in this report.

## Source and method

- Frozen source: `routing-continuation/r46-sconf/hardware/nexus-style-fc.kicad_pcb`, SHA256 `0c70e5be9f0e4a3dfe4c5d074dc11980b66c4bc779b3ec39bc7705b61b55540c`.
- Reconciled latest r47 PCB SHA256 `a1703af533e47f20ddc9830683b8239253c0d60be26b6eaeeb5c904fbb731cf9`: the sole primitive changes are two removed/two new SENS tracks at x110.9–112.255, y113.8175–114.036642, outside every reported pose/access check. Pads, courtyards and all cited local copper are unchanged.
- Read-only S-expression parser and analytic convex-base-plus-radius geometry for actual pads (including rounded/oval pads), tracks, and through vias on every copper layer. No KiCad imports, DRC, fill, or routing solver. Courtyard measurements use source outline coordinates, not rendered line thickness. Native courtyard and filled-zone semantics remain untested.
- Required supply contact/track width 0.250 mm; comparison clearance 0.127 mm. Source through vias are diameter 0.450 mm, drill 0.200 mm. Do not shrink these to make the proposal work.

## Existing circuit and complete local geometry

- U10: TPS70933DBVR, F.Cu, center (109.400,107.050), rotation0°. VIN pad1=(108.450,108.200), size0.490×1.157; GND pad2=(109.400,108.200), same size; EN pad3=(110.350,108.200), same size, intentionally floating; NC pad4=(110.350,105.900), size0.490×1.175; VOUT pad5=(108.450,105.900), same size. Rectangular pads. U10 courtyard x107.744–111.056, y105.163–108.928.
- C18: 1uF, LCSC C52923, existing `Capacitor_SMD:C_0402_1005Metric`, B.Cu center(105.930,116.940),180°. VSYS pad1=(106.410,116.940), GND pad2=(105.450,116.940); both0.560×0.620 roundrect, r=0.140. Courtyard1.820×0.920, nominal body1.000×0.500. Same part and footprint must remain.
- C19: approved10uF/C19702, F.Cu center(109.400,109.800),0°. SENS pad1=(108.625,109.800), GND pad2=(110.175,109.800); both0.900×0.950 roundrect,r=0.225. Courtyard x107.920–110.880,y109.070–110.530.
- C19 GND→U10 GND existing F chain: (110.175,109.800)→(109.400,109.025)→(109.400,108.200),0.127mm width; length1.921016mm. Preserve this unless a separately approved complete ground replacement is proved.

## Strongest near-feasible F.Cu pose

**C18 at (108.700,111.950),0°, F.Cu**. Translation(+2.770,−4.990)mm; displacement 5.707276 mm, rotation change180°, and an explicit side change B→F.

- New VSYS pad1=(108.220,111.950), GND pad2=(109.180,111.950).
- Courtyard x107.790–109.610,y111.490–112.410. Clear source courtyard outlines:0.030mm horizontally from C2,0.042mm from U2,0.100mm vertically from C30; no other courtyard overlap. These are small nominal margins, not native assembly-clearance acceptance. Nominal body x108.200–109.200,y111.700–112.200 stays inside this clear courtyard.
- Full pad copper is clear of all foreign source pad/track/via primitives. VSYS pad nearest foreign primitive is the3V3 F track at x107.475, gap0.340mm. GND pad nearest foreign primitive is S3 via472457fd-f820-4965-8a7d-fa28f38f48af, gap0.287156mm. 180° at the same center is invalid: its VSYS pad overlaps the existing GND branch.
- The new GND pad overlaps existing GND track77d81050-58a6-470d-b9ba-535a5df0f5fd on F.Cu. A proposed0.250mm F connection (109.180,111.950)→(109.555702,111.852500), length0.388147mm, has an analytic nearest foreign primitive gap0.129589mm to U2.1. This can enter the capacitor through a finite0.250mm-wide patch, and terminates at an exact existing GND junction. Existing downstream ground is0.127mm wide, so this is not a claim of a uniformly0.250mm ground loop.
- That junction has an existing all-F path through C19 GND to U10 GND. Including the proposed short connection, its centerline length is4.614363mm. This establishes a possible direct copper path only; refill and return-plane quality are unproved.
- A0.250mm F supply stub from the new pad to(108.220,111.250), length0.700mm, is primitive-clear by at least0.250mm. A finite full-width contact rectangle x108.095–108.345,y111.840–111.860 is wholly within the actual rounded pad. The problem is continuing this stub to VIN.

### Exact input access blockers

1. The direct F continuation north crosses the existing3V3 feed around y110.53–110.56 and the C19 SENS pad/output copper. A full0.250mm supply cannot use those crossings.
2. A rightward F continuation (108.220,111.250)→(108.950,111.250) physically overlaps S3 via472457fd-f820-4965-8a7d-fa28f38f48af at(109.035677,111.127858), signed separation−0.200805mm.
3. A0.450/0.200 through-via at(108.950,111.250) is blocked by:
   - S3 via472457fd...: signed gap−0.300805mm, all copper layers.
   - S3 B tracka1ce87f2-4801-46d7-b970-188c4a605533:−0.260793mm.
   - S3 In2 track5a9a6268-d11a-4ffb-9c05-f67311ca9b71:−0.139305mm.
   - DSM_DATA In2 track4a8edaa1-b102-4207-82c7-622d6c351f52:−0.017626mm.
   - Fixed U1.26 B pad:0.099342mm, below0.127mm.
4. Lowering that via to(108.925,111.400) still overlaps S3/DSM_DATA, is only0.094707mm from U1.25 and0.111500mm from RPM In3 track5e6e604b-0714-495f-b34b-8bf4f96f8668. At y111.500 it remains blocked.
5. An attractive VIN-side through-via at(108.720,108.930), which is plausible looking only at F.Cu, overlaps S3 on In2, RPM on In3 and U1.30 VCAP pad on B.Cu. Its B pad gap is−0.096971mm. Moving this idea around is constrained by the U10 GND/C19 SENS pads on F and the U1 pad bank below.

Consequently, **no complete supply route, input decoupling length, input reference fraction, or complete donor replacement is claimed**. The shortest old source route cannot be substituted as a new local capacitor connection without resolving these gates.

## B.Cu-only near-feasible pose and its additional scope

C18 at(106.505,109.250),90°, B.Cu preserves side. Translation(+0.575,−7.690)mm; pad1 VSYS=(106.505,109.730),pad2 GND=(106.505,108.770). Courtyard x106.045–106.965,y108.340–110.160 is outline-clear, with0.035mm on each side between C22 and U1 and0.060mm from C21 vertically. The local strip is only0.990mm wide; horizontal orientation cannot fit.

It is **not a viable copper placement**:
- VSYS pad directly overlaps three VCAP B tracks1929dd2b-41d4-470b-a3c1-56e2c78626f5,882275c2-61a8-4699-b829-25da97888c64,d5726c15-4f21-480b-b418-65eca507c42f, signed gaps−0.203500mm.
- It overlaps C_TX via b77e0099-6bbe-478d-a93f-12359cf93594 at(106.528775,110.048135), signed gap−0.186865mm, and C_TX track0df15676-7cd0-4c5c-80c6-59a47d9df36f,−0.170990mm.
- It is only0.034071mm from GND via bc9956b2-9ed7-485a-94c7-3435bb0747bc. Reversing to270° puts VSYS into existing GND copper and does not fix the second-pad collisions.
- Other checked vertical centers109.400,109.600,110.350 and111.400 in the narrow strip remain blocked by VCAP/C_TX/C_RX/GND source copper. This is a bounded set of checks, not a global search or proof of impossibility.

The minimum *identified* additional scope for this B-side pose includes complete VCAP and C_TX routing/via donors plus local GND clearance and a complete VIN/ground connection. It is not a complete donor list or an authorized reroute. Moving only C18 does not work here.

## Why the obvious closer poses do not fit

- U10→C19 courtyard gap:0.142mm, versus C18 minimum dimension0.920mm.
- U11→U10 side gap:0.794mm, also too narrow for either cardinal courtyard orientation.
- J2 to U10 gap near the southwest:1.074mm cannot take horizontal C18(1.820mm); the vertical alternative is bounded by U11 at y108.300 and C2 at y109.620, leaving1.320mm for a1.820mm vertical courtyard.
- B.Cu C21→U1 gap:0.720mm, too narrow; the wider0.990mm C22/U1 strip is the blocked B pose above.
- F east pose(112.000,108.750),0°/180° is courtyard-clear, but overlaps VCAP tracks and B_TX via; USB_DM via ab6d1608-078d-4769-81fd-9767b0773ad9 is only0.003347mm from the left pad. The gap east of U10 before U3 is just0.944mm, leaving0.024mm total excess over a vertical C18 courtyard; retained SENS and SPI copper obstruct the useful pads/access.

## Required complete transaction if a move is eventually accepted

This is a scope checklist, **not an application-ready transaction**:

1. Move only C18, preserving1uF/C52923, footprint, UUID, pad nets and schematic. Side change requires explicit approval if the F pose is selected. All other component placements, U10 EN isolation and approved C19 metadata remain unchanged.
2. Remove or deliberately retain the old VSYS capacitor branch as a whole. It consists of abb6d92c-fe4d-4098-9639-a5176a79b8cf,7050ad6f-9636-4133-ba0b-11f6e38331d3,4d573730-8312-45a6-a98e-3d8cfed2019b, total3.592678mm. Both first two touch the old capacitor pad physically. The only external primitive ports of these three tracks, excluding the moving capacitor, are the retained VSYS via e0ea22eb-7130-400d-9532-cf8cdccb26c6 and source segment d1e36549-994b-4a5e-9a3d-f6fadebe507f at that upstream junction. Do not remove the shared upstream feed.
3. The old GND pad physically contacts44e11688-db0b-4bb2-805a-4201f99ccc67,c5059616-fea5-4f49-a870-3fd11019846e,d6d6d5bc-bae3-404e-b044-e534b34cb162. These three tracks also meet at(105.450,116.940), so retaining them preserves their mutual copper connection after moving the pad. Do not cut them as if they were three isolated capacitor stubs.
4. Define and verify a complete0.250mm new supply feed and C18→VIN path, finite pad/via contacts, any new through-via on **all six layers**, and a direct ground path. Any S3/DSM_DATA/RPM/VCAP/C_TX/etc donor change needs a complete endpoint/midspan/area-port replacement; a single moved via without all incident copper is insufficient.
5. Restore the complete all-F output donor transaction only in the same accepted candidate: remove the four old output segments and two output vias, preserve all external branches at U10/C19, and route (108.450,105.900)→(108.450,106.500)→(107.895,107.055)→(107.895,108.950)→(108.625,109.800),0.250mm. The conflicting old local VIN path must be replaced completely, not retained under the new output.
6. Refill, native DRC/opens/parity/ERC, full-width port proofs, source invariants, courtyard/body checks, drill-versus-paste checks, and new full-width input/output return topology are acceptance gates. No current-report number is a substitute for those checks.

## Input/output/ground comparison

- Existing C18→VIN inherited serial track sum25.543149mm; this includes the remote capacitor branch and longIn3 feed. Existing local input trace sum2.664301mm. Existing output trace sum4.488414mm with2.231731mm on In3 and two through-via transitions; intended barrel contribution1.750200mm.
- r44 excluded experiment: all-F output4.400335mm, zero intended output barrel, and100% full-width projection over the same In1 GND component. Input grows to25.932474mm and adds1.413400mm modeled barrel; its reported old F/In1 coverage84.19% regresses to58.43%B/In4 and65.97%F/In1. r44 is not accepted and must not be copied as the solution.
- Proposed C18 lower-F pose: actual capacitor pads/courtyard and a finite-width input escape/ground contact are measurable, but complete input route and post-fill reference are **unknown**. The potential direct C18→U10 ground centerline path is4.614363mm, with inherited0.127mm portions. This does not prove improved total decoupling impedance or regulator stability.

## Decision and potential future scope

**No relocation or approval request is recommended from this review.** No complete supply/return route is proved. Keep C18 in place while comparing the measured output benefit and input transient/return tradeoff of the separate r44 experiment under the corrected TPS709 input requirements. This review does not approve r44 either.

If the user independently asks for a placement redesign later, the concrete lower-F review target would require permission for C18’s B→F side change, translation to (108.700,111.950), rotation to 0°, and a complete local VSYS/GND/output reroute on an isolated candidate. All other component placements, the floating U10 EN, and C19’s approved part must remain fixed. The known S3/DSM_DATA/RPM access conflicts would require complete donor proposals and explicit scope before any such signal reroute. No complete donor replacement currently exists, so this is an inventory of possible scope, not a recommendation to authorize work.

The B-side target similarly requires at least VCAP/C_TX routing changes and local GND clearance before supply/return feasibility can be established. A broader redesign, a claim that a minimum move has been found, or automatic r44 adoption is not justified.
