# Preserved native1 reference measurement sources

This compact archive preserves the formulas and fixed inputs behind the completed reference and actual-return measurements. It does not repeat the measurements, qualify signal integrity, or change the board. The checkpoint evidence directory holds the measured results and engineering disposition.

The actual-return code and bounded routing function, proposal, normalized replay map, fixed inputs, and two frozen geometry/domain outputs are retained. Candidate PCB/native/auxiliary inputs are the existing paired ../hardware and ../native artifacts; no native exports are duplicated here. The source board/native identities belong to ../../native2-in4-rx-v5-20261013.

Run `python3 replay.py --verify` for a file-hash-only check. The replay adapter can prepare a separate actual-return run only when supplied explicit PCB, native, auxiliary, dependency, and execution-lock paths. Preparation does not execute geometry. No numerical or geometry execution was performed for this preservation checkpoint.

## Deliberate replay gaps

- The all-track script is an archival source, not a portable entry point. Its required full source projection cache is preserved byte-for-byte at all-track-reference/inputs/source-all-track-projection.json.gz (SHA-256 47ffdd7f7f7c54bf0bbd4ae7506b609c985ada5332c5eb1a26ca443b5cb07a52, 8,232,878 bytes). It was not already present under that exact Git blob in the predecessor public tree. The compact source-ground-projection is also retained for actual-return; it contains planes only and cannot substitute for the complete cache. Decode the full cache with `gzip -dc all-track-reference/inputs/source-all-track-projection.json.gz > source-all-track-projection.json`; the expected logical SHA-256 is 28cffc7159eebeded3b39da73c232650ff35fe84b66a8ccb335d0a3557619675. No regeneration was performed or is needed to recover this source input.
- The candidate all-track projection cache is also omitted. It is a generated product of the preserved extraction code and paired native export, not a unique source input.
- All-track runtime paths, dependency environment, lock and output placement still require an explicit adapter. The preserved prepare.py and prior measure_reference.py document the original transformation; neither was run. The template's standalone historical manifest/context is not included and is not claimed runnable.
- generic_route_core.py retains its complete historical source. Its native11_context import is not provided for standalone import. actual-return/review_actual.py reads and compiles only its route function AST and supplies its own paths2 helper, so that unused module is not an input of actual-return replay.
- Shapely and its binary environment are external. Exact dependency versions and numerical replay are not verified by this archive.

MANIFEST.json binds original and public file identities, the source packet manifest, AST comparisons and normalization. Source path constants and operational/documentation text are the only Python differences. All formulas and other executable AST nodes are preserved. Public proposal/input changes only remap locators and corresponding hashes; scientific values remain unchanged.
