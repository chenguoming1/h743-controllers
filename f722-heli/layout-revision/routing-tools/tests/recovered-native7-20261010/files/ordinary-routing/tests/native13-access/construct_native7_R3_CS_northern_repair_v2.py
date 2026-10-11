"""Complete R3 leaf plus coordinated FLASH_CS entry relocation; primary return held."""
import argparse, importlib.util, json, resource, signal, sys, time
from datetime import datetime, timezone
from pathlib import Path
from shapely.geometry import Point
H=Path(__file__).resolve().parent;ROOT=H.parents[2]
sys.path.insert(0,str(H))
import native7_recovered_context_v3 as adapter
from prepare_native7_coordinated_context_v3 import replay
import native7_joint_routing_helpers_v3 as routing
import native7_positive_contact_partition_v1 as positive

SUPPLY='da1f25da-e0ad-4065-9e0c-44670c3de5fa'
CS_ENTRY={'recovered-four-source-0','recovered-four-source-1','recovered-FLASH_CS-source-via'}
PEERS=[('FLASH_SCK','U1.34','U3.6'),('FLASH_MISO','U1.35','U3.2'),('FLASH_MOSI','U1.36','U3.5'),('PORT_B_RX_MCU','U1.37','R32.2'),('PORT_B_TX_MCU','U1.38','R33.2'),('FLASH_CS','U1.33','U3.1'),('FLASH_CS','U1.33','R4.2'),('DSM_RX_MCU','U1.43','R38.2'),('DSM_RX_MCU','U1.43','R71.2'),('IMU_CS','U1.20','U2.12'),('IMU_CS','U1.20','R3.2'),('LED_GREEN_K','U1.3','D1.1')]

