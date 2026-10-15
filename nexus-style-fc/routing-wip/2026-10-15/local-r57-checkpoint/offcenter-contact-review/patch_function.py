def finite_patch(t,v,depth=.02):
 aa,zz=xy(t.GetStart()),xy(t.GetEnd());length=math.dist(aa,zz);dr=((zz[0]-aa[0])/length,(zz[1]-aa[1])/length);n=(-dr[1],dr[0]);rad=t.GetWidth()/2e6;cen=xy(v.GetPosition());proj=sum((cen[i]-aa[i])*dr[i] for i in range(2));off=abs(sum((cen[i]-aa[i])*n[i] for i in range(2)))
 for q in [proj+d for d in [0,.12,-.12,.15,-.15,.18,-.18]]+[i*length/500 for i in range(1,500)]:
  if not depth/2<=q<=length-depth/2:continue
  corners=[(aa[0]+(q+s*depth/2)*dr[0]+c*rad*n[0],aa[1]+(q+s*depth/2)*dr[1]+c*rad*n[1]) for s in [-1,1] for c in [-1,1]]
  if not all(hit(v.GetEffectiveShape(t.GetLayer()),vec(p)) for p in corners):continue
  dist=math.hypot(max(abs(proj-q)-depth/2,0),max(off-rad,0))
  if dist<v.GetDrillValue()/2e6+.001:continue
  return {'width_mm':rad*2,'depth_mm':depth,'corners':corners}
 return None
