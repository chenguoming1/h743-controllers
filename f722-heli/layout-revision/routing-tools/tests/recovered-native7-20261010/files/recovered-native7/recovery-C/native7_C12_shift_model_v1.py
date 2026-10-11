"""Exact candidate-only C12 east translation and complete leaf inventory."""
import copy, importlib.util, sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parent.parent
sys.path.insert(0,str(ROOT/'ordinary-routing/tests/native13-access'))
import native7_recovered_context_v3 as adapter
from prepare_native7_coordinated_context_v3 import replay
CUTS=('97832e7d-4506-4ec6-bf89-d2db05e3cda8','fb8288a2-c699-4368-a7ab-e4e79f4d7fa4',
      'd7e5189c-e93c-4dd6-81a5-792b677fafb4','c8bef21f-ce0a-449d-b34b-a063ce5e7c32',
      '3d128062-54a3-4fd3-ab3d-818e4ec84e57','da1f25da-e0ad-4065-9e0c-44670c3de5fa')
GROUND_VIA='3a66a0d8-a4b0-4282-9936-fdae79b412fc'

def build():
    from shapely.geometry import LineString
    from shapely.ops import polygonize, unary_union
    spec=importlib.util.spec_from_file_location('C_C12_bound',HERE/'complete_native7_C_v3.py')
    C=importlib.util.module_from_spec(spec);spec.loader.exec_module(C)
    base=adapter.load();proposal,scope,cuts,held,added,reservation,reserved=replay(base)
    common,scope,view=C._load(base,held+added+[reserved])
    work=list(held+added)
    # Restore both actual original CS leaves, which were cuts in the common proposal.
    cs_ids=[o['uuid'] for o in base.N['objects'] if o['uuid'].startswith(('8a55abc3','296bfec5'))]
    assert len(cs_ids)==2
    for uid in cs_ids:
        assert uid in cuts and all(q[0]['uuid']!=uid for q in work)
        work.append(base.entry(base.by[uid]))
    before=list(work);oldfp=next(f for f in base.N['footprints'] if f['ref']=='C12')
    assert oldfp['xy']==[26.0625,12.0] and oldfp['angle']==-90 and oldfp['side']=='F.Cu'
    oldpads=[q for q in work if q[0].get('ref')=='C12'];assert len(oldpads)==2
    def xy(p):return [round(p[0]+.25,6),p[1]]
    def polys(items):return [dict(p,outer=[xy(v) for v in p['outer']],holes=[[xy(v) for v in h] for h in p.get('holes',[])]) for p in items]
    def table(tab):return {layer:(dict(item,polygons=polys(item['polygons'])) if isinstance(item,dict) else polys(item)) for layer,item in tab.items()}
    newpads=[]
    for q in oldpads:
        o=copy.deepcopy(q[0]);o['xy']=xy(o['xy'])
        for key in ('copper','inside','mask'):
            if key in o:o[key]=table(o[key])
        z=base.entry(o)
        assert all(p.is_valid and not p.is_empty for p in list(z[1].values())+list(z[2].values()))
        assert o['uuid']==q[0]['uuid'] and o['net']==q[0]['net']
        newpads.append(z)
    newfp=copy.deepcopy(oldfp);newfp['xy']=xy(newfp['xy'])
    for z in newfp['graphics']:
        assert z['shape']=='Line'
        z['start']=xy(z['start']);z['end']=xy(z['end'])
    replaced=set(CUTS)|{q[0]['uuid'] for q in oldpads}
    for uid in CUTS:assert any(q[0]['uuid']==uid for q in work)
    work=[q for q in work if q[0]['uuid'] not in replaced]+newpads
    g=copy.copy(base);g.by={q[0]['uuid']:q[0] for q in work};pads={q[0]['key']:q[0] for q in work if q[0].get('key')}
    g.one_pad=lambda key:pads[key];g.pads={k:[v] for k,v in pads.items()}
    g.N=dict(base.N,objects=[q[0] for q in work],footprints=[newfp if f['ref']=='C12' else f for f in base.N['footprints']])
    assert pads['C12.1']['xy']==[26.3125,11.52] and pads['C12.2']['xy']==[26.3125,12.48]
    contacts=[]
    for uid in CUTS:
        leaf=next(q for q in before if q[0]['uuid']==uid)
        touches=[]
        for o,cu,_,_ in before:
            if o['uuid'] in CUTS or o['net']!=leaf[0]['net']:continue
            areas={layer:leaf[1][layer].intersection(cu[layer]).area for layer in set(leaf[1])&set(cu)}
            if any(x>0 for x in areas.values()):touches.append({'uuid':o['uuid'],'key':o.get('key'),'layer_overlap_mm2':areas})
        contacts.append({'removed_record':leaf[0],'retained_contacts':touches})
    def poly(fp,layer):return unary_union(list(polygonize([LineString([r['start'],r['end']]) for r in fp['graphics'] if r['shape']=='Line' and r['layer']==layer])))
    court=poly(newfp,'F.Courtyard');body=poly(newfp,'F.Fab');mechanics=[]
    for fp in g.N['footprints']:
        if fp['ref']=='C12' or fp['side']!='F.Cu':continue
        c=poly(fp,'F.Courtyard');b=poly(fp,'F.Fab')
        if not c.is_empty:mechanics.append({'ref':fp['ref'],'courtyard_gap_mm':court.distance(c),'courtyard_overlap_mm2':court.intersection(c).area,'body_overlap_mm2':0 if b.is_empty else body.intersection(b).area})
    padchecks=[]
    for q in newpads:
        o,cu,masks,_=q;p=cu['F.Cu'];m=next(iter(masks.values()));others=[z for z in work if z[0]['uuid']!=o['uuid']]
        copper=sorted([{'uuid':z['uuid'],'key':z.get('key'),'net':z['net'],'gap_mm':p.distance(c['F.Cu'])} for z,c,_,_ in others if z['net']!=o['net'] and 'F.Cu' in c],key=lambda z:z['gap_mm'])[:6]
        drills=sorted([{'uuid':z['uuid'],'gap_mm':m.distance(d)} for z,_,_,d in others if d is not None],key=lambda z:z['gap_mm'])[:4]
        maskoverlap=[z['uuid'] for z,_,ma,_ in others for face,s in ma.items() if face in ('F.Mask','F.Cu') and m.intersection(s).area>0]
        passed=all(z['gap_mm']>=.127+g.s.ERROR for z in copper) and all(z['gap_mm']>=.2+g.s.ERROR for z in drills) and not maskoverlap and g.s.OUTLINE.covers(p.buffer(.254+g.s.ERROR))
        padchecks.append({'key':o['key'],'xy':o['xy'],'passed':passed,'nearest_foreign_copper':copper,'nearest_drill_to_mask':drills,'mask_overlaps':maskoverlap,'nominal_copper_clearance_surplus_mm':copper[0]['gap_mm']-.127})
    data={'source':base.binding(),'pose':[26.3125,12.,-90.,'F.Cu'],'common_removed_ids':sorted(cuts),'restored_original_CS_records':[base.by[u] for u in cs_ids],
          'retired_planning_reservation':reservation['name'],'footprint_replacement':{'before':oldfp,'after':newfp,'original_pad_records':[q[0] for q in oldpads],'candidate_pad_records':[q[0] for q in newpads],'translation_mm':[.25,0.],'flip_left_right':False},
          'additional_removed_native_records':[base.by[u] for u in CUTS],'original_contact_obligations':contacts,'retained_ground_barrel':base.by[GROUND_VIA],
          'mechanical':{'passed':all(z['courtyard_overlap_mm2']==z['body_overlap_mm2']==0 for z in mechanics),'nearest':sorted(mechanics,key=lambda z:z['courtyard_gap_mm'])[:6]},'candidate_pad_checks':padchecks,
          'main_VDD_feed_and_GND_minimum_width_mm':.20,'exclusive_R3_leaf_width_mm':.127,'native_validation_pending':True,'decoupling_reference_and_loop_review_pending':True}
    return g,base,C,view,work,before,replaced,data
