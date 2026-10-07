# B-RID all-net width review

Current PCB SHA-256: `349fbe54c6d95591bcbd5b6ae21f348d2a8d77a581d6df7f8176709179ab2ae4`

VBUS input-feed correction: implemented at 0.30 mm on both specified segments

Reviewed all 41 routed nets / 688 segments against fresh schematic connectivity. This is a fresh geometry audit against the listed source revision.

## Current-candidate verification

- Exact PCB hash above freshly checked against the file after native refill
- Native reports: **0 DRC violations / 0 unconnected items / 0 schematic-parity issues / 0 ERC violations**
- Independent route comparison against post-VSYS/pre-cleanup checkpoint `67c5c4cb0c9721c38d4762978856360dcfa65dc7c1dc7b3afc11aa58e2138ad6`: **692 → 688 tracks**
- Two equal-width collinear merges and two fully contained redundant fragments preserve the actual cleanup copper. Exact integer capsule/interval checks establish this without a mesh or approximate polygon tolerance
- Only the two specified VBUS feed segments widen, from 0.15 to 0.30 mm; no other net has a width change
- All 104 vias, 311 pads, 60 footprint placements, 3D model associations/transforms, outline and zone definitions match the pre-cleanup checkpoint
- USB/RF, ground returns, VSYS, BAT+ and both switching-node track geometries match exactly
- Native 3V3 fill remains one In2 island containing all 20 via centers
- Fresh USB/RF reference-plane sample results are identical to the pre-cleanup checkpoint. There are no USB uncovered samples away from intentional signal-via antipads; the existing antenna through-hole antipad behavior is unchanged

Evidence: corresponding files under `evidence/routing-cleanup-20261007/`. The inherited ignored native check categories were not changed by this routing cleanup.

## Width decisions

Keep intentional differences between power trunks, short pad escapes, local plane-backed supplies and low-current branches. The only identified additional width correction is the 2.211 mm F.Cu VBUS feed into U3; its two segments should be 0.30 mm. USB remains 0.135 mm, RF remains 0.150 mm, and the VSYS bridges retain 0.60/0.80 mm.

The VBUS change reduces this local nominal trace resistance from about 7.26 to 3.63 mOhm (35 um copper, rho=1.724e-8 Ohm m), approximately 1.82 mV less drop at a 0.5 A screen. This is a modest margin/consistency improvement, not proof that the old geometry failed and not a thermal rating.

GNSS C8-to-U2 B1 VCC uses approximately 3.154 mm of 0.15 mm outer trace, about 10.4 mOhm before plane/via effects, versus the manufacturer guidance to avoid more than 0.2 Ohm added series resistance. V_IO C9 has a 1.960 mm local 0.15 mm link. UART widths are independent of RF feed impedance.

There are 73 segments shorter than 0.20 mm. Preserve real bends, pad/via landings and branch anchors; only merge exactly collinear equal-width chains or remove proved-contained redundant copper.

## All routed nets

