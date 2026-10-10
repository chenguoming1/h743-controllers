"""Strict ephemeral protected-branch views; native physical records stay exact."""
import hashlib
import json
from pathlib import Path

SCOPE_SHA256='b70b00911dbcade6e97470d6a5cb593a122b20af1dcc4672e00711c107f61534'
NATIVE_SHA256='53ddf869c36da4a026880c6b3346dd1ddb304aaabaa948b20f1e66fc3db62505'
TRANSACTION_SHA256='b7ca08e59b4316c8a88c0ff9d3c0fe3cffac4d0f0ad2b407028cd1ef3050f497'
PROTECTED={'PORT_C_RX_EXT','PORT_C_TX_EXT'}
BONDED={'PORT_C_RX_EXT':'U15.1','PORT_C_TX_EXT':'U15.2'}

def load_branch_view(g, scope_file=None):
    path=Path(scope_file) if scope_file else Path(__file__).with_name('native7-C-compact-scope-receipt-v4.json')
    assert hashlib.sha256(path.read_bytes()).hexdigest()==SCOPE_SHA256,'C scope receipt differs'
    scope=json.loads(path.read_text());binding=g.binding()
    assert binding['native_sha256']==NATIVE_SHA256==scope['native_binding']['sha256']
    assert binding['transaction_sha256']==TRANSACTION_SHA256==scope['transaction_binding']['sha256']
    assert binding['board_sha256']==scope['native_binding']['board_sha256']
    metadata=scope['protected_branch_role_metadata']
    native=g.by
    assert {uid for uid,o in native.items() if o['net'] in PROTECTED}==set(metadata),'Protected native role inventory is incomplete'
    for key,p in scope['actual_endpoints'].items():
        actual=g.one_pad(key)
        assert all(actual[k]==p[k] for k in p),'Actual endpoint identity differs: '+key

    def view(physical_net, role, objects, *, additional_roles=None):
        assert physical_net in PROTECTED and role in ('upstream','downstream')
        extra={} if additional_roles is None else additional_roles
        alias=physical_net+'::'+role;result=[]
        for obj,copper,mask,drill in objects:
            net=obj['net']
            assert '::' not in net,'A branch view cannot be used as the physical object set'
            if net not in PROTECTED:
                result.append((obj,copper,mask,drill));continue
            uid=obj['uuid'];key=obj.get('key')
            if uid in native:
                assert obj==native[uid],'Native physical record was mutated: '+uid
                meta=metadata[uid];assert meta['physical_net']==net
                obj_role=meta['role']
                if uid in extra:
                    explicit=extra[uid]['role'] if isinstance(extra[uid],dict) else extra[uid]
                    assert explicit==obj_role,'Cannot override a native protected role'
            else:
                meta=extra.get(uid,obj.get('role'))
                assert meta is not None,'Explicit protected role required for new copper: '+uid
                if isinstance(meta,dict):
                    assert meta.get('net',meta.get('physical_net',net))==net
                    obj_role=meta['role']
                else:obj_role=meta
                assert obj_role in ('upstream','downstream'),'Invalid new protected role'
            if key in ('U15.1','U15.2'):
                assert uid in native and key==BONDED[net]
                classified=alias if net==physical_net else net+'::bonded'
            else:
                assert obj_role in ('upstream','downstream'),'Unclassified protected object'
                classified=net+'::'+obj_role
            changed=dict(obj,net=classified)
            result.append((changed,copper,mask,drill))
        return alias,result

    return view
