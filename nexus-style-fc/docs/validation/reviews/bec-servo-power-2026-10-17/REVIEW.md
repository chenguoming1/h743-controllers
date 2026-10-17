# BEC and servo current-budget calculation, 2026-10-17

## Result

**A 10 A continuous system rating is not established with the selected 3 A header contacts.** The exact child-board copper model gives relatively small resistive losses at 10 A, but the BEC entry contacts exceed their documented rating, including with two equal feeds. The owner has now confirmed three KST BLS505 cyclic servos, one KST DS565X tail servo, and a Hobbywing 120 A V4 at 7.4 V using both BEC power plugs. The second feed location and actual harness resistance are not yet bound.

### Confirmed KST setup

Both servos specify 6.0-8.4 V operation and 7.4 V rated voltage, so the selected 7.4 V BEC setting is within their stated range. The V4 provides 10 A continuous / 25 A peak BEC output; the ESC's 120 A motor rating is separate. See the primary Hobbywing source below.

Unlike the product-page text, both KST technical PDFs include a current-versus-torque graph. Visual readings near the upper plotted torque at 7.4 V are approximately 5 A per BLS505 and 3.5 A for the DS565X, rounded for this screen. They are not exact tabulated stall-current specifications, guaranteed upper limits or typical flight loads. These are the manufacturer's 2020/05 sheets currently linked from its product pages, downloaded and visually inspected on 2026-10-17.

| Load | Rounded upper-graph current screen at 7.4 V |
|---|---:|
| Three BLS505 cyclic servos | 3 x approximately 5 A = 15 A |
| One DS565X tail servo | approximately 3.5 A |
| Servos combined | approximately 18.5 A |
| Plus illustrative 1.1 A FC allowance | approximately 19.6 A |

The coincident upper-graph case exceeds the BEC's continuous rating but is below its stated 25 A peak rating. The permitted duration, repetition and output voltage at that peak are not established here. The actual load trace is needed to judge flight demand; simultaneous maximum-load current must not be treated as normal sustained current. Conversely, simply being below 25 A does not qualify a pulse.

A fresh 19.6 A constant-current stress solve gives maximum feed-conductor current 9.926 A for matched dual leads, 15.624 A for the unequal-lead case, and 19.6 A after losing a full feed. These far exceed the header's 3 A documented current rating. Each upper-graph servo demand also exceeds 3 A individually. This does not establish the retained contacts' unlisted short-pulse capability. Child copper/barrel loss is approximately 0.767 W with matched feeds, or 0.937-1.286 W with one feed, with 52-70 mV child-only worst servo-pad drop in the latter cases. These imposed-current calculations do not model the servo current changing as the supply sags, and do not establish safe temperatures.

KST specifies different control formats: BLS505 1520 us / 333 Hz; DS565X 760 us / 560 Hz. The tail must be configured for the DS565X format. No firmware setting was inspected or changed in this review.

