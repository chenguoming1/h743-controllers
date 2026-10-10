import pcbnew as p,json,hashlib,shutil
from pathlib import Path
R=Path(__file__).resolve().parents[1];O=R/'integrated-routing/trial01';assert not O.exists()
base=R/'placement-adjustments/usb-u5-05';shutil.copytree(base,O,ignore=shutil.ignore_patterns('geometry.json','*.log','drc.json','mechanical-report.json','*.kicad_prl'))
b=p.LoadBoard(str(O/'f722-heli.kicad_pcb'));held=[];seen={};ids={};sources=[]
def key(t):
 if isinstance(t,p.PCB_VIA):return ('via',t.GetNetname(),t.GetPosition().x,t.GetPosition().y,t.GetWidth(),t.GetDrillValue(),t.TopLayer(),t.BottomLayer())
 return ('track',t.GetNetname(),t.GetLayer(),t.GetWidth(),tuple(sorted(((t.GetStart().x,t.GetStart().y),(t.GetEnd().x,t.GetEnd().y)))))
for path in [R/'power-routing/native/f722-heli.kicad_pcb',R/'fixed-copper-routing/trial15/f722-heli.kicad_pcb']:
 s=p.LoadBoard(str(path));bp={f.GetReference():f for f in b.GetFootprints()};diff=[]
 for f in s.GetFootprints():
  q=bp[f.GetReference()]
  if (q.GetPosition()!=f.GetPosition() or q.GetOrientationDegrees()!=f.GetOrientationDegrees() or q.GetLayer()!=f.GetLayer()):diff.append(f.GetReference())
 assert set(diff)<= {'D3','D4'},diff
 added=duplicate=0
 for t in s.GetTracks():
  k=key(t);u=t.m_Uuid.AsString()
  if k in seen:duplicate+=1;continue
  assert u not in ids or ids[u]==k,(u,ids.get(u),k)
  q=t.Duplicate();q.SetNet(b.FindNet(t.GetNetname()));b.Add(q);held.append(q);seen[k]=u;ids[u]=k;added+=1
 sources.append(dict(path=str(path),sha256=hashlib.sha256(path.read_bytes()).hexdigest(),added=added,duplicates=duplicate,pose_difference=diff,zones=[z.GetNetname() for z in s.Zones()]))
sm=p.GetSettingsManager();sm.LoadProject(str(O/'f722-heli.kicad_pro'));b.SetProject(sm.GetProject(str(O/'f722-heli.kicad_pro')));b.SynchronizeNetsAndNetClasses(False);p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard(str(O/'f722-heli.kicad_pcb'),b)
(O/'merge.json').write_text(json.dumps(dict(sources=sources,board_sha256=hashlib.sha256((O/'f722-heli.kicad_pcb').read_bytes()).hexdigest()),indent=2));print(sources)
