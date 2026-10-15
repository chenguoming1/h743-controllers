from pathlib import Path
import pcbnew as k,json,hashlib,sys,collections,csv,math
R=Path('/workspace/scratch/8a35c1f26232/nexus-recovery-20261015');O=R/'routing-continuation/r62-input-cap-star';S=R/'routing-continuation/r61-six-clearances';sys.path.insert(0,str(R/'latest-main/nexus-style-fc/tools'));import validate_nexus_reroute as V
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();val=lambda n,key:V.atom(V.children(n,key)[0][1]);uid=lambda o:o.m_Uuid.AsString();xy=lambda p:[p.x/1e6,p.y/1e6]
def netmap(p):
 text=p.read_text()
 if text.lstrip().startswith('<'):
  import xml.etree.ElementTree as E
  tree=E.fromstring(text);return {(x.attrib['ref'],x.attrib['pin']):n.attrib['name'] for n in tree.findall('./nets/net') for x in n.findall('node')}
 t=V.parse_sexpr(text);out={}
 for n in V.children(V.children(t,'nets')[0],'net'):
  net=val(n,'name');net={'unconnected-(U2-INT2{slash}FSYNC{slash}CLKIN-Pad9)':'unconnected-(U2-INT2/FSYNC/CLKIN-Pad9)','unconnected-(U14-FB{slash}VSET-Pad1)':'unconnected-(U14-FB/VSET-Pad1)'}.get(net,net)
  for node in V.children(n,'node'):
   key=(val(node,'ref'),val(node,'pin'));assert key not in out;out[key]=net
 return out
old=netmap(S/'final-netlist.xml');new=netmap(O/'final-netlist.xml');frozen=netmap(O/'source-final-netlist.xml');assert len(old)==347 and len(new)==349 and new==frozen and {k:v for k,v in new.items() if k in old}==old and set(new)-set(old)=={('C31','1'),('C31','2')} and new['C31','1']=='VSYS' and new['C31','2']=='GND'
b=k.LoadBoard(str(O/'hardware/nexus-style-fc.kicad_pcb'));fps={f.GetReference():f for f in b.GetFootprints()};bm={}
for f in fps.values():
 for p in f.Pads():
  pair=(f.GetReference(),p.GetNumber())
  if pair in bm:assert bm[pair]==p.GetNetname().replace('{slash}','/')
  bm[pair]=p.GetNetname().replace('{slash}','/')
assert all(bm[pair]==n for pair,n in new.items()),('PCB map delta',[(p,n,bm.get(p)) for p,n in new.items() if bm.get(p)!=n])
tr=json.loads((O/'transaction.json').read_text());meta=json.loads((O/'source-schematic-evidence/selected-part-metadata.json').read_text())['parts'];fp=[]
for d in tr['footprint_changes']:
 f=fps[d['ref']];p=meta[d['ref']];assert xy(f.GetPosition())==d['at'] and f.GetOrientationDegrees()==d['angle'] and f.GetLayer()==k.B_Cu;assert f.GetValue()==p['value'] and f.GetField('LCSC').GetText()==p['lcsc'] and f.GetField('Description').GetText()==p['note'] and f.GetFPID().GetLibItemName()==p['fp'].split(':')[1];pads=[]
 for q in f.Pads():
  r=next(x for x in d['pads'] if x['uuid']==uid(q));assert xy(q.GetPosition())==r['at'] and xy(q.GetSize())==r['size'] and q.GetNetname()==r['net'] and q.GetShape()==k.PAD_SHAPE_RECT
  assert q.IsOnLayer(k.B_Cu) and q.IsOnLayer(k.B_Mask) and q.IsOnLayer(k.B_Paste) and not q.IsOnLayer(k.F_Paste)
  if d['ref'] in ['C27','C31']:assert q.GetLocalSolderMaskMargin() in [None,0] and q.GetLocalSolderPasteMargin() in [None,0] and q.GetLocalSolderPasteMarginRatio() in [None,0]
  pads.append({'uuid':uid(q),'number':q.GetNumber(),'net':q.GetNetname(),'position':xy(q.GetPosition()),'size':xy(q.GetSize())})
 fp.append({'reference':d['ref'],'native_position':xy(f.GetPosition()),'raw_rotation_degrees':f.GetOrientationDegrees(),'footprint':str(f.GetFPID().GetLibNickname())+':'+str(f.GetFPID().GetLibItemName()),'value':f.GetValue(),'LCSC':f.GetField('LCSC').GetText(),'description':f.GetField('Description').GetText(),'schematic_path':str(f.GetPath().AsString()),'pads':pads})
