# V19 excluded inputs and replay limits

The following 11 raw inputs are omitted; their exact identities remain in raw-evidence.json. The accepted routed 48/49 boards themselves are reconstructed through paired recovery. Omitted local KiCad preferences are not required for manufacturing source recovery.

| Path | Bytes | SHA256 |
|---|---:|---|
| checkpoint29-review/snapshot/native-geometry.json | 32018826 | `9ef0ea396bf264065621efbf937e1a42edeeda14d57614f8eedd4087c5378f69` |
| independent-core-voltage-review/sources/STM32F722-DS11853-Rev9.pdf | 4773854 | `0b5686b8f9a62d894e13a1feb75bdad3d7a822c2f8881fc83455d2b78d049fb5` |
| ordinary-routing/candidate48/f722-heli.native.json | 31854475 | `fcb2e385f54000b494426678c2ddbe4a28e08924ef773722ebbe78f528e1678f` |
| ordinary-routing/candidate48/reference-snapshot/native-geometry.json | 31854475 | `fcb2e385f54000b494426678c2ddbe4a28e08924ef773722ebbe78f528e1678f` |
| ordinary-routing/candidate49/f722-heli.kicad_prl | 2296 | `aac7e9a596de705a929a62143128dff32bca962176b59697f12f7392961eee54` |
| ordinary-routing/candidate49/f722-heli.native.json | 32018826 | `9ef0ea396bf264065621efbf937e1a42edeeda14d57614f8eedd4087c5378f69` |
| ordinary-routing/candidate49/owner-mechanical-geometry.json | 2531314 | `d0ff005698072e053da0ac3663f388e5562e1162cea3e8220e83dd3b2c0f71e6` |
| ordinary-routing/candidate49/owner-native.json | 32018826 | `9ef0ea396bf264065621efbf937e1a42edeeda14d57614f8eedd4087c5378f69` |
| ordinary-routing/candidate49/reference-snapshot/native-geometry.json | 32018826 | `9ef0ea396bf264065621efbf937e1a42edeeda14d57614f8eedd4087c5378f69` |
| ordinary-routing/tests/port-a48/candidate01/f722-heli.kicad_pcb | 1404431 | `15499b28bb63a8c2326c8c7e73dbac4198b8333b05325ab35653825848ae9069` |
| ordinary-routing/tests/port-a48/candidate01/reference-snapshot/native-geometry.json | 32018826 | `9ef0ea396bf264065621efbf937e1a42edeeda14d57614f8eedd4087c5378f69` |

Native geometry/export/DRC/refill/reference/cut/access replay needs matching omitted inputs and runtime dependencies. The portable verifier does not perform these operations. The vendor PDF text and official source URL remain included. Unaccepted PORT_B/TAIL/flash/servo experiments, private notes, broad raw diagnostics, binary runtimes and Git metadata are excluded.

Some frozen planning helpers retain references to peer reservations. Their searches are not self-contained in this compact packet. The final accepted proposal, constructor and paired source remain sufficient construction inputs after restoration of the source native export. Immutable V18 supplies prior accepted history; it is not rewritten.
