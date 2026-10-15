"""Read-only single C29 placement decision. No board changes or native/solver jobs."""
import sys,copy
sys.path.insert(0,'/workspace/shared/nexus-usb-stack-review/r55-donors')
from static_clearance import *
D=Path('/workspace/shared/nexus-usb-stack-review/r55-c29-option')
DX=-.211;W=.155;G=.127;E=2*W+G;CX=111.8345
rr={val(p,'uuid'):float(val(p,'roundrect_rratio',0)) for f in allc(b,'footprint') for p in allc(f,'pad')}
def rectdist(a,b,sx,sy):
 if any(abs(q[0])<=sx/2 and abs(q[1])<=sy/2 for q in [a,b]):return 0.
 cs=[(-sx/2,-sy/2),(sx/2,-sy/2),(sx/2,sy/2),(-sx/2,sy/2)]
 return min(seg_seg(a,b,c,d) for c,d in zip(cs,cs[1:]+cs[:1]))
def realpad(a,b,p):
 if p['shape']!='roundrect':return seg_pad(a,b,p)
 r=min(p['size'])*rr[p['uuid']];a=local(a,p);b=local(b,p)
 return rectdist(a,b,p['size'][0]-2*r,p['size'][1]-2*r)-r
oldpads=[p for p in pads if p['ref']=='C29'];newpads=copy.deepcopy(oldpads)
for p in newpads:p['at'][0]+=DX
replacements=[]
for uid in ['0a13d11c-c17a-4c7f-add1-b8eb553c3895','2364fc18-712a-4a3d-bd33-5ddd77aba84b']:
 old=next(t for t in tracks if t['uuid']==uid);new=copy.deepcopy(old)
 for end in ['start','end']:
  for p in oldpads:
   if new[end]==p['at']:new[end][0]+=DX
 new['length_mm']=math.dist(new['start'],new['end'])
 replacements.append(dict(original=old,proposed=new,length_delta_mm=new['length_mm']-old['length_mm']))
rt={x['original']['uuid']:x['proposed'] for x in replacements};rp={p['uuid']:p for p in newpads}
nt=[rt.get(t['uuid'],t) for t in tracks];npads=[rp.get(p['uuid'],p) for p in pads]
def screen(s):
 out=[];a=s['start'];b=s['end'];w=s['width'];net=s['net'];layer=s['layer']
 for t in nt:
  if t['net']==net or t['layer']!=layer or t['net'] in ['USB_DP','USB_DM']:continue
  gap=seg_seg(a,b,t['start'],t['end'])-(w+t['width'])/2
  if gap<.127-1e-9:out.append(dict(gap_mm=gap,item=t))
 for v in vias:
  if v['net']==net or v['net'] in ['USB_DP','USB_DM']:continue
  gap=point_seg(v['at'],a,b)[0]-(w+v['diameter'])/2
  if gap<.127-1e-9:out.append(dict(gap_mm=gap,item=v))
 for p in npads:
  if p['net']==net or not(layer in p['layers'] or '*.Cu' in p['layers']):continue
  gap=realpad(a,b,p)-w/2
  if gap<(.2 if p['type']=='np_thru_hole' else .127)-1e-9:out.append(dict(gap_mm=gap,item=p))
 return out
for r in replacements:r['retained_foreign_obstructions']=screen(r['proposed'])
rails=[dict(kind='segment',net=net,layer='F.Cu',start=[CX+offset,120.7],end=[CX+offset,123.0],width=W) for net,offset in [('USB_DP',-(W+G)/2),('USB_DM',(W+G)/2)]]
for r in rails:r['obstructions']=screen(r)
env=dict(kind='segment',net='PAIR_ENVELOPE',layer='F.Cu',start=[CX,120.7],end=[CX,123.0],width=E);env['obstructions']=screen(env)
# Generic direct-copper graph, same-net objects only. No plane-fill or pad-pad links.
def layers(o):return set(ls if o['kind']=='via' or '*.Cu' in o.get('layers',[]) else [o['layer']] if o['kind']=='segment' else [x for x in o['layers'] if x.endswith('.Cu')])
def contact(a,b):
 if not layers(a)&layers(b):return False
 ka=a['kind'];kb=b['kind']
 if ka=='pad' and kb=='pad':return False
 if ka=='segment' and kb=='segment':return seg_seg(a['start'],a['end'],b['start'],b['end'])<=(a['width']+b['width'])/2+1e-8
 if ka=='via' and kb=='via':return math.dist(a['at'],b['at'])<=(a['diameter']+b['diameter'])/2+1e-8
 if ka=='via' and kb=='segment':return point_seg(a['at'],b['start'],b['end'])[0]<=(a['diameter']+b['width'])/2+1e-8
 if ka=='segment' and kb=='via':return contact(b,a)
 if ka=='pad' and kb=='segment':return realpad(b['start'],b['end'],a)<=b['width']/2+1e-8
 if ka=='segment' and kb=='pad':return contact(b,a)
 if ka=='pad' and kb=='via':return realpad(b['at'],b['at'],a)<=b['diameter']/2+1e-8
 if ka=='via' and kb=='pad':return contact(b,a)
 return False
