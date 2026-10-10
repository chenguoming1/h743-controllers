"""Exact-source candidate42 finite entries and copper-only support audit."""
import copy,hashlib,json,math,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent
sys.path[:0]=[str(ROOT/'dsm40-audits'),str(ROOT/'dsm41-audits')]
from audit_dsm40_entries_return import geom,pad_entry,join_entry,groups,section_at,linear_parts,translate_record
from audit_dsm41_entries_return import via_entry
from shapely.geometry import Point,LineString,Polygon
from shapely.affinity import translate
S=ROOT/'candidate41';D=ROOT/'candidate42'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
read=lambda p:json.loads(Path(p).read_text())
write=lambda p,v:Path(p).write_text(json.dumps(v,indent=2)+'\n')
before,after=read(S/'f722-heli.native.json'),read(D/'f722-heli.native.json')
assert sha(S/'f722-heli.kicad_pcb')==before['board_sha256']=='539d9547eb8c4d5984481293ae10cee34355ee838dff11ab43b00cca270ceae2'
assert sha(D/'f722-heli.kicad_pcb')==after['board_sha256']=='eac130eb32389c82b2bae274e2c50b73675c79d442cfc8441956369b4cdf3304'
old={o['uuid']:o for o in before['objects']};new={o['uuid']:o for o in after['objects']}
provenance=read(D/'construction-provenance.json')
removed=set(old)-set(new);added=set(new)-set(old);changed={u for u in old.keys()&new.keys()if old[u]!=new[u]}
assert removed=={o['uuid']for o in provenance['removed_source_records']} and len(removed)==7
assert added=={o['uuid']for o in provenance['added_candidate_records']} and len(added)==41
assert {old[u]['key']for u in changed}=={'R7.1','R7.2','R8.1','R8.2','C69.1','C69.2'}
for u in changed:
    ref=old[u]['key'].split('.')[0]
    if ref in {'R8','C69'}:
        dx,dy={'R8':(.02,.4),'C69':(.01,-.002)}[ref]
        assert translate_record(old[u],dx,dy)==new[u]
assert all(o==new[o['uuid']]for o in provenance['added_candidate_records'])
assert all(o==old[o['uuid']]for o in provenance['removed_source_records'])
assert all(before[k]==after[k]for k in ['edge_cuts','outline_with_npth','copper_layers'])
tracks=[o for o in after['objects']if o['kind']=='track'];pads=[o for o in after['objects']if o['kind']=='pad'];vias=[o for o in after['objects']if o['kind']=='via']
entries=[];joins=[];annular=[];interior=[];classification=[];seen=set()
def finite_track_interior(t,target,layer,endpoint):
    actual=geom(target['copper'][layer]).buffer(-after['maximum_polygon_error_mm'])
    a=t[endpoint];b=t['end'if endpoint=='start'else'start'];length=math.dist(a,b);half=t['width']/2
    normal=[-(b[1]-a[1])/length,(b[0]-a[0])/length]
    section=section_at(a,normal,half);guarded=actual.buffer(-.000001)
    allowed=translate(guarded,normal[0]*half,normal[1]*half).intersection(translate(guarded,-normal[0]*half,-normal[1]*half))
    intervals=LineString([a,b]).intersection(allowed);w=[]
    for interval in linear_parts(intervals):
        c,d=[list(interval.interpolate(f,normalized=True).coords[0])for f in [.25,.75]]
        sa,sb=[list(section_at(q,normal,half).coords)for q in [c,d]];rect=Polygon([sa[0],sa[1],sb[1],sb[0]])
        missing=rect.difference(actual).area
        if missing<=1e-12:w.append({'length_mm':math.dist(c,d),'polygon_mm':list(rect.exterior.coords),'outside_mm2':missing,'boundary_reserve_mm':rect.distance(actual.boundary)})
    return {'passed':actual.contains(Point(a))and section.difference(actual).length<=1e-8 and intervals.length>0 and bool(w),'target_kind':'retained_native_track_interior','track_uuid':t['uuid'],'target_uuid':target['uuid'],'endpoint':endpoint,'layer':layer,'net':t['net'],'width_mm':t['width'],'section_missing_mm':section.difference(actual).length,'transverse_entry_length_mm':intervals.length,'finite_full_width_strips':w,'copper_contraction_mm':after['maximum_polygon_error_mm']}
