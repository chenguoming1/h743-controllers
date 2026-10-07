# Selected R16 VCAP network and assembly limits

The final95 project selects Panasonic **ERJ3RSFR12V / C4059772**, **0.120 Ω ±1%, 0.1 W**, with dedicated `F722_Heli:R_Panasonic_ERJ3R_0603` lands. Supplier spelling ERJ-3RSFR12V denotes the same part. No alternative is authorized. Current selection is bound by unchanged hardware/parts.json, the native board and the complete procurement BOM.

The [exact Panasonic part page](https://industrial.panasonic.com/ww/products/pt/current-sensing-chip-resistors/models/ERJ3RSFR12V) specifies 0603 and TCR 0…+300 ppm/K. Panasonic [DMM0000COL17](https://industrial.panasonic.com/cdbs/www-data/pdf/RDM0000/DMM0000COL17.pdf) gives the ERJ*R 1608 rectangular example: gap a=0.7–0.9 mm, outer span b=2.0–2.2 mm and width c=0.8–1.0 mm. The retained local footprint selects a=0.85, b=2.20 and c=0.95 mm. Its 0.675 × 0.95 mm pads are centered at ±0.7625 mm. Copied/adapted library notices remain in hardware/library/licenses.

This source/land-pattern match is not solder-process qualification. Confirm the delivered exact part, stencil/reflow, solderability, installed R16/C7/copper impedance and regulator startup/stability. [ST DS11853 Table 19](https://www.st.com/resource/en/datasheet/stm32f722rc.pdf) specifies the applicable 4.7 µF / 100–200 mΩ VCAP requirement; the component label alone does not establish the installed network's operating impedance.

[JLC C4059772](https://jlcpcb.com/partdetail/PANASONIC-ERJ-3RSFR12V/C4059772), [LCSC C4059772](https://www.lcsc.com/product-detail/C4059772.html) and [DigiKey](https://www.digikey.com/en/products/detail/panasonic-industry/ERJ-3RSFR12V/308051) are retained exact-identity sourcing references. Dated stock observations are not live assembly inventory or a reservation. Public assembly supply/private-stock handling remains to be confirmed, as stated in the manufacturing assembly notes.

The final exact-board electrical report owns current numerical results and assumptions. Historical resistor-selection budgets from older routed boards are not carried forward here. First-article VCAP voltage/ripple/startup and functional checks remain necessary; no production or flight qualification is asserted.
