# Stock Nexus I2C source review

This compact bundle is intended for `layout-revision/signal-review/`. It preserves the stock firmware and current component choices. No executable firmware or compiled host binary is distributed.

Start with [the electrical review](stock-i2c-review.md). [Final-route requirements](final-native-i2c-requirements.json) identify pending native connectivity, load estimation and bench checks. [Arithmetic](stock-i2c-calculations.json) is reproducible from the included Python script and pinned C source.

The stored [native inventory](native-bus-inventory.json) is explicitly the **historical 158-unconnected checkpoint**, PCB SHA-256 `0ab556b406d336cb94fe54060048bf3e78f8a14dfcc3086d83b7e0232ccb8c86`. Both I2C nets were unrouted there. A later canonical checkpoint has 123 unconnected items and unchanged fitted bus topology; this historical inventory does not certify that checkpoint's routing or capacitance.

## Reproduce from `layout-revision/`

```sh
python3 signal-review/verify_bundle.py
python3 signal-review/reproduce_stock_timing.py
python3 signal-review/calc_stock_i2c.py
python3 signal-review/verify_bundle.py
```

Requirements: Python 3 and a host C compiler available as `cc`. The timing runner creates and removes its binary in a temporary directory. The arithmetic script rewrites only `stock-i2c-calculations.json` deterministically. Neither command accesses hardware, changes firmware, reads the PCB, or downloads sources.

The expected 54 MHz result is `TIMINGR=0x00800D26`. The additional 60 MHz output is a diagnostic check of the upstream function, not approval to overclock. The requested 800 kHz setting gives about 790.17 kHz under the algorithm's assumed edge/filter timings; actual hardware rate must be measured.

The SHA-256 file manifest excludes its own hash to avoid self-reference; its `allowlist` still includes `bundle-manifest.json`. Verify the manifest's externally supplied hash when byte identity of the package is required.

## Evidence boundaries

- A 50 pF total-per-line allocation and 100 ns edge targets are engineering requirements, not measured results or device capacitance guarantees.
- DPS368 output-low operation at 3.3 V and ordinary 800 kHz Fast-mode Plus operation remain unqualified by the reviewed tables.
- Conditional internal-pull-up calculations do not establish an enabled DPS368 SDA/SCL pull-up.
- The regulator's 3.432 V initial-accuracy corner does not bound all rail ripple or transients.
- Actual firmware/register/clock readback, completed-route estimation and first-article validation remain pending.

Public source URLs, versions and hashes are in [the firmware index](stock-source-index.json) and [the datasheet index](datasheet-source-index.json). PDFs and screenshots are excluded. A vendor may later change bytes at a live URL, so the reviewed-byte hash remains the identity reference.

## Attribution and licensing

The eight upstream source files under `stock-ba6c7e3/src/` are byte-identical to Rotorflight commit `ba6c7e3e328b91a549bf6ca87c9eadd7006b6d94`; Git blob IDs are verified by the included script. Their original copyright and license notices remain intact. The unmodified upstream [GPLv3 license text](stock-ba6c7e3/LICENSE) is included; individual source notices permit GPLv3 or later where stated. The ST startup source retains its separate redistribution conditions in its header. These vendor/upstream sources are not relicensed by the hardware project.

`platform.h` and `timing_probe.c` are small host-only review harness files, not replacements for production firmware headers. The source copies support audit and reproduction; they are not a complete firmware source checkout. Infineon's inspected driver and the Nexus target are referenced by exact public commits rather than copied again into this bundle.
