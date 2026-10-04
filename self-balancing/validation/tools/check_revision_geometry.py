#!/usr/bin/python3
"""Read-only, exact-hash P5 -> P6 semantic and copper reference audit.

Never saves a native board. Report files belong to the independent review only.
"""
import argparse, collections, copy, hashlib, json, math, os, pathlib, re, xml.etree.ElementTree as ET
os.environ.setdefault('KICAD_CONFIG_HOME', '/tmp/controller-r3-kicad')
import pcbnew as p
from approved_cleanup_common import load_cleanup

ap = argparse.ArgumentParser()
ap.add_argument('--baseline', type=pathlib.Path, required=True)
ap.add_argument('--project', type=pathlib.Path, required=True)
ap.add_argument('--sha256', required=True)
ap.add_argument('--out', type=pathlib.Path, required=True)
ap.add_argument('--exceptions',type=pathlib.Path,help='Parent-reviewed exact protected/GND delta packet; never allows USB changes')
ap.add_argument('--selfcheck',action='store_true',help='Baseline harness self-check only; cannot certify a P6 candidate')
a = ap.parse_args()
A, B, O = a.baseline.resolve(), a.project.resolve(), a.out.resolve()
O.mkdir(parents=True, exist_ok=True)
sha = lambda x: hashlib.sha256(x.read_bytes()).hexdigest()
expected_old = '6e2031b040ce8f3a534c2f73abb0091e25b3e6adcab982463264ad8898d65cf8'
assert sha(A/'controller.kicad_pcb') == expected_old
assert sha(B/'controller.kicad_pcb') == a.sha256
exceptions=json.loads(a.exceptions.read_text()) if a.exceptions else {}
cleanup=load_cleanup(exceptions,a.sha256)
retired_vias={q['uuid'] for q in cleanup['removed_via_records']} if cleanup else set()
old = p.LoadBoard(str(A/'controller.kicad_pcb'))
new = p.LoadBoard(str(B/'controller.kicad_pcb'))
errors, facts = [], {}
def check(ok, message):
    if not ok: errors.append(message)
uid = lambda x: x.m_Uuid.AsString()
xy = lambda x: [x.x, x.y]
mmxy = lambda x: [round(p.ToMM(x.x), 6), round(p.ToMM(x.y), 6)]

def parse(path):
    tokens = re.findall(r'"(?:\\.|[^"\\])*"|[^\s()]+|[()]', path.read_text())
    stack, root = [], None
    for t in tokens:
        if t == '(':
            x = []
            if stack: stack[-1].append(x)
            stack.append(x)
        elif t == ')':
            root = stack.pop()
        else:
            stack[-1].append(t)
    assert not stack
    return root
def child(node, tag): return next((n for n in node if isinstance(n,list) and n and n[0]==tag),None)
def ident(node):
    u=child(node,'uuid')
    return u[1] if u else None
def footprint_nodes(path):
    root=parse(path)
    return {ident(n):n for n in root if isinstance(n,list) and n and n[0]=='footprint'}

af, bf = footprint_nodes(A/'controller.kicad_pcb'), footprint_nodes(B/'controller.kicad_pcb')
check(af==bf, 'Any footprint/component/pad/text/placement/3D-model semantic changed')
facts['footprints']={'count':len(af),'identical':af==bf}
pad_changes=[]
old_j2=next(f for f in old.GetFootprints() if f.GetReference()=='J2')
target_pads={uid(q) for q in old_j2.Pads() if q.GetNumber()=='S1' and xy(q.GetDrillSize())==[600000,1400000]}
check(len(target_pads)==2,'P5 front shell slot identification differs')

def stable_board(root):
    root=copy.deepcopy(root)
    for n in list(root):
        if not isinstance(n,list) or not n:continue
        if n[0] in ['segment','arc']:root.remove(n)
        elif n[0]=='via' and ident(n).strip('"') in retired_vias:root.remove(n)
        elif n[0]=='zone':
            n[:]=[q for q in n if not (isinstance(q,list) and q and q[0] in ['filled_polygon','fill_segments'])]
        elif n[0]=='title_block':
            rev=child(n,'rev')
            if rev and rev[1]=='"R3-S6-P6"':rev[1]='"R3-S6-P5"'
    return root
check(stable_board(parse(A/'controller.kicad_pcb'))==stable_board(parse(B/'controller.kicad_pcb')), 'Non-track native semantic change, including via/outline/stack/setup/zones/net definitions')
check(old.GetCopperLayerCount()==new.GetCopperLayerCount()==6,'Six-layer stack changed')
facts['semantic_board_exclusions']=['segment/arc geometry','zone fill polygon cache','exact title revision R3-S6-P5 to R3-S6-P6']
if cleanup:facts['semantic_board_exclusions'].append('Exactly six proven redundant one-layer/dead-tree vias');facts['approved_redundant_via_cleanup']=cleanup

