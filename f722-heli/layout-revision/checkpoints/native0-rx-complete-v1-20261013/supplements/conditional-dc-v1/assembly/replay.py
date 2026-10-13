#!/usr/bin/env python3
"""Verify source bindings; opt in to the bounded nominal assembly geometry replay."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

HERE=Path(__file__).resolve().parent
CHECKPOINT=HERE.parents[2]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--run',action='store_true',help='Execute geometry; requires Shapely 2.2.0 and a new work directory.')
    p.add_argument('--work',type=Path)
    args=p.parse_args()
    m=json.loads((HERE/'SOURCE-NORMALIZATION.json').read_text())
    assert sha(HERE/'review_moved_assembly.py')==m['normalized_source']['sha256']
    assert sha(HERE/'after-pad-settings.json')==m['pad_settings']['sha256']
    assert sha(HERE/'MOVED-ASSEMBLY-GEOMETRY.json')==m['raw_geometry']['sha256']
    sources={'diagnostic-board/f722-heli.kicad_pcb':CHECKPOINT/'hardware/f722-heli.kicad_pcb','after.native.json.gz':CHECKPOINT/'native/after.native.json.gz','after-pad-settings.json':HERE/'after-pad-settings.json'}
    assert sha(sources['diagnostic-board/f722-heli.kicad_pcb'])=='84229c571433bd72d410fb18d02cffa3a380c00a87fbe1270e3a73b63f8dd6cd'
    assert sha(sources['after.native.json.gz'])=='83a6c87643977d21a1c3841bc26d4f28694ff721436e36ba20824b7b191174d1'
    if not args.run:
        print(json.dumps({'source_hash_checks':'PASS','geometry_executed':False,'runtime_for_run':'POSIX Python 3.11, Shapely 2.2.0'}));return
    if args.work is None:p.error('--run requires --work pointing at a new directory')
    import shapely
    assert shapely.__version__=='2.2.0',shapely.__version__
    work=args.work.resolve();work.mkdir(parents=True,exist_ok=False)
    (work/'output').mkdir();(work/'replay.lock').touch()
    for target,source in sources.items():
        dest=work/'inputs'/target;dest.parent.mkdir(parents=True,exist_ok=True);dest.symlink_to(source.resolve())
    env=dict(os.environ,F722_ASSEMBLY_WORK_ROOT=str(work),PYTHONDONTWRITEBYTECODE='1',OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1')
    subprocess.run([sys.executable,'-B',str(HERE/'review_moved_assembly.py')],env=env,check=True,timeout=90,stdout=subprocess.DEVNULL)
    old=json.loads((HERE/'MOVED-ASSEMBLY-GEOMETRY.json').read_text());new=json.loads((work/'output/MOVED-ASSEMBLY-GEOMETRY.json').read_text())
    for d in [old,new]:d.pop('peak_RSS_MiB',None);d.pop('script_sha256',None)
    assert old==new,'Replay output differs beyond documented source/runtime metadata'
    print(json.dumps({'source_hash_checks':'PASS','geometry_executed':True,'all_technical_output_exact':True,'output':str(work/'output/MOVED-ASSEMBLY-GEOMETRY.json')}))
if __name__=='__main__':main()
