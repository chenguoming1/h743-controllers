from pathlib import Path
import json,sys,re,hashlib,math
O=Path(sys.argv[1]);tr=json.loads((O/'transaction.json').read_text());S=Path(tr['source_directory']);sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
exec((Path(__file__).parent/'check_offpad_mask_paste.py').read_text().split('results=[]')[0])
results=[]
for ext in ['gts','gbs','gtp','gbp']:
 old=next((O/'mask-paste/before').glob('*.'+ext));new=O/'mask-paste/after'/old.name;a,b=old.read_text(),new.read_text();assert normalize(a)==normalize(b);flashes=parse(b);checks=[]
 for v in tr['added_primitives']:
  if v['kind']!='via':continue
  at=v['at'];gaps=[]
  for f in flashes:
   l,t,r,bot=f['bounds_board_mm'];gap=math.hypot(max(l-at[0],0,at[0]-r),max(t-at[1],0,at[1]-bot))-.1;gaps.append((gap,f))
  gap,near=min(gaps,key=lambda x:x[0]);assert gap>0,(v['uuid'],new.name,gap);checks.append({'via':v['uuid'],'net':v['net'],'at':at,'drill_diameter_mm':.2,'hole_to_all_actual_aperture_bounds_lower_bound_mm':gap,'nearest_aperture':near})
 results.append({'filename':new.name,'source_sha256':sha(old),'candidate_sha256':sha(new),'identical_except_creation_timestamps':True,'flash_count':len(flashes),'checks':checks})
g=next((O/'diagnostic-in3-cam').glob('*.g3'));s=g.read_text();assert '%FSLAX46Y46*%' in s and '%MOMM*%' in s
net=None;dark=None;pts=None;regions=[]
for line in s.splitlines():
 if line.startswith('%TO.N,'):net=line[len('%TO.N,'):-2]
 if line.startswith('%LP'):dark=line=='%LPD*%'
 if line=='G36*':assert pts is None;pts=[];rn=net;rd=dark
 elif line=='G37*':assert pts is not None;regions.append({'net':rn,'dark':rd,'vertices':pts});pts=None
 elif pts is not None:
  m=re.fullmatch(r'X(-?\d+)Y(-?\d+)D0[12]\*',line)
  if m:pts.append((int(m[1]),-int(m[2])))
  else:assert line=='G01*',('unexpected taper region interpolation',line)
assert pts is None
proofs=[]
def canon(pts):
 if pts[0]==pts[-1]:pts=pts[:-1]
 return min(tuple(p[i:]+p[:i]) for p in [pts,list(reversed(pts))] for i in range(len(p)))
for p in tr['added_primitives']:
 if p['kind']!='taper_copper_polygon':continue
 exp=[tuple(round(x*1e6) for x in v) for v in p['vertices_mm']];matches=[z for z in regions if z['net']==p['net'] and z['dark'] and canon(z['vertices'])==canon(exp)];assert len(matches)==1,(p['uuid'],len(matches));proofs.append({'uuid':p['uuid'],'net':p['net'],'exact_native_and_gerber_vertices_nm':exp,'dark_solid_net_tagged_region_count':1})
assert len(proofs)==4
out={'status':'PASS: unchanged exported mask/paste apertures, every new via hole outside all actual aperture bounds, and all four exact solid In3 tapers present in Gerber','source_board_sha256':sha(S/'hardware/nexus-style-fc.kicad_pcb'),'candidate_board_sha256':sha(O/'hardware/nexus-style-fc.kicad_pcb'),'mask_paste':results,'in3_gerber_sha256':sha(g),'taper_regions':proofs,'method':'Actual 4.6 absolute-mm Gerber parsed with all aperture types/flash geometry accounted for. Mask/paste hole separation uses conservative aperture bounding boxes. Taper checks require exact cyclic/reversed polygon equality, dark polarity and correct USB net attribute. No centerline-only assumption.','qualification':'Diagnostic CAM only, not release output. Registration/stencil/assembly and the 16 inherited pasted-hole locations remain unqualified.'};(O/'cam-verification.json').write_text(json.dumps(out,indent=2)+'\n');print(out['status']);print('minimum actual hole-to-aperture lower bound',min(v['hole_to_all_actual_aperture_bounds_lower_bound_mm'] for f in results for v in f['checks']))
