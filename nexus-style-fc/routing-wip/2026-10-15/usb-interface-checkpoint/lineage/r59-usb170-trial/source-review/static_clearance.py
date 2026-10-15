"""Analytic capsule/rectangle clearance screening only. Rounded-rectangle pads conservatively use bounding rectangles. No native DRC."""
from source_context import *
def point_seg(p,a,b):
 dx=b[0]-a[0];dy=b[1]-a[1];z=dx*dx+dy*dy
 t=max(0,min(1,((p[0]-a[0])*dx+(p[1]-a[1])*dy)/z)) if z else 0
 q=(a[0]+t*dx,a[1]+t*dy)
 return math.dist(p,q),q

def cross(a,b,c):return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
def seg_seg(a,b,c,d):
 if max(min(a[0],b[0]),min(c[0],d[0]))<=min(max(a[0],b[0]),max(c[0],d[0]))+1e-12 and max(min(a[1],b[1]),min(c[1],d[1]))<=min(max(a[1],b[1]),max(c[1],d[1]))+1e-12 and cross(a,b,c)*cross(a,b,d)<=0 and cross(c,d,a)*cross(c,d,b)<=0:return 0
 return min(point_seg(a,c,d)[0],point_seg(b,c,d)[0],point_seg(c,a,b)[0],point_seg(d,a,b)[0])
def local(p,pad):
 dx=p[0]-pad['at'][0];dy=p[1]-pad['at'][1];q=math.radians(pad['rotation']);c=math.cos(q);s=math.sin(q)
 return (c*dx-s*dy,s*dx+c*dy)
def seg_pad(a,b,p):
 a=local(a,p);b=local(b,p);sx,sy=p['size']
 if p['shape']=='circle':return point_seg((0,0),a,b)[0]-sx/2
 if p['shape']=='oval':
  if sx>sy:c=(-sx/2+sy/2,0);d=(sx/2-sy/2,0);r=sy/2
  else:c=(0,-sy/2+sx/2);d=(0,sy/2-sx/2);r=sx/2
  return seg_seg(a,b,c,d)-r
 if any(abs(q[0])<=sx/2 and abs(q[1])<=sy/2 for q in [a,b]):return 0
 cs=[(-sx/2,-sy/2),(sx/2,-sy/2),(sx/2,sy/2),(-sx/2,sy/2)]
 return min(seg_seg(a,b,c,d) for c,d in zip(cs,cs[1:]+cs[:1]))
foreign_tracks=[t for t in tracks if t['net'] not in ('USB_DP','USB_DM')];foreign_vias=[v for v in vias if v['net'] not in ('USB_DP','USB_DM')]
def checkseg(net,layer,a,b,w=.15):
 out=[]
 for t in foreign_tracks:
  if t['layer']!=layer:continue
  g=seg_seg(a,b,t['start'],t['end'])-(w+t['width'])/2
  if g<.127-1e-8:out.append(dict(gap_mm=g,item=t,required_mm=.127))
 for v in foreign_vias:
  g=point_seg(v['at'],a,b)[0]-v['diameter']/2-w/2
  if g<.127-1e-8:out.append(dict(gap_mm=g,item=v,required_mm=.127))
 for p in pads:
  if (layer not in p['layers'] and '*.Cu' not in p['layers']) or p['net']==net:continue
  g=seg_pad(a,b,p)-w/2;req=.2 if p['type']=='np_thru_hole' else .127
  if g<req-1e-8:out.append(dict(gap_mm=g,item=p,required_mm=req,shape_screen='bounding rectangle for roundrect pads; exact rectangle/oval/circle otherwise'))
 return sorted(out,key=lambda q:q['gap_mm'])
def checkvia(net,at,size=.45):
 out=[]
 for layer in ls:
  for r in checkseg(net,layer,at,at,size):r['checked_layer']=layer;out.append(r)
 return out
if __name__=='__main__':
 for p in [(108.65,129.8),(108.75,129.95),(108.55,129.95),(108.5,129.8),(110.85,124.35),(110.85,126.25),(110.15,126.65),(110.2,124.35)]:
  r=checkvia('USB_DP' if p[1]<125 or p[1]>129 else 'USB_DM',p)
  print(p,[(round(x['gap_mm'],4),x['item'].get('ref',''),x['item'].get('pin',''),x['item']['net'],x['item']['uuid'][:8],x['checked_layer']) for x in r])
 print('near main vias',[(v['at'],v['net']) for v in foreign_vias if 109<v['at'][0]<111.5 and 119<v['at'][1]<127])
