"""Build an isolated paired KiCad placement candidate from the published source.
Run with a Python environment providing KiCad 10 pcbnew. Does not change source.
"""
import argparse, hashlib, json, shutil
from pathlib import Path
import pcbnew as p

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def pose(f): return [f.GetPosition().x/1e6, f.GetPosition().y/1e6, f.GetOrientationDegrees(), f.GetLayerName()]

ap=argparse.ArgumentParser()
ap.add_argument('--source',type=Path,required=True,help='Published hardware directory')
ap.add_argument('--out',type=Path,required=True,help='New candidate hardware directory')
a=ap.parse_args();root=Path(__file__).resolve().parents[1]
spec=json.loads((root/'source.json').read_text());poses=json.loads((root/'placement.json').read_text())
src=a.source.resolve();dst=a.out.resolve();board=src/'f722-heli.kicad_pcb'
assert sha(board)==spec['board_sha256'],'Source identity mismatch'
assert not dst.exists(),'Use a new output directory'
b=p.LoadBoard(str(board));fps={f.GetReference():f for f in b.GetFootprints()}
assert set(fps)==set(poses) and len(fps)==spec['component_count']
assert b.GetCopperLayerCount()==6
before={r:pose(f) for r,f in fps.items()}
original_pads={(r,x.GetNumber()):x.GetNetname() for r,f in fps.items() for x in f.Pads()}
for r,(x,y,angle,side) in poses.items():
 f=fps[r];assert side in ['F.Cu','B.Cu'] and angle%90==0
 if f.GetLayerName()!=side:f.Flip(f.GetPosition(),True)
 f.SetOrientationDegrees(angle);f.SetPosition(p.VECTOR2I(round(x*1e6),round(y*1e6)))
for r in ['R7','R8']:fps[r].SetValue('2.2k / 1%')
fps['U4'].Reference().SetVisible(False)  # Label would overlap adjacent bypass C17.
u={x.GetNumber():x for x in fps['U13'].Pads()};nets={n:u[n].GetNet() for n in ['1','3','6']}
for old,new in [('1','3'),('3','6'),('6','1')]:u[new].SetNet(nets[old])
held=[];removed_tracks=0;removed_zones=0
for t in list(b.GetTracks()):held.append(t);b.Remove(t);removed_tracks+=1
for z in list(b.Zones()):
 if not z.GetIsRuleArea():held.append(z);b.Remove(z);removed_zones+=1
for r,f in fps.items():
 target=poses[r];actual=pose(f)
 assert abs(actual[0]-target[0])<1e-6 and abs(actual[1]-target[1])<1e-6 and (actual[2]-target[2])%360==0 and actual[3]==target[3],r
changes=[]
for r,f in fps.items():
 for pad in f.Pads():
  key=(r,pad.GetNumber());old=original_pads[key];new=pad.GetNetname()
  if old!=new:changes.append({'ref':r,'pad':key[1],'before':old,'after':new})
assert {(x['ref'],x['pad']) for x in changes}=={('U13','1'),('U13','3'),('U13','6')}
shutil.copytree(src,dst)
p.SaveBoard(str(dst/'f722-heli.kicad_pcb'),b)
report={'source_sha256':sha(board),'candidate_sha256':sha(dst/'f722-heli.kicad_pcb'),'status':'UNROUTED: all prior tracks/vias and filled-copper zones removed; schematic metadata synchronization and checks required','component_count':len(fps),'copper_layers':b.GetCopperLayerCount(),'removed_track_via_items':removed_tracks,'removed_copper_zones':removed_zones,'changed_pad_assignments':changes,'poses_before':before,'poses_after':{r:pose(f) for r,f in fps.items()}}
(dst.parent/'placement-build.json').write_text(json.dumps(report,indent=2)+'\n')
assert sha(board)==spec['board_sha256']
print(json.dumps({k:report[k] for k in ['candidate_sha256','component_count','removed_track_via_items','removed_copper_zones','changed_pad_assignments']}))
