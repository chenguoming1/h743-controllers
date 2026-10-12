"""Proposed output-only adapter. No solver entry point; no global int guard change."""
import gzip
import hashlib
import json
from pathlib import Path

def verify_result(path):
    path = Path(path)
    logical_sha, logical_bytes = hashlib.sha256(), 0
    with gzip.open(path, 'rb') as stream:
        while block := stream.read(1048576):
            logical_sha.update(block)
            logical_bytes += len(block)
    stored_sha = hashlib.sha256()
    with path.open('rb') as stream:
        while block := stream.read(1048576):
            stored_sha.update(block)
    return {'encoding': 'gzip', 'logical_bytes': logical_bytes,
            'logical_sha256': logical_sha.hexdigest(),
            'stored_bytes': path.stat().st_size, 'stored_sha256': stored_sha.hexdigest(),
            'decompression_verified': True}

def write_result(path, result):
    path = Path(path)
    logical_sha = hashlib.sha256()
    logical_bytes = 0
    encoder = json.JSONEncoder(indent=2, allow_nan=False)
    # Matches json.dumps(result, indent=2, allow_nan=False) + '\n' exactly.
    with path.open('xb') as raw:
        with gzip.GzipFile(fileobj=raw, mode='wb', filename='', mtime=0, compresslevel=6) as packed:
            buffer = bytearray()
            for text in encoder.iterencode(result):
                block = text.encode('utf-8')
                logical_sha.update(block)
                logical_bytes += len(block)
                buffer.extend(block)
                if len(buffer) >= 65536:
                    packed.write(buffer)
                    buffer.clear()
            buffer.extend(b'\n')
            packed.write(buffer)
            logical_sha.update(b'\n')
            logical_bytes += 1
    restored_sha, restored_bytes = hashlib.sha256(), 0
    with gzip.open(path, 'rb') as stream:
        while block := stream.read(1048576):
            restored_sha.update(block)
            restored_bytes += len(block)
    if restored_sha.digest() != logical_sha.digest() or restored_bytes != logical_bytes:
        raise ValueError('Lossless result gzip verification failed')
    compressed_sha = hashlib.sha256()
    with path.open('rb') as stream:
        while block := stream.read(1048576):
            compressed_sha.update(block)
    return {'encoding': 'gzip', 'logical_bytes': logical_bytes,
            'logical_sha256': logical_sha.hexdigest(),
            'stored_bytes': path.stat().st_size, 'stored_sha256': compressed_sha.hexdigest(),
            'decompression_verified': True}
