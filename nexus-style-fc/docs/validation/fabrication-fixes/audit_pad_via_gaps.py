import pcbnew,json,sys
from pathlib import Path
b=pcbnew.LoadBoard(sys.argv[1]); mm=pcbnew.ToMM
vias=[x for x in b.GetTracks() if isinstance(x,pcbnew.PCB_VIA)]
out=[]
for f in b.GetFootprints():
 for p in f.Pads():
  for layer in [pcbnew.F_Cu,pcbnew.B_Cu]:
   if not p.IsOnLayer(layer):continue
   poly=p.GetEffectivePolygon(layer)
   for v in vias:
    if not v.IsOnLayer(layer):continue
    center=v.GetPosition();gap=mm(poly.Distance(center)-v.GetWidth(layer)/2)
    if -.01<gap<.1269:
     out.append(dict(ref=f.GetReference(),pad=p.GetNumber(),pad_net=p.GetNetname(),pad_xy=mm(p.GetPosition()),size=mm(p.GetSize()),rotation=p.GetOrientationDegrees(),layer=b.GetLayerName(layer),via_net=v.GetNetname(),via_xy=mm(center),via_uuid=v.m_Uuid.AsString(),via_d=mm(v.GetWidth(layer)),gap_mm=round(gap,6),same_net=p.GetNetCode()==v.GetNetCode()))
print(json.dumps(sorted(out,key=lambda x:x['gap_mm']),indent=2))
