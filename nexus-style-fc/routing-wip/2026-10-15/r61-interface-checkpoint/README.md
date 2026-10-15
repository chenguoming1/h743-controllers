# r61 routing and separate mechanical progress: unfinished

Open the [current experimental project](../../current/hardware/nexus-style-fc.kicad_pro), [PCB](../../current/hardware/nexus-style-fc.kicad_pcb), or [short guide](../../current/README.md).

The stable current directory is a byte-exact copy of accepted r61, SHA256 `5a51610cc1569958442f97407e11533b646b1e0d8997d86356b8968dce50487e`. Native KiCad 10.0.7 refill/save reports **2 clearance errors, zero opens and zero electrical/footprint-filter parity findings**. The exact unchanged schematic is bound to its ERC 0 receipt. Both remaining gaps are the J4 VSYS via against C_RX/C_TX, 0.1073/0.0927 mm. Six complete local transactions remove six r60 findings with no new or worsened pair. All-visible checks retain 13 off-center, five footprint-type and 54 silk warnings. No exclusion or severity waiver was introduced.

[Native DRC](lineage/r61-six-clearances/native-drc.json), [complete verification](lineage/r61-six-clearances/verification.json), and the all-visible diagnostic are sealed with the source-bound copper/return checks. All 24 external ports, four relocated annular entries, 2,656 untouched direct contacts, all 96 shield regions, LDO/local returns and exact USB reference projection are preserved.

## Separate mechanical work

The [new right-hand donor correction](mechanical/main-right-vias-02/verification.json) has **24 native errors and zero opens/physical parity findings**. Its original GND via is restored before native loading and moved clear of the new S1 pad. Complete retained copper net identities, finite main-plane contacts and all four external donor ports pass. This is still an unaccepted mechanical redesign, separate from the two-error current route. The matching [child correction](../usb-interface-checkpoint/mechanical/child-copper-01/verification.json) retains zero errors/opens/ERC, with 11 courtyard and 11 footprint-filter warnings. Physical fit, fixture capability, solder/current, strength and vibration tests remain pending.

### Historical diagnostic correction

The [rejected-baseline audit](mechanical/native-net-reassignment-audit/README.md) records an automatic GND-to-S1 reassignment of via `3bc1d32f-634e-4d77-9c5d-f6bdd353e76c` during KiCad LoadBoard in historical mechanical initial/replay/main-signal-01 files. Those archived native results are genuine diagnostics but do not prove source-net invariance, and remain rejected mechanical baselines. Accepted routing r60/r61 is unaffected. No historical receipt is overwritten. The 45-to-34 mechanical count change before this ten-error correction was an r61 rebase, not eleven additional mechanical fixes.

## Qualification hold

The approved C27/C31 capacitor pair and D5 0.400 mm move are being validated as one atomic successor and are **not included** in this frozen r61. Its original C27 effective-capacitance gate therefore remains. Canonical hardware remains unchanged at 627 inherited errors; the original header retains 11 edge errors.

USB uses explicit 0.170 mm inner / 0.150 mm launch widths and tapers. Its varying reference/coupling and actual production-stack impedance remain unqualified; no 90-ohm or USB-compliance claim is made. Sixteen pasted vias / seventeen contacts, power/thermal/transient/current, assembly, U2 orientation/FSYNC and connector mapping gates remain. Existing CAM/CPL are stale/historical, not manufacturing releases. Do not fabricate, assemble or fly.
