# U15 replacement ground: four existing barrels

Prefer a dedicated new U15 ground barrel. All four previously reachable barrels already terminate component-specific leaves; none is a spare stitch. Reachability came from the older v1 scope and must be rechecked after the 17 cuts and RX-down reassignment.

| Existing barrel | Explicit source return | Original leaf |
|---|---|---|
| 1d7d67c9… at (25.2313,20.4005) | C17.2, 100 nF barometer VDDIO bypass | F.Cu, 0.649963 mm × 0.25 mm |
| 457a8423… at (26.1139,20.6361) | U4.5, DPS368 SDO_ADDR strap to GND; not a GND supply pin | F.Cu, 0.549988 mm × 0.25 mm |
| c4b3b59e… at (22.3,20.725) | C69.2, 1 µF +3V3_CORE bypass for DSM U11 TPS2553 input | B.Cu, 0.800000 mm × 0.40 mm |
| c8f3ea5d… at (26.2074,21.1265) | C75.2, 47 µF +5V_PERIPH bulk capacitor | B.Cu, 1.249987 mm × 0.25 mm |

Each source via has exactly the named explicit leaf and pad component, with no other explicit pad/trace contacts on F/B/In2/In3. These conclusions exclude filled GND planes deliberately. A separate U15 F trace ending directly at one of these barrels retains the old leaf but shares barrel/plane-entry impedance. Joining the old leaf or capacitor pad additionally shares its narrow copper. Eventual common-plane connectivity is a different relationship.

No candidate directly serves an IMU, MCU or ADC ground pad or their dedicated capacitor leaf. The first two place ESD common impedance beside a barometer bypass or logic reference. C69 and C75 serve power bypass/bulk roles and are not interchangeable with spare stitching. The amount of AC/ESD coupling cannot be established from topology; no shared option is qualified here.

The original U15 ground path uses three 0.25 mm tracks to via97282ff5… at(25.287,19.1104). Its source centerline length is 2.573993727 mm. V1’s 2.672503/3.237108/3.636073/3.712429 mm distances are straight distances from anchor(24.5,17.83), not routed lengths from the actual pad. No reviewed board-specific maximum return length or complete loop/inductance bound was found. Preserve both actual U15 GND-pad contacts and prefer the nearest feasible dedicated barrel, with actual trace/mask/drill clearance and fresh contact to both GND planes verified. [TI’s ESD layout guide, section2.4](https://www.ti.com/lit/an/slva680/slva680.pdf) supports a ground via immediately adjacent to the TVS ground and minimizing ground-path inductance.

The JSON contains complete UUIDs, native record hashes, exact dimensions, source receipt/schematic/netlist bindings and limits. Source PCB/native hashes remain unchanged. No router, routing graph, native operation, field solve or CAD edit ran; this is route-selection evidence only.
