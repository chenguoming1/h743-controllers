exec(open('/workspace/scratch/8a35c1f26232/nexus-recovery-20261015/r57-buck-review/inspect.py').read().split("out={'source_sha256'")[0])
import re
O=R/'r57-buck-review';tr=json.loads((O/'transaction-proposal.json').read_text());txt=P.read_text();nodes={}
for m in re.finditer(r'\(segment\s',txt):
 i=m.start();depth=0;quoted=False;escaped=False
 for z in range(i,len(txt)):
  c=txt[z]
  if escaped:escaped=False;continue
  if quoted and c=='\\':escaped=True;continue
  if c=='"':quoted=not quoted;continue
  if quoted:continue
  if c=='(':depth+=1
  elif c==')':
   depth-=1
   if depth==0:
    s=txt[i:z+1];u=re.search(r'\(uuid "([^"]+)"\)',s).group(1);nodes[u]=s;break
for r in tr['replacements']:
 s=nodes[r['source_uuid']];r['source_text']=s;r['source_text_sha256']=hashlib.sha256(s.encode()).hexdigest()
# Specific contact bridges prove that old near-corner overlap ports remain connected by unchanged full-width conductors.
tr['external_port_proofs']=[
 {'port_uuid':'a33d9038-104a-4904-836a-f2c168df6d4c','proof':'See target_annular_proofs: unchanged via is covered by each centered 0.500 mm replacement; 0.375 mm branch has a finite annular entry.'},
 {'port_uuid':'51a22cd5-55d6-4b2a-ab4e-1419692162c2','proof':'New centered In2.Cu track covers the complete annulus. On B.Cu, eba8ff79 replacement still meets unchanged 051424f8 at the exact (103.259295,112.831) endpoint with both widths 0.500 mm. Unchanged 051424f8 starts at this via center and covers its entire B.Cu annulus.'},
 {'port_uuid':'051424f8-a5f4-460c-b1bc-05616bc7fc20','shared_endpoint_mm':[103.259295,112.831],'replacement_source_uuid':'eba8ff79-64eb-43fc-a9c1-492395d73f30','both_width_mm':.5},
 {'port_uuid':'9d5086d7-6a97-4b07-abf0-0f00e1975b7c','proof':'Direct finite overlap preserved. Full-width path is replacement eba8ff79 -> unchanged 051424f8 -> unchanged 9d5086d7, with exact shared endpoints (103.259295,112.831) and (103.259295,112.45), all 0.500 mm B.Cu.'},
 {'port_uuid':'f33cb356-76cc-4f69-92fd-38e4246f5538','shared_endpoint_mm':[104.351,115.699],'replacement_source_uuid':'961eede3-9481-48f8-b1ce-59d89e287a7d','both_width_mm':.5},
 {'port_uuid':'1f2d892b-26ce-4982-9f42-2a3ecd9fcd2b','shared_endpoint_mm':[104.175,111.675],'replacement_source_uuid':'8fde276c-ea86-49b6-b2c1-c7966a02f478','both_width_mm':.5},
 {'port_uuid':'c20c9ea5-99b2-4a56-8b20-f4a915c7ddf3','proof':'R11.1 remote endpoint remains exactly at unchanged pad center (105.55,113.91), track width 0.375 mm. Native finite pad intersection is recorded in source_contacts_preserved; original pad itself is unchanged.'}
]
tr['source_sha256_rechecked']=hashlib.sha256(P.read_bytes()).hexdigest();assert tr['source_sha256_rechecked']==tr['source_board_sha256'];(O/'transaction-proposal.json').write_text(json.dumps(tr,indent=2)+'\n')
manifest={'source_board_sha256':tr['source_board_sha256'],'status':'Read-only review deliverable; no accepted-board modification or heavy verification performed','files':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in O.iterdir() if p.is_file() and p.name!='evidence-manifest.json'}};(O/'evidence-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');print(json.dumps({'transaction_sha256':manifest['files']['transaction-proposal.json'],'review_sha256':manifest['files']['review.json'],'source_unchanged':True},indent=2))