for t in tracks:
    if t['uuid']not in added:continue
    expected=.2 if t['net']=='+3V3_CORE'else .127
    assert t['net']in{'+3V3_CORE','BARO_SCL','BARO_SDA'} and t['width']==expected
    for layer in t['copper']:
        for end in ['start','end']:
            xy=t[end];hp=[p for p in pads if p['net']==t['net']and layer in p['inside']and geom(p['inside'][layer]).contains(Point(xy))]
            ht=[o for o in tracks if o['uuid']!=t['uuid']and o['net']==t['net']and layer in o['copper']and xy in [o['start'],o['end']]]
            hv=[v for v in vias if v['net']==t['net']and layer in v['copper']and v['xy']==xy]
            hi=[]
            if not(hp or ht or hv):hi=[o for o in tracks if o['uuid']in old and o==old[o['uuid']]and o['net']==t['net']and layer in o['copper']and geom(o['copper'][layer]).contains(Point(xy))]
            classification.append({'track':t['uuid'],'net':t['net'],'layer':layer,'endpoint':end,'xy':xy,'pads':[p['key']for p in hp],'exact_track_joins':[o['uuid']for o in ht],'vias':[v['uuid']for v in hv],'retained_track_interiors':[o['uuid']for o in hi],'resolved':bool(hp or ht or hv or hi)})
            for p in hp:
                key=(t['uuid'],p['uuid'],layer,end)
                if key not in seen:seen.add(key);entries.append(pad_entry(t,p,layer,end))
            for o in ht:
                key=tuple(sorted([t['uuid'],o['uuid']]))+(layer,)
                if key not in seen:seen.add(key);joins.append(join_entry(t,o,layer,expected))
            for v in hv:
                key=(t['uuid'],v['uuid'],layer)
                if key not in seen:seen.add(key);annular.append(via_entry(t,v,layer,after))
            for o in hi:interior.append(finite_track_interior(t,o,layer,end))
moved=[]
for p in pads:
    if p['uuid']not in changed:continue
    matches=[]
    for t in tracks:
        if t['net']!=p['net']:continue
        for layer in t['copper'].keys()&p['inside'].keys():
            for end in ['start','end']:
                if geom(p['inside'][layer]).contains(Point(t[end])):
                    matches.append({'track':t['uuid'],'layer':layer,'endpoint':end})
                    key=(t['uuid'],p['uuid'],layer,end)
                    if key not in seen:seen.add(key);e=pad_entry(t,p,layer,end);e['retained_source_track_exact']=t['uuid']in old and t==old[t['uuid']];entries.append(e)
    moved.append({'pad':p['key'],'entries':matches,'has_entry':bool(matches)})
support={}
for net in read(S/'power-audit.json')['nets']:
    a,b=groups(before,net),groups(after,net);support[net]={'passed':a==b and len(b)==1,'pad_group_count':len(b),'source_groups_exactly_preserved':a==b,'groups':b}
topology={net:groups(after,net)for net in ['BARO_SCL','BARO_SDA','PORT_C_TX_EXT','DSM_RX_EXT','DSM_RX_MCU','RPM_LV','SBUS_HV']}
native_i2c_complete=topology['BARO_SCL'][0]['pads']==['R7.2','U1.61','U4.4']and len(topology['BARO_SCL'])==1 and topology['BARO_SDA'][0]['pads']==['R8.2','U1.62','U4.3']and len(topology['BARO_SDA'])==1
preserved_other_topology=all(topology[net]==groups(before,net)for net in topology if not net.startswith('BARO_'))
newvias=[o for o in vias if o['uuid']in added];assert len(newvias)==6
gaps=[]
for z in after['zones']:
    if z['rule']or z['net']!='GND':continue
    for layer,ps in z['filled'].items():
        for v in newvias:
            gap=geom(ps).distance(geom(v['copper'][layer]));gaps.append({'layer':layer,'via_uuid':v['uuid'],'gap_mm':gap,'passed':gap>=.127})
