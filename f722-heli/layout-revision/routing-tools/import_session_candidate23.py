#!/usr/bin/env python3
"""Import only ordinary SES route objects, retaining native identity wherever geometry matches.
Run with KiCad Python. Does not call KiCad's destructive/global SES importer.
"""
import argparse,json,hashlib,re,collections,sys,shutil
from pathlib import Path
import pcbnew as p
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'native-tools' if (ROOT/'native-tools').exists() else ROOT.parent/'protection-checks'))
from export_native_copper import export
from route_geometry import reconcile,geometry as route_union

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def parse(text):
 text=re.sub(r'\(string_quote "\)', '',text)
 toks=re.findall(r'\(|\)|"(?:\\.|[^"\\])*"|[^\s()]+',text);pos=0
 def one():
  nonlocal pos
  t=toks[pos];pos+=1
  if t=='(':
   r=[]
   while toks[pos]!=')':r.append(one())
   pos+=1;return r
  if t.startswith('"'):return json.loads(t)
  return t
 r=one();assert pos==len(toks);return r

def children(x,n):return [v for v in x if isinstance(v,list)and v and v[0]==n]
def child(x,n):return children(x,n)[0]
def ses_routes(path):
 x=parse(Path(path).read_text());r=child(x,'routes');res=child(r,'resolution');assert res[1]=='mm';factor=float(res[2]);out=[]
 for net in children(child(r,'network_out'),'net'):
  name=net[1]
  for wire in children(net,'wire'):
   q=child(wire,'path');layer=q[1];width=float(q[2])/factor;nums=[float(v)/factor for v in q[3:]];pts=[[nums[i],-nums[i+1]]for i in range(0,len(nums),2)]
   for s,e in zip(pts,pts[1:]):out.append({'kind':'track','logical_net':name,'layer':layer,'width':width,'start':s,'end':e})
  for via in children(net,'via'):
   assert via[1]=='VIA_450_200';out.append({'kind':'via','logical_net':name,'xy':[float(via[2])/factor,-float(via[3])/factor],'width':.45,'drill':.20,'layers':['F.Cu','B.Cu']})
 return out

def nm(v):return round(v*1e6)
def key(o,logical=True):
 name=o.get('logical_net',o.get('net'))
 if o['kind']=='track':return('track',name,o['layer'],nm(o['width']),*sorted((tuple(map(nm,o['start'])),tuple(map(nm,o['end'])))))
 return('via',name,*map(nm,o['xy']),nm(o['width']),nm(o['drill']))
