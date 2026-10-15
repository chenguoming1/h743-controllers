from pathlib import Path
import sys,json,hashlib,re,math,collections,zipfile,csv,datetime,shutil
import pcbnew as P
R=Path('/workspace/scratch/8a35c1f26232/nexus-recovery-20261015');S=R/'mechanical-integration/main-assembly-annotation-10';O=R/'mechanical-integration/main-assembly-annotation-10-manufacturing-review';sys.path.insert(0,str(R/'assembly-annotation-cleanup'));import guarded_cleanup as G
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();rows=[]
def gerber_segments(p):
 lines=p.read_text().splitlines();mode=1;pos=None;out=[];ap=None;aps={};pol='D'
 for line in lines:
  m=re.fullmatch(r'%ADD(\d+)C,([\d.]+)\*%',line)
  if m:aps[int(m[1])]=float(m[2]);continue
  m=re.fullmatch(r'D(\d+)\*',line)
  if m:ap=int(m[1]);continue
  if line in ['G01*','G02*','G03*']:mode=int(line[1:3]);continue
  if line in ['%LPD*%','%LPC*%']:pol=line[3];continue
  m=re.fullmatch(r'X(-?\d+)Y(-?\d+)(?:I(-?\d+)J(-?\d+))?D0([123])\*',line)
  if not m:continue
  end=(int(m[1])/1e6,int(m[2])/1e6);d=int(m[5])
  if d==1:
   assert pos is not None;mid=None;center=None
   if mode!=1:
    assert m[3] is not None;center=(pos[0]+int(m[3])/1e6,pos[1]+int(m[4])/1e6);a=math.atan2(pos[1]-center[1],pos[0]-center[0]);b=math.atan2(end[1]-center[1],end[0]-center[0]);sweep=(b-a)%(2*math.pi) if mode==3 else -((a-b)%(2*math.pi));rad=math.dist(pos,center);mid=(center[0]+rad*math.cos(a+sweep/2),center[1]+rad*math.sin(a+sweep/2))
   out.append({'start':pos,'end':end,'mid':mid,'center':center,'aperture':aps.get(ap),'polarity':pol})
  pos=end
 return out
