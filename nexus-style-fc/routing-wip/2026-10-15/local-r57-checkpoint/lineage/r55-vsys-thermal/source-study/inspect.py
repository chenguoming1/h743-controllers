from pathlib import Path
import pcbnew as k,json,hashlib,math
R=Path('/workspace/scratch/8a35c1f26232/nexus-recovery-20261015');O=R/'vsys-thermal-study';P=R/'routing-continuation/r54-crx-ground/hardware/nexus-style-fc.kicad_pcb';h=hashlib.sha256(P.read_bytes()).hexdigest();assert h=='5677fb38db7d7e19cd3afa9dd5da61bbd9932ed0be7f6f2899f7bf4bf58e8fc9';b=k.LoadBoard(str(P));uid=lambda x:x.m_Uuid.AsString();xy=lambda p:[p.x/1e6,p.y/1e6];ts={uid(t):t for t in b.GetTracks()};ps={uid(p):p for f in b.GetFootprints() for p in f.Pads()};objs={**ts,**ps};ls=list(b.GetEnabledLayers().CuStack());conn=b.GetConnectivity()
def info(q):
 d={'uuid':uid(q),'net':q.GetNetname(),'kind':type(q).__name__,'layers':[b.GetLayerName(l) for l in ls if q.IsOnLayer(l)]}
 if isinstance(q,k.PAD):d.update(ref=q.GetParentFootprint().GetReference(),pin=q.GetNumber(),at=xy(q.GetPosition()),size=xy(q.GetSize()))
 elif isinstance(q,k.PCB_VIA):d.update(at=xy(q.GetPosition()),width=q.GetWidth()/1e6,drill=q.GetDrillValue()/1e6)
 else:d.update(start=xy(q.GetStart()),end=xy(q.GetEnd()),width=q.GetWidth()/1e6)
 return d
def hit(a,z):
 v=k.SHAPE.Collide(a,z,0);return v[0] if isinstance(v,tuple) else bool(v)
u='79c2d0d0-a175-4560-bfe6-3ff9a505332c';t=ts[u];contacts=[]
for q in list(conn.GetConnectedTracks(t))+list(conn.GetConnectedPads(t)):
 w=uid(q)
 if w!=u and any(t.IsOnLayer(l) and objs[w].IsOnLayer(l) and hit(t.GetEffectiveShape(l),objs[w].GetEffectiveShape(l)) for l in ls):contacts.append(info(objs[w]))
near=[]
for q in objs.values():
 box=q.GetBoundingBox()
 if q.IsOnLayer(k.In3_Cu) and box.GetRight()>=101e6 and box.GetLeft()<=105e6 and box.GetBottom()>=106e6 and box.GetTop()<=110e6:near.append(info(q))
j={'source':str(P),'source_sha256':h,'target':info(t),'physical_contacts':contacts,'nearby_In3_copper':near};(O/'geometry.json').write_text(json.dumps(j,indent=2)+'\n');print(json.dumps(j,indent=2))
