#!/usr/bin/python3
"""Read-only census of actual same-layer trace components with at most one land.

Contacts use native effective copper, including rounded caps. Distinct pads and
vias are counted by UUID. Filled zone contact is recorded separately, so a
ground stub that actually joins a plane is not misclassified as a floating end.
Actual trace copper outside the attached land is measured. A one-terminal trace
component cannot conduct between different terminals on its layer, although
intentional test/antenna/current-spreading copper still needs engineering review.
This bounded census does not detect every side branch of a multi-terminal tree.
"""
import argparse,collections,hashlib,json,os
from pathlib import Path
os.environ.setdefault('KICAD_CONFIG_HOME','/tmp/controller-r3-kicad')
import pcbnew as p
uid=lambda t:t.m_Uuid.AsString()
sha=lambda q:hashlib.sha256(q.read_bytes()).hexdigest()
mm=lambda v:[v.x/1e6,v.y/1e6]
def poly(q,l):
 r=p.SHAPE_POLY_SET();q.TransformShapeToPolygon(r,l,0,50,p.ERROR_OUTSIDE);return r
def rec(q,l):
 if isinstance(q,p.PCB_VIA):return {'kind':'via','uuid':uid(q),'at_mm':mm(q.GetPosition()),'diameter_mm':q.GetWidth(l)/1e6}
 return {'kind':'pad','uuid':uid(q),'reference':q.GetParentFootprint().GetReference()+'.'+q.GetNumber(),'at_mm':mm(q.GetPosition())}
