import pcbnew as p, json, hashlib,sys
from pathlib import Path
OUT=Path(__file__).resolve().parent
def xy(v): return [v.x/1e6,v.y/1e6]
ROOT=OUT.parents[3]
name=sys.argv[1] if len(sys.argv)>1 else 'four-layer'
file=Path(sys.argv[2]) if len(sys.argv)>2 else ROOT/'hardware/header-board/nexus-header-board.kicad_pcb'
for name,file in [(name,file)]:
 b=p.LoadBoard(str(file)); o={'path':str(file),'sha256':hashlib.sha256(file.read_bytes()).hexdigest(),'footprints':[],'tracks':[],'zones':[]}
 for f in b.GetFootprints():
  pads=[]
  for q in f.Pads():
   pads.append({'number':q.GetNumber(),'net':q.GetNetname(),'xy':xy(q.GetPosition()),'size':xy(q.GetSize()),'drill':xy(q.GetDrillSize()),'layers':[b.GetLayerName(l) for l in q.GetLayerSet().CuStack()],'shape':q.GetShape(),'attribute':q.GetAttribute(),'uuid':q.m_Uuid.AsString()})
  o['footprints'].append({'ref':f.GetReference(),'value':f.GetValue(),'id':str(f.GetFPID().GetLibItemName()),'xy':xy(f.GetPosition()),'angle':f.GetOrientationDegrees(),'pads':pads})
 for t in b.GetTracks():
  if t.GetNetname() not in ('VX','GND'):continue
  a={'type':t.GetClass(),'net':t.GetNetname(),'start':xy(t.GetStart()),'end':xy(t.GetEnd()),'width':(t.GetWidth(p.F_Cu) if isinstance(t,p.PCB_VIA) else t.GetWidth())/1e6,'uuid':t.m_Uuid.AsString()}
  if isinstance(t,p.PCB_VIA):a.update(drill=t.GetDrillValue()/1e6,layers=[b.GetLayerName(l) for l in t.GetLayerSet().CuStack()])
  else:a.update(layer=b.GetLayerName(t.GetLayer()),length=t.GetLength()/1e6)
  o['tracks'].append(a)
 for z in b.Zones():
  a={'net':z.GetNetname(),'layers':[b.GetLayerName(l) for l in z.GetLayerSet().CuStack()],'name':z.GetZoneName(),'thermal_gap':z.GetThermalReliefGap()/1e6,'thermal_spoke':z.GetThermalReliefSpokeWidth()/1e6,'pad_connection':z.GetPadConnection(),'filled':{}}
  for l in z.GetLayerSet().CuStack():
   poly=z.GetFilledPolysList(l); outlines=[]
   for i in range(poly.OutlineCount()):
    line=poly.COutline(i)
    outlines.append({'outer':[xy(line.CPoint(j)) for j in range(line.PointCount())],'holes':[[xy(poly.CHole(i,h).CPoint(j)) for j in range(poly.CHole(i,h).PointCount())] for h in range(poly.HoleCount(i))]})
   a['filled'][b.GetLayerName(l)]=outlines
  o['zones'].append(a)
 (OUT/(name+'-geometry.json')).write_text(json.dumps(o,indent=2))
