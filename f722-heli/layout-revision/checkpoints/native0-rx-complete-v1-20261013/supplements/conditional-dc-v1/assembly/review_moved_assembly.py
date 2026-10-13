#!/usr/bin/env python3
"""One bounded read-only local assembly geometry pass; no KiCad/native execution."""
import os,sys,resource,fcntl,json,gzip,hashlib,signal
from pathlib import Path
os.environ['OPENBLAS_NUM_THREADS']='1';os.environ['OMP_NUM_THREADS']='1';sys.dont_write_bytecode=True
resource.setrlimit(resource.RLIMIT_AS,(768*1024**2,)*2);resource.setrlimit(resource.RLIMIT_CPU,(60,65));signal.alarm(75)
ROOT=Path(os.environ['F722_ASSEMBLY_WORK_ROOT']);OUT=ROOT/'output'
lock=(ROOT/'replay.lock').open('rb');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
import shapely
from shapely.geometry import Polygon,Point,box,LineString,GeometryCollection
from shapely.ops import unary_union,polygonize
from shapely.affinity import rotate
D=ROOT/'inputs'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
expected='84229c571433bd72d410fb18d02cffa3a380c00a87fbe1270e3a73b63f8dd6cd'
assert sha(D/'diagnostic-board/f722-heli.kicad_pcb')==expected
assert sha(D/'after.native.json.gz')=='83a6c87643977d21a1c3841bc26d4f28694ff721436e36ba20824b7b191174d1'
data=json.load(gzip.open(D/'after.native.json.gz','rt'));assert data['board_sha256']==expected
settings=json.loads((D/'after-pad-settings.json').read_text());fps={f['ref']:f for f in data['footprints']};pads=[o for o in data['objects'] if o['kind']=='pad'];objects={o['uuid']:o for o in data['objects']}
def geom(ps):return unary_union([Polygon(p['outer'],p.get('holes',[])) for p in ps])
def graphic_region(f,layer):
 gs=[];lines=[]
 for g in f['graphics']:
  if g['layer']!=layer:continue
  if 'polygons' in g:gs.append(geom(g['polygons']))
  elif g['shape']=='Rect':gs.append(box(min(g['start'][0],g['end'][0]),min(g['start'][1],g['end'][1]),max(g['start'][0],g['end'][0]),max(g['start'][1],g['end'][1])))
  elif g['shape']=='Line':lines.append(LineString([g['start'],g['end']]))
 if lines:gs.extend(polygonize(unary_union(lines)))
 return unary_union(gs)
def nearest(g,rows,count=3):return [{'distance_mm':g.distance(x),'owner':n,'overlap_mm2':g.intersection(x).area} for x,n in sorted(rows,key=lambda row:(g.distance(row[0]),row[1]))[:count]]
regions={s:{'land':[],'mask':[],'paste':[],'body':[],'courtyard':[]} for s in ['F.Cu','B.Cu']}
for side,rs in regions.items():
 for p in pads:
  name=p['ref']+'.'+p['number'];ml=side.replace('.Cu','.Mask');pl=side.replace('.Cu','.Paste')
  if side in p['copper']:rs['land'].append((geom(p['copper'][side]),name))
  if ml in p['mask']:rs['mask'].append((geom(p['mask'][ml]['polygons']),name))
  if pl in p['all_layers']:
   assert all(v==[0,0] for v in settings[p['uuid']]['effective_paste'].values())
   if side in p['copper']:g=geom(p['copper'][side])
   else:
    x,y=p['xy'];w,h=p['size'];g=rotate(box(x-w/2,y-h/2,x+w/2,y+h/2),-p['angle'],origin=(x,y));name+='[conservative paste-only bound]'
   rs['paste'].append((g,name))
 for r,f in fps.items():
  for g in f['graphics']:
   if g['layer']==side.replace('.Cu','.Paste') and 'polygons' in g:rs['paste'].append((geom(g['polygons']),r+'.graphic.'+g['uuid']))
  if f['side']==side:
   for key,layer in [('body',side.replace('.Cu','.Fab')),('courtyard',side.replace('.Cu','.Courtyard'))]:
    g=graphic_region(f,layer)
    if not g.is_empty:rs[key].append((g,r))
