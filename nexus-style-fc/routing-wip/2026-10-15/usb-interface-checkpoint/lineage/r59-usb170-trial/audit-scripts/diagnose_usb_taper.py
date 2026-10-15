from pathlib import Path
import pcbnew as k,json,hashlib,math
R=Path('/workspace/scratch/8a35c1f26232/nexus-recovery-20261015');O=R/'routing-continuation/r59-usb170-trial';tr=json.loads((O/'transaction.json').read_text());b=k.LoadBoard(str(O/'hardware/nexus-style-fc.kicad_pcb'));uid=lambda o:o.m_Uuid.AsString();vec=lambda p:k.VECTOR2I(round(p[0]*1e6),round(p[1]*1e6));xy=lambda p:[p.x/1e6,p.y/1e6];ts={uid(t):t for t in b.GetTracks()};ss={uid(t):t for t in b.GetDrawings()};out=[]
for r in tr['added_primitives']:
 if r['kind']!='taper_copper_polygon':continue
 row={'id':r['id'],'uuid':r['uuid'],'levels':[]};tracks=[t for t in ts.values() if not isinstance(t,k.PCB_VIA) and t.GetNetname()==r['net'] and t.GetLayer()==k.In3_Cu and any(vec(p) in [t.GetStart(),t.GetEnd()] for p in [r['start_port'],r['end_port']])];assert len(tracks)==2
 for err in [20,5,1]:
  def poly(o,loc=k.ERROR_INSIDE):
   p=k.SHAPE_POLY_SET();o.TransformShapeToPolygon(p,k.In3_Cu,0,err,loc);return p
  union=poly(ss[r['uuid']]);[union.BooleanAdd(poly(t)) for t in tracks];cap=k.PCB_TRACK(b);cap.SetLayer(k.In3_Cu);cap.SetStart(vec(r['start_port']));cap.SetEnd(vec(r['end_port']));cap.SetWidth(150000);missing=poly(cap);missing.BooleanSubtract(union);points=[xy(missing.CVertex(i)) for i in range(missing.VertexCount())];row['levels'].append({'polygon_error_nm':err,'uncovered_capsule_area_mm2':abs(missing.Area())/1e12,'missing_vertices_mm':points})
 out.append(row)
result={'candidate_sha256':hashlib.sha256((O/'hardware/nexus-style-fc.kicad_pcb').read_bytes()).hexdigest(),'status':'Diagnostic exact native taper capsule containment at 20/5/1 nm approximation; no threshold or source change','tapers':out};(O/'taper-diagnostic.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps([{'id':r['id'],'levels':[(x['polygon_error_nm'],x['uncovered_capsule_area_mm2']) for x in r['levels']]} for r in out],indent=2))
