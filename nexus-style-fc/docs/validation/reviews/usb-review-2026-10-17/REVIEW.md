# Current USB routing review — 2026-10-17

**Recommendation: retain the present routing for the next prototype. No mandatory USB reroute is established by this review. Do not add length-matching meanders or extra signal vias solely to remove the measured asymmetry. Production impedance/reference qualification remains open.** This is an engineering disposition, not a demonstrated USB electrical compliance result or a board fabrication release.

Follow-up: the [source-bound 90 ohm sensitivity calculation](../usb-impedance-2026-10-17/REVIEW.md) estimates variable local impedance and shows a material difference between the saved CAD stack and JLC's current standard stack. It does not qualify this routing as controlled 90 ohm.

Source: `hardware/nexus-style-fc.kicad_pcb`, SHA-256 `6295c7ebda6c8a4035064f235072d56e1d6e0ff1b7e6b0402f908ce372ae901e`. Checked read-only with KiCad 10.0.6. No PCB, project, schematic, Gerber, or routing settings were changed by this review.

## Fresh checks

- Native DRC: **0 routing/manufacturing violations and 0 unconnected items**. Ten schematic-parity footprint-name/filter issues remain on unrelated parts; none concerns the USB connector, ESD device, MCU, or USB nets. See `drc.json`.
- Actual U1 is **STM32F722RET6**. PA11/U1.44 is USB_DN; PA12/U1.45 is USB_DP. This is the integrated full-speed port. ST identifies OTG_FS device operation as 12 Mbit/s. Its F722 datasheet specifies full-speed rise/fall times of 4–20 ns at the stated 50 pF load, with integrated output matching. No external termination resistors are added by this review. [ST AN4879 supported speeds](https://www.st.com/content/st_com/en/technical-documents/an4879-introduction-to-usb-hardware-and-pcb-guidelines-using-stm32-mcus-stmicroelectronics_asset/chunk-002-topic-an4879-supported-usb-speeds.html), [F722 datasheet, Table 86](https://www.st.com/resource/en/datasheet/stm32f722re.pdf).
- Native complementary-net lookup resolves USB_DP ↔ USB_DN. All ten USB pads physically contact same-net tracks. Both USB-C orientations reach the MCU in the endpoint graph. Cutting the corresponding external 2.3 mm U7 bridge breaks both orientation paths; no copper bypass around the protection path was found. This does not qualify mounted ESD performance.
- The In3 paired trunk has approximately 13.133 mm of 0.170 mm copper on each net. Long parallel sections have 0.297 mm center spacing, hence 0.127 mm edge clearance. Connector, ESD and MCU breakouts use 0.150 mm traces and are not continuously coupled.

## Complete path geometry

| Orientation | D+ planar witness | D− planar witness | D+ excess | Used D+/D− vias |
|---|---:|---:|---:|---:|
| A | 32.693 mm | 30.041 mm | 2.653 mm | 4 / 3 |
| B | 34.431 mm | 31.892 mm | 2.539 mm | 5 / 4 |

All four paths traverse 2.9952 mm of copper-center-to-copper-center barrel distance in the **declared CAD stack**, despite the unequal via counts. Unused barrel stubs, pads, package, connector and protection-device delay remain unmodeled. These are geometric witness lengths, not extracted signal skew. The endpoint graph includes straight taper axes, straight pad-center connections and tiny straight links between overlapping copper endpoints offset by ≤0.005 mm; it does not trim every copper overlap. Consequently these values should not be equated exactly with the older stage35 path convention.

For scale only, the larger planar difference corresponds to approximately 19 ps at an assumed uniform propagation factor √4.6. This is less than 0.5% of the datasheet's 4 ns minimum edge, but **is not a compliance threshold or an extracted delay**. No applicable numerical full-speed PCB mismatch violation has been established. High-speed 480 Mbit/s rules from other interfaces are not silently imposed. Extra meanders would add copper and discontinuities without a demonstrated benefit here.

## Reference and impedance limitations

Fresh saved-fill sampling checks each track center and both copper edges at ≤0.010 mm midpoint steps. The entire paired In3 trunk projects into saved In4 GND with **zero sampled gaps**. This is useful reference coverage evidence; it is not a continuous return-current, finite return-contact, or inductance proof.

The closer In2 GND reference is nonuniform: approximately 4.736 mm of D+ and 3.623 mm of D− trunk centerline lack projected In2 GND; considering either edge raises those values to 5.213 and 4.208 mm. The two references are at different dielectric distances (In2: 0.1532 mm; In4: 0.5500 mm). The 2.514 mm D+ In1 connector join has no projected F.Cu GND above it, and partial In2 coverage below it. Breakout gaps around signal vias and connector pads also require transition analysis. Do not treat each projected gap as a proven disconnected ground path.

Nearest GND-via center distances are approximately 1.17–2.36 mm across the USB signal vias. Distance alone does not establish low-inductance return paths; shield pads and other ground copper may participate. No additional GND via is prescribed solely from this distance metric.

**The route cannot currently be certified as uniformly 90 Ω.** The physical stack and copper environments, rather than the project's unused router defaults, determine impedance. Confirm the actual production stack and evaluate covered and uncovered In2 sections plus the connector crossover. If that analysis or USB full-speed electrical testing shows a problem, prioritize a more consistent ground-reference corridor and simpler connector transitions; select width/gap from that verified stack. Changing only width or adding tuning cannot resolve this uncertainty. [TI USB layout discussion](https://www.ti.com/video/6087491555001), [TI differential-pair guidance](https://www.ti.com/document-viewer/lit/html/SSZTCR1).

The next verification is actual-stack impedance/transition assessment and USB full-speed operation/signal-quality testing in **both connector orientations**, followed by the intended ESD qualification. None was performed in this software review.

## Evidence and reproduction

`check_current_usb.py` writes `current-usb.json`; `check_saved_references.py` takes PCB path and output JSON arguments and writes `current-reference-projections.json`. Run with KiCad's bundled Python. `drc.json` comes from `kicad-cli pcb drc --schematic-parity --format json`; no refill/save was requested. The saved source SHA was verified unchanged after all reads.