holes=[(geom(o['drill']['outside']),o['uuid']) for o in objects.values() if o.get('drill')]
res={'schema':'f722-native0-local-assembly-review/v1','source_pcb_sha256':expected,'native_compressed_sha256':sha(D/'after.native.json.gz'),'pad_settings_sha256':sha(D/'after-pad-settings.json'),'shapely_version':shapely.__version__,'moved_parts':{},'vias':{},'scope':'Three moved bottom components and relocated GREEN/RX through-vias; nominal native geometry only'}
for ref in ['U15','R34','R35']:
 f=fps[ref];rs=regions[f['side']];own={k:unary_union([g for g,n in rows if n==ref or n.startswith(ref+'.')]) for k,rows in rs.items()}; foreign={k:[(g,n) for g,n in rows if n!=ref and not n.startswith(ref+'.')] for k,rows in rs.items()}
 row={'xy':f['xy'],'angle':f['angle'],'side':f['side'],'body_bbox':list(own['body'].bounds),'courtyard_bbox':list(own['courtyard'].bounds),'pad_count':sum(p['ref']==ref for p in pads),'paste_aperture_count':sum(n.startswith(ref+'.') for g,n in rs['paste']),'paste_outside_own_land_mm2':own['paste'].difference(own['land']).area,'paste_outside_own_mask_mm2':own['paste'].difference(own['mask']).area,'nearest_foreign_land_from_paste':nearest(own['paste'],foreign['land']),'nearest_foreign_paste':nearest(own['paste'],foreign['paste']),'nearest_foreign_mask':nearest(own['mask'],foreign['mask']),'nearest_same_side_body':nearest(own['body'],foreign['body']),'nearest_same_side_courtyard':nearest(own['courtyard'],foreign['courtyard']),'nearest_drill_to_paste':nearest(own['paste'],holes),'nearest_drill_to_land':nearest(own['land'],holes),'pad_pose_and_net':[{'number':p['number'],'xy':p['xy'],'net':p['net']} for p in pads if p['ref']==ref]}
 row['nominal_checks_passed']=row['paste_outside_own_land_mm2']<1e-10 and row['paste_outside_own_mask_mm2']<1e-10 and all(row[k][0]['distance_mm']>0 for k in ['nearest_foreign_land_from_paste','nearest_foreign_paste','nearest_foreign_mask','nearest_same_side_body','nearest_same_side_courtyard','nearest_drill_to_paste','nearest_drill_to_land'])
 res['moved_parts'][ref]=row
 if ref=='U15':
  # TI DQA0010B independently reviewed maximum body 2.6 x 1.1, at actual 90-degree pose.
  maxbody=box(27.7-1.3,21.9-.55,27.7+1.3,21.9+.55)
  row['TI_max_body_2p6_by_1p1_bbox']=list(maxbody.bounds);row['TI_max_body_inside_courtyard']=own['courtyard'].covers(maxbody);row['TI_max_body_nearest_same_side_Fab']=nearest(maxbody,foreign['body'])
for label,uid in [('RX','ec1b3878-61fc-5aff-9602-9d5133c60039'),('GREEN','c45deb1f-b195-55f5-9d25-74073f667227')]:
 v=objects[uid];drill=geom(v['drill']['outside']);disk=unary_union([geom(v['copper']['F.Cu']),drill]);row={k:v[k] for k in ['uuid','xy','width','net','tented','mask']};row['drill_mm']=v['drill']['width'];row['sides']={}
 for side,rs in regions.items():
  s={'nearest_disk_to_'+key:nearest(disk,rs[key]) for key in ['land','mask','paste']}
  s.update({'nearest_drill_to_'+key:nearest(drill,rs[key]) for key in ['land','mask','paste']})
  s['nominal_body_projections_crossed']=[{'ref':n,'body_bbox':list(g.bounds),'disk_overlap_mm2':disk.intersection(g).area,'drill_overlap_mm2':drill.intersection(g).area} for g,n in rs['body'] if disk.intersection(g).area>1e-10]
  s['courtyards_crossed']=[n for g,n in rs['courtyard'] if disk.intersection(g).area>1e-10]
  s['no_land_mask_paste_or_drill_overlap']=all(s[k][0]['distance_mm']>0 for k in s if k.startswith('nearest_'))
  row['sides'][side]=s
 row['tented_and_no_mask_opening']=all(v['tented'].values()) and not any(x.get('polygons') for x in v['mask'].values())
 res['vias'][label]=row
res['all_moved_component_nominal_checks_passed']=all(v['nominal_checks_passed'] for v in res['moved_parts'].values())
res['all_via_no_aperture_overlap_and_tented']=all(v['tented_and_no_mask_opening'] and all(s['no_land_mask_paste_or_drill_overlap'] for s in v['sides'].values()) for v in res['vias'].values())
res['peak_RSS_MiB']=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024
res['limits']=['Native exported finite-contour approximation, nominal geometry only; no fabrication/placement tolerance guarantee.','Fab outlines are library body representations, not universal exposed-metal maps or underside seating-height guarantees.','Paste-only pads use conservative rectangular bounds; native custom paste polygons are exact exported contours.','Ordinary tenting is not filled/capped/flat; factory process acceptance and first-article seating remain separate.','No native commands, refill, source edits, manufacturing exports or external actions.']
res['script_sha256']=sha(Path(__file__))
(OUT/'MOVED-ASSEMBLY-GEOMETRY.json').write_text(json.dumps(res,indent=2,sort_keys=True)+'\n')
print(json.dumps(res,indent=2))