def r8_junction():
    pad=new['c006cb50-39d5-4045-93df-766836540643']
    continuation=new['11f37124-1a8f-44ef-abfe-1dc328d81df1']
    incoming=[new[u]for u in ['3f7340f2-99d8-4619-af8f-780e5c14549b','6bf881c2-734b-4dd2-80a8-8e412994c36f']]
    assert pad['key']=='R8.1'and pad['xy']==[23.52,24.51]
    assert continuation['start']==[23.5,24.325]and continuation['end']==[23.5,24.51]
    assert all(t['net']==pad['net']=='+3V3_CORE'and t['width']==.2 and list(t['copper'])==['B.Cu']for t in incoming+[continuation])
    assert all(t==old[t['uuid']]for t in incoming)
    error=after['maximum_polygon_error_mm'];pa=geom(pad['inside']['B.Cu'])
    actual=pa
    for t in incoming+[continuation]:actual=actual.union(geom(t['copper']['B.Cu']).buffer(-error))
    continuation_entries=[pad_entry(continuation,pad,'B.Cu',ep)for ep in ['start','end']]
    joint_proofs=[join_entry(t,continuation,'B.Cu',.2)for t in incoming]
    results=[];controls=[]
    starts=[[23.4,24.325],[23.6,24.32139634946]]
    for t,start in zip(incoming,starts):
        end=pad['xy'];length=math.dist(start,end);normal=[-(end[1]-start[1])/length,(end[0]-start[0])/length]
        aa,bb=[section_at(q,normal,.1)for q in [start,end]];strip=Polygon([aa.coords[0],aa.coords[1],bb.coords[1],bb.coords[0]])
        ia=geom(t['copper']['B.Cu']).buffer(-error)
        missing=strip.difference(actual).area;sm=aa.difference(ia).length;em=bb.difference(pa).length;reserve=strip.distance(actual.boundary)
        direct=pad_entry(t,pad,'B.Cu','end'if t['end']==[23.5,24.325]else'start');assert not direct['passed']
        passed=missing<=1e-12 and sm<=1e-8 and em<=1e-8 and reserve>error
        results.append({'passed':passed,'incoming_track_uuid':t['uuid'],'retained_source_exact':True,'direct_pad_entry_remains_false':True,'direct_entry':direct,'width_mm':.2,'length_mm':length,'centerline_mm':[start,end],'polygon_mm':list(strip.exterior.coords),'area_outside_actual_copper_mm2':missing,'minimum_boundary_reserve_mm':reserve,'start_section_missing_from_retained_track_mm':sm,'end_section_missing_from_actual_pad_mm':em,'track_polygon_inward_reserve_mm':error})
        middle=[(start[i]+end[i])/2 for i in range(2)]
        notched=actual.difference(section_at(middle,normal,.3).buffer(.003,cap_style=2))
        controls.append({'name':'R8_internal_corridor_cut_'+t['uuid'],'rejected':strip.difference(notched).area>1e-12 and aa.difference(notched).length<=1e-8 and bb.difference(notched).length<=1e-8,'outside_notched_mm2':strip.difference(notched).area})
        narrow=LineString([t['start'],t['end']]).buffer(.075,cap_style=1)
        mutated=copy.deepcopy(t);mutated['width']=.15
        mutated['copper']['B.Cu']=[{'outer':list(narrow.exterior.coords),'holes':[]}]
        width_control=join_entry(mutated,continuation,'B.Cu',.2)
        controls.append({'name':'R8_narrow_retained_incoming_full_width_join_'+t['uuid'],'rejected':not width_control['passed'],'required_width_mm':.2,'mutated_width_mm':.15,'section_only_rejected':aa.difference(narrow).length>1e-8,'missing_start_section_mm':aa.difference(narrow).length,'full_native_width_join_guard':width_control,'explanation':'The angled starting section still fits this narrower strip; native width and the full-width exact junction guard reject it. Section-only refusal is explicitly false.'})
    return {'passed':all(r['passed']for r in results)and all(r['passed']for r in continuation_entries+joint_proofs),'classification':'two_exact_retained_track_junctions_with_finite_full_0p20_copper_corridors_into_actual_R8_pad','pad_uuid':pad['uuid'],'continuation_uuid':continuation['uuid'],'continuation_strict_entries':continuation_entries,'exact_full_width_joins':joint_proofs,'corridors':results,'scope':'Only these two retained endpoints at the exact common R8.1 junction; both failed direct transverse predicates remain false.'},controls