immutable=['review/design-netmap.json','review/bom-draft.csv','inputs/user-corrected-JLC_CPL.csv','review/controller-r3s-independent-expectations.json','controller.kicad_pro','controller.kicad_dru','fp-lib-table','sym-lib-table','review/pad-wiring-map.csv','review/edge-pad-map.json','review/h743-pin-map.json','review/assembly-cpl-overrides.json','review/manufacturing-profile.json']
file_checks=[]
for name in immutable:
    ok=(B/name).is_file() and sha(A/name)==sha(B/name)
    metadata=False
    if not ok and name=='review/manufacturing-profile.json' and exceptions.get('manufacturing_metadata'):
        spec=exceptions['manufacturing_metadata'];before=json.loads((A/name).read_text());after=json.loads((B/name).read_text());normalized=copy.deepcopy(after)
        normalized.pop('assembly_production_requirements',None);normalized['via_process'].pop('covering',None);normalized['via_process']['limits']=before['via_process']['limits']
        metadata=normalized==before and spec['baseline_sha256']==sha(A/name) and spec['candidate_sha256']==sha(B/name)
        ok=metadata
    check(ok,'Input changed: '+name)
    file_checks.append({'path':name,'unchanged':ok and not metadata,'approved_descriptive_process_delta':metadata,'sha256':sha(B/name) if (B/name).is_file() else None})
for path in A.glob('*.kicad_sch'):
    current=B/path.name
    ok=current.is_file() and path.read_text()==current.read_text().replace('(rev "R3-S6-P6")','(rev "R3-S6-P5")')
    check(ok,'Schematic change exceeds P5-to-P6 title revision: '+path.name)
    file_checks.append({'path':path.name,'unchanged_except_title_revision':ok,'sha256':sha(current) if current.is_file() else None})
netlist='review/controller-netlist.xml'
if (B/netlist).is_file():
    ax,bx=ET.parse(A/netlist).getroot(),ET.parse(B/netlist).getroot()
    xok=all(ET.tostring(ax.find(tag))==ET.tostring(bx.find(tag)) for tag in ['components','libparts','nets'])
    normalize_root=lambda data:data.replace(str(A).encode(),b'PROJECT_ROOT').replace(str(B).encode(),b'PROJECT_ROOT')
    xok=xok and normalize_root(ET.tostring(ax.find('libraries')))==normalize_root(ET.tostring(bx.find('libraries')))
    ad,bd=copy.deepcopy(ax.find('design')),copy.deepcopy(bx.find('design'))
    export_dates={'before':ad.findtext('date'),'after':bd.findtext('date')}
    ad.find('date').text=bd.findtext('date')
    design_ok=normalize_root(ET.tostring(ad))==normalize_root(ET.tostring(bd)).replace(b'R3-S6-P6',b'R3-S6-P5')
    xok=xok and design_ok
    check(xok,'XML netlist semantic content changed')
    file_checks.append({'path':netlist,'unchanged_electrical_content':xok,'exact_metadata_normalization_pass':design_ok,'permitted_metadata':'Exact project-root substitution, P5-to-P6 revision strings, and export date only','export_dates':export_dates,'sha256':sha(B/netlist)})
else:check(False,'Missing XML netlist')
lib_changes=[]
for path in A.joinpath('library').rglob('*'):
    if not path.is_file(): continue
    rel=path.relative_to(A)
    if not (B/rel).is_file() or sha(path)!=sha(B/rel): lib_changes.append(str(rel))
check(not lib_changes,'Source library content changed')
check({str(x.relative_to(A/'library')) for x in (A/'library').rglob('*') if x.is_file()}=={str(x.relative_to(B/'library')) for x in (B/'library').rglob('*') if x.is_file()},'Source library file set changed')
facts['immutable_inputs']=file_checks
facts['library_changed_files']=lib_changes

def track_rec(t):
    r={'uuid':uid(t),'type':t.GetClass(),'net':t.GetNetname(),'start_nm':xy(t.GetStart()),'end_nm':xy(t.GetEnd()),'width_nm':t.GetWidth(p.F_Cu) if isinstance(t,p.PCB_VIA) else t.GetWidth()}
    if isinstance(t,p.PCB_VIA): r.update(drill_nm=t.GetDrillValue(),layers=[t.TopLayer(),t.BottomLayer()],via_type=int(t.GetViaType()),tented_front=t.IsTented(p.F_Cu),tented_back=t.IsTented(p.B_Cu))
    else:
        r['layer']=t.GetLayerName()
        if isinstance(t,p.PCB_ARC):r['mid_nm']=xy(t.GetMid())
    return r
