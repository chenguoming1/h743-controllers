from pathlib import Path
import pcbnew as k,json,hashlib,math
R=Path('/workspace/scratch/8a35c1f26232/nexus-recovery-20261015');P=R/'routing-continuation/r57-rpm-center/hardware/nexus-style-fc.kicad_pcb';assert hashlib.sha256(P.read_bytes()).hexdigest()=='583e73ba08c80e70d42bfd726ef1b440ab0ddf4d7309cef266de486fd03f461f'
b=k.LoadBoard(str(P));uid=lambda o:o.m_Uuid.AsString();xy=lambda p:[p.x/1e6,p.y/1e6];ts={uid(t):t for t in b.GetTracks()};ps={uid(p):p for f in b.GetFootprints() for p in f.Pads()};ls=list(b.GetEnabledLayers().CuStack());conn=b.GetConnectivity()
def info(o):
 d={'uuid':uid(o),'type':type(o).__name__,'net':o.GetNetname(),'layers':[b.GetLayerName(l) for l in ls if o.IsOnLayer(l)]}
 if isinstance(o,k.PAD):d.update(ref=o.GetParentFootprint().GetReference(),pin=o.GetNumber(),value=o.GetParentFootprint().GetValue(),position=xy(o.GetPosition()),size=xy(o.GetSize()),rotation=o.GetOrientationDegrees(),paste=[b.GetLayerName(l) for l in [k.F_Paste,k.B_Paste] if o.IsOnLayer(l)])
 elif isinstance(o,k.PCB_VIA):d.update(position=xy(o.GetPosition()),diameter=o.GetWidth(k.F_Cu)/1e6,drill=o.GetDrillValue()/1e6)
 else:d.update(start=xy(o.GetStart()),end=xy(o.GetEnd()),width=o.GetWidth()/1e6)
 return d
out={'source_sha256':hashlib.sha256(P.read_bytes()).hexdigest(),'all_5V_BUCK':[info(o) for o in [*ts.values(),*ps.values()] if o.GetNetname()=='5V_BUCK'],'nearby_pads':[info(p) for p in ps.values() if 100<p.GetPosition().x/1e6<108 and 109<p.GetPosition().y/1e6<117]}
for d in out['all_5V_BUCK']:
 o=ts.get(d['uuid']) or ps[d['uuid']];d['connected']=[uid(q) for q in [*conn.GetConnectedTracks(o),*conn.GetConnectedPads(o)] if uid(q)!=uid(o)]
(R/'r57-buck-review/inventory.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
