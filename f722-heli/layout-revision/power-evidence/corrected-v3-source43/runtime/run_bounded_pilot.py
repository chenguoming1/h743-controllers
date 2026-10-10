#!/usr/bin/env python3
"""One explicitly released pilot process, <=25 min and <=4 GiB address space."""
import argparse
import json
import os
import resource
import signal
import sys


def validate_budget(wall_seconds,memory_mib,freeze):
    if not 1<=wall_seconds<=1500 or not 512<=memory_mib<=4096:
        raise ValueError('Pilot bounds are 1..1500 seconds and 512..4096 MiB')
    if freeze.get('numerical_execution_authorized')is not True:
        raise ValueError('The exact freeze is not released for numerical execution')
    declared=freeze.get('pilot_resource_limits',{})
    if wall_seconds>declared.get('overall_wall_seconds',1200)or memory_mib>declared.get('address_space_MiB',4096):
        raise ValueError('Requested process budget exceeds the exact frozen resource declaration')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ['freeze','ledger','out']:p.add_argument('--'+name,required=True)
    p.add_argument('--wall-seconds',type=int,default=1200)
    p.add_argument('--memory-mib',type=int,default=4096)
    p.add_argument('--mesh-cache',help='Private hash-bound assembled mesh/matrix checkpoint directory')
    a=p.parse_args()
    try:
        with open(a.freeze)as f:freeze=json.load(f)
        validate_budget(a.wall_seconds,a.memory_mib,freeze)
    except (OSError,ValueError)as exc:p.error(str(exc))
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
    if a.mesh_cache:sys.argv+=['--mesh-cache',a.mesh_cache]
    try:return validate_main()
    finally:signal.alarm(0)


if __name__=='__main__':raise SystemExit(main())
