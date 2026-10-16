# Stage35 saved USB verification and full-speed disposition

## Saved-source verification

Read-only KiCad 10.0.7 checks on the actual post-refill main PCB passed.

- PCB SHA256: `bf9a10563839b18071dedd1c4a71af60c25ac19e94f392adb1917955b1f4e95d`
- All 102 USB track/arc/via items and four tapers exactly match the v2 bevel + source-consistent alias candidate.
- All ten USB pad identities, UUIDs, coordinates, sizes, orientation and footprint side match that candidate. Every USB pad has direct physical same-net track contact on its copper side.
- Both native complementary-net lookups resolve: USB_DP ↔ USB_DN; PCB net codes remain 22/23.
- All four 0.08 mm bevels are present. Their new diagonals pass native foreign-pad/track/graphic collision checks at 0.127002 mm clearance.
- All four new diagonal centers and both edges project into the freshly saved In4 GND fill at <=0.010 mm sample spacing. The approximately 13.133168 mm matched In3 trunk on each net likewise has zero sampled In4 center/edge gaps.
- Closer In2 coverage remains nonuniform, unchanged from stage32 in the paired trunk. These sampled projections do not establish continuous return impedance or a field-solved differential impedance.
- The PCB hash is unchanged by these verification reads. No refill, board save or new DRC was run here; the parent owns the completed integrated native DRC/parity receipt.

Evidence: `saved-stage35-native-proof.json`, `saved-stage35-reference-projections.json`, `native-proof.log`, `reference-proof.log`. The read-only scripts are retained alongside the proof.

## Full-speed mismatch disposition

**Retain the current routing; do not add tuning meanders solely to erase the approximately 2.57 mm geometric mismatch.** No applicable numerical STM32F722 full-speed PCB skew violation has been established by the reviewed documentation. This is a qualified engineering decision, not certification of this board's USB signal integrity.

The used PA11/PA12 interface is OTG_FS. ST AN4879 Rev12 §2.2 identifies full-speed device operation as 12 Mbit/s. The F722 datasheet DS11853 Rev9 §6.3.29/Table86 gives 4–20 ns rise/fall times at its specified 50 pF load; the neighboring high-speed discussion is explicitly ULPI for STM32F722. Therefore 480 Mbit/s layout limits from other STM32 HS/MPU parts are not silently applied here. Sources: [AN4879](https://www.st.com/resource/en/application_note/an4879-introduction-to-usb-hardware-and-pcb-guidelines-using-stm32-mcus-stmicroelectronics.pdf), [exact STM32F722RE datasheet](https://www.st.com/resource/en/datasheet/stm32f722re.pdf).

Current AN4879 and F7 hardware guide AN4661 do not supply a numerical USB-FS PCB D+/D− length-mismatch limit applicable to this board. AN4661 §8.1 says impedance depends on geometry and the chosen stack/reference planes; its numerical SDMMC/FMC routing limits belong to those interfaces. AN4879's revision history records removal of its earlier FS routing/track-impedance sections in Rev3; superseded guidance is not presented as a current numerical acceptance requirement. Sources: [AN4661](https://www.st.com/resource/en/application_note/an4661-getting-started-with-stm32f7-series-mcu-hardware-development-stmicroelectronics.pdf), [AN4879 revision history](https://www.st.com/resource/en/application_note/an4879-introduction-to-usb-hardware-and-pcb-guidelines-using-stm32-mcus-stmicroelectronics.pdf).

The two orientation-specific planar differences remain 2.570456642 mm (A6/A7) and 2.496864761 mm (B6/B7). For scale only, 2.570 mm at a uniform propagation factor sqrt(4.6) corresponds to about 18.4 ps, less than 0.5% of the datasheet's 4 ns minimum edge. This equal-velocity calculation uses the declared dielectric value; it is **not extracted electrical skew** and excludes unequal layer environments, via barrels, package and connector behavior. It is not a pass/fail threshold.

The reversed A/B USB-C pad ordering requires local fanout/crossover handling but does not prove every millimeter of the observed mismatch is unavoidable. The fixed U7 input/GND escape and F1/VBUS copper block the specific shorter B.Cu candidates studied. No demonstrated benefit justifies expanding this correction into unrelated routing changes or added matching vias/meanders.

Retain normal release qualification: actual-stack impedance/reference and transition-return assessment, full-speed signal-quality testing and ESD testing, including both connector orientations. The measured geometric asymmetry alone is **not** an outstanding mandatory routing repair or evidence of failed USB operation.
