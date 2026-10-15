"""Prepare an in-memory proposal only; never write source boards or tools."""
from pathlib import Path
import copy, hashlib, json, sys
O=Path(__file__).parent
P=O.parent/'mechanical-integration/main-terminal-cleanup-07'
sys.path.insert(0,str(P/'tools'));import sexpr as s
spec=json.loads((O/'slot101-source-guarded-spec.json').read_text())
spec['source_project']=str(P)
for f in spec['source_sha256']:
    h=hashlib.sha256((P/f).read_bytes()).hexdigest()
    if f=='hardware/nexus-style-fc.kicad_pcb':assert h=='1d40a35cf373bef251f8032001766016f09500b007f22ff27ccb6578b0c4e263'
    else:assert h==spec['source_sha256'][f],(f,h)
    spec['source_sha256'][f]=h
b=s.parse((P/'hardware/nexus-style-fc.kicad_pcb').read_text())
def first(n,k):return s.find(n,k)[0]
def ref(n):return next(s.text(p[2]) for p in s.find(n,'property') if s.text(p[1])=='Reference')
def uid(n):return s.text(first(n,'uuid')[1])
j=next(f for f in s.find(b,'footprint') if ref(f)=='J1')
for change in spec['edge_changes']:
    old=next(n for n in j if isinstance(n,list) and s.find(n,'uuid') and uid(n)==change['uuid'])
    assert s.dump(old)==change['old_native_record']
    new=s.parse(change['new_native_record'])
    for key in ('start','mid','end'):
        for xy in s.find(new,key):
            y=float(xy[2]);xy[2]=f'{y+(-.05 if y<2.4 else .05):.6f}'
    change['new_native_record']=s.dump(new)
changes=[]
for z in spec.pop('keepouts_preserved_exactly'):
    old=next(n for n in s.find(b,'zone') if uid(n)==z['uuid'])
    assert s.dump(old)==z['record_unchanged']
    new=copy.deepcopy(old)
    for xy in s.find(first(first(new,'polygon'),'pts'),'xy'):
        y=float(xy[2]);assert y in (101.05,103.75);xy[2]='101' if y==101.05 else '103.8'
    changes.append({'uuid':z['uuid'],'old_native_record':s.dump(old),'old_record_sha256':z['native_sha256'],'new_native_record':s.dump(new),'preserved':'All X coordinates, layers, permissions and other source fields; only the four polygon vertex Y coordinates change.'})
spec['keepout_changes']=changes
assert sorted(spec['all_11_main_pad_records_unchanged'])==sorted(s.dump(p) for p in s.find(j,'pad'))
spec['new_local_slot_bounds']=[[.55,1.3,10.65,3.5],[11.75,1.3,21.85,3.5]]
spec['new_native_slot_bounds']=[[100.55,101.3,110.65,103.5],[111.75,101.3,121.85,103.5]]
spec['geometry_invariants'].pop('slot_width')
spec['new_slot_dimensions']={'length':10.1,'width':2.2}
spec['status']='Parent-approved integrated 10.10x2.20 candidate proposal, subject to coordinated signal repair and complete native checks. This specification changes no source file. Earlier smaller candidates remain study history only.'
for f,items in spec['source_text_replacements'].items():
    for item in items:item[1]=item[1].replace('10.1, 2.1','10.1, 2.2').replace('10.1 x 2.1','10.1 x 2.2')
spec['source_text_replacements']['tools/header_interface_geometry.py'].append(['# Preserve original stricter lateral keepout; expand vertical extent for new slots.','# Keep original X bounds using a 0.45 offset for 10.10 length; expand Y to retain 0.30 beyond the 2.20 slot.'])
checker=(P/'tools/check_header_interface_static.py').read_text();replacements=[]
def change(old,new):
    assert checker.count(old)==1,(old[:100],checker.count(old));replacements.append([old,new])
