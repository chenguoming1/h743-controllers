# Isolated RPM_HV closure from accepted candidate45

Native result:33 unfinished connections, zero geometric errors/warnings, strict schematic parity and ERC zero. Pending owner review; not manufacturing/flight qualified.

Adds nine0.127 mm F.Cu segments from R25.2 to actual bonded U16.1. The native RPM_HV graph now joins R25.2,U16.1,Q1.3. No vias, removals or footprint changes. All1941 previous native records,156 footprints,1383 previous track/via/arc structures and every saved zone record remain exact. Outside-layer-only additions need no plane refill.

All18 new endpoints have finite full-width proof: two native pad entries and eight exact round-ended joins. Five rejection controls pass. All28 support partitions and both I2C complete trees are preserved. The actual U16.1 pad-cut disconnects source from Q1.3 with nominal outside-pad separation0.577505167861 mm, zero outside-pad overlap. Actual protection rises11→12/22 endpoint cases and9→10/20 channels.

A bounded0.04 mm planning-grid search found a complete same-face corridor. Native exact-distance line-of-sight simplification permits arbitrary track angles. The raw proposal and all later local-centering sweeps remain in rpm-F-route.json and refinement-history.json. Final minimum nominal CAD copper gap is0.128106934746 mm, excess0.001106934746 mm above the0.127 mm rule. This is nominal CAD geometry, not manufacturing margin. No actual clearance or fabrication rule was relaxed.

Raw critical comparison is true with zero numerical projection deltas, empty physical GND loss/gain and exact critical record equality. No runtime-net-index exception is needed. All16 critical nets/returns and29 firmware checks pass. I2C electrical status and current numerical power/VCAP remain unqualified.

Source board SHA256:9881a992b12fed90f17131ed627f12af77680cc2ddf95030adf8c564aaa24eb2
Candidate board SHA256:87c5ced471edaf2e0ace382d4236bc1787efb869b7ae759c53d87ee76165c0cb

SBUS_HV remains open. Initial fixed-source local screens are retained one directory above and are not a global impossibility proof. No experimental SBUS geometry is included.
