#!/usr/bin/env python3
"""Construct one explicitly selected planar path located by a failed engine attempt.
This is native route construction, not successful stock engine insertion.
"""
import argparse,hashlib,json,re
from pathlib import Path
from shapely import unary_union
from shapely.geometry import Polygon,LineString
ap=argparse.ArgumentParser()
for name in ['model','native','base-session','base-report','diagnostic-log','out-prefix']:ap.add_argument('--'+name,type=Path,required=True)
ap.add_argument('--waypoint-offsets',type=Path);ap.add_argument('--net',required=True);ap.add_argument('--path-index',type=int,required=True)
a=ap.parse_args();sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();m=json.loads(a.model.read_text());n=json.loads(a.native.read_text());e=json.loads(a.base_report.read_text())
assert m['board_sha256']==n['board_sha256']==e['board_sha256'];assert e['model_sha256']==sha(a.model);assert m['aliases'][a.net]==a.net;assert a.net not in m['source_logical_nets'].values(),'Use a continuation-aware construction for pre-existing net routes'
paths=[json.loads(line[len('INSERT_DIAGNOSTIC '):])for line in a.diagnostic_log.read_text().splitlines()if line.startswith('INSERT_DIAGNOSTIC ')]
paths=[p for p in paths if p['net']==a.net and p['stage']=='located_trace'];p=paths[a.path_index];assert p['layer']in m['routable_layers'];width=2*p['half_width_mm'];assert width==.127
raw=[[round(v*1e5)for v in xy]for xy in p['requested_corners_mm']];points=[]
for xy in raw:
 if points and xy==points[-1]:continue
 while len(points)>=2:
  aa,bb=points[-2:];u=[bb[i]-aa[i]for i in (0,1)];v=[xy[i]-bb[i]for i in (0,1)]
  if u[0]*v[1]-u[1]*v[0]!=0 or sum(u[i]*v[i]for i in (0,1))<0:break
  points.pop()
 points.append(xy)
assert len(points)>=2;coords=[[v/1e5 for v in xy]for xy in points];line=LineString(coords);rawline=LineString([[v/1e5 for v in xy]for xy in raw]);assert line.hausdorff_distance(rawline)<1e-12
original_normalized_coords=coords;adjustment=None
if a.waypoint_offsets:
 adjustment=json.loads(a.waypoint_offsets.read_text());before=[xy[:]for xy in points]
 for key,delta in adjustment['waypoint_offsets_mm'].items():
  index=int(key);assert 0<index<len(points)-1,'Keep original native pad endpoints unchanged';points[index]=[points[index][i]+round(delta[i]*1e5)for i in (0,1)]
 assert all((aa[0]==bb[0]or aa[1]==bb[1]or abs(aa[0]-bb[0])==abs(aa[1]-bb[1]))for aa,bb in zip(points,points[1:])),'Adjusted route must retain 45-degree paths'
 coords=[[v/1e5 for v in xy]for xy in points];line=LineString(coords);adjustment.update(offset_file_sha256=sha(a.waypoint_offsets),maximum_waypoint_displacement_mm=max(((sum((aa[i]-bb[i])**2 for i in (0,1)))**.5/1e5)for aa,bb in zip(before,points)))
geom=lambda ps:unary_union([Polygon(q['outer'],q.get('holes',[]))for q in ps]);gaps=[]
for o in n['objects']:
 if o['net']==a.net or p['layer']not in o['copper']:continue
 gap=line.distance(geom(o['copper'][p['layer']]))-width/2
 gaps.append({'uuid':o['uuid'],'key':o.get('key'),'net':o['net'],'gap_mm':gap})
minimum=min(gaps,key=lambda x:x['gap_mm']);assert minimum['gap_mm']>=.127,minimum
text=a.base_session.read_text();assert re.search(r'\(resolution\s+mm\s+100000\)',text);assert not re.search(r'\(net\s+(?:'+re.escape(a.net)+'|'+re.escape(json.dumps(a.net))+r')(?=\s|\))',text)
start=text.index('(network_out');depth=0;quoted=False;escape=False;end=None
for i in range(start,len(text)):
 c=text[i]
 if quoted:
  if escape:escape=False
  elif c=='\\':escape=True
  elif c=='"':quoted=False
 elif c=='"':quoted=True
 elif c=='(':depth+=1
 elif c==')':
  depth-=1
  if depth==0:end=i;break
assert end is not None
wire='\n      (net '+json.dumps(a.net)+' (wire (path '+p['layer']+' 12700 '+' '.join(f'{x} {-y}'for x,y in points)+') (type route)))\n    '
text=text[:end]+wire+text[end:]
receipt={'kind':'native_construction_from_located_engine_path','engine_insertion_succeeded':False,'board_sha256':m['board_sha256'],'model_sha256':sha(a.model),'native_sha256':sha(a.native),'base_session_sha256':sha(a.base_session),'base_report_sha256':sha(a.base_report),'diagnostic_log_sha256':sha(a.diagnostic_log),'net':a.net,'layer':p['layer'],'width_mm':width,'selected_located_path_index':a.path_index,'original_points_mm':p['requested_corners_mm'],'original_normalized_points_mm':original_normalized_coords,'constructed_points_mm':coords,'explicit_waypoint_adjustment':adjustment,'normalization':'Exact integer collinear and duplicate removal preserves the original centerline before any separately declared waypoint adjustment.','minimum_foreign_object_clearance':minimum,'native_drc_endpoint_protection_process_validation_required':True,'construction_source_sha256':sha(__file__)}
e.pop('areas',None);e.pop('contact_partitions',None);e['route_construction']=receipt;e['native_validation_required']=True;e['routes'].append({'kind':'track','fixed':'NOT_FIXED','nets':[a.net],'layer':p['layer'],'width':width,'points':coords});a.out_prefix.parent.mkdir(parents=True,exist_ok=True);ses=Path(str(a.out_prefix)+'.ses');report=Path(str(a.out_prefix)+'.constructed-report.json');ses.write_text(text);report.write_text(json.dumps(e,indent=2)+'\n');receipt.update(output_session_sha256=sha(ses),output_report_sha256=sha(report));Path(str(a.out_prefix)+'.construction.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt))
