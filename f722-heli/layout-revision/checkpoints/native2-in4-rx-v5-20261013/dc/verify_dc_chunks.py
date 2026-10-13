#!/usr/bin/env python3
"""Verify ordered, lossless DC chunks; optionally reconstruct the saved gzip."""
import argparse
import gzip
import hashlib
import io
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent

class ChunkStream(io.RawIOBase):
    def __init__(self,paths):self.paths=iter(paths);self.stream=None
    def readable(self):return True
    def readinto(self,buffer):
        written=0
        while written<len(buffer):
            if self.stream is None:
                try:self.stream=next(self.paths).open('rb')
                except StopIteration:break
            count=self.stream.readinto(memoryview(buffer)[written:])
            if not count:self.stream.close();self.stream=None
            else:written+=count
        return written
    def close(self):
        if self.stream:self.stream.close()
        super().close()

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,help='Optional new result.json.gz path')
    args=parser.parse_args()
    manifest=json.loads((HERE/'RAW-RESULT-CHUNKS.json').read_text())
    if args.output:assert not args.output.exists(),'Use a new output path'
    combined=hashlib.sha256();stored=0;paths=[]
    out=args.output.open('xb') if args.output else None
    try:
        for index,row in enumerate(manifest['chunks']):
            assert row['index']==index and row['bytes']<=8*1024**2
            path=HERE/row['path'];paths.append(path);part=hashlib.sha256();count=0
            with path.open('rb') as stream:
                for block in iter(lambda:stream.read(1024*1024),b''):
                    part.update(block);combined.update(block);count+=len(block);stored+=len(block)
                    if out:out.write(block)
            assert count==row['bytes'] and part.hexdigest()==row['sha256'],path
    finally:
        if out:out.close()
    assert stored==manifest['stored_bytes'] and combined.hexdigest()==manifest['stored_sha256']
    logical=hashlib.sha256();count=0
    with io.BufferedReader(ChunkStream(paths),buffer_size=1024*1024) as chain:
        with gzip.GzipFile(fileobj=chain,mode='rb') as stream:
            for block in iter(lambda:stream.read(1024*1024),b''):logical.update(block);count+=len(block)
    assert count==manifest['logical_bytes'] and logical.hexdigest()==manifest['logical_sha256']
    print(json.dumps({'status':'PASS','ordered_chunks':len(paths),'stored_bytes':stored,'stored_sha256':combined.hexdigest(),'logical_bytes':count,'logical_sha256':logical.hexdigest(),'numerical_solver_executed':False,'saved_gzip_reconstructed':bool(args.output)},sort_keys=True,indent=2))

if __name__=='__main__':main()
