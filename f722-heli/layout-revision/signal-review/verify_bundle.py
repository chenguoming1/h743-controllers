"""Verify the exact compact-public-bundle allowlist and byte hashes."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
manifest = json.loads((ROOT / "bundle-manifest.json").read_text())
expected = set(manifest["allowlist"])
actual = {p.relative_to(ROOT).as_posix() for p in ROOT.rglob("*") if p.is_file()}
if actual != expected:
    raise SystemExit(f"File inventory differs: missing={sorted(expected-actual)}, unexpected={sorted(actual-expected)}")
for row in manifest["files"]:
    data = (ROOT / row["path"]).read_bytes()
    if len(data) != row["size_bytes"] or hashlib.sha256(data).hexdigest() != row["sha256"]:
        raise SystemExit(f"Byte verification failed: {row['path']}")
index = json.loads((ROOT / "stock-source-index.json").read_text())
for row in index["files"]:
    data = (ROOT / "stock-ba6c7e3" / row["path"]).read_bytes()
    git_hash = hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()
    if git_hash != row["git_blob_sha1"]:
        raise SystemExit(f"Upstream source identity failed: {row['path']}")
for row in index["licenses"]:
    data = (ROOT / row["path"]).read_bytes()
    git_hash = hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()
    if git_hash != row["git_blob_sha1"]:
        raise SystemExit(f"Upstream license identity failed: {row['path']}")
print(f"Verified {len(manifest['files'])} hashed files, exact allowlist, and all bundled upstream source/license identities.")