at,bt={uid(t):track_rec(t) for t in old.GetTracks()},{uid(t):track_rec(t) for t in new.GetTracks()}
changes=[{'uuid':u,'before':at.get(u),'after':bt.get(u)} for u in sorted(at.keys()|bt.keys()) if at.get(u)!=bt.get(u)]
critical=lambda n:n.rsplit('/',1)[-1].startswith(('USB_DP','USB_DM','HSE_','BUCK_','VCAP'))
critical_changes=[c for c in changes if any(q and critical(q['net']) for q in [c['before'],c['after']])]
allowed_critical=exceptions.get('critical_changes',[])
if exceptions:
    check(exceptions.get('baseline_sha256')==expected_old and exceptions.get('candidate_sha256')==a.sha256,'Protected exception packet hash binding differs')
    check(all(all(not q or q['net'].rsplit('/',1)[-1].startswith('HSE_') for q in [c.get('before'),c.get('after')]) for c in allowed_critical),'Exception attempts to change protected non-HSE copper')
check(critical_changes==allowed_critical,'Protected USB/HSE/buck/VCAP geometry changed without exact independently reviewed exception')
facts['protected_exception_packet']={'path':str(a.exceptions) if a.exceptions else None,'sha256':sha(a.exceptions) if a.exceptions else None,'declared_critical_change_count':len(allowed_critical)}
ground_vias=[r for r in bt.values() if r['type']=='PCB_VIA' and r['net']=='GND']
check(len(ground_vias)==97,'Expected exact 97 retained ground vias')
facts['ground_via_count']=len(ground_vias)
via_changes=[c for c in changes if any(q and q['type']=='PCB_VIA' for q in [c['before'],c['after']])]
expected_via_changes=[{'uuid':q['uuid'],'before':q,'after':None} for q in cleanup['removed_via_records']] if cleanup else []
check(via_changes==expected_via_changes,'Via changes exceed exact approved retirement records')
facts['all_via_count']=sum(r['type']=='PCB_VIA' for r in bt.values())
usb_tracks=[r for r in bt.values() if r['type']!='PCB_VIA' and r['net'].rsplit('/',1)[-1].startswith(('USB_DP','USB_DM'))]
check(len(usb_tracks)==27 and all(r['width_nm']==139200 for r in usb_tracks),'Expected exact 27 USB 0.1392mm tracks')
facts['protected_USB_track_count']=len(usb_tracks)

power=lambda name:name in {'3V3_CORE','VLOGIC_IN','+5V_STACK','VDDA','IMU_3V3','USB_VBUS'} or name.startswith('/power/')
in_buck=lambda pt:2000000<=pt[0]<=11000000 and 6000000<=pt[1]<=14000000
buck_local={u:r for u,r in at.items() if r['type']!='PCB_VIA' and power(r['net']) and any(in_buck(pt) for pt in [r['start_nm'],r['end_nm']])}
changed_buck=[u for u,r in buck_local.items() if bt.get(u)!=r]
check(not changed_buck,'Protected buck-local power segment changed')
def ground_target(r):
    return r['type']!='PCB_VIA' and r.get('layer')=='F.Cu' and all(24500000<=pt[0]<=27200000 and 12500000<=pt[1]<=15500000 for pt in [r['start_nm'],r['end_nm']])
ground_changes=[c for c in changes if any(r and r['net']=='GND' for r in [c['before'],c['after']])]
extended_ground_changes=[c for c in ground_changes if any(not ground_target(r) for r in [c['before'],c['after']] if r)]
check(extended_ground_changes==exceptions.get('extended_ground_changes',[]),'GND change outside old front loop lacks exact independently reviewed declaration')
facts['local_protection']={'buck_power_rectangle_mm':[2,6,11,14],'buck_frozen_segment_count':len(buck_local),'changed_buck_segments':changed_buck,'allowed_GND_loop_rectangle_mm':[24.5,12.5,27.2,15.5],'GND_changed_objects':len(ground_changes),'declared_extended_GND_changed_objects':len(extended_ground_changes)}

facts['copper_delta']={'baseline_count':len(at),'candidate_count':len(bt),'changed_count':len(changes),'changes':changes,'critical_changes':critical_changes,'critical_objects_baseline':sum(critical(r['net']) for r in at.values()),'critical_objects_preserved':sum(critical(r['net']) and bt.get(u)==r for u,r in at.items()),'critical_objects_declared_changed':len(allowed_critical)}

def pad_sig(q):
    return (q.GetNumber(),*xy(q.GetPosition()),*xy(q.GetSize()),*xy(q.GetDrillSize()),q.GetOrientationDegrees()%360,int(q.GetShape()),int(q.GetDrillShape()),int(q.GetAttribute()),q.GetLayerSet().FmtHex(),*xy(q.GetOffset()),q.GetLocalSolderPasteMargin(),q.GetLocalSolderPasteMarginRatio(),q.GetLocalSolderMaskMargin())
