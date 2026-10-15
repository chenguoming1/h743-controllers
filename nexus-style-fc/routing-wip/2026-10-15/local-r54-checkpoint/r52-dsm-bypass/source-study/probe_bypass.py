from pathlib import Path
import pcbnew as k,json,hashlib,math,collections,itertools
P=Path('/workspace/scratch/8a35c1f26232/nexus-recovery-20261015/u10-metadata-integration/experimental-r51/hardware/nexus-style-fc.kicad_pcb');b=k.LoadBoard(str(P));uid=lambda t:t.m_Uuid.AsString();xy=lambda p:(p.x/1e6,p.y/1e6);vec=lambda p:k.VECTOR2I(round(p[0]*1e6),round(p[1]*1e6));ts={uid(t):t for t in b.GetTracks()};ps={uid(p):p for f in b.GetFootprints() for p in f.Pads()};items={**ts,**ps};net=ts['cb054904-7c15-4bd2-a45c-831a234ed68f'].GetNetCode();rm={'1e87d743-ebb9-40a9-a891-2357ffc18d2a','95998f31-6893-4884-b5f2-ed36bfde4294','cb054904-7c15-4bd2-a45c-831a234ed68f'};ls=list(b.GetEnabledLayers().CuStack())
def hit(a,b,c=0):
 r=k.SHAPE.Collide(a,b,c);return r[0] if isinstance(r,tuple) else bool(r)
def track(a,z,l):
 t=k.PCB_TRACK(b);t.SetStart(vec(a));t.SetEnd(vec(z));t.SetWidth(127000);t.SetLayer(l);t.SetNetCode(net);return t
obs={l:[(u,o,o.GetEffectiveShape(l)) for u,o in items.items() if o.GetNetCode()!=net and o.IsOnLayer(l)] for l in ls}
def check(points,l):
 hits=[]
 for a,z in zip(points,points[1:]):
  t=track(a,z,l);s=t.GetEffectiveShape(l)
  hits += [u for u,o,q in obs[l] if hit(s,q,127002)]
 return sorted(set(hits))
A=(101.375,111.675);Z=(101.775,113.225);F=[Z,(100.66,114.496)];fh=check(F,k.F_Cu);valid=[];bad=collections.Counter();tested=0
for l in [k.In2_Cu,k.In3_Cu,k.B_Cu]:
 for mid in [(round(101.15+i*.05,6),round(112.45+j*.05,6)) for i in range(10) for j in range(12)]:
  p=[A,mid,Z];tested+=1;hits=check(p,l)
  if not hits and not fh:valid.append({'layer':b.GetLayerName(l),'points':p,'length_mm':sum(math.dist(a,z) for a,z in zip(p,p[1:]))})
  bad.update(hits)
contacts=[]
for u in rm:
 t=ts[u]
 for w,o in items.items():
  if u==w:continue
  common=[b.GetLayerName(l) for l in ls if t.IsOnLayer(l) and o.IsOnLayer(l) and hit(t.GetEffectiveShape(l),o.GetEffectiveShape(l))]
  if common:contacts.append({'donor':u,'other':w,'other_net':o.GetNetname(),'layers':common,'other_kind':'pad' if isinstance(o,k.PAD) else 'via' if isinstance(o,k.PCB_VIA) else 'track'})
out={'source':str(P),'sha256':hashlib.sha256(P.read_bytes()).hexdigest(),'removed':sorted(rm),'old_contacts':contacts,'F_route':F,'F_blockers':fh,'tested':tested,'valid':sorted(valid,key=lambda v:v['length_mm']),'blocker_counts':dict(bad)};Path(__file__).with_name('bypass-probe.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'F_blockers':fh,'tested':tested,'valid_count':len(valid),'best':out['valid'][:8],'old_contacts':contacts},indent=2))
