"""Complete the proved local ADC/cap return with an ordinary-via .127 supply."""
import ast,copy,hashlib,json,math,signal,sys,time
from pathlib import Path
H=Path(__file__).resolve().parent;P=H.parent/'native13-access';sys.path.insert(0,str(P));START=time.monotonic();END=START+58
import composite_native11_divider_joint as g
import route_native11 as r
import graph_native11 as gr
from shapely import unary_union
from shapely.affinity import rotate,translate,scale
from shapely.geometry import Point,LineString,box
from shapely.ops import polygonize,polylabel
from shapely.strtree import STRtree
s=g.s;OUT=H/'R42-C31-full-supply12757-corrected.json';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
SOURCE=H/'R42-C31-domain-cluster57.json';D=json.loads(SOURCE.read_text());SERVOFILE=P/'joint-divider-SERVO1-restore11.json';SERVO=json.loads(SERVOFILE.read_text());assert SERVO['complete']
F={f['ref']:f for f in g.N['footprints']};PF=F['R42'];ORIGIN=tuple(PF['xy']);OLD=[o for o in g.N['objects'] if o.get('ref')=='R42'];CAPF=F['C31'];CAPOLD=[o for o in g.N['objects'] if o.get('ref')=='C31']
model=H/'construct_R42_C31_domain57.py';tree=ast.parse(model.read_text());names={'records','caprecords','routecheck','viacheck','samecontacts','addroute','padcheck'}
defs=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names];assert len(defs)==len(names);exec(compile(ast.Module(body=defs,type_ignores=[]),str(model),'exec'),globals())
cuts={o['uuid'] for o in D['removed_native_records']};BASE=[q for q in g.BASE if q[0]['uuid']not in cuts and q[0].get('ref')not in ('R42','C31')]
sr=D['held_SERVO_routes'];sv=D['held_SERVO_vias'];bootroute=dict(D['held_BOOT_route'],layer='B.Cu');bootvia=D['held_BOOT_via'];assert set(g.one_pad('U1.60')['copper'])=={'B.Cu'}
BASE += [g.track(q['net'],q['layer'],q['points'],q['name'],q['width']) for q in sr+[bootroute]]+[g.via(v['net'],v['xy'],v['name']) for v in sv+[bootvia]]
source_row=next(q for q in D['rows'] if q.get('ADC_routes') and any(not a['unintended_source_GND_contacts'] for a in q.get('ground_trials',[])))
ground=next(a for a in source_row['ground_trials'] if not a['unintended_source_GND_contacts']);cxy,cangle,_=source_row['poses']['C31'];cap=caprecords(cxy,cangle)
av=dict(name='cluster-ADC-transition',net='ADC_BUS',xy=g.by['39a56392-875d-4879-813e-fb2d9fe74901']['xy'],diameter=.45,drill=.2);gv=ground['via'];groute=ground['route']
out=dict(schema='f722-complete-R42-C31-full-supply12757/v1',source=g.binding(),input_receipts={SOURCE.name:sha(SOURCE),SERVOFILE.name:sha(SERVOFILE),model.name:sha(model)},
    removed_native_records=D['removed_native_records'],old_C31_ground_leaf_contacts=D['old_C31_ground_leaf_contacts'],old_C31_ground_via_contacts=D['old_C31_ground_via_contacts'],old_C31_GND_plane_contacts=D['old_C31_GND_plane_contacts'],old_supply_leaf_contacts=D['old_supply_leaf_contacts'],
    original_divider_feed_and_ground_held=True,held_SERVO_routes=sr,held_SERVO_vias=sv,held_BOOT_route=bootroute,held_BOOT_via=bootvia,retained_actual_MCU_ADC_B_witness=D['retained_actual_MCU_ADC_B_witness'],
    rows=[],routes=[],vias=[],complete_cluster=False,complete_ADC_tree=False,complete_BOOT_tree=False,native_candidate=False,adoptable=False,plane_behavior_qualified=False,
    pending=['Actual relocated R43 ADC join','Actual MCU-to-switch BOOT','Fresh native source/pose/process/refill/reference and ADC settling/noise review'])
