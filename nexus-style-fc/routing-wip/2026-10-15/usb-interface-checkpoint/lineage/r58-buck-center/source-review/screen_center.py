exec(open('/workspace/scratch/8a35c1f26232/nexus-recovery-20261015/r57-buck-review/inspect.py').read().split("out={'source_sha256'")[0])
vec=lambda p:k.VECTOR2I(round(p[0]*1e6),round(p[1]*1e6))
def hit(a,z,c=0):
 r=k.SHAPE.Collide(a,z,c);return r[0] if isinstance(r,tuple) else bool(r)
changes={'0097f17a-a60a-4d12-973b-5461dabae78d':('start',(104.575,113.925)),'961eede3-9481-48f8-b1ce-59d89e287a7d':('start',(104.575,113.925)),'eba8ff79-64eb-43fc-a9c1-492395d73f30':('end',(104.575,113.925)),'8fde276c-ea86-49b6-b2c1-c7966a02f478':('start',(103.259295,112.45))}
rows=[]
for u,(which,p) in changes.items():
 t=ts[u];n=k.PCB_TRACK(b);n.SetStart(t.GetStart());n.SetEnd(t.GetEnd());n.SetLayer(t.GetLayer());n.SetWidth(t.GetWidth());n.SetNetCode(t.GetNetCode());getattr(n,'Set'+which.title())(vec(p));l=t.GetLayer();old_contacts=[];new_contacts=[];old_obstacles=[];new_obstacles=[]
 for w,o in {**ts,**ps}.items():
  if w==u or not o.IsOnLayer(l):continue
  shape=o.GetEffectiveShape(l)
  if o.GetNetCode()==t.GetNetCode():
   if hit(t.GetEffectiveShape(l),shape):old_contacts.append(w)
   if hit(n.GetEffectiveShape(l),shape):new_contacts.append(w)
  else:
   if hit(t.GetEffectiveShape(l),shape,127002):old_obstacles.append(w)
   if hit(n.GetEffectiveShape(l),shape,127002):new_obstacles.append(info(o))
 rows.append({'uuid':u,'old':info(t),'proposal':info(n),'old_contacts':old_contacts,'new_contacts_to_unmodified_source_objects':new_contacts,'old_obstacles':old_obstacles,'new_obstacles':new_obstacles})
res={'source_sha256':hashlib.sha256(P.read_bytes()).hexdigest(),'changes':rows};(R/'r57-buck-review/center-screen.json').write_text(json.dumps(res,indent=2)+'\n');print(json.dumps(res,indent=2))
