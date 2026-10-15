from pathlib import Path
import json,re,hashlib,math,csv
R=Path('/workspace/scratch/8a35c1f26232/nexus-recovery-20261015')
O=Path('/workspace/shared/nexus-release-gates-review')
S=R/'mechanical-integration/main-signal-slot-08'
expected='ccd8865f6785fd1cdec0214a08fe409faed4d47bb01e8474f09264ee36acab99'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
p=S/'hardware/nexus-style-fc.kicad_pcb';assert sha(p)==expected;s=p.read_text();stack=[];spans={};root=None
for m in re.finditer(r'\(|\)|"(?:\\.|[^"\\])*"|[^\s()]+',s):
 t=m.group()
 if t=='(':
  n=[]
  if stack:stack[-1][0].append(n)
  stack.append((n,m.start()))
 elif t==')':
  n,i=stack.pop();spans[id(n)]=(i,m.end())
  if not stack:root=n
 else:stack[-1][0].append(t[1:-1] if t.startswith('"') else t)
def sub(n,k):return next((x for x in n[1:] if isinstance(x,list) and x and x[0]==k),None)
def val(n,k):
 x=sub(n,k);return x[1] if x else None
def digest(n):
 a,b=spans[id(n)];return hashlib.sha256(s[a:b].encode()).hexdigest()
items={};fps={};padfps={}
for n in root[1:]:
 if not isinstance(n,list):continue
 if n[0]=='via':items[val(n,'uuid')]=n
 if n[0]=='footprint':
  ref=next((x[2] for x in n[1:] if isinstance(x,list) and x[:2]==['property','Reference']),None);fps[ref]=n
  for q in n[1:]:
   if isinstance(q,list) and q and q[0]=='pad':items[val(q,'uuid')]=q;padfps[val(q,'uuid')]=n
j=json.loads((R/'r56-remaining-via-inventory/remaining-vias.json').read_text());inventory=[]
for v in j['remaining']:
 vv=v['via'];n=items[vv['uuid']];assert digest(n)==vv['source_node_sha256']
 for c in v['pasted_pad_contacts']:
  q=c['pad'];pn=items[q['uuid']];fp=padfps[q['uuid']];assert digest(pn)==q['source_node_sha256']
  a=sub(fp,'at');la=sub(pn,'at');th=math.radians(-float(a[3] if len(a)>3 else 0));x,y=map(float,la[1:3]);gp=[float(a[1])+x*math.cos(th)-y*math.sin(th),float(a[2])+x*math.sin(th)+y*math.cos(th)]
  assert math.dist(gp,q['at'])<1e-9
  inventory.append(dict(via_uuid=vv['uuid'],via_net=vv['net'],via_xy_mm=vv['at'],via_land_mm=vv['diameter_mm'],via_drill_mm=vv['drill_mm'],ref=q['ref'],pad=q['pin'],paste_side='F' if 'F.Paste' in q['all_native_layers'] else 'B',pad_shape=q['shape'],pad_local_size_mm=q['size_mm'],source_drill_gap_mm=c['drill_gap_mm'],via_source_node_sha256=digest(n),pad_source_node_sha256=digest(pn),pad_global_position_unchanged=True))
assert len(inventory)==17 and len({x['via_uuid'] for x in inventory})==16
# Actual exported U5 EP aperture: retain the complete macro, not the 0.005 mm anchor.
g=S/'mask-paste/after/nexus-style-fc-B_Paste.gbp';gs=g.read_text();macro=re.search(r'%AMFreePoly0\*\n(.*?)\*%',gs,re.S).group(1);vals=macro.split(',');count=int(vals[2]);coords=list(map(float,vals[3:3+2*(count+1)]));pts=list(zip(coords[::2],coords[1::2]));xs,ys=zip(*pts)
u5=dict(paste_gerber_sha256=sha(g),macro_name='FreePoly0',macro_text=macro,aperture_code='D33',rotation_deg=180,flash_gerber_mm=[102.4,-107.3],macro_bbox_mm=[min(xs),min(ys),max(xs),max(ys)],bbox_size_mm=[max(xs)-min(xs),max(ys)-min(ys)],single_continuous_aperture=True,no_local_mask_island_or_paste_exclusion_in_source_pad=True,drill_xy_mm=[102.675,108.225],source_drill_gap_mm=-0.07501099999999782)
inputs=[p,S/'verification.json',S/'FINAL-SEAL.json',S/'mask-paste-proof.json',S/'usb-reference-return-verification.json',R/'mechanical-integration/main-signal-slot-08-validation-supplement/verification.json',R/'r56-remaining-via-inventory/remaining-vias.json',R/'header-assembly-fit-review-readonly/README.md',R/'header-assembly-fit-review-readonly/electrical-registration-window.json',R/'routing-continuation/r62-input-cap-star/independent-review/REVIEW.md',R/'routing-continuation/r62-input-cap-star/physical-assembly-evidence/FINAL-ASSEMBLY-SUPPLEMENT.md',R/'publication17-receipt.json',Path('/workspace/shared/nexus-pasted-via-r61/three-bounded-proposals.json')]
receipt=dict(status='Read-only source binding; no native rerun, project edit or manufacturing acceptance',main_board_sha256=expected,child_board_sha256=sha(S/'hardware/header-board/nexus-header-board.kicad_pcb'),source_paths_and_sha256={str(x):sha(x) for x in inputs},inventory=inventory,U5_actual_paste=u5,U2=dict(value='ICM-42688-P',front_side=True,rotation_deg=0,pin9_net=val(next(q for q in fps['U2'] if isinstance(q,list) and q[:2]==['pad','9']),'net'),source_comment='gyro_1_sensor_align CW90; firmware behavior unverified'))
(O/'source-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
with (O/'pasted-contact-inventory.csv').open('w',newline='') as f:
 w=csv.writer(f);w.writerow(['via_uuid','net','x_mm','y_mm','drill_mm','land_mm','ref_pad','side','shape','local_size_mm','signed_source_gap_mm'])
 for x in inventory:w.writerow([x['via_uuid'],x['via_net'],*x['via_xy_mm'],x['via_drill_mm'],x['via_land_mm'],x['ref']+'.'+x['pad'],x['paste_side'],x['pad_shape'],' x '.join(map(str,x['pad_local_size_mm'])),x['source_drill_gap_mm']])
print(json.dumps({'main_sha256':expected,'matching_vias':16,'matching_pasted_pad_records_and_positions':17,'U5_paste_bbox_size_mm':u5['bbox_size_mm'],'U2_pin9_net':receipt['U2']['pin9_net']},indent=2))
