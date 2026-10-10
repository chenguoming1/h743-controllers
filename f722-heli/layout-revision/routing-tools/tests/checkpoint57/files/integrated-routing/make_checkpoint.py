import json,hashlib,shutil,sys
from pathlib import Path
import pcbnew as p
R=Path(__file__).resolve().parents[1];src=R/'integrated-routing/trial02';out=R/'integrated-routing/checkpoint03';delta=Path(sys.argv[1]);assert not out.exists()
shutil.copytree(src,out,ignore=shutil.ignore_patterns('*.json','*.log','*.kicad_prl'))
board=out/'f722-heli.kicad_pcb';b=p.LoadBoard(str(board));tracks={t.m_Uuid.AsString():t for t in b.GetTracks()}
def xy(v):return[v.x/1e6,v.y/1e6]
def vec(v):return p.VECTOR2I(round(v[0]*1e6),round(v[1]*1e6))
for c in json.loads(delta.read_text())['changes']:
 if c['old'] is None:
  t=p.PCB_TRACK(b);t.SetNet(b.FindNet(c['net']));t.SetLayer(b.GetLayerID(c['layer']));t.SetWidth(round(c['width_mm']*1e6));b.Add(t)
 else:
  matches=[t for t in b.GetTracks() if not isinstance(t,p.PCB_VIA) and t.GetNetname()==c['net'] and t.GetLayerName()==c['layer'] and xy(t.GetStart())==c['old']['start'] and xy(t.GetEnd())==c['old']['end']];assert len(matches)==1; t=matches[0];assert t.GetNetname()==c['net'] and t.GetLayerName()==c['layer'];assert xy(t.GetStart())==c['old']['start'] and xy(t.GetEnd())==c['old']['end']
 t.SetStart(vec(c['new']['start']));t.SetEnd(vec(c['new']['end']))
sm=p.GetSettingsManager();sm.LoadProject(str(out/'f722-heli.kicad_pro'));b.SetProject(sm.GetProject(str(out/'f722-heli.kicad_pro')));b.SynchronizeNetsAndNetClasses(False);p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard(str(board),b)
(out/'checkpoint-source.json').write_text(json.dumps({'base_sha256':hashlib.sha256((src/board.name).read_bytes()).hexdigest(),'cc2_delta':json.loads(delta.read_text()),'board_sha256':hashlib.sha256(board.read_bytes()).hexdigest()},indent=2)+'\n')
shutil.copy(src/'parts.json',out/'parts.json');shutil.copy(src/'poses.json',out/'poses.json');print(hashlib.sha256(board.read_bytes()).hexdigest())