def from_snapshot(s):
 out=[]
 for o in s['routes']:
  if o['fixed']=='SYSTEM_FIXED':continue
  assert len(o['nets'])==1
  if o['kind']=='track':
   for a,b in zip(o['points'],o['points'][1:]):out.append({'kind':'track','logical_net':o['nets'][0],'layer':o['layer'],'width':o['width'],'start':[round(v,5)for v in a],'end':[round(v,5)for v in b]})
  else:out.append({'kind':'via','logical_net':o['nets'][0],'xy':[round(v,5)for v in o['xy']],'width':o['diameter'],'drill':o['drill']})
 return out

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--model',type=Path,required=True);ap.add_argument('--session',type=Path,required=True);ap.add_argument('--engine-report',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);ap.add_argument('--preserve-unaffected-fills',action='store_true',help='Require add-only outer-layer tracks on layers without copper zones; preserve every saved fill exactly.');a=ap.parse_args();m=json.loads(a.model.read_text());source=Path(m['physical_board']);assert sha(source)==m['board_sha256'];report=json.loads(a.engine_report.read_text());assert report['model_sha256']==sha(a.model)
 ses=ses_routes(a.session);assert collections.Counter(map(key,ses))==collections.Counter(map(key,from_snapshot(report))),'SES differs from actual engine geometry'
 aliases=m['aliases'];allowed=set(m['ordinary_nets']);assert all(aliases[r['logical_net']]in allowed for r in ses)
 b=p.LoadBoard(str(source));before=export(source);source_by_uuid={t.m_Uuid.AsString():t for t in b.GetTracks()};mutable=set(m.get('mutable_source_ids',[]));source_routes={o['uuid']:o for o in before['objects']if o['kind']!='pad'};old={}
 for uid in mutable:
  o=source_routes[uid];q=dict(o);q['logical_net']=m['source_logical_nets'][uid];q['layer']=next(iter(o['copper']));q['drill']=o['drill']['width']if o['drill']else None;old[uid]=q
 kept,new_routes=reconcile(ses,old);seen=set(kept);added=[];held=[];route_map={uid:old[uid]['logical_net']for uid in kept}
 if a.preserve_unaffected_fills:
  assert seen==mutable,'Fill preservation requires every existing route unchanged'
  assert all(r['kind']=='track' and r['layer'] in {'F.Cu','B.Cu'} for r in new_routes),'Fill preservation requires only outer-layer tracks and no new drills'
  changed_layers={r['layer'] for r in new_routes}
  assert not any(not z['rule'] and changed_layers.intersection(z['layers']) for z in before['zones']),'Changed layer contains a copper zone requiring refill'
 for r in new_routes:
  if r['kind']=='track':
   assert r['layer']in m['routable_layers'];assert nm(r['width'])==127000;t=p.PCB_TRACK(b);t.SetStart(p.VECTOR2I(*map(nm,r['start'])));t.SetEnd(p.VECTOR2I(*map(nm,r['end'])));t.SetWidth(nm(r['width']));t.SetLayer(b.GetLayerID(r['layer']))
  else:
   t=p.PCB_VIA(b);t.SetPosition(p.VECTOR2I(*map(nm,r['xy'])));t.SetWidth(450000);t.SetDrill(200000);t.SetViaType(p.VIATYPE_THROUGH);t.SetLayerPair(p.F_Cu,p.B_Cu);t.SetFrontTentingMode(p.TENTING_MODE_TENTED);t.SetBackTentingMode(p.TENTING_MODE_TENTED)
  t.SetNet(b.FindNet(aliases[r['logical_net']]));b.Add(t);held.append(t);added.append(t.m_Uuid.AsString());route_map[t.m_Uuid.AsString()]=r['logical_net']
 removed=sorted(mutable-seen)
 for uid in removed:b.Remove(source_by_uuid[uid])
 def verify_intended_route_nets(board):
  current={t.m_Uuid.AsString():t.GetNetname() for t in board.GetTracks()}
  assert all(current.get(uid)==aliases[logical] for uid,logical in route_map.items()),'Native connectivity reassigned an intended route net'
 verify_intended_route_nets(b)
 a.out.parent.mkdir(parents=True,exist_ok=True)
 for ext in ['.kicad_pro','.kicad_dru']:
  config=source.with_suffix(ext)
  if config.exists():shutil.copyfile(config,a.out.with_suffix(ext))
 regenerated=set(m.get('regenerable_reference_zones',[]))
 refill=bool(regenerated and (added or removed) and not a.preserve_unaffected_fills)
 if refill:
  project=a.out.with_suffix('.kicad_pro').resolve();assert project.exists(),'Native refill requires the paired source project'
  # KiCad's settings manager needs the actual destination board/project pair.
  # Reopen our newly saved copy before attaching that project's settings.
  p.SaveBoard(str(a.out.resolve()),b);b=p.LoadBoard(str(a.out.resolve()));verify_intended_route_nets(b)
  sm=p.GetSettingsManager();assert sm.LoadProject(str(project)),'Native project load failed';b.SetProject(sm.GetProject(str(project)));b.SynchronizeNetsAndNetClasses(False);b.BuildConnectivity();assert p.ZONE_FILLER(b).Fill(b.Zones()),'Native reference plane refill failed'
  verify_intended_route_nets(b)
 p.SaveBoard(str(a.out),b);after=export(a.out);after_by_uuid={o['uuid']:o for o in after['objects']};fixed=[o for o in before['objects']if o['uuid']not in mutable]
 assert all(after_by_uuid.get(o['uuid'])==o for o in fixed),'Fixed native object identity/geometry changed'
 def source_zone_contract(z):
  return {k:v for k,v in z.items() if not(refill and z['uuid']in regenerated and k in {'filled','fill_representation'})}
 assert before['footprints']==after['footprints'] and list(map(source_zone_contract,before['zones']))==list(map(source_zone_contract,after['zones'])) and before['edge_cuts']==after['edge_cuts'] and before['copper_layers']==after['copper_layers'],'Native non-route geometry changed'
 if refill:
  assert all(z['net']=='GND' and set(z['layers'])<={'In1.Cu','In4.Cu'} and all(z['filled'].get(l) for l in z['layers']) for z in after['zones'] if z['uuid']in regenerated),'Reference refill removed a plane or changed its ownership'
 if not ses and not mutable:assert before['objects']==after['objects'],'Zero import changed native copper'
 actual=[]
 for uid,logical in route_map.items():
  o=after_by_uuid[uid];assert o['net']==aliases[logical],'Native refill/connectivity reassigned an intended route net';q=dict(o);q['logical_net']=logical;q['layer']=next(iter(o['copper']));q['drill']=o['drill']['width']if o['drill']else None;actual.append(q)
 assert route_union(actual)==route_union(ses),'Imported copper differs from independent SES union'
 result={'passed':True,'source_sha256':m['board_sha256'],'output_sha256':sha(a.out),'session_sha256':sha(a.session),'model_sha256':sha(a.model),'fixed_objects_preserved':len(fixed),'unchanged_routes_preserved':len(kept),'routes_added':len(added),'routes_removed':len(removed),'footprints_preserved':len(before['footprints']),'exact_native_geometry_preserved':True,'ses_engine_native_geometry_equal':True,'logical_route_map':route_map}
 handoff_map={uid:logical for uid,logical in m['source_logical_nets'].items() if uid in after_by_uuid and aliases[logical] in allowed};handoff_map.update(route_map)
 logical_handoff={'schema':'f722-logical-route-map/v1','board_sha256':result['output_sha256'],'source_sha256':m['board_sha256'],'model_sha256':sha(a.model),'logical_route_map':handoff_map}
 map_path=a.out.with_suffix('.logical-route-map.json');map_path.write_text(json.dumps(logical_handoff,indent=2)+'\n')
 result.update({'logical_route_map':handoff_map,'logical_route_map_artifact':map_path.name,'synthetic_import_fixture':report.get('synthetic_import_fixture',False),'exact_native_geometry_preserved':not refill,'exact_fixed_native_objects_preserved':True,'zone_identity_outline_and_rules_preserved':True,'reference_plane_refill_performed':refill,'regenerable_reference_zones':sorted(regenerated),'post_refill_reference_validation_required':refill,'preserve_unaffected_fills_requested':a.preserve_unaffected_fills,'unaffected_fill_preconditions_verified':a.preserve_unaffected_fills})
 a.out.with_suffix('.import.json').write_text(json.dumps(result,indent=2)+'\n');a.out.with_suffix('.native.json').write_text(json.dumps(after,separators=(',',':'))+'\n');print(json.dumps({k:v for k,v in result.items()if k!='logical_route_map'}))
if __name__=='__main__':main()
