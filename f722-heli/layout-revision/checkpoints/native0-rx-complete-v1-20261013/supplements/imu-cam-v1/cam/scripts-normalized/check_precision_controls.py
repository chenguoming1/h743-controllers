import copy,hashlib,json
from pathlib import Path
from precision_match import match
P=Path(__file__).resolve().parent;d=json.loads((P/'DRILL-CSV-DIAGNOSTIC.json').read_text());cases={};proof={}
for plating in ['PTH','NPTH']:
 rows=d['drills'][plating]['all_matches'];expected=[r['exact_native_feature'] for r in rows];actual=[r['actual_export_feature'] for r in rows];out=match(expected,actual);proof[plating]={'matched_count':len(out),'unique_assignment':True}
 if plating=='PTH':
  ties=d['drills'][plating]['original_round_key_mismatches'];assert len(ties)==5;assert len(match([r['exact_native_feature'] for r in ties],[r['actual_export_feature'] for r in ties]))==5;cases['five_actual_rounding_ties']='PASS'
  tests={};tests['missing']=actual[:-1];q=copy.deepcopy(actual);q[-1]=q[0];tests['duplicate_same_census']=q
  q=copy.deepcopy(actual);q[0][2]=0.201;tests['wrong_tool_diameter']=q
  q=copy.deepcopy(actual);q[0][3]=float(expected[0][3])+0.000501;tests['overshift_0p000501mm']=q
  slot=next(i for i,x in enumerate(actual) if x[1]=='slot');q=copy.deepcopy(actual);q[slot][5]+=0.001;tests['wrong_slot_endpoint']=q
  for name,rows2 in tests.items():
   try:match(expected,rows2)
   except ValueError as exc:cases[name]={'correctly_rejected':True,'reason':str(exc)}
   else:raise AssertionError('Negative control unexpectedly passed: '+name)
  q=copy.deepcopy(actual);q[slot][3:7]=q[slot][5:7]+q[slot][3:5];match(expected,q);cases['slot_endpoint_reversal']='PASS: same physical slot'
result={'schema':'f722-precision-drill-diagnostic-controls/v1','scope':'Read-only diagnostic validation; no modification of final exporter or source','precision_mm':'0.001','half_grid_mm':'0.0005','extra_arithmetic_tolerance_mm':'0','actual_census':proof,'controls':cases,'matcher_sha256':hashlib.sha256((P/'precision_match.py').read_bytes()).hexdigest(),'source_diagnostic_sha256':hashlib.sha256((P/'DRILL-CSV-DIAGNOSTIC.json').read_bytes()).hexdigest(),'original_exporter_failed_report_preserved':True,'finalrelease':False}
(P/'PRECISION-MATCH-CONTROLS.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps(result,indent=2))
