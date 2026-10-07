# B-RID prototype component qualification

Exact-part review dated 7 October 2026 UTC. The capacitor choices below have been applied to the final schematic and PCB. Stock observations are point-in-time public listings, not reserved inventory. Native parity and layout checks are included separately.

## Selected exact capacitors

| References | Exact MPN | Specification | Public stock observed | Decision |
|---|---|---|---|---|
| C2,C3,C4,C10 | Murata GRM21BR61H106KE43L | 10 µF, 50 V, X5R, ±10%, 0805 | LCSC C440198: 67,720 | Selected and applied |
| C6,C7 | Murata GRM21BR61C226ME44L | 22 µF, 16 V, X5R, ±20%, 0805 | LCSC C86817: 5,305 | Selected and applied, 2 × 22 µF |
| C1,C8 | Murata GRM188R61H225KE11D | 2.2 µF, 50 V, X5R, ±10%, 0603 | LCSC C162273: 125,670 | Selected and applied to both references |
| C5,C9,C11,C15,C16,C17 | Murata GRM155R71C104KA88D | 100 nF, 16 V, X7R, ±10%, 0402 | LCSC C71629: 998,800 | Selected and applied |
| C12 | Murata GRM155R61A105KE15D | 1 µF, 10 V, X5R, ±10%, 0402 | LCSC C76999: 198,450 | Selected and applied |
| C13,C14 | Unpopulated | 0201 RF matching positions | Not applicable | No fixed value or MPN before host RF tuning |

C8 is now 2.2 µF/0603. The evaluated 1 µF part GRM188R71C105KA12D was rejected because it is obsolete and was not available at LCSC.

Stock links: https://www.lcsc.com/product-detail/C440198.html ; https://www.lcsc.com/product-detail/C86817.html ; https://www.lcsc.com/product-detail/C162273.html ; https://www.lcsc.com/product-detail/C71629.html ; https://www.lcsc.com/product-detail/C76999.html

### Actual DC-bias evidence and limits of the calculation

Numeric curves were retrieved from Murata's own SimSurfing characteristics service, not inferred from rated voltage. The raw responses and request URLs are included in `evidence/components/` as `murata-bias.json`, `murata-bias-url.txt`, `murata-extra.json`, and `murata-extra-url.txt`. The entry point is https://ds.murata.co.jp/simsurfing/mlcc.html . The model uses the base MPN without its tape-pack suffix.

| Part base | Bias | Manufacturer typical capacitance | Conservative engineering screen |
|---|---:|---:|---:|
| GRM21BR61H106KE43 | 4.5 V | 7.289 µF | 4.99 µF |
| GRM21BR61C226ME44, each | 3.4 V | 13.990 µF | 9.26 µF each; 18.51 µF pair |
| GRM188R61H225KE11 | 5.5 V | 1.597 µF | 1.09 µF |
| GRM21BR61E106KA73, rejected for C2/C3/C4 conservative screen | 4.5 V | 5.589 µF | 3.87 µF |

Screen = nominal capacitance × (C at bias / C at 0 V from the same manufacturer curve) × negative nominal tolerance × 0.85 temperature allowance × 0.95 additional engineering reserve. The 5% factor is an engineering reserve, not a manufacturer-specified lifetime aging guarantee. The models are typical, at 25°C and their documented AC characterization level (1 Vrms for the 10 µF/50 V and 2.2 µF/50 V parts; 0.5 Vrms for 22 µF/16 V). Murata's service does not supply these parts' curves at the attempted other temperatures or 0.1 Vrms. Consequently these results justify prototype selection and margin, not a guaranteed combined process/temperature/bias/aging bound. Validate capacitance/stability and power transients on assembled hardware over the actual operating range. `evidence/components/capacitor-screen.json` contains the interpolation calculations.

TI TPS63031 Rev. D §9.2.2.3 specifies at least 4.7 µF input, recommends 0.1 µF VINA bypass (no more than 0.22 µF), and recommends **nominal** 10 µF output; it does not publish a guaranteed effective-output minimum in that revision. The actual L1 is 1.5 µH. The selected 2 × 22 µF output pair gives approximately 18.5 µF under the engineering screen above; this is additional margin beyond the current nominal recommendation, rather than a claim that TI specifies an 11 µF effective minimum. https://www.ti.com/lit/ds/symlink/tps63031.pdf

BQ24074 calls for 1–10 µF at IN and 4.7–47 µF at BAT and OUT. C1's selected 2.2 µF addresses DC-bias loss while remaining inside that nominal range. C2 and C4 together remain inside the OUT nominal range. Local capacitor placement and load-step stability still matter. https://www.ti.com/lit/ds/symlink/bq24074.pdf

## Battery candidate and remaining gates

LiPol's LP412550 protected 1S pack, drawing FD_3245_70, documents 490 mAh minimum/500 mAh typical, 250 mA maximum charge, 500 mA continuous discharge, and a 10 kΩ ±1% B3380 NTC. Its JST SHR-03V-S-B drawing shows pin 1 red positive, pin 2 yellow NTC, pin 3 black negative. Size is 4.1±0.3 ×25±0.5 ×50±1 mm with 50±3 mm leads. Charging is allowed at 0–45°C, discharge at −20–60°C. Overcurrent protection trips at 2–4.5 A after 8–16 ms; this is not a cell pulse-current allowance. It has no published pulse rating or NTC beta tolerance. Thus it is a documented candidate, not a fully qualified drop-in pack. Supplier confirmation of the exact assembled pack, current capability, NTC curve/tolerances, availability and certification documents is required. Source: https://www.lipolbattery.com/LiPo-Battery-Datahseet/LiPo_Battery_LP412550_3.7V_500mAh.pdf

