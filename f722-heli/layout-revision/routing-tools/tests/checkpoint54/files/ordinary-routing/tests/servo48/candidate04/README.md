# Complete SERVO1 native candidate04

The exact source17 reconstruction closes R20.2–U12.1–U1.56 and reduces17 opens to15, with zero native errors/warnings. Board SHA-256: `755545e8198e9a3649c0e07533c23e67010d91ab6a8b09556d7463e064ac89eb`.

All136 new track endpoints and six ordinary tented0.45/0.20 mm vias pass finite native entry checks. All28 support partitions,20 completed signal groups,16 critical nets, strict schematic parity, ERC, firmware, native process and declared pose gates pass. Actual I/O cuts pass19/22, adding SERVO1 with0.143294148 mm gap and preserving every prior pass. R50 shifts only +0.25 mm inward;155 other full footprints, both original crystal grounds, ADC and CORE geometry remain exact.

The protected SERVO1 copper totals44.120258 mm; the drawn MCU-to-clamp branch is18.058336 mm with two vias. Four exact outside-window reference width fragments total0.000134787127 mm²; centerline outside own windows is zero. The raw USB_N width delta is retained and classified entirely within unchanged own-via windows. Full source-bound evidence is in signal-geometry-details.json and reference-region-review.

Read conditional-signal-review/SERVO1-electrical-review.md and conditional-support-review/NATIVE-SUPPORT-REVIEW.md. U12 shares a1.681160 mm/0.25 mm lead and existing via with eFuse control returns. ESD coupling, waveform, AC return and fresh loaded-power/VCAP qualification remain open. This is a geometric prototype checkpoint pending independent owner adoption, not electrical release. Earlier failed/incomplete routing and support alternatives remain preserved outside this sealed directory.
