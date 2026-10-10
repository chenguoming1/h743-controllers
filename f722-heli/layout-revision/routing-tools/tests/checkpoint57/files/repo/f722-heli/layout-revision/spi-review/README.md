# Stock Nexus SPI source review

This portable source-only packet supports review of the stock SPI clocks and the constraints for eventual complete routing. It is prepared for owner review; nothing in this packet publishes changes or modifies the PCB, firmware, settings or fitted components.

Start with [stock-spi-review.md](stock-spi-review.md). The initialized stock clocks are 13.5 MHz for the ICM-42688-P on SPI1 and 27 MHz for the W25N01GVZEIG on SPI2 at the default 216 MHz core clock. The flash is at the MCU SPI2 frequency ceiling. Frequency compliance does not establish signal qualification.

The original pad inventory's board hash exactly equals canonical69 / accepted69: `9cf04c88ebd31d7e2c12bdb8a9f80e01b615a7bdb94a73fc2234208a2e0a14c8`. Its binding is recorded in [native-pad-identities.json](native-pad-identities.json). This inventory identifies terminals, not connected routes, lengths, load bounds or completed electrical verification.

## Contents

- `stock-source-index.json`: pinned firmware/target source URLs and exact Git blob identities; `firmware/` contains only the 14 small reviewed source files plus its upstream license.
- `datasheet-source-index.json`: manufacturer-document links, revisions and hashes of the reviewed bytes. Full PDFs, extracted datasheet text, screenshots and downloaded web trees are excluded.
- `calculate_clocks.py` and `clock-calculations.json`: source-derived power-of-two arithmetic including SPI2's prescaler clamp. This is a transcription, not a firmware build or peripheral emulator.
- `verify_bundle.py` and `bundle-manifest.json`: file allowlist/hashes, upstream blob verification and arithmetic reproduction. Python 3 standard library only; no network, KiCad, JVM or solver is required.
- `THIRD_PARTY_NOTICES.md`: upstream attribution and license boundaries.

## Reproduce

Run from any working directory:

```sh
python3 /path/to/spi-review/verify_bundle.py
python3 /path/to/spi-review/calculate_clocks.py
```

Optionally bind the packet to a supplied project, without writing it:

```sh
python3 /path/to/spi-review/verify_bundle.py --board /path/to/layout-revision/hardware/f722-heli.kicad_pcb --parts /path/to/layout-revision/hardware/parts.json
```

The optional checks require exact byte identity. A mismatch means the supplied file is outside this packet's binding; it does not establish an electrical failure. Update the review against changed source before claiming it applies.

The report preserves the distinction between specified maximums, characterization conditions and typical pin capacitances. Unknown complete-net loading, fast-edge response, stock IMU output-level loading, installed settings and physical timing remain open. Firmware and hardware changes are not proposed or authorized by this packet. No completed routing, fabrication readiness or flight qualification is claimed.
