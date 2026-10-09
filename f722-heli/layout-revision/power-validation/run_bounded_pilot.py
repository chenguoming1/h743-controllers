#!/usr/bin/env python3
"""One explicitly released pilot process, <=20 min and <=4 GiB address space."""
import argparse
import json
import os
import resource
import signal
import sys


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ['freeze','ledger','out']:p.add_argument('--'+name,required=True)
    p.add_argument('--wall-seconds',type=int,default=1200)
    p.add_argument('--memory-mib',type=int,default=4096)
    a=p.parse_args()
    if not 1<=a.wall_seconds<=1200 or not 512<=a.memory_mib<=4096:
        p.error('Pilot bounds are 1..1200 seconds and 512..4096 MiB')
    # Set before importing NumPy/SciPy. These are per-process settings only.
    for key in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','BLIS_NUM_THREADS','VECLIB_MAXIMUM_THREADS','NUMEXPR_NUM_THREADS']:
        os.environ[key]='1'
    budget=a.memory_mib*1024*1024
    resource.setrlimit(resource.RLIMIT_AS,(budget,budget))
    # Kernel termination also bounds a long native-library call. A killed run
    # has no qualifying numerical result; progress remains on stderr.
    print(json.dumps({'pilot_budget':{'wall_seconds':a.wall_seconds,'address_space_MiB':a.memory_mib,'native_threads':1}}),file=sys.stderr,flush=True)
    signal.signal(signal.SIGALRM,signal.SIG_DFL);signal.alarm(a.wall_seconds)
    from validate_static import main as validate_main
    sys.argv=[sys.argv[0],'--freeze',a.freeze,'--ledger',a.ledger,'--out',a.out,'--run']
    try:return validate_main()
    finally:signal.alarm(0)


if __name__=='__main__':raise SystemExit(main())