| Net | Segments | Width mm: count / length mm | <0.20 mm | Role and decision |
|---|---:|---|---:|---|
| /3V3 | 91 | 0.150: 38 / 45.967; 0.200: 34 / 30.273; 0.250: 10 / 26.521; 0.300: 9 / 10.367 | 9 | Plane-backed supply and local control/feedback branches. Keep mixed 0.15/0.20/0.25/0.30 mm widths. One In2 plane connects 20 vias. U4.1 is VOUT; U4.10 is FB; U6.1 is SEL. VOUT-to-C6 is 0.30 mm/1.360 mm; C6-to-plane via is 0.30 mm/1.055 mm. GNSS local supply fanout may remain 0.15 mm. |
| /BAT+ | 40 | 0.200: 30 / 34.171; 0.250: 4 / 2.240; 0.300: 1 / 1.000; 0.450: 5 / 13.381 | 5 | Battery charge/discharge feed plus high-impedance divider branch. Keep 0.45 mm In2 main feed, 0.30 mm connector escape and short 0.20/0.25 mm charger links. The long 0.20 mm branch terminates at R13=1 MOhm and is not a high-current feed. With 15.2 um inner and 35 um outer copper, 0.45 mm inner has similar section to 0.195 mm outer. |
| /BATT_NTC | 9 | 0.200: 9 / 25.800 | 0 | Thermistor sense. Uniform 0.20 mm; low-current temperature sensing. |
| /BAT_DIV | 20 | 0.150: 20 / 11.333 | 9 | Divider and reservoir capacitor. Uniform 0.15 mm; high-impedance analog branch, not battery power. |
| /BAT_SENSE | 27 | 0.150: 27 / 25.985 | 0 | ADC input. Uniform 0.15 mm; retain. |
| /BOOT_IO9 | 2 | 0.200: 2 / 3.539 | 0 | Boot GPIO/test pad. Uniform 0.20 mm; retain. |
| /BUCK_EN | 25 | 0.200: 25 / 49.075 | 1 | Converter enable control. Uniform 0.20 mm; U4.6 enable and 100k pulldown, not converter supply current. |
| /CC1 | 3 | 0.200: 3 / 2.237 | 0 | USB Type-C configuration. Uniform 0.20 mm to 5.1k pulldown; not controlled-impedance data. |
| /CC2 | 6 | 0.200: 6 / 6.823 | 0 | USB Type-C configuration. Uniform 0.20 mm to 5.1k pulldown; not controlled-impedance data. |
| /CHARGE_ACTIVE | 26 | 0.150: 21 / 24.194; 0.200: 5 / 2.632 | 2 | Isolated charger status GPIO. 0.20 mm local MOSFET/pullup and 0.15 mm GPIO route are intentional low-current branches; no blanket normalization. |
| /CHG_N | 27 | 0.150: 27 / 15.659 | 4 | Charger open-drain status. Uniform 0.15 mm status/LED sink and MOSFET gate path. |
| /ESP_EN | 6 | 0.200: 6 / 5.568 | 0 | MCU enable RC/test pad. Uniform 0.20 mm; retain. |
| /GNSS_RX | 23 | 0.150: 23 / 26.080 | 3 | GNSS UART receive. Uniform 0.15 mm; retain. |
| /GNSS_TX | 31 | 0.150: 10 / 12.086; 0.200: 21 / 19.440 | 6 | GNSS UART transmit. 0.15 mm compact receiver route transitions to 0.20 mm main UART route. This is low-current digital signaling, not RF. Do not shrink useful copper merely to match widths. |
| /ILIM | 6 | 0.200: 6 / 4.940 | 0 | Charger input-current programming resistor. Uniform 0.20 mm programming input, not charging-current conductor. |
| /ISET | 5 | 0.150: 5 / 6.198 | 0 | Charger charge-current programming resistor. Uniform 0.15 mm programming input, not charging-current conductor. |
| /L1 | 4 | 0.230: 1 / 0.850; 0.500: 3 / 2.928 | 0 | Converter switching node to inductor. Keep 0.23 mm x 0.85 mm QFN escape then 0.50 mm; no layer transition. Preserve compact switching loop and inductor restriction. |
| /L2 | 4 | 0.230: 1 / 0.650; 0.400: 3 / 3.128 | 0 | Converter switching node to inductor. Keep 0.23 mm x 0.65 mm QFN escape then 0.40 mm; no layer transition. Preserve compact switching loop and inductor restriction. |
| /LED_CHG_A | 12 | 0.150: 12 / 9.327 | 4 | Current-limited charge indicator anode. Uniform 0.15 mm after 3.3k; schematic label approximately 0.9 mA. |
| /LED_G | 7 | 0.200: 7 / 11.926 | 0 | GNSS indicator GPIO to resistor. Uniform 0.20 mm; current-limited indicator. |
| /LED_G_A | 14 | 0.150: 14 / 14.072 | 0 | Current-limited GNSS indicator anode. Uniform 0.15 mm after 1k; schematic label approximately 1.2 mA. |
| /LED_R | 9 | 0.200: 9 / 11.915 | 0 | RID indicator GPIO to resistor. Uniform 0.20 mm; current-limited indicator. |
| /LED_R_A | 8 | 0.150: 8 / 15.847 | 0 | Current-limited RID indicator anode. Uniform 0.15 mm after 1k; schematic label approximately 1.2 mA. |
| /LED_S_A | 13 | 0.150: 13 / 10.263 | 0 | Current-limited system indicator anode. Uniform 0.15 mm after 1k; schematic label approximately 1.2 mA. |
| /PGOOD_N | 8 | 0.200: 8 / 10.031 | 0 | Charger power-good GPIO. Uniform 0.20 mm; open-drain status/pullup. |
| /RES_F9 | 5 | 0.150: 5 / 3.539 | 0 | GNSS reserved-pin termination. Uniform 0.15 mm; preserve stipulated termination. |
| /RES_PAIR | 1 | 0.150: 1 / 0.500 | 0 | GNSS reserved-pin tie. Uniform 0.15 mm; preserve stipulated pin tie. |
| /RF_ANT | 4 | 0.150: 4 / 3.459 | 0 | Controlled-impedance GNSS antenna feed. Protect all 0.150 mm RF50 feed/tuning traces; no width or geometry change. |
| /RF_IN | 6 | 0.150: 6 / 2.911 | 0 | Controlled-impedance GNSS receiver feed. Protect all 0.150 mm RF50 feed/tuning traces; no width or geometry change. |
| /RTC_UNUSED | 3 | 0.150: 3 / 2.713 | 0 | GNSS unused RTC termination. Uniform 0.15 mm; preserve termination. |
| /STRAP_IO2 | 4 | 0.200: 4 / 7.221 | 0 | Boot-strap GPIO. Uniform 0.20 mm; low-current pullup. |
| /STRAP_IO8 | 1 | 0.150: 1 / 1.480 | 0 | Boot-strap GPIO. Uniform 0.15 mm; low-current pullup. |
| /USB_500_EN | 33 | 0.150: 33 / 18.600 | 13 | Charger USB current-mode logic. Uniform 0.15 mm; logic, not USB supply current. |
| /USB_D_CONN_N | 25 | 0.135: 25 / 30.125 | 0 | Controlled-impedance connector USB data. Protect 0.135 mm USB90 geometry, differential spacing, topology and reference planes. |
| /USB_D_CONN_P | 26 | 0.135: 26 / 31.390 | 1 | Controlled-impedance connector USB data. Protect 0.135 mm USB90 geometry, differential spacing, topology and reference planes. |
| /USB_D_N | 10 | 0.135: 10 / 3.408 | 3 | Controlled-impedance MCU USB data. Protect 0.135 mm USB90 geometry, differential spacing, topology and reference planes. |
| /USB_D_P | 10 | 0.135: 10 / 3.277 | 3 | Controlled-impedance MCU USB data. Protect 0.135 mm USB90 geometry, differential spacing, topology and reference planes. |
| /USB_SUSPEND | 10 | 0.150: 10 / 15.214 | 0 | Charger suspend logic. Uniform 0.15 mm; control, not USB power. |
| /VBUS | 37 | 0.150: 6 / 10.290; 0.200: 11 / 4.366; 0.250: 5 / 1.799; 0.300: 7 / 5.975; 0.450: 8 / 19.465 | 2 | USB input power, ESD rail and indicator/status branches. Only targeted correction: F.Cu (117,100.9)->(116.25,101.65)->(116.25,102.8), total 2.210660 mm, should be 0.30 mm instead of 0.15 mm. This carries U3 IN current. Keep downstream 0.15 mm branches to 3.3k LED/100k status pullup, 0.20 mm IC escape and 0.45 mm In2 trunk. |
| /VSYS | 44 | 0.200: 22 / 18.924; 0.230: 2 / 0.850; 0.250: 5 / 4.323; 0.300: 1 / 1.253; 0.400: 2 / 2.035; 0.600: 6 / 9.570; 0.800: 6 / 7.789 | 6 | Charger output/system input feed plus controls. Preserve rebuilt 0.60 mm source/VINA bridges and 0.80 mm VIN bridge with named-group width rule, backed local pin escapes and 0.20 mm controls. |
| GND | 43 | 0.150: 13 / 5.705; 0.200: 24 / 22.452; 0.250: 1 / 0.901; 0.300: 2 / 1.900; 0.400: 3 / 5.762 | 2 | Reference planes, power/thermal and signal returns. Intentional 0.15 through 0.40 mm local connections. Preserve converter, RF and USB returns, all thermal/return vias and planes. |

## Manufacturer basis and limits

- [TI BQ24074, layout §12.1](https://www.ti.com/lit/ds/symlink/bq24074.pdf): distinguish high-current paths and low-current ground connections; keep capacitor loops short
- [TI TPS63031, layout §11.1](https://www.ti.com/lit/gpn/tps63031): wide, short main power paths and suitable power/control returns
- [u-blox MIA-M10Q integration manual §4.1](https://content.u-blox.com/sites/default/files/documents/MIA-M10Q_IntegrationManual_UBX-21028173.pdf): supply roles and 0.2 Ohm added-series-resistance guidance
- [u-blox MIA-M10Q datasheet](https://www.u-blox.com/sites/default/files/documents/MIA-M10Q_DataSheet_UBX-22015849.pdf): startup supply capability up to 100 mA

Circuit-role data is reconciled to the fresh netlist and the manufacturer references above. No heavy mesh or transient simulation is used. Fabrication tolerances, thermal behavior, battery/charger qualification and prototype tests remain separate gates. Native ERC/DRC/connectivity/parity and preservation were freshly checked for the exact delivered hash above.
