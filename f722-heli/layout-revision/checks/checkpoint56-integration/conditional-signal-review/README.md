# R4 relocation: bounded electrical and topology review

Reviewed 2026-10-10 UTC. This is a read-only design review of native candidate02. Only this report directory was written; no board, canonical source, firmware, BOM, or index was edited. No router, field solve, or current-capacity qualification was run.

## Result and exact source

The deliberate C15 feed removes the incidental power contacts found in rejected candidate01. R4's value and intended pull-up topology introduce no identified component-value or powered-static contradiction under the stated assumptions. The actual U1.33-to-flash CS connection remains open, so this is an incomplete routing checkpoint, not a completed SPI or electrical qualification.

- Candidate02 PCB: `9d9f2f39c2b200f2c928dd3123f098797eb86ba56cb943d7f6e3fe89bf264a7e`
- Native export: `868d1bb6d333342dd97a51d5c3f441d42becfe6ef06360124432b070ff6fd889`
- Proposal: `c78371bcbe8688c6096fc8afad77eebdd0a45614e074bde7689b98addc47de06`
- Construction receipt: `da66a3e16b57bc2ae99c03174cb3c5a63bcc12956973181ae5e21e6c20153d0a`
- Accepted source55 PCB: `14dea1df09ea9d800bf66a6d74eb5f0dac33a8705161e9ed1a02f2e11f3b58b8`

The exact native candidate and construction inputs are retained in the checkpoint56 reproducible source packet; the hashes above identify the reviewed bytes. Independent replay checked all 13 added track records and both 0.45/0.20 mm through vias against the proposal, including exact endpoints, layers, widths and nets. No source object was deleted. Only the original two R4 pad records and R4 footprint changed; every other original native object and every component value remained exact. Filled-zone records changed, so this statement does not transfer previous return-plane or power results.

## R4, active CS and loading

R4 remains 10 kΩ ±1%, UNI-ROYAL 0402WGF1002TCE, C25744. Its new B-side center is (40.55,19), 180°: pad1 at (41.06,19) is +3V3_CORE; pad2 at (40.04,19) is FLASH_CS. U3 is W25N01GVZEIG NAND. U1.33 is PB12, the flash CS driver.

The U3.1-to-R4.2 copper is **13.999707 mm**, not the predecessor's 11.668458 mm: B 3.915923 mm, In2 7.265711 mm, B 2.818073 mm, two through vias, 0.127 mm width. The future MCU attachment point determines which part is the main path and which part is a pull-up stub. Do not call the whole existing route a final harmless stub before that connection is defined.

The pinned firmware configures FLASH_CS as push-pull, VERY_HIGH output speed, no internal pull after initialization, and actively asserts/deasserts it in transfer handling. R4 is idle bias; the CS net carries fast control transitions. This differs from stock static WP/HOLD straps. R4 is not series isolation or demonstrated line termination, and copper on its signal side directly loads CS.

Using exactly the previous review's continuous-plane line approximations and nominal saved stackup gives only a **1.2915–1.5112 pF trace sensitivity scale** and 0.0865–0.0875 ns one-way line delay. These are not bounds. They omit both vias and unused barrels, pads, resistor parasitics, coupling, actual return detours, device loading and the unfinished MCU route. Winbond specifies 6 pF maximum input capacitance under its table conditions; STM32's 5 pF CIO is typical. A total-load or fastest-edge guarantee cannot be built from these figures. Avoid double-counting device capacitance when using IBIS/package models.

The stock-source verifier passed all 25 packet files, 14 upstream firmware blobs, clock arithmetic and the authoritative parts manifest. At stock 216 MHz, flash detection is nominally 3.375 MHz and initialized SPI2 is **27 MHz**, the MCU SPI2 ceiling. VERY_HIGH GPIO speed still requires edge/return review. Neither repetition rate nor the small nominal line delay proves CS timing, ringing or crosstalk performance.

## Bias and startup limits

An ideal powered-static case with R4=10.1 kΩ, common local rail, Winbond 2 µA input leakage and STM32 1 µA leakage gives 30.3 mV pull-up droop. At 2.7 V this leaves 0.7797 V above the flash's 0.7VCC threshold. This excludes negative injection, unpowered devices/backfeed, rail offsets and transients. With CS=0 V and a 3.6 V rail, R4=9.9 kΩ draws 0.3636 mA and dissipates 1.309 mW; these are static arithmetic, not signal or thermal qualification.

For assumed total loads of 10/25/50 pF, an ideal supply step through 10.1 kΩ takes 0.1216/0.3040/0.6080 µs to reach 0.7VCC. These examples do not bound an actual ramp or an actively driven edge.

Winbond RevQ §§4.1 and9.3 require CS to track VCC during power-up/down, at least 200 µs from VCC(min) to first CS low, and at least 1 ms before a write instruction. The pinned `flash.c` directly shows: preinit registration as input pull-up/high; GPIO output configuration and `IOHi`; `delay(50)`; then the first Read-ID transaction. Successful W25N detection subsequently sends reset, polls ready, writes protection/configuration registers, and finally selects the initialized SPI divider. Under the intended millisecond delay API, that wait would exceed both minima if the local flash supply had already crossed VCC(min) and remained valid. The retained packet does not include the delay/preinit implementation or complete startup call chain, and this review does not measure the rail. The visible software ordering therefore does not guarantee the initial output transition, supply-ramp relationship, brownout recovery, power-down tracking or backfeed behavior.

