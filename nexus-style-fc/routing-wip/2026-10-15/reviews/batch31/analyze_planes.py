from pathlib import Path
import pcbnew as k,json,math,collections
D=Path('/tmp/nexus-boardlevel-review-20261015');j=json.loads((D/'batch31-geometry.json').read_text());old=json.loads((D/'candidate16-geometry.json').read_text())
b=k.LoadBoard(j['path']);ls=list(b.GetEnabledLayers().CuStack());vs={x['uuid']:x for x in j['tracks'] if 'at' in x};items={x['uuid']:x for x in j['tracks']};oi={x['uuid']:x for x in old['tracks']}
polys={b.GetLayerName(l):[z.GetFilledPolysList(l) for z in b.Zones() if not z.GetIsRuleArea() and z.IsOnLayer(l) and z.GetNetname()=='GND'] for l in ls}
def inside(p,l):return any(s.Contains(k.VECTOR2I(round(p[0]*1e6),round(p[1]*1e6))) for s in polys[l])
def vec(a,c,f):return [a[0]+(c[0]-a[0])*f,a[1]+(c[1]-a[1])*f]
def coverage(t,l):
 a,c=t['start'],t['end'];n=math.ceil(t['length']/.02);covered=0;gaps=[];start=None
 for i in range(n):
  f=(i+.5)/n;yes=inside(vec(a,c,f),l)
  if yes:
   covered+=1
   if start is not None:gaps.append([start/n,i/n]);start=None
  elif start is None:start=i
 if start is not None:gaps.append([start/n,1])
 return {'covered_fraction':covered/n,'uncovered_length_mm':(n-covered)*t['length']/n,'gaps':[{'from':vec(a,c,x),'to':vec(a,c,y),'length':(y-x)*t['length']} for x,y in gaps]}
newvia_ids=['379803c4-3c43-4a54-afe8-1aabe6e556c7','27961961-aebc-4e21-abce-c170061b0970','ad43ba66-0b8b-46dd-97d3-1684e4d759e7','5771bb97-8186-4e3f-8a09-236a5710b2bf']
ground=[{**x,'kind':'via'} for x in vs.values() if x['net']=='GND']+[{**x,'kind':'pad'} for x in j['pads'] if x['net']=='GND' and len(x['layers'])>2]
viareview=[]
for u in newvia_ids+['0822d30f-fa7e-4f84-9094-b20c35d8d54a','0822d30f-fa7e-4b70-a489-e63108ca6144','44eb5399-2c82-41bc-8f8d-5685903f1964']:
 if u not in vs:continue
 v=vs[u];near=sorted(ground,key=lambda x:math.dist(x['at'],v['at']))[:5];near=[{**p,'center_distance_mm':math.dist(p['at'],v['at']),'GND_fill_at_center':{l:inside(p['at'],l) for l in polys}} for p in near]
 touches=[x for x in j['tracks'] if 'start' in x and x['net']==v['net'] and min(math.dist(x[z],v['at']) for z in ['start','end'])<1e-5]
 viareview.append({'via':v,'tracks_ending_at_via':touches,'nearest_GND_through_connections':near})
changed=[x for x in j['tracks'] if 'start' in x and (x['uuid'] not in oi or x!=oi[x['uuid']])]
focus=[x for x in changed if (x['net']=='B_TX' and x['layers']==['In2.Cu']) or (x['net']=='3V3_SENS' and x['layers']==['In3.Cu']) or (x['net']=='3V3' and (max(x['start'][1],x['end'][1])>=121) and (min(x['start'][0],x['end'][0])<109))]
ref=[]
for t in focus:
 ref.append({'track':t,'GND_projection':{l:coverage(t,l) for l in polys if l!=t['layers'][0]}})
# Distinct-net geometric crossings with the immediately neighboring signal layer, purely 2D projected.
def crossing(a,b,c,d):
 r=[b[i]-a[i] for i in range(2)];s=[d[i]-c[i] for i in range(2)];den=r[0]*s[1]-r[1]*s[0]
 if abs(den)<1e-12:return None
 q=[c[i]-a[i] for i in range(2)];t=(q[0]*s[1]-q[1]*s[0])/den;u=(q[0]*r[1]-q[1]*r[0])/den
 if 0<=t<=1 and 0<=u<=1:return vec(a,b,t)
 return None
crossings=[]
for t in focus:
 l=t['layers'][0];other={'In2.Cu':'In3.Cu','In3.Cu':'In2.Cu'}.get(l)
 if not other:continue
 for o in j['tracks']:
  if 'start' in o and o['layers']==[other] and o['net'] not in [t['net'],'GND']:
   p=crossing(t['start'],t['end'],o['start'],o['end'])
   if p:crossings.append({'new_track':t,'neighbor_track':o,'projection_crossing':p})
lengths={}
for n in ['main','candidate16','batch31']:
 q=json.loads((D/(n+'-geometry.json')).read_text());acc=collections.defaultdict(float);vias=collections.Counter()
 for t in q['tracks']:
  if 'start'in t:acc[(t['net'],t['layers'][0],t['width'])]+=t['length']
  else:vias[t['net']]+=1
 lengths[n]={'bins':[{'net':a,'layer':c,'width_mm':w,'length_mm':v} for (a,c,w),v in sorted(acc.items())],'vias_by_net':dict(vias)}
out={'sampling':'0.02 mm maximum midpoint step; centerline projection only, fills read as stored; no DRC, refill or solver','vias':viareview,'focus_track_reference':ref,'neighbor_signal_crossings':crossings,'lengths':lengths}
(D/'plane-power-analysis.json').write_text(json.dumps(out,indent=2))
for v in viareview:
 print('\nVIA',v['via']['net'],v['via']['at'],'track layers',[x['layers'] for x in v['tracks_ending_at_via']],'nearest GND',[(p.get('ref','via'),p['at'],round(p['center_distance_mm'],4),p['GND_fill_at_center']) for p in v['nearest_GND_through_connections'][:2]])
for r in ref:
 t=r['track'];print('\nROUTE',t['net'],t['layers'],t['start'],t['end'],round(t['length'],4))
 print({l:round(v['uncovered_length_mm'],4) for l,v in r['GND_projection'].items()})
print('\nCROSSINGS',[(x['new_track']['net'],x['new_track']['layers'],x['neighbor_track']['net'],x['projection_crossing']) for x in crossings])
