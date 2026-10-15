# Nexus C27/C31 cap-star: independent input-loop review

15 October 2026. Read-only review of the sealed proposal, not the unfinished r62 native board.

## Decision

**Proceed with the approved r62 native experiment. Do not describe it as production-qualified or as a demonstrated low-inductance input loop.** The proposal makes a real, reproducible improvement to the C27 positive path and corrects the EN branch topology. Available evidence does not identify an unambiguous missing datasheet feature that mandates another part or EN circuit change. In particular, the nonzero feed length alone is not such a feature; there is no universal route-length limit. No extra part is authorized. Native return-path verification and hardware qualification remain necessary.

Approved scope is the exact Samsung CL21A226MAYNNNE/C602037 pair at C27/C31 and D5 moved 0.400 mm south with unchanged part and nets. Older approval-status prose in the capacitor study predates the separately approved D5 move. No board, schematic, BOM, or external service was changed by this review.

## Actual TI requirements

[TPS629210 non-Q1 Rev B](https://www.ti.com/lit/ds/symlink/tps629210.pdf), §7.3, specifies at least **3 µF effective input capacitance**. The 4.7 µF nominal recommendation in §9.2.2.3.3.2 is not a waiver of that effective minimum; larger low-ESR ceramic input capacitance is permitted. §11.1 calls for the capacitor near VIN/GND, short wide switched-current paths, low loop inductance/resistance and small alternating-current loop area. VIN-tied EN must connect at the input capacitor. VIN recommended operation is 3–17 V; 18 V is an absolute maximum, not an operating target. There is no numerical maximum trace length, via prohibition, or plane-projection percentage pass criterion in these sections.

[TI's switching-loop explanation](https://www.ti.com/document-viewer/lit/html/SSZTBF4/GUID-095BD04D-6DAF-42E7-9AA0-72CB14E1F58C) identifies the buck's input-capacitor/switch loop as the discontinuous-current loop. A continuous ground plane and a low-inductance current loop matter; trace resistance alone cannot establish this.

## What improves, and what does not follow

- C27 → U14 VIN: **12.270839 → 9.401063 mm** declared axis length. Independently summed the new 1.054751 mm B.Cu lead, 7.756524 mm F.Cu route and 0.589788 mm B.Cu lead. The new route is 0.250 mm wide on 0.035 mm nominal outer copper; it has two through-via transitions. The old route was also 0.250 mm wide but included thinner, 0.0152 mm inner copper. “Mixed-thinner” describes thickness, not a narrower old VIN track.
- Nominal 20 °C series trace resistance: **38.038925 → 18.523854 mΩ**, a 19.515071 mΩ reduction. Independently recomputed the latter from axis lengths and copper sections. Neither number includes via barrels, pad spreading, real plating, temperature rise or parallel copper. This is a valid comparative DC metric, not a current rating or an HF impedance measurement.
- C27 GND → U14 GND has a **3.471024 mm continuous B.Cu witness with no via**. It includes 0.664061 mm inside the capacitor pad and 2.806963 mm of retained 0.127 mm track. The retained track alone is 10.887478 mΩ nominal. This proves a conductive fallback; it does not prove where switching return current flows. The old witness was 3.395275 mm, so the return is not geometrically shorter. Filled planes may dominate at frequency.
- C31 → VIN is **14.287422 mm**, sharing the C27-star/VIN branch. Its GND lead reaches a ground via, but there is no explicit track/pad/via-only path from that local component to U14 GND. **C31 cannot be credited as an independently demonstrated local HF capacitor before final plane attachment is established.** Even a connected C31 does not make shared feed inductance disappear.
- The upstream VX → D5 path gains about **6.002 mΩ** nominal trace resistance. Replacement GND donor copper gains about **12.573 mΩ** before parallel planes; the new 0.300 mm inner segment preserves nominal cross-section, not equal end-to-end impedance. These are disclosed costs, not proof of failure. U10/C18 decoupling remains a separate review.

## EN finding

The proposal's physical-contact cuts isolate only U14.7 when the EN leaf is removed, while VIN and the other VSYS ports remain connected. Cutting the VIN branch leaves no alternate PCB copper feed through EN. Thus the thin inner EN branch is not part of the VIN load-current path.

EN and VIN split at the star via immediately beyond C27's positive paste edge, sharing a 1.054751 mm pad-center lead. This is a reasonable implementation of capacitor-local EN sensing in this constrained layout, although it is not a zero-shared-impedance Kelvin connection. No evidence here demands another EN resistor/filter or a new net. Repeat the physical cuts on final emitted geometry. A PCB graph proof says nothing about IC-internal behavior under a deliberately disconnected-pin fault.

## Capacitance and assembly

[Samsung's exact family page](https://product.samsungsem.com/mlcc/CL21A226MAYNNN.do) lists CL21A226MAYNNNE, 22 µF ±20%, 25 V, X5R, 0805, with a maximum 1.45 mm body height and reference-only typical data. The preserved exact curve and calculation give the pair **7.872 µF at 8 V** after separate tolerance/temperature factors, or **5.927 µF** in the explicitly assumed generic 10-year aging scenario. This is a quasi-static capacitance screen at the manufacturer curve conditions (25 °C, 120 Hz, 0.5 Vrms), followed by separate factors. The two values can be summed for that screen; their contribution at U14 VIN over the switching spectrum is a frequency-dependent network involving the shared 9.401 mm feed, both VIN vias, C31's longer feeder, capacitor ESR/ESL and the actual return. A favorable sum therefore cannot close TI's local input-loop guidance. It is neither an exact-part guaranteed combined-corner minimum nor a board HF result. A single part in that same scenario is about 2.963 µF; do not silently drop C31.

The proposed 0.91 × 1.35 mm pads with 0.83 mm gap sit at the lower manufacturer reflow land-pattern bounds documented in the qualification study. Do not shrink them. Retain the exact source body/pinout/envelopes. The assembly supplement's under-D5 VX via and nearby star annulus still need process-qualified tenting, seating/coplanarity and final mask/paste inspection; D5's zero minimum standoff provides no guaranteed clearance above a soldermask tent. Z clearance remains open.

## Remaining gates and smallest justified remedies

1. **Final native evidence:** Bind the finished board to the intended source/schematic; refill and run complete DRC/connectivity; repeat branch cuts. Demonstrate finite C31 GND attachment and all moved ground-stitch attachments, including actual zone necks and thermal spokes. Inspect the In1/In4 return corridors beneath the VIN route, plus ground interconnection near both VIN layer transitions. Old-fill projection fractions are diagnostics only.
2. **No unconditional extra change is justified by the present evidence.** If refill leaves C31 or a necessary return segment isolated, the minimum remedy is a short DRC-clean GND connection/stitch to the demonstrated local ground network. If a plane slot forces a remote return detour, first repair that return locally or change the affected route. Exact locations require final native geometry; this review has not established one.
3. **Bench evidence:** Measure at U14 VIN/GND and EN/GND using low-inductance probing during startup/hot plug, the intended BEC setting, worst intended BEC/servo and FC load steps, and relevant temperature/mode corners. Establish ripple, ringing, rail limits, regulation and unintended reset behavior. Compare against actual system limits, not an invented percentage. If unacceptable HF behavior persists, shorten/tightly couple the local loop or evaluate a compact bypass directly at U14 with exact-part impedance evidence; an added part needs separate approval and does not replace the effective-capacitance gate.
4. **Production evidence:** Establish the actual BEC tolerance/transient envelope, service life, combined capacitance corners/lot variation, ripple heating, stackup/plating, assembly process and enclosure Z clearance. Nominal 8 V is a screening point, not a transient ceiling. A 25 V capacitor does not extend U14's voltage limits. Neither geometric screens nor a working prototype alone qualifies production.

## Evidence binding

- Accepted r61 PCB SHA256: `5a51610cc1569958442f97407e11533b646b1e0d8997d86356b8968dce50487e`
- Sealed atomic proposal SHA256: `1b3fe4992369b702493961750834c0411f6015c15bbdf8991359a482cd88d123`
- Exact inputs and independently recomputed figures: [review-evidence.json](review-evidence.json)
- Original proposal: `/workspace/scratch/8a35c1f26232/nexus-recovery-20261015/r61-cap-star-study/atomic-proposal.json`
- Distribution comparison: same directory, `power-distribution-tradeoffs.json`
- Assembly: `/workspace/shared/c27-parallel-placement-study/r61/FINAL-ASSEMBLY-SUPPLEMENT.md`
- Capacitor data/calculation: `/workspace/shared/nexus-c27-qualification/C27_decision.txt`, `qualification-screens.json`, `aging-guidance-scenario.json` and exact Samsung source files alongside.

No KiCad/native tool, solver or live r62 candidate was used. Existing graph/assembly screens were reviewed, not represented as independently rerun native checks. Source and proposal hashes were verified unchanged.
