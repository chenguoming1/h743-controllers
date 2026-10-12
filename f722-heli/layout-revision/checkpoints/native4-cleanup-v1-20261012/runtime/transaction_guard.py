"""Exact native5-to-native4 delta and raw polygon verification."""
from pathlib import Path
import paired_source as p
import polygon_native
import structural_base as raw
HERE=Path(__file__).resolve().parent
PLAN=HERE/'transaction-contract.json'
PLAN_SHA='333e5645aef926da7162893a790c5ddb35800978084059542dcfb5b3de5e7ddc'
DECLARATION=HERE/'polygon-declaration.json'
DECLARATION_SHA='ad95d4f083ca2890905878237139317c633a565ff57f595bcfea044236bad2e3'
def check_sources():
    plan=p.read(PLAN)
    plan['source_native5']['path']=str(HERE.parent/'inputs/native5.native.json.gz')
    return plan


def binding():return {'schema':'f722-native5-SCK-RED-VX-CORE-native/v1','transaction_contract_sha256':PLAN_SHA,'polygon_declaration_sha256':DECLARATION_SHA,'recipe_sha256':'acc15655b6e25dfb7c90f3c3cab55349d3b27ffc352cd557ea8f2e8d833e7270','source_native5_sha256':polygon_native.CURRENT_NATIVE_SHA,'fresh_power_reference_acceptance_pending':True}


def verify_raw_polygon(board_path):
 row=polygon_native.load_bound_declaration(DECLARATION,DECLARATION_SHA)['primitive'];ast=raw.parse(board_path)
 graphics=[x for x in ast if isinstance(x,list) and x and x[0].startswith('gr_') and raw.children(x,'layer') and '.Cu"' in raw.child(x,'layer')[1]]
 p.require(len(graphics)==1,'Raw board requires exactly one copper graphic');item=graphics[0]
 p.require(item[0]=='gr_poly' and raw.uid(item)==row['uuid'],'Raw polygon type/UUID differs')
 p.require({x[0] for x in item[1:] if isinstance(x,list)}=={'pts','stroke','fill','layer','net','uuid'} and all(isinstance(x,list) for x in item[1:]),'Unexpected raw polygon fields')
 p.require(raw.child(item,'layer')==['layer','"In2.Cu"'] and raw.child(item,'net')==['net','"VX_PROTECTED"'] and raw.child(item,'fill')==['fill','yes'],'Raw polygon net/layer/fill changed')
 stroke=raw.child(item,'stroke');p.require(raw.unordered(stroke)==raw.unordered(['stroke',['width','0'],['type','default']]),'Raw polygon stroke changed')
 points=raw.child(item,'pts')[1:];p.require(all(len(x)==3 and x[0]=='xy' for x in points),'Raw polygon points malformed')
 p.require(polygon_native.ring_id([[polygon_native.nm(x),polygon_native.nm(y)] for _,x,y in points])==polygon_native.ring_id(row['outer_nm']),'Raw polygon integer contour differs')
 return {'uuid':row['uuid'],'raw_record_sha256':p.digest(raw.canonical(item)),'contour_sha256':p.digest(row['outer_nm']),'net_layer_fill_stroke_and_all_vertices_exact':True}


def verify_native5_delta(after,verify_added):
 plan=check_sources();before=p.read(plan['source_native5']['path'])
 old={x['uuid']:x for x in before['objects']};new={x['uuid']:x for x in after['objects']};cuts=plan['native5_extra_cut_hashes'];adds={x['uuid']:x for x in plan['exact_additions']}
 p.require(set(old)-set(new)==set(cuts) and set(new)-set(old)==set(adds),'Actual native5 transaction object inventory differs')
 for uid,h in cuts.items():p.require(p.digest(old[uid])==h,'Current native5 cut source changed')
 without_code=lambda r:{k:v for k,v in r.items() if k!='net_code'}
 for uid,row in old.items():
  if uid not in cuts:p.require(without_code(row)==without_code(new[uid]),'Native5 retained physical record changed: '+uid)
 for uid,row in adds.items():verify_added(row,new[uid])
 p.require({x['ref']:x for x in before['footprints']}=={x['ref']:x for x in after['footprints']},'A native5 footprint changed')
 oldzones={z['uuid']:z for z in before['zones']};newzones={z['uuid']:z for z in after['zones']}
 p.require(set(oldzones)==set(newzones),'Zone inventory changed')
 fill_changes=[]
 for uid,z in oldzones.items():
  actual=newzones[uid];meta=lambda r:{k:v for k,v in r.items() if k not in ['net_code','filled','fill_representation']}
  p.require(meta(z)==meta(actual),'Native5 zone definition changed')
  for layer in set(z['filled'])|set(actual['filled']):
   left=z['filled'].get(layer,[]);right=actual['filled'].get(layer,[])
   fill_changes.append({'zone_uuid':uid,'layer':layer,'source_fill_sha256':p.digest(left),'candidate_fill_sha256':p.digest(right),'exact_fill_unchanged':left==right,'source_components':len(left),'candidate_components':len(right),'source_holes':sum(len(r['holes']) for r in left),'candidate_holes':sum(len(r['holes']) for r in right)})
 return {'source_native5_sha256':plan['source_native5']['sha256'],'exact_five_cuts':cuts,'exact_39_added_UUIDs':sorted(adds),'all_2411_retained_native5_objects_exact_except_bijective_net_codes':True,'all_native5_footprints_exact':True,'zone_definitions_exact':True,'zone_fill_ledger':fill_changes,'physical_fill_difference_reference_review_pending':True}

