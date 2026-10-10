"""Seal the native R2/SW1 branch closure, keeping the MCU BOOT gap explicit."""
import datetime,hashlib,json,shutil
from pathlib import Path
H=Path(__file__).resolve().parent;R=H.parents[1];S=R/'candidate56';D=H/'candidate01'
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
write=lambda name,d:(D/name).write_text(json.dumps(d,indent=2)+'\n')
h=sha(D/'f722-heli.kicad_pcb');sh=sha(S/'f722-heli.kicad_pcb')
assert sh=='9d9f2f39c2b200f2c928dd3123f098797eb86ba56cb943d7f6e3fe89bf264a7e'
s=read(D/'owner-summary.json');assert s['board_sha256']==h
assert s['drc']==s['drc-all']==dict(unconnected=11,errors=0,warnings=0),s
for k in ['process','mechanical','parity','firmware']:assert s[k]['passed'] and s[k]['board_sha256']==h
assert s['critical']['connected_nets']==16 and not s['critical']['faults'] and not s['critical']['missing_ground_returns']
assert not read(D/'owner-drc-parity.json')['schematic_parity']
assert not any(x.get('violations') for x in read(D/'owner-erc.json').get('sheets',[]))
for f in ['entry-support-audit.json','power-audit.json','endpoint-audit.json','native-coordinated-integration.json','stock-spi-binding.json']:
    q=read(D/f);assert q['passed'] and q['board_sha256']==h
p=read(D/'construction-provenance.json');a=read(D/'entry-support-audit.json')
assert len(p['removed_source_records'])==1 and len(p['added_records'])==2
assert len(p['changed_pad_records'])==2 and len(p['changed_footprint_records'])==1
assert a['new_track_endpoints_checked']==4 and len(a['nets'])==28
assert a['signal_groups']['BOOT0']['R2_SW1_branch_complete'] and a['signal_groups']['BOOT0']['U1_60_MCU_link_still_open']
c=read(D/'protection-actual-io.json');b=read(S/'protection-actual-io.json')
passed=lambda x:{r['id'] for r in x['checks'] if r['complete_clamp_first_path_passes']}
assert c['passed']==b['passed']==20 and c['total']==22 and passed(c)==passed(b)
ref=read(D/'reference-comparison56.json');assert ref['critical_object_geometry_identical']
project=read(D/'project-input-preservation.json')
assert all(sha(D/x['path'])==x['sha256']==sha(S/x['path']) for x in project['files'])
write('coordinated-change-receipt.json',dict(schema='f722-R2-SW1-complete-branch-native56/v1',source_board_sha256=sh,board_sha256=h,
    changed_nets=['BOOT0','GND'],removed_source_objects=p['removed_source_records'],added_objects=p['added_records'],
    changed_pad_records=p['changed_pad_records'],footprint_transforms='declared-footprint-transforms.json',
    all_other155_full_footprints_exact=True,all_source_track_via_arc_objects_retained_except_R2_exclusive_ground_leaf=True,
    retained_C31_ground_objects_exact=a['retained_shared_C31_and_switch_ground_records'],all28_support_groups_preserved=True,
    complete_R2_SW1_branch=True,BOOT_U1_60_link_still_open=True,raw_constructor_pending_flags_superseded_by_native_gates=True,
    numerical_power_VCAP_qualified=False,BOOT_startup_qualified=False,reference_AC_qualified=False,owner_adoption_claimed=False))
limits=['Geometric prototype checkpoint; independent owner adoption pending.',
    'R2.1 and both actual SW1.2 contacts form one complete copper branch. U1.60 remains disconnected, so BOOT operation is not qualified.',
    'Only the exclusive R2 F ground leaf is replaced; the original shared C31 ground via and complete C31 B lead remain exact.',
    'R2 keeps its 2.2k/1% identity. The new direct BOOT trace is 1.270127946 mm with zero new vias; its .25mm ground return is 1.063672882 mm.',
    'The seven-via BOOT/ADC exploration is not imported. All original ADC/MID/RED/SERVO and other source routes remain exact.',
    'Numerical power/VCAP, complete BOOT startup/noise, all-signal saved-reference and measured transient behavior remain conditional. Raw reference deltas are retained without thresholds.']
