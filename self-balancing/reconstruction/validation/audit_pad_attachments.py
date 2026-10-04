#!/usr/bin/python3
"""Native copper-polygon trace-to-pad minimum-width attachment screen.

All pad/track contacts come from KiCad effective shapes.  Contacting tracks are
grouped without the pad; the union of each group and the pad is eroded by half
the review width. A connected erosion component must overlap both pad core and
each incident track core. This tests a finite-width passage, not endpoint
coincidence or Boolean electrical continuity. Drill holes are deliberately not
subtracted: approved component annuli/land dimensions are not routing defects.
Failed local contacts require functional alternate-path review before labeling
a route defect. Geometry is inner-approximated at 0.00005 mm; tested widths have
0.0004 mm tolerance. No board is modified.
"""
import argparse, collections, hashlib, json, os, time
from pathlib import Path
os.environ.setdefault('KICAD_CONFIG_HOME','/tmp/controller-r3-kicad')
import pcbnew as p
ERR=50
uid=lambda q:q.m_Uuid.AsString()
xy=lambda q:[q.x/1e6,q.y/1e6]
sha=lambda q:hashlib.sha256(Path(q).read_bytes()).hexdigest()
def polygon(q,l):
 s=p.SHAPE_POLY_SET();q.TransformShapeToPolygon(s,l,0,ERR,p.ERROR_INSIDE);return s
def intersect(a,b):
 s=p.SHAPE_POLY_SET(a);s.BooleanIntersection(b);return s.Area()>1
def erode(s,r):
 z=p.SHAPE_POLY_SET(s);z.Inflate(-round(r*1e6),p.CORNER_STRATEGY_ROUND_ALL_CORNERS,ERR);return z
