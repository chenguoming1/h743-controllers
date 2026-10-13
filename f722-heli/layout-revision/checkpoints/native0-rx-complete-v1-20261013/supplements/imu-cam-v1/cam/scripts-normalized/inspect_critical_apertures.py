"""Bounded inspection of the observed KiCad 10.0.6 Gerber subset, not general CAM certification."""
import collections,fcntl,gzip,hashlib,json,math,os,re,resource,sys,time
from pathlib import Path
os.environ['OPENBLAS_NUM_THREADS']='1';sys.dont_write_bytecode=True
resource.setrlimit(resource.RLIMIT_AS,(1024*1024**2,)*2);resource.setrlimit(resource.RLIMIT_CPU,(90,95))
ROOT=Path('@RUNTIME@');lock=(ROOT/'shared-replay.lock').open('rb');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
sys.path.insert(0,str(ROOT/'python-deps'))
from shapely.geometry import Polygon,Point,LineString,box
from shapely.ops import unary_union
from shapely.affinity import rotate,translate,scale
from PIL import Image,ImageDraw
P=Path('@CAM@');D=Path('@NATIVE_INPUTS@');OUT=Path(__file__).resolve().parent
start=time.monotonic()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def geom(ps):return unary_union([Polygon(p['outer'],p.get('holes',[])) for p in ps])
def gerberframe(g):return scale(g,xfact=1,yfact=-1,origin=(0,0))
data=json.load(gzip.open(D/'after.native.json.gz','rt'));assert data['board_sha256']=='84229c571433bd72d410fb18d02cffa3a380c00a87fbe1270e3a73b63f8dd6cd';pads=[o for o in data['objects'] if o['kind']=='pad'];fps={f['ref']:f for f in data['footprints']}

def parse(path):
 text=path.read_text();assert '%FSLAX46Y46*%' in text and '%MOMM*%' in text
 assert not re.search(r'^G0[23]',text,re.M),'Arcs outside bounded parser scope'
 macros={};ap={};flashes=[];regions=[];strokes=[];selected=None;xy=(0.,0.);attr=None;ring=None;polarity='dark'
 for token in re.findall(r'%[^%]*%|[^%*]+\*',text,re.S):
  token=token.strip()
  if token.startswith('%AM'):
   name,body=token[3:-1].split('*',1);macros[name]=body;continue
  if token.startswith('%ADD'):
   m=re.fullmatch(r'%ADD(\d+)([^,*]+)(?:,([^*]*))?\*%',token);assert m,token
   code=int(m[1]);kind=m[2];v=[float(x) for x in (m[3] or '').split('X') if x]
   if kind=='C':g=Point(0,0).buffer(v[0]/2,quad_segs=256)
   elif kind=='R':g=box(-v[0]/2,-v[1]/2,v[0]/2,v[1]/2)
   elif kind=='O':
    w,h=v;r=min(w,h)/2;g=LineString([(-(w-h)/2,0),((w-h)/2,0)]).buffer(r,quad_segs=256) if w>h else LineString([(0,-(h-w)/2),(0,(h-w)/2)]).buffer(r,quad_segs=256) if h>w else Point(0,0).buffer(r,quad_segs=256)
   elif kind=='RoundRect':
    assert len(v)==10;g=Polygon(list(zip(v[1:9:2],v[2:9:2]))).buffer(v[0],quad_segs=256);g=rotate(g,v[9],origin=(0,0))
   elif kind.startswith('FreePoly'):
    primitive=[x.strip() for x in macros[kind].split('*') if x.strip() and not x.strip().startswith('0 ')];assert len(primitive)==1
    fields=[x.strip() for x in primitive[0].split(',')];assert fields[0:2]==['4','1'];n=int(fields[2]);numbers=[float(x) for x in fields[3:-1]];assert len(numbers)==2*(n+1)
    angle=v[int(fields[-1][1:])-1] if fields[-1].startswith('$') else float(fields[-1]);g=rotate(Polygon(list(zip(numbers[::2],numbers[1::2]))),angle,origin=(0,0))
   else:raise AssertionError('Unsupported aperture '+kind)
   assert g.is_valid,(kind,code);ap[code]=g;continue
  if token.startswith('%TO.P,'):attr=tuple(token[len('%TO.P,'):].removesuffix('*%').split(',')[:2]);continue
  if token.startswith('%TD'):attr=None;continue
  if token.startswith('%LPC'):raise AssertionError('Clear polarity outside bounded parser scope')
  if token.startswith('%') or token.startswith('G04'):continue
  if token=='G36*':assert ring is None;ring=[];continue
  if token=='G37*':assert ring and len(ring)>2;regions.append(Polygon(ring));ring=None;continue
  m=re.fullmatch(r'D(\d+)\*',token)
  if m:selected=int(m[1]);continue
  m=re.fullmatch(r'(?:X(-?\d+))?(?:Y(-?\d+))?D0([123])\*',token)
  if m:
   new=(int(m[1])/1e6 if m[1] else xy[0],int(m[2])/1e6 if m[2] else xy[1]);op=int(m[3])
   if ring is not None:
    if op in [1,2]:ring.append(new)
    else:raise AssertionError('Region flash unsupported')
   elif op==3:flashes.append({'g':translate(ap[selected],*new),'xy':new,'attr':attr,'aperture':selected})
   elif op==1:strokes.append((xy,new,selected))
   xy=new
 return {'flashes':flashes,'regions':regions,'strokes':strokes,'apertures':ap,'sha256':sha(path),'file_function':re.search(r'%TF.FileFunction,([^*]+)',text)[1],'file_polarity':re.search(r'%TF.FilePolarity,([^*]+)',text)[1]}

