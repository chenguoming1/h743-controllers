# Isolated C ground-layer span assessment

No few-millimetre bridge is supported by the exact saved northern-RX/In2 failure. No plane signal was constructed or selected.

The conditional northern RX-down In2 trunk connected (25.397615, 10.812554) to the retained R34.1 barrel (28.963321, 20.840573), but disconnected both actual C MCU targets. Its northern F approach also separately blocks the original R3 CS leaf. Re-layering the whole inner trunk would therefore neither be short nor cure the supply/R3 conflict.

For both failed MCU functions, the saved complete source-side and target-side legal new-via unions are at least **7.824945 mm** apart. Existing-source-to-opposite-domain lower bounds are **11.134527 mm for TX** and **14.044287 mm for RX**. The retained RX target barrel is at least **14.941668 mm** from a legal source-side new-via domain. These are saved-contour distances before plane obstacles or new-route checks; the witness points are not accepted via centers. The companion JSON contains exact endpoints, source/target node sets, native UUIDs, source hashes and method.

A future short bridge on In1 would cut GND zone c956a476-e320-4f09-9832-420df749bd95 and affect F/In2 return references; In4 would cut ee652b71-6147-4d53-abc1-8530e0b19eaf and affect B/In3. A .127 mm trace with .127 mm clearance removes a nominal .381 mm-wide ground corridor before other clearances and reserves. No current capacity or reference continuity follows merely from low baud or one connected plane polygon.

## Required proof if a different context yields a shorter span

1. An isolated span would have to connect two proven source/target ordinary regions of the same logical function, with existing same-function barrels or fully legal new .45/.20 tented barrels. These saved domains do not provide a few-mm candidate; do not silently join different protected branches or reuse a foreign-net via.

2. If a genuinely shorter candidate emerges in a changed context, bind exact centerlines, full native cuts/added records and endpoints, then require the complete actual C pad-to-pad function and all displaced ordinary donors. Re-evaluate the independent original R3/C12 issue; changing the northern inner trunk alone cannot repair its failed F approach.

3. For .127 signal width and .127 clearance, nominal same-layer GND exclusion is at least .381 mm wide before exporter/fabrication reserves. Native refill must determine the actual new void including rounded ends, existing antipads, clearances and plane islands; saved-fill subtraction is a planning calculation only.

4. Check the affected GND plane component partition, terminal membership, annular contacts and minimum surviving necks with global physical drills subtracted. Compare current paths around both slot ends, including return sharing and newly combined voids. No safe current capability follows solely from positive plane connectivity.

5. Rerun source-bound DC/current analysis with actual stackup, conductivity, drill/pad contacts and unchanged load/supply definitions. Rebind all five existing VCAP copper-to-U1-ground loops (U1.12, U1.18, U1.31, U1.47, U1.63); historical source43 results and a historical35mohm limit are not available margin on this changed board.

6. On In1, inspect F.Cu and In2.Cu routes whose return paths would cross the slot, including IMU supplies/returns and other fast signals. On In4, inspect B.Cu and In3.Cu, including MCU/flash entries and VCAP/local ground references. The signal occupying a former GND layer has no newly guaranteed adjacent solid-GND layer: quantify actual coplanar/distant return geometry and transition return vias.

7. Use actual firmware mode and external-driver rise/fall/load evidence, complete signal length, series resistance and receiver thresholds for SI checks. UART baud is not an edge-rate bound. Keep protected U15 role/cut/no-bypass checks explicit, especially for a C_RX_EXT upstream versus downstream span.

8. Any future plane signal requires a separately scoped geometry/importer/native acceptance implementation. The current ordinary-only route helper/importer cannot silently accept In1/In4. Fresh refill/DRC/ERC/parity/positive full-width contacts/reference/power review precedes selection.

## Firmware evidence

The pinned [Nexus target](https://github.com/rotorflight/rotorflight-targets/blob/1d9cb4dc6f85c7895c2b089f4b8aa776ca3d3bd3/configs/RDMS-NEXUS_F7.config) binds serial TX3 to PB11 and RX3 to PB10. It does not establish baud or edge time. Supporting [current official F7 UART source](https://github.com/rotorflight/rotorflight-firmware/blob/5c46583ee228a0a406c7ac20d5ec881b39136bd7/src/main/drivers/serial_uart_stm32f7xx.c) uses LOW speed through IOCFG_AF_PP for normal mode and HIGH for bidirectional mode; [the IO definitions](https://github.com/rotorflight/rotorflight-firmware/blob/5c46583ee228a0a406c7ac20d5ec881b39136bd7/src/main/drivers/io.h) establish that macro. Equivalence to the installed stock firmware is not established. Incoming RX slew depends on the external driver.

Stop here: no 10+ mm plane routing is proposed. This is a bounded negative for the measured fixed context, not a global impossibility claim. The coordinated ordinary C12/R3 correction remains the active alternative.