def trackrow(q):return dict(uuid=uid(q),start_mm=xy(q.GetStart()),end_mm=xy(q.GetEnd()),width_mm=q.GetWidth()/1e6)
def inspect(path,nominal=False):
 before=sha(path);b=p.LoadBoard(str(path));layers=list(b.GetEnabledLayers().CuStack());tracks=[t for t in b.GetTracks() if not isinstance(t,p.PCB_VIA)];pads=[q for f in b.GetFootprints() for q in f.Pads()];by=collections.defaultdict(list);records=[];ncontacts=0;arcs=[];t0=time.time();examined_pairs=0;without_contacts=[]
 for t in tracks:
  by[(t.GetNetname(),t.GetLayer())].append(t)
  if isinstance(t,p.PCB_ARC):arcs.append(uid(t))
 polygons={};shapes={}
 def pol(t,l):
  key=(uid(t),l)
  if key not in polygons:polygons[key]=polygon(t,l)
  return polygons[key]
 def shape(t,l):
  key=(uid(t),l)
  if key not in shapes:shapes[key]=t.GetEffectiveShape(l)
  return shapes[key]
 for pi,q in enumerate(pads):
  for l in layers:
   if not q.IsOnLayer(l):continue
   examined_pairs+=1
   contacts=[t for t in by[(q.GetNetname(),l)] if shape(t,l).GetClearance(shape(q,l))<=0]
   if not contacts:
    without_contacts.append(dict(pad_uuid=uid(q),reference=q.GetParentFootprint().GetReference(),pin=q.GetNumber(),net=q.GetNetname(),layer=b.GetLayerName(l),drill_mm=xy(q.GetDrillSize()),attribute=int(q.GetAttribute())));continue
   ncontacts+=len(contacts);par=list(range(len(contacts)))
   def root(i):
    while par[i]!=i:par[i]=par[par[i]];i=par[i]
    return i
   for i,t in enumerate(contacts):
    for j,u in enumerate(contacts[:i]):
     if shape(t,l).GetClearance(shape(u,l))<=0:par[root(i)]=root(j)
   groups=collections.defaultdict(list)
   for i,t in enumerate(contacts):groups[root(i)].append(t)
   row=dict(pad_uuid=uid(q),reference=q.GetParentFootprint().GetReference(),pin=q.GetNumber(),net=q.GetNetname(),layer=b.GetLayerName(l),xy_mm=xy(q.GetPosition()),size_mm=xy(q.GetSize()),drill_mm=xy(q.GetDrillSize()),shape=int(q.GetShape()),groups=[])
   for ts in groups.values():
    copper=p.SHAPE_POLY_SET(pol(q,l))
    for t in ts:copper.BooleanAdd(pol(t,l))
    intended=min(float('inf') if nominal else .13,min(t.GetWidth()/1e6 for t in ts),q.GetSize().x/1e6,q.GetSize().y/1e6)
    r=max(0,(intended-.0004)/2)
    def connected_at(radius,detail=False,targetids=None):
     u=erode(copper,radius);pc=erode(pol(q,l),radius);tc={uid(t):erode(pol(t,l),radius) for t in ts};passids=set();components=[]
     for k in range(u.OutlineCount()):
      one=u.Subset(k,k+1)
      if not intersect(one,pc):continue
      ids=[uuid for uuid,s in tc.items() if intersect(one,s)];passids.update(ids);components.append(ids)
     return (passids,components) if detail else (set(targetids).issubset(passids) if targetids is not None else len(passids)==len(ts))
    passids,components=connected_at(r,True);fails=[uid(t) for t in ts if uid(t) not in passids];width=None
    if fails:
     lo=0.;hi=intended/2
     for _ in range(14):
      mid=(lo+hi)/2
      if connected_at(mid):lo=mid
      else:hi=mid
     width=round(lo*2,6)
    individual=[]
    if nominal:
     for t in ts:
      target=min(t.GetWidth()/1e6,q.GetSize().x/1e6,q.GetSize().y/1e6);radius=max(0,(target-.0004)/2);passed=connected_at(radius,targetids=[uid(t)]);limit=None
      if not passed:
       lo=0.;hi=target/2
       for _ in range(14):
        mid=(lo+hi)/2
        if connected_at(mid,targetids=[uid(t)]):lo=mid
        else:hi=mid
       limit=round(lo*2,6)
      individual.append(dict(track_uuid=uid(t),nominal_track_width_mm=t.GetWidth()/1e6,land_narrow_dimension_mm=min(q.GetSize().x,q.GetSize().y)/1e6,review_width_mm=target,land_limited=target<t.GetWidth()/1e6,local_finite_width_pass=passed,estimated_local_max_passage_width_mm=limit))
     fails=[v['track_uuid'] for v in individual if not v['local_finite_width_pass']]
    row['groups'].append(dict(tracks=[trackrow(t) for t in ts],review_width_mm=intended,erosion_radius_mm=r,local_finite_width_pass=not fails,failed_track_uuids=fails,estimated_local_max_passage_width_mm=width,pad_connected_eroded_components=components,individual_nominal_tests=individual))
   records.append(row)
 assert sha(path)==before
 return dict(source=str(path),sha256=before,counts=dict(pads=len(pads),examined_pad_layer_pairs=examined_pairs,pad_layer_pairs_without_direct_trace_contacts=len(without_contacts),routed_pad_layer_profiles=len(records),pad_track_contacts=ncontacts,contact_groups=sum(len(q['groups']) for q in records),failed_groups=sum(not g['local_finite_width_pass'] for q in records for g in q['groups']),tracks=len(tracks)),profiles=records,pad_layers_without_direct_trace_contacts=without_contacts,unsupported_arcs=arcs,elapsed_seconds=time.time()-t0)
def main():
 a=argparse.ArgumentParser();a.add_argument('--board',type=Path,required=True);a.add_argument('--sha256',required=True);a.add_argument('--out',type=Path,required=True);a.add_argument('--nominal-width',action='store_true');args=a.parse_args();assert sha(args.board)==args.sha256;r=inspect(args.board,args.nominal_width);r['method']=__doc__;r['mode']='minimum incident nominal width bounded by smallest pad dimension' if args.nominal_width else '0.130mm minimum route-width screen';r['status']='LOCAL GEOMETRY SCREEN: FUNCTIONAL DISPOSITION REQUIRED';args.out.parent.mkdir(parents=True,exist_ok=True);args.out.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(dict(sha256=r['sha256'],counts=r['counts'],elapsed_seconds=r['elapsed_seconds'],failures=[{**{k:v for k,v in q.items() if k!='groups'},'group':g} for q in r['profiles'] for g in q['groups'] if not g['local_finite_width_pass']]),indent=2))
if __name__=='__main__':main()
