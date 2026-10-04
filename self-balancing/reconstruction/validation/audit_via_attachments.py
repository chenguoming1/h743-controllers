#!/usr/bin/python3
"""Read-only signal-via attachment quality, separate from electrical connectivity.

Contacting track capsules are grouped by physical overlap without using the via
as a bridge. Each group gets radial annulus penetration and exact analytic
angular coverage at the mid-annulus ring. A shallow independent branch therefore
cannot be hidden by a different deep branch on the same via/layer. Thresholds
are conservative review prompts, not a fabrication-standard claim.
"""
import argparse,collections,hashlib,json,math,os
from pathlib import Path
os.environ.setdefault('KICAD_CONFIG_HOME','/tmp/controller-r3-kicad')
import pcbnew as p
TAU=2*math.pi
sha=lambda q:hashlib.sha256(q.read_bytes()).hexdigest()
uid=lambda q:q.m_Uuid.AsString()
xy=lambda q:[q.x/1e6,q.y/1e6]
def distance_point_segment(pt,a,z):
 d=(z[0]-a[0],z[1]-a[1]);den=d[0]**2+d[1]**2
 t=max(0,min(1,((pt[0]-a[0])*d[0]+(pt[1]-a[1])*d[1])/den)) if den else 0
 return math.hypot(pt[0]-a[0]-t*d[0],pt[1]-a[1]-t*d[1])
def track_record(t):return {'uuid':uid(t),'net':t.GetNetname(),'layer':t.GetLayerName(),'start_mm':xy(t.GetStart()),'end_mm':xy(t.GetEnd()),'width_mm':t.GetWidth()/1e6}
def sig(t):return (t['net'],t['layer'],tuple(t['start_mm']),tuple(t['end_mm']),t['width_mm'])
def capsule_ring_intervals(a,z,half,rho):
 angles={0.,TAU};d=(z[0]-a[0],z[1]-a[1]);length=math.hypot(*d)
 for q in [a,z]:
  radius=math.hypot(*q)
  if radius and rho:
   value=(rho*rho+radius*radius-half*half)/(2*rho*radius)
   if -1<=value<=1:
    off=math.acos(value);phi=math.atan2(q[1],q[0]);angles.update([(phi-off)%TAU,(phi+off)%TAU])
 if length:
  n=(-d[1]/length,d[0]/length);phi=math.atan2(n[1],n[0]);base=n[0]*a[0]+n[1]*a[1]
  for value in [(base-half)/rho,(base+half)/rho]:
   if -1<=value<=1:
    off=math.acos(value);angles.update([(phi-off)%TAU,(phi+off)%TAU])
 angles=sorted(angles);out=[]
 for start,end in zip(angles,angles[1:]):
  theta=(start+end)/2;pt=(rho*math.cos(theta),rho*math.sin(theta))
  if distance_point_segment(pt,a,z)<=half+1e-12:out.append([start,end])
 return out

def union_intervals(rows):
 merged=[]
 for lo,hi in sorted(rows):
  if not merged or lo>merged[-1][1]+1e-10:merged.append([lo,hi])
  else:merged[-1][1]=max(merged[-1][1],hi)
 spans=[hi-lo for lo,hi in merged]
 if len(merged)>1 and merged[0][0]<1e-10 and merged[-1][1]>TAU-1e-10:spans.append(merged[0][1]+TAU-merged[-1][0])
 return merged,sum(hi-lo for lo,hi in merged),max(spans,default=0)

