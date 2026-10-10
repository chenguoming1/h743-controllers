# CORE supply limits and finite-terminal audit

Review date: 2026-10-09 UTC. Read-only electrical review. No board, firmware, canonical repository, numerical model, historical evidence, Git or Library changes; no mesh or solve. Findings concern the exact fitted devices and pinned stock Nexus source, not an installed binary or completed board qualification.

## Decision

**Use per-sink voltage and mode requirements. There is no defensible universal CORE pass criterion covering every load, bias pin, filtered branch, logic level and external receiver.** A **3.0–3.6 V engineering screen at the actual onboard IC supply pads** is conservative with respect to the listed supply ranges, including full USB electrical operation, but it is not a complete functional guarantee. It does not close VDDA tracking, signal-level/timing, ripple, startup, ferrite-current, or external DSM constraints.

Two material finite-terminal errors were found in the historical source19 numerical model: **U10 and U11 TPS2553DRVR power paths use pin 4 (EN) instead of pin 6 (IN)**. Both pins are wired to the same input net on the real PCB. That connectivity does not make their separate copper contacts physically interchangeable. Correct the model, not the board, and retain the old results as historical diagnostics. The expanded power-path subcheck is in `power-path-subcheck/`.

## Source binding

The inspected accepted candidate39 PCB SHA-256 is `246e3aa5d177377badb90aa248faedaaf832bc99303109d002980aad260fe0b7`. The separately identified candidate41 PCB SHA-256 is `539d9547eb8c4d5984481293ae10cee34355ee838dff11ab43b00cca270ceae2`. This review does not adopt candidate41 or rebind a power solve to either source.

After the routing owner adopted candidate41, `candidate41-pin-identity-check.json` confirmed unchanged parts, byte-identical schematics and the same UUID/pin/net for all 82 listed supply/bias/ground pads; it records their current coordinates. U13.5 moved. This establishes pin-role applicability to candidate41, not unchanged copper resistance or a fresh power pass.

`input-hashes.json` contains exact SHA-256 identities for the native board, native export, parts, schematics, relevant existing reviews, source19 ledger/freeze/result, pinned firmware and retained manufacturer documents. `source-register.json` records official URLs, printed pages and acquired document hashes; `supply-limits.json` provides role/mode-specific requirements without claiming acceptance. `native-core-pin-inventory.json` maps every CORE/ANALOG/IMU/DSM pad to its native UUID/net and fitted schematic pin role. The source19 operator-refined result remains `28dfe7bcff16f08e3919be7063cf06727ab25678e3585e86f6acfda26e0742f1`.

## Actual supply pads and applicable limits

All voltages are measured relative to the device's local ground. All listed 3.6 V ceilings are operating ceilings, not absolute maximum ratings. Source links and exact editions appear below.

