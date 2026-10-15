from geometry import *
contacts=json.loads(OUT.joinpath('static-contacts.json').read_text())
pads=[o for o in items.values() if o['kind']=='pad' and o['pad_type']=='smd' and any(l in o['all_native_layers'] for l in ['F.Paste','B.Paste'])]
viaids=list(dict.fromkeys(c['via']['uuid'] for c in contacts));out=[]
# Eight finite cardinal/corner probes per source via: no routing solver/grid search.
# 0.325 mm source-pad edge to via centre = 0.225 mm land radius + exploratory 0.100 mm copper gap.
for uid in viaids:
 v=items[uid];cps=[c['pad'] for c in contacts if c['via']['uuid']==uid]
 boxes=[]
 for p in cps:
  pts,r=shape(p);boxes.append([min(t[0] for t in pts)-r,min(t[1] for t in pts)-r,max(t[0] for t in pts)+r,max(t[1] for t in pts)+r])
 xmin=min(x[0] for x in boxes)-.325;ymin=min(x[1] for x in boxes)-.325;xmax=max(x[2] for x in boxes)+.325;ymax=max(x[3] for x in boxes)+.325;x,y=v['at']
 points=[[xmin,y],[xmax,y],[x,ymin],[x,ymax],[xmin,ymin],[xmin,ymax],[xmax,ymin],[xmax,ymax]]
 cs=[]
 for i,p in enumerate(points):
  q=dict(v,at=[round(z,6) for z in p],uuid=uid+f'-probe{i}')
  near=[]
  for o in items.values():
   if o['uuid']==uid or o['net']==q['net']:continue
   g=gap(q,o)
   if g<.127002:near.append(dict(uuid=o['uuid'],kind=o['kind'],net=o['net'],ref=o.get('ref'),pin=o.get('pin'),layers=o['layers'],copper_gap_mm=g))
  pastes=[]
  for o in pads:
   g=bases_dist([q['at']],shape(o)[0])-shape(o)[1]-q['drill_mm']/2
   if g<=1e-9:pastes.append(dict(uuid=o['uuid'],ref=o['ref'],pin=o['pin'],net=o['net'],layers=o['layers'],drill_gap_mm=g))
  same=[dict(uuid=o['uuid'],kind=o['kind'],ref=o.get('ref'),pin=o.get('pin'),layers=o['layers']) for o in items.values() if o['uuid']!=uid and o['net']==v['net'] and gap(q,o)<=1e-9]
  cs.append(dict(at=q['at'],shift_mm=math.dist(v['at'],q['at']),fixed_different_net_obstructions=sorted(near,key=lambda x:x['copper_gap_mm']),pasted_drill_contacts=pastes,retained_same_net_contacts=same,land_clear_static=not near and not pastes))
 out.append(dict(via_uuid=uid,net=v['net'],source_at=v['at'],pasted_pads=[p['ref']+'.'+p['pin'] for p in cps],candidates=sorted(cs,key=lambda x:(not x['land_clear_static'],x['shift_mm']))))
OUT.joinpath('finite-land-probes.json').write_text(json.dumps(out,indent=2))
for o in out:
 print('\n',o['via_uuid'],o['net'],o['pasted_pads'])
 for c in o['candidates'][:3]:print(c['at'],'shift',round(c['shift_mm'],3),'clear',c['land_clear_static'],'obs',[(x['ref'] or x['uuid'][:8],x['net'],round(x['copper_gap_mm'],3)) for x in c['fixed_different_net_obstructions'][:4]],'paste',[(x['ref'],x['pin']) for x in c['pasted_drill_contacts']])
