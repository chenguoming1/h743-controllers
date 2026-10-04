#!/usr/bin/python3
"""Characterize actual raw reference differences without exempting own-net voids."""
import argparse,hashlib,json,os,pathlib
os.environ.setdefault('KICAD_CONFIG_HOME','/tmp/controller-r3-kicad')
import pcbnew as p
ap=argparse.ArgumentParser();ap.add_argument('--baseline',type=pathlib.Path,required=True);ap.add_argument('--candidate',type=pathlib.Path,required=True);ap.add_argument('--sha256',required=True);ap.add_argument('--geometry',type=pathlib.Path,required=True);ap.add_argument('--out',type=pathlib.Path,required=True);a=ap.parse_args();sha=lambda q:hashlib.sha256(q.read_bytes()).hexdigest();P5='6e2031b040ce8f3a534c2f73abb0091e25b3e6adcab982463264ad8898d65cf8';assert sha(a.baseline)==P5 and sha(a.candidate)==a.sha256
old=p.LoadBoard(str(a.baseline));new=p.LoadBoard(str(a.candidate));reference={p.F_Cu:p.In1_Cu,p.In2_Cu:p.In3_Cu,p.B_Cu:p.In4_Cu};xy=lambda q:[q.x,q.y];mmxy=lambda q:[p.ToMM(q.x),p.ToMM(q.y)]
def planes(b):
 out={l:p.SHAPE_POLY_SET() for l in reference.values()}
 for z in b.Zones():
  if z.GetNetname()!='GND' or z.GetIsRuleArea():continue
  for l in out:
   if z.IsOnLayer(l):out[l].BooleanAdd(z.GetFilledPolysList(l))
 holes=p.SHAPE_POLY_SET()
 for q in list(b.GetTracks())+[v for f in b.GetFootprints() for v in f.Pads()]:
  if not (isinstance(q,p.PCB_VIA) or isinstance(q,p.PAD) and q.HasHole()):continue
  hole=p.SHAPE_POLY_SET();q.GetEffectiveHoleShape().TransformToPolygon(hole,100,p.ERROR_OUTSIDE);holes.BooleanAdd(hole)
 for l in out:out[l].BooleanSubtract(holes)
 return out
P,Q=planes(old),planes(new)
def signal(b,net,layer,thin=False):
 out=p.SHAPE_POLY_SET()
 for t in b.GetTracks():
  if isinstance(t,p.PCB_VIA) or t.GetLayer()!=layer or t.GetNetname()!=net:continue
  v=t
  if thin:
   assert not isinstance(t,p.PCB_ARC);v=p.PCB_TRACK(b);v.SetStart(t.GetStart());v.SetEnd(t.GetEnd());v.SetLayer(layer);v.SetWidth(100)
  poly=p.SHAPE_POLY_SET();v.TransformShapeToPolygon(poly,layer,0,100,p.ERROR_OUTSIDE);out.BooleanAdd(poly)
 return out
rows=[];vias=[q for q in new.GetTracks() if isinstance(q,p.PCB_VIA)]
for target in json.loads(a.geometry.read_text())['facts']['reference_coverage']:
 if target['new_uncovered_edge_mm2']<=0:continue
 net=target['net'];layer=new.GetLayerID(target['layer']);r=reference[layer];data={'net':net,'layer':target['layer'],'reference':new.GetLayerName(r)}
 for label,thin in [('copper_edge',False),('centerline_100nm_tube',True)]:
  before=signal(old,net,layer,thin);before.BooleanSubtract(P[r]);after=signal(new,net,layer,thin);after.BooleanSubtract(Q[r]);raw=p.SHAPE_POLY_SET(after);raw.BooleanSubtract(before)
  residues={}
  for n in [0,1,2,3,4,5,6,7,8,9,10]:
   envelope=p.SHAPE_POLY_SET(before)
   if n:envelope.Inflate(n,p.CORNER_STRATEGY_ROUND_ALL_CORNERS,1)
   difference=p.SHAPE_POLY_SET(after);difference.BooleanSubtract(envelope);residues[str(n)]=difference.Area()/1e12
  pieces=[]
  for i in range(raw.OutlineCount()):
   shape=p.SHAPE_POLY_SET(raw.COutline(i));vertices=[raw.COutline(i).CPoint(j) for j in range(raw.COutline(i).PointCount())];bb=shape.BBox();mid=bb.GetCenter();near=sorted(vias,key=lambda q:(q.GetPosition()-mid).EuclideanNorm())[:4]
   pieces.append({'area_mm2':shape.Area()/1e12,'bbox_mm':[p.ToMM(v) for v in [bb.GetLeft(),bb.GetTop(),bb.GetRight(),bb.GetBottom()]],'vertices_nm':[xy(v) for v in vertices],'max_vertex_distance_to_old_uncovered_nm':max(before.Distance(v) for v in vertices),'nearest_vias':[{'uuid':q.m_Uuid.AsString(),'net':q.GetNetname(),'xy_mm':mmxy(q.GetPosition()),'same_net':q.GetNetname()==net,'distance_from_piece_center_mm':p.ToMM((q.GetPosition()-mid).EuclideanNorm())} for q in near]})
  data[label]={'raw_new_mm2':raw.Area()/1e12,'outside_expanded_old_uncovered_mm2_by_nm':residues,'smallest_tested_zero_residual_envelope_nm':next((int(n) for n,area in residues.items() if area==0),None),'pieces':pieces}
 rows.append(data)
assert sha(a.baseline)==P5 and sha(a.candidate)==a.sha256
result={'baseline_sha256':P5,'candidate_sha256':a.sha256,'method':__doc__,'polygon_approximation_error_nm':100,'centerline_tube_width_nm':100,'rows':rows,'scope':'Raw uncovered copper uses actual saved reference planes with all drill holes subtracted. No own-via exemption is applied in these residual measurements. Native integer Boolean and offset operations themselves can introduce quantization; this characterizes local geometry, not physical SI.'}
a.out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps([{k:v for k,v in row.items() if k not in ['copper_edge','centerline_100nm_tube']}|{key:{k:v for k,v in row[key].items() if k!='pieces'} for key in ['copper_edge','centerline_100nm_tube']} for row in rows],indent=2))
