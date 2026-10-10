"""Build disposable native drill/mask controls; input board is never saved."""
import argparse, hashlib, json
from pathlib import Path
import pcbnew as p
from export_native_copper import export
ap=argparse.ArgumentParser();ap.add_argument('--board',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();a.out.mkdir(parents=True,exist_ok=True)
source_hash=hashlib.sha256(a.board.read_bytes()).hexdigest();rows=[]
for name,expected in [('valid',None),('same_net_SMT_mask','drill_to_SMT_mask'),('close_drills','drill_to_drill'),('untented_front','via_not_tented_both_faces')]:
 b=p.LoadBoard(str(a.board));coords=[(2.,24.)]
 if name=='same_net_SMT_mask':
  pad=next(x for f in b.GetFootprints() if f.GetReference()=='C17' for x in f.Pads() if x.GetNumber()=='2');assert pad.GetNetname()=='GND';coords=[(pad.GetPosition().x/1e6,pad.GetPosition().y/1e6)]
 if name=='close_drills':coords.append((2.44,24.))
 for xy in coords:
  v=p.PCB_VIA(b);v.SetPosition(p.VECTOR2I(round(xy[0]*1e6),round(xy[1]*1e6)));v.SetWidth(p.FromMM(.45));v.SetDrill(p.FromMM(.20));v.SetViaType(p.VIATYPE_THROUGH);v.SetLayerPair(p.F_Cu,p.B_Cu);v.SetNet(b.FindNet('GND'));v.SetFrontTentingMode(p.TENTING_MODE_NOT_TENTED if name=='untented_front' else p.TENTING_MODE_TENTED);v.SetBackTentingMode(p.TENTING_MODE_TENTED);b.Add(v)
 board=a.out/(name+'.kicad_pcb');p.SaveBoard(str(board),b);geometry=a.out/(name+'.json');geometry.write_text(json.dumps(export(board)));rows.append({'case':name,'expected_violation':expected,'geometry':geometry.name,'native_sha256':hashlib.sha256(board.read_bytes()).hexdigest()})
assert hashlib.sha256(a.board.read_bytes()).hexdigest()==source_hash
(a.out/'manifest.json').write_text(json.dumps({'source_sha256':source_hash,'controls':rows},indent=2)+'\n');print('Built four disposable native process controls; source unchanged.')
