"""Exact geometric reflection checks with a portable pose contract binding."""
from decimal import Decimal
from pathlib import Path
import paired_source as p
HERE=Path(__file__).resolve().parent
POSE=HERE/'mirror-pose-contract.json'
POSE_SHA='a972e8dc0fc59a461cfd1ac9c61b2ca27c4d897933ddb5da0bf7e188072116b8'
def check_sources():
    p.require(p.sha(POSE)==POSE_SHA,'Pose contract changed')
    return p.read(POSE)


def point(value):
    x,y=[Decimal(str(v)) for v in value]
    return [float(Decimal('27.721926')+(x-Decimal('25.5'))),float(Decimal('21.185113')-(y-Decimal('17.6')))]


def verify_planned_U15(before,after):
    plan=check_sources()
    source={r['uuid']:r for r in before['objects'] if r.get('ref')=='U15'}
    actual={r['uuid']:r for r in after['objects'] if r.get('ref')=='U15'}
    wanted={r['uuid']:r for r in plan['pad_map']}
    p.require(len(source)==len(actual)==len(wanted)==10 and set(source)==set(actual)==set(wanted),'All ten exact U15 pad UUIDs required')
    rows=[]
    for uid,row in wanted.items():
        old,new=source[uid],actual[uid]
        p.require(old['key']==new['key']==row['key'] and old['net']==new['net']==row['net'],'Planned pad identity/net differs')
        p.require(old['xy']==row['from'] and new['xy']==row['to']==point(old['xy']),'Planned mirrored pad center differs')
        p.require((new['angle']+old['angle'])%360==0,'Native pad angle does not follow official TOP_BOTTOM flip')
        p.require(set(old['copper'])=={'F.Cu'} and set(new['copper'])=={'B.Cu'},'U15 copper side differs')
        rows.append({'uuid':uid,'key':row['key'],'net':row['net'],'source_xy':old['xy'],'candidate_xy':new['xy']})
    fp=next(f for f in after['footprints'] if f['ref']=='U15')
    p.require(fp['uuid']==plan['source_U15_footprint_uuid'] and [*fp['xy'],fp['angle']%360,fp['side']]==plan['native_pose'],'Native U15 pose does not match exact physical reflection')
    return {'pose_contract_sha256':POSE_SHA,'historical_planning_label':'B180','native_U15_pose':plan['native_pose'],'explicit_geometry_preserved':True,'all_ten_pad_centers_and_nets_exact':True,'all_pad_copper_inside_mask_and_body_graphics_require_native_delta':True,'pad_centers':rows,'NC_internal_continuity_assumed':False}