The nominal 151 mA charge setting is below its 250 mA maximum. But direct BQ24074/103AT sensing permits approximately 0–50°C; its documented two-resistor TS network only extends that window. The pack's 0–45°C limit is therefore not satisfied by an unmodified direct TS connection. An independently qualified fail-safe charge-temperature interlock is required before this pack can be approved. https://www.ti.com/lit/ds/symlink/bq24074.pdf

For load screening, ESP32-C3 Wi-Fi TX can draw 350 mA and MIA-M10Q startup can draw 100 mA. Allowing another 10 mA produces 0.46 A on 3.3 V; at 2.75 V and an assumed 85% conversion efficiency this is about 0.65 A pack current before wiring/PowerPath losses. Even high-duty TX plus ordinary GNSS can exceed the candidate's 500 mA continuous limit near depletion. A rated ≥1 A pulse-capable pack, or a supplier-approved bounded duty/load profile, is needed; measure the actual RID workload. Sources: https://documentation.espressif.com/esp32-c3-mini-1_datasheet_en.pdf and https://content.u-blox.com/sites/default/files/documents/MIA-M10Q_DataSheet_UBX-22015849.pdf

## GNSS and antenna procurement/RF gates

MIA-M10Q-00B is active but DigiKey's live public page shows zero stock, 1,000 expected 6 November 2026, and 28-week standard lead time. Incoming dates are not commitments. Mouser also showed zero stock with differing incoming estimates. Do not silently replace it with a similar module. https://www.digikey.com/en/products/detail/u-blox/MIA-M10Q-00B/16034297

INPAQ still lists the exact PA1575MQ4S-123-1Z, 10×10×4 mm. No credible public stocked distributor offer for that exact suffix was verified. Its manufacturer-authored engineering specification is characterized on a 20×20 mm ground plane: 1575.42±3 MHz, S11≤−10 dB, typical zenith gain −4.5 dBic. The B-RID board/enclosure/battery are a different host. Exact supplier/assembly confirmation and first-article host RF tuning and GNSS/Wi-Fi coexistence tests remain gates. This recommendation retains the directly mounted patch, with no coax substitute. Sources: https://www.inpaqgp.com/product.php?productsID=3&secureChk=26888b40d60703c46b16cf9e447c0d7a and https://www.novitronic.com/Datenbl%C3%A4tter/Generalimport/689427.pdf

## Other exact parts and footprint checks

- U6 TMUX1119DCKR: DigiKey 25,426. TI DCK is SC70-6; pins 1 SEL,2 VDD,3 GND,4 S1,5 D,6 S2 agree with the netlist. Stock: https://www.digikey.com/en/products/detail/texas-instruments/TMUX1119DCKR/9858334 ; data: https://www.ti.com/lit/ds/symlink/tmux1119.pdf
- Q1 Nexperia 2N7002P,215: LCSC C81488 179,480. SOT23 with 1 gate/2 source/3 drain. Stock supports prototype use, but Nexperia marks it **Not for Design In**; lifecycle risk remains. https://www.lcsc.com/product-detail/C81488.html ; https://www.nexperia.com/product/2N7002P ; https://assets.nexperia.com/documents/data-sheet/2N7002P.pdf
- APHB1608CGKSURKC: LCSC C6506245 975. Green is 1 anode/2 cathode; red is 3 anode/4 cathode. G and R mean GNSS and RID, so both intentionally use the green channel; S uses green/red. The custom land dimensions 0.5×0.4 mm at x±0.6/y±0.35 match Kingbright's recommended pattern. https://www.lcsc.com/product-detail/C6506245.html ; https://www.kingbrightusa.com/images/catalog/spec/aphb1608cgksurkc.pdf

## SW1 exact mechanical comparison

SHOU HAN MSK12C02 drawing in the manufacturer-authored A/0 spec (2015-03-26), page 10: https://evelta.com/content/datasheets/336-MSK-12C02.pdf . LCSC C431540 showed 179,930: https://www.lcsc.com/product-detail/C431540.html

- 8±0.2 mm is overall solder-anchor span, not plastic body width. The existing 6.7 mm body approximation is consistent with the drawing; no basis to enlarge plastic to 8 mm
- Body depth 2.8±0.1 mm, height 1.4±0.1 mm; 1.5 mm actuator projection. Assuming centered body origin and the title-block ±0.01 unmarked tolerance, maximum front reach is 1.45+1.51=2.96 mm
- Final B-side origin y103.10 gives 0.14 mm nominal-stack margin to the y100 envelope, before assembly location tolerance. With an assumed 0.10 mm placement allowance, only 0.04 mm remains; final assembly tolerance review is required
- The separate corrected switch visual model uses the nominal 1.50 mm actuator projection. The native footprint was retained; its 3.10 mm courtyard reach covers the component tolerance stack
- Locating holes Ø0.85 mm at x±1.5 mm match the recommended drawing; locating pegs are Ø0.75 mm, 3 mm pitch, about 0.55 mm protrusion
- First-to-second terminal pad pitch is 3 mm as drawn. Drawing's second-to-third recommended spacing 1.45 mm differs from KiCad's 1.50 mm by 0.05 mm; existing 0.6-mm-wide pads accommodate this small difference. No supported need to shift the stock electrical land pattern from this raster drawing
- The drawing lacks a clear actuator-position/contact truth table. Retain PWR labeling and verify left/right continuity on a first article before engraving ON/OFF direction

The linked manufacturer drawings, rather than the simplified 3D models, govern component fit. Procurement variants and assembly placement remain first-article checks.
