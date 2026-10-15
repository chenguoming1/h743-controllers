from candidate_check import *

def gap(a,b):
 if a['kind']==b['kind']=='segment':
  if a['layer']!=b['layer']:return math.inf
  return sc.seg_seg(a['start'],a['end'],b['start'],b['end'])-(a['width']+b['width'])/2
 if a['kind']==b['kind']=='via':return math.dist(a['at'],b['at'])-(a['diameter']+b['diameter'])/2
 if b['kind']=='pad':
  if a['kind']=='segment':
   if a['layer'] not in b['layers'] and '*.Cu' not in b['layers']:return math.inf
   return sc.seg_pad(a['start'],a['end'],b)-a['width']/2
  return sc.seg_pad(a['at'],a['at'],b)-a['diameter']/2
 v,t=(a,b) if a['kind']=='via' else (b,a)
 return sc.point_seg(v['at'],t['start'],t['end'])[0]-(v['diameter']+t['width'])/2
reports=[]
for net in ['SWDIO','IMU_CS']:
 old=[o for o in tracks+vias if o['uuid'] in removed and o['net']==net]
 newnet=[o for o in new if o['net']==net]
 retained=[o for o in tracks+vias+pads if o['net']==net and o.get('uuid') not in removed]
 oldcontacts=[];newcontacts=[]
 for r in retained:
  oldg=min(gap(o,r) for o in old);newg=min(gap(o,r) for o in newnet)
  if oldg<=1e-8:oldcontacts.append(dict(retained=r,gap_mm=oldg))
  if newg<=1e-8:newcontacts.append(dict(retained=r,gap_mm=newg))
 oldids={o['retained']['uuid'] for o in oldcontacts};newids={o['retained']['uuid'] for o in newcontacts}
 # Verify all replacement shapes form one physical copper-connected component.
 adj={i:set() for i in range(len(newnet))}
 for i,a in enumerate(newnet):
  for j,b in enumerate(newnet[:i]):
   if gap(a,b)<=1e-8:adj[i].add(j);adj[j].add(i)
 seen={0};todo=[0]
 while todo:
  k=todo.pop()
  for j in adj[k]-seen:seen.add(j);todo.append(j)
 reports.append(dict(net=net,original_retained_contacts=oldcontacts,replacement_retained_contacts=newcontacts,lost_contacts=sorted(oldids-newids),added_contacts=sorted(newids-oldids),all_replacement_objects_one_component=len(seen)==len(newnet)))
paste=[]
for v in new:
 if v['kind']!='via':continue
 nearest=[]
 for p in pads:
  if not any(l.endswith('.Paste') for l in p['layers']):continue
  d=sc.seg_pad(v['at'],v['at'],p)
  nearest.append(dict(ref=p['ref'],pin=p['pin'],net=p['net'],uuid=p['uuid'],paste_layers=[l for l in p['layers'] if l.endswith('.Paste')],annulus_to_nominal_paste_gap_mm=d-v['diameter']/2,drill_to_nominal_paste_gap_mm=d-v['drill']/2))
 nearest.sort(key=lambda r:r['annulus_to_nominal_paste_gap_mm'])
 paste.append(dict(via=v,nearest_nominal_paste_apertures=nearest[:3],annulus_overlaps_nominal_paste=any(r['annulus_to_nominal_paste_gap_mm']<0 for r in nearest),drill_overlaps_nominal_paste=any(r['drill_to_nominal_paste_gap_mm']<0 for r in nearest)))
out=dict(donor_contacts=reports,paste_screen=paste,limitations='Nominal pad geometry with conservative rectangular bounds for roundrects; not fabrication Gerber/stencil validation. Zone refill and mask/tenting are not modeled.')
(D/'mcu'/'donor-and-paste-summary.json').write_text(json.dumps(out,indent=2)+'\n')
for r in reports: print(r['net'],'old contacts',[(x['retained']['uuid'],x['retained']['kind']) for x in r['original_retained_contacts']],'lost',r['lost_contacts'],'added',r['added_contacts'],'connected',r['all_replacement_objects_one_component'])
for p in paste:print(p['via']['net'],p['nearest_nominal_paste_apertures'][0])
