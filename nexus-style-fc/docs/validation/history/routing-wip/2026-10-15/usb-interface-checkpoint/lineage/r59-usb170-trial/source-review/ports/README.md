# Read-only complete J6/U7 port candidate, accepted r57

Source SHA-256: 583e73ba08c80e70d42bfd726ef1b440ab0ddf4d7309cef266de486fd03f461f. Source remains unchanged. No native KiCad, board writes, solver, or GitHub action used.

## Result

The complete connector/protection transaction is geometrically screenable at 0.150 mm USB width without narrowing or new pasted-via dependencies. It hands off on In3.Cu at DP (109.5115,124.0) and DM (109.7885,124.0). This supersedes the initially requested In2 output layer following the parent's updated trunk decision.

- Both J6 orientations are connected: A6/B6 DP and A7/B7 DM.
- Input attaches at U7 pin3 DP and pin1 DM; output leaves pin4 DP and pin6 DM.
- Preserve original B.Cu 3↔4 and 1↔6 external bridge copper, each 2.3 mm long. Delete old bridge-center branches and the former bypass feed.
- Five existing 0.45/0.20 USB vias are reused. The only added ordinary through via is DM (109.625,125.31).
- One donor segment is completely replaced: LED1_K In2.Cu UUID 7fed82a0-bca6-4de2-afbb-42c2e3662bcd. Its endpoints remain (108.56,124.36) and (110.775,126.575); replacement runs via (108.7,124.5), (108.7,125.3), (109.2,125.8), (110.0,125.8), retaining 0.127 mm width.
- No component, net, fixed pad, power width, or ground contact changes.

## Evidence

port-proposal.json has exact per-layer segments, vias, bridge UUIDs, and affected local source tracks. Bridge entries are included for screening only; preserve existing copper instead of duplicating it. Parent must remove/replace old downstream USB tracks reaching into this window as part of its complete trunk transaction.

verify_ports.py reproduces port-screen.json: zero fixed-object hits, zero new-mutual hits, zero new drill/paste intersections. Smallest different-net new-copper gap is 0.127 mm at trunk handoff; output via-via gap is 0.137133 mm. Bounding rectangles conservatively screen rounded pads. Existing USB routing is excluded but all fixed USB pads remain in the screen.

check_protection_cuts.py reproduces protection-cut-screen.json. Both J6 orientation pads reach their output handoff in the proposed copper graph; removing the corresponding external protection bridge disconnects each one. This excludes a physical bypass around the protected path.

## Important limitations

This is a clearance/topology candidate, not a completed impedance or native DRC signoff. Saved zone fill clearance is not evaluated here; parent owns reference-plane assessment and subsequent refill/native verification.

The connector launch itself is not uniformly paired or length-matched. Proposed planar centerline lengths to the handoff are DP 11.4313 mm / DM 8.8008 mm for orientation A (DP longer by 2.6306 mm), and DP 15.5410 mm / DM 10.7079 mm for orientation B (DP longer by 4.8331 mm). These exclude barrel delay and pad propagation. Therefore a paired downstream trunk alone does not demonstrate end-to-end USB signal-integrity compliance. Keep the launch-skew limitation explicit, or authorize a separate launch-balancing investigation before implementation.
