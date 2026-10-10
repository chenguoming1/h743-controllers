#!/usr/bin/env python3
"""Read-only native KiCad mechanical geometry export; run with KiCad's Python."""
import argparse,hashlib,json
from pathlib import Path
import pcbnew as p
ap=argparse.ArgumentParser();ap.add_argument('--board',type=Path,required=True);ap.add_argument('--source',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
def xy(v):return[v.x/1e6,v.y/1e6]
def poly(s):return[{'outer':[xy(s.Outline(i).CPoint(j))for j in range(s.Outline(i).PointCount())],'holes':[[xy(s.Hole(i,h).CPoint(j))for j in range(s.Hole(i,h).PointCount())]for h in range(s.HoleCount(i))]}for i in range(s.OutlineCount())]
def shape(s):
 d={'layer':s.GetLayerName(),'shape':s.GetShapeStr(),'start':xy(s.GetStart()),'end':xy(s.GetEnd()),'width':s.GetWidth()/1e6}
 if s.GetShapeStr()=='Arc':d['mid']=xy(s.GetArcMid())
 if s.GetShapeStr()=='Circle':d['center']=xy(s.GetCenter())
 if s.GetShapeStr()=='Polygon':d['polygons']=poly(s.GetPolyShape())
 return d
def extract(path):
 before=hashlib.sha256(path.read_bytes()).hexdigest();b=p.LoadBoard(str(path));fs={}
 for f in b.GetFootprints():
  f.BuildCourtyardCaches();o={'value':f.GetValue(),'fpid':str(f.GetFPID().GetLibNickname())+':'+str(f.GetFPID().GetLibItemName()),'xy':xy(f.GetPosition()),'angle':f.GetOrientationDegrees(),'side':f.GetLayerName(),'pads':[],'graphics':[],'courtyards':{},'zones':[]};fs[f.GetReference()]=o
  for pad in f.Pads():
   q={'number':pad.GetNumber(),'xy':xy(pad.GetPosition()),'size':xy(pad.GetSize()),'shape':pad.GetShape(),'attribute':pad.GetAttribute(),'angle':pad.GetOrientationDegrees(),'drill':xy(pad.GetDrillSize()),'npth':pad.GetAttribute()==p.PAD_ATTRIB_NPTH,'net':pad.GetNetname(),'polygons':{}}
   for l in[p.F_Cu,p.B_Cu]:
    if pad.IsOnLayer(l):
     s=p.SHAPE_POLY_SET();pad.TransformShapeToPolygon(s,l,0,100,p.ERROR_OUTSIDE);q['polygons'][b.GetLayerName(l)]=poly(s)
   o['pads'].append(q)
  o['graphics']=[shape(s)for s in f.GraphicalItems()if isinstance(s,p.PCB_SHAPE)]
  o['courtyards']={b.GetLayerName(l):poly(f.GetCourtyard(l))for l in[p.F_Cu,p.B_Cu]}
  o['zones']=[{'name':z.GetZoneName(),'rule':z.GetIsRuleArea(),'forbid_footprints':z.GetDoNotAllowFootprints(),'layers':[b.GetLayerName(l)for l in z.GetLayerSet().Seq()],'polygons':poly(z.Outline())}for z in f.Zones()]
 assert hashlib.sha256(path.read_bytes()).hexdigest()==before
 return{'sha256':before,'kicad':p.GetBuildVersion(),'copper_layers':b.GetCopperLayerCount(),'thickness_mm':b.GetDesignSettings().GetBoardThickness()/1e6,'edge_cuts':[shape(s)for s in b.GetDrawings()if isinstance(s,p.PCB_SHAPE)and s.GetLayer()==p.Edge_Cuts],'footprints':fs}
r={'current':extract(a.board),'published_source':extract(a.source)};a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(r,separators=(',',':'))+'\n');print(json.dumps({k:{q:v[q]for q in['sha256','kicad','copper_layers']}for k,v in r.items()}))
