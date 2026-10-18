"""Actual-copper local 2D sensitivity on the candidate's explicit stack.

Includes all six extracted copper layers, finite ground intervals/antipads,
0.01 mm CAD masks (Er 3.8), and external air. Differential energy impedance
is a local quasi-static estimate, not a 3D crossing/via/connector solve.
"""
from pathlib import Path
import json
import sys

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[3]
sys.path.insert(0,str(ROOT/'tools'))
from sexpr import parse,find,text
sys.path.insert(0,str(OUT.parent/'usb-impedance-2026-10-17'))
from solve_sections import impedance

def stack(pcb):
    entries=find(find(parse(pcb.read_text()),'setup')[0],'stackup')[0]
    depth=0;slabs=[];copper={};previous_er=4.16
    for entry in find(entries,'layer'):
        name=text(entry[1])
        if not (name.endswith('.Cu') or name.startswith('dielectric')):continue
        chunks=[[]]
        for child in entry[2:]:
            if child=='addsublayer':chunks.append([])
            else:chunks[-1].append(child)
        if name.endswith('.Cu'):
            thickness=float(find(entry,'thickness')[0][1])
            copper[name]=[depth,depth+thickness]
            slabs.append([depth,depth+thickness,previous_er])
            depth+=thickness
        else:
            for chunk in chunks:
                thickness=float(find(chunk,'thickness')[0][1]);er=float(find(chunk,'epsilon_r')[0][1])
                slabs.append([depth,depth+thickness,er]);depth+=thickness;previous_er=er
    # Outer copper voids/masks approximate the exposed edge environment;
    # the main internal pair is substantially screened by ground planes.
    slabs[0][2]=3.8;slabs[-1][2]=3.8
    slabs=[[-.51,-.01,1],[-.01,0,3.8]]+slabs+[[depth,depth+.01,3.8],[depth+.01,depth+.51,1]]
    return slabs,copper,[-.51,depth+.51]

def main():
    source=json.loads((OUT/'sections.json').read_text())
    pcb=Path(source['source']);slabs,copper,extent=stack(pcb);cases=[];results=[]
    for section in source['sections']:
        for foreign in ['floating','AC-grounded']:
            labels={'GND':0,'USB_DP':1,'USB_DN':2};nextlabel=3;rects=[]
            for layer,nets in section['copper'].items():
                top,bottom=copper[layer]
                for net,intervals in nets.items():
                    if net not in labels:
                        labels[net]=nextlabel if foreign=='floating' else 0;nextlabel+=1
                    for left,right in intervals:
                        rects.append([left,right,top,bottom,labels[net]])
            config=dict(name=f"Actual six-layer slice y={section['y_mm']:.1f}, foreign {foreign}",
                        rects=rects,extent_y=extent,dielectric=slabs,
                        signal_top_width_reduction_mm=.01778)
            cases.append(config)
            for fine in [.005,.0025]:
                result=impedance(config,fine,halfspan=1.5);results.append(result)
                print(result['name'],fine,round(result['differential_ohm'],3),flush=True)
                (OUT/'field-results.json').write_text(json.dumps(dict(source_sha256=source['sha256'],method=__doc__,results=results),indent=2))
    (OUT/'field-input.json').write_text(json.dumps(dict(source_sha256=source['sha256'],method=__doc__,copper_z_mm=copper,dielectric=slabs,cases=cases),indent=2))
    # Lateral-domain check on the first ground-covered and one crossing slice.
    domain=[]
    for index in [0,4]:
        answer=impedance(cases[index],.0025,halfspan=2.5);domain.append(answer)
        print('DOMAIN',answer['name'],answer['differential_ohm'],flush=True)
    (OUT/'field-domain-check.json').write_text(json.dumps(domain,indent=2))

if __name__=='__main__':main()