def save():out.update(seconds=time.monotonic()-START,script_sha256=sha(__file__));OUT.write_text(json.dumps(out,indent=2)+'\n')
def stop(sig,frame):out['terminal_reason']='Bounded60second full supply construction';save();raise SystemExit(0)
signal.signal(signal.SIGALRM,stop);signal.alarm(max(1,int(60-(time.monotonic()-START))))
out['corrected_inherited_BOOT_layer']=dict(inherited=D['held_BOOT_route']['layer'],actual=bootroute['layer'],actual_pad='U1.60',replaces_invalid_inherited_overlay=True)
out['exclusive_R42_supply_width_rationale']=dict(width_mm=.127,retained_high_current_trunks_unchanged=True,series_resistors_ohm=[68000,16000,16000],nominal_input_V=5,nominal_series_current_uA=50,initial_zero_volt_cap_current_bound_uA=5/68000*1e6)
out['ADC_terminal_ledger']=[dict(key=k,path_complete_to_MCU=k=='U1.10',status='Local complete cluster reconstruction pending'if k!='R43.1'else'Full divider ADC join pending')for k in ('R42.2','C31.1','U1.10','R43.1')]
for rxy,rangle in [([16,7.7],0)]:
    pads=records(rxy,rangle)+cap;entries=[g.entry(q) for q in pads];held=BASE+entries+[g.via(v['net'],v['xy'],v['name']) for v in (av,gv)]+[g.track(groute['net'],groute['layer'],groute['points'],groute['name'],groute['width'])]
    pc=[padcheck(p,e,held) for p,e in zip(pads,entries)];row=dict(poses={'R42':[rxy,rangle,'F.Cu'],'C31':[cxy,cangle,'B.Cu']},pad_checks=pc,complete=False);out['rows'].append(row);save()
    if not all(q['passed'] for q in pc):continue
    pp={p['key']:p for p in pads};adc=[q for q in source_row['ADC_routes'] if q['layer']=='B.Cu']
    first=addroute('ADC_BUS','F.Cu',.127,pp['R42.2']['xy'],av['xy'],held,'cluster-R42-ADC-F')
    if first is None:row['terminal_reason']='Actual R42 ADC entry no longer connects';save();continue
    adc=[first]+adc;held += [g.track(q['net'],q['layer'],q['points'],q['name'],q['width']) for q in adc]
    graph=gr.build('+5V_PERIPH',held);target=g.by['dfd384be-99d1-43a6-afd1-174fc1df74d9'];path=gr.connect(graph,pp['R42.1']['xy'],target['xy'],('F.Cu',),tuple(target['copper']))
    path['actual_pair']=['R42.1',target['uuid']];row['supply_path']=path;save()
    if not path['connected']:row['terminal_reason']='Full four-layer .127 supply graph disconnected';save();continue
    power_vias=[dict(name='cluster-supply-via-'+str(i),net='+5V_PERIPH',xy=v['xy'],diameter=.45,drill=.2) for i,v in enumerate(path['new_vias'])]
    held += [g.via(v['net'],v['xy'],v['name']) for v in power_vias];power=[];complete=True
    for i,leg in enumerate(path['legs']):
        if math.dist(leg['start'],leg['end'])<1e-8:continue
        pts=r.route(graph['nodes'][leg['node']][1],leg['start'],leg['end'],END)
        if pts is None:complete=False;break
        q=dict(name='cluster-supply-route-'+str(i),net='+5V_PERIPH',layer=leg['layer'],width=.127,points=pts);q.update(routecheck(q,held))
        if not q['passed']:complete=False;break
        power.append(q);held.append(g.track(q['net'],q['layer'],q['points'],q['name'],q['width']));save()
    if not complete:row['terminal_reason']='Actual supply copper construction incomplete';save();continue
    routes=adc+[groute]+power;vias=[av,gv]+power_vias
    checks=[dict(name=q['name'],**routecheck(q,held)) for q in routes+sr+[bootroute]]+[dict(name=v['name'],**viacheck(v,held)) for v in vias+sv+[bootvia]]
    row['constructed_routes']=routes;row['constructed_vias']=vias;row['mutual_checks']=checks;row['complete']=all(q['passed'] for q in checks);save()
    if not row['complete']:continue
    row['transformed_pad_records']=pads;out.update(selected=row,routes=routes,vias=vias,complete_cluster=True,new_supply_anchor_record=target)
    out['new_supply_contacts']={q['name']:samecontacts(g.track(q['net'],q['layer'],q['points'],q['name'],q['width']),BASE,set()) for q in power}
    out['ADC_terminal_ledger']=[dict(key=key,xy=pp[key]['xy'] if key in pp else g.one_pad(key)['xy'],path_complete_to_MCU=key!='R43.1',evidence='Constructed cluster and retained exact MCU ADC B witness' if key!='R43.1' else 'Actual divider join pending') for key in ('R42.2','C31.1','U1.10','R43.1')]
    out['BOOT_ledger']=dict(MCU_entry_complete=True,accepted_SW1_R2_segment_complete=True,actual_MCU_to_SW1_path_complete=False);save()
    graph=gr.build('ADC_BUS',held);end=g.one_pad('R43.1');join=gr.connect(graph,pp['C31.1']['xy'],end['xy'],('B.Cu',),tuple(end['copper']));join['actual_pair']=['C31.1','R43.1'];out['actual_divider_join']=join;save()
    if join['connected']:
        jvias=[dict(name='cluster-divider-via-'+str(i),net='ADC_BUS',xy=v['xy'],diameter=.45,drill=.2) for i,v in enumerate(join['new_vias'])];held += [g.via(v['net'],v['xy'],v['name']) for v in jvias];jroutes=[];joined=True
        for i,leg in enumerate(join['legs']):
            if math.dist(leg['start'],leg['end'])<1e-8:continue
            pts=r.route(graph['nodes'][leg['node']][1],leg['start'],leg['end'],END)
            if pts is None:joined=False;break
            q=dict(name='cluster-divider-route-'+str(i),net='ADC_BUS',layer=leg['layer'],width=.127,points=pts);q.update(routecheck(q,held))
            if not q['passed']:joined=False;break
            jroutes.append(q);held.append(g.track(q['net'],q['layer'],q['points'],q['name'],q['width']))
        if joined:
            out['routes']+=jroutes;out['vias']+=jvias;out['full_ADC_mutual_checks']=[dict(name=q['name'],**routecheck(q,held)) for q in out['routes']+sr+[bootroute]]+[dict(name=v['name'],**viacheck(v,held)) for v in out['vias']+sv+[bootvia]]
            out['complete_ADC_tree']=all(q['passed'] for q in out['full_ADC_mutual_checks'])
            if out['complete_ADC_tree']:out['ADC_terminal_ledger'][-1].update(path_complete_to_MCU=True,evidence='Complete actual divider join and mutual finite audit')
    else:join['remaining_terminal_domains']=[dict(layer=graph['nodes'][i][0],bounds=list(graph['nodes'][i][1].bounds),via_area_mm2=graph['eligible'][i].area if i in graph['eligible'] else 0) for i in join['start_nodes']+join['end_nodes']]
    out['terminal_reason']='Complete R42/C31 input/filter/supply/ground; divider ADC join '+('complete' if out['complete_ADC_tree'] else 'still open')+'; full BOOT and native/source/refill/reference gates remain open';save();signal.alarm(0)
    print('TERMINAL',True,out['complete_ADC_tree'],rxy,rangle,[(v['net'],v['xy']) for v in out['vias']],out['seconds'],flush=True);raise SystemExit(0)
out['terminal_reason']='No full .127 supply for the bounded two-part cluster variants';save();signal.alarm(0);print('TERMINAL',False,out['seconds'],flush=True)
