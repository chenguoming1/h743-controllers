"""Exact source support groups and finite native R2/SW1/GND entries."""
import copy,hashlib,json,math,sys,time
from pathlib import Path
H=Path(__file__).resolve().parent;R=H.parents[1];S=R/'candidate56';D=H/'candidate01';START=time.monotonic()
sys.path[:0]=[str(R/'dsm40-audits'),str(R/'dsm41-audits'),str(R.parent/'integrated-routing')]
from shapely.geometry import Point
from audit_dsm40_entries_return import pad_entry,groups,geom
from audit_dsm41_entries_return import via_entry
read=lambda f:json.loads(f.read_text());sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
write=lambda name,value:(D/name).write_text(json.dumps(value,indent=2)+'\n')
a=read(S/'owner-native.json');b=read(D/'f722-heli.native.json');p=read(D/'construction-provenance.json')
assert a['board_sha256']==sha(S/'f722-heli.kicad_pcb')==p['source_board_sha256']
assert b['board_sha256']==sha(D/'f722-heli.kicad_pcb')==p['board_sha256']
old={o['uuid']:o for o in a['objects']};new={o['uuid']:o for o in b['objects']}
removed={o['uuid'] for o in p['removed_source_records']};added=p['added_records'];changed={o['before']['uuid'] for o in p['changed_pad_records']}
assert removed=={'4d067743-6420-47f2-be08-af97a08594c3'} and len(added)==2 and len(changed)==2
assert old.keys()-new.keys()==removed and new.keys()-old.keys()=={o['uuid'] for o in added}
physical=lambda o:{k:v for k,v in o.items() if k!='net_code'}
assert all(physical(o)==physical(new[u]) for u,o in old.items() if u not in removed|changed)
assert all(old[u]['ref']=='R2' and old[u]['key']==new[u]['key'] and old[u]['net']==new[u]['net'] for u in changed)
pads=[o for o in new.values() if o['kind']=='pad'];vias=[o for o in new.values() if o['kind']=='via']
entries=[];annular=[];endpoints=[]
for t in added:
    assert t['kind']=='track';layer=next(iter(t['copper']))
    for end in ('start','end'):
        xy=t[end];hits=[]
        for pad in pads:
            if pad['net']!=t['net'] or layer not in pad['inside'] or not geom(pad['inside'][layer]).contains(Point(xy)):continue
            q=pad_entry(t,pad,layer,end);assert q['passed'],q;entries.append(q);hits.append(dict(pad=pad['key'],uuid=pad['uuid']))
        for via in vias:
            if via['net']==t['net'] and xy==via['xy']:
                q=via_entry(t,via,layer,b);assert q['passed'],q;annular.append(q);hits.append(dict(via=via['uuid']))
        assert hits,(t['uuid'],end,xy)
        endpoints.append(dict(track=t['uuid'],net=t['net'],endpoint=end,xy=xy,connections=hits))
assert len(entries)==3 and len(annular)==1 and len(endpoints)==4
support={}
for net in read(S/'power-audit.json')['nets']:
    before,after=groups(a,net),groups(b,net)
    assert before==after and len(after)==1,(net,before,after)
    support[net]=dict(groups=after,before_groups=len(before),after_groups=len(after),complete=True,source_groups_exactly_preserved=True)
before,after=groups(a,'BOOT0'),groups(b,'BOOT0')
assert len(before)==3 and len(after)==2,(before,after)
assert any(set(q['pads'])=={'R2.1','SW1.2'} for q in after)
assert any(q['pads']==['U1.60'] for q in after)
untouched_nets=sorted({o['net'] for o in old.values()}-{'BOOT0','GND'})
for net in untouched_nets:
    assert {u:physical(o) for u,o in old.items() if o['net']==net}=={u:physical(o) for u,o in new.items() if o['net']==net}
retained=['39a56392-875d-4879-813e-fb2d9fe74901','d94712e6-c55c-5d2f-a271-f17e1825ac82','c43c9592-f448-4136-aa2b-0a57c4b1f68f']
assert all(physical(old[u])==physical(new[u]) for u in retained)
boot=next(t for t in added if t['net']=='BOOT0');ground=next(t for t in added if t['net']=='GND')
bad=copy.deepcopy(b);bad['objects']=[o for o in bad['objects'] if o['uuid']!=boot['uuid']]
controls=[dict(name='remove_new_BOOT_leaf',rejected=len(groups(bad,'BOOT0'))==3)]
badtrack=copy.deepcopy(boot);badtrack['width']=2;pad=next(o for o in pads if o['key']=='R2.1')
controls.append(dict(name='oversized_R2_entry',rejected=not pad_entry(badtrack,pad,'F.Cu','start')['passed']))
assert all(q['rejected'] for q in controls)
binding=dict(board_sha256=b['board_sha256'],source_board_sha256=a['board_sha256'],native_sha256=sha(D/'f722-heli.native.json'),source_native_sha256=sha(S/'owner-native.json'))
audit=dict(schema='f722-R2-SW1-native-entry-support56/v1',passed=True,**binding,new_tracks=2,new_vias=0,new_track_endpoints_checked=4,
           strict_pad_entries=entries,finite_actual_annular_entries=annular,endpoint_inventory=endpoints,nets=support,
           signal_groups={'BOOT0':dict(before=before,after=after,complete=False,R2_SW1_branch_complete=True,U1_60_MCU_link_still_open=True)},
           unchanged_net_objects_exact=untouched_nets,retained_shared_C31_and_switch_ground_records=[new[u] for u in retained],
           negative_controls=controls,seconds=time.monotonic()-START,numerical_power_qualified=False,signal_quality_qualified=False,reference_AC_qualified=False)
write('entry-support-audit.json',audit)
write('endpoint-audit.json',dict(schema='f722-native-endpoint-audit-binding/v1',passed=True,**binding,audit='entry-support-audit.json',audit_sha256=sha(D/'entry-support-audit.json'),new_track_endpoints_checked=4,strict_pad_entries_all_pass=True,new_vias=0,negative_controls=controls))
write('power-audit.json',dict(schema='f722-native-support-audit/v1',passed=True,**binding,audit='entry-support-audit.json',audit_sha256=sha(D/'entry-support-audit.json'),nets=support,ground_native_pad_groups_exactly_preserved=True,numerical_power_qualified=False,method='All28native support groups recomputed; only the exclusive R2 ground leaf is reconstructed at original .25mm width to a retained actual ground via. Original shared C31 ground via and B lead preserved exactly.'))
write('native-length-ledger.json',dict(schema='f722-R2-native-length-ledger56/v1',**binding,
          actual_terminal_paths=[dict(net='BOOT0',from_pad='R2.1',to_pad='SW1.2',trace_centerline_mm=math.dist(boot['start'],boot['end']),new_vias=0),
                                dict(net='GND',from_pad='R2.2',to_via='c43c9592-f448-4136-aa2b-0a57c4b1f68f',trace_centerline_mm=math.dist(ground['start'],ground['end']),width_mm=.25,new_vias=0)],electrical_qualification=False))
print('TERMINAL',b['board_sha256'],'4finite endpoints,28support groups,BOOT3to2groups',audit['seconds'],flush=True)
