#!/usr/bin/env python3
"""Bounded, read-only 2D placement audit from native geometry; needs Shapely 2."""
import argparse,hashlib,itertools,json,math
from pathlib import Path
from shapely.geometry import Polygon,LineString,Point,box
from shapely.ops import unary_union,polygonize
from shapely.affinity import rotate,translate
ap=argparse.ArgumentParser();ap.add_argument('--geometry',type=Path,required=True);ap.add_argument('--poses',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);ap.add_argument('--preview',type=Path);a=ap.parse_args()
x=json.load(open(a.geometry));cur=x['current'];src=x['published_source'];fs=cur['footprints'];empty=Polygon();sides=['F.Cu','B.Cu'];headers=['J'+str(i)for i in range(2,9)];unsupported=[]
def polys(items):return unary_union([Polygon(q['outer'],q['holes'])for q in items])if items else empty
def fab(ref,f,side):
 lines=[];shapes=[]
 for g in f['graphics']:
  if g['layer']!=side[0]+'.Fab':continue
  s=g['shape'];p=g['start'];q=g['end']
  if s=='Line':lines.append(LineString([p,q]))
  elif s=='Rect':shapes.append(box(min(p[0],q[0]),min(p[1],q[1]),max(p[0],q[0]),max(p[1],q[1])))
  elif s=='Circle':shapes.append(Point(g['center']).buffer(math.dist(g['center'],q),quad_segs=64))
  elif s=='Polygon':shapes.append(polys(g['polygons']))
  else:unsupported.append({'reference':ref,'shape':g})
 shapes.extend(polygonize(unary_union(lines)));return unary_union(shapes)if shapes else empty
g={r:{s:{'body':fab(r,f,s),'lands':unary_union([polys(p['polygons'].get(s,[]))for p in f['pads']]),'court':polys(f['courtyards'].get(s,[]))}for s in sides}for r,f in fs.items()}
for r in g:
 for s in sides:
  z=g[r][s];z['raw']=unary_union([z['body'],z['lands']]);z['reserve']=unary_union([z['body'].buffer(.25 if r in headers else .15,quad_segs=64),z['lands'].buffer(.15 if r in headers else .1,quad_segs=64)])
report={'board_sha256':cur['sha256'],'published_source_sha256':src['sha256'],'native_version':cur['kicad'],'copper_layers':cur['copper_layers'],'count':len(fs),'thickness_mm':cur['thickness_mm'],'outline_unchanged':cur['edge_cuts']==src['edge_cuts'],'orthogonal':all(abs(f['angle']/90-round(f['angle']/90))<1e-8 for f in fs.values()),'unsupported_body_shapes':unsupported,'nominal_conflicts':[],'courtyard_conflicts':[],'bounded_process_conflicts':[],'header_solder_access_conflicts':[],'usb_keepout_conflicts':[],'board_edge_conflicts':[],'board_edge_reserve_conflicts':[],'mounting_hole_conflicts':[],'npth_copper_clearance_conflicts':[],'tight_courtyard_gaps':[]}
poses=json.load(open(a.poses));report['target_pose_mismatches']=[]
for r,v in poses.items():
 f=fs.get(r)
 if f is None or math.dist(v[:2],f['xy'])>1e-6 or abs((v[2]-f['angle']+180)%360-180)>1e-8 or v[3]!=f['side']:report['target_pose_mismatches'].append(r)
report['missing_target_poses']=sorted(set(fs)-set(poses))
report['connector_poses']={r:{k:fs[r][k]for k in['xy','angle','side']}for r in['J'+str(i)for i in range(1,13)]}
report['led_switch_poses']={r:{k:fs[r][k]for k in['xy','angle','side']}for r in['D1','D2','SW1']}
for r,t in itertools.combinations(fs,2):
 for s in sides:
  for kind,key in[('raw','nominal_conflicts'),('court','courtyard_conflicts'),('reserve','bounded_process_conflicts')]:
   q=g[r][s][kind];v=g[t][s][kind]
   if q.is_empty or v.is_empty:continue
   overlap=q.intersection(v).area
   if overlap>1e-8:report[key].append({'refs':[r,t],'side':s,'overlap_mm2':overlap})
   if kind=='court'and overlap<=1e-8 and q.distance(v)<.05:report['tight_courtyard_gaps'].append({'refs':[r,t],'side':s,'gap_mm':q.distance(v)})
for h in headers:
 for r in fs:
  if r in headers:continue
  for s in sides:
   access=g[h][s]['lands'].buffer(.30,quad_segs=64);other=unary_union([g[r][s]['body'].buffer(.15,quad_segs=64),g[r][s]['lands']]);area=access.intersection(other).area
   if area>1e-8:report['header_solder_access_conflicts'].append({'header':h,'reference':r,'side':s,'overlap_mm2':area})
for z in fs['J1']['zones']:
 if not z['forbid_footprints']:continue
 region=polys(z['polygons'])
 for s in z['layers']:
  for r in fs:
   if r=='J1':continue
   area=max(g[r][s][k].intersection(region).area for k in['raw','court'])
   if area>1e-8:report['usb_keepout_conflicts'].append({'zone':z['name'],'reference':r,'side':s,'overlap_mm2':area})
