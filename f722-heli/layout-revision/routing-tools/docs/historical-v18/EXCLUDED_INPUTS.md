# V18 excluded inputs and replay limits

Thirteen source paths are deliberately excluded as raw native geometry, placement-only boards, duplicate isolated accepted board, or original vendor PDF. Their exact original identities are retained below and in raw-evidence.json. Omission does not imply their checks were rerun.

| Path | Bytes | SHA256 |
|---|---:|---|
| checkpoint30-placement-preview/preview.kicad_pcb | 835825 | `5642f0502f5031f8b509f9eb82a90e3e4a0027b8134ca75b044c355a93a4b960` |
| checkpoint30-review/snapshot/native-geometry.json | 31854475 | `fcb2e385f54000b494426678c2ddbe4a28e08924ef773722ebbe78f528e1678f` |
| checkpoint32-review/snapshot/native-geometry.json | 31750970 | `d0da380fc5dcb397e5021ee14062ca33f61abbd63916ae84458dd28f5612acdf` |
| independent-core-voltage-review/sources/STM32F722-DS11853-Rev9.pdf | 4773854 | `0b5686b8f9a62d894e13a1feb75bdad3d7a822c2f8881fc83455d2b78d049fb5` |
| ordinary-routing/candidate47/f722-heli.native.json | 31750970 | `d0da380fc5dcb397e5021ee14062ca33f61abbd63916ae84458dd28f5612acdf` |
| ordinary-routing/candidate47/reference-snapshot/native-geometry.json | 31750970 | `d0da380fc5dcb397e5021ee14062ca33f61abbd63916ae84458dd28f5612acdf` |
| ordinary-routing/candidate48/f722-heli.native.json | 31854475 | `fcb2e385f54000b494426678c2ddbe4a28e08924ef773722ebbe78f528e1678f` |
| ordinary-routing/candidate48/owner-mechanical-geometry.json | 2531314 | `661eba597731907b376ad17286ec81ca2eaf53b1971892f70485e05b473082e9` |
| ordinary-routing/candidate48/owner-native.json | 31854475 | `fcb2e385f54000b494426678c2ddbe4a28e08924ef773722ebbe78f528e1678f` |
| ordinary-routing/candidate48/reference-snapshot/native-geometry.json | 31854475 | `fcb2e385f54000b494426678c2ddbe4a28e08924ef773722ebbe78f528e1678f` |
| ordinary-routing/tests/adc-bus45/candidate01/f722-heli.kicad_pcb | 1397754 | `dcdd0e5655d098ceaffa7f40b6a21f1ca101429ac8eb142c50fa96df86697e68` |
| ordinary-routing/tests/adc-bus45/candidate01/reference-snapshot/native-geometry.json | 31854475 | `fcb2e385f54000b494426678c2ddbe4a28e08924ef773722ebbe78f528e1678f` |
| repro-30-placement/hardware/f722-heli.kicad_pcb | 699163 | `dfc501ddbe8706292950d503f7c9ca57f72cb47c46a93b85873e5e8677d1f94f` |

The routed candidate47 and48 paired projects themselves are recoverable exactly through sessions/recovery-v18. The excluded isolated candidate01 routed board is byte-identical to accepted48, but materialization does not silently substitute it. Placement-only boards differ intentionally and are separately hash-bound. Vendor PDF text and official URL are retained with the conditional ADC screen.

Full native geometry/refill/DRC/cut/reference/placement replay needs matching omitted inputs and runtime dependencies. The compact standard-library tests validate recovery, source bindings, a limited independent parser transaction comparison and ADC arithmetic; they do not qualify power, noise, EMC, manufacturing or flight.

Unrelated unaccepted flash/servo/PORT_C work, private owner notes, full raw diagnostics, caches, binaries, runtime packages and Git metadata are excluded. Immutable V17 remains the historical source dependency; no prior accepted package is replaced or rewritten.
