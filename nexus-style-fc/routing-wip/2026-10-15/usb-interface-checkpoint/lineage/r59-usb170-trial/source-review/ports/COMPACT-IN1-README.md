# Compact In1 local-join variant

This optional, fully screened variant changes only the short DP B6→A6 join layer from In4.Cu to In1.Cu compared with compact-port-proposal.json. All XY coordinates, .150 mm USB widths, ordinary .45/.20 vias, seven USB-via total, donor replacements, preserved U7 bridges, and In3 output handoff remain unchanged. All VBUS_C widths remain .250 mm and CC1 remains untouched.

Exact geometry: compact-in1-port-proposal.json.

Evidence: compact-in1-port-screen.json, compact-in1-protection-cut-screen.json, compact-in1-vbus-closure-screen.json, compact-in1-donor-contact-comparison.json, compact-in1-path-via-accounting.json.

The combined screen has zero fixed-object hits and zero new-mutual hits. There are separately zero pasted-pad drill intersections and zero annular-copper/paste overlaps. Donor contact comparison preserves the same LED1_K 2 contacts among 27 retained objects and VBUS_C 4 contacts among 12 retained objects, with zero lost or added contacts. The preserved U7 bridge remains a necessary electrical cut for both J6 orientations.

Using In1 eliminates In4's extra 1.1304 mm DP barrel traversal. A and B, DP and DM each use 2.2885 mm of barrel centerline. Via-transition counts remain A DP/DM 3/2 and B DP/DM 4/3. Planar DP-long mismatch remains A 2.630552 mm and B 2.556960 mm; adding used barrel does not change those mismatches. Barrel count and electromagnetic behavior still differ, so this is not a delay match.

The In1 branch is approximately 2.514 mm long and needs re-poured local GND clearances. It is on a different layer from the In3 DM connector branch; there is no claim of continuous differential coupling through that connector join. Reference continuity, zone refill, native DRC, paste generation, and impedance validation remain for the parent integration. The compact geometry has tight margins: the relocated VBUS_C via-to-J6.B5 copper gap is .130 mm against a .127 mm requirement. No board file was modified.
