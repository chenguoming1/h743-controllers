# Native support binding for SERVO1 candidate04

This final review binds board `755545e8198e9a3649c0e07533c23e67010d91ab6a8b09556d7463e064ac89eb` to source17 `71d33748909bb960c5829973642272460607d8521831a6212975f7de6790d660`. All18 proposed support segments match saved native track records exactly. Native refill, 15/0/0 DRC,136 finite endpoints, six finite via entries, all28 support groups and declared R50 pose pass. The earlier `PREFERRED-QUARTER-SHIFT.md` is retained as preconstruction analysis; its pending native checks are superseded by this binding. Its transient and electrical limitations remain open.

## U12, eFuse and crystal returns

U12.2 previously used 2.227500 mm of0.25 mm F.Cu into its own via(11.27,10.89). That via and its two leads are explicitly removed. U12 now reaches existing GND via `60399785-45a9-4db4-9287-e86acbded333` at(13.5984,13.4847) through2.513660 mm of0.25 mm F.Cu: (12.5,11.8875)→(12.5,12.72)→(13.5984,12.92)→via.

R51 is390 kΩ/1% from U5.2/OVCSEL through R51.1, with R51.2 grounded. Its revised return is3.838234 mm:2.157074 mm of0.20 mm F.Cu into junction(12.5,12.72), then the same1.681160 mm of0.25 mm copper and via as U12. R52 is750 Ω/1% from U5.9/ILM through R52.1; R52.2 approaches the same via separately over2.517386 mm of0.20 mm F.Cu, versus3.860858 mm before. R51's old path was1.750005 mm. The exact outer-layer graph contains U12.2, R51.2 and R52.2, with this single first via.

U5's actual ground reference is pin8 at(12.96,16.725). Its original0.15 mm F.Cu route through(13.5,16.9),(13.65,16.94),(13.85,17.02),(14.15,17.02) to its own via(14.15,17.23) stays exact. U5.4 is PGTH tied to GND, not an additional manufacturer GND pin; its original0.20 mm lead to its separate via(10.76,18.0) also stays exact. Both have positive saved contact to In1/In4, as do the shared control return and all116 accepted plated ties. Exact lengths and records are in `native-binding.json`.

Clamp current can therefore develop a transient voltage across the new common U12/R51 lead and shared R51/R52 via, relative to U5's separately stitched internal ground. That could disturb OVCSEL/ILM behavior and eFuse operation. DC continuity and low DC resistance do not demonstrate ESD equivalence or transient immunity. This remains an explicit prototype qualification limit. A separate dedicated U12 tie is not established by this sealed transaction; any later bounded check is a separate improvement, not a retroactive claim of equivalence.

Both original Y1 case grounds remain exact: Y1.2 has1.050018 mm/0.25 mm B.Cu into(10.2299,11.7982); Y1.4 has1.049967 mm/0.25 mm B.Cu into(13.1048,13.3702). Neither joins the new outer-layer U12 lead or its via. The latter is0.506706 mm from the shared eFuse-control via; common-plane coupling remains possible. The rejected crystal-shared and crystal-pad-bridge alternatives survive separately outside this sealed candidate and are not adopted.

C18.2 remains1.455793 mm/0.20 mm B.Cu to(10.2,15.35); C19.2 remains1.250025 mm/0.25 mm B.Cu to(10.874,9.9139), already shared with C9.2. All original HSE signal, Y1/R9/C18/C19 records are exact. The retained YJX TAXM8M4RDBCCT2T/C400090 sheet marks resonator pins1/3 and grounded pins2/4; no internal2/4 bond is assumed. No crystal startup or immunity qualification follows from geometry alone.

All CORE copper, U12.5 supply entry and the full existing decoupling network and support partitions remain exact. There is no new dedicated U12 capacitor or assumed local AC return. C30 is the ADC_BEC220 nF filter and stays exact; C50 is the actual3.3 nF eFuse DVDT capacitor. ADC_BUS and ADC_DIV_MID topology and native objects also stay exact.

## R50, EN and raw supply

R50 remains1.5 MΩ/1%, F.Cu,0°, shifted +0.25 mm inward to(11.95,13.6). The complete VX_RAW local feeder is3.800000 mm/0.30 mm, its branch toR50.1 is1.341462 mm/0.30 mm, and its branch to existing via(9.7,14) is0.782624 mm/0.25 mm. Before lengths were3.990000,0.882456 and0.956347 mm. No VX_RAW via is added.

R50.2→U5.1/EN changes from2.556360 mm/0.20 mm to3.706286 mm/0.127 mm F.Cu, zero vias. Pinned [TI RevC](https://www.ti.com/lit/ds/symlink/tps25947.pdf) gives ±0.1 µA EN leakage, rising UVLO at most1.223 V and a ≥350 kΩ pullup recommendation under the documented above5V/reverse-input conditions. R50 max1.515 MΩ yields0.1515 V leakage sensitivity. With declared35 µm copper and nominal20°C resistivity, new EN resistance is14.375 mΩ, with1.44 nV drop at0.1 µA or0.223 µV under a loose23 V/1.485 MΩ current bound. This only supports negligible added DC drop. Startup, noise, contamination leakage, clamp interaction, power handling and fresh numerical power/VCAP remain unqualified.
