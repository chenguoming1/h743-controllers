from geometry import *
pads=[o for o in items.values() if o['kind']=='pad' and o['pad_type']=='smd' and any(l in o['all_native_layers'] for l in ['F.Paste','B.Paste'])]
vias=[o for o in items.values() if o['kind']=='via']
contacts=[]
for v in vias:
 for p in pads:
  ps,pr=shape(p)
  dist=bases_dist([v['at']],ps)-pr-v['drill_mm']/2
  if dist<=1e-9:
   cs=dict(via=v,pad=p,drill_gap_mm=dist)
   contacts.append(cs)
print('CONTACTS',len(contacts),'VIAS',len(set(c['via']['uuid'] for c in contacts)),'UNSUPPORTED',unsupported)
OUT.joinpath('static-contacts.json').write_text(json.dumps(contacts,indent=2))
for c in contacts:
 v,p=c['via'],c['pad']
 print(v['uuid'],v['at'],v['net'],'=>',p['ref']+'.'+p['pin'],p['value'],p['shape'],p['at'],p['size_mm'],'gap',c['drill_gap_mm'])
