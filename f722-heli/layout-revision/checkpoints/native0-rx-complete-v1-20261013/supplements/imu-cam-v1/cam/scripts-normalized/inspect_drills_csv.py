import ast,collections,csv,gzip,hashlib,json,math,re,resource
from decimal import Decimal
from pathlib import Path
resource.setrlimit(resource.RLIMIT_AS,(768*1024**2,)*2)
P=Path('@CAM@');D=Path('@NATIVE_INPUTS@');OUT=Path(__file__).resolve().parent
E=Path('@ORIGINAL_EXPORTER@')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def readcsv(p):return list(csv.DictReader(p.open()))
def require(x,m):
 if not x:raise ValueError(m)
class GateError(Exception):pass
exec(compile(ast.Module(body=[x for x in ast.parse(E.read_text()).body if isinstance(x,ast.FunctionDef) and x.name in ['parse_drill','drill_key','parse_gerber','xykey']],type_ignores=[]),str(E),'exec'))
boardsha=sha(D/'diagnostic-board/f722-heli.kicad_pcb');assert boardsha=='84229c571433bd72d410fb18d02cffa3a380c00a87fbe1270e3a73b63f8dd6cd'
data=json.load(gzip.open(D/'after.native.json.gz','rt'));assert data['board_sha256']==boardsha;fps={f['ref']:f for f in data['footprints']};parts=json.loads((D/'diagnostic-board/parts.json').read_text());expected=[]
for o in data['objects']:
 if not o.get('drill'):continue
 dr=o['drill'];a=dr['start'];b=dr['end'];pl='PTH' if o.get('plated') else 'NPTH'
 item=(pl,'round',dr['width'],a[0],-a[1]) if a==b else (pl,'slot',dr['width'],*sorted([(a[0],-a[1]),(b[0],-b[1])])[0])
 if a!=b:
  ends=sorted([(a[0],-a[1]),(b[0],-b[1])]);item=(pl,'slot',dr['width'],*ends[0],*ends[1])
 expected.append((item,{'uuid':o['uuid'],'kind':o['kind'],'ref':o.get('ref'),'number':o.get('number'),'source_center':o['xy']}))
result={'schema':'f722-internal-cam-drill-csv-diagnostic/v1','source_pcb_sha256':boardsha,'formal_exporter_original_failure_retained':True,'finalrelease':False,'drills':{},'input_files':{str(p):sha(p) for p in sorted(P.rglob('*')) if p.is_file()}}
for pl in ['PTH','NPTH']:
 actual,tools=parse_drill(P/'drill'/f'f722-heli-{pl}.drl',pl);src=[e for e in expected if e[0][0]==pl];matches=[];used=set();maxaxis=Decimal(0);maxeuclid=0;rounding=[]
 for a in actual:
  if a[1]=='slot':ends=sorted([a[3:5],a[5:7]]);a=(*a[:3],*ends[0],*ends[1])
  candidates=[]
  for i,(e,owner) in enumerate(src):
   if a[:3]!=e[:3]:continue
   ds=[Decimal(str(x))-Decimal(str(y)) for x,y in zip(a[3:],e[3:])]
   if all(abs(v)<=Decimal('0.0005') for v in ds):candidates.append((i,e,owner,ds))
  assert len(candidates)==1,(a,candidates)
  i,e,owner,ds=candidates[0];assert i not in used;used.add(i);maxaxis=max(maxaxis,*map(abs,ds));maxeuclid=max(maxeuclid,math.sqrt(sum(float(v)**2 for v in ds[:2])))
  row={'actual_export_feature':a,'exact_native_feature':e,**owner,'coordinate_delta_mm':[str(v) for v in ds]};matches.append(row)
  if drill_key(a)!=drill_key(e):rounding.append(row)
 assert len(used)==len(src)==len(actual)
 result['drills'][pl]={'native_count':len(src),'actual_count':len(actual),'unique_one_to_one_match_at_declared_precision':True,'per_coordinate_acceptance_bound_mm':'0.0005 (half of actual 0.001 mm output grid)','maximum_absolute_coordinate_delta_mm':str(maxaxis),'maximum_center_vector_delta_mm':maxeuclid,'diameters_exact':True,'round_count':sum(x[0][1]=='round' for x in src),'slot_count':sum(x[0][1]=='slot' for x in src),'tools_mm':tools,'original_round_key_mismatches':rounding,'slot_records':[r for r in matches if r['actual_export_feature'][1]=='slot'],'all_matches':matches}
