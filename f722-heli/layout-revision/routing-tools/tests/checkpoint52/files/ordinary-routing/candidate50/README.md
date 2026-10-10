# Complete TAIL native candidate03

Source49 reconstruction closes the actual R23.2–U12.6–U1.55 protected tree, reducing29 opens to27 with zero native errors/warnings. All156 footprint poses and558 pad records are unchanged. All28 support partitions and completed SERVO2/3, ADC, RPM and PORT_A paths are restored.

The MCU-to-clamp path is81.063747mm, with4 signal vias; clamp-to-R23 is4.6125mm. CORE has one additional via and an8.867409mm replacement branch at0.20mm. All116 new track endpoints and all5 ordinary tented0.45/0.20mm vias pass finite native entry checks.

TAIL actual-pad cut passes with0.371503mm gap;14/22 actual I/O contracts now pass, preserving every prior pass. Critical/BARO copper and missing-reference geometries remain exact49. TAIL has2.823919mm missing centerline in own-via windows and0.000224846616mm² width outside those windows, preserved and classified in signal-geometry-details.json.

See conditional-signal-review/TAIL-electrical-review.md for pinned LOW GPIO, exact ST IBIS model, component loading, historical topology and limits. This is a geometric prototype checkpoint pending owner review. Waveform, ESD-transient, AC-return and loaded-power qualification remain open; the source43 numerical power result does not apply. Earlier candidate01/02 courtyard failures are preserved separately.
