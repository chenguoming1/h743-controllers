exec(open('/workspace/scratch/8a35c1f26232/nexus-recovery-20261015/r57-buck-review/inspect.py').read().split("out={'source_sha256'")[0])
import uuid,collections
O=R/'r57-buck-review';sourcehash=hashlib.sha256(P.read_bytes()).hexdigest();vec=lambda p:k.VECTOR2I(round(p[0]*1e6),round(p[1]*1e6))
def hit(a,z,c=0):
 r=k.SHAPE.Collide(a,z,c);return r[0] if isinstance(r,tuple) else bool(r)
def poly(t,l):
 q=k.SHAPE_POLY_SET();t.TransformShapeToPolygon(q,l,0,50,k.ERROR_OUTSIDE);return q
def circle(c,r):
 q=k.SHAPE_POLY_SET();p=k.SHAPE_LINE_CHAIN()
 for i in range(1024):
  a=2*math.pi*i/1024;p.Append(vec((c[0]+r*math.cos(a),c[1]+r*math.sin(a))))
 p.SetClosed(True);q.AddOutline(p);return q
def area(p):return abs(p.Area())/1e12
exec((R/'r56-offcenter-contact-review/patch_function.py').read_text())
changes={'0097f17a-a60a-4d12-973b-5461dabae78d':('start',(104.575,113.925),'a33d9038-104a-4904-836a-f2c168df6d4c'),'961eede3-9481-48f8-b1ce-59d89e287a7d':('start',(104.575,113.925),'a33d9038-104a-4904-836a-f2c168df6d4c'),'eba8ff79-64eb-43fc-a9c1-492395d73f30':('end',(104.575,113.925),'a33d9038-104a-4904-836a-f2c168df6d4c'),'8fde276c-ea86-49b6-b2c1-c7966a02f478':('start',(103.259295,112.45),'51a22cd5-55d6-4b2a-ab4e-1419692162c2')}
new={};repls=[]
for u,(which,p,vuid) in changes.items():
 t=ts[u];n=k.PCB_TRACK(b);n.SetStart(t.GetStart());n.SetEnd(t.GetEnd());n.SetLayer(t.GetLayer());n.SetWidth(t.GetWidth());n.SetNetCode(t.GetNetCode());getattr(n,'Set'+which.title())(vec(p));new[u]=n;d=info(n);d['uuid']=str(uuid.uuid5(uuid.NAMESPACE_URL,'nexus/r57-buck-centered-annuli/'+u));repls.append({'source_uuid':u,'source':info(t),'replacement':d,'target_via':info(ts[vuid]),'changed_endpoint':which})
combined={**ts,**ps,**new};pairs=[];obstacles=[];proofs=[];external={}
for u,n in new.items():
 t=ts[u];l=t.GetLayer();ports=[]
 for w,o in {**ts,**ps}.items():
  if w==u or not o.IsOnLayer(l):continue
  no=combined[w]
  if o.GetNetCode()==t.GetNetCode():
   if hit(t.GetEffectiveShape(l),o.GetEffectiveShape(l)):
    overlap=poly(n,l);overlap.BooleanIntersection(poly(no,l));assert area(overlap)>1e-8,('lost finite contact',u,w);pairs.append({'source_track':u,'source_port':w,'replacement_track':next(r['replacement']['uuid'] for r in repls if r['source_uuid']==u),'source_port_kind':type(o).__name__,'layer':b.GetLayerName(l),'new_intersection_area_mm2':area(overlap),'source_port_replaced':w in new});ports.append(w)
    if w not in new:external[w]=info(o)
  elif hit(n.GetEffectiveShape(l),o.GetEffectiveShape(l),127002):obstacles.append({'track':u,'obstacle':info(o),'layer':b.GetLayerName(l)})
 v=ts[changes[u][2]];ann=poly(v,l);ann.BooleanSubtract(circle(xy(v.GetPosition()),v.GetDrillValue()/2e6));source_overlap=poly(t,l);source_overlap.BooleanIntersection(ann);new_overlap=poly(n,l);new_overlap.BooleanIntersection(ann);remaining=k.SHAPE_POLY_SET(ann);remaining.BooleanSubtract(poly(n,l));fullpatch=finite_patch(n,v,.02);centered=xy(n.GetStart())==xy(v.GetPosition()) or xy(n.GetEnd())==xy(v.GetPosition());assert centered;whole=area(remaining)<1e-8;assert whole or fullpatch,(u,area(remaining));proofs.append({'source_track':u,'via':uid(v),'track_width_mm':t.GetWidth()/1e6,'centered':centered,'annular_area_mm2':area(ann),'old_track_annular_contact_mm2':area(source_overlap),'new_track_annular_contact_mm2':area(new_overlap),'whole_annulus_contained_by_track':whole,'uncovered_annular_area_mm2':area(remaining),'centered_round_end_cap_radial_margin_to_land_mm':(n.GetWidth()-v.GetWidth(l))/2e6,'full_width_0_020_mm_rectangle':fullpatch,'explanation':'Entire 0.450 mm land, including all finite annular copper outside 0.200 mm drill, lies inside the centered 0.500 mm round track cap.' if whole else 'Narrower 0.375 mm track retains an explicit finite full-width rectangle outside the drill; other 0.500 mm donors cover the full annulus.'})
