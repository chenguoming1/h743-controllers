# Restore the exact frozen power inputs

The publication connector rejected the original 19,260,348-byte archive because its base64 request exceeded the16MiB transport limit. These three binary chunks preserve every byte; no evidence has been omitted or recomputed.

From the corrected-v3-source43 directory, run:

```sh
python3 frozen-inputs.parts/restore.py
python3 -B verify_package.py
```

The restorer verifies each ordered chunk and the complete archive SHA256, refuses a different existing destination, and atomically creates frozen-inputs.tar.gz. An identical existing archive is verified and retained. The original package MANIFEST.json, verifier, source inventories and evidence remain byte-identical and apply after reconstruction. The restored archive is ignored by Git because these chunks are its repository representation.

Original SHA256: d1aa8519355da5bb7db5ed0ef684f238e56ce461530dec5e1d88ddf328c8b791

This is packaging only. It adds no routing, numerical power, hardware or qualification result.
