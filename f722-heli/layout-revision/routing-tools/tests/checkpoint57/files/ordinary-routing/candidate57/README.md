# R2-to-SW1 native checkpoint from accepted56

The saved board has 11 opens, zero native errors and zero warnings. R2 moves from F (16, 7.7), 0 degrees to F (40.2, 6.2), 270 degrees, preserving its 2.2k/1% value and actual pad/net identities. Its complete SW1.2 pull-down branch is connected. Actual MCU U1.60 remains open. Remaining gaps are PORT_C 5, BOOT 1, RED 1 and flash 4.

The transaction adds two tracks and no vias, removes only R2's exclusive 0.25 mm F ground leaf, and changes only R2's two pads and full footprint pose. A short 0.25 mm return terminates on the retained actual GND via at (39.15, 6.54). The original R2/C31 shared ground via and C31 B lead remain exact, as do all original ADC/MID/RED/SERVO and other source routes.

Native DRC, strict schematic parity, ERC, firmware, mechanical and process checks pass. All 16 critical groups, four finite new endpoints, 28 supply/ground groups and all 20 previously passing actual I/O protection cases are preserved. The actual BOOT0 pad partition changes from three groups to two. Read the source-bound entry/support audit and coordinated integration receipt.

This is a geometric checkpoint for owner review. Complete MCU BOOT routing, startup/noise qualification, numerical power/VCAP and all-signal reference review remain pending. No seven-via exploratory BOOT/ADC geometry is imported.
