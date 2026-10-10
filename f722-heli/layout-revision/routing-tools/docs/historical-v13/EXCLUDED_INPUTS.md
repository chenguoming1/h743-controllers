# V13 excluded inputs and regeneration limits

Seven large export paths are excluded. Their exact original identities are below and in tests/checkpoint41/raw-evidence.json. No raw diagnostic container or full-audit replay is hidden in this packet. The unchanged V12 exclusions remain historical in docs/historical-v12/EXCLUDED_INPUTS.md.

| Original path | Bytes | SHA-256 |
|---|---:|---|
| `ordinary-routing/candidate39/f722-heli.native.json` | 30646992 | `e99bb7888b98c5dd44e44a04b51789ac9dcc47b3fd6b07d1446295acf5b2c577` |
| `ordinary-routing/candidate40/f722-heli.native.json` | 30686967 | `02e51d8bc3a8934ad9aa9bb0ee1b8cfb13b22f62c99bd8aec8cc8d73b410daf6` |
| `ordinary-routing/candidate40/owner-mechanical-geometry.json` | 2531610 | `8d70e211d5c1cf69cde5def0f2cb15c380cabe6e3a5f687f7378ca6e6791dcc7` |
| `ordinary-routing/candidate41/f722-heli.native.json` | 30705902 | `e5bafbcfd37556b38b686d2493d0f0b894c41f714405452b4c6b7177a8f22962` |
| `ordinary-routing/candidate41/owner-mechanical-geometry.json` | 2531621 | `36e88556da350584d43fda9d4c9408b76362b5ae23213025739598f334cc03f3` |
| `ordinary-routing/candidate41/owner-native.json` | 30705902 | `e5bafbcfd37556b38b686d2493d0f0b894c41f714405452b4c6b7177a8f22962` |
| `ordinary-routing/candidate41/reference-snapshot/native-geometry.json` | 30705902 | `e5bafbcfd37556b38b686d2493d0f0b894c41f714405452b4c6b7177a8f22962` |

## Native export recovery

Recover exact paired 39/40/41 projects and materialize included sources. Using the original KiCad 10.0.6 runtime and retained native exporter, regenerate each into a disposable workspace:

```sh
KICAD_PY -B ordinary-routing/native-tools/export_native_copper.py --board ordinary-routing/candidate39/f722-heli.kicad_pcb --out ordinary-routing/candidate39/f722-heli.native.json
KICAD_PY -B ordinary-routing/native-tools/export_native_copper.py --board ordinary-routing/candidate40/f722-heli.kicad_pcb --out ordinary-routing/candidate40/f722-heli.native.json
KICAD_PY -B ordinary-routing/native-tools/export_native_copper.py --board ordinary-routing/candidate41/f722-heli.kicad_pcb --out ordinary-routing/candidate41/f722-heli.native.json
```

Verify each output against the table before using it as a historical input. Candidate41 owner-native.json and reference-snapshot/native-geometry.json are aliases of the identical candidate41 export bytes; copying is justified only after the original digest matches. Regeneration byte identity is not claimed by packaging. On mismatch, recover the original export or perform separately reviewed rebinding; never alter the old hash.

## Mechanical export recovery

The retained `repo/f722-heli/layout-revision/scripts/export_mechanical_geometry.py` requires both the exact current board and the external published-source board SHA-256 `4da0708a4795662cc32b035a0783c70b9bdb85fc386bd4d39af33385b175667f`. That second board is not supplied by this increment. With it, run:

```sh
KICAD_PY -B repo/f722-heli/layout-revision/scripts/export_mechanical_geometry.py --board EXACT40/f722-heli.kicad_pcb --source PUBLISHED_SOURCE.kicad_pcb --out owner-mechanical40.json
KICAD_PY -B repo/f722-heli/layout-revision/scripts/export_mechanical_geometry.py --board EXACT41/f722-heli.kicad_pcb --source PUBLISHED_SOURCE.kicad_pcb --out owner-mechanical41.json
```

Verify the table digests. The original export logs identify KiCad 10.0.6+dfsg-1. The proposal-screen source additionally references its old material ledger and geometry helper; those screens are historical evidence, not a promised complete replay workflow in this delta. Exact constructor-facing proposal40/result bytes are supplied. No power calculation has been renewed.

## Honest replay limits

The 61-file paired-project and disposable preview-board recoveries are complete. Full constructors/finite-width/native-reference/mechanical audits require their declared external dependencies and original compatible runtimes. The portable verifier reruns identity/integration/support-binding helpers only. It does not claim full native geometry replay, DRC, export/refill, fresh preview rendering, JVM route search, numerical power, VCAP, fabrication or assembly qualification.
