from geometry import *
o=json.loads(OUT.joinpath('finite-land-probes.json').read_text())
for v in o:
 for c in v['candidates']:
  holes=[]
  for d in items.values():
   if d['uuid']==v['via_uuid']:continue
   if d['kind']=='via':r=d['drill_mm']/2
   elif d['kind']=='pad' and d['drill_mm']:r=max(d['drill_mm'])/2
   else:continue
   g=math.dist(c['at'],d['at'])-.1-r
   if g<.25:holes.append(dict(uuid=d['uuid'],net=d['net'],ref=d.get('ref'),pin=d.get('pin'),hole_edge_gap_mm=g,approximation='exact round via; pad drill circumscribed if oval'))
  c['hole_spacing_obstructions']=holes
  x,y=c['at'];c['rectangular_edge_copper_gap_mm']=min(x-100,122.4-x,y-100,133.1-y)-.225
  c['edge_check_applicability']='All source via probes are away from rounded board corners. Straight-edge calculation applies.'
  c['land_clear_static']=c['land_clear_static'] and not holes and c['rectangular_edge_copper_gap_mm']>=.3
 v['candidates'].sort(key=lambda x:(not x['land_clear_static'],x['shift_mm']))
 print(v['pasted_pads'],'valid',[(c['at'],round(c['shift_mm'],3)) for c in v['candidates'] if c['land_clear_static']])
OUT.joinpath('finite-land-probes.json').write_text(json.dumps(o,indent=2))
