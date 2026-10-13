"""Portable host-only replay of the exact bounded CAM checks. No KiCad invocation."""
import argparse, hashlib, json, os, shutil, subprocess, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def verify():
    manifest = json.loads((HERE/'MANIFEST.json').read_text())
    for name, digest in manifest['files'].items():
        assert sha(HERE/name) == digest, ('Packet identity mismatch', name)
    return manifest

ap = argparse.ArgumentParser(description=__doc__)
ap.add_argument('mode', choices=['verify', 'controls', 'drill-csv', 'apertures', 'u15-mask'])
ap.add_argument('--output', type=Path)
ap.add_argument('--hardware', type=Path)
ap.add_argument('--native', type=Path, default=HERE/'../../../native/after.native.json.gz')
ap.add_argument('--deps', type=Path, help='Existing Shapely 2.2.0 dependency directory')
ap.add_argument('--lock', type=Path, help='Explicit existing shared heavy-lane lock, required for geometry')
args = ap.parse_args(); manifest = verify()
if args.mode == 'verify':
    print(json.dumps({'packet_files_verified': len(manifest['files']), 'finalrelease': False})); sys.exit()
assert args.output and not args.output.exists(), 'Choose a new output directory'
args.output.mkdir(parents=True)
out = args.output.resolve()
for p in (HERE/'scripts-normalized').glob('*.py'): shutil.copyfile(p, out/p.name)
for name in ['DRILL-CSV-DIAGNOSTIC.json', 'PRECISION-MATCH-CONTROLS.json']:
    shutil.copyfile(HERE/'evidence'/name, out/name)
env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', OPENBLAS_NUM_THREADS='1', OMP_NUM_THREADS='1')

if args.mode == 'controls':
    shutil.copyfile(HERE/'proposed-exporter/native_export.py', out/'native_export.py')
    text = (HERE/'proposed-exporter/check_patch.py').read_text().replace(
        "Path('@DIAGNOSTIC@/DRILL-CSV-DIAGNOSTIC.json')", "P/'DRILL-CSV-DIAGNOSTIC.json'")
    (out/'check_patch.py').write_text(text)
    for name in ['check_precision_controls.py', 'check_patch.py']:
        subprocess.run([sys.executable, str(out/name)], env=env, timeout=60, check=True)
    subprocess.run([sys.executable, str(HERE/'check_explicit_boundary.py'), str(out/'native_export.py'),
                    str(out/'DRILL-CSV-DIAGNOSTIC.json'), str(out/'EXPLICIT-BOUNDARY-PROOF.json')], env=env, timeout=60, check=True)
    sys.exit()

assert args.hardware and args.native.is_file(), 'Supply exact hardware and native inputs'
hardware = args.hardware.resolve()
source = json.loads((HERE/'SOURCE-IDENTITY.json').read_text())
for name, digest in source['files'].items(): assert sha(hardware/name) == digest, name
assert sha(args.native) == manifest['external_inputs']['native_gzip_sha256']
project = json.loads((hardware/'f722-heli.kicad_pro').read_text())
assert project['board']['design_settings']['rules']['max_error'] == 0.005
inputs = out/'inputs'; inputs.mkdir()
(inputs/'diagnostic-board').symlink_to(hardware, target_is_directory=True)
(inputs/'after.native.json.gz').symlink_to(args.native.resolve())
runtime = out/'runtime'; runtime.mkdir()
if args.mode in ['apertures', 'u15-mask']:
    assert args.lock and args.lock.is_file(), 'Geometry requires an explicit existing shared lock'
    (runtime/'shared-replay.lock').symlink_to(args.lock.resolve())
    if args.deps: (runtime/'python-deps').symlink_to(args.deps.resolve(), target_is_directory=True)
    else: (runtime/'python-deps').mkdir()
names = {'drill-csv':'inspect_drills_csv.py', 'apertures':'inspect_critical_apertures.py', 'u15-mask':'review_U15_mask_difference.py'}
name = names[args.mode]; text = (out/name).read_text()
bindings = {
    '@CAM@': HERE/'actual-cam',
    '@NATIVE_INPUTS@': inputs,
    '@ORIGINAL_EXPORTER@': HERE/'original-exporter/native_export.py',
    '@RUNTIME@': runtime,
}
for old, new in bindings.items(): text = text.replace(repr(old), repr(str(new)))
(out/name).write_text(text)
subprocess.run([sys.executable, str(out/name)], env=env, timeout=120, check=True)
verify()
for name, digest in source['files'].items(): assert sha(hardware/name) == digest
assert sha(args.native) == manifest['external_inputs']['native_gzip_sha256']
print('Host-only replay completed; source unchanged; finalrelease=false')
