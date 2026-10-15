from pathlib import Path
import pcbnew as k,json,hashlib,math,collections
R=Path('/workspace/scratch/8a35c1f26232/nexus-recovery-20261015');P=R/'routing-continuation/r52-dsm-bypass/hardware/nexus-style-fc.kicad_pcb';b=k.LoadBoard(str(P));uid=lambda t:t.m_Uuid.AsString();xy=lambda p:(p.x/1e6,p.y/1e6);vec=lambda p:k.VECTOR2I(round(p[0]*1e6),round(p[1]*1e6));ts={uid(t):t for t in b.GetTracks()};ps={uid(p):p for f in b.GetFootprints() for p in f.Pads()};items={**ts,**ps};u='0af3b73f-633f-4ee3-8ff9-e4c4f9f8b95a';t=ts[u];l=t.GetLayer();A,Z=xy(t.GetStart()),xy(t.GetEnd());obs=[(w,o.GetEffectiveShape(l)) for w,o in items.items() if o.GetNetCode()!=t.GetNetCode() and o.IsOnLayer(l)]
def hit(a,b,c=0):
 q=k.SHAPE.Collide(a,b,c);return q[0] if isinstance(q,tuple) else bool(q)
def test(points):
 h=[]
 for a,z in zip(points,points[1:]):
  q=k.PCB_TRACK(b);q.SetStart(vec(a));q.SetEnd(vec(z));q.SetLayer(l);q.SetWidth(t.GetWidth());q.SetNetCode(t.GetNetCode());s=q.GetEffectiveShape(l);h += [w for w,o in obs if hit(s,o,127002)]
 return sorted(set(h))
valid=[];counts=collections.Counter();tested=0
for i in range(15):
 for j in range(9):
  pts=[A,(round(110.35+i*.05,6),round(132.7+j*.025,6)),Z];h=test(pts);tested+=1;counts.update(h)
  if not h:valid.append({'points':pts,'length_mm':sum(math.dist(a,z) for a,z in zip(pts,pts[1:]))})
ports=[w for w,o in items.items() if w!=u and o.IsOnLayer(l) and hit(t.GetEffectiveShape(l),o.GetEffectiveShape(l))];assert all(items[w].GetNetCode()==t.GetNetCode() for w in ports)
out={'source_board_sha256':hashlib.sha256(P.read_bytes()).hexdigest(),'uuid':u,'net':t.GetNetname(),'layer':b.GetLayerName(l),'width_mm':t.GetWidth()/1e6,'start':A,'end':Z,'external_ports':ports,'tested':tested,'valid':sorted(valid,key=lambda x:x['length_mm']),'blocker_counts':dict(counts)};Path(__file__).with_name('bend-probe.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'tested':tested,'valid_count':len(valid),'best':out['valid'][:5],'external_ports':ports},indent=2))
