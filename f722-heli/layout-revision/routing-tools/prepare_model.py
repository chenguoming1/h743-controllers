#!/usr/bin/env python3
"""Build a source-bound local routing model from KiCad's independent native export.
Physical copper and planning contacts are deliberately separate. Every mask/drill
exclusion is foreign-net-independent, and logical protection branches never merge.
"""
import argparse,json,hashlib,collections,math,sys
from pathlib import Path
from shapely.geometry import Polygon,MultiPolygon,GeometryCollection,LineString,box
from shapely import unary_union,constrained_delaunay_triangles,set_precision
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'native-tools' if (ROOT/'native-tools').exists() else ROOT.parent/'protection-checks'))
from check_protection_paths import make_graph
LAYERS=['F.Cu','In1.Cu','In2.Cu','In3.Cu','In4.Cu','B.Cu']
POWER=set('EFUSE_DVDT GND VX_RAW VX_PROTECTED +5V_BEC +5V_PERIPH CORE_BUCK_IN +3V3_CORE +3V3_DSM USB_VBUS_RAW USB_LIMITED ABC_L1 ABC_L2 CORE_SW ABC_FB ABC_VAUX'.split())
CRITICAL=set('HSE_IN HSE_OUT HSE_XTAL_OUT VCAP VCAP_CAP IMU_CS IMU_INT IMU_MISO IMU_MOSI IMU_SCK USB_N USB_P USB_CC1 USB_CC2 +3V3_ANALOG +3V3_IMU'.split())
POWER_REFS={f'U{i}'for i in range(5,12)}|{'L1','L2','D8','C20'}|{f'C{i}'for i in range(53,76)}|{f'R{i}'for i in range(49,72)}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def pg(p):return Polygon(p['outer'],p.get('holes',[]))
def geom(ps):return unary_union([pg(p)for p in ps])
def parts(g):
 if g.is_empty:return []
 if g.geom_type=='Polygon':return [g]
 return [q for x in g.geoms for q in parts(x)]
def polys(g):return [{'outer':[[round(x,6),round(y,6)]for x,y in p.exterior.coords[:-1]],'holes':[[[round(x,6),round(y,6)]for x,y in r.coords[:-1]]for r in p.interiors]}for p in parts(g)]
def rounded(g):return geom(polys(g))
def outward(g,d):
 # Inscribed GEOS buffer widened by its maximum chord sagitta plus 2 nm.
 return rounded(g.buffer((d+0.000002)/math.cos(math.pi/128),quad_segs=32))
_cache={}
def engine_polys(ps,inside=False):
 cachekey=(inside,json.dumps(ps,separators=(',',':')))
 if cachekey in _cache:return _cache[cachekey]
 g=geom(ps)
 quant=set_precision(g.buffer(-.00002 if inside else .00002,quad_segs=4),.00001)
 if quant.geom_type=='Polygon' and not quant.interiors and quant.convex_hull.area-quant.area<1e-6:
  candidate=quant.convex_hull
  if not inside or candidate.difference(g).area<1e-12:quant=candidate
 if inside:
  assert quant.difference(g).area<1e-12 and not quant.is_empty
 else:assert g.difference(quant).area<1e-12
 result=polys(quant);_cache[cachekey]=result;return result
