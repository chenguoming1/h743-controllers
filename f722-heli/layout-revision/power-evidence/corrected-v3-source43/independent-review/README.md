# Independent candidate43 corrected-power result review

The completed review passed for the declared conditional DC scope. This directory preserves the verification performed on 2026-10-09 at approximately 19:08–19:09 UTC. It was persisted afterward at the owner's request; packaging did not rerun the analysis or any numerical solver.

`verify_result.py` preserves the Python body executed inline through standard input. It verifies the original workspace's current canonical source and its exact source-bound job. It deliberately refuses after canonical changes; it is not a portable historical replay or authority to rebind the result to a later board.

The original command used this working directory:

`/workspace/scratch/8a35c1f26232/f722-layout-rebuild/power-terminal-correction-v3`

Its environment prefix and interpreter invocation were:

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=../python-deps OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python3 -B - <<'PY'
# Exact body preserved in ../independent-candidate43-power-result-review/verify_result.py
PY
```

An equivalent reproducible invocation from that same working directory is:

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=../python-deps OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python3 -B - < ../independent-candidate43-power-result-review/verify_result.py
```

Do not run with Python optimization; the checks use assertions. The script reads the existing 299 MiB result, checks its evidence and recomputes classifications and reported numerical guards. It does not assemble meshes or solve circuits. It calls the sealed model's identity and strict report routines in addition to independently recomputing every physical probe voltage/window, voltage-grid guard, impedance sensitivity and VCAP guard. The loaded-field checks inspect recorded residual evidence, not new field solutions.

`review-receipt.json` records the observed results and identities. `observed-output.json` preserves the JSON emitted by the completed command. `execution.json` records the exact environment, working directory, standard-input execution and original exit status. `MANIFEST.json` inventories this separate review directory.

All 294 required cases, ten actual supply-pad windows in every case, five VCAP loops and stated numerical guards pass. All 11 illustrations remain separately classified. Four distinct servo floor failures in one J6-feed-lost illustration remain visible on both grids; runner exit 1 and the overall false result are preserved. No current-polytope interior-extrema, thermal, startup, AC, package-current-sharing, production or flight qualification follows. Later board changes invalidate current applicability and require their own source review.