Primary KST sources: [BLS505 product page](https://kstservos.com/products/bls505-8-4v-7kg-0-07sec-servo-heli-500-cyclic-brushless-hv-servo-motor) and its [technical PDF](primary-evidence/BLS505-technical-specification.pdf), SHA-256 `417fa7eec5b4e2a94109f7905fa3a9f4c3f334f75683b839c01c2dcbcf42778f`; [DS565X product page](https://kstservos.com/products/ds565x-8-4v-6kg-0-04sec-hv-digital-metal-gear-servo-motor) and its [technical PDF](primary-evidence/DS565X-technical-specification.pdf), SHA-256 `9a211c352ed55ec5675471405e312fb9f8ebb44b581395c5c3a797787517c3f5`. Original PDF download URLs are [BLS505](https://cdn.shopify.com/s/files/1/0570/1766/3541/files/BLS505_Technical_Specification.pdf?v=1713171211) and [DS565X](https://cdn.shopify.com/s/files/1/0570/1766/3541/files/DS565X_Technical_Specification.pdf?v=1700473658).

No CAD, CAM, BOM or CPL was changed. The current main PCB is `6295c7ebda6c8a4035064f235072d56e1d6e0ff1b7e6b0402f908ce372ae901e`; the child is `b49ef4108ab0b85d4cd96fac22553e3bc16b214f5acde148a8680e1212097ee6`.

## Actual power path

### Follow-up: PCB copper only

The owner clarified that the question concerns FC PCB traces rather than connector ratings. The main PCB does not carry the aggregate servo current through its VX trunk. The child carries that current; the main branches off for its own electronics and accessories. The matched dual-feed child calculation gives approximately 0.044 W sheet/barrel loss at 4.6 A total, 0.213 W at 10 A, and 0.767 W at the approximately 19.6 A imposed high-load screen. These are electrical-loss results, not temperature-rise or continuous-current ratings. The 19.6 A case cannot be declared thermally acceptable from the DC model alone.

A separate read-only main-positive-route screen on the current main source is retained in `main-vx-route-screen.json`. Using declared 35 um outer / 15.2 um inner copper, prescribed 80 C, 95% IACS, and assumed 18 um via walls, a connected single centerline route from the long J1 VX pad to U5 pad 13 is approximately 0.067 ohm; one to D5 pad 2 is approximately 0.092 ohm. If the full illustrative 1.1 A were applied to either branch separately, its route drop/loss would be approximately 74 mV / 81 mW or 101 mV / 112 mW. This treats each route alone; the board's parallel paths reduce network resistance. In operation the U5 and D5 branch currents split, and are not both the full 1.1 A allowance. These figures omit ground return, internal pad/solder resistance and the regulators; they are not full supply-loop predictions. They do not apply a 19.6 A servo current to the main trunk.

For the assumed FC load, the calculated trace losses are modest. The source does not establish actual accessory current or a thermal rating. A conclusion that the FC branch supports ordinary electronics load is distinct from approving sustained simultaneous near-maximum servo load on the child bus. No copper alteration is justified solely by the aggregate servo current being mistaken for main-trunk current.

The native child J1 is C32713294, Hanxia HX PZ2.54-3x7P ZZ. The columns are S1/S2/S3/TAIL/ESC/RPM/SBUS. Their positive pins are 2/5/8/11/14/17/20 and returns are 3/6/9/12/15/18/21. Servo power is direct VX, so every servo must tolerate the selected BEC voltage.

Aggregate servo current travels between the BEC and servo contacts through the child's continuous front VX copper and return copper. The main-board VX route branches off this bus and supplies the FC electronics/accessories. Recent main-board VX widening does not remove the child-header feed-contact limit.

Native main U5 is TPS62130RGTR on VX, with a nominal approximately 5.16 V output. Main U14 is TPS629210DRLR on VSYS, configured for 3.3 V. VSYS receives VX through D5 B5819WS. U10 TPS70933 supplies the sensor rail from VSYS. These are separate loads; servo power does not pass through the 5 V buck. TI's [TPS62130](https://www.ti.com/product/TPS62130) and [TPS629210](https://www.ti.com/product/TPS629210) are 3 A and 1 A converter ICs respectively. These IC output ratings do not establish the assembled board's available load or temperature margin.

## Fresh child-network calculation

`calculate.py` verifies all artifacts in the original child model seal and the current child source hash. It freshly solves the saved, condensed copper networks; no new copper mesh was needed because the child is byte-identical. The baseline reproduces the original result within 6.5e-13 V. The 20 new cases have a maximum linear residual below 8.8e-11 A. Full results are in `calculations.json`.

Screen conditions: 7.4 V source; prescribed 80 C conductor temperature; 60 um copper; 95% IACS; 18 um barrel wall; optional 1.65 mm barrel length and 0.97 mm header bore for barrel resistance only; 0.075 mm saved mesh; B-side header injection; fixed 1.1 A main load at the small child joint. Copper/plating/tolerance bounds are assumptions requiring fabrication acceptance. The current CAD declares 70 um per face on the child.

The 1.1 A main load is an illustrative allowance, not a measured upper bound. The total includes this allowance. The four synthetic servo allocations are 0.475/0.475/0.475/0.475 A, 1/1/1/0.5 A, 1.225/1.225/1.225/1.225 A, and 4.5/1/1/2.4 A. They are not predictions for unspecified servos.

| Total BEC load, including 1.1 A main | Highest feed-conductor current, matched leads | Highest feed-conductor current, unequal leads | Current after one full feed disconnects |
|---:|---:|---:|---:|
| 3.0 A | 1.519 A | 2.391 A | 3.0 A |
| 4.6 A | 2.330 A | 3.667 A | 4.6 A |
| 6.0 A | 3.039 A | 4.783 A | 6.0 A |
| 10.0 A | 5.064 A | 7.972 A | 10.0 A |

Matched leads use an illustrative 20 mOhm per conductor. The unequal case uses 20 mOhm per conductor in one pair and 80 mOhm in the other. These include illustrative lead/contact resistance; they are not measurements. Unequal sharing also occurs with matched external resistance because of board geometry and load placement. Both feeds are from the same BEC; this is not approval to parallel independent BECs. The second benchmark entry uses the SBUS column only as an unused power entry; actual port use, signal wiring and polarity must be established before adopting that arrangement.

| Single surviving feed at 10 A | Child board-only worst servo-pad drop | Child sheet and barrel loss |
|---|---:|---:|
| ESC | 29.809 mV | 0.258 W |
| SBUS | 38.883 mV | 0.348 W |

The one-feed cases are stress calculations, not permission to run 10 A through that connector. They exclude external input voltage drop when reporting board-only drop. With matched dual feeds at 10 A, board loss is 0.213 W. At 4.6 A total, single-feed board loss is 0.053-0.072 W and drop is 11.6-15.8 mV.

The model omits output servo leads/contacts, main-board copper and joint resistance, internal pin/solder parallel paths, within-land crowding, dynamic BEC response and thermal equilibrium. In particular, **80 C is an input to resistivity, not a prediction of temperature**. These values establish a resistive screen, not a safe continuous-current rating.

## Header and harness constraint

The exact retained manufacturer specification, section 5.2, says 3 A AC/DC; section 5.3 specifies contact resistance at most 0.02 ohm. Source: [retained manufacturer specification](../../child-b49ef410/verification/primary-evidence/header-C32713294-manufacturer.pdf); original [manufacturer drawing/specification](https://www.lcsc.com/datasheet/lcsc_datasheet_2407231541_hanxia-HX-PZ2-54-3x7P-ZZ_C32713294.pdf). The PDF SHA-256 is `b44606922b5eca64eafbe10a439688848635336dbf1bba66a53dd5ae916e88f8`. The actual mating female contact and harness remain unspecified.

One positive and one return in a plug both carry the full branch current; they do not add to a 6 A feed. Two plugs give a theoretical 6 A aggregate ceiling only at perfect 50/50 sharing, before derating and mating-contact limits. The fresh 6 A case already reaches 3.039 A in one conductor. At an 80/20 split, the 3 A rating alone limits aggregate current to 3/0.8 = 3.75 A; one surviving feed limits it to 3 A. These are rating arithmetic, not system qualification or recommended operating targets.

After subtracting the illustrative 1.1 A main allowance, those idealized servo budgets are 4.9 A (perfect sharing), 2.65 A (80/20) and 1.9 A (one feed), with no additional margin. Each individual servo's positive/return contact is separately subject to its contact/harness rating. The 4.5 A output stress case exceeds the retained header's 3 A rating too; a higher-current BEC input alone does not solve that output-contact concern.

For scale, if each positive and return interface is 20 mOhm, a pair dissipates I^2 * 0.04: at 3 A, 0.36 W and 0.12 V drop; at 5 A, 1 W and 0.20 V; at 10 A, 4 W and 0.40 V. Values above rating are illustrations, not extrapolated specifications. Wire resistance adds to this.

## BEC and electronics budget

The owner confirmed the Hobbywing 120 A V4 at 7.4 V with both power plugs. The Platinum 120A V4, SKU 30203401, [manufacturer specification](https://www.hobbywingdirect.com/collections/clearance/products/platinum-120a-v4-esc) lists a 5-8 V BEC, 10 A continuous / 25 A peak, and two BEC output wire pairs. No BEC peak duration is established; the product's separate 10-second motor-current specification must not be applied to the BEC peak rating.

At the actual loaded rail voltage:

`I_BEC = sum(I_servo) + P_5V/(efficiency_5V * V_VX) + I_VSYS_branch + other_VX_loads`

The VSYS branch includes the MCU buck input and sensor LDO input, with D5 loss. MCU output current cannot simply be added to BEC current without conversion. Avoid counting any downstream accessory twice. Voltage-dependent loads and the main input current must be checked at minimum loaded voltage, not just the programmed unloaded BEC setting.

Example only: two 5 V / 1 A accessories need 10 W. At 7.4 V and an assumed 90% buck efficiency, they consume 1.502 A from VX, **before** the FC/receiver/sensor loads. The corresponding input is 1.852 A at 6 V or 1.389 A at 8 V. If accessories are directly on the unmodified 5.16 V rail at 1 A each, use 10.32 W instead, giving 1.550 A at 7.4 V / 90%.

Thus the 1.1 A main allowance is inadequate for that two-accessory example. An 8.9 A servo allocation plus those nominal-5 V accessories is already 10.402 A at 7.4 V / 90%, before FC and receiver consumption; even lossless conversion gives 10.251 A. A nominal 10 A BEC cannot sustain that allocation by its continuous rating, independently of the connector issue.

## What is needed to finish the actual setup assessment

- Location of the second BEC feed, wire lengths/gauges, measured branch resistances and mating-contact part/rating.
- Startup/simultaneous loaded servo current and minimum delivered voltage for this actual mechanical setup, including peak duration and repetition.
- Receiver and 5 V accessory loads, plus main-board input current at the intended firmware/peripheral configuration.

For an intended 10 A continuous design, the feed interface needs an appropriately rated power connection or a separately rated servo power-distribution path. Individual high-current servo output connections need corresponding qualification. Keeping this header requires bounding actual sustained/contact currents and validating the actual harness and transient voltage/temperature under representative simultaneous loads. No powered bench test or flight qualification was performed here.
