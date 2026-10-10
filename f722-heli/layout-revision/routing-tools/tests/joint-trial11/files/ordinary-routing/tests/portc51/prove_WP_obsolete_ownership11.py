"""Exact small WP source boundary, actual-pad partition and retained R5 source proof."""
import hashlib,json,math,time
from pathlib import Path
import composite_native11_C_TX_WP as g
H=Path(__file__).resolve().parent;s=g.s;START=time.monotonic();T=g.TXWP
removed={o['uuid']for o in T['removed_native_records']}
source=[g.entry(o)for o in g.N['objects']if o['net']=='FLASH_WP_N']
after=[q for q in g.BASE if q[0]['net']=='FLASH_WP_N']
def metal(e,l):return e[1][l] if e[3]is None else e[1][l].difference(e[3])
def contacts(entries):
 out=[]
 for i,a in enumerate(entries):
  for b in entries[i+1:]:
   for layer in set(a[1])&set(b[1]):
    area=metal(a,layer).intersection(metal(b,layer)).area
    if area>1e-12:out.append(dict(a=a[0]['uuid'],b=b[0]['uuid'],layer=layer,finite_area_mm2=area))
 return out
def partition(entries,edges):
 parent={q[0]['uuid']:q[0]['uuid']for q in entries}
 def root(x):
  while parent[x]!=x:parent[x]=parent[parent[x]];x=parent[x]
  return x
 for e in edges:parent[root(e['a'])]=root(e['b'])
 groups={}
 for q in entries:groups.setdefault(root(q[0]['uuid']),[]).append(q[0].get('key')or q[0]['uuid'])
 return [sorted(v)for v in groups.values()]
before_edges=contacts(source);after_edges=contacts(after)
boundary=[e for e in before_edges if(e['a']in removed)!=(e['b']in removed)]
retained_boundary={e['b']if e['a']in removed else e['a']for e in boundary}
expected={g.one_pad('R5.2')['uuid'],'ed0fb583-232d-5ae4-8ef5-7fae5339a5e9'}
assert retained_boundary==expected,(retained_boundary,expected)
retained=[q for q in source if q[0]['uuid']not in removed]
after_by={q[0]['uuid']:q for q in after}
assert all(g.physical(q[0])==g.physical(after_by[q[0]['uuid']][0])for q in retained)
source_pad=g.entry(g.one_pad('R5.1'));core_contacts=[]
for o in g.N['objects']:
 if o['net']!='+3V3_CORE'or o['uuid']==source_pad[0]['uuid']:continue
 q=g.entry(o)
 for layer in set(q[1])&set(source_pad[1]):
  area=metal(q,layer).intersection(metal(source_pad,layer)).area
  if area>1e-12:
   rows=[e for e in g.BASE if e[0]['uuid']==o['uuid']]
   core_contacts.append(dict(uuid=o['uuid'],key=o.get('key'),layer=layer,finite_area_mm2=area,retained_record_exact=len(rows)==1 and g.physical(rows[0][0])==g.physical(o)))
before_partition=partition(source,before_edges);after_partition=partition(after,after_edges)
source_degree={q[0]['uuid']:set()for q in after}
for e in after_edges:source_degree[e['a']].add(e['b']);source_degree[e['b']].add(e['a'])
ends=[q[0]['uuid']for q in after if len(source_degree[q[0]['uuid']])==1]
actual_pad_ids={g.one_pad('R5.2')['uuid'],g.one_pad('U3.3')['uuid']}
assert len(before_partition)==len(after_partition)==1
assert set(ends)==actual_pad_ids,(ends,actual_pad_ids)
assert all(q['retained_record_exact']for q in core_contacts)
out=dict(schema='f722-WP-obsolete-objects-ownership11/v1',source=g.binding(),transaction_sha256=hashlib.sha256(g.TXWP_FILE.read_bytes()).hexdigest(),
 removed_native_records=T['removed_native_records'],removed_scope_only_WP=True,exact_source_boundary_contacts=boundary,
 expected_retained_boundary_records=[g.by[u]for u in sorted(expected)],before_actual_object_partition=before_partition,after_actual_object_partition=after_partition,
 retained_WP_source_records_exact=True,after_finite_contacts=after_edges,only_degree_one_objects_are_actual_R5_2_and_U3_3_pads=True,
 R5_1_CORE_pad_record_exact=g.physical(source_pad[0])==g.physical(g.by[source_pad[0]['uuid']]),R5_1_direct_CORE_contacts=core_contacts,
 R5_value_and_pose_changed=False,WP_widths_mm=.127,WP_trace_length_before_after_mm=[T['WP_trace_length_before_mm'],T['WP_trace_length_after_mm']],
 WP_via_counts_before_after=T['WP_via_count_before_after'],fresh_native_reference_still_required=True,passed=True,seconds=time.monotonic()-START)
out['script_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest();p=H/'WP-obsolete-objects-ownership11.json';p.write_text(json.dumps(out,indent=2)+'\n')
print('PASSED',out['seconds'],'BOUNDARY',sorted(retained_boundary),'ENDS',sorted(ends),flush=True)
