#!/usr/bin/env python3
"""Bounded, explicitly released saved-mesh port diagnostic; never remesh a board."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import resource
import signal
import time


def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ['freeze','ledger','cache_metadata','out']:p.add_argument('--'+name.replace('_','-'),type=Path,required=True)
    p.add_argument('--run',action='store_true')
    args=p.parse_args()
    if not args.run:p.error('An owner-released diagnostic requires --run')
    if args.out.exists():p.error('Preserve the existing diagnostic output')
    for name in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','BLIS_NUM_THREADS','NUMEXPR_NUM_THREADS']:os.environ[name]='1'
    resource.setrlimit(resource.RLIMIT_AS,(4*1024**3,4*1024**3))
    signal.signal(signal.SIGALRM,signal.SIG_DFL);signal.alarm(180)
    import numpy as np
    from copper_fem import Limits,Refused
    from mesh_cache import load_mesh,_builder
    started=time.monotonic()
    freeze=json.loads(args.freeze.read_text());ledger=json.loads(args.ledger.read_text())
    assert ledger['freeze_manifest_sha256']==digest(args.freeze)
    for row in freeze['files'].values():assert digest(args.freeze.parent/row['path'])==row['sha256']
    envelope=json.loads(args.cache_metadata.read_text());meta=envelope['payload'];binding=meta['binding']
    assert binding['board_sha256']==freeze['files']['board']['sha256']
    assert binding['native_geometry_sha256']==freeze['files']['geometry']['sha256']
    assert binding['network'] in ledger['networks'] and binding['spacing_mm']in ledger['mesh_spacings_mm']
    assert binding['geometry_builder']==_builder(), 'Geometry builder differs; cache cannot be reused'
    mesh=load_mesh(args.cache_metadata.parent,binding,Limits(**ledger['limits']))
    assert mesh is not None
    report={'status':'INCOMPLETE SAVED-MESH DIAGNOSTIC','qualified_two_grid_result':False,
      'board_sha256':binding['board_sha256'],'native_geometry_sha256':binding['native_geometry_sha256'],
      'freeze_sha256':digest(args.freeze),'ledger_sha256':digest(args.ledger),
      'cache_metadata_sha256':digest(args.cache_metadata),'cache_arrays_sha256':meta['arrays_sha256'],
      'runtime_sha256':{name:digest(Path(__file__).parent/name)for name in ['copper_fem.py','mesh_cache.py','native_edge_noding.py','diagnose_cached_element_operator.py']},
      'network':binding['network']['net'],'spacing_mm':binding['spacing_mm'],
      'resource_limits':{'wall_seconds':180,'address_space_GiB':4,'numerical_threads':1},
      'geometry_rebuilt':False,'results':[]}
    try:
        physical=mesh.physical_operator();report['physical_operator']=mesh.physical_operator_diagnostics
        report['double_preconditioner_maximum_row_sum_S']=float(max(abs(np.asarray(mesh.K.astype(np.longdouble).sum(axis=1)).ravel())))
        names=list(mesh.contact_nodes);z=np.zeros((len(names)-1,len(names)-1))
        for i,name in enumerate(names[1:]):
            row=mesh.solve({name:1.,names[0]:-1.},names[0])
            z[:,i]=[row['contact_voltage_V'][n]for n in names[1:]]
            report['results'].append({'injection':name,'reference':names[0],
              **{key:row[key]for key in ['contact_voltage_V','copper_loss_W','port_power_W','KCL_max_residual_A','linear_solver_diagnostics']}})
        report['maximum_reciprocity_error_ohm']=float(max(abs(z-z.T).ravel()))
        if report['maximum_reciprocity_error_ohm']>1e-7:raise Refused('Diagnostic reciprocity gate failed')
        report['status']='ALL SAVED-MESH PORT CONTROLS PASS; NO TWO-GRID CASE/LOOP ACCEPTANCE'
        report['passed']=True
    except Refused as exc:
        report.update(status='REFUSED SAVED-MESH DIAGNOSTIC',passed=False,reason=str(exc),last_linear_diagnostics=getattr(mesh,'linear_diagnostics',{}))
    report['elapsed_seconds']=time.monotonic()-started
    report['peak_RSS_bytes']=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024
    args.out.write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
    signal.alarm(0)
    print(json.dumps({key:report[key]for key in ['status','passed','elapsed_seconds','peak_RSS_bytes']}))
    return 0 if report['passed']else 2


if __name__=='__main__':raise SystemExit(main())
