# Full-load child power-path improvement targets

These are calculated design screens, not changes to CAD or approved production specifications. The owner confirmed three KST BLS505 servos, one DS565X, Hobbywing 120 A V4, 7.4 V, and both BEC power plugs. The second feed location, harness properties and accessory loads remain unbound. The 19.6 A case combines rounded upper-graph servo readings of 5/5/5/3.5 A with an assumed 1.1 A FC input. It is not a guaranteed maximum or a normal continuous flight load. The servos' high-torque duty limits still apply.

## Copper and barrel improvements

Fresh fixed-geometry network solves use the same exact child source b49ef4108ab0b85d4cd96fac22553e3bc16b214f5acde148a8680e1212097ee6. Conditions remain prescribed 80 C, 95% IACS, 0.075 mm sheet grid, 1.65 mm barrel length, 0.97 mm header-bore resistance sensitivity, B-side header injection, small main-load joint, illustrative matched dual 20 mOhm/conductor feeds. The actual CAD declares 70 um per face; 60 um is the conservative analysis assumption, not a supplier-guaranteed minimum.

| Actual sheet copper assumed on each face | Barrel wall assumed | Sheet loss | Barrel loss | Total child loss |
|---:|---:|---:|---:|---:|
| 60 um, baseline | 18 um | 0.385 W | 0.382 W | 0.767 W |
| 90 um | 18 um | 0.259 W | 0.380 W | 0.639 W |
| 120 um | 18 um | 0.195 W | 0.379 W | 0.574 W |
| 60 um | 25 um | 0.383 W | 0.275 W | 0.658 W |
| 60 um | 35 um | 0.380 W | 0.197 W | 0.577 W |
| 90 um | 25 um | 0.257 W | 0.273 W | 0.530 W |
| 120 um | 35 um | 0.193 W | 0.193 W | 0.386 W |

Reproduction: `full-load-options.py`; full numerical receipts: `full-load-options.json`. These change material parameters only. No new zones or vias were modeled. Thickness and plating are independent manufacturing acceptance requirements; nominal copper weight does not establish finished minimum thickness or barrel plating. Manufacturability/clearance must be rechecked before selecting heavier copper.

The present conservative model divides loss approximately equally between sheets and barrels. Doubling sheet copper alone saves only about 25% overall. Doubling both effective sheet and barrel conductance roughly halves dissipation; the 120/35 um scenario saves approximately 50%. This is a useful electrical objective, not proof that this material selection is necessary or thermally sufficient.

Layout work should prioritize a continuous, broad B.Cu VX path in parallel with the front bus and stronger B.Cu GND continuity, with distributed nearby power/return stitching. VX and GND need equal attention. In the baseline high-load model, each input barrel carries approximately 9.7-9.9 A. The TAIL GND plated-hole barrel carries approximately 7.12 A, despite a 3.5 A tail load, because it also transfers other return current between layer islands. That is an internal barrel current, not the tail mating-contact current. Ground stitching near that transfer and the feed pins is therefore a concrete candidate to investigate. The actual new pour/via geometry must be extracted and solved before specifying via count or promising this benefit. Real pin/solder conduction in parallel with the barrel is excluded in the conservative model and should be included or measured when qualifying the physical assembly.

Do not widen all main-board nets for the servo aggregate: the main branch carries FC/accessory demand only. The narrow retained child branch to the main joint is also modeled at 1.1 A rather than 19.6 A.

## Quantified electrical and thermal objectives

For this exact distributed 19.6 A allocation, the present child loss-equivalent resistance is P/I^2 = 2.00 mOhm. An illustrative board loss target of at most 0.4 W requires at most 1.04 mOhm loss-equivalent resistance, approximately half the present value. This metric is load-distribution-specific; it is not a unique feed-to-servo resistance or a local hotspot bound.

An illustrative ambient of 40 C and permitted rise of 20 C requires a lumped effective thermal resistance no greater than 20/0.767 = 26.1 C/W at baseline. At 0.4 W, the corresponding budget is 50 C/W. The board's actual thermal resistance is unknown. Hotspots, mounting, both PCB faces, header/lead heat conduction, main-board conduction, enclosure and airflow must be included. Temperature-dependent resistivity must be iterated with the thermal solution. Merely prescribing 80 C in a DC solver does not establish the rise. A 0.4 W target is an engineering starting point pending that analysis and physical measurement, not an established safe threshold.

For pulsed high load, calculate each conductor's RMS current and deposited energy, integral I(t)^2 R(T) dt, over the actual pulse duration and repetition. Use transient thermal response and minimum rail voltage. Average aggregate current alone misses independent branch heating and local return transfers. Full simultaneous upper-graph load is an electrical stress scenario, not permission to hold the servos near stall continuously.

## Complete full-load power path

If approximately 20 A is required continuously, the source must deliver at least that at the loaded 7.4 V rail after derating; a 25 A continuous design target would provide approximately 25% nominal current headroom but still requires environmental qualification. The present V4 is specified for 10 A continuous / 25 A peak. It cannot become a 20 A continuous source through PCB changes. For a short peak, compare its allowable peak duration/repetition and voltage regulation with the measured servo demand. [Manufacturer specification](https://www.hobbywingdirect.com/collections/clearance/products/platinum-120a-v4-esc).

At 19.6 A, matched dual feeds carry approximately 9.9 A/conductor and the illustrative unequal-lead case reaches 15.6 A. A single input path carrying the full design load needs an appropriately rated approximately 20 A or higher positive and return connection, with margin. If single-feed survival is a requirement, each remaining feed must independently meet the full requirement. Retained 3 A header contacts do not provide that documented rating. Individual output connections must also accommodate approximately 5 A cyclic / 3.5 A tail stress demand with an explicit duty rating and margin; copper changes do not change contact ratings. Both feeds must remain outputs of the same BEC, not unapproved parallel independent regulators.

As a separate illustrative harness target, allowing 0.2 V input-path drop at 20 A means total positive-plus-return equivalent resistance at most 10 mOhm. With two perfectly equal feed pairs in parallel, each pair would need at most 20 mOhm loop resistance. Actual sharing and hot resistance must be measured. Contact, cable, solder and PCB losses belong in the full calculation; the sheet/barrel numbers above omit contacts and output leads.

## Recommended next design calculation

Create a child-only candidate strengthening both rear power nets and their layer transitions, then compare it against the unchanged source under matched feeds, measured unequal feeds and the required feed-failure cases. Use accepted minimum copper/plating, the actual load waveform and a defined ambient/rise target. Select the lightest manufacturable copper option that meets voltage and hotspot limits, rather than ordering heavier copper solely from nominal current. No CAD edit or fabrication approval has been made in this calculation.
