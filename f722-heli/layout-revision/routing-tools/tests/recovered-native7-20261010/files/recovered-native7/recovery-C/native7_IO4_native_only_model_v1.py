"""Native7-only equivalent RX channel model; no common routing proposal is loaded."""
import copy,importlib.util,json,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent.parent
sys.path.insert(0,str(ROOT/'ordinary-routing/tests/native13-access'))
import native7_recovered_context_v3 as adapter
RX='PORT_C_RX_EXT';TX='PORT_C_TX_EXT'
PREFIX=('7e53c88f-9a87-5ba3-9c32-455d9649a9f5','0704cc1e-3f63-51e7-b36b-26e4c9a347e5','84864ccd-ac78-5d94-bbdd-daebc37d1ceb','6e64820c-b464-5142-a228-ebb74be4b044')
GND=('a08299df-6002-52fd-8f9e-27b83956263e','c577b646-60c8-5101-b044-be71979ecce8','97282ff5-d6b5-415f-a3c4-0390df70f0ea')
HOLD=('00d3d778-abd5-4fa9-8b8f-9877e7b83803','f30237b0-7063-45c1-947a-2b6d75ac6f88','8f22baac-a8ff-4219-8c6b-8d5695979bc7','bcf4a808-4cd6-5541-8d5e-f9545c5dc1a2')

def build():
    assert adapter.digest(HERE/'native7-C-compact-scope-receipt-v4.json')=='b70b00911dbcade6e97470d6a5cb593a122b20af1dcc4672e00711c107f61534'
    spec=importlib.util.spec_from_file_location('C_native_only_IO4',HERE/'complete_native7_C_v3.py');C=importlib.util.module_from_spec(spec);spec.loader.exec_module(C)
    base=adapter.load();scope=json.loads((HERE/'native7-C-compact-scope-receipt-v4.json').read_text());metadata=copy.deepcopy(scope['protected_branch_role_metadata'])
    old={k:base.one_pad(k) for k in ('U15.1','U15.10','U15.5','U15.6')};new={}
    assignments={'U15.1':('unconnected-(U15-IO1-Pad1)',old['U15.5']['net_code']),'U15.10':('unconnected-(U15-NC-Pad10)',old['U15.6']['net_code']),'U15.5':(RX,old['U15.1']['net_code']),'U15.6':(RX,old['U15.1']['net_code'])}
    for key,(net,code) in assignments.items():
        o=copy.deepcopy(old[key]);o.update(net=net,net_code=code);new[o['uuid']]=o
        assert {k:v for k,v in old[key].items() if k not in ('net','net_code')}=={k:v for k,v in o.items() if k not in ('net','net_code')}
    metadata.pop(old['U15.1']['uuid']);metadata.pop(old['U15.10']['uuid']);metadata[old['U15.5']['uuid']]={'role':'bonded','key':'U15.5'};metadata[old['U15.6']['uuid']]={'role':'upstream','key':'U15.6'}
    cuts=set(PREFIX+GND+HOLD);assert len(cuts)==11
    work=[base.entry(new.get(o['uuid'],o)) for o in base.N['objects'] if o['uuid'] not in cuts]
    g=copy.copy(base);g.by={q[0]['uuid']:q[0] for q in work};pads={q[0]['key']:q[0] for q in work if q[0].get('key')};g.one_pad=lambda key:pads[key];g.pads={k:[v] for k,v in pads.items()};g.N=dict(base.N,objects=[q[0] for q in work]);expected=dict(g.by)
    io={RX:base.entry(new[old['U15.5']['uuid']])[1],TX:base.entry(base.one_pad('U15.2'))[1]}
    def view(net,role,objects,*,additional_roles=None):
        assert net in (RX,TX) and role in ('upstream','downstream');alias=net+'::'+role;result=[];extra={} if additional_roles is None else additional_roles
        for source,copper,mask,drill in objects:
            physical=source['net'];assert '::' not in physical
            if physical not in (RX,TX):result.append((source,copper,mask,drill));continue
            uid=source['uuid'];key=source.get('key')
            if uid in expected:assert source==expected[uid]
            objrole=extra.get(uid,metadata.get(uid,{}).get('role',source.get('role')))
            if isinstance(objrole,dict):objrole=objrole['role']
            if key in ('U15.5','U15.2'):
                assert key==({RX:'U15.5',TX:'U15.2'}[physical]);classified=alias if physical==net else physical+'::bonded'
            else:
                assert objrole in ('upstream','downstream'),(uid,objrole);classified=physical+'::'+objrole
            cu=copper
            if physical==net and source['kind']=='track' and classified!=alias:cu={l:shape.difference(io[net][l]) if l in io[net] else shape for l,shape in copper.items()}
            result.append((dict(source,net=classified),cu,mask,drill))
        return alias,result
    inventory={'source':g.binding(),'pad_net_delta':[{'before':old[k],'after':new[old[k]['uuid']]} for k in assignments],'removed_native_records':[base.by[u] for u in sorted(cuts)],'removed_native_ids':sorted(cuts),'native_cut_count':11,'no_common_proposal_added_or_cut':True,'all_ordinary_IMU_C12_R3_TX_copper_preserved':True,'U15_ground_first_segment_held':'ac132cca-ea4d-53a6-8376-a7cab37beb2b','complete_U15_GND_and_HOLD_restoration_required':True,'original_five_ordinary_opens_not_claimed_closed':True,'source_native_bytes_unchanged':True,'fresh_GND_plane_ESD_reference_and_power_pending':True}
    return g,base,C,view,work,inventory
