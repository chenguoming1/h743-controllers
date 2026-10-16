# Compact two-layer child power and matched-fit prototype

**Status: implemented engineering prototype, not a fabrication, assembly, thermal, current-capacity, or flight release.** This is the selected child direction. The separate main-board placement correction must be integrated and rechecked before a coherent final pair is released.

## Result

The child retains its 22.4 × 11.0 mm total outline envelope, 8.4 mm body above the seat, standard 3×7 / 2.54 mm servo header, signal functions and polarity. Its front VX copper is now one continuous saved region connecting all seven supply contacts. The front GND region is also continuous. The back has five separate GND regions; the analysis preserves their actual links through tracks and finite plated barrels rather than pretending they are one plane.

The ESC signal crossing moved from front to back. The former 0.50 mm ESC-to-RPM VX back-layer V-bridge was removed. The affected SBUS-to-RPM ground link moved to the front, where it joins the return sheet. Three ordinary 0.60/0.30 mm VX vias connect the main-board branch to the front VX sheet. There is no filled/capped-via process or solder-reinforced conductor assumption.

This eliminates the first prototype's remaining mandatory shared VX bridge. No new feed connector, special servo plug, external support part, changed servo lead, or BEC harness adapter is selected.

## Exact source and rollback

- Selected child PCB SHA-256: `b49ef4108ab0b85d4cd96fac22553e3bc16b214f5acde148a8680e1212097ee6`
- Matching main in this snapshot, before the separate placement correction: `f39eba3ca14a833fb534a0ef133824923f67c515f60f7e81335c8d31ef0541fc`
- Sealed stage10 source remains unchanged: main `2099ceb9ff904859a68e288683ee68b2ad74d7741b8b670341baf67bf67e1ea3`; child `bfec2a120fbda6c97c1f8a36dfff6a35337e13ab1c3af63abb987f529d761403`.
- The earlier compact copper and matched-fit candidates are preserved in adjacent directories as rollback. The taller XT30/Nano-Fit experiment is not selected and must not be fabricated or mistaken for this design.

## Copper and fabrication assumptions

Selected manufacturer/process direction: JLCPCB two-layer FR-4, nominal 2 oz copper on both faces and ENIG. Public 2 oz two-layer trace/space minimum is 0.16/0.16 mm. This candidate uses a stricter 0.20 mm minimum track, 0.16 mm clearance, 0.254 mm copper-to-edge, 0.25 mm hole-to-copper and hole-to-hole, and 0.15 mm via annulus. Signal vias remain 0.60/0.30 mm; the three new power vias use the same dimensions.

The PCB file declares 70 µm copper per face, 1.44 mm core and 10 µm mask per face. Its nominal declared stack sum is 1.60 mm; the actual KiCad VRML envelope including rendered mask is 1.625 mm. These are CAD declarations, not a promise about the delivered laminate or coating thickness.

The current model uses two explicit scenarios: nominal 70 µm at 20°C and a conservative proposed acceptance screen of 60 µm at 80°C, 95% IACS conductivity. **A guaranteed 60 µm finished minimum was not established from the public JLC source.** Require agreement/coupon evidence or rerun at the supplier's guaranteed minimum. Plated barrels are screened at 18 and 20 µm wall thickness. The JLC explanatory plating article distinguishes average plating from thinnest-point plating; it does not certify this future batch.

The native rules are more conservative than the allowed F722 minima where the selected 2 oz process requires it. No rule was relaxed or warning suppressed to obtain a clean error count.

The exact Hanxia drawing recommends finished PCB holes of 1.02 ±0.05 mm. The preserved 1.00 mm nominal header drill is within that nominal recommendation, but delivered finished holes and actual pin tolerances still require supplier acceptance/inspection; ordinary fabrication tolerances must not be silently equated to the drawing tolerance. The electrical calculation uses nominal bore dimensions unless explicitly noted in an addendum.

## Electrical model and load envelope

The full source-bound calculation, cases and assumptions are in the sealed `verification/power/V2-POWER-REVIEW.md` and accompanying machine-readable evidence. It solves actual saved copper at 0.10 and 0.075 mm grids, with separate front/back annular-land terminals and finite plated barrels. Both-face injection sensitivity is included. Ideal equipotential copper lands are a stated simplification; header pin, contact, solder-joint, cable, dynamic BEC response and temperature equilibrium are not thereby qualified.

The target benchmark is 10 A aggregate at the PCB distribution network, not 10 A per servo. Cases include equal four-output loading; the illustrative uneven 4.5/1/1/2.4 A servo pattern plus a fixed 1.1 A main-board allowance; moderate loading; both feeds with unequal positive and return resistance; each full feed open; and single positive/return degradation or opening. The small T2/T1 and wide K2/K1 main-board joint paths are screened separately, without crediting an ideal main-board shunt.

For the **uneven 10 A benchmark**, 60 µm / 80°C / 95% IACS / 18 µm barrels / B-land injection:

