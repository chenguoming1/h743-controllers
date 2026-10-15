from geometry import *
contacts=json.loads(OUT.joinpath('static-contacts.json').read_text())
vids=list(dict.fromkeys(c['via']['uuid'] for c in contacts))
allitems=list(items.values())
# Existing source copper contacts only. Dynamic zone fills are separately listed.
for uid in vids:
 v=items[uid]; print('\nVIA',uid,v['at'],v['net'])
 for o in allitems:
  if o['uuid']==uid or o['net']!=v['net'] or not set(o['layers'])&set(v['layers']):continue
  if gap(v,o)<=1e-9:print('CONTACT',json.dumps(o))
 print('ZONE LAYERS',[(z['layer'],[p['index'] for p in z['fill_polygons'] if contains(v['at'],p['points'])]) for z in zones if z['net']==v['net'] and any(contains(v['at'],p['points']) for p in z['fill_polygons'])])
