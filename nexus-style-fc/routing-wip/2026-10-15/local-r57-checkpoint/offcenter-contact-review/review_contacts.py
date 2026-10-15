from pathlib import Path
import pcbnew as k,json,hashlib,math,sys,collections
O=Path(__file__).parent;R=O.parent;S=R/'routing-continuation/r56-offpad-ground';P=S/'hardware/nexus-style-fc.kicad_pcb';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();assert sha(P)=='64eb0addce9b1ef9c14f29714224834a09e44b96ecd66a967d2f667f9530900f';diag=json.loads((R/'diagnostic-r56-visible-checks/diagnostic-classification.json').read_text());b=k.LoadBoard(str(P));uid=lambda x:x.m_Uuid.AsString();xy=lambda p:(p.x/1e6,p.y/1e6);vec=lambda p:k.VECTOR2I(round(p[0]*1e6),round(p[1]*1e6));ts={uid(t):t for t in b.GetTracks()};ps={uid(p):p for f in b.GetFootprints() for p in f.Pads()};ls=list(b.GetEnabledLayers().CuStack());conn=b.GetConnectivity()
def hit(a,b):
 r=k.SHAPE.Collide(a,b,0);return r[0] if isinstance(r,tuple) else bool(r)
exec((O/'patch_function.py').read_text())
def poly(t,l):
 q=k.SHAPE_POLY_SET();t.TransformShapeToPolygon(q,l,0,50,k.ERROR_OUTSIDE);return q
def circle(c,r):
 q=k.SHAPE_POLY_SET();p=k.SHAPE_LINE_CHAIN()
 for i in range(1024):
  a=2*math.pi*i/1024;p.Append(vec((c[0]+r*math.cos(a),c[1]+r*math.sin(a))))
 p.SetClosed(True);q.AddOutline(p);return q
def area(p):return abs(p.Area())/1e12
def info(q,l):
 d={'uuid':uid(q),'kind':type(q).__name__,'net':q.GetNetname(),'layer':b.GetLayerName(l)}
 if isinstance(q,k.PAD):d.update(ref=q.GetParentFootprint().GetReference(),pin=q.GetNumber(),position=xy(q.GetPosition()),size_mm=xy(q.GetSize()))
 elif isinstance(q,k.PCB_VIA):d.update(position=xy(q.GetPosition()),diameter_mm=q.GetWidth(l)/1e6,drill_mm=q.GetDrillValue()/1e6)
 else:d.update(width_mm=q.GetWidth()/1e6,start=xy(q.GetStart()),end=xy(q.GetEnd()))
 return d