assert not obstacles,obstacles
# Full net topology is taken from direct native physical connectivity, not net name alone.
inv=json.loads((O/'inventory.json').read_text());invmap={x['uuid']:x for x in inv['all_5V_BUCK']}
def path(a,z):
 q=collections.deque([[a]]);seen={a}
 while q:
  p=q.popleft()
  if p[-1]==z:return p
  for n in invmap[p[-1]]['connected']:
   if n not in seen:seen.add(n);q.append(p+[n])
 raise AssertionError((a,z))
L1='51344573-e135-4cba-8521-b809d86da7da';branches=[]
for target in ['7dce48cf-7158-4f7f-abb5-73207c7640b2','c20c9ea5-99b2-4a56-8b20-f4a915c7ddf3','ff3c0e6c-9533-4fb1-8719-c97231c99e78','33fff768-e003-439c-bf7b-71b5ae2c8277','64044ac8-2d13-4e3f-9fd2-6b7becd8e281','68292b28-ecad-431a-a670-083f4a28699d']:
 p=path(L1,target);branches.append({'from':'L1.2','to':invmap[target]['ref']+'.'+invmap[target]['pin'],'path':p,'path_items':[invmap[u] for u in p],'track_widths_mm':sorted(set(invmap[u]['width'] for u in p if 'width' in invmap[u]))})
# Rejected larger same-location lands are evaluated without adding or saving board objects.
large=[]
for vu in ['a33d9038-104a-4904-836a-f2c168df6d4c','51a22cd5-55d6-4b2a-ab4e-1419692162c2']:
 v=ts[vu];p=xy(v.GetPosition());s=k.SHAPE_CIRCLE(vec(p),300000);obs=[]
 for w,o in {**ts,**ps}.items():
  if w==vu or o.GetNetCode()==v.GetNetCode():continue
  for l in ls:
   if o.IsOnLayer(l) and hit(s,o.GetEffectiveShape(l),127002):obs.append({'object':info(o),'layer':b.GetLayerName(l)})
 large.append({'via':vu,'candidate_diameter_mm':.6,'position':p,'obstructions':obs})