raw=readcsv(P/'assembly/native-all-pos.csv');cpl=readcsv(P/'assembly/jlc-cpl-SMT-HELD.csv');bom=readcsv(P/'assembly/jlc-bom-SMT-HELD.csv');proc=readcsv(P/'assembly/procurement-full-per-reference.csv');manual={f'J{i}' for i in range(2,9)};bare={f'TP{i}' for i in range(1,6)};pop=set(fps)-bare;smt=pop-manual
assert len(raw)==len(pop)==151 and {r['Ref'] for r in raw}==pop
for row in raw:
 f=fps[row['Ref']];assert row['Val']==f['value'] and row['Package']==f['fpid'].split(':',1)[1];assert row['Side']==('top' if f['side']=='F.Cu' else 'bottom');assert all(abs(float(row[k])-v)<=.0000011 for k,v in [('PosX',f['xy'][0]),('PosY',-f['xy'][1]),('Rot',f['angle'])])
assert len(cpl)==144 and {r['Designator'] for r in cpl}==smt and collections.Counter(r['Layer'] for r in cpl)=={'top':65,'bottom':79}
rawmap={r['Ref']:r for r in raw}
for row in cpl:
 r=rawmap[row['Designator']];assert all(row[k]==r[v] for k,v in [('Mid X','PosX'),('Mid Y','PosY'),('Rotation','Rot'),('Layer','Side')])
refs=[]
for row in bom:
 for ref in row['Designator'].split(','):
  refs.append(ref);assert row['Comment']==fps[ref]['value'] and row['Footprint']==fps[ref]['fpid'] and row['LCSC Part #']==parts[ref]['jlcpcb_lcsc_code']
assert collections.Counter(refs)==collections.Counter(smt)
assert len(proc)==151 and {r['Reference'] for r in proc}==pop
for row in proc:
 ref=row['Reference'];p=parts[ref];assert row['Manufacturer']==p['manufacturer'] and row['MPN']==p['mpn'] and row['LCSC Part #']==(p.get('jlcpcb_lcsc_code') or '') and row['Footprint']==p['proposed_footprint']
assert len(readcsv(P/'assembly/placement-manual-THT.csv'))==7 and len(readcsv(P/'assembly/excluded-board-features.csv'))==5
result['assembly']={'all151_native_poses_values_packages_sides_exact':True,'all144_CPL_native_XY_angle_side_exact':True,'SMT_BOM_CPL_reference_multisets_exact':True,'all151_procurement_manufacturer_MPN_LCSC_package_joins_exact':True,'csv_sets':len(list((P/'assembly').glob('*.csv'))),'procurement_groups':len(readcsv(P/'assembly/procurement-full-grouped.csv')),'SMT_BOM_groups':len(bom),'moved_CPL':{r['Designator']:r for r in cpl if r['Designator'] in ['U15','R34','R35']},'factory_rotation_corrections_applied':False,'factory_part_model_orientation_acceptance':False}
result['limits']=['This diagnoses original verifier quantization; its failure is preserved and no final exporter code or gate is altered.','Unique full-census matching bounds actual coordinate quantization, not fabrication/drill/process tolerances.','No 2D previews were reached in the stopped original run.','Native/CPL orientation equality is not supplier-model polarity approval.']
(OUT/'DRILL-CSV-DIAGNOSTIC.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
print(json.dumps({'drills':{p:{k:v for k,v in d.items() if k not in ['all_matches','slot_records','original_round_key_mismatches']} for p,d in result['drills'].items()},'assembly':result['assembly']},indent=2))
