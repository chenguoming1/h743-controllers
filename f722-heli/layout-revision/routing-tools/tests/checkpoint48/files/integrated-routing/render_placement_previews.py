"""Make source-bound placement-only SVGs from an isolated copy; source unchanged."""
from pathlib import Path
import argparse,hashlib,json,subprocess
import pcbnew as p
ap=argparse.ArgumentParser();ap.add_argument('board',type=Path);ap.add_argument('poses',type=Path);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
r=Path(__file__).resolve().parents[1];h=lambda f:hashlib.sha256(f.read_bytes()).hexdigest();source=h(a.board);poses=json.loads(a.poses.read_text());assert not a.out.exists();a.out.mkdir(parents=True)
b=p.LoadBoard(str(a.board));fps={f.GetReference():f for f in b.GetFootprints()};assert len(fps)==156 and set(fps)==set(poses)
for ref,f in fps.items():
 v=poses[ref];assert f.GetPosition()==p.VECTOR2I(round(v[0]*1e6),round(v[1]*1e6)) and abs((f.GetOrientationDegrees()-v[2])%360)<1e-7 and f.GetLayerName()==v[3],ref
 f.Value().SetVisible(False)
held=[]
for t in list(b.GetTracks()):held.append(t);b.Remove(t)
for z in list(b.Zones()):
 if not z.GetIsRuleArea():held.append(z);b.Remove(z)
preview=a.out/'preview.kicad_pcb';p.SaveBoard(str(preview),b)
files={}
for face in ['front','back']:
 out=a.out/f'placement-{face}.svg';side='F' if face=='front' else 'B';cmd=[str(r.parent/'kicad10-runtime/kicad-cli'),'pcb','export','svg','--layers',f'{side}.Cu,{side}.Fab,{side}.Silkscreen,Edge.Cuts','--mode-single','--page-size-mode','2','--exclude-drawing-sheet','--output',str(out)]
 if face=='back':cmd+=['--mirror']
 cmd+=[str(preview)];q=subprocess.run(cmd,capture_output=True,text=True);(a.out/f'{face}.log').write_text(q.stdout+q.stderr);assert q.returncode==0 and '<svg' in out.read_text();files[out.name]=h(out)
assert h(a.board)==source
receipt={'routed_board_sha256':source,'placement_only_board_sha256':h(preview),'poses_sha256':h(a.poses),'native_version':p.GetBuildVersion(),'footprints':156,'source_unchanged':True,'files_sha256':files,'scope':'Placement only; copper routing and filled zones omitted, values hidden only in disposable copy. Front and mirrored back. Board-area cropping can clip edge labels. No fabrication or assembly qualification.'};(a.out/'placement-preview-source.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt))