| Surviving feed | Worst board-only servo drop | Sheet dissipation | Barrel dissipation | Total PCB model dissipation |
|---|---:|---:|---:|---:|
| ESC only | 28.660 mV | 0.08316 W | 0.16433 W | 0.24749 W |
| SBUS only | 37.734 mV | 0.17348 W | 0.16434 W | 0.33782 W |

A separate sensitivity reuses the same saved sheet geometry while increasing barrel length to 1.65 mm and reducing only the header-barrel bore to the drawing-derived 0.97 mm lower limit. For the same conservative uneven T2/T1 allocation, the SBUS-only result becomes **38.883 mV / 0.34807 W**, and ESC-only **29.809 mV / 0.25774 W**. The 0.30 mm via bore remains nominal. This adds about 1.149 mV and 10.25 mW to the original screen; it does not qualify manufacturing tolerances. See the separately sealed addendum under `verification/power/barrel-length-addendum/`.

These are calculated steady electrical values, **not measured temperature rise**. For the equal four-load 10 A benchmark, the revised far-feed case reduces modeled board loss from approximately 0.566 W in the first matched-fit prototype to 0.326 W. Its former 0.50 mm shared V-bridge is no longer the compulsory route.

The 1.1 A main allowance is a current bound at the loaded VX voltage. It is not a guarantee that a constant-power 5 V regulator load stays within 1.1 A as voltage falls. Two 1 A, 5 V accessories already need at least 1.351 A from 7.4 V even with ideal conversion, before FC consumption. The 8.9 A servo illustration cannot be combined continuously with that accessory case on a 10 A BEC.

## Contacts and factory leads remain the release blocker

The retained Hanxia HXPZ2.54-3X7PZZ / C32713294 catalog lists 3 A AC/DC and contact resistance no greater than 20 mΩ. It does not establish the energized-contact count, actual factory female contact, derating, or pulse conditions. Retaining the connector therefore does **not** establish 10 A operation through one feed, or even normal 5 A-per-feed operation at a 10 A equally shared load. Unequal illustrative feed impedances put roughly 8 A on the stronger feed. Single-conductor loss can send the full 10 A through one positive or return contact even while the other pair is still connected.

As a scale comparison only, a 20 mΩ contact at 10 A dissipates 2 W. This is why a low board-copper drop does not approve the complete system. It is not permission to bench-test an unqualified 3 A contact continuously at 10 A. A board-only 10 A characterization needs a separately qualified current-injection fixture that does not rely on those stock contacts.

The Hobbywing Platinum 120A V4, SKU 30203401, specifies a 10 A continuous / 25 A peak BEC, with no peak duration established in the reviewed manual. Both conductor pairs come from the same BEC. The white/red/black throttle lead includes power; the separate red/brown BEC cable is recommended for a battery or unused receiver channel; yellow is the separate RPM signal. The reviewed manufacturer material does not identify the BEC lead gauge/length or mating-contact rating. Its listed 12 AWG battery/motor wires must not be attributed to the BEC leads.

ESC and SBUS columns are stress-model feed locations, not an approved final wiring diagram. The actual second power-only lead must go to a suitable unused port without misconnecting its signal cavity or blocking the selected receiver interface. Pinout and polarity must be physically checked.

Actual cyclic/tail servo assignment and transient duration remain unknown. The former chart endpoints are illustrations, not continuous servo ratings. No arbitrary 2.5 A-per-output limit is imposed, and no 4.5 A transient or 25 A BEC pulse is certified. A documented male header alone cannot upgrade an unidentified female servo contact. Samtec's TSW/SSW example rating depends on a specified mated system and powered-contact arrangement, so it was not substituted as an automatic upgrade.

## Thermal verification still required

80°C is the conductor-resistance screening temperature, not a solved equilibrium. A proposed bench condition is 40°C ambient with the intended enclosure, cooling, wiring and duty cycle, with a pre-agreed temperature-rise and absolute-temperature limit for every conductor/contact/component. A preliminary 80°C conductor ceiling would imply no more than 40 K rise at that ambient, but it remains an engineering test criterion requiring component and system review, not an established safe operating rating.

Measure local board, plated-hole, solder-joint and mating-contact temperatures and four-wire voltage drops to equilibrium. Exercise the actual load distribution, normal feeds, each full feed loss and asymmetric conductor failures with a safe current-rated fixture. Characterize actual factory leads and servo connectors separately at their documented limits. Do not use only total board I²R or a single current-density number as thermal qualification.

## Tighter PCB-only fit

The selected physical tabs are 9.3 mm wide, local x=0.95..10.25 and 12.15..21.45, pitch 11.2 mm, length 2.6 mm. Main slots shrink to 9.8 × 2.10 mm R0.5 at unchanged centers. Child roots use 270-degree R0.5 reliefs. Every joint contact keeps its X/width/net/pin; the exposed pad begins 0.8 mm below the seat and ends at 2.346 mm. The solderable portion below the parent tip is retained. Root contact clearance is at least 0.56565 mm nominal; tip copper clearance is 0.254 mm. The 0.254 mm inset is a nominal CAD design rule, not a guaranteed finished setback under independent ±0.20 mm routing. The public manufacturer copper-to-edge capability is a design rule, not a finished-copper warranty. Adequate final geometry/process margin and qualified finished-edge/registration requirements remain an open release gate; no new finished-edge acceptance floor is imposed.

