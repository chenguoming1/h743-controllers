# Standard-stack adaptation — 17 October 2026

The main board is adapted to **standard JLC06161H-3313**, six layers, nominal 1.6 mm, 1 oz outer / 0.5 oz inner. Source/CAM hashes: [binding](binding.json). This supersedes the custom 2116A order instructions and quote.

The In1/In2 copper contents are exchanged. Physical L3/In2 is now the GND reference just 0.1088 mm above the L4/In3 USB trunks; L5/In4 remains GND 0.550 mm below them. The 41 matched USB segment/arc objects change from 0.143 to **0.132 mm** width, giving **0.165 mm** nominal edge spacing at unchanged centerlines. Four taper polygons are adjusted. No components, footprint/pad geometry, vias, outline or non-USB track widths/XY are changed. In particular the owner's 5V_BUCK widening, VCAP circuit and child board are preserved. BOM and CPL are byte-identical.

JLC's live calculator synthesizes approximately 0.1313 mm at a requested 0.1651 mm gap for a 90 ohm differential pair on L4, referenced to L3/L5 on the standard stack. The stack dialog gives an actual nominal thickness of **1.5384 mm +/-10%**, matching the CAD copper-plus-dielectric sum. [Calculator inputs/result](standard-calculator.txt), [layer assignment](layer-sequence.png).

The five source-bound, six-layer cross sections give about **90.3–90.6 ohm** at 0.0025 mm mesh, with floating/AC-grounded foreign-net sensitivity and domain checks retained in the JSON outputs. Model includes a 0.01778 mm signal etch taper, nominal material Er, ideal metal and locally uniform 2D crossings. Outer 3313 Er4.05 is assumed, not a supplier-guaranteed value. This is not a full 3D connector/via/ESD simulation, manufactured coupon or assembled USB certification.

Both matched trunks have zero uncovered center/edge samples on both GND references, at <=0.010 mm sampling. Top-layer returns are less direct because L2 is now mixed routing. Top SPI/I2C pieces affected are short (0.7–3.2 mm); F-layer USB pieces are 2.1–2.4 mm, and long bottom MCU/crystal/VCAP routes retain L5 GND. See [front projection comparison](front-reference.json). This is a cost-driven six-layer arrangement with greater top-signal return/coupling uncertainty than the former custom stack; SPI/I2C, sensor noise, USB and EMI still require prototype testing. Geometric coverage is not a return-current proof.

Fresh native validation: main ERC/DRC/opens/parity all **0**; child ERC/errors/opens/parity **0**, with its 11 inherited bare-contact courtyard warnings. Rules, exclusions, child source and child Gerbers are unchanged. Fresh [JLCDFM PCB analysis](https://jlcdfm.com/viewer?pcbUploadFileId=634385030643404802) has **all 29 category triples unchanged**, including green width, clearance, pad-spacing, corners, mask-to-trace and slot checks. Existing annular-ring/THT/silk flags remain; the report is not all green. SMT was not repeated because placement, pad geometry, BOM/CPL and outer artwork are unchanged.

The owner explicitly declined the paid +/-10% impedance inspection. **90 ohm is the nominal layout target; no production impedance test/coupon/report is ordered.** Although JLC's general help page mentions free +/-20% testing, this quote's No requirement tooltip explicitly says no impedance test/report is provided. No free-test assurance is claimed.

Regular **+/-0.2 mm** contour tolerance replaces paid +/-0.1 mm. Nominal main slot 2.2 mm against child nominal 1.6 mm leaves about 0.24 mm thickness clearance at a 2.0 mm slot and 1.76 mm child. Slot length 9.8 mm against tab width 8.4 mm leaves 1.0 mm total at +/-0.2 mm opposing size limits; pitch and router/finished-thickness effects still need factory fit review. The joint is a soldered prototype interface, not a validated press-fit or current-rated connector.

Current quote and package bindings are recorded below after the final upload. No NEXT, cart submission, terms acceptance or payment is authorized by this review. J6 shell-leg soldering/retention and parts stock/attrition still need the existing factory review before release.


## Final quote left open

[First-page quote](https://cart.jlcpcb.com/quote?rand=0.7211921819509453): **USD 87.88 PCB estimate**, plus USD 9.66 shipping estimate. Parts and assembly remain unquoted. This is USD **142.05 less** than the earlier comparable USD229.93 custom-stack/precision/paid-test form: USD100.49 stack, USD8.48 contour precision and USD33.08 impedance inspection removed.

Five fabricated PCBs, **two Standard assembled, both sides**; standard JLC06161H-3313, green/white, ENIG1u, TG155, 1oz outer/0.5oz inner, all228 POFV vias, 0.20mm via option, regular +/-0.2mm contour; no paid impedance testing/report. Explicit F/In1/In2/In3/In4/B file assignment, factory rails/fiducials and depaneling enabled. Both production-file and placement approvals are manual, with automatic approval disabled. Assembly terms remain **unchecked**. NEXT, cart submission and payment were not performed.

The final quote upload ZIP SHA256 is `136b2928860cad2c4de53e89b75e9c1cedf82e89b9da3a0ccecabae82b961d38`; its 16 CAM members match the fresh DFM archive byte for byte, plus the revised nominal-design-target JPG that explicitly says no paid test/report. [Recorded form](quote-page.txt), [selected buttons](quote-options.json), [final price/terms](quote-footer.png), [standard stack and no paid test](quote-standard-stack.png).

The complete updated order package is `manufacturing/nexus-prototype-order-2026-10-17.zip`; internal MANIFEST hashes match every bundled file. The child remains a separate quote with its existing four-layer 2oz requirements.
