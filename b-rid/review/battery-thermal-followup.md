# Battery and autonomous temperature-interlock follow-up

7 October 2026. Battery qualification research; no supplier contact or purchases. The component report is `component-qualification.md`. No complete compact pack/thermistor pairing was verified for unrestricted charging release.

## Concrete sourcing choices

1. **Compact lead: KBT-602535PL**, protected 500 mAh, 35×25×6 mm, manufacturer states **2C maximum continuous discharge = 1 A**. No built-in NTC or charge-temperature window is documented on its product page, and the page's sold-out/add-to-cart display is ambiguous. It remains a supplier-confirmation lead. https://www.kbt18650battery.com/products/kbt-602535pl-3-7v-500mah-li-polymer-rechargeable-battery
2. **Smaller lead: KBT-602035PL**, protected 380 mAh, 35×20×6 mm, manufacturer states **2C continuous = 760 mA**, about 8 g. This fits the desired footprint class and reduces runtime relative to 500 mAh. It also lacks a qualified temperature/NTC specification, has a two-wire connector, and needs a pulse/load test near depletion even though the stated current rating is above the initial 650 mA estimate. https://www.kbt18650battery.com/products/kbt-602035pl-3-7v-380mah-li-polymer-rechargeable-battery-with-2pin-2-54-jst-connector
3. **Documented larger fallback only: TinyCircuits ASR00012**, protected 1000 mAh, 40±3×30±2×8±0.5 mm, 1 A maximum discharge, charging 0–50°C, discharge −10–60°C, 2-pin JST-SH. Direct public listing showed 75 available; Mouser showed 310. It needs an external thermistor and qualified three-wire harness. Its sheet specifies maximum charging voltage as exactly 4.20 V, whereas BQ24074 regulation can reach 4.23 V; written allowance for that normal charger tolerance is still needed. Sources: https://tinycircuits.com/products/lithium-ion-polymer-battery-3-7v-1000mah and https://files.tinycircuits.com/Datasheets/ASR00012_1000mAh.pdf

The original LiPol LP412550 is the best-documented exact three-wire/NTC candidate but remains limited to 500 mA continuous and 0–45°C charging. Do not infer cell pulse capability from its 2–4.5 A protection trip. A seemingly helpful Power-Xtra PX602535 retailer claim of “1.5 A” was rejected: the manufacturer sheet states only **1C = 500 mA** maximum continuous discharge, 0–45°C charging. Source: https://www.power-xtra.com/uploads/content/900869503136-dspdf.pdf?v=1561376348 (search-indexed manufacturer sheet; direct PDF currently returned 404)

## Native BQ24074 TS proof

The current TI datasheet §9.3.6, p30, explicitly says its illustrated Rs/Rp network cannot tighten the native thermistor window, only extend it. A different thermistor R/T characteristic can produce a different native window, but “10 kΩ” alone does not establish compatibility.

For guaranteed fault detection at the two temperature boundaries, use the full charger limits:

- Cold at 0°C: minimum external TS resistance must exceed VCOLD(max)/INTC(min) = 2.2 V /72 µA = **30.556 kΩ**
- Hot at the allowed maximum: maximum external TS resistance must be below VHOT(min)/INTC(max) = 0.270 V/78 µA = **3.462 kΩ**

A direct 10 kΩ, B3950 thermistor with assumed ±1% R25 and ±1% beta gives a latest hot trip of approximately **51.5°C**, with earliest cold trip about **1.4°C**, using the beta approximation. That is not bounded inside a 0–50°C pack rating. The calculation is only a screen; final design must use manufacturer R/T bounds rather than one constant beta across the whole range.

A high-beta 10 kΩ thermistor plus a parallel resistor can move this toward a narrower useful range. Exact stocked TDK B57331V2103J060 has B25/50=4390 K, R25±5%, beta±3%, 4,566 listed at DigiKey. Its manufacturer-authored catalog identifies R/T curve8503. However the available tolerance envelope leaves very little room at 0°C and 50°C with a roughly430 kΩ shunt; it provides no defensible thermal-contact/aging margin. I did **not** qualify it as a final harness choice. A tight-tolerance high-beta sensor or a bounded separate interlock remains necessary. Source: https://mm.digikey.com/Volume0/opasdata/d220001/medias/docus/1138/B57311_21_31.pdf ; stock https://www.digikey.com/en/products/detail/tdk/B57331V2103J060/739858

