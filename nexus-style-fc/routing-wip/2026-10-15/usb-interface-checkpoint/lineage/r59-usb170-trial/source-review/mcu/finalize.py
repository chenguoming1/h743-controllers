from candidate_check import *
from pathlib import Path
import hashlib
clear=[]
for j,o in enumerate(new):
 if o['kind']=='segment': layers=[o['layer']];a=o['start'];b=o['end'];w=o['width']
 else:layers=ls;a=b=o['at'];w=o['diameter']
 for l in layers:
  for t in tracks:
   if t['net'] in ['USB_DM','USB_DP',o['net']] or t['uuid'] in removed or t['layer']!=l:continue
   clear.append(dict(candidate_index=j,layer=l,gap_mm=sc.seg_seg(a,b,t['start'],t['end'])-(w+t['width'])/2,kind='track',net=t['net'],uuid=t['uuid'],required_mm=.127))
  for v in vias:
   if v['net'] in ['USB_DM','USB_DP',o['net']] or v['uuid'] in removed:continue
   clear.append(dict(candidate_index=j,layer=l,gap_mm=sc.point_seg(v['at'],a,b)[0]-(w+v['diameter'])/2,kind='via',net=v['net'],uuid=v['uuid'],required_mm=.127))
  for p in pads:
   if (l not in p['layers'] and '*.Cu' not in p['layers']) or p['net']==o['net']:continue
   clear.append(dict(candidate_index=j,layer=l,gap_mm=sc.seg_pad(a,b,p)-w/2,kind='pad',net=p['net'],uuid=p['uuid'],ref=p['ref'],pin=p['pin'],required_mm=.2 if p['type']=='np_thru_hole' else .127))
mutual=[]
for i,a in enumerate(new):
 for j,b in enumerate(new[:i]):
  if a['net']==b['net']:continue
  if a['kind']==b['kind']=='segment':
   if a['layer']!=b['layer']:continue
   gap=sc.seg_seg(a['start'],a['end'],b['start'],b['end'])-(a['width']+b['width'])/2
  elif a['kind']==b['kind']=='via':gap=math.dist(a['at'],b['at'])-(a['diameter']+b['diameter'])/2
  else:
   v,t=(a,b) if a['kind']=='via' else (b,a)
   gap=sc.point_seg(v['at'],t['start'],t['end'])[0]-(v['diameter']+t['width'])/2
  mutual.append(dict(candidate_indices=[i,j],nets=[a['net'],b['net']],gap_mm=gap,required_mm=.127))
clear.sort(key=lambda q:q['gap_mm']-q['required_mm']);mutual.sort(key=lambda q:q['gap_mm'])
lengths={n:{l:sum(math.dist(o['start'],o['end']) for o in new if o['kind']=='segment' and o['net']==n and o['layer']==l) for l in ['B.Cu','In3.Cu']} for n in ['USB_DM','USB_DP']}
summary=dict(source_sha256_before=H,source_sha256_after=hashlib.sha256(S.read_bytes()).hexdigest(),failures=check(),new_object_count=len(new),removed_foreign_object_count=len(removed),minimum_fixed=clear[:20],minimum_new_mutual=mutual[:20],usb_length_mm=lengths)
(D/'mcu'/'clearance-summary.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps(summary,indent=2))
