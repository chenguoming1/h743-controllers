"""Source-only checks by default; explicitly requested finite geometry replay."""
import argparse, ast, fcntl, hashlib, json, os, pathlib, shutil, subprocess, sys, time
HERE=pathlib.Path(__file__).resolve().parent
def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--checkpoint-root',type=pathlib.Path,default=HERE.parent.parent/'native2-in4-rx-v5-20261013')
    parser.add_argument('--output',type=pathlib.Path)
    parser.add_argument('--run-geometry',action='store_true')
    args=parser.parse_args()
    os.environ['F722_REFERENCE_CHECKPOINT_ROOT']=str(args.checkpoint_root.resolve())
    import portable_paths as p
    manifest=p.verify()
    for file in HERE.glob('*.py'):ast.parse(file.read_text(),filename=str(file))
    if not args.run_geometry:
        print(json.dumps({'source_only_checks_passed':True,'public_inputs':len(manifest['public_inputs']),'package_files':len(manifest['package_files']),'geometry_executed':False}));return
    if args.output is None:parser.error('--run-geometry requires --output outside the checkpoint')
    out=args.output.resolve();checkpoint=args.checkpoint_root.resolve()
    assert not out.exists() and not out.is_relative_to(checkpoint), 'A new isolated output directory is required.'
    assert shutil.disk_usage(out.parent).free>=192*1024**2, 'Keep 128 MiB reserve plus 64 MiB output budget.'
    lock=open(out.parent/'.f722-reference-review.lock','a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    out.mkdir()
    env=dict(os.environ,F722_REFERENCE_OUTPUT=str(out),F722_REFERENCE_RUN_GRANTED='1',PYTHONDONTWRITEBYTECODE='1',OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1')
    stages=[['measure_reference.py','extract','source'],['measure_reference.py','extract','candidate'],['review_returns.py','--run-authorized-local-review'],['measure_reference.py','inventory'],['targeted_review.py','targeted']]
    receipts=[]
    for stage in stages:
        start=time.monotonic()
        with open(out/(stage[0]+'.'+stage[-1]+'.log'),'x') as log:
            cp=subprocess.run([sys.executable,'-B',str(HERE/stage[0]),*stage[1:]],env=env,stdout=log,stderr=subprocess.STDOUT,timeout=125,check=False)
        receipts.append({'command':stage,'returncode':cp.returncode,'elapsed_seconds':time.monotonic()-start})
        assert cp.returncode==0, 'Review stage failed; preserve its exact log.'
        assert sum(x.stat().st_size for x in out.iterdir() if x.is_file())<=64*1024**2, 'Output budget exceeded.'
        assert shutil.disk_usage(out).free>=128*1024**2, 'Free reserve exhausted.'
    subprocess.run([sys.executable,'-B',str(HERE/'compare_metrics.py'),str(out)],env=env,timeout=30,check=True)
    receipt={'schema':'f722-native2-v5-reference-replay/v1','source_inputs_verified':True,'stages':receipts,'numeric_comparison_required':'Compare generated inventory, targeted and actual-return fields to the immutable checkpoint evidence; wall times, paths and script hashes differ by design.','new_engineering_or_adoption_decision':False}
    (out/'REPLAY-RECEIPT.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps({'output':str(out),'stages_completed':len(stages),'acceptance_claimed':False}))
if __name__=='__main__':main()