layers={key:parse(P/'gerbers'/f'f722-heli-{key.replace(".","_")}.{ext}') for key,ext in [('F.Cu','gtl'),('B.Cu','gbl'),('F.Mask','gts'),('B.Mask','gbs'),('F.Paste','gtp'),('B.Paste','gbp')]}
# Native contour approximation plus 1-micrometre-coordinate-digit Gerber precision
# are bounded separately; this numerical shape bound is 0.00003 mm, not a fab tolerance.
bound=.00003;tests=[]
for p in pads:
 if p['ref'] not in {'J1','U15','R34','R35'}:continue
 for layer,polys in [(k,v) for k,v in p['copper'].items() if k in ['F.Cu','B.Cu']]+[(k,v['polygons']) for k,v in p['mask'].items() if k in ['F.Mask','B.Mask']]:
  native=gerberframe(geom(polys));eligible=[f for f in layers[layer]['flashes'] if not layer.endswith('.Cu') or f['attr']==(p['ref'],p['number'])]
  if native.is_empty:continue
  assert eligible,(p['ref'],p['number'],layer)
  match=min(eligible,key=lambda f:f['g'].hausdorff_distance(native));dist=match['g'].hausdorff_distance(native)
  tests.append({'ref':p['ref'],'pad':p['number'],'layer':layer,'native_to_actual_aperture_Hausdorff_mm':dist,'symmetric_difference_mm2':match['g'].symmetric_difference(native).area,'matched_aperture':match['aperture'],'matched_flash_xy':match['xy'],'passed':dist<=bound})
 for layer in ['F.Paste','B.Paste']:
  if layer not in p['all_layers']:continue
  side=layer.replace('.Paste','.Cu');native=gerberframe(geom(p['copper'].get(side,[])))
  if native.is_empty:continue
  match=min(layers[layer]['flashes'],key=lambda f:f['g'].hausdorff_distance(native));dist=match['g'].hausdorff_distance(native);tests.append({'ref':p['ref'],'pad':p['number'],'layer':layer,'native_to_actual_aperture_Hausdorff_mm':dist,'symmetric_difference_mm2':match['g'].symmetric_difference(native).area,'matched_aperture':match['aperture'],'matched_flash_xy':match['xy'],'passed':dist<=bound})