for name,rel,ncu in [('nexus-style-fc','hardware/nexus-style-fc.kicad_pcb',6),('nexus-header-board','hardware/header-board/nexus-header-board.kicad_pcb',2)]:
 d=O/name;g=d/'gerbers';archive=d/(name+'-gerbers.zip');files=sorted(p.name for p in g.iterdir() if p.is_file());expected={name+'-'+x for x in ['F_Cu.gtl','B_Cu.gbl','F_Mask.gts','B_Mask.gbs','F_Paste.gtp','B_Paste.gbp','F_Silkscreen.gto','B_Silkscreen.gbo','Edge_Cuts.gm1','PTH.drl','NPTH.drl','job.gbrjob']+[f'In{i}_Cu.g{i}' for i in range(1,ncu-1)]};assert set(files)==expected
 with zipfile.ZipFile(archive) as z:
  assert z.testzip() is None and set(z.namelist())==set(files)
  for f in files:assert z.read(f)==(g/f).read_bytes(),f
 for p in g.iterdir():
  if p.suffix not in ['.drl','.gbrjob']:assert '%FSLAX46Y46*%' in p.read_text() and '%MOMM*%' in p.read_text() and p.read_text().rstrip().endswith('M02*'),p
 b=P.LoadBoard(str(S/rel));ox,oy=[P.ToMM(v) for v in (b.GetDesignSettings().GetAuxOrigin().x,b.GetDesignSettings().GetAuxOrigin().y)];native_expected=[]
 for t in b.GetTracks():
  if isinstance(t,P.PCB_VIA):native_expected.append(('PTH',P.ToMM(t.GetDrillValue()),P.ToMM(t.GetPosition().x)-ox,oy-P.ToMM(t.GetPosition().y),'round'))
 oval_expected=[]
 for f in b.GetFootprints():
  for p in f.Pads():
   ds=p.GetDrillSize();dx,dy=P.ToMM(ds.x),P.ToMM(ds.y)
   if not max(dx,dy):continue
   plating='NPTH' if p.GetAttribute()==P.PAD_ATTRIB_NPTH else 'PTH';x,y=P.ToMM(p.GetPosition().x)-ox,oy-P.ToMM(p.GetPosition().y)
   if abs(dx-dy)<1e-9:native_expected.append((plating,dx,x,y,'round'))
   else:oval_expected.append({'plating':plating,'diameter':min(dx,dy),'center':[x,y],'route_length':abs(dx-dy),'pad':f.GetReference()+'.'+p.GetNumber()})
 drill_counts={};max_quant=0;actual=[];actual_ovals=[]
 for plating in ['PTH','NPTH']:
  text=(g/(name+'-'+plating+'.drl')).read_text();assert 'METRIC' in text and '; FORMAT={-:-/ absolute / metric / decimal}' in text;tools={int(a):float(b) for a,b in re.findall(r'^T(\d+)C([\d.]+)$',text,re.M)};tool=None;route_start=None;rounds=0;ovals=0
  for line in text.splitlines():
   m=re.fullmatch(r'T(\d+)',line)
   if m:tool=int(m[1]);continue
   m=re.fullmatch(r'(G00|G01)?X(-?[\d.]+)Y(-?[\d.]+)',line)
   if not m:continue
   q=(float(m[2]),float(m[3]));assert tool in tools
   if m[1]=='G00':route_start=q
   elif m[1]=='G01':assert route_start;actual_ovals.append({'plating':plating,'diameter':tools[tool],'center':[(q[0]+route_start[0])/2,(q[1]+route_start[1])/2],'route_length':math.dist(q,route_start)});ovals+=1;route_start=None
   else:actual.append((plating,tools[tool],q[0],q[1],'round'));rounds+=1
  drill_counts[plating]={'round_hits':rounds,'routed_slots':ovals,'tools_mm':tools}
 assert len(actual)==len(native_expected)
 remaining=actual.copy()
 for e in native_expected:
  candidates=[(math.hypot(a[2]-e[2],a[3]-e[3]),i) for i,a in enumerate(remaining) if a[0]==e[0] and a[1]==round(e[1],3)];assert candidates,e;dist,i=min(candidates);assert abs(remaining[i][2]-e[2])<=.0005001 and abs(remaining[i][3]-e[3])<=.0005001,(e,remaining[i]);max_quant=max(max_quant,dist);remaining.pop(i)
 assert not remaining and len(actual_ovals)==len(oval_expected)
 for e in oval_expected:
  hits=[a for a in actual_ovals if a['plating']==e['plating'] and a['diameter']==round(e['diameter'],3) and math.dist(a['center'],e['center'])<.00071 and abs(a['route_length']-e['route_length'])<.00101];assert len(hits)==1,e
 # Compare every actual exported contour segment and arc midpoint to source geometry.
 root=G.parse((S/rel).read_text());expected_edges=[]
 def add_edges(parent,off=(0,0)):
  for q in parent.items:
   if isinstance(q,G.Node) and q.tag in ['gr_line','gr_arc','fp_line','fp_arc'] and q.val('layer')=='Edge.Cuts':
    def xy(k):a=q.one(k).items[1:3];return (float(a[0])+off[0]-ox,oy-float(a[1])-off[1])
    expected_edges.append({'start':xy('start'),'end':xy('end'),'mid':xy('mid') if q.tag.endswith('_arc') else None})
 add_edges(root)
 for f in root.children('footprint'):
  e=[q for q in f.items if isinstance(q,G.Node) and q.tag in ['fp_line','fp_arc'] and q.val('layer')=='Edge.Cuts']
  if e:
   at=f.one('at').items[1:];assert len(at)<3 or float(at[2])==0;assert f.val('layer')=='F.Cu';add_edges(f,tuple(map(float,at[:2])))
 parsed=gerber_segments(g/(name+'-Edge_Cuts.gm1'));assert len(parsed)==len(expected_edges),(len(parsed),len(expected_edges));remaining=parsed.copy();errmax=0
 for e in expected_edges:
  hits=[]
  for i,a in enumerate(remaining):
   if (a['mid'] is None)!=(e['mid'] is None):continue
   err=min(max(math.dist(a['start'],e['start']),math.dist(a['end'],e['end'])),max(math.dist(a['start'],e['end']),math.dist(a['end'],e['start'])))
   if e['mid'] is not None:err=max(err,math.dist(a['mid'],e['mid']))
   if err<=.0000016:hits.append((err,i))
  assert len(hits)==1,(e,hits);err,i=hits[0];errmax=max(errmax,err);remaining.pop(i)
 bom=list(csv.DictReader((d/(name+'-bom-jlc.csv')).open()));cpl=list(csv.DictReader((d/(name+'-cpl-jlc.csv')).open()));refs={r for q in bom for r in q['Designator'].split(',')};assert refs=={q['Designator'] for q in cpl}
 if name=='nexus-style-fc':
  assert len(refs)==83
  for filename in [name+'-bom-jlc.csv',name+'-cpl-jlc.csv']:assert (d/filename).read_bytes()==(S/'wip-bom-cpl'/filename).read_bytes()
 else:assert refs=={'J1'} and b.FindFootprintByReference('J1').GetAttributes() & P.FP_THROUGH_HOLE
 rows.append({'board':name,'PCB_sha256':sha(S/rel),'zip':str(archive.relative_to(O)),'zip_sha256':sha(archive),'zip_CRC_and_entries_exact':True,'plot_files':files,'copper_layer_count':ncu,'drills':drill_counts,'native_to_Excellon_max_center_quantization_mm':max_quant,'all_native_holes_and_routed_slots_accounted':True,'diameters_exact_to_native_rounded_3_decimal_mm':True,'max_drill_diameter_quantization_mm':max([abs(round(e[1],3)-e[1]) for e in native_expected]+[abs(round(e['diameter'],3)-e['diameter']) for e in oval_expected]+[0]),'all_exported_contours_match_source':True,'contour_segments_and_arcs':len(parsed),'max_contour_geometry_error_mm':errmax,'BOM_rows':len(bom),'selected_parts':len(refs),'BOM_sha256':sha(d/(name+'-bom-jlc.csv')),'CPL_sha256':sha(d/(name+'-cpl-jlc.csv')),'assembly_note':'83 selected main placements, mixed J6 and manual J1 process remain explicit' if name=='nexus-style-fc' else 'Only J1 servo header C32713294 is exported. It is through-hole; its CPL row is not an SMT placement approval. Tab/joint contacts are manual.'})
