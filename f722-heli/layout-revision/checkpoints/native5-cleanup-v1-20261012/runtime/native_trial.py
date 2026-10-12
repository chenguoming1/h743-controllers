"""Technical native geometry checks extracted in original definition order."""
from decimal import Decimal
import copy, hashlib, json
from pathlib import Path
import paired_source as paired
import pose_guard, cleanup_guard
import representation_equivalence as representation
HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
SOURCE=ROOT/'inputs/source-hardware'


def require(value,message):
    if not value:raise ValueError(message)


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda:f.read(1048576),b''):h.update(chunk)
    return h.hexdigest()


def digest(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def read(path):return paired.read(path)


def write(path,value):
    with Path(path).open('x') as f:json.dump(value,f,separators=(',',':'),sort_keys=True,allow_nan=False);f.write('\n')


def nm(v):
    x=Decimal(str(v))*1000000
    require(x.is_finite() and x==x.to_integral_value(),'Non-integral native coordinate')
    return int(x)


def transform(point,old,new):
    angle=(int(new[2])-int(old[2]))%360
    require(angle in (0,90,180,270),'Only cardinal same-side poses')
    x,y=[nm(point[i])-nm(old[i]) for i in (0,1)]
    x,y={0:(x,y),90:(y,-x),180:(-x,-y),270:(-y,x)}[angle]
    return [(x+nm(new[0]))/1000000,(y+nm(new[1]))/1000000]


def ring_id(ring):
    row=tuple(tuple(nm(x) for x in p) for p in ring)
    if row and row[0]==row[-1]:row=row[:-1]
    return min(row[i:]+row[:i] for i in range(len(row))) if row else ()


def polygons_id(rows):
    return sorted((ring_id(r['outer']),tuple(sorted(ring_id(h) for h in r['holes']))) for r in rows)


def transformed_polygons(rows,old,new):
    return [{'outer':[transform(p,old,new) for p in r['outer']],
             'holes':[[transform(p,old,new) for p in h] for h in r['holes']]} for r in rows]


def verify_pad(source,actual,old,new):
    require(set(source)==set(actual),'Native pad field inventory changed')
    skip={'xy','angle','copper','inside','mask','drill'}
    require({k:v for k,v in source.items() if k not in skip}=={k:v for k,v in actual.items() if k not in skip},'Pad UUID/net/size/layers/attributes changed')
    require(actual['xy']==transform(source['xy'],old,new),'Pad position differs from exact transform')
    require((actual['angle']-source['angle']-(new[2]-old[2]))%360==0,'Pad angle changed incorrectly')
    for kind in ['copper','inside']:
        require(set(source[kind])==set(actual[kind]),'Pad contour layers changed')
        for layer,rows in source[kind].items():
            require(polygons_id(transformed_polygons(rows,old,new))==polygons_id(actual[kind][layer]),'Native pad contour differs: '+kind)
    require(set(source['mask'])==set(actual['mask']),'Pad mask layer changed')
    for layer,row in source['mask'].items():
        require({k:v for k,v in row.items() if k!='polygons'}=={k:v for k,v in actual['mask'][layer].items() if k!='polygons'},'Mask expansion changed')
        require(polygons_id(transformed_polygons(row['polygons'],old,new))==polygons_id(actual['mask'][layer]['polygons']),'Mask contour changed')
    require(source['drill'] is None and actual['drill'] is None,'Moving drilled footprints is outside this contract')


def verify_footprint(source,actual,old,new):
    require(set(source)==set(actual),'Footprint fields changed')
    require({k:v for k,v in source.items() if k not in ['xy','angle','graphics']}=={k:v for k,v in actual.items() if k not in ['xy','angle','graphics']},'Footprint identity/package/side changed')
    require(actual['xy']==new[:2] and (actual['angle']-new[2])%360==0,'Footprint target pose differs')
    s={x['uuid']:x for x in source['graphics']};a={x['uuid']:x for x in actual['graphics']}
    require(set(s)==set(a),'Footprint internal graphic/courtyard UUIDs changed')
    for uid,g in s.items():
        q=a[uid];coords={'start','end','mid','center','polygons'}
        require({k:v for k,v in g.items() if k not in coords}=={k:v for k,v in q.items() if k not in coords},'Graphic attributes changed')
        if g['shape']=='Polygon':
            require(polygons_id(transformed_polygons(g['polygons'],old,new))==polygons_id(q['polygons']),'Graphic polygon changed')
            require(g['start']==q['start'] and g['end']==q['end'],'Native polygon sentinel changed')
        else:
            for key in ['start','end','mid','center']:
                if key in g:require(q[key]==transform(g[key],old,new),'Graphic coordinate changed')


def verify_added(expected,actual):
    require(actual['uuid']==expected['uuid'] and actual['kind']==expected['kind'] and actual['net']==expected['net'],'Added identity/net/kind differs')
    if expected['kind']=='track':
        require(actual['start']==expected['start'] and actual['end']==expected['end'] and actual['width']==expected['width'],'Added track coordinates/width differ')
        require(list(actual['copper'])==[expected['layer']] and actual['width_by_layer']=={expected['layer']:expected['width']} and actual['drill'] is None,'Added track structure differs')
    else:
        require(actual['xy']==expected['xy'] and actual['start']==expected['xy'] and actual['end']==expected['xy'],'Added via coordinates differ')
        require(actual['width']==expected['diameter'] and actual['drill']['width']==expected['drill'] and actual['drill']['start']==expected['xy'] and actual['drill']['end']==expected['xy'],'Added via diameter/drill differs')
        require(actual['via_type']==4 and actual['top_layer']=='F.Cu' and actual['bottom_layer']=='B.Cu' and actual['plated'] is True,'Only ordinary through vias permitted')
        require(actual['barrel_layers']==expected['layers'] and actual['width_by_layer']=={l:expected['diameter'] for l in expected['layers']},'Via layer/ring geometry differs')
        require(actual['tented']==expected['tented'] and actual['mask']=={},'Via tenting differs')


def verify_delta(before,after,poses,r):
    old={x['uuid']:x for x in before['objects']};new={x['uuid']:x for x in after['objects']}
    cuts=r['remove_source_records'];adds=r['proposed_add_tracks']+r['proposed_add_vias']
    require(set(old)-set(new)==set(cuts),'Exact 40 whole-record cut set differs')
    require(set(new)-set(old)=={x['uuid'] for x in adds},'Exact 20 added UUID set differs')
    for uid,row in cuts.items():require(digest(old[uid])==row['native_record_sha256'],'Cut source record changed: '+uid)
    for row in adds:verify_added(row,new[row['uuid']])
    oldfp={x['ref']:x for x in before['footprints']};newfp={x['ref']:x for x in after['footprints']}
    require(set(oldfp)==set(newfp),'Footprint inventory changed')
    for ref,fp in oldfp.items():
        if ref in poses:
            require(digest(fp)==r['pose_recipe'][ref]['source']['full_native_footprint_record_sha256'],'Source pose/footprint changed')
            verify_footprint(fp,newfp[ref],[*fp['xy'],fp['angle'],fp['side']],poses[ref])
        else:require(fp==newfp[ref],'Unmoved footprint changed: '+ref)
    moved=[];fixed=[]
    for uid,row in old.items():
        if uid in cuts:continue
        if row.get('ref') in poses:
            fp=oldfp[row['ref']];verify_pad(row,new[uid],[*fp['xy'],fp['angle'],fp['side']],poses[row['ref']]);moved.append(uid)
        else:require(row==new[uid],'Fixed object changed: '+uid);fixed.append(uid)
    for key in ['copper_layers','copper_layer_ids','edge_cuts','outline_with_npth','board_thickness_mm']:
        require(before[key]==after[key],'Board structure changed: '+key)
    bz={z['uuid']:z for z in before['zones']};az={z['uuid']:z for z in after['zones']}
    require(set(bz)==set(az),'Zone inventory changed')
    meta=lambda z:{k:v for k,v in z.items() if k not in ['filled','fill_representation']}
    for uid in bz:require(meta(bz[uid])==meta(az[uid]),'Zone outline/rule/net changed')
    for row in r['pad_obligations']:
        actual=new[row['uuid']]
        require(actual['net']==row['net'] and actual['xy']==row['proposed_xy'] and actual['key']==row['key'],'Required pad/aperture identity or endpoint differs')
    require({x['uuid'] for x in r['pad_obligations']}=={x['uuid'] for x in before['objects'] if x.get('ref') in poses},'Moved pad obligations incomplete')
    return {'moved_pad_ids':sorted(moved),'fixed_object_records_unchanged':len(fixed),'fixed_record_hashes':{u:digest(new[u]) for u in fixed},'removed_records':{u:old[u] for u in cuts},'added_records':{x['uuid']:new[x['uuid']] for x in adds},'track_via_removals':len(cuts),'track_via_additions':len(adds),'zone_fill_changes_only':True,'all_moved_pad_obligations_retained':True}


_base_transform=transform


_base_verify_pad=verify_pad


_base_verify_footprint=verify_footprint


def transform(point,old,new):
    if old[3]==new[3]:return _base_transform(point,old,new)
    local=_base_transform(point,old,[0,0,0,old[3]])
    return _base_transform([local[0],-local[1]],[0,0,0,new[3]],new)


def swap(layer):
    return 'B.'+layer[2:] if layer.startswith('F.') else 'F.'+layer[2:] if layer.startswith('B.') else layer


def ring_id(ring):
    row=tuple(tuple(nm(x) for x in p) for p in ring)
    if row and row[0]==row[-1]:row=row[:-1]
    return min([v[i:]+v[:i] for v in (row,row[::-1]) for i in range(len(v))]) if row else ()


def verify_pad(source,actual,old,new):
    if old[3]==new[3]:return _base_verify_pad(source,actual,old,new)
    mapped=copy.deepcopy(source)
    # Geometry still uses the explicit reflected physical transform above.
    for kind in ['copper','inside','mask','shape_by_layer']:
        mapped[kind]={swap(k):v for k,v in mapped[kind].items()}
    for kind in ['all_layers','barrel_layers']:mapped[kind]=[swap(k) for k in mapped[kind]]
    # Layer serialization order is immaterial, membership is exact.
    require(set(mapped['all_layers'])==set(actual['all_layers']),'Flipped pad layers differ')
    mapped['all_layers']=actual['all_layers']
    mapped['angle']=2*old[2]-source['angle']
    _base_verify_pad(mapped,actual,old,new)


_verify_pad_exact=verify_pad


_active_representation_context=None


_active_representation_rows=None


def make_representation_context(before,after,raw_proof,before_settings,after_settings,candidate_board):
    return representation.context(before,after,raw_proof,before_settings,after_settings,candidate_board)


def verify_pad(source,actual,old,new,representation_context=None):
    try:return _verify_pad_exact(source,actual,old,new)
    except ValueError as exc:
        if source.get('ref')!='U15' or str(exc) not in ['Mask contour changed','Native pad contour differs: copper']:raise
        ctx=representation_context if representation_context is not None else _active_representation_context
        proof=representation.verify_pad(_verify_pad_exact,source,actual,old,new,ctx,transformed_polygons)
        if _active_representation_rows is not None:_active_representation_rows.append(proof)
        return proof


def verify_footprint(source,actual,old,new):
    if old[3]==new[3]:return _base_verify_footprint(source,actual,old,new)
    mapped=copy.deepcopy(source);mapped['side']=new[3]
    for g in mapped['graphics']:g['layer']=swap(g['layer'])
    _base_verify_footprint(mapped,actual,old,new)


_verify_delta_before_net_code_normalization=verify_delta


def verify_delta(before,after,poses,r,representation_context=None):
    global _active_representation_context,_active_representation_rows
    def bijection(data):
        names={};codes={};counts={}
        for row in data['objects']+data['zones']:
            name=row['net'];code=row['net_code']
            require(name not in names or names[name]==code,'One net name has multiple codes')
            require(code not in codes or codes[code]==name,'One net code has multiple names')
            names[name]=code;codes[code]=name
            kind=row.get('kind','zone');counts[kind]=counts.get(kind,0)+1
        return names,counts
    source,source_counts=bijection(before);current,current_counts=bijection(after)
    require(set(source)==set(current),'Net-name inventory changed')
    normalized=copy.deepcopy(after)
    for row in normalized['objects']+normalized['zones']:row['net_code']=source[row['net']]
    require(_active_representation_context is None,'Nested representation comparison forbidden')
    _active_representation_context=representation_context;_active_representation_rows=[]
    try:
        proof=_verify_delta_before_net_code_normalization(before,normalized,poses,r)
        proof['U15_representation_equivalence']={'context':representation_context,'pad_checks':_active_representation_rows,'actual_candidate_geometry_unchanged':True}
    finally:
        _active_representation_context=None;_active_representation_rows=None
    proof['fixed_objects_identical_after_bijective_net_code_normalization']=proof.pop('fixed_object_records_unchanged')
    proof['source_code_normalized_fixed_record_hashes']=proof.pop('fixed_record_hashes')
    actual={x['uuid']:x for x in after['objects']}
    proof['added_records']={uid:actual[uid] for uid in proof['added_records']}
    proof['net_code_bijection']={'all_names_identical':True,'both_maps_bijective':True,'source_counts':source_counts,'candidate_counts':current_counts,'rows':[{'net':k,'source_net_code':source[k],'candidate_net_code':current[k]} for k in sorted(source)]}
    proof['comparison_only_net_code_normalization']=True
    proof['mirror_pose']=pose_guard.verify_planned_U15(before,after)
    proof['TX_unused_arm_cleanup']=cleanup_guard.contract_binding()
    proof.update(paired.verify_pad_nets(before,after))
    return proof

