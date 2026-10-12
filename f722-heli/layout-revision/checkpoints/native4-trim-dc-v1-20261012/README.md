# Native4 SCK trim and completed conditional DC evidence

This is the adopted geometric routing WIP, not a manufacturing or electrical release. Open `hardware/f722-heli.kicad_pro` with its paired schematic, board and libraries. Current board SHA256: `1b463dbb2115f5fa0d0ffada1f80fe674b1418a4ddbd661c83cb7516f334374a`; logical native SHA256: `c4d5b66eeabdc7d9e7b87715ddcb811038ce9f8b2b67a722eec578cf807fe779`.

The SCK return stitch plus two-track lead trim retains four opens, zero geometric DRC errors, three historical dangling-via warnings, clear ERC and zero schematic parity issues. The four opens are PORT_C_RX_EXT J11.1 to clamp, PORT_C_TX_MCU, PORT_C_RX_MCU and FLASH_MOSI. FLASH_SCK connects U1.34 to U3.6. Its geometric reference improvements are not SI validation. Full actual-I/O audit remains 21/22, with full RX incomplete before cut and raw false aggregates retained.

## DC result and scope

The completed original numerical result uses the stitched predecessor board `8f9d4be2fc97633bd9d83b2bc44be7cd4359eb45b90c14fbd410187292136029`, native `02c72e195b5c2cde307ec83ed587b07dc0c18565892afd2b7bf16f6602986034`. Separate independent evidence verifies exact power-domain mathematical-input equivalence to the trimmed board. No solve on the trim is claimed. Historical geometry receipts that say DC was pending remain historical; `dc/FINAL-HANDOFF.json` and `dc/INDEPENDENT-COMPLETED-TRIM-APPLICABILITY.json` provide the subsequent completed result and applicability finding.

All 294 required conditional cases pass on both 0.12 mm and 0.09 mm grids. The required supply envelope is ideal BEC 5.0 V, two receiver ports at 1 A each, 0.32 A electronics, and DSM at 20 mA classic or 500 mA capacity; USB uses 4.33 V and 0.30 A electronics without external loads. Enumerated tolerances and load distributions are preserved in `dc/model-inputs/` and `dc/compiled/ledger.json.gz`. Copper assumptions are 105 C, 0.015 mm thickness, 95% IACS conductivity and 0.015 mm plating. These are conditional model assumptions, not measured hardware guarantees.

All eleven servo illustrations remain separate from the required cases. The 7.4 V, approximately 18.56 A single-feed illustration fails the 6.0 V PCB-pad floor: J2–J5 are 5.864–5.879 V. The overall conditional static screen remains false. Approximately 11 A source-current illustrations exceed a 10 A continuous source limit even where their voltage tests pass. There is no exact 10 A solved case. These results do not qualify the servos, source, harness or connector.

## Reproduction and provenance

`CONTENT-MANIFEST.json` inventories payload bytes. `SOURCE-PROVENANCE.json` binds original source hashes separately from public review-copy hashes. Public receipt paths are relative, and private execution coordination is omitted. Such normalized copies must not be mistaken for original byte-identical receipts. Exact unchanged runtime modules, native sources and input hashes are retained wherever no normalization is needed.

Current native and auxiliary JSON are lossless gzip streams. `reconstruction/json_reconstruction.py` and hash-bound JSON patches reproduce predecessor logical JSON or the trim logical JSON from the pinned prior checkpoint. The compiled DC input bundle includes the original predecessor native gzip, so its exact stored-byte identity is also available. `dc/compiled/ledger.json.gz` is a losslessly compressed compiled ledger; decompress before use. The runtime and geometry code, corrected model plans, physical assumptions, scope, port audit, support and source bindings are included. Original execution launchers with machine-specific controls are omitted; recipes and saved outputs remain reviewable. Reproduction requires the original documented KiCad/Python numerical dependencies and deliberately adapted relative paths/hash bindings for normalized inputs. No portable end-to-end rebuild or fresh numerical run was tested during packaging.

`dc/reduced-result.json.gz` retains reduced numerical evidence. `RAW-RESULT-REFERENCE.json` binds the full raw result (stored and logical size/hash), preserved locally; assembled operators and the 31.6 MB raw result are not duplicated in this checkpoint. The reduction script is included. Small original dependency references point to unchanged paths in PR26 head `ea6c6a23311846052071b4acea2f2ea54091b4d1`.

Remaining gates include the four opens, full RX protection, SCK return/SI, shared C75 ESD/transients, RED/J11 assembly qualification, stock-I2C timing/sink-guarantee gaps, thermal/AC behavior, manufacturing and final board/flight qualification.
