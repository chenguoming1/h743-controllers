"""One exact IO4 local-support prerequisite; no native mutation or selection."""
import argparse,json,math,signal,time
from pathlib import Path
from native7_RX_IO4_model_v3 import build,adapter,HERE,ROOT

PEERS=[('FLASH_SCK','U1.34','U3.6'),('FLASH_MISO','U1.35','U3.2'),('FLASH_MOSI','U1.36','U3.5'),('PORT_B_RX_MCU','U1.37','R32.2'),('PORT_B_TX_MCU','U1.38','R33.2'),('FLASH_CS','U1.33','U3.1'),('FLASH_CS','U1.33','R4.2'),('DSM_RX_MCU','U1.43','R38.2'),('DSM_RX_MCU','U1.43','R71.2'),('IMU_CS','U1.20','U2.12'),('IMU_CS','U1.20','R3.2'),('LED_GREEN_K','U1.3','D1.1')]

def main(path):
    start=time.monotonic();ct=json.loads(path.read_text());end=start+ct['internal_seconds']
    for item in ct['source_files']:assert adapter.digest(ROOT/item['path'])==item['sha256'],item['path']
    output=ROOT/ct['receipt'];out={'schema':'f722-native7-IO4-joint-local-support/v2','complete':False,'selected':False,'native_board_edited':False,'contract_sha256':adapter.digest(path),'routes':[],'vias':[],'checks':[],'plans':[],'stages':[]}
    def save():out['seconds']=time.monotonic()-start;output.write_text(json.dumps(out,indent=2,allow_nan=False)+'\n')
    def stage(s):out['stages'].append({'stage':s,'elapsed_seconds':time.monotonic()-start,'remaining_seconds':end-time.monotonic()});save()
    def alarm(sig,frame):out['terminal_reason']='Bounded joint local-support prerequisite deadline';save();raise TimeoutError()
    signal.signal(signal.SIGALRM,alarm);signal.alarm(ct['internal_seconds'])
    try:
        from shapely.geometry import Point,box
        from shapely.ops import unary_union,polylabel
        g,base,C,view,work,before,inventory,jobs=build();packet=json.loads((ROOT/ct['packet']).read_text());scope=json.loads((ROOT/ct['scope']).read_text());out['source']=g.binding();out['scope']=scope;out['inventory']=inventory
        assert packet['source']==g.binding()
        for r in packet['routes']:
            if r['net']!='PORT_C_RX_EXT':continue
            q=g.track(r['net'],r['layer'],r['points'],r['name'],r['width']);work.append((dict(q[0],role=r['role']),*q[1:]))
        original={q[0]['uuid']:q for q in work};cuts={r['uuid'] for r in scope['additional_removed_native_records']}
        for r in scope['additional_removed_native_records']:assert original[r['uuid']][0]==r
        down=next(j for j in jobs if j['name']=='RX_down')
        walltrial=[q for q in work if q[0]['uuid'] not in scope['U15_ground_wall_native_ids']]
        p,_=C._plan(g,view,down,walltrial,end);out['ground_wall_only_RX_down_attribution']=p;stage('actual_IO5_after_only_complete_wall_pair_release')
        out['wall_only_failure_does_not_reject_combined_scope']=True
        work=[q for q in work if q[0]['uuid'] not in cuts]
        # Exact old stitch contact inventory; no barrel deletion is performed.
        oldvia=original['97282ff5-d6b5-415f-a3c4-0390df70f0ea'];contacts=[]
        for rec,cu,mask,drill in original.values():
            if rec['net']!='GND' or rec['uuid']==oldvia[0]['uuid']:continue
            areas={layer:cu[layer].intersection(oldvia[1][layer]).area for layer in cu.keys()&oldvia[1].keys()}
            areas={layer:area for layer,area in areas.items() if area>0}
            if areas:contacts.append({'uuid':rec['uuid'],'kind':rec['kind'],'key':rec.get('key'),'overlap_mm2':areas,'removed_in_current_scope':rec['uuid'] in cuts})
        out['old_U15_GND_stitch_contacts']={'uuid':oldvia[0]['uuid'],'actual_copper_contacts':contacts,'plane_fill_contacts_pending_fresh_native_review':True,'barrel_retained':True}
        # Prove a physical departure outside actual bonded copper before graph use.
        io=g.entry(g.one_pad('U15.5'))[1]['F.Cu'];x0,y0,x1,y1=io.bounds;center=g.one_pad('U15.5')['xy']
        exits=[('west',[x0-.1,center[1]]),('north',[center[0],y0-.1]),('south',[center[0],y1+.1]),('east',[x1+.1,center[1]])]
        alias,strict=view('PORT_C_RX_EXT','downstream',work);trials=[];out['actual_IO5_prefix_trials']=trials
        for direction,xy in exits:
            points=[center,C._xy(xy)];q=g.track('PORT_C_RX_EXT','F.Cu',points,'IO4-joint-RX-down-prefix',.127)
            physical=g.check_track('PORT_C_RX_EXT','F.Cu',points,width=.127,objects=work)
            branch=g.check_track(alias,'F.Cu',points,width=.127,objects=strict)
            outside=q[1]['F.Cu'].difference(io);opposite=[(o,c['F.Cu'].difference(io)) for o,c,m,d in strict if o['net']=='PORT_C_RX_EXT::upstream' and 'F.Cu' in c]
            gaps=[{'uuid':o['uuid'],'outside_pad_gap_mm':outside.distance(c)} for o,c in opposite if not c.is_empty]
            rolepass=all(v['outside_pad_gap_mm']>=.127+g.s.ERROR for v in gaps)
            section=C._section(g,{'kind':'track','name':q[0]['uuid'],'net':'PORT_C_RX_EXT','layer':'F.Cu','points':points,'width':.127},work)
            entrypass=any(v['point']==center and v['passed'] for v in section)
            row={'direction':direction,'points':points,'physical_checks_passed':C._passed(physical),'strict_role_view_passed':C._passed(branch),'outside_actual_IO5_branch_gap_passed':rolepass,'outside_branch_gaps':gaps,'actual_pad_entry_passed':entrypass,'actual_pad_entry_witnesses':section,'physical_nearest':physical[:6],'branch_nearest':branch[:6],'minimum_nominal_surplus_mm':min(z['extra_clearance_mm'] for z in physical+branch)}
            row['passed']=row['physical_checks_passed'] and row['strict_role_view_passed'] and rolepass and entrypass;trials.append(row)
        good=[z for z in trials if z['passed']]
        if not good:raise C.CFailure('No finite cardinal outside-IO5 prefix in the full coordinated scope; exact physical/role collisions retained')
        selected=max(good,key=lambda z:z['minimum_nominal_surplus_mm']);recipe={'kind':'track','name':'IO4-joint-RX-down-prefix','net':'PORT_C_RX_EXT','logical_net':'PORT_C_RX_EXT','role':'downstream','layer':'F.Cu','points':selected['points'],'width':.127};out['routes'].append(recipe)
        q=g.track(recipe['net'],recipe['layer'],recipe['points'],recipe['name'],recipe['width']);work.append((dict(q[0],role='downstream'),*q[1:]))
        out['actual_IO5_selected_prefix']=selected;down=dict(down,a=recipe['points'][-1]);jobs=[down if j['name']=='RX_down' else j for j in jobs]
        p,_=C._plan(g,view,down,work,end);out['full_80_cut_RX_down_from_proved_prefix']=p;stage('full_coordinated_scope_actual_IO5_prefix_and_target_query')
        if not p['connected']:raise C.CFailure('Full80-cut candidate has a finite actual IO5 departure but remains disconnected from R34.1; no support barrel selected')
        up=next(j for j in jobs if j['name']=='RX_up');p,_=C._plan(g,view,up,work,end);out['RX_up_after_full_HOLD_scope_release']=p;stage('RX_up_after_declared_local_support_release')
        if not p['connected']:raise C.CFailure('Complete HOLD transition release still lacks actual IO5/header reach; no barrel selected')
        # Ground return source is the retained .25-mm segment's actual terminal.
        gj={'name':'U15_GND_return','net':'GND','role':None,'width':.25,'a':[24.5,17.83],'b':None,'start_layers':['F.Cu'],'end_layers':['F.Cu'],'layers':['F.Cu']}
        with C._width_state(g,.25):free,obs,vobs=g.rt.domain('GND','F.Cu',objects=work)
        comp=g.rt.component(free,gj['a']);legal=g.s.OUTLINE.buffer(-.479-g.s.ERROR-.0001).difference(g.rt.expanded(vobs))
        eligible=comp.intersection(legal) if comp is not None else Point().buffer(0)
        local=eligible.intersection(box(21.5,17.5,24.5,20.5));parts=g.rt.parts(local)
        out['U15_ground_barrel_domain']={'unrestricted_area_mm2':eligible.area,'unrestricted_bounds':None if eligible.is_empty else list(eligible.bounds),'unrestricted_wkb_hex':eligible.wkb_hex,'local_strategy_window_mm':[21.5,17.5,24.5,20.5],'window_is_candidate_strategy_not_user_keepout':True,'local_area_mm2':local.area,'local_wkb_hex':local.wkb_hex}
        if not parts:raise C.CFailure('No source-connected legal U15 barrel in the bounded southwest return strategy; unrestricted domain retained')
        seed=Point(24,18.25);part=min(parts,key=lambda x:x.distance(seed));pt=seed if part.covers(seed) else polylabel(part,tolerance=.00001);xy=C._xy([pt.x,pt.y]);gj['b']=xy
        C._add_via(g,view,gj,work,xy,'IO4-joint-U15-GND-via',out['vias'],out['checks']);out['U15_ground_barrel_domain']['chosen_xy']=xy
        # Reserve every selected signal barrel before any new support track.
        def job(name,net,ak,b,endlayers):
            a=g.one_pad(ak);return {'name':name,'net':net,'role':None,'width':.127,'a':a['xy'],'b':b,'start_layers':list(a['copper']),'end_layers':endlayers,'layers':list(C.ORDINARY)}
        hold=job('HOLD_complete_transition','FLASH_HOLD_N','R6.2',[35.9343,25.077034],['In2.Cu'])
        allocation=[down,up,hold,next(j for j in jobs if j['name']=='TX_MCU'),next(j for j in jobs if j['name']=='TX_down')]
        for j in allocation:
            p,_=C._plan(g,view,j,work,end);record={'job':j,'plan':p};out['plans'].append(record);save()
            if not p['connected']:raise C.CFailure('Joint selected-barrel allocation disconnects '+j['name'])
            for i,v in enumerate(p['new_vias']):C._add_via(g,view,j,work,v['xy'],'IO4-joint-'+j['name']+'-via-'+str(i),out['vias'],out['checks'])
        stage('all_GND_HOLD_RX_and_TX_barrels_reserved_together_before_new_tracks')
        out['reserved_signal_barrels_are_conditional_until_actual_source_paths_constructed']=True
        C._add_track(g,view,gj,work,'F.Cu',gj['a'],gj['b'],'IO4-joint-U15-GND-return',out['routes'],out['checks'],end)
        groups=C._physical_groups(g,work,'GND');out['actual_U15_GND_contact']=any('U15.3' in q['keys'] and 'IO4-joint-U15-GND-via' in q['ids'] for q in groups)
        if not out['actual_U15_GND_contact']:raise C.CFailure('Actual U15.3-to-new-GND-barrel copper contact failed')
        out['ground_plane_review']={'old_barrel_retained':'97282ff5-d6b5-415f-a3c4-0390df70f0ea','saved_fill_only_contacts':[],'fresh_refill_plane_necks_ESD_reference_power_pending':True}
        q=next(q for q in work if q[0]['uuid']=='IO4-joint-U15-GND-via')
        for zone in g.N['zones']:
            if zone['rule'] or zone['net']!='GND':continue
            for layer,polys in zone['filled'].items():
                if layer not in ('In1.Cu','In4.Cu') or not polys:continue
                fill=g.s.geom(polys);assert fill.is_valid;area=fill.intersection(q[1][layer].difference(q[3])).area
                out['ground_plane_review']['saved_fill_only_contacts'].append({'zone_uuid':zone['uuid'],'layer':layer,'annular_overlap_mm2':area})
        out['U15_ground_return_comparison']={'old_full_trace_length_mm':2.573993726854674,'new_full_trace_length_mm':math.dist([25.0825,17.6],[24.5,17.83])+sum(math.dist(a,b) for r in out['routes'] if r['net']=='GND' for a,b in zip(r['points'],r['points'][1:])),'width_mm':.25,'AC_equivalence_established':False}
        # Complete the entire HOLD donor, including its long In2 obligation.
        p=next(r['plan'] for r in out['plans'] if r['job']['name']==hold['name'])
        for i,leg in enumerate(p['legs']):C._add_track(g,view,hold,work,leg['layer'],leg['start'],leg['end'],'IO4-joint-HOLD-leg-'+str(i),out['routes'],out['checks'],end)
        hj=job('HOLD_actual_pads','FLASH_HOLD_N','R6.2',g.one_pad('U3.7')['xy'],list(g.one_pad('U3.7')['copper']))
        out['HOLD_actual_terminal_connection']=C._already_connected(g,view,hj,work)
        if not out['HOLD_actual_terminal_connection']:raise C.CFailure('HOLD donor does not restore actual R6.2-to-U3.7')
        stage('complete_U15_ground_and_HOLD_routes_present')
        out['C_support_access']={};C._all_C_plans(g,view,jobs,work,end,record=out['C_support_access']);save()
        if not out['C_support_access']['passed']:raise C.CFailure('Actual complete support routes consume a remaining C target')
        out['peer_access']={'passed':False,'checks':[]};graphs={}
        for net,ak,bk in PEERS:
            C._deadline(end);a,b=g.one_pad(ak),g.one_pad(bk);j=job(net,net,ak,b['xy'],list(b['copper']))
            if C._already_connected(g,view,j,work):r={'net':net,'start_key':ak,'end_key':bk,'connected':True,'actual_held_copper_connected':True}
            else:
                if net not in graphs:
                    with C._width_state(g,.127):graphs[net]=g.gg.build(net,work)
                pp=g.gg.connect(graphs[net],a['xy'],b['xy'],tuple(a['copper']),tuple(b['copper']));r={'net':net,'start_key':ak,'end_key':bk,'connected':pp['connected'],'plan':pp}
            out['peer_access']['checks'].append(r);save()
        out['peer_access']['passed']=all(r['connected'] for r in out['peer_access']['checks']);out['complete']=out['peer_access']['passed']
        out['terminal_reason']='Joint support copper and all C/peer target access pass; full C/trunk/donor construction remains pending' if out['complete'] else 'Joint support copper consumes a required shared peer target';save()
    except TimeoutError:pass
    except Exception as e:out['terminal_reason']=str(e);out['exception_type']=type(e).__name__;save()
    finally:
        signal.alarm(0);print(json.dumps({'complete':out['complete'],'terminal_reason':out.get('terminal_reason'),'seconds':time.monotonic()-start,'receipt_sha256':adapter.digest(output)},indent=2),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--contract',type=Path,required=True);main(p.parse_args().contract)
