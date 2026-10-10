import json,hashlib,pathlib,sys
import native_geometry as m
from shapely.affinity import translate
from shapely.geometry import Point,LineString
H=pathlib.Path(__file__).resolve().parent;D=H/'candidate01';sha=lambda p:hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest();r=json.load(open(H/'planned_adc_obstacles.json'));a=json.load(open(D/'f722-heli.native.json'));prov=json.load(open(D/'construction-provenance.json'));planned=[]
for o,c,ma,d in m.OBJECTS:
 if o.get('ref')=='R43':planned.append((o,{l:translate(g,0,.3)for l,g in c.items()},{l:translate(g,0,.3)for l,g in ma.items()},None))
for i,q in enumerate(r['ADC_BUS_vias_mm']):
 o={'uuid':'planned-ADC-via'+str(i),'net':'ADC_BUS','kind':'via'};planned.append((o,{l:Point(q).buffer(.225001,quad_segs=256)for l in a['copper_layers']},{},Point(q).buffer(.100001,quad_segs=256)))
for i,(x,y)in enumerate(zip(r['ADC_BUS_In3_points_mm'],r['ADC_BUS_In3_points_mm'][1:])):
 o={'uuid':'planned-ADC-trunk'+str(i),'net':'ADC_BUS','kind':'track'};planned.append((o,{'In3.Cu':LineString([x,y]).buffer(.063501,quad_segs=256)},{},None))
rows=[]
for o in prov['added_records']:
 c={l:m.geom(ps)for l,ps in o['copper'].items()};d=m.geom(o['drill']['outside'])if o.get('drill')else None
 for po,pc,pm,pd in planned:
  if o['net']!=po['net']:
   for l in c.keys()&pc.keys():rows.append({'new_uuid':o['uuid'],'new_net':o['net'],'planned':po.get('key',po['uuid']),'planned_net':po['net'],'category':'copper','layer':l,'gap_mm':c[l].distance(pc[l]),'required_mm':.127})
   if pd is not None and o['kind']=='track':
    for l,g in c.items():rows.append({'new_uuid':o['uuid'],'new_net':o['net'],'planned':po['uuid'],'category':'planned_drill_to_new_track','layer':l,'gap_mm':pd.distance(g),'required_mm':.20})
  if d is not None:
   for l,g in pm.items():rows.append({'new_uuid':o['uuid'],'planned':po.get('key',po['uuid']),'category':'new_drill_to_planned_R43_mask','layer':l,'gap_mm':d.distance(g),'required_mm':.20})
   if pd is not None:rows.append({'new_uuid':o['uuid'],'planned':po['uuid'],'category':'new_and_planned_drills','gap_mm':d.distance(pd),'required_mm':.25})
for row in rows:row['extra_mm']=row['gap_mm']-row['required_mm']
rows.sort(key=lambda r:r['extra_mm']);assert rows[0]['extra_mm']>=a['maximum_polygon_error_mm']
out={'schema':'f722-proposed-parallel-ADC-clearance/v1','passed':True,'board_sha256':sha(D/'f722-heli.kicad_pcb'),'native_sha256':sha(D/'f722-heli.native.json'),'source_board_sha256':m.EXPECTED,'planned_input_sha256':sha(H/'planned_adc_obstacles.json'),'script_sha256':sha(__file__),'checks':len(rows),'nearest':rows[:30],'source_unchanged':sha(m.BOARD)==m.EXPECTED,'scope':'Exact current SBUS transaction checked against the parallel worker-proposed R43 translation, two ADC_BUS vias and In3 trunk. Conservative1nm radial envelopes used for planned round copper. No final ADC board or C31 branch is claimed; final merged native/refill/source gates remain mandatory.'};(D/'parallel-ADC-planned-clearance.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'passed':True,'checks':len(rows),'minimum':rows[0]}))