def module(path):
    spec=importlib.util.spec_from_file_location('R3_bound_C',path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def main(path):
    start=time.monotonic();contract=json.loads(path.read_text())
    for row in contract['source_files']:assert adapter.digest(ROOT/row['path'])==row['sha256'],row['path']
    deadline=start+contract['internal_seconds'];output=ROOT/contract['receipt'];router=None
    out=dict(schema='f722-native7-R3-CS-northern-repair/v2',complete=False,selected=False,native_board_edited=False,
             contract_sha256=adapter.digest(path),script_sha256=adapter.digest(__file__),started_at_utc=datetime.now(timezone.utc).isoformat(),stages=[],attempts=[],additional_removed_records=[])
    def save():
        out['seconds']=time.monotonic()-start;r=resource.getrusage(resource.RUSAGE_SELF)
        out['resources']={'user_cpu_seconds':r.ru_utime,'system_cpu_seconds':r.ru_stime,'peak_resident_memory_KiB':r.ru_maxrss}
        if router:out['routes']=router.routes;out['vias']=router.vias;out['routing_attempts']=router.attempts
        output.write_text(json.dumps(out,indent=2,allow_nan=False)+'\n')
    def stage(name):out['stages'].append({'name':name,'seconds':time.monotonic()-start});save()
    def alarm(*args):raise TimeoutError('Bounded local R3 repair deadline')
    signal.signal(signal.SIGALRM,alarm);signal.alarm(contract['internal_seconds'])
    try:
        C=module(ROOT/contract['C_helper']);g=adapter.load();out['source']=g.binding()
        proposal,scope,cuts,held,added,reservation,reserved_via=replay(g)
        _,_,view=C._load(g,held+added+[reserved_via]);objects=held+added
        seed=json.loads((ROOT/contract['source_packet']).read_text());out['source_packet_sha256']=adapter.digest(ROOT/contract['source_packet'])
        assert seed['common_packet_sha256']==C.COMMON_SHA and seed['C_scope_sha256']==C.SCOPE_SHA
        seed_checks=[];cjob=next(j for j in C._jobs(g) if j['name']=='RX_down')
        for row in seed['vias']+seed['routes']:
            alias,branch=C._view(view,cjob,objects)
            check=g.check_via(alias,row['xy'],objects=branch) if row['kind']=='via' else g.check_track(alias,row['layer'],row['points'],width=row['width'],objects=branch)
            seed_checks.append({'name':row['name'],'passed':C._passed(check),'nearest':check[:4]})
            if not C._passed(check):raise RuntimeError('Exact northern seed finite replay failed')
            entry=g.via(row['net'],row['xy'],row['name']) if row['kind']=='via' else g.track(row['net'],row['layer'],row['points'],row['name'],row['width'])
            objects.append((dict(entry[0],role='downstream'),*entry[1:]))
        out['northern_seed_checks']=seed_checks;out['held_northern_routes']=seed['routes'];out['held_northern_vias']=seed['vias']
        out['original_removed_native_ids']=sorted(cuts);out['retired_planning_reservation']=reservation['name']
        out['R3_pad_records']=[g.one_pad('R3.1'),g.one_pad('R3.2')];out['exclusive_supply_record']=g.by[SUPPLY]
        assert g.by[SUPPLY]['net']=='+3V3_IMU' and g.by[SUPPLY]['width']==.2
        original_snapshot=C._snapshot(objects);router=routing.Router(g,objects,deadline,prefix='R3-northern')
        stage('exact_shared_context_replayed')
        initial_holes=positive.drill_voids(router.objects,g.N['copper_layers'])
        initial_groups=[]
        for net in ['IMU_CS','+3V3_IMU']:
            groups,membership=positive.partition(router.objects,net,g.N['copper_layers'],holes=initial_holes)
            initial_groups.append({'net':net,'groups':[{'record_uuids':sorted(group),'actual_pads':sorted(q[0]['key'] for q in router.objects if q[0]['uuid'] in group and q[0].get('key'))} for group in groups]})
        out['before_actual_source_groups']=initial_groups;save()
        def assess(label,work):
            a,b=g.one_pad('U1.20'),g.one_pad('R3.2')
            graph,plan=router.graph('IMU_CS',a['xy'],b['xy'],tuple(a['copper']),tuple(b['copper']),objects=work)
            row={'label':label,'actual_pad_plan':plan,'target_domains':[],'source_domains':[]}
            frontier=routing.source_target_frontier(g,graph,plan) if not plan['connected'] else []
            row['frontier']=frontier
            for key,nodes in [('target_domains',plan['end_nodes']),('source_domains',plan['start_nodes'])]:
                for node in nodes:
                    layer,poly=graph['nodes'][node];legal=graph['eligible'].get(node)
                    row[key].append({'node':node,'layer':layer,'area_mm2':poly.area,'bounds':list(poly.bounds),'wkb_hex':poly.wkb_hex,'legal_barrel_area_mm2':0 if legal is None else legal.area,'legal_barrel_wkb_hex':None if legal is None else legal.wkb_hex})
            blockers={x.get('uuid') for f in frontier for x in f['blockers']}
            row['actual_frontier_records']=[q[0] for q in work if q[0]['uuid'] in blockers]
            out['attempts'].append(row);save();return row,plan,graph
        row,plan,graph=assess('R3_fixed_pose_and_all_held_power',router.objects)
        if plan['connected']:
            raise RuntimeError('Pinned northern context unexpectedly changed; inspect baseline before entry relocation')
        removed=[q for q in router.objects if q[0]['uuid'] in CS_ENTRY]
        assert len(removed)==3 and all(q[0]['net']=='FLASH_CS' for q in removed)
        out['replaced_proposal_records']=[q[0] for q in removed]
        out['replaced_proposal_recipes']=[q for q in proposal['proposed_common_routes']+proposal['proposed_common_vias'] if q['name'] in CS_ENTRY]
        assert len(out['replaced_proposal_recipes'])==3
        router.objects=[q for q in router.objects if q[0]['uuid'] not in CS_ENTRY]
        row,plan,graph=assess('complete_FLASH_CS_source_entry_released_ground_held',router.objects)
        if not plan['connected']:
            raise RuntimeError('Complete FLASH_CS entry release does not restore actual R3 pad access; primary return held')
        router.layer_route('IMU_CS','F.Cu',[24.259999,10.365],g.one_pad('R3.2')['xy'],'R3-CS-joint-R3-F',budget=42)
        stage('complete_R3_CS_branch_constructed')
        cs_graph,cs_plan=router.graph('FLASH_CS',g.one_pad('U1.33')['xy'],[24.29,13.36],('B.Cu',),('In3.Cu',))
        out['replacement_FLASH_CS_entry_plan']=cs_plan
        if not cs_plan['connected']:
            out['replacement_FLASH_CS_frontier']=routing.source_target_frontier(g,cs_graph,cs_plan)
            raise RuntimeError('Held full R3 branch leaves no complete FLASH_CS source-to-retained-boundary graph')
        router.connect('FLASH_CS',g.one_pad('U1.33')['xy'],[24.29,13.36],'R3-CS-joint-CS-entry',('B.Cu',),('In3.Cu',),budget=65)
        stage('complete_FLASH_CS_source_entry_reconstructed')
        holes=positive.drill_voids(router.objects,g.N['copper_layers'])
        actual=[]
        for net,a,b in [('IMU_CS','U1.20','R3.2'),('IMU_CS','U1.20','U2.12'),('+3V3_IMU','C12.1','R3.1')]:
            _,membership=positive.partition(router.objects,net,g.N['copper_layers'],holes=holes)
            passed=bool(membership[g.one_pad(a)['uuid']] & membership[g.one_pad(b)['uuid']])
            actual.append({'net':net,'source':a,'target':b,'positive_area_drill_aware_connected':passed})
        cs_target=[q[0] for q in router.objects if q[0]['kind']=='via' and q[0]['net']=='FLASH_CS' and q[0].get('xy')==[24.29,13.36]]
        assert len(cs_target)==1
        _,members=positive.partition(router.objects,'FLASH_CS',g.N['copper_layers'],holes=holes)
        actual.append({'net':'FLASH_CS','source':'U1.33','retained_boundary_uuid':cs_target[0]['uuid'],'positive_area_drill_aware_connected':bool(members[g.one_pad('U1.33')['uuid']] & members[cs_target[0]['uuid']])})
        out['actual_restored_contacts']=actual
        if not all(r['positive_area_drill_aware_connected'] for r in actual):raise RuntimeError('Actual positive-area contact gate failed')
        finite=[];entries=[]
        for recipe in router.vias+router.routes:
            others=[q for q in router.objects if q[0]['uuid']!=recipe['name']]
            check=g.check_via(recipe['net'],recipe['xy'],objects=others) if recipe['kind']=='via' else g.check_track(recipe['net'],recipe['layer'],recipe['points'],width=recipe['width'],objects=others)
            finite.append({'name':recipe['name'],'passed':C._passed(check),'nearest':check[:5]})
            if recipe['kind']=='track':
                witnesses=C._section(g,recipe,router.objects);annular=C._annular_entries(g,recipe,router.objects)
                passed=all(any(w['point']==p and w['passed'] for w in witnesses) for p in [recipe['points'][0],recipe['points'][-1]]) and all(w['passed'] for w in annular)
                entries.append({'name':recipe['name'],'passed':passed,'full_width':witnesses,'annular':annular})
        for recipe in seed['routes']+seed['vias']:
            others=[q for q in router.objects if q[0]['uuid']!=recipe['name']];alias,branch=C._view(view,cjob,others)
            check=g.check_via(alias,recipe['xy'],objects=branch) if recipe['kind']=='via' else g.check_track(alias,recipe['layer'],recipe['points'],width=recipe['width'],objects=branch)
            finite.append({'name':recipe['name'],'held_northern_rechecked':True,'passed':C._passed(check),'nearest':check[:5]})
        out['finite']=finite;out['entries']=entries
        if not all(x['passed'] for x in finite+entries):raise RuntimeError('Full-width finite/entry gate failed')
        c_guard={'passed':False,'checks':[]};out['remaining_C_access']=c_guard;C._all_C_plans(g,view,C._jobs(g),router.objects,deadline,record=c_guard);save()
        if not c_guard['passed']:raise RuntimeError('Completed R3 repair blocks actual C/support access')
        peers={'passed':False,'checks':[]};out['peer_access']=peers;graphs={}
        for net,a,b in PEERS:
            C._deadline(deadline);aa,bb=g.one_pad(a),g.one_pad(b)
            if net not in graphs:graphs[net]=g.gg.build(net,router.objects)
            p=g.gg.connect(graphs[net],aa['xy'],bb['xy'],tuple(aa['copper']),tuple(bb['copper']))
            peers['checks'].append({'net':net,'source':a,'target':b,'connected':p['connected'],'plan':p});save()
        peers['passed']=all(x['connected'] for x in peers['checks'])
        if not peers['passed']:raise RuntimeError('Completed R3 repair blocks a shared actual peer demand')
        allowed=CS_ENTRY
        C._preserved({k:v for k,v in original_snapshot.items() if k not in allowed},router.objects)
        out['complete']=True;out['terminal_reason']='Complete conditional R3 and FLASH_CS source-entry restoration preserves actual C/peer access; no full joint/native acceptance'
    except Exception as exc:
        out['terminal_reason']=str(exc);out['exception_type']=type(exc).__name__
    finally:
        signal.alarm(0);save();print(json.dumps({k:out.get(k) for k in ['complete','terminal_reason','seconds','resources']},indent=2),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--contract',type=Path,required=True);main(p.parse_args().contract)
