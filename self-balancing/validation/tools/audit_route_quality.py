#!/usr/bin/python3
"""Read-only per-net geometry screening; never substitutes for visual review.

Splits straight centerlines at exact same-net endpoints, records endpoint
pad/via anchors and branch points, and walks every resulting maximal centerline chain.
Signals are review prompts: branches, copper overlap junctions, obstacle-driven
escapes, and terminal entry may justify a flagged shape. Every net is reported,
including protected geometry. Only human inspection can close route quality.
"""
import argparse, collections, csv, hashlib, json, math, os
from pathlib import Path
os.environ.setdefault('KICAD_CONFIG_HOME','/tmp/controller-r3-kicad')
import pcbnew as p

def sha(q): return hashlib.sha256(q.read_bytes()).hexdigest()
def xy(q): return (q.x,q.y)
def mm(q): return [round(v/1e6,6) for v in q]
def dist(a,b):return math.hypot(a[0]-b[0],a[1]-b[1])/1e6
def angle(a,b,c):
 u=(b[0]-a[0],b[1]-a[1]);v=(c[0]-b[0],c[1]-b[1])
 return math.degrees(math.atan2(u[0]*v[1]-u[1]*v[0],u[0]*v[0]+u[1]*v[1]))
def protected(n):return n.rsplit('/',1)[-1].startswith(('USB_DP','USB_DM','HSE_','BUCK_','VCAP'))
def power(n):return n in {'GND','3V3_CORE','VLOGIC_IN','+5V_STACK','VDDA','IMU_3V3','USB_VBUS'} or n.startswith('/power/')
def inventory(path):
 b=p.LoadBoard(str(path));by=collections.defaultdict(list);term=collections.defaultdict(list);nets={};all_tracks=[]
 for t in b.GetTracks():
  n=t.GetNetname()
  if isinstance(t,p.PCB_VIA):
   for l in b.GetEnabledLayers().CuStack():
    if t.IsOnLayer(l):term[(n,l)].append(t)
   continue
  all_tracks.append(t)
  by[(n,t.GetLayer())].append(t)
 for f in b.GetFootprints():
  for q in f.Pads():
   for l in b.GetEnabledLayers().CuStack():
    if q.IsOnLayer(l):term[(q.GetNetname(),l)].append(q)
 candidates=[];chain_rows=[]
 for (net,layer),ts in sorted(by.items()):
  row=nets.setdefault(net,{'net':net,'protected':protected(net),'rail_or_power':power(net),'tracks':0,'arcs':0,'total_length_mm':0.,'layer_counts':collections.Counter(),'width_length_mm':collections.Counter(),'chains':0,'bends':0,'short_segments_lt_030mm':0,'tiny_segments_lt_010mm':0,'collinear_joins':0,'reverse_hooks':0,'scallops':0,'width_transitions':0,'short_width_pulses':0,'detour_windows':0,'long_chain_detours':0})
  row['layer_counts'][b.GetLayerName(layer)]+=len(ts)
  for t in ts:
   ln=p.ToMM(t.GetLength());row['tracks']+=1;row['arcs']+=isinstance(t,p.PCB_ARC);row['total_length_mm']+=ln;row['short_segments_lt_030mm']+=ln<.3;row['tiny_segments_lt_010mm']+=ln<.1;row['width_length_mm'][str(round(p.ToMM(t.GetWidth()),6))]+=ln
  straight=[t for t in ts if not isinstance(t,p.PCB_ARC)];points={xy(q) for t in ts for q in [t.GetStart(),t.GetEnd()]};edges=[];at=collections.defaultdict(list)
  for t in straight:
   a,z=xy(t.GetStart()),xy(t.GetEnd());u=(z[0]-a[0],z[1]-a[1]);den=u[0]**2+u[1]**2
   if not den:continue
   cuts=[a,z]
   for c in points:
    if c==a or c==z:continue
    v=(c[0]-a[0],c[1]-a[1]);along=v[0]*u[0]+v[1]*u[1]
    if 0<along<den and u[0]*v[1]-u[1]*v[0]==0:cuts.append(c)
   cuts.sort(key=lambda q:(q[0]-a[0])*u[0]+(q[1]-a[1])*u[1])
   for a,z in zip(cuts,cuts[1:]):
    e={'a':a,'b':z,'uuid':t.m_Uuid.AsString(),'width':t.GetWidth(),'length':dist(a,z)};i=len(edges);edges.append(e);at[a].append(i);at[z].append(i)
  anchors={}
  for pt,ids in at.items():
   labels=[];v=p.VECTOR2I(*pt)
   for t in term[(net,layer)]:
    if t.GetEffectiveShape(layer).Collide(v,0):
     labels.append(('via:'+t.m_Uuid.AsString()) if isinstance(t,p.PCB_VIA) else t.GetParentFootprint().GetReference()+'.'+t.GetNumber())
   if labels:anchors[pt]=labels
  # Width changes and terminal contacts are annotated, not used to hide a
  # geometrically continuous scallop. Physical topology is separately gated.
  boundaries={q for q,ids in at.items() if len(ids)!=2};visited=set();paths=[]
  def walk(start,edge):
   pts=[start];ids=[];cur=start;i=edge
   while i not in visited:
    visited.add(i);ids.append(i);e=edges[i];cur=e['b'] if e['a']==cur else e['a'];pts.append(cur)
    if cur in boundaries:break
    rest=[j for j in at[cur] if j not in visited]
    if not rest:break
    i=rest[0]
   return pts,ids
  for start in sorted(boundaries):
   for i in at[start]:
    if i not in visited:paths.append(walk(start,i))
  for i,e in enumerate(edges):
   if i not in visited:paths.append(walk(e['a'],i))
  for pts,ids in paths:
   if not ids:continue
   es=[edges[i] for i in ids];lens=[e['length'] for e in es];widths=[e['width']/1e6 for e in es];angs=[angle(*pts[i:i+3]) for i in range(len(pts)-2)];total=sum(lens);chord=dist(pts[0],pts[-1]);ratio=total/chord if chord else None;chain_id=len(chain_rows)
   cr={'id':chain_id,'net':net,'layer':b.GetLayerName(layer),'protected':protected(net),'points_mm':[mm(q) for q in pts],'uuids':[e['uuid'] for e in es],'widths_mm':widths,'length_mm':round(total,6),'chord_mm':round(chord,6),'detour_ratio':round(ratio,4) if ratio else None,'turn_angles_deg':[round(q,2) for q in angs],'anchor_contacts':[{'point_index':i,'labels':anchors[q]} for i,q in enumerate(pts) if q in anchors],'start_labels':anchors.get(pts[0],[]),'end_labels':anchors.get(pts[-1],[]),'start_degree':len(at[pts[0]]),'end_degree':len(at[pts[-1]])};chain_rows.append(cr);row['chains']+=1;row['bends']+=sum(abs(v)>1 for v in angs)
   def flag(kind,indices,details):
    inside=[(('via:'+t.m_Uuid.AsString()) if isinstance(t,p.PCB_VIA) else t.GetParentFootprint().GetReference()+'.'+t.GetNumber()) for t in term[(net,layer)] if all(t.GetEffectiveShape(layer).Collide(p.VECTOR2I(*pts[j]),0) for j in indices)]
    q={'inside_one_terminal_centerline':inside,'kind':kind,'net':net,'layer':b.GetLayerName(layer),'protected':protected(net),'chain':chain_id,'points_mm':[mm(pts[j]) for j in indices],'uuids':list(dict.fromkeys(es[j]['uuid'] for j in range(max(0,min(indices)-1),min(len(es),max(indices)+1)))),**details};candidates.append(q);row[kind]+=1
   for j,v in enumerate(angs):
    if abs(v)<.01 and widths[j]==widths[j+1]:flag('collinear_joins',[j,j+1,j+2],{'at_mm':mm(pts[j+1])})
    if abs(v)>100 and min(lens[j:j+2])<.5:flag('reverse_hooks',[j,j+1,j+2],{'turn_deg':round(v,2),'lengths_mm':lens[j:j+2]})
   for j in range(1,len(widths)):
    if abs(widths[j]-widths[j-1])>1e-6:flag('width_transitions',[j],{'widths_mm':widths[j-1:j+1],'at_mm':mm(pts[j])})
   for j in range(1,len(widths)-1):
    if widths[j-1]==widths[j+1] and widths[j]!=widths[j-1] and lens[j]<1:flag('short_width_pulses',[j,j+1],{'widths_mm':widths[j-1:j+2],'middle_length_mm':lens[j]})
   # A scallop is a compact zig-zag of at least three alternating turns.
   j=0
   while j<len(angs)-2:
    if all(abs(v)>=15 for v in angs[j:j+3]) and angs[j]*angs[j+1]<0 and angs[j+1]*angs[j+2]<0 and max(lens[j+1:j+3])<.8:
     end=j+3
     while end<len(angs) and abs(angs[end])>=15 and angs[end]*angs[end-1]<0 and lens[end]<.8:end+=1
     flag('scallops',list(range(j,end+2)),{'turns_deg':[round(v,2) for v in angs[j:end]],'length_mm':round(sum(lens[j:end+1]),6)});j=end
    else:j+=1
   # Non-overlapping greedy windows with true backtracking or >=35% excess
   # path length. Mere many-segment subdivision is never called a detour.
   windows=[]
   for i in range(len(es)-1):
    for j in range(i+2,min(len(es),i+8)+1):
     length=sum(lens[i:j]);direct=dist(pts[i],pts[j]);excess=length-direct
     if direct<.15 or excess<.20:continue
     ar=angs[i:j-1]
     if sum(abs(v)>15 for v in ar)<2:continue
     v=(pts[j][0]-pts[i][0],pts[j][1]-pts[i][1]);back=sum(lens[k] for k in range(i,j) if (pts[k+1][0]-pts[k][0])*v[0]+(pts[k+1][1]-pts[k][1])*v[1]<0)
     if length/direct>=1.35 or back>.15:windows.append((excess,i,j,length,direct,back))
   used=set()
   for excess,i,j,length,direct,back in sorted(windows,reverse=True):
    if any(k in used for k in range(i,j)):continue
    used.update(range(i,j));flag('detour_windows',list(range(i,j+1)),{'length_mm':round(length,6),'chord_mm':round(direct,6),'excess_mm':round(excess,6),'ratio':round(length/direct,4),'backtrack_length_mm':round(back,6),'clearance_validated':False})
   if ratio and total>3 and ratio>1.5:flag('long_chain_detours',[0,len(pts)-1],{'length_mm':round(total,6),'chord_mm':round(chord,6),'ratio':round(ratio,4),'clearance_validated':False})
 for r in nets.values():
  r['total_length_mm']=round(r['total_length_mm'],6);r['layer_counts']=dict(r['layer_counts']);r['width_length_mm']={k:round(v,6) for k,v in sorted(r['width_length_mm'].items())}
 summary={'routed_nets':len(nets),'track_count':len(all_tracks),'arc_count':sum(isinstance(t,p.PCB_ARC) for t in all_tracks),'total_length_mm':round(sum(r['total_length_mm'] for r in nets.values()),6),'chains':len(chain_rows),'signals':dict(collections.Counter(c['kind'] for c in candidates)),'ordinary_signals':dict(collections.Counter(c['kind'] for c in candidates if not c['protected'])),'external_terminal_signals':dict(collections.Counter(c['kind'] for c in candidates if not c['inside_one_terminal_centerline'])),'external_ordinary_signals':dict(collections.Counter(c['kind'] for c in candidates if not c['inside_one_terminal_centerline'] and not c['protected'])),'nets_with_signals':len({c['net'] for c in candidates})}
 return {'source':str(path),'sha256':sha(path),'summary':summary,'per_net':nets,'chains':chain_rows,'review_candidates':candidates,'status':'SCREENING ONLY; VISUAL REVIEW REQUIRED','method':__doc__,'thresholds':{'reversal_turn_gt_deg':100,'reversal_short_limb_lt_mm':.5,'scallop_internal_limb_lt_mm':.8,'short_width_pulse_lt_mm':1.,'detour_window_min_excess_mm':.20,'detour_window_ratio':1.35},'limits':'No flag independently proves a routing defect or safe replacement. No flags independently prove visual quality. Pad/via contacts are annotated; paths pass through them to expose visual irregularities. This is geometric screening rather than the separate electrical topology proof.'}

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--candidate',type=Path,required=True);ap.add_argument('--sha256',required=True);ap.add_argument('--baseline',type=Path);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();assert sha(a.candidate)==a.sha256;a.out.mkdir(parents=True,exist_ok=True)
 after=inventory(a.candidate);(a.out/'route-quality.json').write_text(json.dumps(after,indent=2)+'\n')
 fields=['net','protected','tracks','arcs','total_length_mm','chains','bends','short_segments_lt_030mm','tiny_segments_lt_010mm','collinear_joins','reverse_hooks','scallops','width_transitions','short_width_pulses','detour_windows','long_chain_detours']
 with (a.out/'route-quality-per-net.csv').open('w') as f:
  w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows({k:r[k] for k in fields} for r in after['per_net'].values())
 if a.baseline:
  before=inventory(a.baseline);delta=[]
  for n in sorted(set(before['per_net'])|set(after['per_net'])):
   x=before['per_net'].get(n,{});y=after['per_net'].get(n,{})
   delta.append({'net':n,'protected':protected(n),'before':x,'after':y,'delta':{k:round(y.get(k,0)-x.get(k,0),6) for k in fields if k not in ['net','protected']}})
  report={'baseline_sha256':before['sha256'],'candidate_sha256':after['sha256'],'before_summary':before['summary'],'after_summary':after['summary'],'per_net':delta,'status':'SCREENING ONLY; NO NUMERIC AESTHETIC ACCEPTANCE','interpretation':'Every routed net is inventoried. Count or length reductions alone do not satisfy all-route cleanup. Inspect remaining signals, especially ordinary-net reversals, scallops, width pulses, and detours, and render every route.'}
  (a.out/'route-quality-comparison.json').write_text(json.dumps(report,indent=2)+'\n')
 assert sha(a.candidate)==a.sha256
 print(json.dumps(after['summary'],indent=2))
if __name__=='__main__':main()
