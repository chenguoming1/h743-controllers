#!/usr/bin/python3
"""Require real multilayer use of vias; internal placeholder strokes do not count.

A functional layer has actual via contact to a native trace component reaching
another distinct pad/via terminal, direct pad copper contact, or native filled
zone overlap. Trace-to-land quality and interterminal topology are separate gates.
"""
import argparse,collections,hashlib,json,os
from pathlib import Path
os.environ.setdefault('KICAD_CONFIG_HOME','/tmp/controller-r3-kicad')
import pcbnew as p
from audit_single_terminal_copper import inventory
sha=lambda q:hashlib.sha256(q.read_bytes()).hexdigest()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--candidate',type=Path,required=True);ap.add_argument('--sha256',required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();assert sha(a.candidate)==a.sha256;tools={str(q):sha(q) for q in [Path(__file__),Path(__file__).with_name('audit_single_terminal_copper.py')]};I=inventory(a.candidate);b=p.LoadBoard(str(a.candidate));layers=list(b.GetEnabledLayers().CuStack());pads=[q for f in b.GetFootprints() for q in f.Pads()];zones=collections.defaultdict(list)
 for z in b.Zones():
  if z.GetIsRuleArea():continue
  for l in layers:
   if z.IsOnLayer(l) and z.HasFilledPolysForLayer(l):zones[z.GetNetname(),l].append(z.GetFilledPolysList(l))
 rows=[]
 for v in b.GetTracks():
  if not isinstance(v,p.PCB_VIA):continue
  u=v.m_Uuid.AsString();functional=[q for q in I['all_component_terminal_inventory'] if len(q['terminals'])>1 and any(t['uuid']==u for t in q['terminals'])];ls={q['layer'] for q in functional};pl=[];zl=[]
  for l in layers:
   if not v.IsOnLayer(l):continue
   shape=v.GetEffectiveShape(l)
   for q in pads:
    if q.GetNetname()==v.GetNetname() and q.IsOnLayer(l) and shape.GetClearance(q.GetEffectiveShape(l))<=0:pl.append({'layer':b.GetLayerName(l),'pad':q.GetParentFootprint().GetReference()+'.'+q.GetNumber()});ls.add(b.GetLayerName(l))
   for z in zones[v.GetNetname(),l]:
    poly=p.SHAPE_POLY_SET();v.TransformShapeToPolygon(poly,l,0,50,p.ERROR_OUTSIDE);poly.BooleanIntersection(z)
    if poly.Area()>0:zl.append(b.GetLayerName(l));ls.add(b.GetLayerName(l))
  rows.append({'uuid':u,'net':v.GetNetname(),'xy_mm':[v.GetPosition().x/1e6,v.GetPosition().y/1e6],'functional_layers':sorted(ls),'functional_track_components':functional,'direct_pad_contacts':pl,'zone_layers':zl,'review':len(ls)<2})
 flags=[r for r in rows if r['review']];assert sha(a.candidate)==a.sha256 and all(sha(Path(q))==h for q,h in tools.items());out={'status':'REVIEW REQUIRED' if flags else 'PASS REAL MULTILAYER VIA USE','source':str(a.candidate),'candidate_sha256':a.sha256,'audit_script_sha256':tools,'via_count':len(rows),'ground_vias':sum(r['net']=='GND' for r in rows),'one_layer_or_zero_layer_review':flags,'all_via_roles':rows,'method':__doc__};a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'status':out['status'],'via_count':len(rows),'flag_count':len(flags),'flags':[{k:r[k] for k in ['uuid','net','xy_mm','functional_layers']} for r in flags]},indent=2))
if __name__=='__main__':main()