source_matches=[]
library_board=p.BOARD()
for f in new.GetFootprints():
    lib,item=str(f.GetFPID().GetLibNickname()),str(f.GetFPID().GetLibItemName())
    if not lib:
        source_matches.append({'reference':f.GetReference(),'footprint':item,'source':'Board-local mechanical feature; full P5 semantic invariance checked','pads_match':True})
        continue
    local=B/'library'/f'{lib}.pretty'
    if not local.is_dir():local=pathlib.Path('/usr/share/kicad/footprints')/f'{lib}.pretty'
    check(local.is_dir(),'Source footprint library unavailable: '+lib)
    if not local.is_dir():continue
    source=p.FootprintLoad(str(local),item)
    check(bool(source),'Missing local source footprint: '+lib+':'+item)
    if not source:continue
    library_board.Add(source)
    source.SetLayerAndFlip(f.GetLayer());source.SetOrientationDegrees(f.GetOrientationDegrees());source.SetPosition(f.GetPosition())
    expected=collections.Counter(pad_sig(q) for q in source.Pads());actual=collections.Counter(pad_sig(q) for q in f.Pads())
    ok=expected==actual
    check(ok,'Local library/native pad geometry mismatch: '+f.GetReference())
    source_matches.append({'reference':f.GetReference(),'footprint':lib+':'+item,'source':str(local/(item+'.kicad_mod')),'pads_match':ok,'missing':list((expected-actual).elements()),'extra':list((actual-expected).elements())})
facts['source_footprints']=source_matches

layers=[p.In1_Cu,p.In3_Cu,p.In4_Cu]
refmap={p.F_Cu:p.In1_Cu,p.In2_Cu:p.In3_Cu,p.B_Cu:p.In4_Cu}
def planes(b):
    out={l:p.SHAPE_POLY_SET() for l in layers}
    for z in b.Zones():
        if z.GetNetname()!='GND' or z.GetIsRuleArea():continue
        for l in layers:
            if z.IsOnLayer(l) and z.HasFilledPolysForLayer(l):out[l].BooleanAdd(z.GetFilledPolysList(l))
    return out
pa,pb=planes(old),planes(new)
raw_reference_planes={l:p.SHAPE_POLY_SET(poly) for l,poly in pb.items()}
plane_delta=[]
for l in layers:
    loss=p.SHAPE_POLY_SET(pa[l]);loss.BooleanSubtract(pb[l])
    gain=p.SHAPE_POLY_SET(pb[l]);gain.BooleanSubtract(pa[l])
    plane_delta.append({'layer':new.GetLayerName(l),'loss_mm2':loss.Area()/1e12,'gain_mm2':gain.Area()/1e12})
facts['reference_plane_delta']=plane_delta
if cleanup:
    proof_source=p.LoadBoard(cleanup['source']);proof_planes=planes(proof_source);baseline_binding=[]
    for l in layers:
        loss=p.SHAPE_POLY_SET(pa[l]);loss.BooleanSubtract(proof_planes[l]);gain=p.SHAPE_POLY_SET(proof_planes[l]);gain.BooleanSubtract(pa[l]);baseline_binding.append({'layer':new.GetLayerName(l),'loss_mm2':loss.Area()/1e12,'gain_mm2':gain.Area()/1e12})
    check(all(q['loss_mm2']==q['gain_mm2']==0 for q in baseline_binding),'Retirement proof source planes differ from P5 baseline')
    facts['retirement_reference_baseline_binding']=baseline_binding
else:check(all(r['loss_mm2']==r['gain_mm2']==0 for r in plane_delta),'Reference-plane copper changed despite frozen vias/plane definitions')
for l in layers:
    check(pa[l].OutlineCount()==pb[l].OutlineCount()==1,'Ground reference plane is not one continuous filled polygon: '+new.GetLayerName(l))
facts['plane_outline_counts']={new.GetLayerName(l):pb[l].OutlineCount() for l in layers}
def subtract_drills(b,planes):
    holes=p.SHAPE_POLY_SET()
    for q in list(b.GetTracks())+[q for f in b.GetFootprints() for q in f.Pads()]:
        if not (isinstance(q,p.PCB_VIA) or isinstance(q,p.PAD) and q.HasHole()):continue
        pp=p.SHAPE_POLY_SET();q.GetEffectiveHoleShape().TransformToPolygon(pp,100,p.ERROR_OUTSIDE);holes.BooleanAdd(pp)
    for l in planes:planes[l].BooleanSubtract(holes)
subtract_drills(old,pa);subtract_drills(new,pb)
physical_delta=[]
for l in layers:
    loss=p.SHAPE_POLY_SET(pa[l]);loss.BooleanSubtract(pb[l]);gain=p.SHAPE_POLY_SET(pb[l]);gain.BooleanSubtract(pa[l])
    physical_delta.append({'layer':new.GetLayerName(l),'loss_mm2':loss.Area()/1e12,'gain_mm2':gain.Area()/1e12})
