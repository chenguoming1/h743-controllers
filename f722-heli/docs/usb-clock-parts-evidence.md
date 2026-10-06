# USB, BOOT and HSE component evidence

Research date: 2026-10-04, approximately 16:33–16:46 UTC. Read-only sourcing and engineering research; no order placed and no CAD changed by this research task.

## Recommended population

| Function | Exact manufacturer / MPN | JLC code | Qty | Observed stock / available order quantity |
|---|---|---:|---:|---:|
| USB-C receptacle | GCT USB4105-GF-A-120 | C5184243 | 1 | 3,886 / 2,473 |
| BOOT switch | C&K KMT031NGJLHS | C221708 | 1 | 2,521 / 2,521 |
| HSE crystal | YJX TAXM8M4RDBCCT2T | C400090 | 1 | 189,901 / 181,234 |
| D+, D−, CC1, CC2 ESD | onsemi ESD9M5.0ST5G | C242267 | 4 | 16,097 / 15,976 |
| CC pull-downs | UNI-ROYAL 0402WGF5101TCE, 5.1 kΩ 1% | C25905 | 2 | 5,949,844 / 5,267,472 |
| BOOT0 pull-down | UNI-ROYAL 0402WGF2201TCE, 2.2 kΩ 1% | C25879 | 1 | 2,218,193 / 1,819,919 |
| Initial HSE load capacitors | FH 0402CG150J500NT, 15 pF, C0G, 5%, 50 V | C1548 | 2 | 1,430,641 / 1,276,841 |

Stock was read from the actual public JLC detail pages on the research date; for USB -060 the visible cloud-browser page independently showed the same fields as the downloaded public HTML. The larger “In Stock” count and smaller “Available Order Qty” are distinct. These are snapshots, not reserved inventory or a quotation. Live page links:

- [USB -120](https://jlcpcb.com/partdetail/5849584-USB4105_GF_A120/C5184243)
- [BOOT switch](https://jlcpcb.com/partdetail/C221708)
- [HSE crystal](https://jlcpcb.com/partdetail/TAXM8M4RDBCCT2T/C400090)
- [Signal ESD](https://jlcpcb.com/partdetail/C242267)
- [CC resistors](https://jlcpcb.com/partdetail/26648-0402WGF5101TCE/C25905)
- [BOOT resistor](https://jlcpcb.com/partdetail/C25879)
- [HSE capacitors](https://jlcpcb.com/partdetail/0402CG150J500NT/C1548)

## 1. USB-C connector and exact KiCad footprint

Select `Connector_USB:USB_C_Receptacle_GCT_USB4105-xx-A_16P_TopMnt_Horizontal` for **USB4105-GF-A-120**. The installed KiCad 9 footprint explicitly lists -060, standard, and -120 variants in its tags. Its 2D layout was compared with the GCT drawing. The variant changes shell-stake length, not the contact/slot layout. The catalog's “12P” description counts physical solder tails: the connector has 16 USB contacts, with paired power/ground contacts sharing four tails.

Primary references:

- [GCT product page](https://gct.co/connector/usb4105)
- [GCT drawing](https://gct.co/files/drawings/usb4105.pdf), also [GCT drawing mirrored by LCSC](https://datasheet.lcsc.com/datasheet/pdf/76718c6dacc0a6125953c12b5ebc82df.pdf?productCode=C3025063)
- [GCT product specification, A3](https://gct.co/files/specs/usb4105-spec.pdf)
- Installed KiCad footprint: `/usr/share/kicad/footprints/Connector_USB.pretty/USB_C_Receptacle_GCT_USB4105-xx-A_16P_TopMnt_Horizontal.kicad_mod`

The following coordinates are extracted from the installed KiCad footprint, in millimetres, before board rotation. All contact pad centres have y = −3.680. The mating opening faces +Y; the footprint PCB-edge guide is y = +3.675.

| Pad identifiers | x | Pad width × length | Connect to |
|---|---:|---:|---|
| A1 and B12, coincident | −3.200 | 0.60 × 1.15 | GND |
| A4 and B9, coincident | −2.400 | 0.60 × 1.15 | USB_VBUS |
| B8 | −1.750 | 0.30 × 1.15 | SBU2, explicit no-connect |
| A5 | −1.250 | 0.30 × 1.15 | CC1 |
| B7 | −0.750 | 0.30 × 1.15 | D− |
| A6 | −0.250 | 0.30 × 1.15 | D+ |
| A7 | +0.250 | 0.30 × 1.15 | D− |
| B6 | +0.750 | 0.30 × 1.15 | D+ |
| A8 | +1.250 | 0.30 × 1.15 | SBU1, explicit no-connect |
| B5 | +1.750 | 0.30 × 1.15 | CC2 |
| A9 and B4, coincident | +2.400 | 0.60 × 1.15 | USB_VBUS |
| A12 and B1, coincident | +3.200 | 0.60 × 1.15 | GND |

All four shield/stake pads are numbered S1. Rear centres are (±4.320, −3.105), 1.00 × 2.10 copper lands, 0.60 × 1.70 plated slots. Front centres are (±4.320, +1.075), 1.00 × 1.80 lands, 0.60 × 1.40 plated slots. Two non-plated locating holes are Ø0.65 at (±2.890, −2.605). Preserve the through-hole copper and paste attributes; do not replace the slots with plain SMT pads.

Footprint body rectangle is 8.94 × 7.35; courtyard 10.64 × 8.94. GCT drawing height is 3.31 above PCB. Include connector and any overhang, rather than only Edge.Cuts, in the 41.3 × 25.4 × 13.1 mm assembled-envelope audit.

### Stake length and 1.0 mm nominal PCB

The -060 part C3025063 was also available (1,169 stock / 486 orderable), but is not preferred for this design. Drawing stake lengths are 0.60 ±0.15 mm (-060), 0.95 ±0.15 mm (no suffix), and 1.20 ±0.15 mm (-120). At exactly 1.0 mm PCB thickness, -120 protrudes 0.05–0.35 mm; -060 remains recessed by 0.25–0.55 mm. These are derived geometric values before PCB-thickness tolerance or solder standoff.

**A 1.0 mm nominal board with ±0.1 mm tolerance does not guarantee positive bottom protrusion at the worst combined tolerance:** 1.05 − 1.10 = −0.05 mm. The longer part nevertheless offers substantially better barrel engagement. Do not describe recessed-tail acceptance as manufacturer-approved: the reviewed documents give no such approval or minimum PCB thickness. Request assembler DFM review for the plated-slot paste/solder process, solder fill and mechanical retention. If positive protrusion is mandatory, constrain maximum finished PCB thickness or reconsider 0.8 mm; do not silently change the agreed stackup.

**Latest stackup update:** the layout team's live JLC check found six-layer stackup **JLC06101H-3313**, nominal 1.0 mm, calculated finished thickness **1.03 mm ±10%**, superseding the earlier provisional 1.2 mm public-document minimum. At 1.03 mm the nominal -120 stake projection is 0.17 mm. Combining 1.20 ±0.15 mm stake tolerance with 0.927–1.133 mm finished-board thickness gives −0.083…+0.423 mm projection, before solder standoff. Thus positive projection is still not guaranteed; retain the assembler DFM gate for plated-slot fill and retention. The GCT ordering grid does not document -150 or -240 stake options; no such stock item was verified. See the project stackup evidence for the live fabrication choice.

GCT's A3 product specification supports convection reflow and tests 20,000 mating cycles. These connector-level tests do not qualify the finished PCB for helicopter vibration. Keep all four stakes electrically and mechanically anchored; verify actual solder joints and insertion-load behavior on prototypes.

### Outer GND land-to-locator clearance assessment, 18:33 UTC

The actual board and installed KiCad footprint already use **roundrect** SMT lands, with `roundrect_rratio 0.25`; the 0.60 mm-wide outer GND lands therefore have a **0.15 mm corner radius**. They are not rectangular. Four placement-DRC violations represent two physical lands: coincident A1/B12 and A12/B1, each 0.60 × 1.15 mm, next to the unchanged Ø0.65 mm NPTH locating holes. The reported clearance is 0.1944 mm against a 0.2000 mm rule.

Using the footprint coordinates above, the corner-to-hole geometry gives `clearance(r) = sqrt((0.010+r)^2 + (0.500+r)^2) - r - 0.325`, in millimetres. This reproduces the reported 0.194403 mm at r = 0.15. A proposed smaller r = 0.06 would reduce clearance to 0.179358 mm. The exact radius threshold for 0.200000 mm clearance is 0.175468 mm; r = 0.18 yields only 0.201045 mm.

**Recommended minimal adaptation:** increase the radius to **0.20 mm**, `roundrect_rratio 0.333333333`, on all four named outer GND pad objects, keeping their dimensions and centres. Predicted clearance is **0.205821 mm**. The additional area removed from each of the two physical lands is `(4−π) × (0.20²−0.15²) = 0.015022 mm²`, or **2.24% of its existing copper/paste area**. The final land retains 95.02% of the rectangular bounding area. Both duplicate pad objects at each location must be changed so their union has the intended outline.

This preserves the GCT drawing's recommended land extents, terminal alignment, both locator-hole sizes/positions, and all four shell stakes. Rounded SMT lands are already used by the standard KiCad footprint. Increasing their corner radius is a reasonable small fabrication adaptation; GCT does not explicitly approve this altered corner shape. It is preferable here to changing locator fit or shortening the solder land. The 0.200 mm fabrication rule is a nominal CAD constraint, not proof of tolerance-free as-built spacing. Re-run DRC after the authorized CAD change and include the custom shape in assembler review. This research assessment did **not** change CAD. Primary comparison: GCT drawing page 1, “Recommended PCB Layout”; local evidence: `validation/placement-drc.json` and `hardware/f722-heli.kicad_pcb`.

## 2. USB electrical/protection topology

Use `Connector:USB_C_Receptacle_USB2.0_16P` or a project symbol with the exact pad names above. Join A6 to B6 at the receptacle and route D+ to **STM32F722RE PA12, pin 45**. Join A7 to B7 and route D− to **PA11, pin 44**. Budget routing space for both orientations rather than leaving B6/B7 unconnected. Keep branch stubs short, use a continuous return plane, and obtain differential geometry from the actual stackup.

CC1 (A5) and CC2 (B5) each have a separate 5.1 kΩ pull-down and separate ESD diode. Do not join them. SBU1/A8 and SBU2/B8 are unused. This is a USB 2.0 device/sink port without PD negotiation. Passive Rd does not authorize an arbitrary current draw. [ST AN5225](https://www.st.com/resource/en/application_note/an5225-usb-typec-power-delivery-using-stm32-mcus-and-mpus-stmicroelectronics.pdf)

### Preferred ground-only ESD

Fit four onsemi **ESD9M5.0ST5G** devices: D+, D−, CC1, CC2. Pin 1 is cathode to the signal; pin 2 is anode to GND. KiCad `Diode_SMD:D_SOD-923` has pad 1 at (−0.42, 0), pad 2 at (+0.42, 0), each 0.36 × 0.25 mm. Its 1.20 mm overall land span matches onsemi case 514AB. This is a single-line shunt protector, not an inline two-terminal series device. Place near connector with short ground returns and no long shunt stubs.

The onsemi part is specified for high-speed interfaces including USB, 2.5 pF maximum capacitance, 5 V working reverse voltage, 9.8 V maximum clamp at 1 A 8/20 µs, and ±10 kV contact/±15 kV air ESD. Its ground-only topology avoids steering signal current into connector VBUS when the MCU is BEC-powered and the USB host is absent/unpowered. [onsemi primary datasheet, Rev 9](https://www.onsemi.com/download/data-sheet/pdf/esd9m5.0s-d.pdf)

**This does not provide VBUS surge protection.** Use a separate VBUS TVS and the power sheet's input-current limiting/reverse-blocking arrangement. Select its standoff voltage against the allowed USB input range; do not substitute the 5 V signal protector indiscriminately.

### USBLC6 option researched, not preferred population

ST USBLC6-2SC6, C7519, was available at 47,405 stock / 43,520 orderable. Its exact map is 1↔6 = I/O1, 3↔4 = I/O2, 2 = GND, 5 = VBUS. The intended USB application ties pin 5 to USB VBUS and uses local 100 nF. Generic VCC applications exist, so “3.3 V is forbidden” would be unjustified; however no explicit USB 3.3 V-bias qualification was established in this review. The BEC-powered, no-VBUS-sense topology can backfeed absent VBUS through its upper steering diodes, so use the ground-only option above. [ST primary datasheet](https://www.st.com/resource/en/datasheet/usblc6-2.pdf)

STM32F722 DS11853 Rev 9 p169 says external DP/DM termination resistors are unnecessary because the embedded driver includes matching impedance. Use direct traces, or 0 Ω tuning positions if retained; do not automatically fit 22 Ω. The project reserves PA9 for stock UART TX1, so no normal hardware VBUS sensing is assumed. Prototype tests must include BEC-only operation with an unpowered host, because ESD topology alone does not guarantee correct firmware D+ attach/detach behavior. [STM32 primary datasheet](https://www.st.com/resource/en/datasheet/stm32f722rc.pdf)

## 3. BOOT switch footprint

**C&K KMT031NGJLHS, C221708** meets the strict complete-part size envelope. Manufacturer catalog PDF page 14 (printed B–16) gives 3.0 mm nominal body length, 2.6 mm body width, 3.4 ±0.1 mm overall lead span, and 0.65 ±0.07 mm height. It is top-actuated, normally open, IP68, 3.4 N nominal force. Its silver-contact specification calls for at least 1 mA switching current. A 2.2 kΩ BOOT0 pull-down draws approximately 1.5 mA while pressed at 3.3 V; connect the switch from BOOT0 to 3V3. [C&K manufacturer catalog distributed by Farnell, pp13–14](https://www.farnell.com/datasheets/2969021.pdf)

Custom footprint, top/component view and origin at centre:

- Four 0.65 × 0.70 mm rectangular copper/paste/mask lands
- Centres: (−1.475, −0.950), (+1.475, −0.950), (−1.475, +0.950), (+1.475, +0.950)
- Outer land rectangle 3.60 × 2.60 mm, inner gaps 2.30 × 1.20 mm
- The two upper pads form one terminal; the two lower pads form the other
- The drawing does not prescribe pin numbers. Assign duplicate pad `1` to the upper pair and duplicate pad `2` to the lower pair, consistently with the two-pin schematic switch
- No ground terminal: `NGJ` is the no-ground-pin J-lead variant
- Keep at least a 1 mm diameter accessible actuator contact area; provide a practical finger/probe-access region in layout

Do not use the initially researched XUNPU TS-1088-AR02016 C720477 if 4 × 3 mm applies to the entire component: its nominal body is 4 × 3 × 2 mm but terminal span is 4.8 ±0.3 mm. [XUNPU manufacturer drawing mirror](https://storage.googleapis.com/graviton-electric-symbols/document_assets/lcsc/2409302330_XUNPU-TS-1088-AR02016_C720477.pdf)

## 4. 8 MHz HSE design

YJX **TAXM8M4RDBCCT2T** is a fundamental 8 MHz passive crystal, CL 10 pF ±10%, ESR ≤250 Ω, C0 ≤7 pF, ±10 ppm initial tolerance, ±15 ppm temperature stability over −40…+85°C, ±5 ppm/year aging. Package is 3.2 × 2.5 × 0.70 ±0.10 mm. Electrical terminals are 1 and 3; 2 and 4 are grounded case pads. [Exact YJX manufacturer sheet](https://datasheet.lcsc.com/lcsc/1912111437_Yajingxin-TAXM8M4RDBCCT2T_C400090.pdf), [inspected PDF mirror](https://storage.googleapis.com/graviton-electric-symbols/document_assets/lcsc/1912111437_Yajingxin-TAXM8M4RDBCCT2T_C400090.pdf)

The manufacturer's 1.4 × 1.2 mm recommended pads match installed KiCad `Crystal:Crystal_SMD_3225-4Pin_3.2x2.5mm`: pad 1 (−1.1,+0.85), 2 (+1.1,+0.85), 3 (+1.1,−0.85), 4 (−1.1,−0.85). Use `Device:Crystal_GND24`, never a four-pin powered-oscillator symbol. Connect between PH0/OSC_IN (MCU pin 5) and PH1/OSC_OUT (pin 6), with one load capacitor from each node to local ground. Put an optional series-resistor tuning footprint at OSC_OUT, initially 0 Ω.

### Calculated compatibility and remaining qualification

STM32F722 supports HSE 4–26 MHz and specifies maximum crystal critical transconductance of 1 mA/V (DS11853 Rev 9 Table 40). Using the [ST AN2867 oscillator-design equation](https://www.st.com.cn/resource/en/application_note/an2867-oscillator-design-guide-for-stm8afals-stm32-mcus-and-mpus-stmicroelectronics.pdf):

`gmcrit = 4 × ESR × (2πf)^2 × (C0 + CL)^2`

- CL = 10 pF: gmcrit = 0.730 mA/V
- CL = 11 pF worst specified load: gmcrit = 0.819 mA/V

Both are below the MCU's 1 mA/V maximum-crystal-critical-transconductance limit. This limit is already a crystal criterion; it is not the raw oscillator gm and must not be divided by five again.

Start with two 15 pF C0G capacitors (FH C1548). Their series equivalent is 7.5 pF; assuming 2.5 pF effective pin/layout stray gives 10 pF total load. This stray assumption is a design estimate, not a measured property. Keep loops short, locally grounded, and away from switching/servo-current paths. Tune after layout/prototype frequency measurement.

**Qualification gate:** the YJX sheet states a 10 µW drive level without an unambiguous maximum. Verify crystal drive current, startup margin and start time on the actual board across voltage/temperature and component tolerances; adjust series resistance/load if needed. A high series resistor can improve drive but reduce startup margin, so do not choose one from a guessed formula and call the design qualified. The selection is electrically plausible and sourceable, not hardware-validated.

An alternate researched lower-ESR family was HCI 0132M4-8.000F10DTNM C51822710, stock 442/orderable 441. The JLC listing gives 100 Ω and 10 pF, but the available [generic HCI sheet](https://www.hcixtal.com/uploads/44524/files/0132M4.pdf) omits an 8 MHz ESR row. It was therefore not chosen as a more strongly verified replacement.

## 5. ROM DFU, bootloader UART scan, and stock USB attachment

### F722 ROM DFU entry

The documented F72xxx/F73xxx ROM USB configuration uses PA11/DM and PA12/DP in forced-device mode, with an internal D+ pull-up. PA9 is listed for USART1 TX, not DFU. Keep the present PA9 no-connect. HSE must be an integer MHz frequency in 4–26 MHz; **8 MHz is explicitly preferred over 25 MHz**. This establishes documented compatibility, not measured enumeration. [ST AN2606 Rev 70, §44/Table 97, pp228–232](https://www.st.com/resource/en/application_note/an2606-stm32-microcontroller-system-memory-boot-mode-stmicroelectronics.pdf#page=228)

Hold BOOT0 high through power-up/reset, with **BOOT_ADD1 = 0x0040**. This is the factory system-bootloader setting. Verify it during commissioning; pressing BOOT without reset does not select ROM. The project exposes NRST at TP5. [ST RM0431 Rev 4, §1.9 and boot-address option bytes, pp62/78](https://www.st.com/resource/en/reference_manual/rm0431-stm32f72xxx-and-stm32f73xxx-advanced-armbased-32bit-mcus-stmicroelectronics.pdf#page=62)

### Complete ROM UART RX comparison

Table 97 lists only USART1 and two USART3 pin locations. Its ROM UART RX inputs are **PA10, PB11, and PC11**. PB11 and PC11 receive internal pull-ups; PA10 receives no internal pull. USART2/4/6 are not listed. [ST AN2606 Rev 70, Table 97, p229](https://www.st.com/resource/en/application_note/an2606-stm32-microcontroller-system-memory-boot-mode-stmicroelectronics.pdf#page=229)

Actual connectivity was checked in the exported `validation/development.net` against the project's MCU symbol and stock target configuration on 2026-10-04:

| GPIO / package pin | Actual schematic connection | ROM status | Additional DFU pull-up |
|---|---|---|---|
| PA10 / U1.43 | DSM_RX_MCU → R38 22 Ω → DSM_RX_EXT/J12; D7 signal ESD | USART1 RX, no pull | **Recommend one 100 kΩ to +3V3_CORE** |
| PB11 / U1.29 | PORT_C_TX_MCU → R35 22 Ω → PORT_C_TX_EXT/J11; U15 ESD | USART3 RX, internal pull-up | None needed for an otherwise undriven line |
| PC11 / U1.52 | Explicit no-connect; no other net nodes | Alternate USART3 RX, internal pull-up | None |
| PC7 / U1.38 | PORT_B_TX_MCU → R33 22 Ω → PORT_B_TX_EXT/J10; U14 ESD | Not scanned by this ROM | None for DFU |
| PA3 / U1.17 | SBUS_MCU → R45 220 Ω → SBUS_LV; existing R37 4.7 kΩ pull-up | Not scanned by this ROM | None |

PA2/RPM likewise is outside this ROM UART scan and already has its translated-input pull-up. Stock port names do not redefine ROM pin functions: Port C TX/PB11 becomes a ROM receive input during bootloader detection, while Port B TX/PC7 is not a bootloader UART resource.

**Smallest justified external set: one 100 kΩ resistor from DSM_RX_MCU to +3V3_CORE, on the MCU side of R38.** ST recommends defined levels on unused bootloader RX inputs and gives 100 kΩ as a typical USART pull-up. [AN2606 §4.3, pp47/49](https://www.st.com/resource/en/application_note/an2606-stm32-microcontroller-system-memory-boot-mode-stmicroelectronics.pdf#page=47) This biases the otherwise disconnected DSM input high and adds only about 33 µA when driven low at 3.3 V. It neither inverts the data nor changes the stock resource assignment. This is a recommendation; no resistor or CAD change was made by this research task.

Weak pulls prevent floating inputs; they cannot override an actively transmitting receiver or guarantee DFU selection under arbitrary attached-peripheral traffic. Use USB-only service power with BEC disconnected, and disconnect or quiet external serial equipment. Additional external pulls on PB11/PC11 are unnecessary for the documented idle case. Validate recovery with representative cables and peripherals before calling it deterministic in service.

### Practical limitation of stock firmware with self-power

The copied classic target identifies firmware commit **ba6c7e3e328b91a549bf6ca87c9eadd7006b6d94**. Its F7 USB FS setup explicitly disables hardware VBUS sensing in [usbd_conf_stm32f7xx.c, line 405](https://github.com/rotorflight/rotorflight-firmware/blob/ba6c7e3e328b91a549bf6ca87c9eadd7006b6d94/src/main/vcp_hal/usbd_conf_stm32f7xx.c#L405); [serial_usb_vcp.c, line 263](https://github.com/rotorflight/rotorflight-firmware/blob/ba6c7e3e328b91a549bf6ca87c9eadd7006b6d94/src/main/drivers/serial_usb_vcp.c#L263) starts the USB device. These files were read from that exact upstream commit, not inferred from the ROM behavior. Later firmware revisions require a fresh check.

This board supplies no connector-VBUS sense signal to firmware. PC2 monitors the peripheral 5 V rail, which can be present from BEC power and therefore does not establish host VBUS presence. With BEC power maintained, the USB device can remain attached through its D+ pull-up while host VBUS is absent or lost. Ground-only data ESD and power-path reverse blocking do not implement USB attach/detach control.

**Do not claim self-powered USB compliance for this stock configuration.** ST distinguishes bus-powered service, where separate VBUS sensing is unnecessary, from self-powered operation, which requires VBUS-aware attachment. [AN4879 Rev 12, §2.6 and §3.1, pp11–14](https://www.st.com/resource/en/application_note/an4879-introduction-to-usb-hardware-and-pcb-guidelines-using-stm32-mcus-stmicroelectronics.pdf#page=11) Normal enumeration may still work, but BEC-only/unpowered-host and VBUS-removal behavior need bench qualification. Meeting the self-powered attachment requirement would require a suitable VBUS-aware hardware/firmware arrangement; adding a wire to PA9 alone does not make the unchanged stock code use it.

## Release checks specific to this block

1. Verify all 16 named USB contacts and four S1 stakes survive symbol/footprint transfer with the intended nets
2. Verify D+ and D− connections in both connector orientations and enforce separate CC pull-downs
3. Confirm ground-only signal ESD polarity and a separate VBUS TVS; test BEC-only and USB-only power paths for backfeed
4. Approve -120 stake/barrel engagement and soldering process against the selected 1.03 mm ±10% finished-board thickness; re-run land-to-NPTH DRC after the proposed outer GND corner-radius adaptation
5. Verify BOOT0 reaches valid high when pressed and low when released; use the specified KMT0 land orientation
6. Measure HSE frequency, drive level, startup and USB stability before claiming operational compatibility
7. Recheck orderable inventory and exact suffixes immediately before a future assembly order