def component(items,start):
 seen={start};todo=[start]
 while todo:
  a=todo.pop()
  for j in range(len(items)):
   if j not in seen and contact(items[a],items[j]):seen.add(j);todo.append(j)
 return [items[j] for j in sorted(seen)]
connections={}
for net,pin in [('VX_SENSE','1'),('GND','2')]:
 orig=[x for x in tracks+vias+pads if x['net']==net];proposed=[x for x in nt+vias+npads if x['net']==net]
 oi=next(i for i,x in enumerate(orig) if x['kind']=='pad' and x['ref']=='C29' and x['pin']==pin);ni=next(i for i,x in enumerate(proposed) if x['kind']=='pad' and x['ref']=='C29' and x['pin']==pin)
 oc=component(orig,oi);nc=component(proposed,ni)
 connections[net]=dict(original_object_count=len(oc),proposed_object_count=len(nc),lost_original_uuids=sorted(set(x['uuid'] for x in oc)-set(x['uuid'] for x in nc)),original_pads=[x for x in oc if x['kind']=='pad'],proposed_pads=[x for x in nc if x['kind']=='pad'])
obj=dict(status='REJECTED_SINGLE_C29_DECISION_OPTION_NOT_APPROVAL_REQUEST',source_path=str(S),source_sha256=H,footprint_uuid='bb21fc42-376b-471b-9b7d-0455d4f59443',old_center_mm=[111.39,121.55],new_center_mm=[111.179,121.55],offset_mm=[DX,0],old_and_new_rotation_deg=90,original_pads=oldpads,proposed_pads=newpads,required_port_reterminations=replacements,pair_primitive_scope='Illustrative local slot only; north and south connector/U7/trunk launches remain unclosed. Do not apply these lanes.',pair_rails=rails,conservative_pair_envelope=env,finite_contact_graph=connections,stopping_test=dict(required_C29_J5_gap_mm=.691,after_move_gap_mm=.691,required_pad_via_clearance_mm=.127,actual_C29_1_to_retained_GND_via_mm=.053142,deficit_mm=.073858,max_clearance_preserving_west_shift_mm=.137142,corridor_gap_at_max_shift_mm=.617142,result='Fail: single minimum west move cannot clear both fixed via and pair slot.'),ADC_role=dict(capacitor_nF=100,R16_ohm=52300,R17_ohm=10000,example_VX_V=7.4,example_current_mA=7.4/62300*1000,ports=['R16.2','R17.1','C29.1','U1.9'],values_and_net_assignment_unchanged=True),limits=['Decision proposal only: no component movement authorized or applied.','No native DRC, refill, SI, or assembly qualification.','The two finite reterminations preserve same-net contacts but fail the reported foreign-copper/USB tests.','All fixed connectors, vias, power copper and other parts remain. No pasted-hole dependency is added.','Current source bound is r55; later boards need applicability recheck.','Frozen donor and reservation-refinement reports are unchanged.'])
assert all(not x['lost_original_uuids'] for x in connections.values())
assert hashlib.sha256(S.read_bytes()).hexdigest()==H
(D/'c29-option.json').write_text(json.dumps(obj,indent=2)+'\n')
for net,x in connections.items():print(net,x['original_object_count'],x['proposed_object_count'],[(p['ref'],p['pin']) for p in x['proposed_pads']])
for r in replacements:print('terminal',r['original']['uuid'],r['length_delta_mm'],[(x['item']['net'],x['item'].get('ref',''),x['item']['uuid'][:8],x['gap_mm']) for x in r['retained_foreign_obstructions']])
for r in rails:print('pair',r['net'],[(x['item']['net'],x['item'].get('ref',''),x['item']['uuid'][:8],x['gap_mm']) for x in r['obstructions']])