Nominal longitudinal half-play falls from about 0.808 to 0.183 mm. Parent outer/center rails increase to 0.70/1.40 mm. Shoulder bearing width increases by 12.5%; the minimum root neck is 8.3 mm versus the previous 8.4 mm. These geometric changes are not a strength, fatigue or insertion-force certification.

The independently checked actual exported child model has zero nominal interference with the matching main and 0.13749995 mm minimum clearance. Rendered mating thickness is 1.625 mm. The selected full-profile matched-pair acceptance and optional tighter supplier limits are in `verification/mechanical/geometry-contract.json`. Do not assume every ordinary JLC ±0.20 mm route / ±10% thickness pair will fit. Measure both actual profiles, pitch, finish, burr/bow and copper registration; reject or re-pair failures, never force-fit or sand plated contacts. No external saddle is selected.

## Native, schematic, generator and BOM/CPL checks

KiCad 10.0.7 child DRC with refill/save, all track errors, schematic parity and all severities: **0 errors, 0 unconnected**. Visible inherited advisories: 11 missing-courtyard and 11 custom-footprint filter mismatches. No ignored DRC checks.

Matching-main snapshot DRC: **0 errors, 0 unconnected, 0 parity issues**, with the same 61 warnings as sealed stage10: 30 silk overlaps, 16 silk-over-copper, 11 off-center track/via entries, 3 silk-edge and 1 footprint-type mismatch. These are not silently waived. This receipt will not cover later placement edits.

ERC under the inherited project settings finds 0 violations. Separate all-visible ERC copies enable the four default ignored checks: child 0 errors / 11 footprint-filter warnings; main 0 errors / 13 single-global-label and 3 library-symbol warnings. No check remains ignored in those all-visible receipts.

The portable guarded route generator `tools/apply_continuous_vx_route.py` reproduces the final route geometry from the exact matched V1 input. Its output was compared semantically to the saved final board, excluding only regenerated fill cache and node ordering; the proof is in `verification/route-reproduction-proof.json`. Historical generic rebuilding/routing scripts are not a replacement for this reviewed source-bound delta.

Semantic assertions confirm the native closed outlines, all 11 contact boxes, unchanged standard header/pinout, exact generator/library/native pad agreement, fixed model transform, declared stack and intended route deltas. The footprint generator deliberately separates the widened physical tabs from the unchanged electrical-contact registration. Slot keepout offsets are 0.60/0.35 mm, preserving the old actual routed-main keepout envelope after the slot shrink.

Local child Gerber/drill/BOM/CPL outputs under `verification/wip-fabrication/` are explicitly unfinished engineering/DFM comparison files, not order-ready outputs. They are bound to the final child hash.

Both BOM/CPL sets were exported from the checked snapshot. The child has one purchased component, J1 C32713294; its other named contacts are fabricated copper, not placement parts. The final main placement owner must regenerate its own final BOM/CPL.

## Integration and release gates

Use `handoff/child-integration-manifest.json` for exact child/library/model/generator hashes. Do not overwrite the newer main-board PCB or placement generator with this older main snapshot. Apply the guarded main slot delta to the newer main, bind the final child model, and rerun native checks and independent assembly proof on that coherent pair.

Before release: agree actual finished copper/plating/thickness/fit acceptance; resolve the header/female/lead current envelope; identify actual servos and peripheral load; run thermal, voltage-drop, vibration and joint tests; and rerun final sealed DFM. Prior DFM results cover the original stage10 files only. No order, external upload, or flight approval was made here.

## Primary sources

- Hobbywing product: https://www.hobbywingdirect.com/products/platinum-120a-v4-esc
- Hobbywing specification: https://www.hobbywing.com/en/products/platinum-120a-v471.html
- Hobbywing manual: https://support.hobbywingdirect.com/hc/en-us/article_attachments/17873440353811
- JLC copper weights and 2 oz rules: https://jlcpcb.com/help/article/jlcpcb-copper-weight
- JLC FR-4 capability: https://jlcpcb.com/pcb-fabrication/fr4-pcb
- JLC manufacturing capability and tolerances: https://jlcpcb.com/capabilities/pcb-capabilities
- JLC thickness: https://jlcpcb.com/resources/pcb-thickness
- JLC plating discussion: https://jlcpcb.com/blog/mastering-pcb-plating
- JLC finish discussion: https://jlcpcb.com/help/article/jlcpcb-surface-finish
- Hanxia selected-header manufacturer PDF: https://www.lcsc.com/datasheet/lcsc_datasheet_2407231541_hanxia-HX-PZ2-54-3x7P-ZZ_C32713294.pdf
- Samtec specified mated-header system: https://suddendocs.samtec.com/productspecs/tsw-ssw.pdf

The Hanxia manufacturer PDF and primary manufacturer files are preserved with the engineering evidence. Alternative XT30 and Nano-Fit datasheets are historical research, not selected BOM entries.
