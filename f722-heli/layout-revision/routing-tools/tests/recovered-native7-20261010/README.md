# Recovered native7 routing sources

This source-only checkpoint preserves the tools and proposed routing geometry used to continue the seven-open F722 candidate published in PR19. It does not change either the canonical eleven-open board or the isolated seven-open board, and it does not select the experimental recipes as PCB copper.

The published paired project and all 73 reconstruction dependencies were recovered with exact Git blob and SHA-256 checks. All 129 payload entries in its manifest and the losslessly compressed routing transaction verified. The official KiCad 10.0.6+dfsg-1 runtime was restored from 54 pinned Debian packages authenticated against a signed Debian snapshot index.

Both native exports reproduced their published hashes exactly:

- Canonical11 PCB: `454b7bb2454695b49c039f3d97e5edefb1946912363bab00ef5ced6ba2b0ea16`
- Canonical11 native export: `98f7d08c700cbc6e31cdd7f522be86091521ee4f2b7c760a9080541ade08cebd`
- Isolated7 PCB: `a7355c26018a7bea66b77ccdc5201c2042a96b8e6820179fc5684dc72e170b4f`
- Isolated7 native export: `53ddf869c36da4a026880c6b3346dd1ddb304aaabaa948b20f1e66fc3db62505`

Fresh KiCad checks reproduced seven missing connections, zero geometric errors, seven dangling-copper warnings, zero schematic-parity items and zero ERC violations. The recorded transaction's 201 segments, 32 vias, 558 pads and 156 footprints passed input validation.

The new geometry adapter requires exact source hashes before loading. It preserves all 2,384 native objects and reconstructs all 100 recorded recipes into their 233 native members without renaming the source records or repairing their polygons. Its connectivity control reproduces all seven native opens. Wider support-track controls verify that .18/.20/.25 mm branches use their actual width for clearance checks.

The proposed centerlines are reconstruction inputs. Their original experimental packets were not recovered; their previous results do not qualify the reconstructed proposals. Every selected successor still requires complete donor restoration, finite contact and actual bonded protection checks, native DRC/ERC, return-path review, and fresh source-bound electrical analysis. Current power/VCAP results remain stale for the seven-open geometry. The inherited rounded-end-only U2.9 ground entry and all PR19 manufacturing, reference, timing and bench limitations remain explicit.

The UART source review checks the stock pin-swap detection through HAL configuration to CR2.SWAP for all three UART pairs. It does not verify an installed firmware binary or physical operation. No firmware or pinout changes are introduced here.

No fabrication, assembly, electrical or flight qualification is claimed.

## Reproduction

Use the PR19 checkpoint's `RESTORE.md` to restore its exact project and regenerate both native exports. For the layout below, place the repository checkout under `repo/`, the official pinned runtime under `kicad10-runtime/`, and choose `recovered-native7/` as the new restoration workspace. Copy this checkpoint's `files/` contents into that rebuild root while preserving their relative paths. Use Python 3.12 with `numpy==2.2.6` and `shapely==2.2.0`; KiCad native export uses the separate pinned runtime Python.

Run the recovered adapter's input-only command before any geometry calculation. The adapter accepts explicit `--workspace`, `--native`, `--board`, `--transaction` and `--logical-map` paths when using another directory layout. Its neighboring validation script reproduces the finite-width negative controls and seven-open connectivity check. The C inventory generator recreates full native records from the hash-bound exports; only its compact receipt is stored here.

These sources provide reproducible planning inputs. They do not execute a router merely by importing the adapter, change the published board, or turn past planning results into new validation.