def inspect(path,include_ground=False):
 b=p.LoadBoard(str(path));ts=[t for t in b.GetTracks() if not isinstance(t,p.PCB_VIA)];vias=[v for v in b.GetTracks() if isinstance(v,p.PCB_VIA) and (include_ground or v.GetNetname()!='GND')];by=collections.defaultdict(list);profiles={};arcs=[]
 for t in ts:
  if isinstance(t,p.PCB_ARC):arcs.append(uid(t))
  by[(t.GetNetname(),t.GetLayer())].append(t)
 pads=[q for f in b.GetFootprints() for q in f.Pads()]
 for v in vias:
  for layer in b.GetEnabledLayers().CuStack():
   if not v.IsOnLayer(layer):continue
   contact=[t for t in by[(v.GetNetname(),layer)] if t.GetEffectiveShape(layer).GetClearance(v.GetEffectiveShape(layer))<=0]
   if not contact:continue
   par=list(range(len(contact)))
   def root(i):
    while par[i]!=i:par[i]=par[par[i]];i=par[i]
    return i
   for i,t in enumerate(contact):
    for j,u in enumerate(contact[:i]):
     if t.GetEffectiveShape(layer).GetClearance(u.GetEffectiveShape(layer))<=0:par[root(i)]=root(j)
   groups=collections.defaultdict(list)
   for i,t in enumerate(contact):groups[root(i)].append(t)
   pos=xy(v.GetPosition());outer=v.GetWidth(layer)/2e6;inner=v.GetDrillValue()/2e6;mid=(outer+inner)/2;rows=[]
   for tracks in groups.values():
    minima=[];ints=[];maxima=[]
    for t in tracks:
     a=[q-pos[i] for i,q in enumerate(xy(t.GetStart()))];z=[q-pos[i] for i,q in enumerate(xy(t.GetEnd()))];half=t.GetWidth()/2e6;minima.append(max(0,distance_point_segment((0,0),a,z)-half));maxima.append(max(math.hypot(*a),math.hypot(*z))+half);ints+=capsule_ring_intervals(a,z,half,mid)
    merged,total,largest=union_intervals(ints);minr=min(minima);penetration=min(1,max(0,(outer-minr)/(outer-inner)));minimum_width=min(t.GetWidth() for t in tracks)/1e6;arclength=mid*largest;contained=max(maxima)<=outer+1e-9;shallow=not contained and (penetration<.5-1e-9 or arclength<minimum_width*.5-1e-9)
    touched=[q.GetParentFootprint().GetReference()+'.'+q.GetNumber() for q in pads if q.GetNetname()==v.GetNetname() and q.IsOnLayer(layer) and any(t.GetEffectiveShape(layer).GetClearance(q.GetEffectiveShape(layer))<=0 for t in tracks)]
    rows.append({'fully_contained_within_via_land':contained,'contained_stub_disposition':'No external trace attachment: entire copper group lies within the native via land' if contained else None,'tracks':[track_record(t) for t in tracks],'native_mid_annulus_disk_gap_mm':min(t.GetEffectiveShape(layer).GetClearance(p.SHAPE_CIRCLE(v.GetPosition(),round(mid*1e6))) for t in tracks)/1e6,'min_copper_radius_mm':minr,'annulus_radial_penetration_fraction':penetration,'reaches_mid_annulus':penetration>=.5-1e-9,'mid_annulus_coverage_degrees':math.degrees(total),'largest_mid_annulus_contact_arc_mm':arclength,'half_minimum_incident_track_width_mm':minimum_width*.5,'shallow_review_prompt':shallow,'direct_pad_contacts':sorted(touched),'mid_annulus_intervals_radians':merged})
   key=uid(v)+':'+b.GetLayerName(layer);profiles[key]={'via_uuid':uid(v),'net':v.GetNetname(),'layer':b.GetLayerName(layer),'xy_mm':pos,'via_diameter_mm':2*outer,'drill_mm':2*inner,'mid_annulus_radius_mm':mid,'contact_groups':rows}
 return {'source':str(path),'sha256':sha(path),'audited_vias':len(vias),'signal_vias':sum(v.GetNetname()!='GND' for v in vias),'ground_vias':sum(v.GetNetname()=='GND' for v in vias),'profiles':profiles,'unsupported_arcs':arcs}

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--include-ground',action='store_true');ap.add_argument('--baseline',type=Path,required=True);ap.add_argument('--candidate',type=Path,required=True);ap.add_argument('--sha256',required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();assert sha(a.candidate)==a.sha256;A=inspect(a.baseline,a.include_ground);B=inspect(a.candidate,a.include_ground);flags=[];existing=[];changed=[];disappeared=[]
 for key,row in B['profiles'].items():
  old=A['profiles'].get(key,{}).get('contact_groups',[])
  for i,g in enumerate(row['contact_groups']):
   ids={q['uuid'] for q in g['tracks']};geometry={sig(q) for q in g['tracks']}
   exact=next((q for q in old if {sig(t) for t in q['tracks']}==geometry),None)
   match=max(old,key=lambda q:len(ids&{t['uuid'] for t in q['tracks']}),default=None)
   if match and not(ids&{t['uuid'] for t in match['tracks']}):
    # Most local-contact groups have no surviving UUID after complete path
    # replacement. With a unique former group, comparison is unambiguous.
    match=old[0] if len(old)==1 else None
   entry={k:v for k,v in row.items() if k!='contact_groups'};entry.update(group_index=i,candidate=g,baseline_match=exact or match,exact_contact_geometry_retained=bool(exact))
   if not exact:changed.append(entry)
   if not g['shallow_review_prompt']:continue
   if exact:entry['classification']='Inherited exact shallow contact geometry';existing.append(entry);continue
   worse=not match or g['annulus_radial_penetration_fraction']<match['annulus_radial_penetration_fraction']-1e-6 or g['largest_mid_annulus_contact_arc_mm']<match['largest_mid_annulus_contact_arc_mm']-1e-6
   entry['classification']='New or worsened shallow contact group' if worse else 'Changed but no shallower than matched baseline contact'
   if worse:flags.append(entry)
   else:existing.append(entry)
 for key,row in A['profiles'].items():
  if key not in B['profiles']:disappeared.append({k:v for k,v in row.items() if k!='contact_groups'})
 report={'status':'REVIEW REQUIRED: NEW SHALLOW CONTACTS' if flags else 'NO NEW SHALLOW SIGNAL-VIA CONTACTS FOUND','candidate_sha256':a.sha256,'baseline_sha256':A['sha256'],'summary':{'audited_vias':B['audited_vias'],'signal_vias':B['signal_vias'],'ground_vias':B['ground_vias'],'baseline_routed_via_layer_profiles':len(A['profiles']),'candidate_routed_via_layer_profiles':len(B['profiles']),'baseline_contact_groups':sum(len(q['contact_groups']) for q in A['profiles'].values()),'candidate_contact_groups':sum(len(q['contact_groups']) for q in B['profiles'].values()),'changed_contact_groups':len(changed),'new_or_worsened_shallow_groups':len(flags),'inherited_or_improved_shallow_groups':len(existing),'via_layer_contacts_disappeared':len(disappeared)},'thresholds':{'mid_annulus_radial_fraction':.5,'minimum_largest_mid_annulus_contact_arc_fraction_of_incident_width':.5,'regression_comparison_tolerance_mm':1e-6},'new_or_worsened_shallow_groups':flags,'inherited_or_improved_shallow_groups':existing,'changed_contact_groups':changed,'disappeared_via_layer_contacts':disappeared,'baseline':A,'candidate':B,'method':__doc__,'limits':'Geometric attachment screening only, independent of and additional to electrical topology. Does not establish fabrication acceptance or physical current capacity. Pure copper arcs require separate handling; all current board routes are straight capsules.'}
 assert not A['unsupported_arcs'] and not B['unsupported_arcs'];assert sha(a.candidate)==a.sha256 and sha(a.baseline)==A['sha256'];a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'status':report['status'],'summary':report['summary'],'flags':[{'net':q['net'],'layer':q['layer'],'xy_mm':q['xy_mm'],'via_uuid':q['via_uuid'],'penetration':q['candidate']['annulus_radial_penetration_fraction'],'mid_contact_arc_mm':q['candidate']['largest_mid_annulus_contact_arc_mm']} for q in flags]},indent=2))
if __name__=='__main__':main()
