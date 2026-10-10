"""Exact IO4 finite and ordinary-domain prerequisite, with actual support add-backs."""
import argparse,json,signal,time
from pathlib import Path
from native7_RX_IO4_model_v2 import build,adapter,HERE,ROOT

def main(path):
    start=time.monotonic();ct=json.loads(path.read_text());end=start+ct['internal_seconds']
    for item in ct['source_files']:assert adapter.digest(ROOT/item['path'])==item['sha256'],item['path']
    output=ROOT/ct['receipt'];out={'schema':'f722-native7-RX-IO4-access/v3','complete':False,'selected':False,'native_board_edited':False,'contract_sha256':adapter.digest(path),'routes':[],'vias':[],'checks':[],'stages':[]}
    def save():out['seconds']=time.monotonic()-start;output.write_text(json.dumps(out,indent=2,allow_nan=False)+'\n')
    def stage(name):out['stages'].append({'stage':name,'elapsed_seconds':time.monotonic()-start,'remaining_seconds':end-time.monotonic()});save()
    def alarm(sig,frame):out['terminal_reason']='Bounded IO4 access prerequisite deadline';save();raise TimeoutError()
    signal.signal(signal.SIGALRM,alarm);signal.alarm(ct['internal_seconds'])
    try:
        from shapely.geometry import Point
        from shapely.ops import unary_union,nearest_points
        g,base,C,view,work,before,inventory,jobs=build();out['inventory']=inventory;baseline=list(work)
        ground=inventory['dedicated_U2_9_ground'];out['routes'].extend(ground['routes']);out['vias'].extend(ground['vias']);out['dedicated_ground_finite']=[]
        for r in ground['routes']+ground['vias']:
            others=[q for q in work if q[0]['uuid']!=r['name']]
            finite=g.check_via('GND',r['xy'],objects=others) if r['kind']=='via' else g.check_track('GND',r['layer'],r['points'],width=r['width'],objects=others)
            row={'name':r['name'],'passed':C._passed(finite),'nearest':finite[:8]}
            if r['kind']=='track':
                row['full_width_contacts']=C._section(g,r,others)
                row['passed']=row['passed'] and all(any(z['point']==p and z['passed'] for z in row['full_width_contacts']) for p in (r['points'][0],r['points'][-1]))
            out['dedicated_ground_finite'].append(row)
        if not all(r['passed'] for r in out['dedicated_ground_finite']):raise C.CFailure('Dedicated U2.9 return fails finite process or full-width contact prerequisite')
        groups=C._physical_groups(g,work,'GND');keys={'U2.6','U2.7','U2.9'}
        ground_contact=any(keys.issubset(set(z['keys'])) and ground['vias'][0]['name'] in z['ids'] for z in groups)
        out['dedicated_ground_saved_fill_DC']={'passed':ground_contact,'actual_required_pad_keys':sorted(keys),'new_barrel':ground['vias'][0]['name'],'fresh_native_fill_and_AC_reference_pending':True}
        if not ground_contact:raise C.CFailure('Dedicated U2.9 return has no actual pad/barrel/source ground component connection')
        stage('dedicated_U2_9_return_finite_and_source_DC')
        out['common_addback_finite']=[]
        for record in inventory['common_addback_records']:
            C._deadline(end);peers=[q for q in work if q[0]['uuid']!=record['uuid']]
            if record['net'] in ('PORT_C_RX_EXT','PORT_C_TX_EXT'):
                role=next(q[0] for q in work if q[0]['uuid']==record['uuid']).get('role')
                if role is None:
                    scope=json.loads((HERE/'native7-C-compact-scope-receipt-v4.json').read_text());role=scope['protected_branch_role_metadata'][record['uuid']]['role']
                net,peers=view(record['net'],role,peers)
            else:net=record['net']
            checks=g.check_via(net,record['xy'],objects=peers) if record['kind']=='via' else g.check_track(net,next(iter(record['copper'])),[record['start'],record['end']],width=record['width'],objects=peers)
            out['common_addback_finite'].append({'uuid':record['uuid'],'net':record['net'],'passed':C._passed(checks),'nearest':checks[:4]})
        if not all(x['passed'] for x in out['common_addback_finite']):
            raise C.CFailure('A complete native TX/VX/R3 add-back conflicts with the shared proposal before any IO4 route; this is a pre-existing donor obligation')
        stage('all_native_TX_VX_R3_addbacks_finite')
        # The upstream stub is real copper through the bonded IO4 pad to NC6, never an internal NC link.
        up=next(j for j in jobs if j['name']=='RX_up');bridge=dict(up,a=g.one_pad('U15.5')['xy'],b=g.one_pad('U15.6')['xy'],layers=['F.Cu'])
        C._add_track(g,view,bridge,work,'F.Cu',bridge['a'],bridge['b'],'IO4-RX-up-bonded-to-NC6',out['routes'],out['checks'],end)
        if not C._already_connected(g,view,bridge,work):raise C.CFailure('Actual IO4-to-NC6 physical contact proof failed')
        out['actual_bonded_IO4_bridge']={'passed':True,'bonded_key':'U15.5','NC_key':'U15.6','actual_footprint_unchanged':True,'no_internal_connection_assumed':True}
        stage('actual_IO4_upstream_bridge_finite')
        out['RX_plans']=[]
        for job in jobs[:2]:
            plan,graph=C._plan(g,view,job,work,end);row={'job':job,'plan':plan};out['RX_plans'].append(row)
            alias,peers=C._view(view,job,work)
            with C._width_state(g,.127):free,_,vobs=g.rt.domain(alias,'F.Cu',objects=peers)
            source=g.rt.component(free,job['a']);legal=g.s.OUTLINE.buffer(-.479-g.s.ERROR-.0001).difference(g.rt.expanded(vobs))
            row['actual_source_F_domain']={'area_mm2':0 if source is None else source.area,'bounds':None if source is None else list(source.bounds),'wkb_hex':None if source is None else source.wkb_hex}
            eligible=None if source is None else source.intersection(legal)
            row['unrestricted_source_connected_via_domain']={'area_mm2':0 if eligible is None else eligible.area,'bounds':None if eligible is None or eligible.is_empty else list(eligible.bounds),'wkb_hex':None if eligible is None else eligible.wkb_hex}
            if not plan['connected']:
                fs={}
                for side in ('source','target'):
                    fs[side]=unary_union([graph['nodes'][r['node']][1] for r in plan['actual_frontier'] if r['side']==side and r['layer']=='F.Cu'])
                if not fs['source'].is_empty and not fs['target'].is_empty:
                    a,b=nearest_points(fs['source'],fs['target']);pts=[[a.x,a.y],[b.x,b.y]]
                    row['nearest_F_frontier']={'gap_mm':a.distance(b),'points':pts,'checks':g.check_track(alias,'F.Cu',pts,width=.127,objects=peers)[:12]}
            save()
        out['both_RX_jobs_reachable']=all(r['plan']['connected'] for r in out['RX_plans']);stage('both_actual_RX_domains_measured')
        # Independent functions are checked even on an RX failure to retain useful causal evidence.
        out['remaining_C_support']={'passed':False,'checks':[]}
        C._all_C_plans(g,view,jobs[2:],work,end,record=out['remaining_C_support']);save()
        peers=[('FLASH_SCK','U1.34','U3.6'),('FLASH_MISO','U1.35','U3.2'),('FLASH_MOSI','U1.36','U3.5'),('PORT_B_RX_MCU','U1.37','R32.2'),('PORT_B_TX_MCU','U1.38','R33.2'),('FLASH_CS','U1.33','U3.1'),('FLASH_CS','U1.33','R4.2'),('DSM_RX_MCU','U1.43','R38.2'),('DSM_RX_MCU','U1.43','R71.2'),('IMU_CS','U1.20','U2.12'),('IMU_CS','U1.20','R3.2'),('LED_GREEN_K','U1.3','D1.1')]
        out['peer_access']={'passed':False,'checks':[]};graphs={}
        for net,ak,bk in peers:
            C._deadline(end);a,b=g.one_pad(ak),g.one_pad(bk);job={'name':net,'net':net,'role':None,'width':.127,'a':a['xy'],'b':b['xy'],'start_layers':list(a['copper']),'end_layers':list(b['copper']),'layers':list(C.ORDINARY)}
            if C._already_connected(g,view,job,work):r={'net':net,'start_key':ak,'end_key':bk,'connected':True,'actual_held_copper_connected':True}
            else:
                if net not in graphs:
                    with C._width_state(g,.127):graphs[net]=g.gg.build(net,work)
                plan=g.gg.connect(graphs[net],a['xy'],b['xy'],tuple(a['copper']),tuple(b['copper']));r={'net':net,'start_key':ak,'end_key':bk,'connected':plan['connected'],'plan':plan}
            out['peer_access']['checks'].append(r);save()
        out['peer_access']['passed']=all(r['connected'] for r in out['peer_access']['checks'])
        out['complete']=out['both_RX_jobs_reachable'] and out['remaining_C_support']['passed'] and out['peer_access']['passed']
        out['terminal_reason']='Actual IO4 domains and all C/support/peer access measured; complete copper construction and paired schematic/native proof remain required'
        save()
    except TimeoutError:pass
    except Exception as e:out['terminal_reason']=str(e);out['exception_type']=type(e).__name__;save()
    finally:
        signal.alarm(0);print(json.dumps({'complete':out['complete'],'terminal_reason':out.get('terminal_reason'),'seconds':time.monotonic()-start,'receipt_sha256':adapter.digest(output)},indent=2),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--contract',type=Path,required=True);main(p.parse_args().contract)
