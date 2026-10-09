"""Reconstruct a hash-pinned historical replay PCB from a published PCB.

The JSON data is a list of non-overlapping line replacements, not executable
instructions. Both complete input and output byte hashes are mandatory.
"""
import argparse
import hashlib
import json
from pathlib import Path


def reconstruct(base: bytes, delta: dict) -> bytes:
    if delta.get("schema") != "f722-historical-source-delta/v1":
        raise ValueError("Unsupported delta schema")
    if hashlib.sha256(base).hexdigest() != delta["base_board_sha256"]:
        raise ValueError("Published base PCB hash mismatch")
    lines = base.decode("utf-8").splitlines(keepends=True)
    result, cursor = [], 0
    for edit in delta["replacements"]:
        start, end = edit["start_line"], edit["end_line"]
        if not (isinstance(start, int) and isinstance(end, int)
                and cursor <= start <= end <= len(lines)):
            raise ValueError("Invalid or overlapping replacement range")
        if not isinstance(edit["text"], str):
            raise ValueError("Replacement must be text")
        result.extend(lines[cursor:start])
        result.append(edit["text"])
        cursor = end
    result.extend(lines[cursor:])
    data = "".join(result).encode("utf-8")
    if len(data) != delta["target_bytes"]:
        raise ValueError("Reconstructed PCB length mismatch")
    if hashlib.sha256(data).hexdigest() != delta["target_board_sha256"]:
        raise ValueError("Reconstructed PCB hash mismatch")
    return data


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-board", type=Path, required=True)
    parser.add_argument("--delta", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    data = reconstruct(args.base_board.read_bytes(), json.loads(args.delta.read_text()))
    with args.out.open("xb") as output:
        output.write(data)
    print(json.dumps({"output_sha256": hashlib.sha256(data).hexdigest(),
                      "bytes": len(data), "status": "Exact historical replay input only"}))