change('import hashlib,json,sys','import hashlib,json,sys\nif not __debug__:\n    raise SystemExit("Refusing optimized Python: verification requires active assertion guards.")')
change("    gap=min(rdist(box,(cx-4.5,cy-.55,cx+4.5,cy+.55))-.5 for cx,cy in g.SLOT_CENTERS)\n    assert gap>=.35-1e-6", "    gap=min(rdist(box,(cx-g.SLOT_LENGTH/2+g.SLOT_RADIUS,cy-g.SLOT_WIDTH/2+g.SLOT_RADIUS,cx+g.SLOT_LENGTH/2-g.SLOT_RADIUS,cy+g.SLOT_WIDTH/2-g.SLOT_RADIUS))-g.SLOT_RADIUS for cx,cy in g.SLOT_CENTERS)\n    assert gap>=.30-1e-6  # Existing 0.300 nominal copper-edge floor is retained; no rule relaxation.")
oldcase=next(line for line in checker.splitlines() if line.startswith('for label,L,W,t,T,r,pitch in '))
newcase="for label,L,W,t,T,r,pitch in [('nominal',g.SLOT_LENGTH,g.SLOT_WIDTH,1.6,8.4,g.SLOT_RADIUS,0),('adverse_size_R0.5',g.SLOT_LENGTH-.2,g.SLOT_WIDTH-.2,1.76,8.6,.5,0),('adverse_size_pitch0.4_R0.5',g.SLOT_LENGTH-.2,g.SLOT_WIDTH-.2,1.76,8.6,.5,.4),('adverse_size_pitch0.4_R0.55',g.SLOT_LENGTH-.2,g.SLOT_WIDTH-.2,1.76,8.6,.55,.4),('adverse_size_pitch0.4_R0.6',g.SLOT_LENGTH-.2,g.SLOT_WIDTH-.2,1.76,8.6,.6,.4),('loose_size',g.SLOT_LENGTH+.2,g.SLOT_WIDTH+.2,1.44,8.2,.5,0)]:"
change(oldcase,newcase)
change('if 1.76/cos(a)+1.76*sin(a)/cos(a)<=1.9:lo=a','if 1.76/cos(a)+1.76*sin(a)/cos(a)<=g.SLOT_WIDTH-.2:lo=a')
change("'assumptions':'t=1.76, main thickness=1.76, slot width=1.9; straight-sided section only, no bow/burr/finish/radius/position allowances. Not an assembly angle specification.'", "'assumptions':f't=1.76, main thickness=1.76, slot width={g.SLOT_WIDTH-.2}; straight-sided section only, no bow/burr/finish/radius/position allowances. Not an assembly angle specification.'")
change("'main_schematic_expected_sha256':'49f9e0571424d0610e294bdcd6b120a42d04db284ecda9e660428fc587e62699'", "'main_schematic_expected_sha256':'7a133c241ba24a688d2d2490ae423ff74d26f57cf6578f871cc757093584de42'")
change("'main_outer_ligament_nominal_mm':.6,'main_central_web_nominal_mm':1.2,'main_front_ligament_nominal_mm':1.35,'single_slot_removed_area_mm2':10*2.1-(4-pi)*.5**2", "'main_outer_ligament_nominal_mm':5.6-g.SLOT_LENGTH/2,'main_central_web_nominal_mm':11.2-g.SLOT_LENGTH,'main_front_ligament_nominal_mm':2.4-g.SLOT_WIDTH/2,'main_outer_ligament_plus0p2_length_mm':5.6-(g.SLOT_LENGTH+.2)/2,'main_central_web_plus0p2_length_mm':11.2-(g.SLOT_LENGTH+.2),'main_front_ligament_plus0p2_width_mm':2.4-(g.SLOT_WIDTH+.2)/2,'single_slot_removed_area_mm2':g.SLOT_LENGTH*g.SLOT_WIDTH-(4-pi)*g.SLOT_RADIUS**2")
coupled='''# Coupled rounded-corner study; independent X/Y budgets cannot be spent together.
def coupled_corner(L,W,T,t,r,P,dx,dy):
    qx=max(0,T/2+P/2+abs(dx)-(L/2-r));qy=max(0,t/2+abs(dy)-(W/2-r))
    return r-hypot(qx,qy)
assert (g.SLOT_LENGTH,g.SLOT_WIDTH,g.SLOT_RADIUS)==(10.1,2.2,.5)
coupled={'finished_L':9.9,'finished_W':2.0,'tab_width':8.6,'child_thickness':1.76,'max_finished_radius':.6,'pair_pitch_mismatch':.4,'study_dx_half':.1,'study_dy_half':.05,'corner_radial_reserve':coupled_corner(9.9,2.0,8.6,1.76,.6,.4,.1,.05),'scope':'Conditional rigid perpendicular cross-section about actual feasible midpoint; size allowances require drawing acceptance and radius/pitch are illustrative bounds. No unallocated absolute copper/outline datum, bow/twist, finish, burr, thermal or seating errors. Not a physical fit guarantee or an all-free-play electrical registration check.'}
assert abs(coupled['corner_radial_reserve']-.013996587040655872)<1e-9
# Exact native keepout construction with all permissions preserved.
expected_keepouts={'c67f2612-ad61-4083-8c9a-72e3a887c688':[(100.1,101.0),(111.1,101.0),(111.1,103.8),(100.1,103.8)],'79e1149d-aeb4-4aaf-8cd7-cf3a7ca09f8a':[(111.3,101.0),(122.3,101.0),(122.3,103.8),(111.3,103.8)]}
for zid,pts in expected_keepouts.items():
    z=next(z for z in s.find(main,'zone') if tx.uid(z)==zid)
    assert [tuple(map(float,p[1:3])) for p in s.find(one(one(z,'polygon'),'pts'),'xy')]==pts
    assert {k:s.text(val(one(z,'keepout'),k)[0]) for k in ('tracks','vias','pads','copperpour','footprints')}=={'tracks':'not_allowed','vias':'not_allowed','pads':'allowed','copperpour':'allowed','footprints':'allowed'}
'''
change('# Worst screen tilt about longitudinal axis, ignores all simultaneous radius/pitch/copper registration errors.',coupled+'# Worst screen tilt about longitudinal axis, ignores all simultaneous radius/pitch/copper registration errors.')
change("'tolerance_screen':cases,'transverse_tilt_screen':tilt", "'tolerance_screen':cases,'coupled_corner_screen':coupled,'transverse_tilt_screen':tilt")
spec['source_text_replacements']['tools/check_header_interface_static.py']=replacements
spec['source_replacement_counts']={f:[{'old_text':a,'expected_count':(P/f).read_text().count(a)} for a,_ in pairs] for f,pairs in spec['source_text_replacements'].items()}
for f,pairs in spec['source_text_replacements'].items():
    proposed=(P/f).read_text()
    for a,c in pairs:assert a in proposed;proposed=proposed.replace(a,c)
    compile(proposed,str(P/f),'exec')  # Syntax only; do not execute proposed source.