| Device and fitted package | Actual pins and nets | Supply requirement and condition |
|---|---|---|
| U1 STM32F722RET6, LQFP64 | VDD 19/32/48/64 on +3V3_CORE; VSS 18/31/47/63 | **2.7–3.6 V for the pinned 216 MHz, scale-1, overdrive, 7-wait-state stock startup. 3.0–3.6 V when requiring full USB FS electrical specifications.** General 1.7 V advertising does not apply to this stock operating mode. [S1 pp101–104,168] |
| U1 backup supply | Pin 1 VBAT on +3V3_CORE | 1.65–3.6 V backup-domain operating range; not a main VDD injection contact. Its minimum does not permit the rest of the MCU to operate at 1.65 V. [S1 p102] |
| U1 analog supply | Pin 13 VDDA on +3V3_ANALOG after FB1; pin 12 VSSA on GND | General internal-reset-on operation starts at 1.8 V; headline 1.7 V requires the unavailable reset-off arrangement. ADC clocks up to 18 MHz use the lower-voltage range; 36 MHz requires VDDA≥2.4 V. **Stock ADC is 13.5 MHz**, not 36 MHz. VDDA must remain supplied from the VDD source with its required supply relationship; no independent low VDDA operating corner is approved here. 3.0 V is an optional conservative screening target, not a manufacturer-specific VDDA minimum. [S1 pp27,30,102–104,150–153; S8] |
| U2 ICM-42688-P, LGA14 | Pin 5 VDDIO and pin 8 VDD on +3V3_IMU after FB2; pin 6 GND; pin 7 reserved-ground | Each supply **1.71–3.6 V**, specified range −40…85°C. VDDIO is also the reference for receiver thresholds and output levels. Both supply pads must be checked. The 0.88 mA six-axis current is typical, not a guaranteed maximum. [S2 pp13–14,20] |
| U3 W25N01GVZEIG, WSON8 | Pin 8 VCC on +3V3_CORE; pin 4 GND and exposed pad 9 tied GND | **2.7–3.6 V**; exact selected industrial part −40…85°C. Official selected-part page independently confirms this range; retained manufacturer-authored Rev Q has it in §9.2. No lower supply is justified by the nominal stock 27 MHz clock. [S3 p56 and official part page] |
| U4 DPS368XTSA1, VLGA8 | Pin 8 VDD and pin 6 VDDIO on +3V3_CORE; grounds 1 and 7 | VDD **1.7–3.6 V**; VDDIO **1.2–3.6 V**, −40…85°C. Pin 2 is **CSB**, tied high for I2C, not a supply pin. A high-state check is relative to VDDIO (VIH≥0.7×VDDIO), not an independent supply floor. Supply compliance does not prove stock 800 kHz operation or a 3.3 V output-low guarantee. [S4 pp6–7,23–24] |
| U11 TPS2553DRVR, DRV/WSON6 plus exposed pad | Pin 6 IN and pin 4 EN on +3V3_CORE; pin 1 OUT on +3V3_DSM; pin 5 GND, pad 7 GND | IN **2.5–6.5 V**, EN range 0–6.5 V and high threshold ≥1.1 V. The shared CORE system constrains its actual upper input to 3.6 V. This input floor is unrelated to the external DSM receiver's required output voltage. [S5 pp5–6] |
| U12/U13 USBLC6-4SC6, SOT23-6 | Pin 5 VBUS bias on +3V3_CORE; pin 2 GND | Passive steering/TVS protection, no active-IC functional supply minimum is specified. Table 2 leakage at 5.25 V and breakdown at 1 mA are test/rating conditions, not a 3.3 V supply acceptance floor or a MCU-safe transient clamp proof. [S6 pp1–3] |

U9.6 is VOS, a feedback sense pin on +3V3_CORE; power is delivered to that net through L2.2. U9 is supplied from CORE_BUCK_IN. Q1.1/Q2.1 are BSS138LT1G **gate** biases; VGS, source voltage and load govern their level-shifting behavior. Neither their 0.85–1.5 V threshold nor the ±20 V absolute gate rating is a functional CORE floor. The current onsemi sheet has a 2.75 V VGS on-resistance row, which is not equivalent to 2.75 V rail-to-ground if the source is elevated. [S7 pp1–2]

The inventory also includes CORE decouplers, pull-ups R1/R4/R5/R6/R7/R8/R36/R37/R64/R71, LED-feed R10/R11, bias-divider R62, SW1 and TP3. These do not introduce standalone IC supply minima. Their voltage-dependent input, output, LED, mux-priority and load behavior still needs its own relevant screen. FB1/FB2 are series elements, not powered ICs. VCAP is the MCU's internal regulator output and remains subject to its separate existing DC-loop and capacitor requirements.

## Stock mode facts

The unchanged stock target is commit `1d9cb4dc6f85c7895c2b089f4b8aa776ca3d3bd3`, target blob `ca042b1f51a341a46980cb9aba78420beab48be7`; firmware is `ba6c7e3e328b91a549bf6ca87c9eadd7006b6d94`. Startup explicitly sets voltage scale 1, enables overdrive, and calls clock configuration with `FLASH_LATENCY_7`. Thus the datasheet's lower-voltage 216 MHz rows requiring 8 or 9 wait states cannot justify a lower floor without changing stock firmware. USB is functionally possible at 2.7–3.0 V but its full electrical specifications are degraded there.

