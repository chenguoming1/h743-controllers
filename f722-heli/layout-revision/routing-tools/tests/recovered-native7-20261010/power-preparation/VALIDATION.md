# Validation summary

This is disabled preparation. Power remains STALE; no final electrical
acceptance or numerical release is claimed.

## Completed on the retained native7 source

- Verified exact GitHub source/file identities and selected archive-member
  hashes. Reconstructed the reference ledger with its original exact file hash.
- Audited all 107 contacts / 109 modeled pads against both PCB text and native
  export, including UUID, net, copper layers and global coordinates. All 93
  power/control/sense contract entries also match.
- Confirmed exactly two contact-layer changes: R42.1 and R44.2 are on B.Cu.
- Verified unchanged identities for all 305 cases, fixed physics, loads,
  voltage floors, VCAP loops, mesh grids and convergence/resource guards.
- Passed five mesh-free tests covering complete contact coverage, rejection of
  TPS2553 EN4 used as IN6, falsified layer/position data and an incorrect board
  hash. Original package verification and clean extraction roundtrip passed.

Board SHA-256:
`a7355c26018a7bea66b77ccdc5201c2042a96b8e6820179fc5684dc72e170b4f`

Native SHA-256:
`53ddf869c36da4a026880c6b3346dd1ddb304aaabaa948b20f1e66fc3db62505`

## Publication supplement

The exact environment receipt records the four required package versions via
explicit `python-deps`. Its SHA-256 is
`0ccdda292fc738bb7b59b9ea30734b6a3194855032efe473236bc82fe9815349`.
It supersedes the earlier default-interpreter package observation. No board,
model audit, native operation or numerical job was rerun to create this variant.
Historical source bytes and prepared model bytes remain identical.

`PACKAGE-MANIFEST.json` and `seal_recovery.py --verify` cover the publication
files. Hash verification establishes integrity and declared identity, not an
independent electrical qualification.

## Still required

Final routing/refill, fresh applicable source gates and support binding, a new
implementation/model review and a fresh bounded numerical run. Old USB/DSM
results with incorrect TPS2553 or DPS368 terminals remain invalid. Source43's
18.560272 A single-feed illustration still failed all four 6.0 V servo-pad
floors outside the 10 A continuous envelope. No old solve/pass count replaces
the final source-bound assessment.
