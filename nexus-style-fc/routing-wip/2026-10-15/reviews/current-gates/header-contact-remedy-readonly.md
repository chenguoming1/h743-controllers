# Header contacts: read-only dimensional remedy

No pad, outline, slot, net or assembly process was changed. This is a geometry option for a separate approval, not a release or joint-strength qualification.

## Copper recession can preserve nominal solder overlap

The exact original header source has eleven contact lands ending 0.150 mm from each tab end. Keeping the land start at the seating line and trimming its lower edge by 0.104 mm gives the required 0.254 mm nominal clearance. Land height decreases from 2.450 to 2.346 mm. The 2.600 mm tab projects 1.000 mm below the 1.600 mm main board, so exposed copper below the main-board bottom remains 0.746 mm instead of 0.850 mm. A bottom fillet still has nominal vertical copper overlap; the approximately 12.2% smaller exposed height needs assembly/strength/current review.

Bottom recession alone is insufficient. P1(S1), P7(SBUS), T1(GND), T2(VX) and both outer strips also have 0.200 mm lateral clearances at their tab ends. The corresponding outer edges need another 0.054 mm trim to achieve 0.254 mm. Cropping only the affected edges preserves the other edges and most matching main-land overlap: edge signal lands become 1.146 mm wide, edge power lands 1.546 mm, and each 9.800 mm strip becomes 9.692 mm. All landing contacts/routing would still need native validation. The JSON provides exact native bounding boxes and hypothetical new bounds.

This is a contact-pad geometry change, even though parts/nets and the tab outline could remain unchanged. It is not authorized by the routing-only request and has not been applied. Translating the entire pad upward by 0.104 mm is less suitable than trimming the lower edge: translation moves its top above the intended seating line and can affect existing route contacts.

## Copper movement does not cure the assembly interference

Each square 10.200 mm wide ×1.600 mm thick tab is intended to pass through a 10.400 ×1.800 mm capsule slot. At either board face, 0.800 mm from the slot centerline, the slot end circle has horizontal reach sqrt(0.900²−0.800²)=0.412311 mm. The capsule straight section is 8.600 mm, giving only 9.424621 mm usable rectangular width. The tab therefore interferes by 0.387689 mm per end, even before tolerances.

Keeping the square tab and 1.800 mm slot width would require at least 11.175379 mm capsule length merely for nominal zero interference. The two slot centers are 11.200 mm apart inside a 22.400 mm board. Such slots would leave only about 0.024621 mm between them and 0.012311 mm to each outer board edge. Simple slot-length enlargement is therefore not a viable mechanical correction within this architecture.

Shortening each tab to at most 9.424621 mm would nominally fit, but would cut into existing outer contact copper and require materially larger pad/strip reshaping, new clearances, and joint/current-strength review. A controlled relieved/dog-bone slot-end profile or a specified tab-edge/bevel process could be investigated, but neither is designed or manufacturing-approved here. Ordinary 2D rounding of the tab insertion tip alone does not prove clearance through the full 1.600 mm board thickness.

## Decision needed

Moving copper inward can retain nominal solder contact, but cannot establish assemblability. A separately scoped tab/slot/contact geometry correction and tolerance/fillet verification is required. Keep the 11 header DRC findings and fabrication hold visible until the chosen geometry passes native clearance and a real 3D/tolerance check. No blanket edge-rule waiver is proposed.

Source: tools/make_footprints.py and the exact native header board at SHA256 99d06c7ec685f776f357958c22f684f198f9ef5bf7e9bed437833c9d6aadfba0. Native pad bounding boxes and arithmetic are in header-contact-remedy-readonly.json. No board save, refill, DRC or routing was performed for this note.