The byte-verified ADC source blob is `c122ab48c23faaeae2e0acd79f8bd614e365140c`. It selects PCLK2/8 and 480-cycle sampling; with pinned PCLK2=108 MHz, fADC=13.5 MHz. ADC static-accuracy tables have additional reference, source-impedance, sampling and supply conditions. A rail meeting a functional supply minimum does not establish measurement accuracy. Existing installed settings/registers are unverified; no firmware change is proposed.

## Historical contact gaps and required follow-through

`historical-contact-findings.json` retains all affected case names, JSON pointers, exact U10/U11 elements, actual pin UUIDs and network contact inventories. For U11, the historical resistor is `U11_selected_path`, p=`U11.4`, n=`U11.1`, 0.15 Ω; the CORE contact list contains U11.4 and omits U11.6. For U10, USB cases similarly use U10.4 for `U10_USB_limiter_path` and its IQ screen. TI's **DRV** column, not its different DBV/SOT23 pinout, governs both fitted parts.

The historical ten 0.32 A electronics vertices comprise four U1 VDD pads, U3.8, U4.2/6/8 and FB1.1/FB2.1. They are mathematical copper-load corners, not a physically valid 0.32 A operating current for every individual device pin. U4.2 is a logic strap; the last two vertices stop before the ferrites. +3V3_ANALOG and +3V3_IMU are absent from the 13 modeled networks. An upstream reported voltage is not a measured or solved downstream supply voltage. True functional supply contacts are U1.19/32/48/64/13, U3.8, U4.6/8 and U2.5/8; use actual local ground pairs.

Keep historical cases/results intact. Before a new source-bound solve is accepted, correct actual power-input contacts, review device-internal pad unions/return assumptions, and add actual supply reports and explicitly justified mode limits without silently deleting old diagnostic cases. VBAT, CSB and protection bias should be separate role-appropriate reports, not substitutes for supply injections. Ground/reference differences must be included. A current forced into EN can change local sheet current and voltage even when both pads share a connected net; error magnitude/sign are not computed here.

## Filtered-branch verification proposal

The existing selected-BOM evidence §9 records FB1/FB2=BLM15AG601SN1D: **300 mA**, **0.52 Ω initial / 0.62 Ω after reliability tests**, at the manufacturer's stated standard conditions. It explicitly establishes **20 mA per filtered branch** and **1 Ω hot-bead acceptance** as project validation bounds, not guaranteed manufacturer maximums. The exact official reference PDF returned HTTP500 and the official part page HTTP403 in this pass; existing evidence is retained and hashed, not silently promoted to a newly revalidated hot-DCR specification. Search-indexed official Murata part lists independently show the 0.52 Ω/300 mA nominal catalog entries.

Do not move the complete 0.32 A allocation downstream through a ferrite: it exceeds the catalog current rating and the existing branch-current budget. A corrected constrained envelope may preserve the 0.32 A total while bounding each filtered branch separately; U2 VDD+VDDIO share one FB2 budget. The inherited upstream vertices should remain historical diagnostics.

A possible independent bound is:

`V_sink_local >= min_cases(V_FB_input - V_actual_sink_ground) - I_branch_max * (R_bead_max + R_forward_copper_bound)`.

If the reference ground differs, add a separately bounded return-voltage term. At the existing conditional 20 mA/1 Ω limits, bead-only loss is **20 mV**; forward copper/contact loss, source uncertainty and dynamic margins are additional. This is a proposed verification method, **not a computed board pass**. In particular, an upstream 3.000 V floor cannot prove a downstream 3.000 V floor after a nonzero series loss. VDDA also needs the VDD relationship reviewed; the datasheet's 300 mV allowance is only for power-up/down, not a steady-state tolerance. ST AN4661 §1.2 p11 permits a ferrite between VDD and VDDA. [S8]

## Limits that remain open

Candidate41's reported 0.691 mV added worst-allocation drop concerns a local positive CORE feed reaching C4.1/C6.1/U1.1/U1.64/U13.5. It cannot establish the absolute minimum or maximum of that branch. U1.64 is the main functional supply in that set; U1.1 is VBAT and U13.5 is protection bias. No historical voltage result was shifted and relabeled as candidate41 acceptance here.