board=box(0,0,41.66,25.4)
mount_holes=[Point(e['center']).buffer(math.dist(e['center'],e['end']),quad_segs=64)for e in cur['edge_cuts']if e['shape']=='Circle']
report['edge_cut_mounting_hole_count']=len(mount_holes)
npth=[]
for ref,f in fs.items():
 for pad in f['pads']:
  if not pad.get('npth'):continue
  dx,dy=pad['drill'];rad=min(dx,dy)/2;delta=abs(dx-dy)/2
  h=(Point(0,0)if delta==0 else LineString([(-delta,0),(delta,0)])if dx>=dy else LineString([(0,-delta),(0,delta)])).buffer(rad,quad_segs=64)
  h=translate(rotate(h,-pad['angle'],origin=(0,0)),*pad['xy']);npth.append((ref,h))
report['npth_hole_count']=len(npth)
for owner,h in npth:
 for ref,f in fs.items():
  for side in sides:
   if ref!=owner:
    area=g[ref][side]['raw'].intersection(h).area
    if area>1e-8:report['mounting_hole_conflicts'].append({'reference':ref,'side':side,'hole_owner':owner,'overlap_mm2':area})
   for pad in f['pads']:
    if pad.get('npth'):continue
    q=polys(pad['polygons'].get(side,[]))
    if not q.is_empty and q.distance(h)<.254-.000001:report['npth_copper_clearance_conflicts'].append({'reference':ref,'pad':pad['number'],'side':side,'hole_owner':owner,'clearance_mm':q.distance(h)})
for r in fs:
 if r in headers:continue
 for s in sides:
  z=g[r][s]
  for q,key in[(z['raw'],'board_edge_conflicts'),(unary_union([z['body'].buffer(.15,quad_segs=64),z['lands'].buffer(.1,quad_segs=64)]),'board_edge_reserve_conflicts')]:
   area=q.difference(board).area
   if area>1e-8:report[key].append({'reference':r,'side':s,'outside_mm2':area})
  for i,h in enumerate(mount_holes):
   area=z['raw'].intersection(h).area
   if area>1e-8:report['mounting_hole_conflicts'].append({'reference':r,'side':s,'hole_index':i,'overlap_mm2':area})
report['header_housing']={'nominal_row_gaps_mm':[fs['J'+str(i+1)]['xy'][1]-fs['J'+str(i)]['xy'][1]-2.54 for i in range(2,8)],'reserved_row_gaps_mm':[fs['J'+str(i+1)]['xy'][1]-fs['J'+str(i)]['xy'][1]-2.54-.5 for i in range(2,8)]}
report['method']={'native_polygon_error_mm':.0001,'bodies':'Closed native Fab centerline polygons; no Fab or silk stroke inflation. Bare testpoints have no body.','smt_body_radial_reserve_mm':.15,'smt_land_solder_growth_mm':.1,'header_body_radial_reserve_mm':.25,'header_land_solder_growth_mm':.15,'header_land_access_band_mm':.3,'board_mm':[41.66,25.4],'nominal_assembly_mm':[47.5,25.4],'limits':'Bounded 2D screen, not a manufacturer tolerance, mating-harness, 3D height, process-yield or flight qualification. Native DRC separately checks copper-to-hole/edge spacing. Routing completion and electrical-current/return checks remain separate.'}
checks=['target_pose_mismatches','missing_target_poses','unsupported_body_shapes','nominal_conflicts','courtyard_conflicts','bounded_process_conflicts','header_solder_access_conflicts','usb_keepout_conflicts','board_edge_conflicts','board_edge_reserve_conflicts','mounting_hole_conflicts','npth_copper_clearance_conflicts'];report['gates']={k:not report[k]for k in checks};report['gates'].update(six_layers=cur['copper_layers']==6,orthogonal=report['orthogonal'],outline_unchanged=report['outline_unchanged']);report['passed']=all(report['gates'].values());report['input_hashes']={p.name:hashlib.sha256(p.read_bytes()).hexdigest()for p in[a.geometry,a.poses]};a.out.write_text(json.dumps(report,indent=2)+'\n')
if a.preview:
 import matplotlib;matplotlib.use('Agg')
 import matplotlib.pyplot as plt
 from matplotlib.patches import Polygon as MP
 fig,axes=plt.subplots(2,1,figsize=(18,21))
 for ax,s in zip(axes,sides):
  for r,f in fs.items():
   c='royalblue'if r.startswith('C')else 'green'if r.startswith('R')else 'darkorange'if r.startswith('U')else 'purple'
   for poly in f['courtyards'].get(s,[]):ax.add_patch(MP(poly['outer'],fill=False,lw=.65,ec=c))
   for p in f['pads']:
    for poly in p['polygons'].get(s,[]):ax.add_patch(MP(poly['outer'],fc=c,ec='none',alpha=.5))
   if (f['side']==s or r.startswith('J'))and f['xy'][0]>=8.5:ax.text(*f['xy'],r,fontsize=8,ha='center',va='center',bbox={'fc':'white','ec':'none','alpha':.65,'pad':.1})
  ax.set(xlim=(8.5,42),ylim=(26,-.5),aspect='equal',xticks=range(9,43),yticks=range(0,27),title=s+' — interior placement, common board coordinates');ax.grid(alpha=.15)
 fig.suptitle('F722 six-layer layout revision · Placement only · Not for fabrication',fontsize=15);fig.tight_layout(rect=(0,0,1,.975));fig.savefig(a.preview,dpi=140)
print(json.dumps({'passed':report['passed'],'board_sha256':report['board_sha256'],'gates':report['gates'],'tight_courtyard_gaps':report['tight_courtyard_gaps']},indent=2))
raise SystemExit(0 if report['passed']else 1)
