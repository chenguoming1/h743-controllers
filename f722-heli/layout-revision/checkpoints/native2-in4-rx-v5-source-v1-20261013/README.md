# Native2 v5 portable-source supplement

This add-only source supplement provides the portable DC and finite reference/return recipes for the existing native2 In4 RX v5 prototype checkpoint. It changes no PCB, schematic, native export, raw numerical result, operating setting or acceptance disposition.

The [accepted evidence checkpoint](../native2-in4-rx-v5-20261013/README.md) remains the design and recorded-result source. Its PCB is SHA-256 `7d9af57e9b22064fc6b2fd9cde4f2f5b72dc252cdbb1b104e706472bfdbbcdcb`. The older [source3 checkpoint](../native3-r35-cleanup-v1-20261012/README.md) supplies the exact predecessor exports. No hardware, native exports, raw DC chunks, generated meshes or caches are duplicated here.

## Verified during packaging

- Package and external input hashes, decompressed native identities, and Python syntax.
- Exact regeneration of the DC model's 305 cases (294 required and 11 illustrative), 107 contacts, 15 networks and five VCAP loops from the three unchanged corrected model inputs.
- Byte identity of all ten numerical runtime modules and three model inputs against the completed solve; only external freeze paths and the ledger's freeze-manifest link change for placement.
- AST identity of the selected pure geometry functions and streaming reader against the reviewed original measurement source.

These are source, hash and mesh-free model checks. **The portable numerical preflight, finite-port audit, full solve and five-stage geometry replay have not been run during packaging.** Their explicit future commands and resource limits are provided in [dc/README.md](dc/README.md) and [reference/README.md](reference/README.md). The historical results remain current evidence; this supplement makes their selected workflows reproducible from public inputs without claiming a new successful scientific replay.

From this supplement directory, read-only verification is:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -B dc/replay.py verify
PYTHONDONTWRITEBYTECODE=1 python3 -B reference/run_review.py
```

Use the exact documented Python/scientific-library versions for future heavy replay. No install or network step runs automatically. Outputs go to isolated new locations; recorded inputs must remain immutable.

`PLACEMENT-NORMALIZATION.json` distinguishes the upstream portable packages from the additional public-relative placement changes. Their original normalization ledgers remain intact. Scientific values, route UUIDs, measured WKB, selected geometry expressions and solved-model definitions are not changed. Documentary producer snapshots are provenance, not alternate launchers.

## Retained engineering limits

Two connections remain open: FLASH_MOSI and PORT_C_RX_EXT. All 294 required conditional DC cases passed both grids, with 15 sensitivity comparisons and five VCAP copper-loop checks passing. The overall static screen remains false for the retained approximately 18.56 A lost-J6-feed illustration and its four servo board-pad voltage failures. Required material/contact/source/load assumptions and measured finite return margins remain explicit in the evidence checkpoint.

Portable source availability does not establish AC/ESD equivalence, ampacity, thermal or assembly/process tolerance, first-article behavior, manufacturing release or flight qualification. Fast-edge receiver and simultaneous-switching tests remain targeted bench work. The approved 400 kHz I2C choice keeps its overshoot caveat; 385 kHz remains pending. Later MOSI/RX_EXT geometry needs a new source-bound applicability review.
