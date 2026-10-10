# Verified incremental importer: source-only publication v1

This immutable handoff preserves the already verified importer. It contains source, contracts, host tests, a host smoke verifier, two exact plans, and compact historical verification. It contains no board, native export, copied project, candidate directory, active/expired owner lease, or full-object proof receipt. The inactive lease template is deliberately unusable.

## Materialization contract

Do not execute the source directly from this staging directory. Restore the native7 project and official runtime using the existing PR19 checkpoint procedure. Install these files into `recovered-native7/recovery-importer/` under that restored workspace root. The existing root must contain `kicad10-runtime/`, `repo/f722-heli/layout-revision/checkpoints/joint-native7-20261010/`, and the exact `recovered-native7/ordinary-routing/tests/native13-access/joint-native-import11-v1/candidates/published-reference02/` project/native export. The importer validates every required source identity before use.

The replacement plan is stored as deterministic gzip solely to keep the publication compact. Decompress it byte-for-byte to `identity-replacement-plan-v1.json` in that installation directory before checking or using it. Do not reserialize or reformat either plan: exact plan bytes participate in native UUID derivation. Its required uncompressed SHA-256 is `91ce7b1e5e6d00ad7b2d865d5e34f61c15aa6204aa737712d89757c03b2d0f1b`.

```python
from pathlib import Path
import gzip, hashlib
root = Path("recovered-native7/recovery-importer")
raw = gzip.decompress((root / "identity-replacement-plan-v1.json.gz").read_bytes())
assert hashlib.sha256(raw).hexdigest() == "91ce7b1e5e6d00ad7b2d865d5e34f61c15aa6204aa737712d89757c03b2d0f1b"
with (root / "identity-replacement-plan-v1.json").open("xb") as stream:
    stream.write(raw)
```

`README.md` is the unchanged verified-workspace documentation. Its historical `candidates/` references describe local smoke evidence deliberately excluded here. `verification-summary-v1.json` carries the exact smoke board/native output hashes and qualification limits; its original `files` hash bindings refer to the installed, uncompressed filenames. No tests or native operations were repeated to prepare this publication.

`MANIFEST.json` inventories every publication file except itself with bytes, SHA-256 and Git blob SHA-1. Copying these files does not publish or modify an external repository. Keep this frozen bundle unchanged; future changes belong in a new versioned handoff.
