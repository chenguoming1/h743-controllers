# Nexus main-board placement correction — engineering checkpoint

This is an unfinished engineering revision, not a fabrication release. The published stage10 source remains preserved separately. No purchase or manufacturing submission is authorized by this checkpoint.

## Implemented and checked

- **MCU core capacitor C9:** moved to the MCU side. Its VCAP connection is now a direct approximately 1.71 mm B.Cu trace with no supply vias, plus an explicit local ground connection. The original audit's full-segment witness was approximately 13.90 mm with three vias; that witness was not an impedance measurement.
- **MCU VDD19 capacitor C1:** moved to the MCU side with a short direct local supply branch and explicit return. The obsolete front-side branch was removed without breaking the retained C2 rail.
- **Buck cell U5/C21–C24/L1/R11/R12:** compact backside placement, retaining the joint soldering courtyard. C21-to-VIN is a direct approximately 1.56 mm, 0.50 mm connection. Three short SW fanout traces reach L1 without layer changes. The input and output capacitors have explicit local ground stitches and In4 connections to the exposed-pad ground via.
- **Buck sense:** VOS uses an inner signal layer to the existing output takeoff. The final approximately 1.33 mm of 0.50 mm output copper is shared with load current. This is not a true Kelvin connection; switching pickup and transient behavior remain qualification items.
- **IMU bypass:** C13/C14/C15 supply paths are approximately 1.670/2.770/2.169 mm; C15 has an approximately 2.739 mm explicit front return. The upstream C16/C17 feed uses an off-body transition and a bounded DSM_DATA reroute rather than an additional under-QFN via.
- **C2 return:** the temporary narrow continuity bridge was removed. C2 now has a direct approximately 0.652 mm, 0.40 mm front trace to a nearby ground stitch. C_TX and SBUS were locally rerouted to make this possible; no pin roles changed.
- **Crystal:** C11/C12 are on their corresponding crystal sides, with approximately 1.50 mm direct capacitor connections and short explicit returns. MCU oscillator traces remain on B.Cu.
- **U10:** approved TPS70933DBVR/C89347, center, rotation and pin nets are unchanged. A dedicated TI DBV example-land variant uses 0.60 × 1.10 mm lands at row offsets ±1.30 mm. Tiny coordinated SCK/MOSI via/track and C19-feed adjustments restore clearance. EN remains floating as approved. This is a documented land-pattern improvement; it does not establish the cause of the earlier JLC model-overlay report.
- **Main/child integration:** exact guarded 9.8 × 2.10 mm slot contours are paired with the sealed 9.3 mm child tabs and continuous-VX child board. Pads, joint pose and body datum are retained.

## Native and source validation

Official KiCad 10.0.7, final main PCB SHA256:
`f214f8141e8f21a7e0983c8eb4f2be89634e3b69d0d2b168a1ac3153f28a83de`

The native refill/DRC reports **0 errors, 0 unconnected items and 0 schematic-parity differences**, under the exact approved project rules SHA256:
`b34415304c2bd364fed7f2f22231db9a893f4a0a4810e0c9300f54499674ba5b`.

There are **58 warnings**: 30 silk overlaps, 15 silk-over-copper, seven track endpoints not centered on vias, three silk-edge warnings, one dangling ground tail, one footprint-type warning and one copper sliver. They have not been represented as clean manufacturing acceptance. The original stage10 report had 61 warnings.

A staging check accidentally used a KiCad-default project after loading a temporary board under a different basename. Its report is preserved as invalid evidence. The accepted check restores the exact original approved project; no design rule was relaxed to obtain the result above.

Final source regeneration matches all 89 footprints and 356 pads, including U10’s revised lands. Main BOM/CPL contains 48 grouped rows and 83 placements, with approved part identities and pin roles preserved. Main and child ERC each report zero violations. The final local Gerbers, drills and placement outputs are bound by the checkpoint seal. The placement generator is a floorplan generator; running a full regeneration does not reproduce the manually revised routing automatically.

## Mechanical and assembly boundaries

The selected main/child/model proof finds no nominal interference, with minimum slot mesh clearance 0.137500 mm. Backside capacitor-to-J1 courtyard gaps are C21 0.07 mm and C22/C23 0.09 mm. U10's dedicated courtyard retains an explicit 0.15 mm dense-layout land margin; it is 0.05 mm behind J1's courtyard and 0.450006 mm behind the actual nominal child-header envelope. These are nominal CAD measurements, not process tolerance qualification.

The VX feed via at (104.95,107.35) occupies an unused QFN corner. The board requests tenting; the actual exported backside mask and paste contain no aperture touching its annulus, with a conservative nearest-opening gap of 0.185 mm. Nominal underside-metal separation does not guarantee tent integrity or assembly registration. No filled/capped-via process is assumed. The retained exposed-pad via and existing vias intersecting other solderable areas also retain their manufacturing qualification requirements.

## Explicit remaining work

1. Reset-capacitor placement remains at its original pose. The attempted closer placement intersects an ADC transition and needs a coordinated follow-on repair.
2. Remaining ADC and USB routing/placement qualification is not closed by this checkpoint. C30 retains its original placement; the accepted C29 and IMU-related changes are recorded in the source delta.
3. Validate switching behavior, output sense pickup, the relocated U11 ESD clamp rail, current density at the buck fanout, thermal behavior and actual copper stackup. U11 rail width remains 0.35 mm.
4. Qualify capacitor effective capacitance/ESR, under-package tenting, exposed-pad paste/via behavior, soldering/rework access and production tolerances with the selected assembly process.
5. Resolve or explicitly accept the remaining silk, sliver, contact-centering and other warnings, and rerun factory DFM on the exact intended release after the user authorizes that upload.

The actual U10 output routing already contained 0.1874 mm sections in the baseline. This revision does not claim a nonexistent all-0.25 mm width invariant.

## Return/contact and visual evidence

The final C2 stitch is in the same filled In1/In4 GND polygon as the C21/C24/EP vias. A 0.01 mm raster of the 0.40 mm-radius disk around C2’s stitch contains 5,025 copper samples and no voids. Explicit C21 return lengths are 0.846 mm B.Cu at 0.40 mm width plus 2.519 mm In4 at 0.50 mm; C24 uses 1.818 mm B.Cu and 3.220 mm In4, both 0.40 mm. C9-to-MCU ground is 2.216 mm at 0.20 mm; C1’s ground dogleg is 3.872 mm at 0.20 mm. These centerline lengths do not measure impedance.

The new sensor feed is 8.304 mm on In2. In1 GND covers its centerline between the expected endpoint-via antipads. Two small edge samples clip an existing adjacent-via antipad; it is not an uninterrupted full-width reference everywhere, and no SI/PI signoff is inferred.

All 18 newly identified vias have no outer copper-pad approach within 0.10 mm. Every explicit centered track contact extends beyond its via’s outer annulus; the two zone-only stitches are covered by native connectivity. The separately moved U10-area vias have their own native hole/pad/contact screen.

Final native front/back copper, courtyard and silk renders were visually inspected. The compact power/decoupling and crystal placements, revised U10 lands and matched slots agree with the source. Existing silk overlaps remain visible and recorded; this is not a production-assembly visual signoff.
