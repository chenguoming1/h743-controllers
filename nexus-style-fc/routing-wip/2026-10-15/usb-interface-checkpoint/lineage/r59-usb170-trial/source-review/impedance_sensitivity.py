"""Lightweight explicit analytic sensitivity proxies only. No field solver and no PCB modification."""
from source_context import *
w=.150;t=.0152;gap=.127;d=w+gap
# An equivalent thin wire represents each strip. Two-radius choices expose shape sensitivity,
# not a rigorous finite-width correction or accuracy bound. Infinite flat equipotential planes.
def two_plane(h_up,h_down,er,r):
 b=h_up+h_down
 selfterm=math.log(2*b/(math.pi*r)*math.sin(math.pi*h_up/b))
 mutual=.5*math.log((math.cosh(math.pi*d/b)-math.cos(2*math.pi*h_up/b))/(math.cosh(math.pi*d/b)-1))
 return 120/math.sqrt(er)*(selfterm-mutual)
def single_plane(h,er,r):return 120/math.sqrt(er)*(math.log(2*h/r)-.5*math.log(1+(2*h/d)**2))
cases=[]
for name,ha,hb in [('In2_and_In4_covered',.1532+t/2,.55+t/2),('In2_absent_In1_and_In4_covered',.1532+.0152+.55+t/2,.55+t/2)]:
 vals=[dict(epsilon_r=er,equivalent_radius_mm=r,zdiff_proxy_ohm=two_plane(ha,hb,er,r)) for er in [4.16,4.6] for r in [w/4,(w+t)/4]]
 cases.append(dict(name=name,upper_plane_distance_from_trace_center_mm=ha,lower_plane_distance_from_trace_center_mm=hb,sensitivity_cases=vals,minimum_proxy_ohm=min(q['zdiff_proxy_ohm'] for q in vals),maximum_proxy_ohm=max(q['zdiff_proxy_ohm'] for q in vals),representative_proxy_ohm=two_plane(ha,hb,4.38,(w+t)/4)))
one=[single_plane(.55+t/2,er,r) for er in [4.16,4.6] for r in [w/4,(w+t)/4]]
z0=87/math.sqrt(4.16+1.41)*math.log(5.98*.1164/(.8*w+.035));outer=2*z0*(1-.48*math.exp(-.96*gap/.1164))
result=dict(source_sha256=H,geometry=dict(width_mm=w,edge_gap_mm=gap,inner_copper_mm=t,adjacent_dielectric_mm=[.1532,.55],adjacent_epsilon_r=[4.16,4.6]),method='Equivalent-wire analytic image-charge proxy for two strips between infinite solid grounded planes. Zdiff = 120/sqrt(er) * {ln[(2b/(pi*r))*sin(pi*h_up/b)] - 0.5*ln[(cosh(pi*d/b)-cos(2*pi*h_up/b))/(cosh(pi*d/b)-1)]}; b=h_up+h_down; d=w+gap. A homogeneous er sensitivity sweep brackets the declared Er values but does not model the actual dielectric interfaces. r=w/4 and (w+t)/4 are shape sensitivity choices, not guaranteed bounds.',cases=cases,covered_to_absent_representative_change_ohm=cases[1]['representative_proxy_ohm']-cases[0]['representative_proxy_ohm'],single_remote_In4_only_sensitivity_ohm=[min(one),max(one)],outer_F_or_B_microstrip_seed_ohm=outer,outer_formula='TI-style microstrip approximation: Z0=87/sqrt(er+1.41)*ln(5.98h/(.8w+t)); Zdiff=2Z0*(1-.48exp(-.96gap/h)). h=.1164,t=.035,er=4.16. Only a parallel outer segment with actual adjacent GND, not the internal trunk or uncoupled terminals.',limits=['These numbers are analytic sensitivity cases, not rigorous upper/lower bounds, tolerance ranges, field-solver output, eye-diagram results, or fabricator qualification.','Actual finite rectangular strips, two dielectric materials, plane edges, near signal/power copper, coplanar GND after refill, soldermask, etched width and frequency dispersion are omitted.','Covered and uncovered labels describe idealized cross sections; real saved-fill edges are gradual multiconductor transitions.','In2 non-GND copper cannot automatically be treated as an equipotential GND plane. Its impedance/termination and coupling may change both odd and common modes.','No numerical length or skew acceptance threshold is imposed.','Nominal total declared thickness1.6168mm vs1.6mm is a production stack confirmation item, not by itself a fabrication defect.'],sources=[dict(title='NBS/NIST strip-transmission-line paper, capacitance and lossless Z=1/(vC) basis',url='https://nvlpubs.nist.gov/nistpubs/jres/71C/jresv71Cn1p59_A1b.pdf'),dict(title='TI stripline/microstrip hardware guide and approximation limitations',url='https://www.ti.com/lit/an/sprabi2d/sprabi2d.pdf'),dict(title='TI differential-pair guidance: fairly constant/equal odd-mode impedance',url='https://www.ti.com/document-viewer/lit/html/SSZTCR1')])
(D/'impedance-sensitivity.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
