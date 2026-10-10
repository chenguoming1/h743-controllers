"""Exact physical reference proof; preserves raw comparator and runtime net indices."""
import pathlib,sys,json,hashlib,copy
HERE=pathlib.Path(__file__).resolve().parent;ROOT=HERE.parents[2];S=ROOT/'ordinary-routing/candidate44';D=HERE/'candidate01'
sys.path.insert(0,str(ROOT/'repo/f722-heli/layout-revision/signal-review/native'))
from compare_reference_geometry import load
from check_signal_geometry import CRITICAL,I2C
sha=lambda f:hashlib.sha256(pathlib.Path(f).read_bytes()).hexdigest()
read=lambda f:json.loads(pathlib.Path(f).read_text())
bg,bm,br=load(S/'reference-snapshot',S/'f722-heli.kicad_pcb');ag,am,ar=load(D/'reference-snapshot',D/'f722-heli.kicad_pcb');raw=read(D/'reference-comparison44.json')
assert raw['before_board_sha256']==bg['board_sha256'] and raw['after_board_sha256']==ag['board_sha256']
def mappings(g):
 byname={};bycode={}
 for o in g['objects']+g['zones']:
  name=o['net'];code=o['net_code']
  assert byname.get(name,code)==code and bycode.get(code,name)==name
  byname[name]=code;bycode[code]=name
 return byname
oldmap,newmap=mappings(bg),mappings(ag);assert set(oldmap)==set(newmap)
critical=set(CRITICAL)|set(I2C);old={o['uuid']:o for o in bg['objects']if o['net']in critical};new={o['uuid']:o for o in ag['objects']if o['net']in critical};assert old.keys()==new.keys()
def physical(o):return {k:v for k,v in o.items()if k!='net_code'}
def same_records(a,b):return a.keys()==b.keys() and all(physical(a[u])==physical(b[u])for u in a)
assert same_records(old,new)
diff=[]
for u in old:
 assert physical(old[u])==physical(new[u]),u
 if old[u]!=new[u]:
  fields=sorted(k for k in old[u].keys()|new[u].keys()if old[u].get(k)!=new[u].get(k));assert fields==['net_code'];diff.append({'uuid':u,'net':old[u]['net'],'kind':old[u]['kind'],'changed_fields':fields,'before_net_code':old[u]['net_code'],'after_net_code':new[u]['net_code']})
assert sorted(r['uuid']for r in diff)==raw['critical_object_differences'];assert raw['critical_object_geometry_identical']is False
assert bg['zones']==ag['zones'];assert br['nets']==ar['nets'];assert all(v==0 for row in raw['net_numeric_deltas_after_minus_before'].values()for v in row.values());assert all(p['physical_GND_lost_mm2']==p['physical_GND_gained_mm2']==0 for p in raw['ground_fill_changes'].values())
sample=next(o for o in new.values()if o['kind']=='track');controls=[]
for field,value in [('net','NRST'),('width',sample['width']+.001),('uuid','changed-uuid'),('start',[sample['start'][0]+.001,sample['start'][1]])]:
 bad=copy.deepcopy(new);bad[sample['uuid']][field]=value;controls.append({'name':'reject_'+field+'_change','rejected':not same_records(old,bad)})
bad=copy.deepcopy(new);layer=next(iter(sample['copper']));bad[sample['uuid']]['copper'][layer][0]['outer'][0][0]+=.001;controls.append({'name':'reject_copper_polygon_change','rejected':not same_records(old,bad)});bad=copy.deepcopy(new);del bad[sample['uuid']];controls.append({'name':'reject_omitted_UUID','rejected':not same_records(old,bad)});assert all(x['rejected']for x in controls)
r={'schema':'f722-exact-reference-runtime-net-index-proof/v1','passed':True,'before_board_sha256':bg['board_sha256'],'board_sha256':ag['board_sha256'],'raw_comparison_sha256':sha(D/'reference-comparison44.json'),'before_native_sha256':sha(S/'reference-snapshot/native-geometry.json'),'after_native_sha256':sha(D/'reference-snapshot/native-geometry.json'),'before_report_sha256':sha(S/'reference-snapshot/critical-reference.json'),'after_report_sha256':sha(D/'reference-snapshot/critical-reference.json'),'script_sha256':sha(__file__),'raw_critical_object_geometry_identical':False,'raw_difference_count':len(diff),'critical_physical_records_exact_except_runtime_net_code':True,'critical_record_count':len(old),'each_raw_difference_is_only_net_code':True,'runtime_net_mapping_bijections_verified':True,'raw_runtime_net_index_differences':diff,'all_saved_zone_records_exact':True,'all_critical_reference_net_reports_exact':True,'all_numeric_projection_deltas_exactly_zero':True,'physical_GND_lost_and_gained_geometry_empty':True,'negative_controls':controls,'scope':'The original comparator compares complete exported records including transient native name-to-integer net lookup indices. Only those indices differ. No fields in stored snapshots or raw reports were edited. UUIDs, exact names, pad/net identities, widths, layers, drills and all physical polygons remain exact for every critical object; all saved zone records and full reference net reports are identical. No numerical electrical or AC qualification claimed.'}
(D/'reference-runtime-index-proof.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({k:r[k]for k in ['passed','board_sha256','raw_difference_count','critical_record_count','all_saved_zone_records_exact','all_critical_reference_net_reports_exact']}))