# Mask-subtracted CAM retains a closed pair of 0.075 mm-radius arcs with0.150 mm stroke for each .300 mm dot.
g=O/'nexus-style-fc/gerbers/nexus-style-fc-F_Silkscreen.gto';shapes=gerber_segments(g);dots=[]
for ref,x in [('D1',7.25),('D2',13.65),('D3',10.45)]:
 arcs=[a for a in shapes if a['center'] and math.dist(a['center'],(x,6.9))<1e-8 and abs(a['aperture']-.15)<1e-9 and a['polarity']=='D'];assert len(arcs)==2 and all(abs(math.dist(a['start'],a['center'])-.075)<1e-9 for a in arcs);dots.append({'ref':ref,'center_mm':[x,6.9],'CAM_full_circle_stroke_outer_diameter_mm':.3,'closed_two_half_arcs':True})
out={'status':'PASS source-bound unreleased manufacturing exports; remote DFM and production qualification pending','source_seal_sha256':sha(S/'FINAL-SEAL.json'),'source_manifest_sha256':sha(S/'evidence-manifest.json'),'boards':rows,'printed_cathode_CAM_witnesses':dots,'stack_caveat':'Main nominal1.600 mm; copper/dielectric sum1.6168 mm and mask-inclusive sum1.6368 mm. Child nominal1.600 mm with no detailed stack. Native job files preserve these inputs; actual finished stack not selected or qualified.','scope':'Native export integrity, exact outlines, hole inventory/origin/rounding, layer files, archive and BOM/CPL source binding. Not a complete independent Gerber copper-clearance or factory DFM signoff.'};(O/'verification.json').write_text(json.dumps(out,indent=2)+'\n');shutil.copy2(__file__,O/Path(__file__).name);print(json.dumps(out,indent=2))
