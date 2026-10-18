import pcbnew as k,json,collections,hashlib,shutil,sys
from pathlib import Path
root=Path.cwd();out=root/'docs/validation/reviews/order-fixes-2026-10-17';report={}
for name,rel in [('main','hardware/nexus-style-fc.kicad_pcb'),('child','hardware/header-board/nexus-header-board.kicad_pcb')]:
 path=root/rel;b=k.LoadBoard(str(path));vias=[t for t in b.GetTracks() if isinstance(t,k.PCB_VIA)];drills=collections.Counter(round(v.GetDrillValue()/1e6,3) for v in vias)
 row={'via_count':len(vias),'via_drills_mm':dict(drills),'footprints':len(b.GetFootprints()),'source_sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
 if name=='main':
  assert len(vias)==228 and drills=={.2:228};fs={f.GetReference():f for f in b.GetFootprints()};eps=[p for p in fs['J6'].Pads() if p.GetNumber()=='EP'];assert len(eps)==4
  assert all(p.GetDrillSize().x==850000 and p.GetDrillSize().y==850000 and p.GetDrillShape()==k.PAD_DRILL_SHAPE_CIRCLE for p in eps)
  row['USB_shell_holes']=[{'xy_mm':[p.GetPosition().x/1e6,p.GetPosition().y/1e6],'drill_mm':.85,'center_annulus_mm':.15} for p in eps]
  row['vcap_pads']={r:{p.GetNumber():{'net':p.GetNetname(),'xy_mm':[p.GetPosition().x/1e6,p.GetPosition().y/1e6]} for p in fs[r].Pads()} for r in ['C9','R23']}
 else:
  assert len(vias)==32 and drills=={.3:32};header=next(f for f in b.GetFootprints() if f.GetReference()=='J1');assert len(list(header.Pads()))==21
  assert all(p.GetSize().x==1520000 and p.GetSize().y==1520000 and p.GetDrillSize().x==1000000 for p in header.Pads());row['header_annulus_mm']=.26
 report[name]=row
(out/'native-geometry.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
