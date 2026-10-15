import sys,json,math
sys.path.insert(0,'/workspace/shared/nexus-usb-stack-review/r57-inner-pair')
import static_clearance as sc
from source_context import *
# Bounded, explicitly chosen manual polylines only. No search or route optimizer.
def path(net,layer,pts,w=.15):return [dict(kind='segment',net=net,layer=layer,start=list(a),end=list(b),width=w) for a,b in zip(pts,pts[1:])]
def via(net,at):return dict(kind='via',net=net,at=list(at),diameter=.45,drill=.2,layers=['F.Cu','B.Cu'])
removed=[t['uuid'] for t in tracks if t['net']=='SWDIO' and t['layer']=='B.Cu']+[v['uuid'] for v in vias if v['net']=='SWDIO' and v['at']==[114.251387,108.48676]]
removed+=['f4f94bae-80da-4eb4-bca1-2a090557d795','91546caa-2776-4d18-a585-2372a009501f']
new=[]
new+=path('USB_DM','B.Cu',[(115.35,106.15),(115.321716,107.057591),(115.28,107.105),(114.66,107.105),(112.664254,109.179537),(112.060074,109.703910),(111.55,109.703910),(111.38,109.68),(110.98,109.68)])
new+=path('USB_DP','B.Cu',[(115.85,106.15),(115.85,107.067),(115.57,107.50),(114.67,107.50),(112.846878,109.389955),(112.242698,109.914328),(111.8,110.34),(110.972,110.34)])
new+=[via('USB_DM',(110.98,109.68)),via('USB_DP',(110.972,110.34)),via('SWDIO',(114.251387,108.55))]
new+=path('SWDIO','B.Cu',[(116.35,106.15),(116.35,107.15),(115.85,107.80),(115.001387,107.80),(114.251387,108.55)],.127)
new+=path('SWDIO','In3.Cu',[(114.251387,108.55),(114.191252,108.776284)],.127)
new+=path('IMU_CS','In2.Cu',[(110.528858,109.112142),(110.63,109.23),(111.45,109.23),(111.72,109.50),(111.72,110.155),(111.610503,110.264497)],.127)

new+=path('USB_DM','In3.Cu',[(110.98,109.68),(111.40,110.10),(111.40,110.524),(111.28,110.644),(111.10,110.78),(111.0385,110.85)])
new+=path('USB_DP','In3.Cu',[(110.972,110.34),(110.7615,110.5505),(110.7615,110.85)])

def check():
 out=[]
 for idx,o in enumerate(new):
  oldt=sc.foreign_tracks;oldv=sc.foreign_vias
  sc.foreign_tracks=[t for t in oldt if t['uuid'] not in removed and t['net']!=o['net']]
  sc.foreign_vias=[v for v in oldv if v['uuid'] not in removed and v['net']!=o['net']]
  rr=sc.checkseg(o['net'],o['layer'],o['start'],o['end'],o['width']) if o['kind']=='segment' else sc.checkvia(o['net'],o['at'],o['diameter'])
  sc.foreign_tracks=oldt;sc.foreign_vias=oldv
  for r in rr:out.append(dict(new_index=idx,new_item=o,**r))
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
   if gap<.127-1e-8:out.append(dict(new_index=i,new_item=a,gap_mm=gap,item=b,other_new_index=j,required_mm=.127))
 return out
if __name__=='__main__':
 out=check()
 for r in out:
  i=r['item'];print(r['new_index'],r['new_item']['net'],round(r['gap_mm'],5),r.get('checked_layer'),i['net'],i.get('layer'),i.get('uuid','NEW'+str(r.get('other_new_index'))),i.get('ref'),i.get('pin'))
 print('FAILURES',len(out))
 (D/'mcu'/'candidate.json').write_text(json.dumps(dict(source_sha256=H,removed_uuids=removed,new_objects=new,violations=out),indent=2)+'\n')
