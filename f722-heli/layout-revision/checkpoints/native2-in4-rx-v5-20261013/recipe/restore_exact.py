#!/usr/bin/env python3
"""Reconstruct the exact saved PCB from a pinned public source and text patch.

This restores recorded bytes; it does not refill copper or rerun engineering
checks. The separate replay_native.py performs the actual KiCad construction.
"""
import argparse
import gzip
import hashlib
import json
import re
from pathlib import Path

HERE=Path(__file__).resolve().parent.parent

def apply_exact(source,patch):
    before=source.splitlines(keepends=True)
    lines=patch.splitlines(keepends=True)
    assert lines[0].startswith('--- ') and lines[1].startswith('+++ ')
    out=[];cursor=0;i=2
    while i<len(lines):
        header=re.fullmatch(r'@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@\n',lines[i])
        assert header,lines[i]
        old_start,old_count,new_start,new_count=(int(x) if x is not None else 1 for x in header.groups())
        begin=old_start-1 if old_count else old_start
        assert cursor<=begin
        out.extend(before[cursor:begin]);cursor=begin
        assert len(out)==(new_start-1 if new_count else new_start)
        consumed=created=0;i+=1
        while i<len(lines) and not lines[i].startswith('@@ '):
            line=lines[i];mark=line[0];content=line[1:]
            assert mark in ' +-'
            if mark in ' -':
                assert cursor<len(before) and before[cursor]==content,'Patch context differs'
                cursor+=1;consumed+=1
            if mark in ' +':out.append(content);created+=1
            i+=1
        assert (consumed,created)==(old_count,new_count)
    out.extend(before[cursor:])
    return ''.join(out)

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,default=HERE.parent/'native3-r35-cleanup-v1-20261012/hardware/f722-heli.kicad_pcb')
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    delta=json.loads((HERE/'recipe/route-delta.json').read_text())
    source=args.source.read_bytes()
    assert hashlib.sha256(source).hexdigest()==delta['source_board_sha256']
    assert not args.output.exists(),'Use a new output path'
    patch=gzip.decompress((HERE/'recipe/source-to-candidate.patch.gz').read_bytes()).decode()
    result=apply_exact(source.decode(),patch).encode()
    assert hashlib.sha256(result).hexdigest()==delta['expected_board_sha256']
    with args.output.open('xb') as stream:stream.write(result)
    print(json.dumps({'restored_exact_saved_board':True,'board_sha256':delta['expected_board_sha256'],'native_or_numerical_execution':False},indent=2))

if __name__=='__main__':main()
