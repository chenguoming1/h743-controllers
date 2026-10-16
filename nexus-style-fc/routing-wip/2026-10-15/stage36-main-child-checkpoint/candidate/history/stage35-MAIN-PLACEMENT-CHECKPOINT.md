# Stage35 checked successor

## Results
- Official KiCad 10.0.7: zero DRC errors, zero unconnected items, zero schematic-parity violations; 56 warnings remain. Main ERC has zero violations.
- Four off-pad USB right-angle corners become 0.08 mm leg-trim bevels. Each net shortens equally by 0.093726 mm. USB_DM is consistently renamed USB_DN in PCB, schematic, project and both source tools; native USB_DP/USB_DN pairing now works. All ten USB pad identities/contact sets survive.
- The obsolete six-object 3V3_SENS dead leaf is removed. All 15 live sensor-rail pads and six retained via contact sets remain connected.
- The U5.2 switch fanout receives a short vertical exit before its diagonal. The neighboring U5.3 mask/paste/copper gap increases from approximately 0.0087 mm to 0.2350 mm; added centerline length is 0.100844 mm. All three switch pins remain directly connected to L1 without vias.
- Fresh Gerbers/drill and BOM/CPL are bound to the sealed board. Generated source agrees on all 89 footprints and 356 pads; BOM/CPL are byte-identical to stage32 (48 groups, 83 placements).
- Full parsed footprint, outline, stack/setup objects are identical to stage32 after only the USB alias normalization. Joint geometry, poses, pads, courtyards and model transforms therefore retain the prior nominal mechanical proof (minimum mesh gap 0.1375 mm). Child PCB/model are unchanged.
- Saved-plane checks retain the local ground returns. The four new USB bevels and both approximately 13.133 mm In3 trunks have sampled In4 center/edge coverage. These are geometric checks, not SI/PI qualification.

## Remaining work and qualification
NRST capacitor and ADC filter placement/routing trials remain isolated and are not included here. USB complete-path planar differences (approximately 2.570/2.497 mm) and unequal via counts remain documented; no applicable USB full-speed numeric PCB mismatch limit was established, so they are not labeled demonstrated failures. Nonuniform closer In2 copper and stack/process details still require signal-integrity review.

Stage32 JLC results remain bound to stage32. Its U10 model still reported one pin without pad, four lead overlap ratios of 0.66 and 0.96 mm misalignment, despite correct native pinout and the TI land-pattern change. Actual model/rotation-overlay cause remains unresolved. C19 lead-to-hole, component edge/access, silk and other fabrication findings remain review gates. Stage35 fixes the two localized native geometries associated with the new mask-sliver and free-end findings; it has not yet received a fresh JLC result.

The 56 native warnings are 30 silk overlaps, 15 silk-over-copper, seven track-not-centered-on-via, three silk-edge-clearance and one footprint-type mismatch. Reliable tenting of the documented U5 corner via, component effective capacitance/ESR, assembly clearances, board-edge process, thermal/current/transient/EMI and mechanical/vibration qualification remain open. No filled/capped via process is assumed.

## Evidence
verification/dfm-local-repair contains saved native and exact fresh-Gerber primitive proofs; verification/usb contains the USB contact/reference audit; verification/main-source-synchronization contains generator/BOM/CPL checks; verification/mechanical contains the exact unchanged-geometry rebind. Earlier stage32 engineering and mechanical evidence is preserved under history.
