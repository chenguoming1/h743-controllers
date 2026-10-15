#!/usr/bin/env python3
"""Source-bound text/analytic verification; no KiCad, native DRC or strength certification."""
from pathlib import Path
from math import sqrt,pi,atan2,sin,cos,hypot,atan
import hashlib,json,sys
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
# All generated mating pad coordinates/sizes and slot contours match native, to 1 nm grid.
j=fp(main,'J1');lib=s.parse((HW/'library/NexusFC.pretty/HeaderBoard_Joint.kicad_mod').read_text())
def padsig(p):return s.text(p[1]),tuple(round(v,6) for v in xy(p,'at')),tuple(round(v,6) for v in xy(p,'size')),tuple(s.text(x) for x in val(p,'layers'))
assert sorted(map(padsig,s.find(j,'pad')))==sorted(map(padsig,s.find(lib,'pad')))
assert not any(s.text(p[2])=='np_thru_hole' for p in s.find(j,'pad'))
for r in ('P1','P2','P3','P4','P5','P6','P7','T1','T2','K1','K2'):
    f=fp(child,r);name=s.text(f[1]).split(':')[1];lf=s.parse((HW/'library/NexusFC.pretty'/f'{name}.kicad_mod').read_text());assert padsig(one(f,'pad'))==padsig(one(lf,'pad'))
    if not r.startswith('K'):assert abs(xy(f,'at')[0]-100-mf.pad_x_child(net(one(f,'pad'),child)))<1e-6
mating=[]
for p in s.find(j,'pad'):
    b=padbox(j,p);box=(b[0]-100,b[1]-100,b[2]-100,b[3]-100)
    gap=min(rdist(box,(cx-4.5,cy-.55,cx+4.5,cy+.55))-.5 for cx,cy in g.SLOT_CENTERS)
    assert gap>=.35-1e-6
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
for label,L,W,t,T,r,pitch in [('nominal',10,2.1,1.6,8.4,.5,0),('adverse_size_R0.5',9.8,1.9,1.76,8.6,.5,0),('adverse_size_pitch0.4_R0.5',9.8,1.9,1.76,8.6,.5,.4),('adverse_size_pitch0.4_R0.55',9.8,1.9,1.76,8.6,.55,.4),('adverse_size_pitch0.4_R0.6',9.8,1.9,1.76,8.6,.6,.4),('loose_size',10.2,2.3,1.44,8.2,.5,0)]:
    eff=usable(L,W,t,r);budget=eff-T-pitch
    cases.append({'case':label,'slot_length':L,'slot_width':W,'child_thickness':t,'entire_tab_envelope_width':T,'slot_radius':r,'pair_pitch_mismatch':pitch,'usable_width':eff,'remaining_total_x_budget':budget,'total_y_budget':W-t,'rigid_centered_size_screen':'no interference' if budget>=0 and W>=t else 'interference','unallocated_common_x_translation_half_budget':budget/2})
# Worst screen tilt about longitudinal axis, ignores all simultaneous radius/pitch/copper registration errors.
lo,hi=0.,pi/4
for _ in range(60):
    a=(lo+hi)/2
    if 1.76/cos(a)+1.76*sin(a)/cos(a)<=1.9:lo=a
    else:hi=a
tilt={'adverse_size_only_max_transverse_tilt_degrees':lo*180/pi,'equation':'t/cos(theta) + main_thickness*tan(abs(theta)) <= slot_width','assumptions':'t=1.76, main thickness=1.76, slot width=1.9; straight-sided section only, no bow/burr/finish/radius/position allowances. Not an assembly angle specification.'}
# Complete-net copper inventory preserves routing owner's visibility; no trimming or routing is performed.
ports={}
for label,b in (('main',main),('child',child)):
    nets={m['net'] for m in mating if m['board']==label};records=[]
    for n in s.find(b,'segment')+s.find(b,'via'):
        nn=net(n,b)
        if nn in nets:
            rec={'kind':n[0],'uuid':tx.uid(n),'net':nn,'native_record':s.dump(n)};records.append(rec)
    ports[label]={'scope':'Complete existing segment/via inventory for every mating net; unchanged by transaction. Zone caches invalidated; new local routes and refill needed. Not a preapproved deletion list.','records':records,'counts':{n:{k:sum(v['net']==n and v['kind']==k for v in records) for k in ('segment','via')} for n in sorted(nets)}}
(OUT/'routing-preservation-inventory.json').write_text(json.dumps(ports,indent=2)+'\n')
res={'status':'UNFINISHED; static analytic/text checks only; native loading, DRC, ERC/parity, refill, 3D and physical qualification not performed','native_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [HW/'nexus-style-fc.kicad_pcb',HW/'header-board/nexus-header-board.kicad_pcb',HW/'nexus-style-fc.kicad_sch',HW/'header-board/nexus-header-board.kicad_sch']},'tests':{'closed_main_cutout_contours':True,'continuous_child_bottom_contour':True,'native_and_generated_mating_pad_geometry_agree':True,'full_1p2_signal_1p6_power_widths_retained':True,'all_22_mating_pads_nominal_edge_limits':True,'main_signal_pinmap_and_all_connected_pad_ids_unchanged':'asserted by transaction','main_schematic_expected_sha256':'49f9e0571424d0610e294bdcd6b120a42d04db284ecda9e660428fc587e62699'},'mating_pads':mating,'tolerance_screen':cases,'transverse_tilt_screen':tilt,'geometric_strength_screen':{'material':'unspecified laminate; no material rating assumed','single_tab_root_gross_section_mm2':8.4*1.6,'single_tab_out_of_plane_nominal_section_modulus_mm3':8.4*1.6**2/6,'sum_nominal_flat_seat_lengths_mm':1.6,'sum_nominal_seat_area_mm2':1.6*1.6,'main_outer_ligament_nominal_mm':.6,'main_central_web_nominal_mm':1.2,'main_front_ligament_nominal_mm':1.35,'single_slot_removed_area_mm2':10*2.1-(4-pi)*.5**2,'limitations':'Gross sections only; not FEA or allowable loads. Connector loads, lever arm, restraint/load sharing, notch concentration, laminate stack/fibre direction, solder alloy/fillet/current, creep, fatigue, shock and thermal cycles need definition/qualification.'}}
assert res['native_sha256']['hardware/nexus-style-fc.kicad_sch']==res['tests']['main_schematic_expected_sha256']
(OUT/'static-validation.json').write_text(json.dumps(res,indent=2)+'\n')
print(json.dumps({'checks':res['tests'],'cases':cases,'tilt':tilt},indent=2))
