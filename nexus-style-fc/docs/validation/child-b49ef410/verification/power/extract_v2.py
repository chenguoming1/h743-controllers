import pcbnew as p, json, hashlib
from pathlib import Path
SRC=Path('/workspace/scratch/8a35c1f26232/nexus-recovery-20261015/mechanical-integration/main-assembly-annotation-10/hardware')
OUT=Path('/workspace/shared/nexus-compact-power-review')
def xy(v): return [v.x/1e6,v.y/1e6]
for name,file in [('v2',Path('/workspace/scratch/8a35c1f26232/nexus-child-power-redesign/candidate-continuous-vx-unfinished/hardware/header-board/nexus-header-board.kicad_pcb'))]:
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
 print(name)
 for f in o['footprints']:
  if any(q['net']=='VX' for q in f['pads']) or f['ref'].startswith(('J','T','K')):
   print(f['ref'],f['value'],f['id'],f['xy'],f['angle']);print([(q['number'],q['net'],q['xy'],q['size'],q['drill'],q['layers']) for q in f['pads']])
 print('VX TRACKS');print(*[x for x in o['tracks'] if x['net']=='VX'],sep='\n')
 print('ZONES');print(*[{k:v for k,v in x.items() if k!='filled'} for x in o['zones']],sep='\n')