facts['drill_subtracted_reference_plane_delta']=physical_delta
# A merged plane hole may contain vias from several nets. Never attribute the
# whole merged hole to every resident net. Use an exact isolated native antipad
# template with matching physical geometry, clearance and netclass; otherwise
# use only a conservative inscribed nominal clearance envelope.
own_voids={};isolated_templates={};hole_inventory=[];via_objects=[v for v in new.GetTracks() if isinstance(v,p.PCB_VIA)];drilled_pads=[q for f in new.GetFootprints() for q in f.Pads() if q.HasHole()]
def via_signature(v,l):return (l,v.GetWidth(l),v.GetDrillValue(),v.GetOwnClearance(l),str(v.GetNetClassName()),v.GetNetname()=='GND')
for l,pp in pb.items():
    for oi in range(pp.OutlineCount()):
        for hi in range(pp.HoleCount(oi)):
            hole=p.SHAPE_POLY_SET(pp.CHole(oi,hi));residents=[v for v in via_objects if v.IsOnLayer(l) and hole.Contains(v.GetPosition())];pad_residents=[q for q in drilled_pads if hole.Contains(q.GetPosition())]
            hole_inventory.append((l,hole,residents,pad_residents))
            if len(residents)==1 and not pad_residents:
                v=residents[0];template=p.SHAPE_POLY_SET(hole);template.Move(-v.GetPosition());isolated_templates.setdefault(via_signature(v,l),template)
void_dispositions=[]
for l,hole,residents,pad_residents in hole_inventory:
    for v in residents:
        signature=via_signature(v,l)
        if len(residents)==1 and not pad_residents:
            own=p.SHAPE_POLY_SET(hole);method='exact isolated native hole'
        elif signature in isolated_templates:
            own=p.SHAPE_POLY_SET(isolated_templates[signature]);own.Move(v.GetPosition());method='translated exact isolated native hole with identical via geometry, clearance, netclass and reference layer'
        else:
            own=p.SHAPE_POLY_SET()
            if v.GetNetname()=='GND':v.GetEffectiveHoleShape().TransformToPolygon(own,100,p.ERROR_INSIDE)
            else:v.TransformShapeToPolygon(own,l,v.GetOwnClearance(l),100,p.ERROR_INSIDE)
            method='conservative inscribed nominal via clearance; no isolated native template exists'
        own_voids.setdefault((v.GetNetname(),l),p.SHAPE_POLY_SET()).BooleanAdd(own)
        if len(residents)>1 or pad_residents:void_dispositions.append({'net':v.GetNetname(),'via_uuid':uid(v),'reference_layer':new.GetLayerName(l),'merged_hole_via_count':len(residents),'merged_hole_drilled_pad_count':len(pad_residents),'method':method})
facts['same_net_antipad_boundaries']={'method':'Merged holes are never attributed wholesale to a resident net. Exact isolated antipad templates are geometry/clearance/netclass/reference-layer matched; conservative nominal inscribed envelopes are used if no exact isolated template exists.','merged_hole_dispositions':void_dispositions}
def polys(ts,thin=False):
    out=p.SHAPE_POLY_SET()
    for t in ts:
        q=t
        if thin:
            q=p.PCB_TRACK(new);q.SetStart(t.GetStart());q.SetEnd(t.GetEnd());q.SetWidth(100);q.SetLayer(t.GetLayer());q.SetNetCode(t.GetNetCode())
        poly=p.SHAPE_POLY_SET();q.TransformShapeToPolygon(poly,q.GetLayer(),0,100,p.ERROR_OUTSIDE);out.BooleanAdd(poly)
    return out
groups=collections.defaultdict(lambda:{'old':[],'new':[]})
changed_keys={(r['net'],r.get('layer')) for c in changes for r in [c['before'],c['after']] if r and r['type']!='PCB_VIA'}
for label,b in [('old',old),('new',new)]:
    for t in b.GetTracks():
        if isinstance(t,p.PCB_VIA) or t.GetLayer() not in refmap:continue
        if critical(t.GetNetname()) or (t.GetNetname(),t.GetLayerName()) in changed_keys:
            groups[(t.GetNetname(),t.GetLayer())][label].append(t)
