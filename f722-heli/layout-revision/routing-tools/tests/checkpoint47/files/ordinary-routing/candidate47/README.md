# Isolated SBUS_HV closure from accepted candidate46

Native result:32 unfinished connections, zero geometric errors/warnings, strict schematic parity and ERC zero. Pending owner adoption; not manufacturing/flight qualified.

Fourteen0.127mm F.Cu/In3.Cu tracks and two0.45/0.20mm tented through-vias complete Q2.3→actual bonded U16.2. The SBUS_HV native graph now joins Q2.3,U16.2,R26.2. Actual U16.2 pad cut disconnects source and target with0.4208mm nominal outside-pad gap. The existing RPM_HV actual U16.1 cut remains exactly0.577505167861mm. Protection rises12→13/22 endpoint cases and10→11/20 channels; supplemental7/7.

The complete local reconstruction removes exactly four source objects: CORE via4ac2092d-48da-4042-9f80-6d638e3072d9; CORE tracks4c08b337-8a52-4b54-91f6-5521720e8561 ande712d11a-7e0e-4cb8-9a2a-275159c4142c; ADC_DIV_MID In2 tracka502a7e6-5c8c-4e37-91e0-b48000060a82. CORE via moves(17.110541,9.777898)→(17.1,9.84); both feeds keep0.20mm width and exactly the same remote source endpoints. Combined feed length0.947400815→0.966218588mm, increase0.018817774mm. No capacitor footprints or GND return objects move. ADC_DIV_MID receives four0.127mm replacement segments; complete coordinates and native IDs are in constructed-paths.json and coordinated-change-receipt.json.

Twenty tracks plus three vias are added;1946 source records,all156 footprints and all GND pad/track/via records remain exact. Both reference planes are refilled with unchanged definitions. All40 new track endpoints have finite proof, comprising two actual pad entries,18 full-width joins and8 actual annular entries. Eleven rejection controls pass. All28 native support pad partitions, both complete I2C trees and16 critical nets/returns pass. Raw critical-record comparison is true with zero reference metric deltas and zero lost-ground overlap with critical trace widths. Changed fill geometry is retained explicitly.

The narrow local portal geometry and route centering are nominal CAD evidence only, not manufacturing margin. The source CORE-via proposal had0.000489371mm minimum excess over its controlling native rule. Planned ADC_BUS obstacle clearance was also checked; this is a partial future compatibility receipt, not a merged ADC board qualification. Final ADC/C31 changes require source-bound merged native checks.

Current numerical power/VCAP and I2C electrical applicability remain pending. No historical source43 numerical qualification is inherited.

Source SHA256:87c5ced471edaf2e0ace382d4236bc1787efb869b7ae759c53d87ee76165c0cb
Candidate SHA256:f7d5731bb0bf1ad314aca6d507da004993671bce413fbdeba545083168e28161
