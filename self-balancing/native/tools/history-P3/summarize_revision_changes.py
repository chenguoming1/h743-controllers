#!/usr/bin/python3
"""Compare current routed geometry with the preserved P2 source; never edits CAD."""
import argparse,collections,hashlib,json,os,sys
from pathlib import Path
import pcbnew as p
ap=argparse.ArgumentParser();ap.add_argument('--baseline',type=Path,required=True);ap.add_argument('--current',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
sha=lambda q:hashlib.sha256(q.read_bytes()).hexdigest();hashes=[sha(a.baseline),sha(a.current)]
boards=[p.LoadBoard(str(q)) for q in [a.baseline,a.current]]
def xy(q):return [p.ToMM(q.x),p.ToMM(q.y)]
def uid(q):return q.m_Uuid.AsString()
def track(q):
 d={'uuid':uid(q),'net':q.GetNetname(),'layer':q.GetLayerName(),'start_mm':xy(q.GetStart()),'end_mm':xy(q.GetEnd()),'width_mm':p.ToMM(q.GetWidth(p.F_Cu) if isinstance(q,p.PCB_VIA) else q.GetWidth())}
 if isinstance(q,p.PCB_VIA):d.update(drill_mm=p.ToMM(q.GetDrillValue()),kind='via')
 else:d.update(kind='track',length_mm=p.ToMM(q.GetLength()))
 return d
def footprint(q):return {'xy_mm':xy(q.GetPosition()),'angle_deg':q.GetOrientationDegrees(),'layer':q.GetLayerName(),'footprint':str(q.GetFPID().GetLibNickname())+':'+str(q.GetFPID().GetLibItemName()),'value':q.GetValue()}
inventories=[{uid(t):track(t) for t in b.GetTracks()} for b in boards];fps=[{f.GetReference():footprint(f) for f in b.GetFootprints()} for b in boards]
fp_changes=[{'reference':r,'before':fps[0].get(r),'after':fps[1].get(r)} for r in sorted(fps[0].keys()|fps[1].keys()) if fps[0].get(r)!=fps[1].get(r)]
via_changes=[{'uuid':u,'before':inventories[0].get(u),'after':inventories[1].get(u)} for u in sorted(inventories[0].keys()|inventories[1].keys()) if (inventories[0].get(u,{}).get('kind')=='via' or inventories[1].get(u,{}).get('kind')=='via') and inventories[0].get(u)!=inventories[1].get(u)]
stats=[]
for data in inventories:
 ts=[x for x in data.values() if x['kind']=='track'];vs=[x for x in data.values() if x['kind']=='via'];hist=collections.Counter(x['width_mm'] for x in ts)
 stats.append({'track_segments':len(ts),'vias':len(vs),'total_track_length_mm':sum(x['length_mm'] for x in ts),'width_histogram_mm':dict(sorted(hist.items())),'below_0130_count':sum(x['width_mm']<.13 for x in ts)})
res={'baseline':str(a.baseline),'current':str(a.current),'sha256':hashes,'baseline_stats':stats[0],'current_stats':stats[1],'segment_reduction':stats[0]['track_segments']-stats[1]['track_segments'],'footprint_changes':fp_changes,'via_changes':via_changes,'track_geometry_changes':sum(inventories[0][u]!=inventories[1][u] for u in inventories[0].keys()&inventories[1].keys()),'removed_copper_objects':len(inventories[0].keys()-inventories[1].keys()),'added_copper_objects':len(inventories[1].keys()-inventories[0].keys()),'qualification':'Geometry comparison only; electrical, clearance, return-path and manufacturing acceptance are separate audits. Segment reduction is not by itself an electrical-quality claim.'}
assert hashes==[sha(a.baseline),sha(a.current)];a.out.write_text(json.dumps(res,indent=2)+'\n');print(json.dumps({k:res[k] for k in ['segment_reduction','baseline_stats','current_stats','footprint_changes']},indent=2));sys.stdout.flush();os._exit(0)