named_reference={};named_reference_facts=[]
via_by_uuid={uid(v):v for v in new.GetTracks() if isinstance(v,p.PCB_VIA)}
for spec in exceptions.get('named_antipad_reference_exceptions',[]):
    net=spec['net'];lname=spec['layer'];l=new.GetLayerID(lname)
    check(net.rsplit('/',1)[-1].startswith('HSE_') and l in refmap,'Named antipad exception is outside reviewed HSE scope')
    if not (net.rsplit('/',1)[-1].startswith('HSE_') and l in refmap):continue
    target=via_by_uuid[spec['via_uuid']];sample=via_by_uuid[spec['isolated_reference_via_uuid']];r=refmap[l]
    identical=target.GetNetname()==net and target.GetWidth(r)==sample.GetWidth(r) and target.GetOwnClearance(r)==sample.GetOwnClearance(r) and target.GetNetClassName()==sample.GetNetClassName()
    check(identical,'Named reference via differs from isolated sample geometry/clearance/netclass')
    if not identical:continue
    pp=raw_reference_planes[r];found=[]
    for oi in range(pp.OutlineCount()):
        for hi in range(pp.HoleCount(oi)):
            hp=p.SHAPE_POLY_SET(pp.CHole(oi,hi))
            if not hp.Contains(sample.GetPosition()):continue
            residents=[v for v in via_by_uuid.values() if v.IsOnLayer(r) and hp.Contains(v.GetPosition())]
            check(len(residents)==1 and uid(residents[0])==uid(sample),'Native reference antipad sample is merged with another via')
            if len(residents)!=1 or uid(residents[0])!=uid(sample):continue
            hp.Move(target.GetPosition()-sample.GetPosition());found.append(hp)
    check(len(found)==1,'Expected exactly one isolated native antipad contour')
    if len(found)==1:
        named_reference[(net,l)]=found[0]
        named_reference_facts.append({**spec,'reference_layer':new.GetLayerName(r),'matched_via_width_mm':p.ToMM(target.GetWidth(r)),'matched_clearance_mm':p.ToMM(target.GetOwnClearance(r)),'matched_netclass':str(target.GetNetClassName()),'isolated_antipad_area_mm2':found[0].Area()/1e12,'method':'Translate exact isolated native filled-plane antipad of identical via diameter, clearance and netclass on same reference plane; do not subtract merged multi-via hole'})
facts['named_antipad_reference_exceptions']=named_reference_facts
dc_rail={}
for spec in exceptions.get('dc_rail_outer_edge_exceptions',[]):
    check(spec['net']=='3V3_CORE' and spec['layer']=='B.Cu' and spec['start_mm']==[37.5,26.2] and spec['end_mm']==[37.5,26.7] and spec['width_mm']==.45,'DC-edge exception exceeds exact owner-approved operation')
    ts=[t for t in new.GetTracks() if not isinstance(t,p.PCB_VIA) and t.GetNetname()=='3V3_CORE' and t.GetLayer()==p.B_Cu and mmxy(t.GetStart())==[37.5,26.2] and mmxy(t.GetEnd())==[37.5,26.7] and t.GetWidth()==450000]
    check(len(ts)==1,'Expected exact single approved .450mm east rail segment')
    check(all(u not in bt for u in ['0197ba6a-c28c-456a-ac5e-5442c744f27a','4c9bbe30-688c-47d9-b116-6bdc9e369105']),'Approved east rail source primitives were not replaced exactly')
    if len(ts)==1:dc_rail[('3V3_CORE',p.B_Cu)]=ts[0]
