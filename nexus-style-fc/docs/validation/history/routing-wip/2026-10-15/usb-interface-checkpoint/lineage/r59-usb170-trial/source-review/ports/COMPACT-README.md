# Bounded compact J6 join alternative

Use compact-port-proposal.json in place of the baseline port-proposal.json if the extra USB via and split-layer local join are acceptable. It retains the same U7 handoff and LED1_K donor. Accepted r57 source has not been changed.

## Complete change

Remove the old DP B6 via (108.65,131.754) and its lower excursion. New ordinary USB vias are DP B6 (108.66,129.82) and DM B7 (108.08,129.77), both 0.45/0.20 mm. Preserve the A6 via (108.075,127.375) and A7/DM via (108.65,127.846).

DP B6 reaches its new via on F.Cu, then joins A6 via with one 0.150 mm In4.Cu segment. DM B7 reaches its new via on F.Cu, then joins A7 via with one 0.150 mm In3.Cu segment. DP input continues on In3 to U7 pin3; DM continues on B.Cu to pin1. U7 pin4/pin6 egress and the preserved 2.3 mm physical bridges remain exactly as in the baseline proposal.

The VBUS_C via (109.1,129.8), UUID dec81706-decb-4019-9e9c-89950cffcba7, must move to (109.245,129.845). Completely replace its three old incident source segments:

- F.Cu 9d44ed26-9c00-46f8-bae2-d6c9450e8c39: new via → (109.5,129.6)
- B.Cu a8c14c58-c428-41b2-a1b5-19e9f92325b7: new via → (109.245,130.1) → F1.1 at (108.4,130.9)
- In2.Cu e585a894-f9ca-4ca8-a469-3926f53c3771: new via → (109.245,129.15) → existing endpoint (107.732,128.645)

All replacement power traces remain 0.250 mm. All other VBUS_C copper remains; copper-graph testing confirms J6 A4, A9, B4, B9 each remains connected to F1.1. No CC1 modification or new donor dependency is needed. There are seven USB vias versus baseline six; total VBUS_C via count does not change.

## Bounded verification

- compact-port-screen.json: zero fixed foreign-object hits; zero new-mutual hits
- New J6 USB via-via copper gap: 0.132151 mm
- New DP-to-relocated-VBUS_C via gap: 0.135534 mm
- Relocated VBUS_C via copper gap to fixed J6.B5: 0.130000 mm; to R21.2: 0.137836 mm
- compact-protection-cut-screen.json: both orientations reach their output, and each loses that connection when its corresponding U7 external bridge is cut
- compact-vbus-closure-screen.json: all four J6 VBUS_C contacts remain connected to F1.1
- Both drill/paste intersection and annular-copper/paste-overlap tests are separately zero, against all pasted pad bounds. Minimum annular-copper-to-paste gap is 0.110 mm at the reused DP input via near same-net U7.3. This is not a foreign-net clearance violation. No explicit board, footprint, or pad paste margin override was found for the nearby evaluated footprints; screen conservatively treats roundrect pad bounds as rectangles. Final generated paste/DRC verification remains required.

## Branch tradeoff and length

Planar copper centerline paths to the unchanged handoff:

- Orientation A: DP 11.431331 mm; DM 8.800779 mm; DP longer by 2.630552 mm
- Orientation B: DP 13.169392 mm; DM 10.612432 mm; DP longer by 2.556960 mm

B-versus-A branch addition is 1.738061 mm for DP and 1.811653 mm for DM, a 0.073592 mm difference. Baseline branch additions were 4.109668 mm DP and 1.907107 mm DM. The compact alternative removes the large B6 excursion and improves orientation consistency, but does not claim a mathematically minimized branch or an end-to-end length-matched pair.

The explicit engineering tradeoff is one additional USB via and a roughly 2.514 mm In4 DP branch opposite an approximately 2.007 mm In3 DM branch. These local launches are not continuously coupled. In4 GND fill must be re-poured around the branch; reference continuity and via-barrel delay need separate evaluation. Both A and B routes still have approximately 2.6 mm DP-long planar skew. A later common DM length-balance transaction could address this, but no unverified meander or arbitrary maximum-length assumption is included here.

No native KiCad or board-writing operation was used. The exact geometry is a candidate, not an impedance, fabrication, or native-DRC signoff.

## Complete same-net boundary contacts and used via barrels

compact-donor-contact-comparison.json compares each removed donor block against every retained same-net track, via, and pad, including incidental non-endpoint contact. LED1_K examines 27 retained objects and preserves exactly the same 2 contacts. VBUS_C examines 12 retained objects and preserves exactly the same 4 contacts. Neither block loses or adds a retained contact. In particular, the VBUS_C F.Cu branch also physically contacts the retained A9↔B4 vertical trace away from its endpoint; that contact is preserved.

compact-path-via-accounting.json records every layer transition and copper-center Z. A orientation uses 3 DP transitions and 2 DM transitions, each totaling 2.2885 mm of used barrel. B orientation uses 4 DP transitions totaling 3.4189 mm and 3 DM transitions totaling 2.2885 mm. In4's detour adds 1.1304 mm of used DP barrel; B planar-plus-used-barrel DP excess is therefore 3.687360 mm, not its planar-only 2.556960 mm. Ordinary unused barrel sections are present. These values are physical path accounting, not electrical delay or SI signoff.