rows=[]
for old in diag['centering_rows']:
 t=ts[old['track_uuid']];v=ts[old['via_uuid']];l=t.GetLayer();land=poly(v,l);hole=circle(xy(v.GetPosition()),v.GetDrillValue()/2e6);ann=k.SHAPE_POLY_SET(land);ann.BooleanSubtract(hole);tp=poly(t,l);over=k.SHAPE_POLY_SET(tp);over.BooleanIntersection(ann);depths=[]
 for depth in [.02,.01,.005,.002,.001]:
  proof=finite_patch(t,v,depth)
  if proof:depths.append(proof);break
 donors=[];alternates=[];viaobjs=[]
 for q in list(conn.GetConnectedTracks(v))+list(conn.GetConnectedPads(v)):
  u=uid(q)
  if u==uid(v):continue
  q=ts.get(u) or ps.get(u);layers=[a for a in ls if q.IsOnLayer(a) and v.IsOnLayer(a) and hit(q.GetEffectiveShape(a),v.GetEffectiveShape(a))]
  for a in layers:
   data=info(q,a);qp=poly(q,a);vp=poly(v,a);vp.BooleanSubtract(hole);qp.BooleanIntersection(vp);data['annular_overlap_area_mm2']=area(qp)
   if isinstance(q,k.PAD):
    remain=k.SHAPE_POLY_SET(vp);remain.BooleanSubtract(poly(q,a));data['entire_annular_land_contained_in_pad']=area(remain)<1e-8
   elif not isinstance(q,k.PCB_VIA):data['direct_full_width_entry']=finite_patch(q,v,.02)
   donors.append(data)
  if l in layers:viaobjs.append(q)
 # Exact same-width endpoint chain to another proved track entry; at most 3 unchanged segments.
 frontier=[(t,[uid(t)])];seen=set()
 while frontier:
  cur,path=frontier.pop(0);u=uid(cur)
  if u in seen:continue
  seen.add(u)
  if u!=uid(t):
   pp=finite_patch(cur,v,.02)
   if pp:alternates.append({'path':path,'minimum_width_mm':min(ts[a].GetWidth()/1e6 for a in path),'finite_entry':pp});continue
  if len(path)>=4:continue
  endpoints={xy(cur.GetStart()),xy(cur.GetEnd())}
  for q in conn.GetConnectedTracks(cur):
   w=uid(q);q=ts[w]
   if w in seen or isinstance(q,k.PCB_VIA) or q.GetLayer()!=l or q.GetNetname()!=t.GetNetname() or q.GetWidth()<t.GetWidth():continue
   if endpoints&{xy(q.GetStart()),xy(q.GetEnd())} and hit(cur.GetEffectiveShape(l),q.GetEffectiveShape(l)):frontier.append((ts[w],path+[w]))
 pad_paths=[]
 for p in ps.values():
  if not p.IsOnLayer(l) or p.GetNetname()!=t.GetNetname():continue
  if hit(t.GetEffectiveShape(l),p.GetEffectiveShape(l)) and hit(v.GetEffectiveShape(l),p.GetEffectiveShape(l)):
   a=poly(t,l);a.BooleanIntersection(poly(p,l));annleft=k.SHAPE_POLY_SET(ann);annleft.BooleanSubtract(poly(p,l));pad_paths.append({'pad':info(p,l),'track_pad_overlap_area_mm2':area(a),'whole_via_annulus_inside_pad':area(annleft)<1e-8,'qualification':'Pad bridge present; whole-annulus containment and geometric overlap are reported separately, not inferred from net connectivity.'})
 classification='direct full-width annular entry >=0.020 mm' if old['direct_full_track_width_by_0_020_mm_annular_patch'] else 'same-width retained donor chain reaches a proven >=0.020 mm annular entry' if alternates else 'shorter direct full-width annular entry measured; margin is limited' if depths else 'partial-annular junction needs explicit donor/contact review; direct full-width entry not established'
 rows.append({**old,'annular_overlap_area_mm2':area(over),'via_annulus_area_mm2':area(ann),'fraction_of_via_annulus_contacted_on_layer':area(over)/area(ann),'largest_tested_full_width_entry':depths[0] if depths else None,'retained_same_width_track_donor_paths':alternates,'shared_pad_paths':pad_paths,'all_direct_via_donors':donors,'review_classification':classification})
out={'status':'Read-only complete inventory of all 18 reenabled off-center findings; no warning or geometry changed','source_board_sha256':sha(P),'all_visible_diagnostic_sha256':sha(R/'diagnostic-r56-visible-checks/native-drc.json'),'area_method':'Native polygon copper with 0.00005 mm arc approximation; subtract 1024-vertex nominal drill circle. Contact areas are approximate geometric measures, not current/thermal ratings. Finite rectangle tests use exact native shape containment and exclude a 0.001 mm drill margin.','findings':rows,'classification_counts':dict(collections.Counter(r['review_classification'] for r in rows)),'limits':'Exact endpoint/width and actual pad/annular contacts, not netlist continuity alone. Off-center geometry can be valid; failed finite-entry tests do not alone prove a tangent/neck. Any unproved power junction remains open for explicit donor/ampacity review.'};(O/'contact-review.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out['classification_counts'],indent=2));print([(r['net'],r['track_uuid'],r['track_width_mm'],r['annular_overlap_area_mm2'],r['review_classification']) for r in rows if not r['direct_full_track_width_by_0_020_mm_annular_patch']]);assert sha(P)==out['source_board_sha256']