spec['library_edit']='Match all 16 old Edge.Cuts shape coordinates against the bound library and apply exactly the corresponding proposed coordinates, retaining every non-edge field except its 10.0 x 2.1 description to 10.1 x 2.2. All pads, body/courtyard/model fields remain identical. Compare generated fp_joint output in memory; never run full board generators on routed sources.'
spec['native_description_edit']='J1 descr 10.0 x 2.1 becomes 10.1 x 2.2. Only its 16 Edge.Cuts records change otherwise; all pad/net/model/courtyard records are retained.'
spec['fill_rule']='Invalidate only cached filled_polygon/fill_segments, then native refill. Preserve source copper zones, layers/net/rule/permissions. Two keepout polygon Y ranges explicitly expand per specification. Coordinated DSM/RPM/SBUS repair is a separately guarded transaction; SW_5V stays fixed.'
spec['static_checker_warning']='The explicit replacements above bind the checker to 10.10x2.20 and the current unchanged 7a133c24 schematic. Do not delete/waive guards or report historical checker output as current. apply_header_interface.py remains an r54-to-redesign historical transaction; do not rerun it against stage07 or bypass its r54 anchors. Use the lane-owned guarded incremental transaction.'
spec['affected_DSM_donors']=[]
for xid in ('1820c4c2-7b40-522a-a5f4-bb1f05c3ea7b','23a76edb-07a7-56c4-ac2b-748fb6295bbe','527e82f5-aa9c-530c-848d-87b60ae4314f'):
    n=next(n for n in s.find(b,'segment') if uid(n)==xid)
    spec['affected_DSM_donors'].append({'uuid':xid,'native_record':s.dump(n),'old_slot_gap':.3365,'new_slot_gap':.2865,'required_nominal_rule_floor':.3,'repair_scope':'Coordinated local signal repair by native owner; not preapproval to delete connectivity.'})
spec['receipt_paths']=['bounded-width-alternative.json','full-radius-model-check.json','electrical-registration-window.json','main-terminal-cleanup-07-geometry-binding.json','README.md']
spec['fit_caveat']='10.10x2.20 supports the illustrative adverse +/-0.10 X and +/-0.05 Y window with only 0.013996587 radial corner reserve. Feasible pose and deliberate copper registration are distinct; no physical guarantee or strength/current rating.'
for f,h in spec['source_sha256'].items():assert hashlib.sha256((P/f).read_bytes()).hexdigest()==h
dest=O/'slot101x220-source-guarded-spec.json';dest.write_text(json.dumps(spec,indent=2)+'\n')
print(json.dumps({'path':str(dest),'sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'edge_count':len(spec['edge_changes']),'keepout_count':len(spec['keepout_changes']),'unchanged_pad_count':len(spec['all_11_main_pad_records_unchanged']),'source_main':spec['source_sha256']['hardware/nexus-style-fc.kicad_pcb']},indent=2))
