"""Candidate-only equivalent U15 IO4 RX assignment at the exact native pose."""
import copy,importlib.util,json,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent.parent
sys.path.insert(0,str(ROOT/'ordinary-routing/tests/native13-access'))
import native7_recovered_context_v3 as adapter
from prepare_native7_coordinated_context_v3 import replay
RX='PORT_C_RX_EXT';TX='PORT_C_TX_EXT'
PAD_IDS={'U15.1':'76401567-1405-4a22-b70c-0a7f2502777e','U15.10':'85f6ae89-da40-4223-9e1c-51ee8cc2f22f','U15.5':'dddece5c-5254-4426-8e4c-1fb5f9e85655','U15.6':'af34758d-03d4-4898-8fb1-2be5765ea280'}
PREFIX_CUTS=('7e53c88f-9a87-5ba3-9c32-455d9649a9f5','0704cc1e-3f63-51e7-b36b-26e4c9a347e5','84864ccd-ac78-5d94-bbdd-daebc37d1ceb','6e64820c-b464-5142-a228-ebb74be4b044')

def build():
    spec=importlib.util.spec_from_file_location('C_IO4_bound',HERE/'complete_native7_C_v3.py');C=importlib.util.module_from_spec(spec);spec.loader.exec_module(C)
    base=adapter.load();proposal,scope,cuts,held,added,reservation,reserved=replay(base)
    _,scope,_=C._load(base,held+added+[reserved]);work=list(held+added)
    addback=[]
    for name in ('TX_down_complete_tail','TX_up_header_tail','private_VX_leaf'):addback.extend(scope['scopes'][name]['native_ids'])
    addback.extend(o['uuid'] for o in base.N['objects'] if o['uuid'].startswith(('8a55abc3','296bfec5')))
    assert len(addback)==26 and len(set(addback))==26
    for uid in addback:
        assert uid in cuts and all(q[0]['uuid']!=uid for q in work)
        work.append(base.entry(base.by[uid]))
    source_with_supports=list(work)
    original={key:base.one_pad(key) for key in PAD_IDS}
    assert all(original[key]['uuid']==uid for key,uid in PAD_IDS.items())
    assert original['U15.5']['xy']==[25.0825,18.6] and original['U15.6']['xy']==[25.9175,18.6]
    fp=next(f for f in base.N['footprints'] if f['ref']=='U15');assert fp['xy']==[25.5,17.6] and fp['angle']==0 and fp['side']=='F.Cu'
    assert original['U15.1']['net']==original['U15.10']['net']==RX
    assert all(original[k]['net'].startswith('unconnected-') for k in ('U15.5','U15.6'))
    changed={}
    # Net codes are candidate-local slots; paired native netlist must regenerate and verify them.
    assignments={'U15.1':('unconnected-(U15-IO1-Pad1)',original['U15.5']['net_code']),
                 'U15.10':('unconnected-(U15-NC-Pad10)',original['U15.6']['net_code']),
                 'U15.5':(RX,original['U15.1']['net_code']),'U15.6':(RX,original['U15.1']['net_code'])}
    for key,(net,code) in assignments.items():
        record=copy.deepcopy(original[key]);record['net']=net;record['net_code']=code
        assert {k:v for k,v in record.items() if k not in ('net','net_code')}=={k:v for k,v in original[key].items() if k not in ('net','net_code')}
        changed[record['uuid']]=record
    assert all(any(q[0]['uuid']==uid for q in work) for uid in PREFIX_CUTS)
    work=[base.entry(changed[q[0]['uuid']]) if q[0]['uuid'] in changed else q for q in work if q[0]['uuid'] not in PREFIX_CUTS]
    g=copy.copy(base);g.by={q[0]['uuid']:q[0] for q in work};pads={q[0]['key']:q[0] for q in work if q[0].get('key')};g.one_pad=lambda key:pads[key];g.pads={key:[p] for key,p in pads.items()}
    g.N=dict(base.N,objects=[q[0] for q in work])
    metadata=copy.deepcopy(scope['protected_branch_role_metadata'])
    metadata.pop(PAD_IDS['U15.1']);metadata.pop(PAD_IDS['U15.10'])
    metadata[PAD_IDS['U15.5']]={'physical_net':RX,'role':'bonded_only_active_channel_may_alias','key':'U15.5'}
    metadata[PAD_IDS['U15.6']]={'physical_net':RX,'role':'upstream','key':'U15.6'}
    expected={q[0]['uuid']:q[0] for q in work}
    def view(physical_net,role,objects,*,additional_roles=None):
        assert physical_net in (RX,TX) and role in ('upstream','downstream')
        alias=physical_net+'::'+role;result=[];extra={} if additional_roles is None else additional_roles
        for o,cu,mask,drill in objects:
            net=o['net'];assert '::' not in net
            if net not in (RX,TX):result.append((o,cu,mask,drill));continue
            uid=o['uuid'];key=o.get('key')
            if uid in expected:
                assert o==expected[uid],uid
                if uid in metadata:obj_role=metadata[uid]['role']
                else:obj_role=o.get('role')
            else:obj_role=extra.get(uid,o.get('role'))
            if isinstance(obj_role,dict):obj_role=obj_role['role']
            if key in ('U15.5','U15.2'):
                assert key==({RX:'U15.5',TX:'U15.2'}[net])
                classified=alias if net==physical_net else net+'::bonded'
            else:
                assert obj_role in ('upstream','downstream'),(uid,obj_role)
                classified=net+'::'+obj_role
            result.append((dict(o,net=classified),cu,mask,drill))
        return alias,result
    jobs=C._jobs(g)
    for job in jobs:
        if job['name']=='RX_up':job.update(a=pads['U15.6']['xy'])
        if job['name']=='RX_down':job.update(a=pads['U15.5']['xy'])
    inventory={'source':base.binding(),'U15_unchanged_footprint':fp,'pad_net_delta':[{'before':original[key],'after':changed[uid]} for key,uid in PAD_IDS.items()],
      'candidate_local_net_codes_require_paired_schematic_native_validation':True,'bonded_RX_key':'U15.5','upstream_RX_NC_key':'U15.6','no_internal_NC_connection_assumed':True,
      'common_original_cut_ids':sorted(cuts),'common_addback_records':[base.by[u] for u in addback],'additional_old_RX_prefix_removed_records':[base.by[u] for u in PREFIX_CUTS],
      'resulting_native_copper_cut_ids':sorted((set(cuts)-set(addback))|set(PREFIX_CUTS)),'retired_planning_only_reservation':reservation['name'],
      'TX_bonded_key_held':'U15.2','TX_NC_key_held':'U15.9','original_C12_R3_and_all_GND_VX_geometry_held':True,'RX_domain_jobs':jobs[:2]}
    return g,base,C,view,work,source_with_supports,inventory,jobs
