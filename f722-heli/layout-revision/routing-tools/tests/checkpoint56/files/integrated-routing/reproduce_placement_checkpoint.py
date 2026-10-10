"""Rebuild isolated placement from the pinned original; compare every pose and pad."""
from pathlib import Path
import argparse, hashlib, json, shutil, subprocess, sys

ROOT = Path(__file__).resolve().parents[1]
N = ROOT/'repo/f722-heli/layout-revision'
K = ROOT.parent/'kicad10-runtime'
ap = argparse.ArgumentParser()
ap.add_argument('candidate', type=Path)
ap.add_argument('--out', type=Path, required=True)
a = ap.parse_args()
D, O = a.candidate.resolve(), a.out.resolve()
assert not O.exists(), 'Use a fresh isolated output directory'
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
read = lambda p: json.loads(Path(p).read_text())
board = D/'f722-heli.kicad_pcb'
before = sha(board)
O.mkdir(); (O/'scripts').mkdir()
for name in ['rebuild_placement.py','patch_metadata.py','check_native_parity.py']:
    shutil.copy2(N/'scripts'/name, O/'scripts'/name)
shutil.copy2(N/'source.json', O/'source.json')
shutil.copy2(D/'poses-native.json', O/'placement.json')
def run(name, args):
    with (O/(name+'.log')).open('w') as log:
        subprocess.run([str(x) for x in args], cwd=ROOT, stdout=log,
                       stderr=subprocess.STDOUT, check=True)
run('build', [K/'python',O/'scripts/rebuild_placement.py','--source',ROOT/'repo/f722-heli/hardware','--out',O/'hardware'])
run('metadata', [sys.executable,O/'scripts/patch_metadata.py','--hardware',O/'hardware','--report',O/'metadata-changes.json','--apply'])
run('netlist', [K/'kicad-cli','sch','export','netlist','--format','kicadxml','--output',O/'reconstructed.net',O/'hardware/f722-heli.kicad_sch'])
run('parity', [K/'python',O/'scripts/check_native_parity.py','--board',O/'hardware/f722-heli.kicad_pcb','--netlist',O/'reconstructed.net','--out',O/'parity.json'])
sys.path.insert(0, str(ROOT/'ordinary-routing/tests/mpn-parity'))
from apply_metadata_copy import parse, children, properties, shape
def pads(path):
    records = {}
    for f in children(parse(path.read_text()), 'footprint'):
        ref = properties(f)['Reference'].items[2].value
        for pad in children(f, 'pad'):
            uid = children(pad, 'uuid')[0].items[1].value
            assert (ref,uid) not in records
            records[ref,uid] = shape(pad)
    return records
rebuilt = O/'hardware/f722-heli.kicad_pcb'
expected, actual = pads(board), pads(rebuilt)
assert len(expected) == len(actual) == 558 and expected == actual
parity, poses = read(O/'parity.json'), read(O/'placement.json')
assert parity['passed'] and len(parity['footprints']) == len(poses) == 156
for ref, pose in poses.items():
    f = parity['footprints'][ref]
    assert f['xy_mm'] == pose[:2] and f['angle_deg'] % 360 == pose[2] % 360 and f['side'] == pose[3]
assert sha(board) == before
report = {'source_board_sha256':before,'reconstructed_placement_board_sha256':sha(rebuilt),
          'placement_json_sha256':sha(O/'placement.json'),'156_poses_exact':True,
          '558_complete_native_pad_records_exact':True,'paired_native_parity_passed':True,
          'builder_sha256':sha(O/'scripts/rebuild_placement.py'), 'orchestrator_sha256':sha(__file__),
          'scope':'Pinned original plus pose recipe reproduces all poses and full pad records; no routed-board reconstruction or electrical qualification.'}
(O/'placement-reproduction.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report))
