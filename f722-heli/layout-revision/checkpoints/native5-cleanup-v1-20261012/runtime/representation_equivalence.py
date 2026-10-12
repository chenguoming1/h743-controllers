"""Exact-identity U15 polygon representation guard. Never changes board geometry.

Symmetric capsule coverage proves a continuous boundary-distance upper bound,
not merely vertex samples. One simple contour without holes is the only allowed
topology. Input positions are integral KiCad nanometres; calculations use local
coordinate differences, with a conservative numerical reserve inside the 23 nm cap.
"""
import copy,math
from decimal import Decimal
from pathlib import Path
import paired_source as p
import structural_base as raw
import pose_guard
HERE=Path(__file__).resolve().parent
THRESHOLD_NM=23
WORK_RADIUS_NM=22.999  # 0.001nm numerical reserve; the declared bound remains23nm.
GROUND={'51c6de31-9fac-4287-b433-3b9eaac67b1d','ef45fa73-d7c1-46b1-b97b-5758fa665b65'}
SCHEMA='f722-U15-native-representation-equivalence/v1'
POLICY_SHA='f8b304ec6559f7c7fe05528175eb560bf5935d61cf67eb21208711f78f4a9407'
def policy_binding():
    path=HERE/'representation-policy.json';p.require(p.sha(path)==POLICY_SHA,'Representation policy changed');return POLICY_SHA
def contract_binding():return {'schema':SCHEMA,'policy_sha256':policy_binding(),'maximum_contour_distance_nm':23,'scope':'U15_only_exact_reflection','actual_candidate_geometry_unchanged':True}
def pad_binding(row):return p.digest({k:v for k,v in row.items() if k!='net_code'})

def nm(v):
    x=Decimal(str(v))*1000000
    p.require(x.is_finite() and x==x.to_integral_value(),'Contour is not on the native1nm grid')
    return int(x)
def cross(a,b):return a[0]*b[1]-a[1]*b[0]
def sub(a,b):return(a[0]-b[0],a[1]-b[1])
def dot(a,b):return a[0]*b[0]+a[1]*b[1]
def edges(ring):return list(zip(ring,ring[1:]+ring[:1]))
def orient(a,b,c):return cross(sub(b,a),sub(c,a))
def onsegment(a,b,c):return orient(a,b,c)==0 and min(a[0],b[0])<=c[0]<=max(a[0],b[0]) and min(a[1],b[1])<=c[1]<=max(a[1],b[1])
def intersects(a,b,c,d):
    q=[orient(a,b,c),orient(a,b,d),orient(c,d,a),orient(c,d,b)]
    return (q[0]*q[1]<0 and q[2]*q[3]<0) or any([q[0]==0 and onsegment(a,b,c),q[1]==0 and onsegment(a,b,d),q[2]==0 and onsegment(c,d,a),q[3]==0 and onsegment(c,d,b)])

def ring(polygons):
    p.require(len(polygons)==1 and polygons[0]['holes']==[],'U15 fallback requires exact single-component zero-hole topology')
    values=[(nm(x),nm(y)) for x,y in polygons[0]['outer']]
    if values and values[0]==values[-1]:values=values[:-1]
    p.require(3<=len(values)<=2048 and len(set(values))==len(values),'Contour repeats vertices or exceeds bound')
    segments=edges(values)
    for i,b in enumerate(values):
        a,c=values[i-1],values[(i+1)%len(values)]
        p.require(orient(a,b,c)!=0 or dot(sub(b,a),sub(c,b))>0,'Contour doubles back at adjacent edge')
    p.require(sum(cross(a,b) for a,b in segments)!=0,'Zero-area contour')
    for i,(a,b) in enumerate(segments):
        for j in range(i+1,len(segments)):
            if j==i+1 or (i==0 and j==len(segments)-1):continue
            p.require(not intersects(a,b,*segments[j]),'Contour self-intersection/topology changed')
    return values

