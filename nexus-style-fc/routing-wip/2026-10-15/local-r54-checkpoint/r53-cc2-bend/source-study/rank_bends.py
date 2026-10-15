from pathlib import Path
import pcbnew as k,json,math
R=Path('/workspace/scratch/8a35c1f26232/nexus-recovery-20261015');D=R/'cc2-corridor-study';j=json.loads((D/'bend-probe.json').read_text());b=k.LoadBoard(str(R/'routing-continuation/r52-dsm-bypass/hardware/nexus-style-fc.kicad_pcb'));ts={t.m_Uuid.AsString():t for t in b.GetTracks()};p=next(p for f in b.GetFootprints() for p in f.Pads() if p.m_Uuid.AsString()=='2560591b-d7d7-48d5-bbb2-112e1f874870');g=k.SHAPE_POLY_SET()
for z in b.Zones():
 if z.GetNetname()=='GND' and z.IsOnLayer(k.In1_Cu) and not z.GetIsRuleArea():g.BooleanAdd(z.GetFilledPolysList(k.In1_Cu))
def score(pts):
 path=k.SHAPE_POLY_SET();gaps=[]
 for a,z in zip(pts,pts[1:]):
  t=k.PCB_TRACK(b);t.SetStart(k.VECTOR2I(round(a[0]*1e6),round(a[1]*1e6)));t.SetEnd(k.VECTOR2I(round(z[0]*1e6),round(z[1]*1e6)));t.SetWidth(127000);t.SetLayer(k.F_Cu);t.TransformShapeToPolygon(path,k.F_Cu,0,500,k.ERROR_OUTSIDE);s=t.GetEffectiveShape(k.F_Cu);q=p.GetEffectiveShape(k.F_Cu);lo,hi=0,500000
  while hi-lo>1:
   mid=(lo+hi)//2;r=s.Collide(q,mid);hit=r[0] if isinstance(r,tuple) else bool(r)
   if hit:hi=mid
   else:lo=mid
  gaps.append(hi/1e6)
 total=abs(path.Area());path.BooleanSubtract(g);return {'minimum_J6_EP_gap_mm':min(gaps),'full_width_In1_coverage_fraction':1-abs(path.Area())/total}
old=score([j['start'],j['end']]);v=[{**x,**score(x['points'])} for x in j['valid']];out={'source_board_sha256':j['source_board_sha256'],'old_route':old,'candidates':sorted(v,key=lambda x:(-x['full_width_In1_coverage_fraction'],abs(x['minimum_J6_EP_gap_mm']-.16),x['length_mm']))};(D/'ranked-bends.json').write_text(json.dumps(out,indent=2)+'\n');print(old);print(out['candidates'][:4])
