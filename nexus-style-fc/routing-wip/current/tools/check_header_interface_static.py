#!/usr/bin/env python3
"""Source-bound text/analytic verification; no KiCad, native DRC or strength certification."""
from pathlib import Path
from math import sqrt,pi,atan2,sin,cos,hypot,atan
import hashlib,json,sys
if not __debug__:
    raise SystemExit("Refusing optimized Python: verification requires active assertion guards.")
import sexpr as s
import header_interface_geometry as g
import apply_header_interface as tx
import make_footprints as mf
ROOT=Path(__file__).resolve().parents[1]; HW=ROOT/'hardware'
OUT=ROOT/'docs/header-interface-candidate';OUT.mkdir(parents=True,exist_ok=True)

def one(n,k):return s.find(n,k)[0]
def val(n,k):return one(n,k)[1:]
def xy(n,k):return tuple(map(float,val(n,k)[:2]))
def st(n,k):return s.text(val(n,k)[-1])
def fp(b,r):return next(n for n in s.find(b,'footprint') if tx.ref(n)==r)
def padbox(f,p):
    x,y=xy(f,'at');px,py=xy(p,'at');w,h=xy(p,'size');return (x+px-w/2,y+py-h/2,x+px+w/2,y+py+h/2)
def rdist(a,b):return hypot(max(a[0]-b[2],b[0]-a[2],0),max(a[1]-b[3],b[1]-a[3],0))
def usable(L,W,t,r):
    if t>W:return None
    q=max(0,t/2-W/2+r);return L-2*r+2*sqrt(r*r-q*q)
def chain(shapes,closed=False):
    for a,b in zip(shapes,shapes[1:]):assert all(abs(x-y)<1e-6 for x,y in zip(a[-1],b[1]))
    if closed:assert shapes[-1][-1]==shapes[0][1]
def net(n,b):
    v=val(n,'net');z=s.text(v[-1])
    if z.isdigit():
        return next(s.text(v[2]) for v in s.find(b,'net') if v[1]==z)
    return z

main=s.parse((HW/'nexus-style-fc.kicad_pcb').read_text());child=s.parse((HW/'header-board/nexus-header-board.kicad_pcb').read_text())
for c in g.SLOT_CENTERS:chain(g.rounded_slot(*c),True)
chain(g.tab_outline())
# Verify ACTUAL native contours, not merely the expected generator definitions.
j=fp(main,'J1');lib=s.parse((HW/'library/NexusFC.pretty/HeaderBoard_Joint.kicad_mod').read_text())
def shape_sig(n):
    keys=('start','mid','end') if n[0].endswith('_arc') else ('start','end')
    return n[0].split('_')[-1],tuple(tuple(round(v,6) for v in xy(n,k)) for k in keys),st(n,'layer')
def edges(n,prefix):
    return [x for x in n if isinstance(x,list) and x[0] in (prefix+'_line',prefix+'_arc') and st(x,'layer')=='Edge.Cuts']
def component_count(es):
    adj={}
    for n in es:
        a,b=(tuple(round(v,6) for v in xy(n,k)) for k in ('start','end'))
        assert a!=b
        adj.setdefault(a,[]).append(b);adj.setdefault(b,[]).append(a)
    assert adj and all(len(v)==2 for v in adj.values()), 'Native open/branched outline'
    unseen=set(adj);count=0
    while unseen:
        stack=[next(iter(unseen))];count+=1
        while stack:
            q=stack.pop()
            if q not in unseen:continue
            unseen.remove(q);stack.extend(adj[q])
    return count
expected_main=[s.parse(g.kicad_shape(sh)) for c in g.SLOT_CENTERS for sh in g.rounded_slot(*c)]
assert sorted(map(shape_sig,edges(j,'fp')))==sorted(map(shape_sig,expected_main))
assert sorted(map(shape_sig,edges(j,'fp')))==sorted(map(shape_sig,edges(lib,'fp')))
assert len(edges(j,'fp'))==16 and component_count(edges(j,'fp'))==2
native_child=edges(child,'gr')
assert len(native_child)==18 and component_count(native_child)==1
expected_bottom=[s.parse(g.kicad_shape(sh,'gr',(100,108.4),str(tx.uuid.uuid5(tx.NS,f'child-bottom-{i}')))) for i,sh in enumerate(g.tab_outline())]
for n in expected_bottom:
    actual=next(x for x in native_child if tx.uid(x)==tx.uid(n))
    assert shape_sig(actual)==shape_sig(n)