def clipped_linear(lo,hi,base,slope,minimum,maximum):
    if slope==0:return (lo,hi) if minimum<=base<=maximum else None
    a,b=(minimum-base)/slope,(maximum-base)/slope
    if a>b:a,b=b,a
    lo=max(lo,a);hi=min(hi,b)
    return (lo,hi) if lo<=hi else None

def capsule_intervals(a,b,c,d,radius):
    """Parameter intervals of AB inside the closed radius-capsule of CD."""
    direction=sub(b,a);target=sub(d,c);squared=dot(direction,direction);length2=dot(target,target)
    p.require(squared>0 and length2>0,'Zero contour edge')
    offset=sub(a,c);out=[]
    current=clipped_linear(0.,1.,dot(offset,target),dot(direction,target),0,length2)
    if current:
        current=clipped_linear(*current,cross(target,offset),cross(target,direction),-radius*math.sqrt(length2),radius*math.sqrt(length2))
        if current:out.append(current)
    for center in [c,d]:
        delta=sub(a,center);projection=-dot(direction,delta)/squared
        perpendicular2=cross(direction,delta)**2/squared
        margin=radius*radius-perpendicular2
        if margin>=0:
            half=math.sqrt(margin/squared);lo=max(0.,projection-half);hi=min(1.,projection+half)
            if lo<=hi:out.append((lo,hi))
    return out

def boundary_covered(left,right):
    target=edges(right)
    for a,b in edges(left):
        intervals=[]
        for c,d in target:
            # Exact integer bounding boxes discard distant target capsules.
            if max(min(a[0],b[0]),min(c[0],d[0]))>min(max(a[0],b[0]),max(c[0],d[0]))+THRESHOLD_NM:continue
            if max(min(a[1],b[1]),min(c[1],d[1]))>min(max(a[1],b[1]),max(c[1],d[1]))+THRESHOLD_NM:continue
            intervals.extend(capsule_intervals(a,b,c,d,WORK_RADIUS_NM))
        reach=0.
        for lo,hi in sorted(intervals):
            if lo>reach:break
            reach=max(reach,hi)
            if reach>=1.:break
        p.require(reach>=1.,'Continuous contour distance exceeds23nm bound')

def verify_contour(expected,actual):
    left,right=ring(expected),ring(actual)
    p.require(len(left)==len(right),'Native U15 ring vertex-count topology changed')
    boundary_covered(left,right);boundary_covered(right,left)
    return {'maximum_continuous_boundary_distance_nm':THRESHOLD_NM,'proof':'symmetric_segment_capsule_coverage','components':1,'holes':0,'simple_contours':True,'expected_vertices':len(left),'actual_vertices':len(right),'expected_sha256':p.digest(expected),'actual_sha256':p.digest(actual)}