## CORE feed and old-pad junction

The new R4 supply spur is **4.335 mm ×0.20 mm B.Cu**, from R4.1 through (41,19),(41,22.175) to the actual C15.1 center (39.9,22.175). Lightweight native-polygon inspection confirms its only old CORE contacts are C15.1 and retained track `a31c2226` within that pad. It has no contact with C14.1 (2.125 mm copper separation) or the former incidental C15 via `80dfbb3f` (1.613846 mm separation). Nominal 20°C trace resistance at saved 35 µm copper is 10.676 mΩ, giving 3.882 µV drop in the stated 0.3636 mA static pull-up case. This narrow calculation applies to the R4 spur only.

The old R4 supply pad was also a CORE junction. Candidate02 retains leaf `4d92c569`, via `a53ae213`, C3 trunk `b78df967`, and all original C14/C15/U3 feed copper. A new **1.835756 mm ×0.20 mm B.Cu bridge** goes from the old leaf endpoint (28.01,19.8) to actual C3.1 (28.25,17.98). This supplies a complete explicit centerline path independent of the moved pad's former copper. The bridge's isolated nominal track resistance is 4.521 mΩ; overlapping existing copper and parallel current paths prevent treating that as a solved network resistance. Its current is not bounded by R4's bias current. Fresh actual-terminal power/decoupling and filled-plane review must preserve all these contacts and evaluate the entire network.

C3/C14 remain 100 nF/16 V/X7R and C15 remains 1 µF/10 V/X7R. Their values, pads, and original feed/ground records are unchanged. That does not establish effective capacitance, package/loop inductance, current division or transient rail performance.

Rejected candidate01 PCB `1c8cca2810d0c5aa3edf231631ee950a6f138121c11ba2fe8644f6b798a94ffb` had an 8.405 mm supply path. It overlapped C14.1 by a 0.050000 mm-deep sliver (0.02445184 mm²), crossed C15's retained 0.20 mm track at 32.28083°, and contacted C15 supply via80dfbb3f. Those findings apply only to the rejected predecessor; the successor removes the lower run entirely.

## Restrictions remaining before use

1. Finish the actual U1.33 CS connection and review the complete driver-to-U3 tree, including the resulting R4 spur, both via barrels, adjacent nets and nearby reference transfer. Current native CS contains nine tracks, two vias and three pads, with U1.33 isolated.
2. Bind geometry/process, reference-plane and fresh power/decoupling checks to the same final saved/refilled successor. Do not carry an earlier power result across the moved junction or changed zones.
3. At U3 pins, check active CS setup/hold and deselect intervals, especially both polled and DMA traffic. RevQ lists active setup/hold 5/3 ns and deselect 10 ns for array-read-to-array-read versus 50 ns for its specified erase/program/status sequences; observe the other CS-to-clock conditions as well. The AC conditions use ≤5 ns input transitions. These are device timing requirements, not demonstrated PCB margins.
4. Prototype checks remain: actual binary/clocks/GPIO settings; local U3 supply and CS on startup, reset, brownout and shutdown; both endpoints' levels, fastest edges, ringing/recrossing and CS timing; flash command/status/readback under representative regulator/output activity. Include probe loading and intended voltage/temperature. No flight, fabrication, AC or current-capacity approval is supplied by this report.

## Pinned primary evidence

- [Rotorflight flash initialization](https://github.com/rotorflight/rotorflight-firmware/blob/ba6c7e3e328b91a549bf6ca87c9eadd7006b6d94/src/main/drivers/flash.c#L130), [GPIO settings](https://github.com/rotorflight/rotorflight-firmware/blob/ba6c7e3e328b91a549bf6ca87c9eadd7006b6d94/src/main/drivers/bus_spi.h#L37), [W25N reset/detection](https://github.com/rotorflight/rotorflight-firmware/blob/ba6c7e3e328b91a549bf6ca87c9eadd7006b6d94/src/main/drivers/flash_w25n01g.c#L265).
- [Winbond manufacturer-authored RevQ](https://www.mouser.com/pdfDocs/W25N01GV_DS.pdf), retained PDF SHA256 `4e814c5db462372f2cb6a034f7ecb6d1f8c67022c8fe9fcf29bbab04607ef303`, §§4.1,9.3–9.6. This is the selected-part evidence already pinned in the project, not a claim about a newer datasheet revision.
- [ST DS11853 Rev9](https://www.st.com/resource/en/datasheet/stm32f722re.pdf), retained PDF SHA256 `0b5686b8f9a62d894e13a1feb75bdad3d7a822c2f8881fc83455d2b78d049fb5`, Tables61,63,81.
- Existing repository `layout-revision/spi-review/stock-spi-review.md`, `hardware/parts.json`, and source55 `conditional-signal-review/calculate_review.py` supplied the verified source mapping and conditional line-model arithmetic.
