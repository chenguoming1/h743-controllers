# Conditional DC replay for native1 MOSI/BARO

The current source-bound run passes all 294 required conditional cases on both
0.12 mm and 0.09 mm grids, all 15 impedance checks, and all five VCAP resistance
checks. Its raw overall result remains false: the single-feed all-cyclic 905X
capacity illustration draws 18.560994254 A and leaves four servo board pads
between 5.863718452 V and 5.878528194 V, below the 6 V floor.

Current PCB SHA256: b31e6b9ca47e8e5a0b8967ec25f8390a66541b0c374ebedde77a39380e7d73ca.
Current native logical SHA256: 6c0485bf7e1098d0f51d8d63ca7e7a5ee6a26c21656192c0c967cd6e32917261.
Exact hardware and compressed native exports are required beside this directory,
in ../hardware/ and ../native/. This source has 330 actual drilled objects,
including the two new MOSI through vias. Every physical drill removes copper on
its spanned layers irrespective of electrical net. The current saved fill is used.

This package contains the complete numerical source, corrected case plan,
terminal registry, material/settings inputs, resolved ledger, and all frozen
inputs consumed by numerical preflight. The actual USB/DSM supply entry remains
IN pin 6 to OUT pin 1; EN pin 4 remains a separate enable probe. All 305 cases,
107 finite contacts, five loops, both grids, numerical limits and convergence
criteria match the completed run. The model contract is
285961cbf0d79d0ae28e2e2a84b256380da8c6a922b6977a2495b7554c922a95.

The numerical Python modules and three model inputs are byte-exact copies from
the completed run. NORMALIZATION.json records original/public identities and
changed JSON pointers or text lines for documentary copies. Coordination-only
receipt fields are removed. The historical native DRC controller snapshot is
represented by an explicitly labeled original-producer identity record; it is
never executed by the numerical replay. The separate hardware recipe supplies
fresh native checks. Known file paths
become relative paths. Other historical locators become content identities or
opaque identifiers. Hash links to changed documentary copies are updated
explicitly. Only the ledger's freeze-manifest link changes. Historical result
hashes still identify the exact original completed run. No generated mesh or
cache is included, and no numerical replay was performed for this packaging.

Use Linux, CPython 3.12.14, and the pinned versions in requirements.txt. The
following source-only verification uses Python's standard library. It checks all
package/external input hashes and regenerates the complete model for exact
comparison with the ledger. This command was tested during packaging:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -B dc/replay.py verify
```

The following heavy replay commands are provided but have not been executed for
this package. Prepare repeats numerical preflight and the 107-contact finite
port audit. Run requires its prepared receipt and solves the full two-grid model:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -B dc/replay.py prepare --out /tmp/f722-native1-dc-replay
PYTHONDONTWRITEBYTECODE=1 python3 -B dc/replay.py run --out /tmp/f722-native1-dc-replay
```

The launcher uses fresh output directories, one CPU/thread, 4 GiB address space,
a local exclusive lock, 600 seconds for prepare and 1,800 seconds for run. It
requires 800 MiB output-volume launch admission and preserves 128 MiB free on
both source/output volumes. Its combined package/output cap is 512 MiB. All
generated output stays under /tmp. Changed inputs, missing dependencies,
resource stops and incomplete results fail closed. Logs and failed output remain
available. Exit 1 represents a complete overall-false result; inspect its exact
failed cases. Exit 2 or a resource stop is not a qualified result. New output
hashes bind the portable manifest and new execution, rather than reproducing
historical provenance byte for byte.

The exact historical raw gzip is supplied separately by this checkpoint as
ordered lossless chunks no larger than 8 MiB under dc/raw/. This source package
contains no duplicate raw payload. The raw stored SHA256 is
79774d3af8c62c3e8a3b06dd89de85a78c6f3abcdf43015e3dc8c53ba5b184ba;
the logical JSON SHA256 is
adc0b6e38cfe09bc2d65fc7288e4d949c69981ffef1ed02eaaddde7f6ab14761.
Historical raw references in normalized evidence identify that reassembled
artifact; the raw result is not needed to regenerate the numerical solution.
The separate native hardware recipe regenerates geometry and its checks.
Documentary producer snapshots describe prior checks and are not commands for
that hardware replay.

This result is a conditional fixed-temperature DC screen at 105 C, with
0.015 mm copper/plating and 95% IACS. Ideal terminal lands, annuli and package
current distribution remain model assumptions. The maximum fine-grid VCAP loop
is 26.324988 milliohms against a 35 milliohm limit. Global density, layer-loss or
barrel-current values do not establish local neck ampacity. AC return behavior,
startup, thermal performance, flight, manufacturing and final board qualification
remain outside this result. The raw inherited native contact-applicability flag
remains false; its exact current VX-window supplement is separately retained.
