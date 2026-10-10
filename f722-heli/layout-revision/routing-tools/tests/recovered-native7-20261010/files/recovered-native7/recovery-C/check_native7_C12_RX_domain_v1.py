"""One northern-cell source-domain control with exact conditional MISO fallback."""
import argparse,json,signal,time
from pathlib import Path
from native7_C12_shift_model_v1 import build,adapter,HERE,ROOT

def main(path):
    start=time.monotonic();ct=json.loads(path.read_text());end=start+ct['internal_seconds']
    for item in ct['source_files']:assert adapter.digest(ROOT/item['path'])==item['sha256'],item['path']
    output=ROOT/ct['receipt'];out={'schema':'f722-native7-C12-RX-domain/v1','complete':False,'selected':False,'native_board_edited':False,'contract_sha256':adapter.digest(path),'attempts':[]}
    def save():out['seconds']=time.monotonic()-start;output.write_text(json.dumps(out,indent=2,allow_nan=False)+'\n')
    def alarm(sig,frame):out['terminal_reason']='Bounded northern-cell prerequisite deadline';save();raise TimeoutError()
    signal.signal(signal.SIGALRM,alarm);signal.alarm(ct['internal_seconds'])
    try:
        from shapely.geometry import Point
        from shapely.ops import unary_union,polylabel,nearest_points
        g,base,C,view,original,before,replaced,inventory=build();out['inventory']=inventory
        if not inventory['mechanical']['passed'] or not all(x['passed'] for x in inventory['candidate_pad_checks']):raise C.CFailure('Candidate pad or courtyard prerequisite failed')
        job=next(x for x in C._jobs(g) if x['name']=='RX_down');job=dict(job,b=[25.397615,10.812554],end_layers=['F.Cu'],layers=['F.Cu'])
        supports=[dict(name='U2_VDD_feed',net='+3V3_IMU',role=None,width=.20,a=[25.797499,11.745],b=g.one_pad('C12.1')['xy']),
          dict(name='C11_C12_feed',net='+3V3_IMU',role=None,width=.20,a=g.one_pad('C11.1')['xy'],b=g.one_pad('C12.1')['xy']),
          dict(name='C12_GND',net='GND',role=None,width=.20,a=g.one_pad('C12.2')['xy'],b=[25.375,12.9]),
          dict(name='R3_pullup',net='+3V3_IMU',role=None,width=.127,a=g.one_pad('C12.1')['xy'],b=g.one_pad('R3.1')['xy'])]
        out['support_jobs']=supports
        for mode in ('MISO_retained','MISO_source_released'):
            C._deadline(end);source_contract=ct['candidate_contracts'][mode];sc=json.loads((ROOT/source_contract['path']).read_text());assert adapter.digest(ROOT/source_contract['path'])==source_contract['sha256']
            cuts=set(sc['additional_proposal_cut_ids']);work=[q for q in original if q[0]['uuid'] not in cuts]
            assert len(original)-len(work)==len(cuts)
            row={'mode':mode,'source_contract_sha256':source_contract['sha256'],'additional_proposal_removed_records':[q[0] for q in original if q[0]['uuid'] in cuts],'routes':[],'vias':[],'checks':[],'four_support_paths':[]};out['attempts'].append(row);save()
            net,peers=C._view(view,job,work)
            with C._width_state(g,.127):free,_,vobs=g.rt.domain(net,'F.Cu',objects=peers)
            source=g.rt.component(free,job['a']);assert source is not None
            legal=g.s.OUTLINE.buffer(-.479-g.s.ERROR-.0001).difference(g.rt.expanded(vobs))
            cell=g.rt.component(legal,[25.397615,10.812554]);assert cell is not None
            usable=source.intersection(cell)
            def region(p):return {'area_mm2':p.area,'bounds':None if p.is_empty else list(p.bounds),'wkb_hex':p.wkb_hex}
            row['unrestricted_source_F_domain']=region(source);row['full_northern_legal_barrel_cell']=region(cell);row['source_connected_northern_cell']=region(usable)
            if usable.is_empty or usable.area<1e-12:
                pocket=g.rt.component(free,[25.397615,10.812554]);row['northern_F_pocket']=None if pocket is None else region(pocket)
                if pocket is not None:
                    a,b=nearest_points(source,pocket);points=[[a.x,a.y],[b.x,b.y]];row['nearest_F_frontier']={'gap_mm':a.distance(b),'points':points,'checks':g.check_track(net,'F.Cu',points,width=.127,objects=peers)[:12]}
                row['terminal_reason']='No source-connected point in full exact northern legal cell';save();continue
            part=max(g.rt.parts(usable),key=lambda x:x.area);p=polylabel(part,tolerance=.000001);xy=[round(p.x,6),round(p.y,6)]
            assert usable.covers(Point(xy));row['selected_planning_xy']=xy
            C._add_via(g,view,job,work,xy,'C12-shift-RX-northern-via',row['vias'],row['checks'])
            C._add_track(g,view,job,work,'F.Cu',job['a'],xy,'C12-shift-RX-northern-F',row['routes'],row['checks'],end)
            for support in supports:
                C._deadline(end);sjob=dict(support,layers=list(C.ORDINARY),start_layers=['F.Cu'],end_layers=['F.Cu'])
                plan,_=C._plan(g,view,sjob,work,end);row['four_support_paths'].append({'job':support,'plan':plan});save()
            row['four_support_paths_reachable']=all(q['plan']['connected'] for q in row['four_support_paths'])
            row['terminal_reason']='Complete finite RX F entry/barrel and all four ordinary support plans measured; no support copper constructed'
            save()
            if row['four_support_paths_reachable']:
                out['complete']=True;out['terminal_reason']='A conditional northern allocation preserves all four actual support plans; complete support construction and all peer gates remain mandatory';break
            # An exact retained-MISO failure may justify the one explicitly declared source release.
        if not out.get('terminal_reason'):out['terminal_reason']='No tested northern source allocation preserves all four support plans'
        save()
    except TimeoutError:pass
    except Exception as e:out['terminal_reason']=str(e);out['exception_type']=type(e).__name__;save()
    finally:
        signal.alarm(0);print(json.dumps({'complete':out['complete'],'terminal_reason':out.get('terminal_reason'),'seconds':time.monotonic()-start,'receipt_sha256':adapter.digest(output)},indent=2),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--contract',type=Path,required=True);main(p.parse_args().contract)