r8,controls=r8_junction()
failed_entries=[e for e in entries if not e['passed']]
expected_false={(r['incoming_track_uuid'],'R8.1')for r in r8['corridors']}
assert {(e['track_uuid'],e['pad'])for e in failed_entries}==expected_false and len(failed_entries)==2
# Existing primitive rejection controls are rerun on current native witnesses.
for entry in [e for e in entries if e['passed']][:2]:
    track=copy.deepcopy(new[entry['track_uuid']]);pad=new[entry['pad_uuid']]
    track['width']=2.0
    controls.append({'name':'oversize_entry_'+track['uuid'],'rejected':not pad_entry(track,pad,entry['layer'],entry['endpoint'])['passed']})
for row in annular[:2]:
    via=copy.deepcopy(new[row['via_uuid']]);via['drill']['outside']=copy.deepcopy(via['copper'][row['layer']])
    controls.append({'name':'drill_only_entry_'+row['track_uuid'],'rejected':not via_entry(new[row['track_uuid']],via,row['layer'],after)['passed']})
gates={'source_contract':True,'all_new_endpoints_resolved':all(x['resolved']for x in classification),'strict_pad_entries_or_two_explicit_R8_corridors':r8['passed']and all(e['passed']or(e['track_uuid'],e['pad'])in expected_false for e in entries),'track_junctions':all(x['passed']for x in joins),'retained_track_interior_entry':all(x['passed']for x in interior),'annular_entries':all(x['passed']for x in annular),'moved_pad_entries':all(x['has_entry']for x in moved),'all_28_support_groups_preserved':len(support)==28 and all(x['passed']for x in support.values()),'both_I2C_nets_complete':native_i2c_complete,'retained_signal_topologies':preserved_other_topology,'saved_GND_via_clearances':all(x['passed']for x in gaps),'negative_controls':all(x['rejected']for x in controls)}
report={'schema':'f722-I2C42-entry-support-audit/v1','passed':all(gates.values()),'gates':gates,'source_board_sha256':before['board_sha256'],'board_sha256':after['board_sha256'],'script_sha256':sha(__file__),'source_native_sha256':sha(S/'f722-heli.native.json'),'candidate_native_sha256':sha(D/'f722-heli.native.json'),'construction_sha256':sha(D/'construction-provenance.json'),'source_power_audit_sha256':sha(S/'power-audit.json'),'classification':classification,'strict_pad_entries':entries,'strict_pad_entries_all_pass':False,'direct_pad_entry_failures_preserved':failed_entries,'explicit_R8_retained_junction':r8,'negative_controls':controls,'full_width_track_joins':joins,'retained_track_interior_entries':interior,'finite_annular_entries':annular,'moved_pad_entry_inventory':moved,'nets':support,'signal_pad_groups':topology,'new_signal_via_saved_GND_gaps':gaps,'numerical_power_VCAP_applicable':False,'adoption_claimed':False,'limits':['Finite nominal copper geometry and copper-only topology. No loaded-power, VCAP, transient, tolerance, RC or device timing qualification.','The R7 side transformation must pass an explicit native owner proof.','Both I2C routes intentionally introduce new reference geometry; unchanged-reference assertions do not apply.']}
write(D/'i2c-entry-support-audit.json',report)
print(json.dumps({'passed':report['passed'],'gates':gates,'pad_entries':len(entries),'joins':len(joins),'annular':len(annular),'retained_interiors':len(interior),'failed_pad_entries':[x for x in entries if not x['passed']],'failed_annular':[x for x in annular if not x['passed']],'unresolved':[x for x in classification if not x['resolved']]}))
