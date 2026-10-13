import ast,copy,hashlib,json,math
from decimal import Decimal
from pathlib import Path
P=Path(__file__).resolve().parent;source=P/'native_export.py';dpath=Path('@DIAGNOSTIC@/DRILL-CSV-DIAGNOSTIC.json');data=json.loads(dpath.read_text())
class GateError(Exception):pass
def require(x,m):
 if not x:raise GateError(m)
exec(compile(ast.Module(body=[x for x in ast.parse(source.read_text()).body if isinstance(x,ast.FunctionDef) and x.name=='match_drill_features'],type_ignores=[]),str(source),'exec'))
results={};controls={}
for pl in ['PTH','NPTH']:
 rows=data['drills'][pl]['all_matches'];expected=[r['exact_native_feature'] for r in rows];actual=[r['actual_export_feature'] for r in rows];results[pl]=match_drill_features(expected,actual)
 if pl!='PTH':continue
 ties=data['drills'][pl]['original_round_key_mismatches'];controls['five_actual_half_grid_ties']=match_drill_features([r['exact_native_feature'] for r in ties],[r['actual_export_feature'] for r in ties])
 cases={'missing_feature':actual[:-1]};x=copy.deepcopy(actual);x[-1]=x[0];cases['same_count_duplicate']=x;x=copy.deepcopy(actual);x[0][2]=0.201;cases['wrong_tool_diameter']=x;x=copy.deepcopy(actual);x[0][0]='NPTH';cases['wrong_plating']=x
 x=copy.deepcopy(actual);x[0][3]=float(expected[0][3])+0.000501;cases['overshift_0p000501mm']=x;x=copy.deepcopy(actual);x[0][3]=float(expected[0][3])+0.000500000001;cases['overshift_above_roundoff_bound']=x
 slot=next(i for i,f in enumerate(actual) if f[1]=='slot');x=copy.deepcopy(actual);x[slot][5]+=0.001;cases['wrong_slot_endpoint']=x
 x=copy.deepcopy(actual);x[0][3]=float('nan');cases['non_finite_coordinate']=x
 for name,x in cases.items():
  try:match_drill_features(expected,x)
  except GateError as exc:controls[name]={'correctly_rejected':True,'reason':str(exc)}
  else:raise AssertionError('Negative control passed: '+name)
 x=copy.deepcopy(actual);x[slot][3:7]=x[slot][5:7]+x[slot][3:5];controls['slot_endpoint_reversal']=match_drill_features(expected,x)
 # Floating arithmetic only, smaller than the declared 16-ulp bound.
 controls['computed_coordinate_one_ulp']=match_drill_features([('PTH','round',.2,math.nextafter(20.0005,math.inf),1.0)],[('PTH','round',.2,20.0,1.0)])
result={'schema':'f722-drill-precision-patch-controls/v1','patched_tool_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'actual_data_sha256':hashlib.sha256(dpath.read_bytes()).hexdigest(),'actual_census_results':results,'controls':controls,'only_host_matcher_executed':True,'native_or_export_commands_executed':False,'original_tool_failure_retained':True,'finalrelease':False};(P/'PATCH-CONTROLS.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps(result,indent=2))