An exact sensor assembly must specify R/T min/max over the charge boundary range, resistance/beta tolerances, attachment materials and thermal lag, isolation, lead routing, and strain relief. It must remain thermally coupled to the actual cell. No board-temperature-only substitute was approved.

## Proposed TLV7042 circuit: important blockers

The steady-state polarity is correct: cold comparator IN+=cold reference, IN−=NTC node; hot comparator IN+=NTC node, IN−=hot reference. With open-drain outputs tied together, an open NTC raises the sense node to VBUS and trips cold; a short trips hot. Healthy-high then drives the proposed N-MOSFET to pull CE low.

**Startup is not fail-safe in the proposed form.** TLV7042's POR holds outputs **high impedance**, which the pull-up converts to “healthy,” enabling the CE transistor before the comparators are valid. The 200 µs power-up figure is typical, with no maximum shown. A simple assumed RC delay therefore does not prove safety. A push-pull TLV7032 alternative has POR-low outputs, but they cannot be wire-ANDed; two series enable FETs or another correct AND stage would be needed.

TLV7042 operates at 1.6–6.5 V; its input common-mode range reaches the positive rail plus 0.1 V. Dual-device offset is ±8 mV maximum and hysteresis 3–25 mV in the published conditions. The precision table covers 1.8–5 V and specifies common mode at midrail; a guaranteed aggregate offset at 5.5 V and the actual thresholds was not established. Source: https://www.ti.com/lit/ds/symlink/tlv7042.pdf

For engineering comparison only, biasing a B3380 10 kΩ NTC through10 kΩ and using cold reference10 kΩ(top)/24.9 kΩ(bottom) and hot18.7 kΩ(top)/10 kΩ(bottom) produces nominal trips near3°C/42°C. Enumerating ±1% resistor and R25 corners, VBUS4.75–5.5 V, and an intentionally conservative signed33 mV comparator allowance gives:

- Assumed beta±1%: cold0.90–4.65°C; hot40.21–44.74°C
- Assumed beta±3%: cold0.45–5.02°C; hot39.90–45.17°C

The pack does not publish beta tolerance, and neither range includes attachment/thermal-lag error. Thus the suggested3°C/42°C circuit is **not qualified**. Do not replace the pack TS connection with a fixed10 kΩ resistor until the independent interlock is actually proven. The corner script is `thermal_screen.py`.

## Timer and charge-current choices

TI BQ24074 floating TMR gives4/5/6 hours minimum/typical/maximum fast-charge time. With RISET=5.90 kΩ±1%, KISET limits797–975 AΩ yield charge current about **134–167 mA**. A 1 Ah pack already needs7.48 hours of ideal constant-current charging at the low-current corner, before the CV tail. Floating TMR is unsuitable for that pairing.

Within the documented18–72 kΩ timing range:

| RTMR ±1% | Fast timer minimum | Typical | Maximum |
|---|---:|---:|---:|
|52.3 kΩ|5.18 h|6.97 h|8.80 h|
|69.8 kΩ|6.91 h|9.31 h|11.75 h|
|71.5 kΩ|7.08 h|9.53 h|12.04 h|

Even the maximum supported range does not establish full 1 Ah charging at the existing151 mA setting. If the larger fallback were selected, **RISET3.57 kΩ±1% gives221–276 mA**, nominal249 mA, and RTMR69.8 kΩ gives a plausible retained-safety-timer starting point. Minimum-current idealCC duration becomes4.52 hours; confirm actual CV tail, PowerPath load sharing, charge temperature, and thermal throttling in first-article testing. This is not a committed CAD change.

For the compact380–500 mAh class at151 mA, a longer RTMR such as52.3 kΩ provides useful margin without disabling the timer, subject to the actual pack's charge profile. Grounding TMR disables the safety timer per TI, but removes that independent safeguard and is not recommended merely to accommodate an oversized pack. The dynamic timer behavior can extend wall-clock time during limiting, but should not be used to justify an inadequately sized nominal timing window.

Source for native TS/current/timer parameters: https://www.ti.com/lit/ds/symlink/bq24074.pdf

## Release decision

Keep the compact design and label the battery/harness as a real procurement-and-safety gate. KBT602035PL/602535PL are concrete compact leads, LP412550 is the documented three-wire low-current lead, and ASR00012 is a larger documented fallback. None is yet a fully bounded drop-in pack for the present charger and harness. Supplier confirmation and prototype validation are needed; no order or outreach was made.
