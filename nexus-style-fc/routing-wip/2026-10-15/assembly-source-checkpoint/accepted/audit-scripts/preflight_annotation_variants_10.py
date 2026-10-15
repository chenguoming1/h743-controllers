from pathlib import Path
import sys,json,hashlib,math
import pcbnew as P
R=Path('/workspace/scratch/8a35c1f26232/nexus-recovery-20261015');M=R/'assembly-annotation-cleanup/local-variant-remedy';C=M/'source-candidate-final';S=R/'mechanical-integration/main-assembly-annotation-09';O=R/'mechanical-integration/annotation-variant-preflight-10-fixed';assert not O.exists();O.mkdir();sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();mapping=json.loads((M/'fpid-mapping.json').read_text());b=P.LoadBoard(str(S/'hardware/nexus-style-fc.kicad_pcb'));source={f.GetReference():f for f in b.GetFootprints()};probe=P.BOARD();rows=[]
def xy(q):return [int(q.x),int(q.y)]
def shapes(f):
 out=[]
 for g in f.GraphicalItems():
  if not isinstance(g,P.PCB_SHAPE):continue
  out.append([int(g.GetShape()),int(g.GetLayer()),int(g.GetWidth()),xy(g.GetStart()),xy(g.GetEnd()),bool(g.IsSolidFill())])
 return sorted(out,key=lambda x:json.dumps(x))
def pads(f):
 return sorted([[p.GetNumber(),xy(p.GetPosition()),xy(p.GetSize()),int(p.GetShape()),int(p.GetAttribute()),xy(p.GetDrillSize()),p.GetLayerSet().FmtHex(),p.GetOrientationDegrees()] for p in f.Pads()],key=lambda x:json.dumps(x))
for ref,row in mapping.items():
 p=C/row['variant_library'];assert sha(p)==row['variant_library_sha256'];f=P.FootprintLoad(str(p.parent),p.stem);assert f is not None,ref;probe.Add(f);f.SetReference(ref);f.SetPosition(source[ref].GetPosition());f.SetOrientationDegrees(source[ref].GetOrientationDegrees());assert f.GetLayer()==source[ref].GetLayer();assert shapes(f)==shapes(source[ref]),(ref,'native graphic geometry');assert pads(f)==pads(source[ref]),(ref,'native pad geometry');rows.append({'ref':ref,'library':row['variant_library'],'sha256':sha(p),'native_shapes_match_approved_stage09':True,'native_pad_geometry_match':True,'shape_count':len(shapes(f)),'pad_count':len(pads(f))})
P.SaveBoard(str(O/'native-library-load-probe.kicad_pcb'),probe)
out={'status':'PASS five exact local variant libraries native-load with approved graphics and unchanged physical pads','pcbnew_version':P.GetBuildVersion(),'source_annotation_board_sha256':sha(S/'hardware/nexus-style-fc.kicad_pcb'),'mapping_sha256':sha(M/'fpid-mapping.json'),'checks':rows,'scope':'Small isolated import probe only; routed source boards were read, not saved or changed.'};(O/'verification.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
