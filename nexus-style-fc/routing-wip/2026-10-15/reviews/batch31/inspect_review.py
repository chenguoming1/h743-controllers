from pathlib import Path
import pcbnew as k,json,hashlib,math
D=Path('/tmp/nexus-boardlevel-review-20261015')
paths={'batch31':'/tmp/nexus-clearance-isolated-20261015-0017/batch31/hardware/nexus-style-fc.kicad_pcb','candidate16':'/tmp/nexus-reroute-f722-20261014/experiments/attempt-16/hardware/nexus-style-fc.kicad_pcb','main':'/tmp/nexus-reroute-f722-20261014/backups/main-before-rule-refill.kicad_pcb'}
xy=lambda p:[p.x/1e6,p.y/1e6]
uid=lambda t:t.m_Uuid.AsString()
def poly(ps):
 out=[]
 for i in range(ps.OutlineCount()):
  shell=ps.COutline(i); holes=[]
  for j in range(ps.HoleCount(i)):
   h=ps.CHole(i,j);holes.append([xy(h.CPoint(n)) for n in range(h.PointCount())])
  out.append({'shell':[xy(shell.CPoint(n)) for n in range(shell.PointCount())],'holes':holes})
 return out
for name,path in paths.items():
 b=k.LoadBoard(path);layers=list(b.GetEnabledLayers().CuStack()); tracks=[];pads=[];zones=[]
 for t in b.GetTracks():
  r={'uuid':uid(t),'net':t.GetNetname(),'class':t.GetClass(),'layers':[b.GetLayerName(l) for l in layers if t.IsOnLayer(l)]}
  if isinstance(t,k.PCB_VIA):r.update(at=xy(t.GetPosition()),diameter=t.GetWidth(k.F_Cu)/1e6,drill=t.GetDrillValue()/1e6,tented_front=int(t.GetFrontTentingMode()),tented_back=int(t.GetBackTentingMode()))
  else:r.update(start=xy(t.GetStart()),end=xy(t.GetEnd()),width=t.GetWidth()/1e6,length=t.GetLength()/1e6)
  tracks.append(r)
 for f in b.GetFootprints():
  for p in f.Pads():pads.append({'uuid':uid(p),'ref':f.GetReference(),'value':f.GetValue(),'pad':p.GetNumber(),'net':p.GetNetname(),'at':xy(p.GetPosition()),'size':xy(p.GetSize()),'angle':p.GetOrientationDegrees(),'attribute':int(p.GetAttribute()),'drill':xy(p.GetDrillSize()),'layers':[b.GetLayerName(l) for l in layers if p.IsOnLayer(l)]})
 for z in b.Zones():
  if z.GetIsRuleArea():continue
  for l in layers:
   if z.IsOnLayer(l):zones.append({'uuid':uid(z),'net':z.GetNetname(),'layer':b.GetLayerName(l),'filled':poly(z.GetFilledPolysList(l)),'outline':poly(z.Outline())})
 out={'path':path,'sha256':hashlib.sha256(Path(path).read_bytes()).hexdigest(),'layers':[b.GetLayerName(l) for l in layers],'tracks':tracks,'pads':pads,'zones':zones}
 (D/(name+'-geometry.json')).write_text(json.dumps(out))
 print(name,'hash',out['sha256'],'tracks',len(tracks),'pads',len(pads),'zones',[(z['net'],z['layer'],len(z['filled']),sum(len(x['shell']) for x in z['filled'])) for z in zones],flush=True)
