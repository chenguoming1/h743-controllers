from pathlib import Path
import pcbnew as k,json,hashlib,math,collections,time
R=Path('/workspace/scratch/8a35c1f26232/nexus-recovery-20261015');O=R/'vsys-thermal-study';j=json.loads((O/'geometry.json').read_text());P=Path(j['source']);sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();assert sha(P)==j['source_sha256'];b=k.LoadBoard(str(P));uid=lambda x:x.m_Uuid.AsString();xy=lambda p:[p.x/1e6,p.y/1e6];vec=lambda p:k.VECTOR2I(round(p[0]*1e6),round(p[1]*1e6));ts={uid(t):t for t in b.GetTracks()};ps={uid(p):p for f in b.GetFootprints() for p in f.Pads()};obs={u:q.GetEffectiveShape(k.In3_Cu) for u,q in {**ts,**ps}.items() if q.IsOnLayer(k.In3_Cu)};conn=b.GetConnectivity();ids=['79c2d0d0-a175-4560-bfe6-3ff9a505332c','f681f3fd-77a9-4540-9df2-9684b7e01ed4','83f0f3e3-4a0f-4c11-94a4-4febb46bb6fb'];ports={}
def col(a,c,g=0):
 v=k.SHAPE.Collide(a,c,g);return v[0] if isinstance(v,tuple) else bool(v)
def make(u,pts):
 a=ts[u];out=[]
 for p,q in zip(pts,pts[1:]):
  t=k.PCB_TRACK(b);t.SetStart(vec(p));t.SetEnd(vec(q));t.SetWidth(a.GetWidth());t.SetLayer(k.In3_Cu);t.SetNetCode(a.GetNetCode());out.append(t)
 return out
for u in ids:
 t=ts[u];ports[u]=sorted({uid(q) for q in list(conn.GetConnectedTracks(t))+list(conn.GetConnectedPads(t)) if uid(q)!=u and q.IsOnLayer(k.In3_Cu) and col(t.GetEffectiveShape(k.In3_Cu),q.GetEffectiveShape(k.In3_Cu))})
a,z=xy(ts[ids[0]].GetStart()),xy(ts[ids[0]].GetEnd());f0,f1=xy(ts[ids[1]].GetStart()),xy(ts[ids[1]].GetEnd());f0,f1=sorted([f0,f1],key=lambda p:p[1]);linear=lambda y:[round(a[0]+(y-a[1])*(z[0]-a[0])/(z[1]-a[1]),6),y]
sol=[];bad=collections.Counter();tested=0;start=time.monotonic()
for x in [103.16,103.17,103.18,103.19,103.20]:
 for fx in [103.60,103.62,103.64,103.66,103.68,103.70]:
  for top in [108.08,108.12,108.16]:
   for bottom in [108.4,108.5,108.6]:
    tested+=1;p=[a,linear(107.93),[x,top],[x,bottom],linear(108.75),z];f=[[104.656011,106.760858],[fx,107.910071],[fx,bottom],[103.52,109.3],[103.52,109.9],f1];new=make(ids[0],p)+make(ids[1],f);failed=None
    for t in new:
     shape=t.GetEffectiveShape(k.In3_Cu)
     for u,s in obs.items():
      if u in ids or (ts.get(u) or ps.get(u)).GetNetCode()==t.GetNetCode():continue
      if col(shape,s,127002):failed=u;break
     if failed:break
     for q in new:
      if q.GetNetCode()!=t.GetNetCode() and col(shape,q.GetEffectiveShape(k.In3_Cu),127002):failed='coordinated-new-pair';break
     if failed:break
    if failed:bad[failed]+=1
    else:sol.append({'VSYS_points':p,'5V_points':f,'new_length_mm':sum(t.GetLength()/1e6 for t in new)})
    if time.monotonic()-start>60:raise RuntimeError('Bound exceeded')
ground={}
for lay in [k.In2_Cu,k.In4_Cu]:
 q=k.SHAPE_POLY_SET()
 for z in b.Zones():
  if not z.GetIsRuleArea() and z.GetNetname()=='GND' and z.IsOnLayer(lay):q.BooleanAdd(z.GetFilledPolysList(lay))
 ground[lay]=q
def coverage(tracks):
 p=k.SHAPE_POLY_SET()
 for t in tracks:
  q=k.SHAPE_POLY_SET();t.TransformShapeToPolygon(q,k.In3_Cu,0,500,k.ERROR_OUTSIDE);p.BooleanAdd(q)
 total=abs(p.Area())/1e12;data={}
 for l,g in ground.items():
  q=k.SHAPE_POLY_SET(p);q.BooleanSubtract(g);missing=abs(q.Area())/1e12;data[b.GetLayerName(l)]={'total_area_mm2':total,'uncovered_area_mm2':missing,'coverage_fraction':1-missing/total}
 return data
before={'VSYS':coverage([ts[ids[0]]]),'5V':coverage([ts[ids[1]],ts[ids[2]]])}
for a in sol:
 a['reference']={'VSYS':coverage(make(ids[0],a['VSYS_points'])),'5V':coverage(make(ids[1],a['5V_points']))}
 a['nonregressing_projection']=all(a['reference'][n][l]['coverage_fraction']>=before[n][l]['coverage_fraction'] and a['reference'][n][l]['uncovered_area_mm2']<=before[n][l]['uncovered_area_mm2']+1e-10 for n in before for l in before[n])
sol.sort(key=lambda x:(not x['nonregressing_projection'],-x['reference']['5V']['In2.Cu']['coverage_fraction'],x['new_length_mm']));out={'source':str(P),'source_sha256':sha(P),'removed_tracks':ids,'inherited_widths_mm':{u:ts[u].GetWidth()/1e6 for u in ids},'layer':'In3.Cu','all_physical_external_ports':ports,'before_reference':before,'nonregressing_count':sum(x['nonregressing_projection'] for x in sol),'tested':tested,'valid_count':len(sol),'best':sol[:20],'blockers':bad.most_common(),'seconds':time.monotonic()-start,'scope':'Read-only native geometry screen of complete two-net same-layer, inherited-width paths; no source mutation, no native DRC/return acceptance.'};(O/'reference-ranked-probe.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2));assert sha(P)==j['source_sha256']
