"""Verify and reconstruct this technical packet. Does not execute numerical code."""
import argparse,gzip,hashlib,json,shutil,tempfile
from pathlib import Path

def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''): h.update(b)
    return h.hexdigest()

def member(root,name):
    p=(root/name).resolve()
    if not p.is_relative_to(root.resolve()): raise ValueError('Unsafe member path')
    return p

def copy_checked(source,target,expected_size,expected_sha):
    h=hashlib.sha256();n=0
    with target.open('xb') as out:
        for b in iter(lambda:source.read(1048576),b''):
            n+=len(b)
            if n>expected_size: raise ValueError('Decompressed size exceeds manifest')
            h.update(b);out.write(b)
    if n!=expected_size or h.hexdigest()!=expected_sha: raise ValueError('Reconstruction mismatch')

def main():
    a=argparse.ArgumentParser(description=__doc__)
    a.add_argument('--repository',type=Path,required=True)
    a.add_argument('--output',type=Path,required=True)
    opts=a.parse_args();root=Path(__file__).resolve().parent
    manifest=json.loads((root/'COMPRESSION-MANIFEST.json').read_text())
    opts.output.mkdir(parents=True,exist_ok=False)
    for row in manifest['members']:
        target=member(opts.output,row['logical_path']);target.parent.mkdir(parents=True,exist_ok=True)
        if row['encoding']=='repository-file':
            src=member(opts.repository,row['repository_path'])
            with src.open('rb') as f:copy_checked(f,target,row['logical_bytes'],row['logical_sha256'])
        elif row['encoding']=='identity':
            src=member(root,row['stored_path'])
            with src.open('rb') as f:copy_checked(f,target,row['logical_bytes'],row['logical_sha256'])
        elif row['encoding']=='gzip':
            with tempfile.TemporaryFile() as packed:
                h=hashlib.sha256();n=0
                for part in row['parts']:
                    src=member(root,part['path'])
                    if src.stat().st_size!=part['bytes'] or digest(src)!=part['sha256']:raise ValueError('Compressed part mismatch')
                    with src.open('rb') as f:
                        for b in iter(lambda:f.read(1048576),b''):packed.write(b);h.update(b);n+=len(b)
                if n!=row['compressed_bytes'] or h.hexdigest()!=row['compressed_sha256']:raise ValueError('Compressed stream mismatch')
                packed.seek(0)
                with gzip.GzipFile(fileobj=packed,mode='rb') as f:copy_checked(f,target,row['logical_bytes'],row['logical_sha256'])
        else:raise ValueError('Unknown encoding')
    print('Verified reconstruction complete; numerical execution remains disabled.')
if __name__=='__main__':main()