def inventory(path):
 b=p.LoadBoard(str(path));layers=list(b.GetEnabledLayers().CuStack());tracks=collections.defaultdict(list);lands=collections.defaultdict(list);zones=collections.defaultdict(list)
 for q in list(b.GetTracks())+[pd for f in b.GetFootprints() for pd in f.Pads()]:
  if isinstance(q,(p.PAD,p.PCB_VIA)):
   for l in layers:
    if q.IsOnLayer(l):lands[q.GetNetname(),l].append(q)
  else:tracks[q.GetNetname(),q.GetLayer()].append(q)
 for z in b.Zones():
  if z.GetIsRuleArea():continue
  for l in layers:
   if z.IsOnLayer(l) and z.HasFilledPolysForLayer(l):zones[z.GetNetname(),l].append((uid(z),z.GetFilledPolysList(l)))
 candidates=[];component_inventory=[];summary=collections.Counter();pernet=collections.defaultdict(collections.Counter)
 for (net,l),ts in sorted(tracks.items()):
  par=list(range(len(ts)));shapes=[q.GetEffectiveShape(l) for q in ts];bbs=[q.BBox() for q in shapes]
  def root(i):
   while par[i]!=i:par[i]=par[par[i]];i=par[i]
   return i
  order=sorted(range(len(ts)),key=lambda i:bbs[i].GetLeft())
  for oi,i in enumerate(order):
   a=bbs[i]
   for j in order[oi+1:]:
    c=bbs[j]
    if c.GetLeft()>a.GetRight():break
    if c.GetTop()>a.GetBottom() or c.GetBottom()<a.GetTop():continue
    if shapes[i].GetClearance(shapes[j])<=0:par[root(i)]=root(j)
  groups=collections.defaultdict(list)
  for i in range(len(ts)):groups[root(i)].append(i)
  pernet[net]['tracks']+=len(ts)
  for ids in groups.values():
   summary['same_layer_track_components']+=1;pernet[net]['components']+=1
   terminals=[q for q in lands[net,l] if any(shapes[i].GetClearance(q.GetEffectiveShape(l))<=0 for i in ids)]
   component_inventory.append({'net':net,'layer':b.GetLayerName(l),'track_uuids':[uid(ts[i]) for i in ids],'terminals':[rec(q,l) for q in terminals]})
   summary['components_with_'+str(min(len(terminals),2))+'_or_more_terminals' if len(terminals)>=2 else 'components_with_'+str(len(terminals))+'_terminal']+=1
   if len(terminals)>1:continue
   copper=p.SHAPE_POLY_SET()
   for i in ids:copper.BooleanAdd(poly(ts[i],l))
   outside=p.SHAPE_POLY_SET(copper)
   for q in terminals:outside.BooleanSubtract(poly(q,l))
   zone_contacts=[]
   for zid,zp in zones[net,l]:
    overlap=p.SHAPE_POLY_SET(copper);overlap.BooleanIntersection(zp)
    if overlap.Area()>0:zone_contacts.append({'zone_uuid':zid,'actual_overlap_mm2':overlap.Area()/1e12})
   area=outside.Area()/1e12
   cls='TERMINAL-CONTAINED COPPER' if area<=1e-10 else 'FILLED-PLANE CONTACT; NOT A FREE DEAD END' if zone_contacts else 'EXPOSED SINGLE-TERMINAL COMPONENT; REVIEW' if terminals else 'NO TERMINAL OR PLANE CONTACT; REVIEW'
   summary[cls]+=1;pernet[net][cls]+=1
   bb=copper.BBox()
   candidates.append({'net':net,'layer':b.GetLayerName(l),'classification':cls,'terminal_count':len(terminals),'terminals':[rec(q,l) for q in terminals],'filled_zone_contacts':zone_contacts,'copper_area_mm2':copper.Area()/1e12,'copper_outside_attached_lands_mm2':area,'bbox_mm':[bb.GetLeft()/1e6,bb.GetTop()/1e6,bb.GetRight()/1e6,bb.GetBottom()/1e6],'track_count':len(ids),'total_centerline_length_mm':sum(ts[i].GetLength()/1e6 for i in ids),'tracks':[{'uuid':uid(ts[i]),'start_mm':mm(ts[i].GetStart()),'end_mm':mm(ts[i].GetEnd()),'width_mm':ts[i].GetWidth()/1e6} for i in ids]})
 via_roles=[]
 for q in candidates:
  if q['classification']!='TERMINAL-CONTAINED COPPER' or len(q['terminals'])!=1 or q['terminals'][0]['kind']!='via':continue
  v=q['terminals'][0];functional=[r for r in component_inventory if len(r['terminals'])>1 and any(t['uuid']==v['uuid'] for t in r['terminals'])];vlayers=sorted({r['layer'] for r in functional});native=next(t for t in b.GetTracks() if uid(t)==v['uuid']);zlinks=[]
  for l in layers:
   for zid,zp in zones[q['net'],l]:
    contact=poly(native,l);contact.BooleanIntersection(zp)
    if contact.Area()>0:zlinks.append({'layer':b.GetLayerName(l),'zone_uuid':zid,'overlap_mm2':contact.Area()/1e12})
  via_roles.append({'via':v,'net':q['net'],'contained_stub_layer':q['layer'],'contained_stub_tracks':q['tracks'],'functional_trace_layers':vlayers,'functional_trace_components':functional,'zone_contacts':zlinks,'classification':'BENIGN: VIA HAS TWO FUNCTIONAL ROUTING LAYERS OR REAL PLANE CONTACT' if len(vlayers)>=2 or zlinks else 'REDUNDANT ONE-LAYER VIA REVIEW'})
 return {'summary':dict(summary),'per_net':{n:dict(v) for n,v in pernet.items()},'candidates':candidates,'routed_nets':len(pernet),'all_component_terminal_inventory':component_inventory,'contained_signal_via_roles':via_roles}
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--candidate',type=Path,required=True);ap.add_argument('--sha256',required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();assert sha(a.candidate)==a.sha256;script=sha(Path(__file__));report=inventory(a.candidate);assert sha(a.candidate)==a.sha256 and sha(Path(__file__))==script
 report.update({'source':str(a.candidate),'source_sha256':a.sha256,'audit_script_sha256':script,'method':__doc__,'native_polygon_error_nm':50});a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'report':str(a.out),'routed_nets':report['routed_nets'],'summary':report['summary'],'review':[{k:q[k] for k in ['net','layer','track_count','bbox_mm','total_centerline_length_mm','terminals']} for q in report['candidates'] if q['classification'].endswith('REVIEW')]},indent=2))
if __name__=='__main__':main()