tr={'status':'PROPOSAL ONLY: source unchanged; same-width centered junctions pass finite geometric and foreign track/pad/via clearance screens. Native refill, all-visible DRC and return validation remain required.','source_board':str(P),'source_board_sha256':sourcehash,'source_schematic_sha256':hashlib.sha256(P.with_suffix('.kicad_sch').read_bytes()).hexdigest(),'operation':'Replace exactly four track segments, preserving each original net, layer, width and remote endpoint. Keep every via unchanged.','replacements':repls,'expected_external_ports':list(external.values()),'source_contacts_preserved':pairs,'target_annular_proofs':proofs,'new_obstructions_at_0_127002_mm':obstacles,'unchanged_vias':['a33d9038-104a-4904-836a-f2c168df6d4c','51a22cd5-55d6-4b2a-ab4e-1419692162c2'],'restrictions':['No part, placement, pad, net, rule, layer, outline, via, paste, mask, thermal, or protection-return edits.','No power-width reduction.','No warning severity change, waiver, exclusion, or current-rating inference.','Invalidate if source SHA256 or any complete source item changes.','Heavy-lane owner must apply to isolated candidate, refill, compare all-visible diagnostics and validate all protected return and pad contacts before acceptance.'],'acceptance_gates':['Native full refill and DRC including all track errors and schematic parity, zero new violations or opens.','Compare all-visible diagnostic finding identities; remove exactly these four centering findings, preserve every other inherited diagnostic.','Original pad copper, paste, mask, via geometry, source support files and footprints unchanged.','Source donor physical connectivity and finite annular coverage reverified after refill.','Protected ground/protection/thermal return continuity and named parent validation suite pass.','Power ampacity, regulator layout and fabrication signoff remain separate open gates.']}
(O/'transaction-proposal.json').write_text(json.dumps(tr,indent=2)+'\n')
review={'source_board_sha256':sourcehash,'topology_inventory':'inventory.json','net_objects':len(invmap),'all_net_pad_terminals':[x for x in invmap.values() if x['type']=='PAD'],'source_physical_branch_paths':branches,'target_annular_proofs':proofs,'larger_land_option':{'same_corridor_maximum_diameter_at_0_127_clearance_mm':.546,'gap_width_mm':.8,'minimum_circular_land_diameter_for_centered_0_5_by_0_02_rectangle_outside_0_2_drill_with_0_001_margin_mm':2*math.hypot(.25,.121),'same_location_0_6_mm_obstruction_screen':large,'limitation':'This rejects local enlargement under the full-width J2 pad strip, not every remote location. A relocated larger via would need materially more routing and a complete donor/return screen.'},'parallel_via_option':{'recommendation':'Not required to correct these four off-center entries. A parallel ordinary via is a distinct load-current/fabrication design choice, not a geometric necessity or proven current rating. No new barrel is proposed without a validated all-layer position and explicit current-stackup criterion.','existing_single_via_main_load_transfer':'a33d9038-104a-4904-836a-f2c168df6d4c','sense_only_branch_via':'51a22cd5-55d6-4b2a-ab4e-1419692162c2'},'manufacturer_context':[{'device':'U5 TPS62130RGTR','source':'https://www.ti.com/lit/gpn/TPS62130','sections':['6, pin 14 VOS','11.1 Layout Guidelines'],'finding':'VOS is output-voltage sensing/control, not the load-current output. TI calls for a short dedicated connection to the output capacitor, away from the VOUT power route and SW, with common AGND/PGND/thermal ground. Existing branch at 51a22cd5 taps the L1-to-C24 power route upstream of C24; this existing topology is preserved, and regulator-layout signoff remains open.'},{'device':'U9 TPS2116DRLR','source':'https://www.ti.com/lit/ds/symlink/tps2116.pdf','sections':['5 Pin Configuration and Functions'],'finding':'U9 pin 3 VIN1 is the load-supply input, while pin 5 MODE is a logic/configuration input. Thus a33d9038 transfers the downstream load branch; 51a22cd5 only serves the U5 VOS branch. Existing 0.127 mm necks at U9 are unchanged and are not certified by this review.'}],'no_ampacity_claim':'Annular area, full land coverage, trace widths and device labels do not establish allowable current, plating quality, temperature rise or assembled-board power capability.','verification_scope':'Read-only native geometric checks; no board save, zone refill, DRC, router, GitHub write or user-computer access.'}
(O/'review.json').write_text(json.dumps(review,indent=2)+'\n');assert hashlib.sha256(P.read_bytes()).hexdigest()==sourcehash;print(json.dumps({'source':sourcehash,'replacements':len(repls),'contacts_preserved':len(pairs),'external_ports':len(external),'obstructions':len(obstacles),'annular_proofs':proofs,'larger_land_obstructions':large},indent=2))
