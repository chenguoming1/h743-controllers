"""Recover exact historical replay inputs from the hash-pinned accepted75 project.

Python 3 standard library only. Delta operations are UTF-8 literals or
[byte offset, byte count] copies from the checked base; no code is evaluated.
"""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re


def digest(data):
    return hashlib.sha256(data).hexdigest()


def check(data, expected, label):
    if digest(data) != expected:
        raise ValueError(label + " SHA-256 mismatch")


def compact_metadata(data):
    """Deterministically restore historical single-line footprint properties."""
    starts = re.compile(rb'(?m)^\t\t\(property "(?:MPN|Manufacturer|LCSC|Supplier)"')
    tokens = re.compile(rb'"(?:\\.|[^"\\])*"|\(|\)|[^\s()"]+')
    result, cursor = [], 0
    for match in starts.finditer(data):
        start = match.start() + 2
        if start < cursor:
            raise ValueError("Overlapping property spans")
        depth, pieces, previous = 0, [], b"("
        for token in tokens.finditer(data, start):
            value = token.group()
            depth += (value == b"(") - (value == b")")
            pieces.append((b"" if previous == b"(" or value == b")" else b" ") + value)
            previous = value
            if depth == 0:
                break
        else:
            raise ValueError("Unclosed property")
        result.extend((data[cursor:start], b"".join(pieces)))
        cursor = token.end()
    result.append(data[cursor:])
    return b"".join(result)


def reconstruct(base, delta):
    if delta.get("schema") != "f722-historical-source-copy-delta/v1":
        raise ValueError("Unsupported delta schema")
    check(base, delta["base_sha256"], "Base file")
    transform = delta.get("base_transform")
    if transform:
        if transform["name"] != "compact-footprint-metadata/v1":
            raise ValueError("Unsupported base transformation")
        base = compact_metadata(base)
        check(base, transform["sha256"], "Transformed base")
    wanted = delta["target_bytes"]
    if type(wanted) is not int or wanted < 0:
        raise ValueError("Invalid target length")
    result, length = [], 0
    for operation in delta["operations"]:
        if isinstance(operation, str):
            piece = operation.encode("utf-8")
        elif (isinstance(operation, list) and len(operation) == 2
              and all(type(v) is int for v in operation)):
            offset, count = operation
            if offset < 0 or count < 0 or offset + count > len(base):
                raise ValueError("Invalid copy range")
            piece = base[offset:offset + count]
        else:
            raise ValueError("Invalid delta operation")
        length += len(piece)
        if length > wanted:
            raise ValueError("Reconstructed length exceeds target")
        result.append(piece)
    data = b"".join(result)
    if len(data) != wanted:
        raise ValueError("Reconstructed length mismatch")
    check(data, delta["target_sha256"], "Reconstructed target")
    return data


def relative_path(value):
    path = PurePosixPath(value)
    if path.is_absolute() or not path.parts or any(p in ("..", ".") for p in path.parts):
        raise ValueError("Unsafe manifest path")
    return Path(*path.parts)


def prepare_project(base_project, source, packet):
    manifest = json.loads((packet / "paired-files.json").read_bytes())
    if manifest["schema"] != "f722-historical-paired-files/v1":
        raise ValueError("Unsupported paired-file manifest")
    selected = manifest["sources"][source]
    outputs = {}
    for name, info in manifest["required_base_files"].items():
        path = relative_path(name)
        data = (base_project / path).read_bytes()
        check(data, info["sha256"], name)
        if len(data) != info["bytes"]:
            raise ValueError("Base file length mismatch: " + name)
        if name in selected["deltas"]:
            entry = selected["deltas"][name]
            delta_bytes = (packet / relative_path(entry["file"])).read_bytes()
            check(delta_bytes, entry["sha256"], "Delta " + name)
            data = reconstruct(data, json.loads(delta_bytes))
        outputs[path] = data
    return outputs


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_subparsers(dest="mode", required=True)
    project = modes.add_parser("project", help="Recover a complete paired replay project")
    project.add_argument("--base-project", type=Path, required=True)
    project.add_argument("--source", choices=("candidate09", "candidate12"), required=True)
    project.add_argument("--out", type=Path, required=True, help="New output directory")
    single = modes.add_parser("file", help="Recover only one exact file")
    single.add_argument("--base-file", type=Path, required=True)
    single.add_argument("--delta", type=Path, required=True)
    single.add_argument("--out", type=Path, required=True, help="New output file")
    args = parser.parse_args()
    if args.mode == "project":
        if args.out.exists():
            raise FileExistsError("Output directory must not exist")
        outputs = prepare_project(args.base_project, args.source, Path(__file__).resolve().parent)
        # Check every base, delta and target before creating any output.
        args.out.mkdir(parents=True, exist_ok=False)
        for relative, data in outputs.items():
            destination = args.out / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            with destination.open("xb") as stream:
                stream.write(data)
        board = outputs[Path("f722-heli.kicad_pcb")]
        print(json.dumps({"source": args.source, "files": len(outputs),
                          "board_sha256": digest(board), "board_bytes": len(board),
                          "status": "Exact historical replay project; not adopted layout"}))
    else:
        data = reconstruct(args.base_file.read_bytes(), json.loads(args.delta.read_bytes()))
        with args.out.open("xb") as stream:
            stream.write(data)
        print(json.dumps({"sha256": digest(data), "bytes": len(data)}))


if __name__ == "__main__":
    main()
