"""Independently verify a candidate changes only declared-net copper to an adopted board."""
import argparse,sys,json,hashlib,copy
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('old',type=Path);p.add_argument('new',type=Path);p.add_argument('--net',action='append',required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'ordinary-routing/tests/mpn-parity'))
from apply_metadata_copy import parse,children,child,value,properties,shape,Node
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
o=parse(a.old.read_text());n=parse(a.new.read_text());allowed={'MPN','Manufacturer','LCSC','Supplier','Datasheet','Description'}
def keyed(root,kind):return {value(x,'uuid'):x for x in children(root,kind)}
def stripped(fp):
 x=copy.deepcopy(fp);x.items=[z for z in x.items if not(isinstance(z,Node) and z.items[0].value=='property' and z.items[1].value in allowed)];return shape(x)
of=keyed(o,'footprint');nf=keyed(n,'footprint');assert set(of)==set(nf)
for k in of:assert stripped(of[k])==stripped(nf[k]),('footprint physical/nonapproved metadata change',k)
added=[];removed=[];changed=[];retained=0
for kind in ['segment','via','arc']:
 old=keyed(o,kind);new=keyed(n,kind)
 for k in set(old)&set(new):
  if shape(old[k])==shape(new[k]):retained+=1;continue
  oldnet=value(old[k],'net');newnet=value(new[k],'net')
  assert oldnet==newnet and oldnet in a.net,(kind,k,'unauthorized changed object')
  changed.append({'uuid':k,'kind':kind,'net':oldnet,'before':shape(old[k]),'after':shape(new[k])})
 for k in set(old)-set(new):
  net=value(old[k],'net');assert net in a.net,(kind,k,net,'unauthorized removal')
  removed.append({'uuid':k,'kind':kind,'net':net,'before':shape(old[k])})
 for k in set(new)-set(old):
  net=value(new[k],'net');assert net in a.net,(kind,k,net,'unauthorized addition')
  added.append({'uuid':k,'kind':kind,'net':net,'after':shape(new[k])})
oz=keyed(o,'zone');nz=keyed(n,'zone');assert set(oz)==set(nz)
for k in oz:
 def config(z):return [shape(x) if isinstance(x,Node) else x.value for x in z.items if not(isinstance(x,Node) and x.items[0].value in ['filled_polygon','fill_segments'])]
 assert config(oz[k])==config(nz[k]),('zone design changed',k)
excluded={'footprint','segment','via','arc','zone'}
def rest(root):return [shape(x) if isinstance(x,Node) else x.value for x in root.items if not(isinstance(x,Node) and x.items[0].value in excluded)]
assert rest(o)==rest(n),'Other board settings/edges changed'
r={'schema':'f722-owner-coordinated-integration/v1','source_board_sha256':sha(a.old),'board_sha256':sha(a.new),'passed':True,'retained_footprints':len(of),'retained_track_via_arc_objects':retained,'unchanged_zone_designs':len(oz),'allowed_changed_nets':a.net,'removed_objects':sorted(removed,key=lambda x:x['uuid']),'changed_objects':sorted(changed,key=lambda x:x['uuid']),'added_objects':sorted(added,key=lambda x:x['uuid']),'limits':'Saved filled polygons are allowed to change after refill and require separate native connectivity/process/reference checks. Only six reviewed informational footprint fields are excluded from exact physical structure comparison.'};a.out.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({k:v for k,v in r.items() if k not in ['added_objects','removed_objects','changed_objects','limits']}));print('added objects',len(added))
