# U5–U10 power-terminal subcheck

**One proven model error: U10 uses EN as its power input.** The released candidate19 ledger models `U10_USB_limiter_path` from **U10.4 to U10.1**, and `U10_IQ_table_screen` from **U10.4 to U10.5**. The exact TPS2553DRVR is the **DRV/WSON** variant: **IN=6, EN=4, OUT=1, GND=5**. Both pins 4 and 6 are correctly assigned USB_VBUS_RAW in the actual schematic and candidate39 board, so a same-net check did not detect the incorrect finite injection location. Their land centers are 1.3 mm apart. The ledger has no U10.6 contact. [TI TPS2553 SLVS841F, p.5](https://www.ti.com/lit/ds/symlink/tps2553.pdf#page=5)

This affects the two released USB cases, `usb_configuration_USB4.33_NONE_mcu_vdd19_baseline` and `usb_configuration_USB4.33_NONE_flash_baseline`. Rebind the contact and both elements to actual IN=6 before a fresh solve. The voltage-error magnitude and direction have **not** been computed. This is a numerical-model mapping defect; the reviewed schematic pin functions and board net assignments are correct. U11 was excluded as requested and is covered separately.

## Exact-package role check

| Device and package | Modeled roles checked against manufacturer | Finding |
|---|---|---|
| U5 TPS259472ARPWR, RPW | IN5 → OUT6; IQ returns to GND8 | Correct. PGTH4 is also board GND but is a control input, not an alternate ground contact. [TI pp.4–6](https://www.ti.com/lit/ds/symlink/tps25947.pdf#page=5) |
| U6 TPS63070RNMR, RNM | VIN12/13; VOUT7/8; power return PGND10; feedback FB5 referenced to GND4 | Correct. Both declared power-contact unions contain all documented power leads and are connected native land unions. Grounded PS/SYNC1, FB2_6 and VSEL15 are controls. [TI p.3](https://www.ti.com/lit/ds/symlink/tps63070.pdf#page=3) |
| U7 TPS2117DRLR, DRL | BEC VIN1=3 or USB VIN2=6 → VOUT2/7; IQ return GND1 | Correct. Both output contacts connect to DEV_U7_OUT through separate ideal zero-volt sources. MODE5 shares +5V_BEC with VIN1=3 but is not another power input. [TI p.3](https://www.ti.com/lit/ds/symlink/tps2117.pdf#page=3) |
| U8 TPS2121RUXR, RUX | BEC IN1=7 or USB IN2=2 → OUT1/8; IQ return GND12 | Correct. Both output contacts connect to DEV_U8_OUT through separate ideal zero-volt sources. Grounded OV1=5 and OV2=4 are control inputs. [TI pp.4–5](https://www.ti.com/lit/ds/symlink/tps2121.pdf#page=4) |
| U9 TPS62162DSGR, DSG | VIN2/PGND1 input; output injected at L2.2; VOS6/AGND4 sense | Correct. U9.7→L2.1 is the switching-node side; L2.2 is the +3V3_CORE inductor output. U9.6 is sense only, not the load-current injection. Same-net EN3 is not another VIN. [TI p.4](https://www.ti.com/lit/ds/symlink/tps62160.pdf#page=4) |
| U10 TPS2553DRVR, DRV | Uses EN4 → OUT1; IQ at EN4/GND5 | **Wrong input terminal; use IN6.** The native board and schematic distinguish EN4 and IN6 correctly. [TI p.5](https://www.ti.com/lit/ds/symlink/tps2553.pdf#page=5) |

## Ground and package assumptions to retain explicitly

- U10 GND5 is valid. TI identifies the exposed PowerPAD as internally grounded and requires it to be externally connected to GND. Candidate39 pad7 is that grounded exposed pad; the ledger exposes only pin5. This omits internal pin5/PowerPAD current sharing, for which no package resistance or split was verified. Do not silently treat separate lands as one connected geometric contact.
- U9 PGND1 and AGND4 are valid distinct model roles. The exposed pad is numbered 9 by this KiCad symbol and is connected to GND; TI requires connection to AGND. Fixed-output FB5 is also tied to GND. Neither is a separate ledger contact. The data does not establish a package-current distribution or authorize using all grounded control pads as equivalent power returns.
- U6's two ground roles, U7/U8 ideal output ties, and U9's averaged converter/inductor-loss treatment remain explicit idealizations. No solder or package impedance, switch-state behavior, thermal acceptance, or dimensional/orientation certification is supplied by this check.

## Binding and reproducibility

`audit.json` records every selected numbered native pad, manufacturer function, schematic net/pinfunction, native UUID, location, area, canonical pad-object hashes, every distinct modeled role and its case membership, released contacts and contact-audit receipts, all 28 verified freeze inputs, and exact hashes of every local source used. It also directly extracts the selected library-symbol pin functions from the three actual schematic files. All six symbol pin maps match TI; all selected native pin/net records match the bound schematic netlist and are identical between candidate19 and candidate39. **This pad comparison does not establish unchanged intervening routing or final-board numerical applicability.**

- Released ledger SHA-256: `f811c4d93dd074e5d74fb000db2d1218d10199ceb7c0562173be437fda572951`
- Released freeze SHA-256: `1e0296e48e779f1a3531a7f0fa901c25ab978da97687e20826a395e58bb727b5`
- Candidate39 native SHA-256: `e99bb7888b98c5dd44e44a04b51789ac9dcc47b3fd6b07d1446295acf5b2c577`
- Candidate39 board SHA-256: `246e3aa5d177377badb90aa248faedaaf832bc99303109d002980aad260fe0b7`
- Selected parts SHA-256: `99e1589baf2033bc696613ad52c5deab3403397d7caafff6d8aa011296846858`
- Bound schematic netlist SHA-256: `4243bd2401f97591002798145ebb9e064a4efb5b9abc6b87ed6532f3640230ec`

Primary TI data sheets were inspected through official web access; URLs, revisions and printed page numbers are in the JSON. Raw PDF bytes are not archived/hash-certified. Existing `independent-power-drop-review` and `bec-voltage-source-packet` evidence was read first and is separately hashed; this audit does not inherit their broader acceptance claims.

Reproduce only the read-only extraction from the workspace root:

```sh
PYTHONPATH=python-deps python independent-core-voltage-review/power-path-subcheck/audit.py
```

The script writes only this independent artifact directory. No canonical source, board, numerical model, Git state or Library item was edited. No numerical solver was run.
