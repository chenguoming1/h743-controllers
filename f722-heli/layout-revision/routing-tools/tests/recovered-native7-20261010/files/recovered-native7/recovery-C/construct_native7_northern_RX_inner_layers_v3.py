"""Keep the proven northern RX-down entry; test only direct In3 and B trunks."""
import argparse
import importlib.util
import json
from pathlib import Path
import signal
import sys
import time

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent.parent
sys.path.insert(0,str(ROOT/'ordinary-routing/tests/native13-access'))
import native7_recovered_context_v3 as adapter
from prepare_native7_coordinated_context_v3 import replay


def module(path):
    spec=importlib.util.spec_from_file_location('C_northern_inner_bound',path)
    result=importlib.util.module_from_spec(spec);spec.loader.exec_module(result)
    return result


def main(contract_file):
    started=time.monotonic();contract=json.loads(contract_file.read_text())
    for row in contract['source_files']:
        assert adapter.digest(ROOT/row['path'])==row['sha256'],row['path']
    deadline=started+contract['internal_seconds'];output=ROOT/contract['receipt']
    out={'schema':'f722-native7-northern-RX-inner-layers/v3','source_contract_sha256':adapter.digest(contract_file),
         'script_sha256':adapter.digest(__file__),'complete':False,'selected':False,'native_board_edited':False,
         'stages':[],'attempts':[],'held_source_entry_unchanged':True,'tested_inner_layers':['In3.Cu','B.Cu'],
         'full_C_SPI_B_support_donor_restoration_pending':True}
    def save():
        out['seconds']=time.monotonic()-started
        output.write_text(json.dumps(out,indent=2,allow_nan=False)+'\n')
    def stage(name,event):
        now=time.monotonic();out['stages'].append({'stage':name,'event':event,'elapsed_seconds':now-started,'remaining_seconds':deadline-now});save()
    def alarm(signum,frame):
        out['terminal_reason']='Bounded two-layer control deadline; no candidate selected';save();raise TimeoutError(out['terminal_reason'])
    signal.signal(signal.SIGALRM,alarm);signal.alarm(contract['internal_seconds'])
    try:
        C=module(ROOT/contract['C_helper']);g=adapter.load();out['source']=g.binding()
        proposal,scope,cuts,held,added,reservation,reserved_via=replay(g)
        packet,scope,view=C._load(g,held+added+[reserved_via]);objects=held+added
        source=json.loads((ROOT/contract['source_packet']).read_text())
        assert source['common_packet_sha256']==C.COMMON_SHA
        assert source['C_scope_sha256']==C.SCOPE_SHA
        assert source['source_entry_C_support']['passed'] and not source['complete_RX_down']
        out['source_packet_sha256']=adapter.digest(ROOT/contract['source_packet'])
        out['removed_native_ids']=sorted(cuts);out['retired_planning_only_reservation']=reservation['name']
        jobs=C._jobs(g);job=next(j for j in jobs if j['name']=='RX_down')
        assert len(source['routes'])==len(source['vias'])==1
        initial_snapshot=C._snapshot(objects);seed_checks=[]
        for row in source['vias']+source['routes']:
            assert row['role']=='downstream' and row['net']==job['net']
            alias,branch=C._view(view,job,objects)
            check=(g.check_via(alias,row['xy'],objects=branch) if row['kind']=='via' else
                   g.check_track(alias,row['layer'],row['points'],width=row['width'],objects=branch))
            result={'name':row['name'],'passed':C._passed(check),'nearest':check[:5]}
            if row['kind']=='track':
                witnesses=C._section(g,row,objects);result['full_width_contacts']=witnesses
                result['passed'] &= all(any(w['point']==p and w['passed'] for w in witnesses) for p in (row['points'][0],row['points'][-1]))
                entry=g.track(row['net'],row['layer'],row['points'],row['name'],row['width'])
            else:entry=g.via(row['net'],row['xy'],row['name'])
            seed_checks.append(result)
            if not result['passed']:raise C.CFailure('Exact source entry replay failed: '+row['name'])
            objects.append((dict(entry[0],role='downstream'),*entry[1:]))
        out['held_routes']=source['routes'];out['held_vias']=source['vias'];out['source_replay_checks']=seed_checks
        C._preserved(initial_snapshot,objects);seed_snapshot=C._snapshot(objects)
        xy=source['vias'][0]['xy'];target=contract['retained_target_barrel']
        target_records=[q[0] for q in objects if q[0].get('kind')=='via' and q[0].get('net')==job['net'] and q[0].get('xy')==target]
        if len(target_records)!=1:raise C.CFailure('Exact retained RX-down target barrel missing')
        out['retained_target_barrel']=target_records[0]
        stage('exact_northern_F_entry_replay','passed')
        peer_jobs=[('FLASH_SCK','U1.34','U3.6'),('FLASH_MISO','U1.35','U3.2'),('FLASH_MOSI','U1.36','U3.5'),
                   ('PORT_B_RX_MCU','U1.37','R32.2'),('PORT_B_TX_MCU','U1.38','R33.2'),
                   ('FLASH_CS','U1.33','U3.1'),('FLASH_CS','U1.33','R4.2'),
                   ('DSM_RX_MCU','U1.43','R38.2'),('DSM_RX_MCU','U1.43','R71.2'),
                   ('IMU_CS','U1.20','U2.12'),('IMU_CS','U1.20','R3.2'),('LED_GREEN_K','U1.3','D1.1')]
        # The previous run never reached shared peer checks. Establish this
        # exact source-entry-only baseline before assigning causality to a trunk.
        baseline={'passed':False,'checks':[]};out['source_entry_peer_baseline']=baseline
        base_graphs={};stage('source_entry_peer_baseline','start')
        for net,a_key,b_key in peer_jobs:
            C._deadline(deadline);a,b=g.one_pad(a_key),g.one_pad(b_key)
            jp={'name':net,'net':net,'role':None,'width':.127,'a':a['xy'],'b':b['xy'],
                'start_layers':list(a['copper']),'end_layers':list(b['copper']),'layers':list(C.ORDINARY)}
            if C._already_connected(g,view,jp,objects):
                row={'net':net,'start_key':a_key,'end_key':b_key,'connected':True,'actual_copper_connected':True}
            else:
                if net not in base_graphs:
                    with C._width_state(g,.127):base_graphs[net]=g.gg.build(net,objects)
                plan=g.gg.connect(base_graphs[net],a['xy'],b['xy'],tuple(a['copper']),tuple(b['copper']))
                row={'net':net,'start_key':a_key,'end_key':b_key,'connected':plan['connected'],'plan':plan}
            baseline['checks'].append(row);save()
        baseline['passed']=all(x['connected'] for x in baseline['checks'])
        if not baseline['passed']:raise C.CFailure('Held northern F-entry/barrel fails a shared peer demand before any alternate inner trunk')
        stage('source_entry_peer_baseline','passed')
        for index,layer in enumerate(('In3.Cu','B.Cu')):
            C._deadline(deadline)
            work=list(objects);trial={'layer':layer,'complete':False,'routes':[],'vias':[],'checks':[]};out['attempts'].append(trial)
            stage(layer,'start')
            try:
                inner=dict(job,a=xy,b=target,start_layers=[layer],end_layers=[layer],layers=[layer])
                plan,graph=C._plan(g,view,inner,work,deadline);trial['actual_target_plan']=plan;save()
                if not plan['connected']:raise C.CFailure('Actual northern barrel and retained target are disconnected on '+layer)
                assert not plan['new_vias']
                C._allocate(g,view,inner,plan,work,'northern-RX-inner-'+str(index),trial['routes'],trial['vias'],trial['checks'],min(deadline-60,time.monotonic()+35),complete=True)
                assert not trial['vias']
                if not C._already_connected(g,view,job,work):raise C.CFailure('Full actual R34.1 connection missing')
                stage(layer+'_actual_RX_down','complete')
                guard={'passed':False,'checks':[]};trial['remaining_C_support']=guard
                C._all_C_plans(g,view,jobs,work,deadline,record=guard);save()
                if not guard['passed']:raise C.CFailure('Alternative inner trunk consumes an actual C/VX path')
                stage(layer+'_C_support','passed')
                trial['peer_access']={'passed':False,'checks':[]};graphs={}
                for net,a_key,b_key in peer_jobs:
                    C._deadline(deadline);a,b=g.one_pad(a_key),g.one_pad(b_key)
                    jp={'name':net,'net':net,'role':None,'width':.127,'a':a['xy'],'b':b['xy'],
                        'start_layers':list(a['copper']),'end_layers':list(b['copper']),'layers':list(C.ORDINARY)}
                    if C._already_connected(g,view,jp,work):
                        row={'net':net,'start_key':a_key,'end_key':b_key,'connected':True,'actual_copper_connected':True}
                    else:
                        if net not in graphs:
                            with C._width_state(g,.127):graphs[net]=g.gg.build(net,work)
                        plan=g.gg.connect(graphs[net],a['xy'],b['xy'],tuple(a['copper']),tuple(b['copper']))
                        row={'net':net,'start_key':a_key,'end_key':b_key,'connected':plan['connected'],'plan':plan}
                    trial['peer_access']['checks'].append(row);save()
                trial['peer_access']['passed']=all(x['connected'] for x in trial['peer_access']['checks'])
                if not trial['peer_access']['passed']:raise C.CFailure('Alternative inner trunk consumes an actual shared peer channel')
                groups=C._physical_groups(g,work,job['net']);cut=C._physical_groups(g,work,job['net'],'U15.1')
                contact=any({'U15.1','R34.1'}.issubset(x['keys']) for x in groups)
                bypass=any({'U15.10','R34.1'}.issubset(x['keys']) for x in cut)
                trial['actual_contacts_and_cut']={'groups':groups,'cut_groups':cut,'U15_1_to_R34_1_connected':contact,'no_NC10_to_R34_bypass_after_actual_pad_cut':not bypass}
                if not contact or bypass:raise C.CFailure('Actual bonded IO path or pad-cut proof failed')
                finite=[];annular=[]
                for row in source['routes']+source['vias']+trial['routes']:
                    others=[q for q in work if q[0]['uuid']!=row['name']];alias,branch=C._view(view,job,others)
                    check=(g.check_track(alias,row['layer'],row['points'],width=row['width'],objects=branch) if row['kind']=='track' else g.check_via(alias,row['xy'],objects=branch))
                    finite.append({'name':row['name'],'passed':C._passed(check),'nearest':check[:5]})
                    if row['kind']=='track':annular.extend(C._annular_entries(g,row,work))
                trial['final_mutual_finite']=finite;trial['annular_entries']=annular
                if not all(x['passed'] for x in finite+annular):raise C.CFailure('Final finite or annular gate failed')
                C._preserved(seed_snapshot,work);trial['complete']=True;out['complete']=True;out['accepted_attempt']=index
                out['terminal_reason']='Complete northern RX-down preserves measured C/VX and peer access; joint routing/native validation pending'
                stage(layer,'passed');break
            except C.CFailure as error:
                trial['terminal_reason']=str(error);stage(layer,'failed')
        if not out['complete']:out['terminal_reason']='Neither direct In3 nor B trunk supplied a complete compatible northern RX-down path'
        save()
    except TimeoutError:pass
    except Exception as error:
        out['terminal_reason']=str(error);out['exception_type']=type(error).__name__;save()
    finally:
        signal.alarm(0)
        print(json.dumps({'complete':out['complete'],'terminal_reason':out.get('terminal_reason'),'seconds':time.monotonic()-started,'receipt_sha256':adapter.digest(output)},indent=2),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--contract',type=Path,required=True)
    main(parser.parse_args().contract)