custom=[]
for graphic in fps['U15']['graphics']:
 if graphic['layer']!='B.Paste' or 'polygons' not in graphic:continue
 native=gerberframe(geom(graphic['polygons']));actual=min(layers['B.Paste']['regions'],key=lambda g:g.hausdorff_distance(native));dist=actual.hausdorff_distance(native);custom.append({'graphic_uuid':graphic['uuid'],'native_to_actual_region_Hausdorff_mm':dist,'symmetric_difference_mm2':actual.symmetric_difference(native).area,'passed':dist<=bound})
assert len(custom)==2
# Actual plotted pin-1 or A/K centers support source orientation, not factory library corrections.
orientation=[]
for p in pads:
 if not re.match(r'^(U|D|Q|J|Y)\d+$',p['ref']) or p['number'] not in ['1','A','K']:continue
 side=fps[p['ref']]['side'];eligible=[f for f in layers[side]['flashes'] if f['attr']==(p['ref'],p['number'])]
 if not eligible:continue
 target=gerberframe(geom(p['copper'].get(side,[])))
 if target.is_empty:continue
 f=min(eligible,key=lambda f:f['g'].hausdorff_distance(target));dist=f['g'].hausdorff_distance(target);orientation.append({'ref':p['ref'],'pin':p['number'],'layer':side,'plotted_xy':f['xy'],'shape_match':dist<=bound})
via_results={}
for label,uid in [('RX','ec1b3878-61fc-5aff-9602-9d5133c60039'),('GREEN','c45deb1f-b195-55f5-9d25-74073f667227')]:
 v=next(o for o in data['objects'] if o['uuid']==uid);center=(v['xy'][0],-v['xy'][1]);disk=Point(center).buffer(v['width']/2,quad_segs=256);drill=Point(center).buffer(v['drill']['width']/2,quad_segs=256);row={'xy_native':v['xy'],'native_tented':v['tented'],'native_mask_opening_map':v['mask'],'actual_opening_clearances':{}}
 for layer in ['F.Mask','B.Mask','F.Paste','B.Paste']:
  actual=unary_union([f['g'] for f in layers[layer]['flashes']]+layers[layer]['regions']);row['actual_opening_clearances'][layer]={'disk_gap_mm':disk.distance(actual),'drill_gap_mm':drill.distance(actual),'overlap_mm2':disk.intersection(actual).area}
 via_results[label]=row
# Actual outline endpoint census from Gerber 4.6 geometry.
edge=(P/'gerbers/f722-heli-Edge_Cuts.gm1').read_text();xy=(0.,0.);segments=[]
for line in edge.splitlines():
 m=re.fullmatch(r'(?:X(-?\d+))?(?:Y(-?\d+))?D0([12])\*',line)
 if m:
  new=(int(m[1])/1e6 if m[1] else xy[0],int(m[2])/1e6 if m[2] else xy[1])
  if m[3]=='1':segments.append((xy,new))
  xy=new
