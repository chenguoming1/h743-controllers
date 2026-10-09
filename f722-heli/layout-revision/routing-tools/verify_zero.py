#!/usr/bin/env python3
"""Independent geometry/role/partition audit of the actual loaded engine model."""
import argparse,collections,hashlib,json,sys
from pathlib import Path
from shapely.geometry import Polygon
from shapely import unary_union
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'native-tools' if (ROOT/'native-tools').exists() else ROOT.parent/'protection-checks'))
from check_protection_paths import make_graph

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def geometry(ps):return unary_union([Polygon(p['outer'],p.get('holes',[]))for p in ps])
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--model',type=Path,required=True);ap.add_argument('--engine',type=Path,required=True);ap.add_argument('--imported',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();m=json.loads(a.model.read_text());e=json.loads(a.engine.read_text());n=json.loads(Path(m['physical_native']).read_text());im=json.loads(a.imported.read_text());errors=[]
 if e['model_sha256']!=sha(a.model):errors.append('Engine model hash differs')
 if e['passes_requested']!=0:errors.append('Nonzero pass run')
 if n['board_sha256']!=m['board_sha256']:errors.append('Native source hash differs')
 expected=collections.defaultdict(list);native_shapes={}
 for g in m['guards']:
  kind='via_guard'if g['kind']=='via'else'foreign_guard';k=(kind,g['label'],g['layer'],tuple(sorted(g['owners'])));expected[k]+=g['engine_polygons'];native_shapes[k]=('contains',g['polygons'])
 for c in m['contacts']:
  k=('contact',c['uuid']+'|'+c['key'],c['layer'],(c['net'],));expected[k]+=c['engine_polygons'];native_shapes[k]=('inside',c['polygons'])
 actual=collections.defaultdict(list)
 for c in e['areas']:
  k=(c['kind'],(c['uuid']+'|' if c['kind']=='contact'else'')+c['label'],c['layer'],tuple(sorted(c['nets'])));actual[k].append({'outer':c['outer'],'holes':[]})
 if set(expected)!=set(actual):errors.append({'model_area_keys_missing':list(set(expected)-set(actual)),'model_area_keys_extra':list(set(actual)-set(expected))})
 worst=0.;worstkey=None
 for k in set(expected)&set(actual):
  eg,ag=geometry(expected[k]),geometry(actual[k]);diff=eg.symmetric_difference(ag).area
  if diff>worst:worst=diff;worstkey=k
  if diff>1e-10:errors.append({'engine_geometry_diff':k,'mm2':diff})
  direction,raw=native_shapes[k];ng=geometry(raw);leak=ng.difference(ag).area if direction=='contains'else ag.difference(ng).area
  if leak>1e-10:errors.append({'native_conservative_containment_failed':k,'direction':direction,'mm2':leak})
 roles=collections.defaultdict(set)
 for c in m['contacts']:roles[c['net']].add(c['uuid'])
 expected_part=[]
 for net,ids in roles.items():
  obs=[o for o in n['objects']if o['uuid']in ids or (o['kind']!='pad'and m['source_logical_nets'].get(o['uuid'],o['net'])==net)]+[z for z in m.get('fixed_zones',[])if z['net']==net]
  for g in make_graph(obs):
   values=tuple(sorted({o['object']['uuid']+':'+o['layer']for o in g if o['object']['kind']=='pad'}))
   if values:expected_part.append((net,values))
 actual_part=[(p['net'],tuple(sorted(p['contacts'])))for p in e['contact_partitions']]
 if collections.Counter(expected_part)!=collections.Counter(actual_part):errors.append({'native_partition_missing':list((collections.Counter(expected_part)-collections.Counter(actual_part)).elements()),'native_partition_extra':list((collections.Counter(actual_part)-collections.Counter(expected_part)).elements())})
 if not im['passed']or not im['exact_native_geometry_preserved']or not im['ses_engine_native_geometry_equal']:errors.append('Native import failed')
 result={'passed':not errors,'board_sha256':m['board_sha256'],'model_sha256':sha(a.model),'engine_sha256':sha(a.engine),'ordinary_nets':len(m['ordinary_nets']),'logical_ordinary_nets':sum(p in m['ordinary_nets']for p in m['aliases'].values()),'source_pad_uuids':len([o for o in n['objects']if o['kind']=='pad']),'engine_area_keys':len(actual),'native_contact_partitions':len(expected_part),'maximum_engine_geometry_diff_mm2':worst,'maximum_engine_geometry_diff_key':worstkey,'physical_object_identity_exact':im['exact_native_geometry_preserved'],'planning_geometry':m['planning_geometry'],'errors':errors}
 a.out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items()if k!='errors'}));print('errors',len(errors));sys.exit(bool(errors))
if __name__=='__main__':main()
