# F722 support for the selected KST and Hobbywing setup

7 October 2026. The user has confirmed BLS815 cyclic servos and the Hobbywing 200 A **SBEC** version. The installation assumption is three BLS815 cyclic servos and one BLS805X **or** BLS905X tail servo. This review uses the documented Platinum HV 200A SBEC V4.1 topology; it does not substitute the OPTO model. No CAD, firmware or physical wiring was changed.

**Recommended design setting: 7.4 V BEC, with both supplied BEC feed paths used and current sharing analyzed.** This voltage fits all three servo models and the F722 electronics input. Configure the cyclic and tail outputs for their different pulse protocols. The exact final95 two-feed electrical analysis is complete. Physical work remains: measure actual lead/contact behavior, qualify thermal/pulse limits and resolve the servo signal-level guarantee.

## Voltage and exact wiring

Hobbywing publishes 5–8 V adjustable BEC output, default 7.4 V, with 10 A continuous/30 A peak capacity. Its main throttle cable carries white=signal, red=BEC positive and black=ground. The additional red/brown BEC lead connects to the same internal output. The manual recommends that extra lead go to an available FBL power/channel connection when the FBL permits it. It gives no peak duration or current-sharing guarantee. [Official SBEC/OPTO V4.1 manual, page 1, §§03, 04 and 06](https://www.hobbywing.com/en/uploads/file/20221015/a728560821bb05490636413c693a115f.pdf)

For the existing F722 raw-header pinout, the required connections are:

| Connection | Pin 1 GND | Pin 2 VX_RAW | Pin 3 signal |
|---|---|---|---|
| J6 ESC, main throttle/BEC lead | Black | Red, 7.4 V | White throttle |
| J8 SBUS, auxiliary BEC lead, **only if SBUS is unused** | Brown | Red, 7.4 V | Empty cavity |
| J7 RPM, supplied yellow-only signal lead | Empty | Empty | Yellow RPM signal |
| J2/J3/J4 cyclic and J5 tail | Servo brown | Servo red | Servo orange |

The J8 option assumes a UART receiver installation leaving the raw SBUS header unused. Do not connect the auxiliary 7.4 V lead to a regulated 5 V JST-GH receiver port. The main flight battery connects to the ESC's heavy battery leads; it does not connect to the F722 raw header.

The Hobbywing wiring drawing shows a three-cavity auxiliary housing with two wires, but it is monochrome and supplies no numbered mating-face pinout. Therefore the **electrical mapping above is specified, while factory plug polarity must be checked from its actual colored wires before mating**: red on the center raw-positive contact, brown on GND, remaining signal cavity empty. The drawing does not establish a finished-plug mechanical envelope or contact rating.

Two feeds are two paths from the same BEC, not two independent BECs. Their resistance and landing positions determine current division. Equal sharing, a doubled current rating and continued full-load operation after losing one lead are not assumed. The previous Harwin 3 A connector was only a dimensional reference; it is neither the verified Hobbywing lead nor verified Nexus hardware.

## Servo requirements and document versions

| Model and source | Printed issue | Supply | PWM and electrical limits | Current evidence |
|---|---|---|---|---|
| BLS815 V8, current product-linked sheet [1] | 2022/05 | 6–8.4 V, rated 7.4 V | 1520 µs/333 Hz; 900–2100 µs; HIGH 3.3–5.0 V, LOW 0–1.5 V | At 7.4 V, approximately 1.1 A at the green region's 4 kgf·cm edge and 4.5 A near the 17 kgf·cm curve endpoint |
| BLS815 V2, general manual-index sheet [2] | 2021-1 | 6–8.4 V, rated 7.4 V | 900–2100 µs; HIGH 3.3–5.0 V, stricter LOW 0–0.5 V; 22 AWG cable stated | Different plot: approximately 1.4 A at the 5 kgf·cm green edge and 4.1 A near 17 kgf·cm |
| BLS805X, current product-linked sheet [3] | 2020-02 | 6–8.4 V, rated 7.4 V | 760 µs/560 Hz; 450–1050 µs; HIGH 3.3–5.0 V, LOW 0–1.5 V | Approximately 2.3 A at 6.5 kgf·cm; green region roughly 0.5–0.6 A |
| BLS905X, current product-linked sheet [4] | 2020-02 | 6–8.4 V, rated 7.4 V | Same tail protocol and signal limits as BLS805X | Approximately 2.4 A at 7 kgf·cm; green region roughly 0.5–0.6 A |

[1: BLS815 V8 specification, p1](https://cdn.shopify.com/s/files/1/0570/1766/3541/files/BLS815_V8.0_Technical_Specification.pdf?v=1700473913), [2: BLS815 V2 specification, pp2–3](https://cdn.shopify.com/s/files/1/0570/1766/3541/files/BLS815_v2.0-2021424-104432300.pdf?v=1660889845), [3: BLS805X specification, p1](https://cdn.shopify.com/s/files/1/0570/1766/3541/files/BLS805X_Technical_Specification.pdf?v=1713150470), [4: BLS905X specification, p1](https://cdn.shopify.com/s/files/1/0570/1766/3541/files/BLS905X_Technical_Specification.pdf?v=1709113577)

The [current BLS815 product](https://kstservos.com/products/bls815-digital-20kg-metal-gear-0-07sec-rc-brushless-standard-servo) identifies V8 as cyclic; 805X/905X are tail models. The [older 805X](https://cdn.shopify.com/s/files/1/0570/1766/3541/files/BLS805X-201719-113339763.pdf?v=1660889551) and [older 905X](https://cdn.shopify.com/s/files/1/0570/1766/3541/files/BLS905X.pdf?v=1678938113) sheets linked by KST's general manual page have **no printed issue date**. Both retain 6–8.4 V and 760 µs/560 Hz but omit current graphs and logic limits. Their PDF metadata says 2015-05-21; that is not a printed revision or proof of an existing servo's hardware version. Omission of a logic limit in the old sheet does not establish a more permissive limit.

For new support work, use the current product sheets; keep the V2 LOW requirement of ≤0.5 V if supporting that version too. Do not infer an existing unit's revision from today's download link. All current sheets specify −10 to +65°C; the older BLS815 V2 sheet says −20 to +65°C. The whole installation is not rated for the PCB resistance model's assumed 105°C copper.

**Signal-level issue:** an MCU rail nominally called 3.3 V does not prove a guaranteed output HIGH of at least 3.3 V after rail tolerance, GPIO loss and ground movement. Conversely, a buffer powered by the F722 peripheral rail can exceed the servo sheet's 5.0 V HIGH maximum because that rail can exceed 5.0 V. The final driver must meet both ends, plus the applicable LOW limit. Actual servo input capacitance/leakage is not specified in these sheets. No new buffer choice or compatibility pass is claimed here.

## Concrete current cases at 7.4 V

The manufacturer plots distinguish a green continuous region, a short-time region marked under 10 seconds/repeat, and an overload region marked under 1 second with 60 seconds cooldown. They provide **approximate plotted operating currents**, not guaranteed worst-case startup/stall currents, tolerances or waveform rise times. Curves stop near the colored boundary; do not extrapolate them to a maximum current guarantee.

Use these specific comparison profiles for the three-cyclic/one-tail installation:

| Profile | Cyclic currents J2/J3/J4 | Tail current J5 | Servo subtotal |
|---|---|---:|---:|
| Moderate simultaneous motion, inside the plotted green regions | 1 / 1 / 1 A | 0.5 A | 3.5 A |
| One heavily loaded cyclic, other two active, heavily loaded 905X tail | 4.5 / 1 / 1 A, permuted across cyclic ports | 2.4 A | 8.9 A |
| All three cyclics near their V8 plotted endpoints, 805X tail | 4.5 / 4.5 / 4.5 A | 2.3 A | 15.8 A |
| All three cyclics near their V8 plotted endpoints, 905X tail | 4.5 / 4.5 / 4.5 A | 2.4 A | 15.9 A |

These are engineering comparison cases, not guaranteed device bounds. Add the **newly solved electronics demand at 7.4 V**, with the intended A/B/C and DSM loads, before comparing with the BEC and entry paths. The old 5 V electronics maximum cannot be presented as a same-state 7.4 V prediction.

The 15.8/15.9 A servo-only cases already exceed the BEC's 10 A continuous specification. They are not sustained operating targets. The 30 A BEC peak figure does not establish that these loads are supported for ten seconds, one second or any chosen pulse duration. Nor does it assign a 30 A rating to either cable, header or PCB. Startup, synchronized reversal, all-servo stall and loss of a feed still require bounded waveform/fault criteria; neither the KST curves nor the ESC manual supplies a guaranteed envelope for all of them.

The [completed exact-board review](final-electrical-review.md) includes the 7.4 V J6/J8 model, unequal positive/return path resistances, each feed missing in turn, and the stated profiles/peripheral loads. A current limit that causes loss of required servo voltage does not make an undersized path compatible. Retain prototype tests for thermal rise, pulse response and real harness retention, while correcting any driver or entry-path design limit exposed before fabrication.

## Reconciled OPTO distinction

The original [Platinum 200A HV V4 OPTO manual, p1](https://www.hobbywing.com/en/uploads/file/20221025/e28a72957d07d72c1c063cb1229e520f.pdf) prints 20161227 and has no BEC. Its throttle red wire is a 5–8 V **input** for the optical-coupler circuitry. That is not the confirmed SBEC installation. It would need external regulated power; a fully charged 8.4 V 2S pack would exceed that stated input range. The combined V4.1 manual also lists an OPTO variant separately with no auxiliary BEC wire. No OPTO wiring assumption is carried into the selected SBEC design.

All source PDFs and inspection images remain outside the shareable folder. The source manifest records URLs, file hashes and printed dates. The F722 pin mapping is retained in the final95 paired project, PCB 4da0708a4795662cc32b035a0783c70b9bdb85fc386bd4d39af33385b175667f. Its exact-board numerical current assessment is complete; physical current, contact, pulse, temperature, fit and signal-level qualification remain open.