want=[((0.,0.),(41.66,0.)),((41.66,0.),(41.66,-25.4)),((41.66,-25.4),(0.,-25.4)),((0.,-25.4),(0.,0.))]
key=lambda s:tuple(sorted(s));assert collections.Counter(map(key,segments))==collections.Counter(map(key,want))
res={'schema':'f722-internal-critical-aperture-review/v1','source_pcb_sha256':data['board_sha256'],'finalrelease':False,'method':'Bounded parser for only actual observed KiCad C/R/O/RoundRect/FreePoly flashes and linear G36 regions; unsupported primitives rejected. Exact source native contours compared after Y inversion.','numerical_shape_bound_mm':bound,'native_maximum_polygon_error_mm':data['maximum_polygon_error_mm'],'aperture_comparisons':tests,'U15_custom_paste_regions':custom,'source_pin1_A_K_orientation_checks':orientation,'vias':via_results,'actual_outline_segments':segments,'actual_outline_exact_41p660_by_25p400':True,'gerber_layer_provenance':{k:{x:v[x] for x in ['sha256','file_function','file_polarity']} for k,v in layers.items()},'all_selected_apertures_match':all(t['passed'] for t in tests+custom),'source_orientation_shapes_match':all(t['shape_match'] for t in orientation),'all_selected_via_mask_paste_gaps_positive':all(x['disk_gap_mm']>0 and x['drill_gap_mm']>0 and x['overlap_mm2']==0 for v in via_results.values() for x in v['actual_opening_clearances'].values()),'peak_RSS_MiB':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024,'elapsed_seconds':time.monotonic()-start,'limits':['Internal targeted actual-aperture review, not independent whole-board CAM certification.','Gerber mask negative file polarity represents openings; dark plotted shapes are reviewed as mask openings.','Buffer tessellation is only a numerical contour comparison/render aid, not manufactured tolerance.','Supplier part-model pin-1/rotation/pickup, stack/tenting/slot acceptance and first article remain pending.']}
(OUT/'CRITICAL-APERTURE-REVIEW.json').write_text(json.dumps(res,indent=2,sort_keys=True)+'\n')
# Direct rendering of parsed actual Gerber aperture shapes; no native SVG substituted.
j1=unary_union([gerberframe(geom(p['copper'].get('F.Cu',[]))) for p in pads if p['ref']=='J1']);x1,y1,x2,y2=j1.bounds
views=[('USB J1 - actual FRONT Gerber apertures','F',(x1-.5,y1-.5,x2+.5,y2+.5)),('U15 / R34 / R35 - actual BACK apertures','B',(25.8,-24.6,30.35,-18.8)),('RX / GREEN - actual BACK apertures','B',(30.5,-24.1,37.6,-21.3)),('RX / GREEN - actual FRONT apertures','F',(30.5,-24.1,37.6,-21.3))]
W,H=1000,620;im=Image.new('RGB',(W*2,H*2),'white');draw=ImageDraw.Draw(im)
for idx,(title,side,bounds) in enumerate(views):
 col,row=idx%2,idx//2;ox,oy=col*W,row*H;draw.text((ox+20,oy+12),title,fill='black');draw.text((ox+20,oy+30),'Actual apertures: copper gray, mask blue, paste orange, drill black. PCB top-view coordinates.',fill='black');loX,loY,hiX,hiY=bounds;s=min((W-50)/(hiX-loX),(H-90)/(hiY-loY));cx=ox+25;cy=oy+65;clip=box(*bounds)
 def pts(r):return [(cx+(x-loX)*s,cy+(hiY-y)*s) for x,y in r.coords]
 def paint(g,color):
  g=g.intersection(clip)
  for poly in (g.geoms if hasattr(g,'geoms') else [g]):
   if poly.geom_type!='Polygon':continue
   draw.polygon(pts(poly.exterior),fill=color)
   for hole in poly.interiors:draw.polygon(pts(hole),fill='white')
 for suffix,color in [('.Cu','#bdbdbd'),('.Mask','#75b8e5'),('.Paste','#e88a32')]:
  layer=layers[side+suffix]
  for f in layer['flashes']:
   if f['g'].intersects(clip):paint(f['g'],color)
  for g in layer['regions']:
   if g.intersects(clip):paint(g,color)
 for o in data['objects']:
  if not o.get('drill'):continue
  g=gerberframe(geom(o['drill']['outside']))
  if g.intersects(clip):paint(g,'#222222')
 for ref in ['J1','U15','R34','R35','U3']:
  f=fps[ref];x,y=f['xy'][0],-f['xy'][1]
  if loX<x<hiX and loY<y<hiY:draw.text((cx+(x-loX)*s,cy+(hiY-y)*s),ref,fill='#900050')
im.save(OUT/'actual-Gerber-critical-apertures.png')
print(json.dumps({k:res[k] for k in ['all_selected_apertures_match','source_orientation_shapes_match','all_selected_via_mask_paste_gaps_positive','peak_RSS_MiB','elapsed_seconds']}));print('checks',len(tests),'orientation',len(orientation),'failed',[t for t in tests if not t['passed']])