assert xy(fp(child,'J1'),'at')==(111.2,103.56)
# All generated mating pad coordinates/sizes and slot contours match native, to 1 nm grid.
def padsig(p):return s.text(p[1]),tuple(round(v,6) for v in xy(p,'at')),tuple(round(v,6) for v in xy(p,'size')),tuple(s.text(x) for x in val(p,'layers'))
assert sorted(map(padsig,s.find(j,'pad')))==sorted(map(padsig,s.find(lib,'pad')))
assert not any(s.text(p[2])=='np_thru_hole' for p in s.find(j,'pad'))
for r in ('P1','P2','P3','P4','P5','P6','P7','T1','T2','K1','K2'):
    f=fp(child,r);name=s.text(f[1]).split(':')[1];lf=s.parse((HW/'library/NexusFC.pretty'/f'{name}.kicad_mod').read_text());assert padsig(one(f,'pad'))==padsig(one(lf,'pad'))
    if not r.startswith('K'):assert abs(xy(f,'at')[0]-100-mf.pad_x_child(net(one(f,'pad'),child)))<1e-6
mating=[]
for p in s.find(j,'pad'):
    b=padbox(j,p);box=(b[0]-100,b[1]-100,b[2]-100,b[3]-100)
    gap=min(rdist(box,(cx-g.SLOT_LENGTH/2+g.SLOT_RADIUS,cy-g.SLOT_WIDTH/2+g.SLOT_RADIUS,cx+g.SLOT_LENGTH/2-g.SLOT_RADIUS,cy+g.SLOT_WIDTH/2-g.SLOT_RADIUS))-g.SLOT_RADIUS for cx,cy in g.SLOT_CENTERS)
    assert gap>=.30-1e-6  # Existing 0.300 nominal copper-edge floor is retained; no rule relaxation.
    mating.append({'board':'main','pad_uuid':tx.uid(p),'number':s.text(p[1]),'net':net(p,main),'box':box,'minimum_slot_gap':gap,'minimum_external_edge_gap':min(box[0],22.4-box[2],box[1])})
for f in s.find(child,'footprint'):
    if tx.ref(f)=='J1':continue
    p=one(f,'pad');b=padbox(f,p);box=(b[0]-100,b[1]-108.4,b[2]-100,b[3]-108.4);a,c=g.TABS[0 if box[0]<11.2 else 1]
    gaps=[box[0]-a,c-box[2],2.6-box[3]]
    relief=min(rdist(box,(x,0,x,0))-.5 for x in (.9,10.3,12.1,21.5))
    assert min(gaps)>=.254-1e-6 and relief>=.254-1e-6
    m=next(m for m in mating if m['net']==net(p,child) and (m['box'][1]<1.1)==tx.ref(f).startswith('K'))
    mirrored=(22.4-box[2],22.4-box[0]);overlap=min(mirrored[1],m['box'][2])-max(mirrored[0],m['box'][0]);assert overlap>=box[2]-box[0]-1e-6
    mating.append({'board':'child','ref':tx.ref(f),'pad_uuid':tx.uid(p),'net':net(p,child),'box':box,'minimum_tab_edge_gap':min(gaps),'minimum_root_relief_gap':relief,'nominal_matching_main_x_overlap':overlap})
# Bounded rigid centred/parallel cross sections. These do not establish real assembly fit.
cases=[]
for label,L,W,t,T,r,pitch in [('nominal',g.SLOT_LENGTH,g.SLOT_WIDTH,1.6,8.4,g.SLOT_RADIUS,0),('adverse_size_R0.5',g.SLOT_LENGTH-.2,g.SLOT_WIDTH-.2,1.76,8.6,.5,0),('adverse_size_pitch0.4_R0.5',g.SLOT_LENGTH-.2,g.SLOT_WIDTH-.2,1.76,8.6,.5,.4),('adverse_size_pitch0.4_R0.55',g.SLOT_LENGTH-.2,g.SLOT_WIDTH-.2,1.76,8.6,.55,.4),('adverse_size_pitch0.4_R0.6',g.SLOT_LENGTH-.2,g.SLOT_WIDTH-.2,1.76,8.6,.6,.4),('loose_size',g.SLOT_LENGTH+.2,g.SLOT_WIDTH+.2,1.44,8.2,.5,0)]:
    eff=usable(L,W,t,r);budget=eff-T-pitch
    cases.append({'case':label,'slot_length':L,'slot_width':W,'child_thickness':t,'entire_tab_envelope_width':T,'slot_radius':r,'pair_pitch_mismatch':pitch,'usable_width':eff,'remaining_total_x_budget':budget,'total_y_budget':W-t,'rigid_centered_size_screen':'no interference' if budget>=0 and W>=t else 'interference','unallocated_common_x_translation_half_budget':budget/2})
