# F722 joint routing trial checkpoint 11, WIP

Accepted native hardware is unchanged at 11 opens. Its PCB SHA-256 remains `454b7bb2454695b49c039f3d97e5edefb1946912363bab00ef5ced6ba2b0ea16`. This checkpoint preserves conditional source recipes and selected evidence, not an adopted native candidate. Speculative copper is incomplete; final native, power, reference, return and AC qualification remain pending.

The verified PR #17 head is `59cc52206d285b145fee15dcc683896aaf9d2951`, with frozen tree `84f15313494e580e633f6eac731fc0aa524404ad`. Local commit `d1d7dc9e3a0d85b4f442abdc589ccbd9710ff5dc` has the identical tree. Recovery reads by exact tree identity and works with any repository containing that tree.

## Selected source

The selected final model is `ordinary-routing/tests/native13-access/composite_native11_dedicated_IMU_CS.py`, bound by `RECOVERY-native11-joint-v5.json`. It composes the corrected R42/C31 cluster, exact native SBUS restoration, declared-width C/TX/WP v2, complete ordinary-layer BOOT, and a complete dedicated-IMU/DSM/CS exchange. The stored final exchange reports five paths, three vias, preserved actual CS/DSM/BOOT/C-TX/WP terminal partitions, and two independent IMU return barrels. Its imported helper hashes are checked by the recovery tool.

The BOOT seal includes U1.60, R2.1 and both physical SW1.2 pads. The new final accessor rejects absent released divider pads and ambiguous physical pad keys. R43/R44 divider reconstruction, remaining SPI signals and C branches/MCU links are still unfinished. Nominal finite-clearance receipts do not establish manufacturing robustness or final saved-fill connectivity.

`export_joint_transaction11.py` and `dedicated-joint-recorded-transaction11.json` preserve the exact recorded constructor arguments: 89 new copper records, 18 changed pads and the four explicitly missing R43/R44 pads. Every selected new shape matches its recorded constructor bytes, retaining the original bends. The receipt binds the exporter and imported model hashes. This is a future builder input, not a native candidate or DRC pass; the exporter was not rerun during checkpoint verification.

## Preserve the corrections

- `R42-C31-full-supply12757.json` and `construct_cluster_full_supply12757_failed_Fprefix.py` are the failed inherited front-BOOT model. The selected `R42-C31-full-supply12757-corrected.json` and its constructor use the actual B.Cu MCU entry.
- C/TX/WP transaction v1 preserves the earlier incomplete declared-width audit. Transaction v2, its declared-width receipt and the WP ownership proof are selected. The original native SBUS segment is restored exactly; the unnecessary private bend is removed.
- The failed single-switch-pad BOOT sealing script is retained separately. The selected seal checks both physical pads of SW1.2.
- `review-imu-return11` reviews the superseded diagonal shared-return proposal. It remains rationale and manufacturer evidence. The selected successor restores independent returns and uses a 0.254 mm straight outward U2.7 lead. The historical 0.20 mm drill departure from literal >8 mil guidance, retained 0.25 mm U2.6 lead, and 0.006592423108496984 mm² outward body strip remain explicit. No TDK, AC or noise compliance claim is made.
- `review-joint-identities11.json` and its exact reviewed source snapshots preserve the bounded historical identity review. Its UUID-only provenance and inherited accessor findings describe that snapshot; the final successor fixes the accessor and completion ledger. The historical C constructor remains valid only in its earlier pre-BOOT scope.

## Verify and recover without executing geometry

Use Python 3 with assertions enabled. All commands below use only the standard library and read the Git base without changing its index or refs.

```sh
python -B tools/verify_and_materialize.py --base-repo /path/to/repo
python -B tools/verify_and_materialize.py --base-repo /path/to/repo --out /new/isolated/workspace
```

The output directory must not exist. The tool verifies the exact package allowlist, Git base tree, every raw/compressed payload, source syntax, selected recipe hashes, native input hashes, included review inputs and external manufacturer hash metadata before writing. It restores original workspace-relative paths. The accepted PCB is obtained from the base commit. Two exact native JSON exports and the candidate44 bootstrap PCB are included losslessly. `native44_geometry.py` eagerly loads candidate44 before `native11_context.py` replaces its model, so both historical bootstrap files are required even though they do not remain the selected geometry. Every individual package file is below 8 MB.

For a later authorized source replay, use CPython 3.12 with the versions in `requirements.txt`, installing dependencies into a separate environment or the restored workspace's `python-deps` directory. From the restored `ordinary-routing` directory, put `../python-deps`, `tests/native13-access`, `tests/portc51` and `tests/boot56` on `PYTHONPATH`. Importing the final composite constructs geometry and was not performed during checkpoint verification. The old divider/census scripts require the explicit `R42-C31-full-supply12757-corrected.json` argument; their unselected historical default is not bundled.

## Reproducibility limits

`raw-evidence.json` records the exact recoverable files; `DEPENDENCIES.json` records local imports, file inputs, classified output-only paths and omitted historical generators. Upstream selected receipts are frozen inputs. This package does not include every earlier sweep, optional failed-search graph or upstream generator, and does not claim end-to-end regeneration of historical receipts. Historical absolute provenance strings are preserved unchanged. The V5 parent-manifest digest is a lineage reference, not a claim that the entire prior diagnostic collection is bundled.

Manufacturer PDFs, full extracted text and captured product-page HTML are not redistributed. `EXTERNAL_MANUFACTURER_EVIDENCE.json` preserves source URLs, versions, original sizes and exact hashes; the concise review and comparison metadata are included. These documents are not executable geometry inputs. Repeating the document review requires obtaining the cited revisions separately and matching their hashes. The original review manifest remains an immutable historical record, with its intentionally omitted entries declared explicitly. Verification checks those external identities, not unavailable external file contents or continued URL availability.

Stored pass/fail results were inspected and hash-bound, not rerun. No geometry graphs, routing, native export/refill/DRC, numerical power, FEM, reference or electrical job ran during checkpoint verification. The historical exact Python build, binary wheels and GEOS build are not bundled. Timing-bounded searches may return different paths on another runtime; exact restored recipe and receipt bytes are the reproducible deliverable. Constructor scripts often refuse to overwrite an existing receipt, so any future rerun must use another isolated copy and retain the frozen evidence separately.

This is an unfinished source-only checkpoint. The speculative transaction has not been adopted into native hardware.