def convex(ps):
 result=[]
 for q in ps:
  g=pg(q)
  if len(g.interiors)==0 and g.symmetric_difference(g.convex_hull).area<1e-14:result.append(q['outer']);continue
  ts=list(constrained_delaunay_triangles(g).geoms)
  assert unary_union(ts).symmetric_difference(g).area<1e-10
  result.extend([list(t.exterior.coords)[:-1]for t in ts])
 return result
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--native',type=Path,required=True);ap.add_argument('--board',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);ap.add_argument('--support-ready',action='store_true');ap.add_argument('--fixed-ids',type=Path);ap.add_argument('--logical-route-map',type=Path);a=ap.parse_args();a.out.mkdir(parents=True,exist_ok=True)
 n=json.loads(a.native.read_text());assert n['board_sha256']==sha(a.board);assert n['copper_layers']==LAYERS
 objs=n['objects'];pads=[o for o in objs if o['kind']=='pad'];bykey=collections.defaultdict(list)
 for o in pads:bykey[o['key']].append(o)
 nets=collections.defaultdict(list)
 for o in pads:
  if o['net']:nets[o['net']].append(o)
 owned_path=(ROOT/'config/power-owned-nets.json' if (ROOT/'config/power-owned-nets.json').exists() else ROOT.parent/'power-routing/owned-nets.json');power_owned=set(json.loads(owned_path.read_text())['nets'])if owned_path.exists()else POWER
 powerlocal={net for net,os in nets.items()if all(o['ref']in POWER_REFS for o in os)}
 ordinary=sorted(net for net in nets if net not in power_owned|CRITICAL|powerlocal and len(nets[net])>=2 and not net.startswith('unconnected-'))
 proof=(ROOT/'config/published-clamp-proof.json' if (ROOT/'config/published-clamp-proof.json').exists() else ROOT.parent/'repo/f722-heli/evidence/clamp-first-proof.json');checks=json.loads(proof.read_text())['checks'];chains={}
 for c in checks[:14]:
  if c['net']in ordinary:
   clamp=c['clamp']
   if clamp.startswith('U13.'):
    current=[o['key']for o in nets[c['net']]if o['ref']=='U13'];assert len(current)==1;clamp=current[0]
   chains[c['net']]=[c['source'],clamp,c['target']]
 for c in checks[14:]:
  if c['net']in chains:chains[c['net']].insert(1,c['clamp'])
 chains.update({'RPM_HV':['R25.2','U16.1','Q1.3'],'SBUS_HV':['R26.2','U16.2','Q2.3']})
 roles={};aliases={};contact_aliases={}
 for net,os in nets.items():
  if net in chains:
   chain=chains[net];assert set(chain)=={o['key']for o in os},(net,chain,[o['key']for o in os])
   assert all(len(bykey[k])==1 for k in chain)
   names=[net+'::P'+str(i)for i in range(len(chain)-1)]
   roles[net]={'kind':'protected_chain','sequence':chain,'branches':[{'logical_net':names[i],'terminals':chain[i:i+2]}for i in range(len(names))]}
   for name in names:aliases[name]=net
   for i,k in enumerate(chain):contact_aliases[bykey[k][0]['uuid']]=names[max(0,i-1):min(len(names),i+1)]
  else:
   aliases[net]=net;roles[net]={'kind':'ordinary'if net in ordinary else 'fixed_domain','terminals':[o['uuid']for o in os]}
   for o in os:contact_aliases[o['uuid']]=[net]
 fixed_ids=set(json.loads(a.fixed_ids.read_text()))if a.fixed_ids else set()
 route_map=json.loads(a.logical_route_map.read_text())if a.logical_route_map else {}
 if 'logical_route_map'in route_map:route_map=route_map['logical_route_map']
 fixed=[];mutable=[];source_logical={}
 for o in objs:
  if o['kind']=='pad':continue
  logical=route_map.get(o['uuid'],o['net'])
  if o['net']in chains:assert o['uuid']in route_map,'Protected source copper requires explicit logical ownership'
  assert aliases.get(logical)==o['net'];source_logical[o['uuid']]=logical
  (mutable if o['net']in ordinary and o['uuid']not in fixed_ids else fixed).append(o)
 fixed_zones=[]
 for z in n['zones']:
  if not z['rule']and z['filled']:
   assert z['net']not in ordinary,'Ordinary signal fills require explicit role/model review'
   fixed_zones.append({'uuid':z['uuid'],'kind':'zone','net':z['net'],'copper':z['filled'],'plated':False,'drill':None})
 groups={}
 for alias,physical in aliases.items():
  subset=[o for o in pads if alias in contact_aliases.get(o['uuid'],[])]+[o for o in fixed if source_logical[o['uuid']]==alias]+[z for z in fixed_zones if z['net']==alias]
  for group in make_graph(subset):
   labels=sorted({(v['object']['uuid'],v['layer'])for v in group if v['object']['kind']=='pad'});group_id=hashlib.sha256(json.dumps([alias,labels]).encode()).hexdigest()
   for uid,l in labels:
    assert (alias,uid,l)not in groups,'Disconnected custom-pad island requires separate contacts'
    groups[alias,uid,l]=(group_id,len(labels)>1)
 guards=[];contacts=[]
 def guard(label,layer,ps,kind='foreign',owners=(),clearance=.127):
  if ps:guards.append({'label':label,'layer':layer,'kind':kind,'owners':list(owners),'clearance':clearance,'polygons':ps,'engine_polygons':engine_polys(ps),'convex':convex(engine_polys(ps))})
 for o in pads:
  owners=contact_aliases.get(o['uuid'],[])
  for l,ps in o['copper'].items():
   guard(o['uuid']+':copper',l,ps,owners=owners)
   for alias in owners:
    contacts.append({'uuid':o['uuid'],'key':o['key'],'net':alias,'physical_net':o['net'],'layer':l,'plated':o['plated'],'native_group':groups[alias,o['uuid'],l][0],'native_group_multi':groups[alias,o['uuid'],l][1],'owners':owners,'polygons':o['inside'][l],'engine_polygons':engine_polys(o['inside'][l],True),'convex':convex(engine_polys(o['inside'][l],True))})
  if o['smd']:
   for face,m in o['mask'].items():
    # Via radius .225, drill radius .100: .075 padding makes .20 drill/mask.
    ps=polys(outward(geom(m['polygons']),.075))
    guard(o['uuid']+':mask:'+face,'F.Cu'if face=='F.Mask'else'B.Cu',ps,'via',(),0)
  if o['drill']:
   g=geom(o['drill']['outside'])
   # Via copper radius .225 vs drill radius .100, so .125 reserve gives .25 drill gap.
   for l in LAYERS:guard(o['uuid']+':drill',l,polys(outward(g,.125)),'via',(),0)
   if o['npth']:
    for l in LAYERS:guard(o['uuid']+':npth',l,polys(outward(g,.254)),'foreign',(),0)
 for z in n['zones']:
  if z['rule']:
   for l in z['layers']:
    if z['forbid']['tracks'] or z['forbid']['copper']:guard(z['uuid']+':rule',l,z['outline'],'foreign',(),0)
    elif z['forbid']['vias']:guard(z['uuid']+':rule',l,z['outline'],'via',(),0)
  else:
   for l,ps in z['filled'].items():guard(z['uuid']+':fill',l,ps,owners=[a for a,p in aliases.items()if p==z['net']])
 # Explicit board-edge reserve outside the physical outline, including NPTH holes.
 region=geom(n['outline_with_npth']['polygons']);ext=box(*[region.bounds[0]-1,region.bounds[1]-1,region.bounds[2]+1,region.bounds[3]+1])
 edge=ext.difference(region.buffer(-.254,join_style='mitre'))
 for l in LAYERS:guard('board-edge',l,polys(edge),'foreign',(),0)
 for o in fixed:
  for l,ps in o['copper'].items():guard(o['uuid']+':fixed',l,ps,owners=[source_logical[o['uuid']]])
  if o['kind']=='via':
   for l in LAYERS:guard(o['uuid']+':drill',l,polys(outward(geom(o['drill']['outside']),.125)),'via',(),0)
 model={'schema':'f722-ordinary-model/v1','board_sha256':n['board_sha256'],'native_sha256':sha(a.native),'proof_source_sha256':sha(proof),'adapter_sources':{str(p.relative_to(ROOT)):sha(p)for p in sorted((ROOT/'src').rglob('*.java'))},'layers':LAYERS,'routable_layers':['F.Cu','In2.Cu','In3.Cu','B.Cu'],'ordinary_nets':ordinary,'aliases':aliases,'roles':roles,'contacts':contacts,'guards':guards,'fixed_objects':fixed,'fixed_zones':fixed_zones,'mutable_source_ids':[o['uuid']for o in mutable],'source_logical_nets':source_logical,'rules':{'track_width':.127,'clearance':.127,'via_diameter':.45,'via_drill':.20,'drill_mask_gap':.20,'drill_drill_gap':.25,'edge_npth_gap':.254,'max_new_vias':None,'max_net_length':None},'planning_geometry':{'engine_grid_mm':.00001,'guard_pad_buffer_mm':.00002,'contact_inset_mm':.00002,'native_model_unchanged':True},'support_ready':a.support_ready,'physical_native':str(a.native.resolve()),'physical_board':str(a.board.resolve())}
 # DSN supplies topology/rules and exact fixed native tracks. Areas come from the hashed native model.
 q=lambda s:json.dumps(s)
 s=['(pcb "f722-local" (parser (string_quote ") (space_in_quoted_tokens on) (host_cad "KiCad") (host_version "10.0.6")) (resolution mm 100000) (unit mm)','(structure']
 for i,l in enumerate(LAYERS):s.append(f'(layer {l} (type signal) (property (index {i})))')
 for p in n['outline_with_npth']['polygons']:s.append('(boundary (polygon pcb 0 '+' '.join(f'{x:.6f} {-y:.6f}'for x,y in p['outer'])+'))')
 s+=['(via "VIA_450_200") (rule (width 0.127) (clearance 0.127)))','(placement)','(library (padstack "VIA_450_200"']
 for l in LAYERS:s.append(f'(shape (circle {l} 0.45))')
 s+=['(attach off))']
 via_stacks={}
 for o in fixed+mutable:
  if o['kind']!='via':continue
  assert o['via_type']==3 or o['top_layer']=='F.Cu'and o['bottom_layer']=='B.Cu','Review non-through source via'
  dims=tuple((l,o.get('width_by_layer',{}).get(l,o['width']))for l in LAYERS if l in o['copper'])
  key=(dims,o['drill']['width']);name='FIXED_VIA_'+hashlib.sha256(repr(key).encode()).hexdigest()[:12]
  if len(dims)==6 and all(abs(d-.45)<1e-9 for l,d in dims)and abs(o['drill']['width']-.20)<1e-9:name='VIA_450_200'
  via_stacks[o['uuid']]=name
  if name not in ''.join(s):
   s.append('(padstack '+q(name))
   for l,d in dims:s.append(f'(shape (circle {l} {d}))')
   s.append('(attach off))')
 s+=[')','(network']
 for alias in sorted(aliases):s.append('(net '+q(alias)+' (pins))')
 s+=['(class "ordinary" '+' '.join(q(a)for a,p in aliases.items()if p in ordinary)+' (circuit (use_via "VIA_450_200")) (rule (width 0.127) (clearance 0.127)))',')','(wiring']
 for o in fixed+mutable:
  logical=source_logical.get(o['uuid'],o['net']);route_type='fix'if o in fixed else'route'
  if o['kind']=='track':
   s.append('(wire (path '+next(iter(o['copper']))+' '+str(o['width'])+' '+' '.join(f'{x:.6f} {-y:.6f}'for x,y in [o['start'],o['end']])+') (net '+q(logical)+') (type '+route_type+'))')
  elif o['kind']=='via':
   s.append(f'(via {q(via_stacks[o["uuid"]])} {o["xy"][0]} {-o["xy"][1]} (net {q(logical)}) (type {route_type}))')
  else:raise RuntimeError('Unsupported fixed route geometry: '+o['kind'])
 s+=['))'];(a.out/'routing.dsn').write_text('\n'.join(s)+'\n');model['dsn_sha256']=sha(a.out/'routing.dsn');(a.out/'model.json').write_text(json.dumps(model,separators=(',',':'))+'\n')
 summary={'board_sha256':n['board_sha256'],'ordinary_nets':ordinary,'logical_nets':sum(p in ordinary for p in aliases.values()),'pad_objects':len(pads),'contacts':len(contacts),'guards':len(guards),'fixed_objects':len(fixed),'support_ready':a.support_ready,'protected_chains':chains};(a.out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary))
if __name__=='__main__':main()