# Coupled rounded-corner study; independent X/Y budgets cannot be spent together.
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
# Worst screen tilt about longitudinal axis, ignores all simultaneous radius/pitch/copper registration errors.
lo,hi=0.,pi/4
for _ in range(60):
    a=(lo+hi)/2
    if 1.76/cos(a)+1.76*sin(a)/cos(a)<=g.SLOT_WIDTH-.2:lo=a
    else:hi=a
tilt={'adverse_size_only_max_transverse_tilt_degrees':lo*180/pi,'equation':'t/cos(theta) + main_thickness*tan(abs(theta)) <= slot_width','assumptions':f't=1.76, main thickness=1.76, slot width={g.SLOT_WIDTH-.2}; straight-sided section only, no bow/burr/finish/radius/position allowances. Not an assembly angle specification.'}
# Complete-net copper inventory preserves routing owner's visibility; no trimming or routing is performed.
ports={}
for label,b in (('main',main),('child',child)):
    nets={m['net'] for m in mating if m['board']==label};records=[]
    if label=='main':nets.add('DSM_DATA')  # independent review found new cutout proximity conflicts
    for n in s.find(b,'segment')+s.find(b,'via'):
        nn=net(n,b)
        if nn in nets:
            rec={'kind':n[0],'uuid':tx.uid(n),'net':nn,'native_record':s.dump(n)};records.append(rec)
    ports[label]={'scope':'Complete existing segment/via inventory for every mating net plus nearby DSM_DATA on main; unchanged by transaction. Zone caches invalidated; new local routes and refill needed. Not a preapproved deletion list.','records':records,'counts':{n:{k:sum(v['net']==n and v['kind']==k for v in records) for k in ('segment','via')} for n in sorted(nets)}}
(OUT/'routing-preservation-inventory.json').write_text(json.dumps(ports,indent=2)+'\n')
res={'status':'UNFINISHED; static analytic/text checks only; native loading, DRC, ERC/parity, refill, 3D and physical qualification not performed','native_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [HW/'nexus-style-fc.kicad_pcb',HW/'header-board/nexus-header-board.kicad_pcb',HW/'nexus-style-fc.kicad_sch',HW/'header-board/nexus-header-board.kicad_sch']},'tests':{'closed_main_cutout_contours':True,'continuous_child_bottom_contour':True,'native_and_generated_mating_pad_geometry_agree':True,'full_1p2_signal_1p6_power_widths_retained':True,'all_22_mating_pads_nominal_edge_limits':True,'main_signal_pinmap_and_all_connected_pad_ids_unchanged':'asserted by transaction','main_schematic_expected_sha256':'7a133c241ba24a688d2d2490ae423ff74d26f57cf6578f871cc757093584de42'},'mating_pads':mating,'tolerance_screen':cases,'coupled_corner_screen':coupled,'transverse_tilt_screen':tilt,'geometric_strength_screen':{'material':'unspecified laminate; no material rating assumed','single_tab_root_gross_section_mm2':8.4*1.6,'single_tab_out_of_plane_nominal_section_modulus_mm3':8.4*1.6**2/6,'sum_nominal_flat_seat_lengths_mm':1.6,'sum_nominal_seat_area_mm2':1.6*1.6,'main_outer_ligament_nominal_mm':5.6-g.SLOT_LENGTH/2,'main_central_web_nominal_mm':11.2-g.SLOT_LENGTH,'main_front_ligament_nominal_mm':2.4-g.SLOT_WIDTH/2,'main_outer_ligament_plus0p2_length_mm':5.6-(g.SLOT_LENGTH+.2)/2,'main_central_web_plus0p2_length_mm':11.2-(g.SLOT_LENGTH+.2),'main_front_ligament_plus0p2_width_mm':2.4-(g.SLOT_WIDTH+.2)/2,'single_slot_removed_area_mm2':g.SLOT_LENGTH*g.SLOT_WIDTH-(4-pi)*g.SLOT_RADIUS**2,'limitations':'Gross sections only; not FEA or allowable loads. Connector loads, lever arm, restraint/load sharing, notch concentration, laminate stack/fibre direction, solder alloy/fillet/current, creep, fatigue, shock and thermal cycles need definition/qualification.'}}
assert res['native_sha256']['hardware/nexus-style-fc.kicad_sch']==res['tests']['main_schematic_expected_sha256']
(OUT/'static-validation.json').write_text(json.dumps(res,indent=2)+'\n')
print(json.dumps({'checks':res['tests'],'cases':cases,'tilt':tilt},indent=2))