# Actual WIP BOM/CPL, preserving every unrelated part row and exact native placement.
def load(label,kind):
 rows=list(csv.DictReader((O/'wip-bom-cpl'/label/f'nexus-style-fc-{kind}-jlc.csv').open()));out={}
 for r in rows:
  for ref in r['Designator'].split(','):out[ref]={k:v for k,v in r.items() if k!='Designator'}
 return out
ba,bb=load('source','bom'),load('candidate','bom');ca,cb=load('source','cpl'),load('candidate','cpl');assert set(bb)-set(ba)==set(cb)-set(ca)=={'C31'} and not set(ba)-set(bb) and not set(ca)-set(cb);assert all(ba[r]==bb[r] for r in ba if r!='C27');assert all(ca[r]==cb[r] for r in ca if r not in ['C27','D5']);
for r in ['C27','C31']:assert bb[r]=={'Comment':'22uF','Footprint':'C_0805_2012Metric_Samsung_CL21_MinLand','LCSC Part #':'C602037'}
origin=b.GetDesignSettings().GetAuxOrigin();cpl=[]
for r in ['C27','C31','D5']:
 f=fps[r];pos=f.GetPosition();row=cb[r];expected={'Mid X':f'{(pos.x-origin.x)/1e6:.4f}mm','Mid Y':f'{-(pos.y-origin.y)/1e6:.4f}mm','Layer':'Bottom','Rotation':f'{f.GetOrientationDegrees()%360:.0f}'};assert row==expected,(r,row,expected);cpl.append({'ref':r,'native_raw_position':xy(pos),'drill_origin':xy(origin),'actual_CPL':row})
# Determine the exact minimum new-object foreign copper gap within 0.300 mm.
objects={uid(x):x for x in b.GetTracks()};objects.update({uid(p):p for f in b.GetFootprints() for p in f.Pads()});objects.update({uid(x):x for x in b.GetDrawings() if isinstance(x,k.PCB_SHAPE) and x.GetLayer() in list(b.GetEnabledLayers().CuStack())});changed={r['uuid'] for r in tr['added_primitives']}|{r['uuid'] for r in tr['moved_vias']}|{p['uuid'] for f in tr['footprint_changes'] for p in f['pads']};ls=list(b.GetEnabledLayers().CuStack());closest=None;seen=set()
def hit(a,b,c):
 r=k.SHAPE.Collide(a,b,c);return r[0] if isinstance(r,tuple) else bool(r)
for u in changed:
 p=objects[u];box=p.GetBoundingBox();box.Inflate(300001)
 for w,q in objects.items():
  if u==w or p.GetNetname()==q.GetNetname() or not box.Intersects(q.GetBoundingBox()):continue
  for l in ls:
   key=(min(u,w),max(u,w),l)
   if key in seen or not p.IsOnLayer(l) or not q.IsOnLayer(l):continue
   seen.add(key);a,z=p.GetEffectiveShape(l),q.GetEffectiveShape(l)
   if not hit(a,z,300001):continue
   lo,hi=0,300001
   while hi-lo>1:
    mid=(lo+hi)//2
    if hit(a,z,mid):hi=mid
    else:lo=mid
   row={'new_uuid':u,'other_uuid':w,'nets':[p.GetNetname(),q.GetNetname()],'layer':b.GetLayerName(l),'native_shape_clearance_interval_mm':[lo/1e6,hi/1e6]}
   if closest is None or lo<closest['native_shape_clearance_interval_mm'][0]*1e6:closest=row
assert closest and closest['native_shape_clearance_interval_mm'][0]>=.127,closest
out={'status':'PASS fresh 349-pin parity, exact approved instance metadata/geometry and actual native WIP BOM/CPL selection','candidate_sha256':sha(O/'hardware/nexus-style-fc.kicad_pcb'),'source_pin_count':347,'candidate_pin_count':349,'all_original_pin_nets_exact':True,'export_format_normalization':'Fresh KiCad S-expression net export escapes slash in exactly the two pre-existing U2.9 and U14.1 unconnected net names as {slash}; old XML retains / while native PCB matches the fresh S-expression spelling. Only those exact two strings are decoded for semantic pin-map comparison. All other names are exact.','added_pin_pairs':[{'ref':'C31','pin':'1','net':'VSYS'},{'ref':'C31','pin':'2','net':'GND'}],'native_instance_proof':fp,'BOM_part_count_before':len(ba),'BOM_part_count_after':len(bb),'BOM_only_changed_existing_row':'C27','CPL_only_changed_existing_rows':['C27','D5'],'added_BOM_CPL_ref':'C31','native_CPL_position_proof':cpl,'minimum_changed_copper_gap':closest,'qualification':'BOM/CPL diagnostic exports only; custom minimum land, capacitor bias/tolerance, under-body tenting, assembly and HF input behavior remain qualification gates.'};(O/'source-export-verification.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
