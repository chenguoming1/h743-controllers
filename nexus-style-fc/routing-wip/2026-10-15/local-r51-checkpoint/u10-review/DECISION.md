# U10 routing decision: replay the all-front output alternative

15 October 2026. This is an engineering recommendation for a fresh, isolated routing trial. It does not adopt the old experiment or qualify the circuit.

## Recommendation

Replay the r44 output-loop improvement against the latest sealed routed board, retaining the approved C19 and EN changes. Keep all existing components, placements, nets, supply widths and pad contacts. If fresh source-bound native and physical checks pass without a known requirement violation, prefer this output connection to the current inner-layer output detour. Document input-transient/PSRR and complete regulator qualification as pending.

The decision is based on the device's different input and output requirements. It is not based on a universal reference-coverage percentage threshold. No component substitution or C18 relocation is recommended by this review.

## Applicable requirements and component evidence

TI's non-Q1 TPS709 datasheet, SBVS186H, section 8.1.1 (printed page 14), requires effective output capacitance of 1.5–47 µF for the 3.3 V output and appropriate ESR. Input capacitance is not required for stability; TI recommends 0.1–2.2 µF for reactive sources, transient/ripple and PSRR performance. An input capacitor becomes necessary when line transients exceeding 10 V in magnitude are anticipated. This is a transient-amplitude condition, not a 10 V DC input ceiling. The nominal 7.4 V BEC does not establish its actual waveform or peaks. Section 10.1 (printed page 16) calls for close input/output capacitor placement and a direct output-capacitor ground connection. [TI datasheet](https://www.ti.com/lit/ds/symlink/tps709.pdf)

Approved C19 is Samsung CL10A106KP8NNNC / C19702, 10 µF, 10 V, X5R on the unchanged 0603 footprint. Exact typical manufacturer data imply about 4.429 µF at 3.3 V; separate tolerance/temperature screening gives about 3.388 µF. These are not guaranteed simultaneous-corner minima or proof of system stability. [Samsung C19](https://product.samsungsem.com/mlcc/CL10A106KP8NNN.do)

Existing C18 is Samsung CL05A105KA5NQNC / C52923, 1 µF, 25 V, X5R, 0402. Exact typical manufacturer data imply about 0.2501 µF at 7.4 V; separate tolerance/temperature screening gives about 0.1913 µF. No input-stability violation is demonstrated, and no input-part substitution is justified solely by this result. Neither the nominal recommendation nor these ratios constitute stability margins. [Samsung C18](https://product.samsungsem.com/mlcc/CL05A105KA5NQN.do)

## What the old r44 experiment actually demonstrated

Original source PCB: `a79fe4a4d8a13460ab9648489fc5f2aa8d23740fd6f3d5f15f1a9933ede6bfb7`.
Conditional r44 PCB: `5207868d2a02322cd8b992ea8859c320b751aedd4ccc096d6916fed527a9c548`.
Its historical native receipt used schematic `742252dba39bef886fefb10381fb6cb111bc63bf584c68309753b2e89fa7da18`; it predates the final C19 metadata revision. These receipts cannot certify a replay on the current board.

- The complete 0.250 mm output leg becomes about 4.400 mm entirely on F.Cu, eliminating two output vias. All eight external ports were proved full-width in the old transaction.
- Its actual saved post-refill output copper projection was entirely over one In1 GND component, including the report's separate 0.0635 mm erosion check. Direct C19 ground and retained C18 contacts were preserved.
- The input route adds 0.389325 mm of planar travel and 1.4134 mm of modeled barrel travel. Full-width adjacent-reference projection changes from 84.19% on the prior F.Cu leg to 58.43% on the new B.Cu leg and 65.97% on the new F.Cu leg. These are measured geometric differences, not impedance measurements or a published pass/fail criterion.
- The input capacitor is already remote: the recorded complete serial path changes from about 25.543 to 25.932 mm before the modeled barrel addition. It is not equivalent to local decoupling. The actual input-source impedance, ringing, transient current and PSRR effect remain unmeasured.
- Native DRC remained at 29 clearance errors, with no new/worsened pair, zero opens/parity and 54 unchanged silk warnings. The added via's closest new measured gap was approximately 0.128247 mm. Those are historical results, not a fresh acceptance claim.

Improving the output connection has a concrete geometrical benefit in a circuit whose output capacitance and connection are stability-relevant. The additional input travel and changed reference geometry are real tradeoffs, but the available evidence does not establish that they violate a TPS709 requirement. The net electrical effect remains an engineering inference until tested.

## Fresh replay acceptance

1. Start from the latest sealed candidate, not the historical r44 file. Verify exact donor geometry and retain every later repair, approved C19 field and floating EN net.
2. Prove all eight external ports, original full-width supply entries, retained direct contacts, pad/placement/net invariants, ordinary via drill/annulus/tenting, paste avoidance and EN isolation.
3. Use native KiCad 10 to refill/save, run all-track/all-severity DRC and schematic parity, and bind the result to exact saved bytes. Carry ERC only for an exact unchanged schematic; otherwise rerun it. Accept no new or worsened residual violation and no new suppression.
4. Recompute actual post-refill finite ground contacts, output coverage/component continuity and input comparison. Original zone definitions or zero opens alone do not prove equivalent returns.
5. Keep startup, BEC/load-step response, input overshoot/ringing, sensor-rail disturbance, temperature and component-corner qualification open. This routing decision does not authorize manufacturing, assert current capacity, or establish flight readiness.

## C18 placement and metadata observations

A separate bounded read-only placement review found no complete viable one-part C18 move. Its best front-side pose had clear pads/courtyards but no proved full-width VSYS connection; a rear-side pose overlapped existing signal copper. There is no defensible relocation approval request from that review.

The authoritative U10 Value/LCSC fields and both BOMs select TPS70933DBVR/C89347. A separate inherited donor-footprint field, `LCSC Part=C82942`, and library description `ME6211C33M5G-N` are stale. Existing exports use the correct schematic/design LCSC value, not that donor field. No different component was selected. This metadata ambiguity should be cleaned up separately without altering pads, placement, nets or the actual selected part.
