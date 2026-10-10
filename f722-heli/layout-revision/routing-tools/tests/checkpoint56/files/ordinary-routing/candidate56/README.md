# R4 pull-up native checkpoint from accepted55

The saved board has 12 opens, zero native errors and zero warnings. R4 moves from B(27.5,19.8),180 degrees to B(40.55,19),180 degrees, preserving its 10k/1% value and actual pad/net identities. Its complete U3.1 pull-up branch is connected; the MCU U1.33 FLASH_CS gap remains open. Remaining gaps are PORT_C 5, BOOT 2, RED 1 and flash 4.

The transaction adds 13 tracks and two ordinary tented vias, removes no source copper, and changes only R4's two pads and full footprint pose. The .20 mm R4 supply lead deliberately ends at actual C15.1. It has zero overlap with C14.1, and its contact to the retained C15 lead is wholly inside the actual C15.1 pad. The original R4 pad's parallel CORE-feed junction is restored by a separate .20 mm full-width bridge to actual C3.1. Every original power, ground and other track/via remains exact.

Native DRC, schematic parity, ERC, firmware, mechanical and process checks pass. All 16 critical groups, 26 finite new endpoints, 28 supply/ground groups and all 20 previously passing actual I/O protection cases are preserved. The actual FLASH_CS pad partition changes from three groups to two; no other pad partition changes. Read the source-bound entry/support audit and coordinated integration receipt.

The native pull-up branch measures 13.999707308 mm plus two via barrels; source-bound edge/loading and power review remain pending. Raw saved-reference deltas are preserved. This is a geometric checkpoint for owner review, not an electrically qualified release.