The external classic-DSM probe remains its separate conditional 3.1394–3.465 V board-pad screen; do not reuse it as CORE's universal floor. TPS62162 initial accuracy is not a bound on line/load/ripple/transient error. Component/body temperature, supported stock clocks, decoupling, startup, regulator dynamics, USB coexistence and actual logic levels remain separate obligations. The 105°C/15 µm/95% IACS copper model does not qualify semiconductor or capacitor temperatures. Existing stock-I2C and SPI review gaps remain unchanged, particularly the DPS368 800 kHz/3.3 V output-low evidence gap.

## Source register

- **S1:** [ST DS11853 Rev9](https://www.st.com/resource/en/datasheet/stm32f722re.pdf), pinout p48, power/reset pp27–35, Tables16–17 pp101–104, ADC pp150–153, USB Table85 p168. [ST AN4879 Rev12](https://www.st.com/resource/en/application_note/an4879-introduction-to-usb-hardware-and-pcb-guidelines-using-stm32-mcus-stmicroelectronics.pdf), §2.5 pp10–11, explains low-pin-count VDD supply for USB. Relevant rendered min/max columns and footnotes were visually reviewed.
- **S2:** [TDK DS-000347 Rev1.6](https://product.tdk.com/system/files/dam/doc/product/sensor/mortion-inertial/imu/data_sheet/ds-000347-icm-42688-p-v1.6.pdf), supply ranges p13, logic pp14–16, pins p20.
- **S3:** [Winbond selected W25N01GVZEIG page](https://www.winbond.com/hq/product/code-storage-flash/qspi-nand/w25n-gv/?__locale=ja&partNo=W25N01GVZEIG); retained manufacturer-authored [RevQ datasheet](https://www.mouser.com/pdfDocs/W25N01GV_DS.pdf), §9.2 p56. The current official download was not acquired; no new silicon-lot compatibility claim is made.
- **S4:** [Infineon DPS368 v1.1, 2019-07-03](https://www.infineon.com/assets/row/public/documents/30/49/infineon-dps368-datasheet-en.pdf), pins p6, operating range p7, interface pp23–24.
- **S5:** [TI TPS255x SLVS841F](https://www.ti.com/lit/ds/symlink/tps2553.pdf), DRV pins p5, recommended conditions p6, switch characteristics p7. Retained PDF SHA-256 `88e453700cea2b263cdb5b44fce1e883e0f6d3b975457f879ac1423eeea42071`.
- **S6:** [ST USBLC6-4 DocID11068 Rev7](https://www.st.com/resource/en/datasheet/usblc6-4.pdf), pp1–3.
- **S7:** [onsemi BSS138LT1/D Rev15, September2026](https://www.onsemi.com/pdf/datasheet/bss138lt1-d.pdf), pp1–2.
- **S8:** [ST AN4661 Rev5](https://www.st.com/resource/en/application_note/an4661-getting-started-with-stm32f7-series-mcu-hardware-development-stmicroelectronics.pdf), §1.1.1 p7 and ferrite guidance §1.2 p11; [pinned ADC source](https://github.com/rotorflight/rotorflight-firmware/blob/ba6c7e3e328b91a549bf6ca87c9eadd7006b6d94/src/main/drivers/adc_stm32f7xx.c); [pinned startup](https://github.com/rotorflight/rotorflight-firmware/blob/ba6c7e3e328b91a549bf6ca87c9eadd7006b6d94/src/main/startup/system_stm32f7xx.c).
- **S9:** [Murata exact selected-part page](https://pim.murata.com/en-global/pim/details/?partNum=BLM15AG601SN1%23), [ENFA0018 reference specification](https://www.murata.com/products/productdata/8796740059166/ENFA0018.pdf?1730777411000=); inherited detailed extraction in `repo/f722-heli/docs/passive-bom-evidence.md` §9. Fresh-access limits are stated above.

In the full research tree, reproduce read-only mapping and input hashes with `PYTHONDONTWRITEBYTECODE=1 python3 -B independent-core-voltage-review/build_inventory.py` from the rebuild root. This performs no electrical solve and never updates source artifacts. The compact public packet instead includes `verify_packet.py` for portable integrity and retained-evidence consistency checks; vendor PDFs/screenshots are omitted and linked above. Full source re-extraction requires the original bound input artifacts.
