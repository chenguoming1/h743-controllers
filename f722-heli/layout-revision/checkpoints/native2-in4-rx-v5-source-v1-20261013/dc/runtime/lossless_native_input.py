"""Exact return-stitch native input storage adapter, never a geometry transform."""
import gzip
import hashlib
from pathlib import Path

STORED_SHA256 = 'c193b7e9988bbf0d72bf08365ba01268244a349db41c832a5a6785f91b8f0cef'
STORED_BYTES = 6905333
LOGICAL_SHA256 = 'ae89889c542bca2c96abbdd48e66e70215ab7da84ceb9bccf7d619f8739825a5'
LOGICAL_BYTES = 37015511

def stored_sha256(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        while block := stream.read(1048576):
            h.update(block)
    return h.hexdigest()

def read_bytes(path):
    path = Path(path)
    if path.suffix != '.gz':
        return path.read_bytes()
    if path.stat().st_size != STORED_BYTES or stored_sha256(path) != STORED_SHA256:
        raise ValueError('Compressed native input bytes/hash differ from exact source')
    with gzip.open(path, 'rb') as stream:
        raw = stream.read(LOGICAL_BYTES+1)
    if len(raw) != LOGICAL_BYTES or hashlib.sha256(raw).hexdigest() != LOGICAL_SHA256:
        raise ValueError('Decompressed native input bytes/hash differ from exact source')
    return raw

def sha256(path):
    if Path(path).suffix == '.gz':
        return hashlib.sha256(read_bytes(path)).hexdigest()
    return stored_sha256(path)

def receipt(path):
    raw = read_bytes(path)
    if Path(path).suffix != '.gz':
        raise ValueError('Compressed native source required for storage receipt')
    return {'encoding':'gzip','stored_sha256':STORED_SHA256,'stored_bytes':STORED_BYTES,
            'logical_sha256':hashlib.sha256(raw).hexdigest(),'logical_bytes':len(raw),
            'decompression_verified':True}