write('checkpoint-limits.json',dict(board_sha256=h,limits=limits,raw_critical_reference_deltas=ref['net_numeric_deltas_after_minus_before'],native_length_ledger='native-length-ledger.json'))
ledger=read(D/'native-length-ledger.json')
(D/'README.md').write_text('''# R2-to-SW1 native checkpoint from accepted56

The saved board has 11 opens, zero native errors and zero warnings. R2 moves from F (16, 7.7), 0 degrees to F (40.2, 6.2), 270 degrees, preserving its 2.2k/1% value and actual pad/net identities. Its complete SW1.2 pull-down branch is connected. Actual MCU U1.60 remains open. Remaining gaps are PORT_C 5, BOOT 1, RED 1 and flash 4.

The transaction adds two tracks and no vias, removes only R2's exclusive 0.25 mm F ground leaf, and changes only R2's two pads and full footprint pose. A short 0.25 mm return terminates on the retained actual GND via at (39.15, 6.54). The original R2/C31 shared ground via and C31 B lead remain exact, as do all original ADC/MID/RED/SERVO and other source routes.

Native DRC, strict schematic parity, ERC, firmware, mechanical and process checks pass. All 16 critical groups, four finite new endpoints, 28 supply/ground groups and all 20 previously passing actual I/O protection cases are preserved. The actual BOOT0 pad partition changes from three groups to two. Read the source-bound entry/support audit and coordinated integration receipt.

This is a geometric checkpoint for owner review. Complete MCU BOOT routing, startup/noise qualification, numerical power/VCAP and all-signal reference review remain pending. No seven-via exploratory BOOT/ADC geometry is imported.
''')
for name in ['construct_R2_standalone56.py','audit_R2_standalone56.py','extra_R2_standalone56.py','validate_checkpoint56.py','seal_R2_standalone56.py']:
    shutil.copy2(H/name,D/(Path(name).stem+'.used.py'))
ties=read(D/'reference-snapshot/critical-reference.json')['GND_ties']
hand=dict(schema='f722-native-route-handoff/v1',status='sealed_native_11_open_R2_SW1_branch_pending_owner_review',
    sealed_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),board_sha256=h,integration_source_sha256=sh,native_sha256=sha(D/'f722-heli.native.json'),
    drc=dict(unconnected=11,errors=0,warnings=0,strict_schematic_parity=0,ERC_violations=0),remaining_gap_accounting=dict(PORT_C=5,BOOT=1,RED=1,flash=4),
    pose_reference=str((D/'poses-native.json').relative_to(R)),declared_footprint_transforms='declared-footprint-transforms.json',
    coordinated=True,allowed_changed_nets=['BOOT0','GND'],all_other155_full_footprints_exact=True,removed_source_objects=1,added_native_objects=2,new_tracks=2,new_vias=0,
    finite_new_endpoints=4,support_groups_preserved=28,completed_branch=['SW1.2','R2.1'],incomplete_BOOT_terminal='U1.60',
    actual_IO_cuts_passed=20,actual_IO_contracts=22,actual_IO_passes_exactly_preserved=True,critical_object_geometry_identical=True,
    raw_critical_reference_deltas=ref['net_numeric_deltas_after_minus_before'],all_signal_reference_owner_review_pending=True,
    ground_ties_to_both_saved_planes=len(ties['accepted']),rejected_ground_ties=len(ties['rejected']),native_length_ledger='native-length-ledger.json',
    limits_file='checkpoint-limits.json',signal_quality_qualified=False,BOOT_startup_qualified=False,reference_AC_qualified=False,protection_transient_qualified=False,
    numerical_power_VCAP_qualified=False,owner_adoption_pending=True)
hand['files']={str(f.relative_to(D)):sha(f) for f in sorted(D.rglob('*')) if f.is_file() and f.name!='route-handoff.json'}
write('route-handoff.json',hand);assert all(sha(D/k)==v for k,v in hand['files'].items())
print(json.dumps(dict(board_sha256=h,handoff_sha256=sha(D/'route-handoff.json'),files=len(hand['files']),status=hand['status'])),flush=True)
