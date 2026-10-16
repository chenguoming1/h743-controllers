# Selected PCB-only joint prototype

## Result

The integrated prototype keeps the 22.4 × 8.4 mm child, standard servo-header placement/pinout and 22.4 × 33.1 mm parent body. It uses 9.3 mm tabs in 9.8 × 2.10 mm R0.50 slots. Nominal X half-play falls from ±0.8083 to ±0.1830 mm, a77.36% reduction. Nominal transverse clearance falls from0.60 to0.50 mm total.

This is an **insertable, lower-play nominal design with explicit matched-pair inspection requirements**, not a guarantee that every standard-tolerance PCB pair will fit. No external brace, changed servo plug, added connector or larger enclosure part is included. Physical strength and service life remain unqualified.

Independent proof on integrated main SHA f39eba3ca14a833fb534a0ef133824923f67c515f60f7e81335c8d31ef0541fc, child SHAb49ef4108ab0b85d4cd96fac22553e3bc16b214f5acde148a8680e1212097ee6 and model SHAfae6c66ed62270d7096f0ce6272e00ce853ec379e43c03f58bf43e89370c61cc:

- Both main slots and all17 child bottom-contour segments match the exact geometry contract.
- All11 child pad X positions, widths, pin/net/face identities and the complete original servo-header placement/pinout are preserved.
- The actual exported24-mesh model,11,136faces, was clipped against the parent slab. All1,046 intersecting polygons fit within the true rounded slots. Minimum nominal clearance0.13749995 mm; no interference. The exported board/mask envelope is1.625 mm thick, which is a rendering result, not the finished manufacturing maximum.
- The implementing worker reports native child and main0errors/0opens, main parity0, with22child and61main inherited/advisory warnings. Independent checks here were read-only native-text/mesh checks, not a second native DRC run.

The main-placement task is subsequently changing placement/routing. Its final main hash must receive a new combined check; the above hash-specific pass does not automatically cover later edits.

## Exact geometry and copper transaction

Main J1 stays at native(100,100). Slots remain centered at local(5.6,2.4) and(16.8,2.4), radius0.50 mm; length10.10→9.80 and width2.20→2.10 mm. All16 edge UUIDs are retained. Pads, net assignments and model transform remain unchanged. Existing larger routing keepouts remain conservative. Slot shrink cannot decrease clearance to unchanged copper; it increases slot-edge distance by at least0.05 mm. The previous0.30 mm slot-to-copper bound therefore becomes at least0.35 mm before later routing changes.

Child origin remains native(100,108.4). Tabs are localX0.95..10.25 and12.15..21.45, length2.6 mm, on11.2 mm pitch. Four local270° R0.50 open root reliefs use an assumed nominal1.0 mm router, not sharp internal corners. Exact line/arc start/mid/end points are in `pcb-only-candidate/geometry-contract.json`.

Shoulder flats areX0..0.45,10.75..11.65,21.95..22.4. Total nominal seating width grows1.6→1.8 mm (+12.5%). Parent nominal outer rails grow0.55→0.70 mm; center web1.10→1.40 mm (+27.27%); front rim1.30→1.35 mm. The root neck is8.30 mm, versus8.40 before (−1.19%). These are geometric comparisons, not strength multipliers. Relief stress concentration and the actual residual rails require tests and finished inspection.

Every child joint pad/strip keeps its old X range and width. Y changes from0..2.346 to0.8..2.346: center1.573, height1.546 mm. Total exposed rectangle area decreases34.10%, but the lower solderable projection is unchanged:0.746 mm below a nominal1.60 mm parent and0.586 mm below a1.76 mm parent. Individual power-pad area changes3.7536→2.4736 mm²; each long strip18.514632→12.201032 mm². Those exposure figures assume flush seating and that parent thickness is measured from the actual finished seating surface to the finished lower joint surface; a seating gap or coating not included in that measurement must be subtracted. Nominal new root-to-pad gap is at least0.565653 mm; tip copper clearance remains0.254 mm. Main land positions are unchanged, so nominal perpendicular solder-fillet reach remains0.60 mm despite the smaller slot; this still requires solder-process qualification.

The reduced top pad area is not a free ampacity claim. Power routes/planes must reconnect into the new rectangles through the root; the final filled-board current model and solder/temperature-rise tests decide the electrical limit. Native pad/mask openings remain1:1, no per-pad margin override, ENIG declared. Mask wear, pooling, burr and full finished tab thickness must be measured.

## Tolerance and process decision

