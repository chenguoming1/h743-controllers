"""Export an exact selected planning transaction without reconstructing buffered centerlines.

This records native11_context track/via constructor arguments during module import.
It never modifies the accepted board and refuses unrecorded or ambiguous new copper.
The output is a planning transaction, not a native/DRC validation receipt.
"""
import argparse,hashlib,importlib,json,sys
from pathlib import Path
P=Path(__file__).resolve();ROOT=P.parents[2]
for d in [P.parent,ROOT/'tests/boot56',ROOT/'tests/portc51']:
 sys.path.insert(0,str(d))
parser=argparse.ArgumentParser();parser.add_argument('module');parser.add_argument('output');a=parser.parse_args()
import native11_context as c
registry={};origtrack=c.track;origvia=c.via

def record_track(net,layer,points,name,width=.127):
 q=origtrack(net,layer,points,name,width)
 registry.setdefault(name,[]).append((q,dict(kind='track',name=name,net=net,layer=layer,points=[list(p)for p in points],width=width)))
 return q

def record_via(net,xy,name):
 q=origvia(net,xy,name)
 registry.setdefault(name,[]).append((q,dict(kind='via',name=name,net=net,xy=list(xy),diameter=.45,drill=.20,layers=list(c.N['copper_layers']),tented_front=True,tented_back=True)))
 return q
c.track=record_track;c.via=record_via
g=importlib.import_module(a.module)

def same_shape(q,r):
 return set(q[1])==set(r[1]) and all(q[1][k].wkb==r[1][k].wkb for k in q[1]) and set(q[2])==set(r[2]) and all(q[2][k].wkb==r[2][k].wkb for k in q[2]) and ((q[3]is None and r[3]is None)or(q[3]is not None and r[3]is not None and q[3].wkb==r[3].wkb))

def physical(o):return {k:v for k,v in o.items()if k!='net_code'}
ids=[q[0]['uuid']for q in g.BASE];assert len(set(ids))==len(ids)
original=c.by;current={q[0]['uuid']:q for q in g.BASE};removed=[original[k]for k in sorted(set(original)-set(current))]
changedpads=[];new=[];retained=[]
for uid,q in current.items():
 if uid in original:
  o=original[uid];old=c.entry(o)
  if o['kind']=='pad':
   assert q[0]['kind']=='pad' and q[0]['key']==o['key'],uid
   if physical(q[0])!=physical(o) or not same_shape(q,old):changedpads.append(dict(before=o,after=q[0]))
  else:
   assert physical(q[0])==physical(o) and same_shape(q,old),('Unrecorded mutation of native copper',uid)
  retained.append(uid)
 else:
  matches=[r for qq,r in registry.get(uid,[])if same_shape(q,qq)and q[0]['net']==qq[0]['net']and q[0]['kind']==qq[0]['kind']]
  unique={json.dumps(r,sort_keys=True):r for r in matches}
  assert len(unique)==1,('Unrecorded or ambiguous selected copper',uid,len(unique))
  new.append(dict(recipe=next(iter(unique.values())),selected_object_record=q[0]))
code={}
for m in list(sys.modules.values()):
 f=getattr(m,'__file__',None)
 if f:
  p=Path(f).resolve()
  if p.suffix=='.py' and p.is_relative_to(ROOT):code[str(p.relative_to(ROOT))]=hashlib.sha256(p.read_bytes()).hexdigest()
missingpads=[o['key']for o in removed if o['kind']=='pad']
out=dict(schema='f722-recorded-joint-planning-transaction/v1',selected_module=a.module,source=g.binding(),source_board_sha256=c.EXPECTED,source_native_sha256=hashlib.sha256(c.SOURCE.read_bytes()).hexdigest(),removed_native_records=removed,changed_pad_records=changedpads,added_copper=new,retained_native_ids=retained,missing_actual_pad_keys=missingpads,complete_pad_inventory=not missingpads,native_candidate=False,native_refill_DRC_electrical_review_pending=True,constructor_argument_capture=True,all_selected_new_shapes_match_recorded_constructor_bytes=True,imported_code_hashes=code,exporter_sha256=hashlib.sha256(P.read_bytes()).hexdigest())
p=Path(a.output);assert not p.exists();p.write_text(json.dumps(out,indent=2,allow_nan=False)+'\n')
print('EXPORTED',len(new),'new copper records;',len(changedpads),'changed pads;',len(missingpads),'pending pads')