coverage=[]
for (net,l),g in groups.items():
    r=refmap[l];before=polys(g['old']);before.BooleanSubtract(pa[r]);after=polys(g['new']);after.BooleanSubtract(pb[r]);added=p.SHAPE_POLY_SET(after);added.BooleanSubtract(before)
    before_c=polys(g['old'],True);before_c.BooleanSubtract(pa[r]);after_c=polys(g['new'],True);after_c.BooleanSubtract(pb[r]);added_c=p.SHAPE_POLY_SET(after_c);added_c.BooleanSubtract(before_c)
    own=p.SHAPE_POLY_SET(own_voids.get((net,r),p.SHAPE_POLY_SET()));own.Inflate(2,p.CORNER_STRATEGY_ROUND_ALL_CORNERS,1)
    foreign=p.SHAPE_POLY_SET(added);foreign.BooleanSubtract(own);foreign_c=p.SHAPE_POLY_SET(added_c);foreign_c.BooleanSubtract(own)
    old_gap_rounding=p.SHAPE_POLY_SET(before);old_gap_rounding.Inflate(2,p.CORNER_STRATEGY_ROUND_ALL_CORNERS,1)
    foreign_above_rounding=p.SHAPE_POLY_SET(after);foreign_above_rounding.BooleanSubtract(old_gap_rounding);foreign_above_rounding.BooleanSubtract(own)
    old_center_rounding=p.SHAPE_POLY_SET(before_c);old_center_rounding.Inflate(2,p.CORNER_STRATEGY_ROUND_ALL_CORNERS,1)
    foreign_center_above_rounding=p.SHAPE_POLY_SET(after_c);foreign_center_above_rounding.BooleanSubtract(old_center_rounding);foreign_center_above_rounding.BooleanSubtract(own)
    foreign_center_polys=[{'outer_nm':[xy(foreign_c.COutline(i).CPoint(j)) for j in range(foreign_c.COutline(i).PointCount())]} for i in range(foreign_c.OutlineCount())]
    foreign_polys=[{'outer_nm':[xy(foreign.COutline(i).CPoint(j)) for j in range(foreign.COutline(i).PointCount())]} for i in range(foreign.OutlineCount())]
    row={'net':net,'layer':new.GetLayerName(l),'reference':new.GetLayerName(r),'baseline_uncovered_mm2':before.Area()/1e12,'candidate_uncovered_mm2':after.Area()/1e12,'new_uncovered_edge_mm2':added.Area()/1e12,'new_uncovered_centerline_tube_mm2':added_c.Area()/1e12,'new_foreign_edge_mm2':foreign.Area()/1e12,'new_foreign_centerline_tube_mm2':foreign_c.Area()/1e12,'new_foreign_edge_above_2nm_boolean_rounding_mm2':foreign_above_rounding.Area()/1e12,'foreign_polygons':foreign_polys,'foreign_centerline_polygons':foreign_center_polys,'new_foreign_centerline_above_2nm_boolean_rounding_mm2':foreign_center_above_rounding.Area()/1e12,'critical':critical(net)}
    qualified_foreign=p.SHAPE_POLY_SET(foreign_above_rounding)
    if (net,l) in dc_rail:
        dc=dc_rail[(net,l)];allowed=polys([dc]);allowed.BooleanSubtract(pb[r]);allowed.BooleanSubtract(before)
        outer=p.SHAPE_POLY_SET()
        for oi in range(raw_reference_planes[r].OutlineCount()):outer.BooleanAdd(p.SHAPE_POLY_SET(raw_reference_planes[r].COutline(oi)))
        inside=p.SHAPE_POLY_SET(allowed);inside.BooleanIntersection(outer)
        center_loss=polys([dc],True);center_loss.BooleanSubtract(pb[r])
        rectangle=p.SHAPE_POLY_SET();rectangle.NewOutline()
        for x,y in [(37050000,26000000),(37649000,26000000),(37649000,26900000),(37050000,26900000)]:rectangle.Append(x,y)
        rectangle.BooleanSubtract(pb[r]);bounds=allowed.BBox();bbox=[bounds.GetLeft()/1e6,bounds.GetTop()/1e6,bounds.GetRight()/1e6,bounds.GetBottom()/1e6]
        valid=inside.Area()==0 and center_loss.Area()==0 and rectangle.Area()==0 and allowed.Area()/1e12<=.005391978843+1e-12 and bbox[0]>=37.649998 and bbox[2]<=37.725002 and bbox[1]>=25.974998 and bbox[3]<=26.925002
        check(valid,'Declared DC edge allowance lacks exact bounded support/outer-edge proof')
        row['declared_DC_outer_edge_exception']={'added_unsupported_mm2':allowed.Area()/1e12,'bbox_mm':bbox,'inside_reference_outer_contour_mm2':inside.Area()/1e12,'new_centerline_exposure_mm2':center_loss.Area()/1e12,'missing_inward_ground_rectangle_mm2':rectangle.Area()/1e12,'supported_width_mm':.375,'outward_unreferenced_width_mm':.075,'scope':'Exact regulated DC rail only; outer edge strip, not a foreign hole or slot'}
        if valid:allowed.Inflate(2,p.CORNER_STRATEGY_ROUND_ALL_CORNERS,1);qualified_foreign.BooleanSubtract(allowed)
    row['new_undeclared_foreign_edge_mm2']=qualified_foreign.Area()/1e12
    row['new_undeclared_foreign_centerline_mm2']=foreign_center_above_rounding.Area()/1e12
    coverage.append(row)
    if critical(net):
        if (net,l) in named_reference:
            named_edge=p.SHAPE_POLY_SET(added);named_edge.BooleanSubtract(named_reference[(net,l)]);named_center=p.SHAPE_POLY_SET(added_c);named_center.BooleanSubtract(named_reference[(net,l)])
            row['named_antipad_exception_residual_edge_mm2']=named_edge.Area()/1e12;row['named_antipad_exception_residual_centerline_mm2']=named_center.Area()/1e12
            check(named_edge.Area()<1 and named_center.Area()<1,'Critical reference exposure outside exact named isolated antipad: '+net+' '+new.GetLayerName(l))
        else:check(added.Area()<1 and added_c.Area()<1,'New critical reference loss: '+net+' '+new.GetLayerName(l))
    else:check(qualified_foreign.Area()<1 and foreign_center_above_rounding.Area()<1,'New ordinary reference loss outside same-net via antipad and 2nm polygon rounding: '+net+' '+new.GetLayerName(l))
facts['reference_coverage']=coverage