[JLCPCB's capabilities](https://jlcpcb.com/capabilities/pcb-capabilities) list normal routing and NPTH slot dimensions at±0.20 mm,1.6 mm thickness at±10%, and minimum soldermask thickness10 µm. The published±0.10 mm precision-outline option requires at least50 × 50 mm with three≥1.5 mm tooling holes; it does not independently promise those limits for this internal-slot/copper-datum/pitch combination. Maximum mask thickness, routed-profile pitch, corner-radius tolerance and routed-outline-to-copper registration are not established by that page. [JLCPCB's finish guide](https://jlcpcb.com/help/article/jlcpcb-surface-finish) supports choosing flat ENIG rather than uneven HASL; its typical coating figures are not a maximum-finished-thickness contract.

**Copper-to-finished-edge qualification remains open.** The existing 0.254 mm copper-to-edge CAD rule is retained, including the nominal tab-tip setback. JLC's public ≥0.20 mm routed copper-clearance entry describes a design capability; it is not a warranted minimum measured after routing. Neither that entry nor the public outline dimensional tolerance establishes a complete routed-profile-to-copper registration budget. Therefore the drawing does not establish a 0.254 mm finished setback. For illustration only, a 0.20 mm inward edge displacement would consume all but 0.054 mm of the nominal tip setback before copper registration or edge damage. This is an illustrative edge-displacement assumption, not a claim that the dimensional tolerance equals a guaranteed datum-registration limit.

No lower finished acceptance floor is adopted. The required final copper-to-edge setback must be qualified for the electrical environment, routing/finish process and exposed solder-joint geometry, then supported by measured process registration and adequate nominal margin. If 0.254 mm were required after manufacture, a 0.20 mm inward-edge allowance alone would require at least 0.454 mm nominal, plus any separate adverse copper-registration/edge-condition allowance; alternatively the corresponding displacement must be tightly controlled. Increasing the tip setback reduces exposed solderable length, so that remedy requires a new joint/current check. Profile-fit selection alone does not close this copper-edge gate.

The full-radius test uses qx=max(0,T/2+P/2+|dx|−(L/2−r)) and qy=max(0,t/2+|dy|−(W/2−r)). Radial clearance is r−sqrt(qx²+qy²). T is finished tab width, t is the complete finished mating thickness, P is actual pair-pitch mismatch. Both real profiles and absolute copper registration must also be checked.

Ordinary adverse dimensions L9.60,W1.90,T9.50,t1.76, with explicitly hypothetical r0.60/P0.40, give−0.31837 mm radial interference. These radius/pitch numbers are not vendor guarantees; the example proves that ordinary size limits do not establish fit. An ordinary loose-size example allows±0.44508 mm X play and0.86 mm total Y clearance, with possible foreign-land projection at its extreme. It too must be rejected by the acceptance gauge.

**Prototype matched-pair route:** manufacture nominal drawings, inspect the complete finished pair, and select only pairs with:

- At least0.025 mm true profile clearance through a common±0.02 mm X/Y insertion window about the intended copper-aligned pose
- No more than0.50 mm total X or Y freeplay
- Final inspected copper X registration within±0.10 mm, plus direct intended/foreign-net and fillet inspection
- No forcing, conductive-surface sanding, chips, burr obstruction or unacceptable bow/twist

The0.025 mm margin is a proposed inspection/design allowance, not a validated insertion-force standard. Actual selection yield and assembly capability are unknown. Rejected pairs are rejected or re-paired; the drawing is not an unconditional standard-process release.

**One sufficient supplier-controlled box:** finished slotL9.75..9.80,W2.05..2.10; tabT9.25..9.35; complete finished thickness1.60..1.65; radius0.49..0.51; actual pair-pitch mismatch≤0.05 mm. These are proposed tighter/unilateral acceptance limits, not a published JLC promise. Worst insertion corner retains0.025309 mm reserve with±0.02 mm X/Y offset. The loosest checked dimensions retain approximately±0.2122 mm X play and0.50 mm total Y clearance. Absolute copper datum/tilt/bow still need measured acceptance.

For the adverse controlled box and required0.025 mm reserve, exact conditional boundaries areL≥9.749155,W≥2.049092,T≤9.350845,t≤1.650908,P≤0.050845 mm, varying only one parameter at a time. These independent maxima cannot all be taken together. Full calculations and witnesses are in `pcb-only-candidate/fit-verification.json`.

## Load path and remaining gates

Root shoulders provide downward seating; the narrower matched slots limit lateral travel and supply FR4 side bearing after clearance closes. Normal separated electrical fillets provide retention; no oversized solder bridge is proposed. With no external retained support, connector/cable moment still reaches the root, slot rims and soldered joint. This analysis cannot establish its acceptable load or fatigue life.

Before release: qualified finished copper-to-edge requirement and proven geometry/process margin; final coherent native DRC/refill/netlist and actual 3D check after the main-placement changes; finished paired-profile/registration and insertion-force checks; solder wetting/fillet inspection; final-current/temperature tests; plug mating/extraction and cable-strain tests; representative helicopter vibration/shock and thermal cycling with powered continuity and post-test crack/fillet inspection. Any additional strain-relief or structural part requires its envelope and mounting consequences to be resolved separately.

Keep export origin100×108.4 mm, model offset(22.4,−2.4,0), rotation(−90,0,180). Native child-to-main-local mapping isX=122.4−x_child,Y=2.4−v,Z=108.4−y_child, wherev is the child's centered thickness coordinate. Never shift the origin with a future body-height change.