def context(before,after,raw_proof,before_settings,after_settings,candidate_board):
    policy_binding()
    p.require(before['board_sha256']==p.sha(p.SOURCE/'f722-heli.kicad_pcb'),'Source board/native binding differs')
    p.require(before['maximum_polygon_error_mm']==after['maximum_polygon_error_mm']==.00001,'Both exports must use ERROR_IU10')
    p.require(before['native_build']==after['native_build']=='10.0.6+dfsg-1','Native implementation changed')
    p.require(before_settings==after_settings and len(before_settings)==558,'Exact all-pad inverse settings proof required')
    p.require(raw_proof['raw_source_check']=='PASSED' and raw_proof['all_pad_aperture_settings_and_local_shapes_preserved'] is True,'Exact inverse native AST proof required')
    p.require(raw_proof['forward_pose_checked']['U15']==[27.721926,21.185113,0,'B.Cu'],'Wrong exact reflection')
    p.require(after['board_sha256']==p.sha(candidate_board),'Candidate board/native binding differs')
    inverse=Path(raw_proof['inverse_pose_check_copy'])
    p.require(inverse.parent==Path(candidate_board).parent.parent and inverse.is_file(),'Wrong inverse-check artifact')
    source_ast=raw.parse(p.SOURCE/'f722-heli.kicad_pcb');inverse_ast=raw.parse(inverse)
    u15=lambda tree:next(x for x in raw.children(tree,'footprint') if raw.ref(x)=='U15')
    # A full inverse record equality includes every analytic custom primitive,
    # mask/paste setting, pad UUID/net/number and local text/graphics setting.
    p.require(raw.unordered(u15(source_ast))==raw.unordered(u15(inverse_ast)),'U15 analytic primitives or settings changed in inverse AST')
    return {'schema':SCHEMA,'policy_sha256':POLICY_SHA,'pad_record_bindings':{row['uuid']:{'source':pad_binding(row),'candidate':pad_binding(next(a for a in after['objects'] if a['uuid']==row['uuid']))} for row in before['objects'] if row.get('ref')=='U15'},'source_board_sha256':before['board_sha256'],'candidate_board_sha256':after['board_sha256'],'inverse_board_sha256':p.sha(inverse),'source_U15_raw_AST_sha256':p.digest(raw.canonical(u15(source_ast))),'inverse_U15_raw_AST_sha256':p.digest(raw.canonical(u15(inverse_ast))),'all_558_inverse_pad_settings_sha256':p.digest(before_settings),'raw_proof_sha256':p.digest(raw_proof),'source_error_nm':10,'candidate_error_nm':10,'integer_grid_nm':1,'maximum_contour_distance_nm':23,'analytic_primitives_exact':True,'settings_exact':True,'inverse_AST_exact':True,'actual_candidate_geometry_unchanged':True}

def verify_pad(exact,source,actual,old,new,ctx,transform_polygons):
    p.require(ctx and ctx['schema']==SCHEMA and ctx['analytic_primitives_exact'] is True and ctx['settings_exact'] is True and ctx['inverse_AST_exact'] is True,'U15 representation fallback requires exact paired inverse evidence')
    p.require(ctx['source_error_nm']==ctx['candidate_error_nm']==10 and ctx['maximum_contour_distance_nm']==23,'Wrong representation error bound')
    p.require(ctx['policy_sha256']==policy_binding(),'Representation policy binding differs')
    p.require(ctx['pad_record_bindings'][source['uuid']]=={'source':pad_binding(source),'candidate':pad_binding(actual)},'Representation context is bound to different pad records')
    plan=pose_guard.check_sources();allowed={r['uuid'] for r in plan['pad_map']}
    p.require(source['ref']==actual['ref']=='U15' and source['uuid']==actual['uuid'] and source['uuid'] in allowed,'Representation fallback only permits ten sealed U15 pads')
    p.require(old==[25.5,17.6,0,'F.Cu'] and new==[27.721926,21.185113,0,'B.Cu'],'Representation fallback only permits exact reflection')
    corrected=copy.deepcopy(actual);rows=[]
    targets=[('mask','F.Mask','B.Mask')]
    if source['uuid'] in GROUND:targets.append(('copper','F.Cu','B.Cu'))
    for kind,oldlayer,newlayer in targets:
        expected=transform_polygons(source[kind][oldlayer]['polygons'] if kind=='mask' else source[kind][oldlayer],old,new)
        observed=actual[kind][newlayer]['polygons'] if kind=='mask' else actual[kind][newlayer]
        check=verify_contour(expected,observed)
        rows.append({'uuid':source['uuid'],'key':source['key'],'kind':kind,'source_layer':oldlayer,'candidate_layer':newlayer,**check})
        if kind=='mask':corrected[kind][newlayer]['polygons']=expected
        else:corrected[kind][newlayer]=expected
    # All identity/settings and every inside contour still pass original exact
    # guards. Only this disposable comparison copy receives equivalent contours.
    exact(source,corrected,old,new)
    return {'pad_uuid':source['uuid'],'key':source['key'],'context_sha256':p.digest(ctx),'contours':rows,'inside_contours_exact':True,'all_other_fields_exact':True,'actual_candidate_geometry_unchanged':True}
