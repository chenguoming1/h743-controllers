#!/usr/bin/env python3
"""Verify all chunks and restore the exact historical archive without overwriting data."""
import argparse,hashlib,json,os,re,tempfile
from pathlib import Path
EXPECTED="d1aa8519355da5bb7db5ed0ef684f238e56ce461530dec5e1d88ddf328c8b791"
SIZE=19260348
def require(ok,message):
    if not ok:raise ValueError(message)
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path);a=p.parse_args()
    root=Path(__file__).resolve().parent;m=json.loads((root/'manifest.json').read_text())
    require(m['schema']=='f722-lossless-archive-parts/v1' and m['sha256']==EXPECTED and m['bytes']==SIZE,'Archive identity mismatch')
    blocks=[];whole=hashlib.sha256();offset=0
    for i,row in enumerate(m['parts']):
        require(row['path']==f'part-{i:04d}.bin' and row['offset']==offset,'Invalid chunk name/order/offset')
        b=(root/row['path']).read_bytes()
        require(len(b)==row['bytes'] and hashlib.sha256(b).hexdigest()==row['sha256'],'Chunk mismatch: '+row['path'])
        blocks.append(b);whole.update(b);offset+=len(b)
    require(offset==SIZE and whole.hexdigest()==EXPECTED,'Reconstructed archive mismatch')
    out=a.output.resolve() if a.output else root.parent/'frozen-inputs.tar.gz'
    if out.exists():
        require(out.is_file() and out.stat().st_size==SIZE and hashlib.sha256(out.read_bytes()).hexdigest()==EXPECTED,'Refusing to overwrite different existing output')
        print(json.dumps(dict(output=str(out),sha256=EXPECTED,bytes=SIZE,existing_identical=True)));return
    require(out.parent.is_dir(),'Output parent must already exist')
    temporary=None
    try:
        with tempfile.NamedTemporaryFile(prefix='.f722-archive-',dir=out.parent,delete=False) as f:
            temporary=Path(f.name)
            for b in blocks:f.write(b)
            f.flush();os.fsync(f.fileno())
        require(hashlib.sha256(temporary.read_bytes()).hexdigest()==EXPECTED,'Written archive mismatch')
        os.link(temporary,out)  # Atomic creation; never replace an existing path.
    finally:
        if temporary is not None:temporary.unlink(missing_ok=True)
    print(json.dumps(dict(output=str(out),sha256=EXPECTED,bytes=SIZE,existing_identical=False)))
if __name__=='__main__':main()
