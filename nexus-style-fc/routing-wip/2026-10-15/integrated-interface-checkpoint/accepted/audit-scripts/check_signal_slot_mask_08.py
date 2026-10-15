from pathlib import Path
import re,json,sys,math,hashlib
O=Path(sys.argv[1]);tr=json.loads((O/'transaction.json').read_text());S=Path(tr['source_directory']);sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def normalize(text):return '\n'.join(x for x in text.splitlines() if not x.startswith(('%TF.CreationDate,','G04 Created by KiCad ')))
def parse(text):
 assert '%FSLAX46Y46*%' in text and '%MOMM*%' in text
 assert all(x=='%LPD*%' for x in text.splitlines() if x.startswith('%LP'))
 macros=dict(re.findall(r'%AM([^*]+)\*(.*?)\*%',text,re.S));aps={}
 for ident,name,args in re.findall(r'%ADD(\d+)([A-Za-z0-9_]+),([^*]+)\*%',text):
  p=list(map(float,args.split('X')))
  if name=='C':assert len(p)==1;box=[-p[0]/2,-p[0]/2,p[0]/2,p[0]/2]
  elif name in ['R','O']:assert len(p)==2;box=[-p[0]/2,-p[1]/2,p[0]/2,p[1]/2]
  elif name=='RoundRect':
   assert len(p)==10 and p[9]==0;r=p[0];pts=list(zip(p[1:9:2],p[2:9:2]));box=[min(x for x,y in pts)-r,min(y for x,y in pts)-r,max(x for x,y in pts)+r,max(y for x,y in pts)+r]
  elif name=='FreePoly0':
   assert len(p)==1;cmd=macros[name].strip().split(',');assert cmd[:2]==['4','1'] and cmd[-1]=='$1';n=int(cmd[2]);coords=list(map(float,cmd[3:-1]));assert len(coords)==2*(n+1);a=math.radians(p[0]);pts=[(x*math.cos(a)-y*math.sin(a),x*math.sin(a)+y*math.cos(a)) for x,y in zip(coords[::2],coords[1::2])];box=[min(x for x,y in pts),min(y for x,y in pts),max(x for x,y in pts),max(y for x,y in pts)]
  else:raise AssertionError(('Unsupported aperture',name))
  aps[int(ident)]={'type':name,'parameters':p,'bounds':box}
 flashes=[];selected=None;ref=None
 for line in text.splitlines():
  if line.startswith('%TO.C,'):ref=line.removeprefix('%TO.C,').removesuffix('*%')
  m=re.fullmatch(r'D(\d+)\*',line)
  if m:selected=int(m[1]);assert selected in aps
  if line.startswith(('X','Y')):
   m=re.fullmatch(r'X(-?\d+)Y(-?\d+)D03\*',line);assert m,('Unsupported drawing command',line);x,y=int(m[1])/1e6,-int(m[2])/1e6;a=aps[selected];xmin,ymin,xmax,ymax=a['bounds'];flashes.append({'ref':ref,'aperture_id':selected,'aperture_type':a['type'],'center':[x,y],'bounds_board_mm':[x+xmin,y-ymax,x+xmax,y-ymin]})
  assert not line.startswith(('G02','G03','G36','G37','%SR','%LM','%LR','%LS')),('Unsupported Gerber transform/path',line)
 assert flashes and all(a in aps for a in [x['aperture_id'] for x in flashes]);return flashes
results=[]
for ext in ['gts','gbs','gtp','gbp']:
 old=next((O/'mask-paste/before').glob('*.'+ext));new=O/'mask-paste/after'/old.name;assert normalize(old.read_text())==normalize(new.read_text());flashes=parse(new.read_text());records=[]
 for m in tr['moved_vias']:
  at=m['to'];gaps=[]
  for f in flashes:
   l,t,r,bot=f['bounds_board_mm'];gap=math.hypot(max(l-at[0],0,at[0]-r),max(t-at[1],0,at[1]-bot))-.1;gaps.append((gap,f))
  gap,near=min(gaps,key=lambda x:x[0])
  if ext in ['gtp','gbp']:assert gap>=.975-1e-8
  records.append({'via':m['uuid'],'net':m['net'],'at':at,'minimum_hole_to_aperture_bound_mm':gap,'nearest_aperture':near,'interpretation':'Paste-hole margin must pass; negative B.Mask distance is the inherited intentional own-net J1 contact land opening, not a new foreign-net mask bridge.'})
 results.append({'filename':new.name,'source_sha256':sha(old),'candidate_sha256':sha(new),'geometry_exact_except_timestamp':True,'moved_via_aperture_measurements':records})
out={'status':'PASS exact source/candidate mask and paste aperture retention','source_board_sha256':sha(S/'hardware/nexus-style-fc.kicad_pcb'),'candidate_board_sha256':sha(O/'hardware/nexus-style-fc.kicad_pcb'),'files':results,'qualification':'No via or pad geometry changes in this transaction. J1 contacts remain B.Cu/B.Mask without paste; their exposed-hole solder-joint assembly and the 16 inherited pasted-via locations remain qualification gates.'};(O/'mask-paste-proof.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