facts['reference_gap_classification']={
    'method':'Raw filled-plane minus physical drills; compare candidate uncovered copper to baseline uncovered copper. True newly uncovered foreign copper means residual outside the baseline copper-edge or centerline gap expanded by exactly 2nm and individually bounded same-net via antipads. Area alone never waives a gap.',
    'declared_DC_outer_edge_exception_net_layers':[{'net':r['net'],'layer':r['layer'],**r['declared_DC_outer_edge_exception']} for r in coverage if 'declared_DC_outer_edge_exception' in r],
    'raw_new_gap_net_layers':len([r for r in coverage if r['new_uncovered_edge_mm2']>0]),
    'true_new_foreign_gap_net_layers':len([r for r in coverage if r['new_undeclared_foreign_edge_mm2']>=1e-12 or r['new_undeclared_foreign_centerline_mm2']>=1e-12]),
    'rounding_only_net_layers':[{'net':r['net'],'layer':r['layer'],'raw_new_foreign_edge_mm2':r['new_foreign_edge_mm2'],'raw_new_foreign_centerline_mm2':r['new_foreign_centerline_tube_mm2'],'above_2nm_envelope_mm2':r['new_foreign_edge_above_2nm_boolean_rounding_mm2']} for r in coverage if (r['new_foreign_edge_mm2']>0 or r['new_foreign_centerline_tube_mm2']>0) and r['new_foreign_edge_above_2nm_boolean_rounding_mm2']<1e-12 and r['new_foreign_centerline_above_2nm_boolean_rounding_mm2']<1e-12],
}
facts['retained_special_footprints']={ref:{'exact_full_semantic_match':af['"'+uid(next(f for f in old.GetFootprints() if f.GetReference()==ref))+'"']==bf['"'+uid(next(f for f in new.GetFootprints() if f.GetReference()==ref))+'"'],'pad_count':len(list(next(f for f in new.GetFootprints() if f.GetReference()==ref).Pads()))} for ref in ['J2','D4','U2','U11']}


new_j2=next(f for f in new.GetFootprints() if f.GetReference()=='J2')
slots=[]
objects=list(new.GetTracks())+[q for f in new.GetFootprints() for q in f.Pads()]
for q in new_j2.Pads():
    if uid(q) not in target_pads:continue
    hole=q.GetEffectiveHoleShape();s=hole.GetSeg()
    copper_near=[];hole_near=[]
    for v in objects:
        if uid(q)==uid(v):continue
        if v.GetNetname()!=q.GetNetname():
            for l in [p.F_Cu,p.In1_Cu,p.In2_Cu,p.In3_Cu,p.In4_Cu,p.B_Cu]:
                if not v.IsOnLayer(l):continue
                gap=q.GetEffectiveShape(l).GetClearance(v.GetEffectiveShape(l))
                if gap<p.FromMM(.6):copper_near.append({'uuid':uid(v),'net':v.GetNetname(),'layer':new.GetLayerName(l),'gap_mm':p.ToMM(gap)})
        if isinstance(v,p.PCB_VIA) or isinstance(v,p.PAD) and v.HasHole():
            gap=hole.GetClearance(v.GetEffectiveHoleShape())
            if gap<p.FromMM(1):hole_near.append({'uuid':uid(v),'net':v.GetNetname(),'gap_mm':p.ToMM(gap)})
    copper_near.sort(key=lambda r:r['gap_mm']);hole_near.sort(key=lambda r:r['gap_mm'])
    row={'uuid':uid(q),'center_native_mm':mmxy(q.GetPosition()),'size_local_mm':mmxy(q.GetSize()),'drill_local_mm':mmxy(q.GetDrillSize()),'hole_native_endpoints_mm':[mmxy(s.A),mmxy(s.B)],'hole_export_endpoints_mm':[[p.ToMM(v.x),38-p.ToMM(v.y)] for v in [s.A,s.B]],'annulus_mm':[(q.GetSize().x-q.GetDrillSize().x)/2e6,(q.GetSize().y-q.GetDrillSize().y)/2e6],'foreign_copper_near':copper_near,'holes_near':hole_near}
    check(all(x>=.15-1e-6 for x in [r['gap_mm'] for r in copper_near]),'Slot foreign-copper gap below 0.15mm')
    check(all(x>=.25-1e-6 for x in [r['gap_mm'] for r in hole_near]),'Slot hole gap below 0.25mm')
    slots.append(row)
facts['front_slots']=slots
check(a.selfcheck or a.sha256!=expected_old,'Unchanged P5 baseline cannot be certified as a P6 cleanup')
check(sha(A/'controller.kicad_pcb')==expected_old and sha(B/'controller.kicad_pcb')==a.sha256,'Native source changed during check')
result={'status':('BASELINE HARNESS SELF-CHECK PASS; NOT P6 ACCEPTANCE' if a.selfcheck else 'PASS P6 READ-ONLY GEOMETRY/REFERENCE') if not errors else 'NOT PASSED','baseline_sha256':expected_old,'candidate_sha256':a.sha256,'errors':errors,'facts':facts,'limits':'Read-only native geometry/reference consistency. Does not establish solder process, supplier acceptance or physical performance. Changed ordinary-net reference loss is reported for contextual review.'}
(O/'revision-geometry.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'status':result['status'],'errors':errors,'pad_changes':len(pad_changes),'copper_changes':len(changes),'source_footprints':len(source_matches),'plane_delta':plane_delta,'reference_losses':[r for r in coverage if r['new_uncovered_edge_mm2']>1e-12],'report':str(O/'revision-geometry.json')},indent=2))
raise SystemExit(bool(errors))
