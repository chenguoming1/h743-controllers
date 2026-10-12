"""Exact saved-JSON reconstruction; no geometry library or native execution."""
import hashlib,json

def encoded(value):return (json.dumps(value,sort_keys=True,separators=(',',':'))+'\n').encode()
def fingerprint(value):return hashlib.sha256(encoded(value)).hexdigest()
def keyed(value):return isinstance(value,list) and value and all(isinstance(v,dict) and isinstance(v.get('uuid'),str) for v in value) and len({v['uuid'] for v in value})==len(value)
def patch(before,after):
 if before==after:return None
 binding={'before_sha256':fingerprint(before)}
 if isinstance(before,dict) and isinstance(after,dict):
  return {**binding,'kind':'dict','remove':sorted(set(before)-set(after)),'add':{k:after[k] for k in after.keys()-before.keys()},'change':{k:p for k in before.keys()&after.keys() if (p:=patch(before[k],after[k])) is not None}}
 if keyed(before) and keyed(after):
  a={v['uuid']:v for v in before};b={v['uuid']:v for v in after}
  return {**binding,'kind':'uuid-list','order':[v['uuid'] for v in after],'records':{k:v for k,v in b.items() if k not in a or v!=a[k]}}
 if isinstance(before,list) and isinstance(after,list) and len(before)==len(after):
  return {**binding,'kind':'list','change':{str(i):p for i,(a,b) in enumerate(zip(before,after)) if (p:=patch(a,b)) is not None}}
 return {**binding,'kind':'replace','value':after}
def apply(value,change):
 if change is None:return value
 assert fingerprint(value)==change['before_sha256'],'Reconstruction source changed'
 kind=change['kind']
 if kind=='replace':return change['value']
 if kind=='dict':
  out=dict(value)
  for k in change['remove']:del out[k]
  out.update(change['add'])
  for k,p in change['change'].items():out[k]=apply(out[k],p)
  return out
 if kind=='list':
  out=list(value)
  for i,p in change['change'].items():out[int(i)]=apply(out[int(i)],p)
  return out
 if kind=='uuid-list':
  rows={v['uuid']:v for v in value};rows.update(change['records']);return [rows[k] for k in change['order']]
 raise ValueError(kind)
