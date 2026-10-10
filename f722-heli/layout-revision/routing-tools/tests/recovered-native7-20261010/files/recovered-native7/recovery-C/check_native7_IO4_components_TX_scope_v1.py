"""Actual bonded-pad role regression, full terminal components and bounded TX donor topology."""
import argparse,json,signal,time
from pathlib import Path
from native7_RX_IO4_model_v3 import build,adapter,HERE,ROOT

def main(path):
    start=time.monotonic();ct=json.loads(path.read_text());end=start+ct['internal_seconds']
    for r in ct['source_files']:assert adapter.digest(ROOT/r['path'])==r['sha256'],r['path']
    output=ROOT/ct['receipt'];out={'schema':'f722-native7-IO4-components-TX-scope/v1','selected':False,'native_board_edited':False,'contract_sha256':adapter.digest(path),'RX_components':[],'TX_diagnostic_scopes':[]}
    def save():out['seconds']=time.monotonic()-start;output.write_text(json.dumps(out,indent=2,allow_nan=False)+'\n')
    def alarm(sig,frame):out['terminal_reason']='Bounded component-query deadline';save();raise TimeoutError()
    signal.signal(signal.SIGALRM,alarm);signal.alarm(ct['internal_seconds'])
    try:
        from shapely.geometry import Point
        from shapely.ops import unary_union,nearest_points,polylabel
        g,base,C,view,work,before,inventory,jobs=build();packet=json.loads((ROOT/ct['packet']).read_text());assert packet['source']==g.binding()
        for r in packet['routes']:
            if r['net']!='PORT_C_RX_EXT':continue
            q=g.track(r['net'],r['layer'],r['points'],r['name'],r['width']);work.append((dict(q[0],role=r['role']),*q[1:]))
        out['source']=g.binding();out['physical_packet_sha256']=adapter.digest(ROOT/ct['packet']);out['physical_packet_peer_gates']=packet['peer_access'];out['inventory']=inventory
        # Regression on actual current geometry, before any graph query.
        io=g.entry(g.one_pad('U15.5'))[1]['F.Cu'];retired=g.entry(g.one_pad('U15.1'))[1]['F.Cu']
        uid='IO4-RX-up-bonded-to-NC6';original=next(q for q in work if q[0]['uuid']==uid)
        alias,down=view('PORT_C_RX_EXT','downstream',work);clipped=next(q for q in down if q[0]['uuid']==uid)
        _,up=view('PORT_C_RX_EXT','upstream',work);own=next(q for q in up if q[0]['uuid']==uid)
        expected=original[1]['F.Cu'].difference(io)
        out['actual_pad_regression']={'bonded_key':'U15.5','bonded_uuid':g.one_pad('U15.5')['uuid'],'retired_pad_net':g.one_pad('U15.1')['net'],
          'foreign_track_clip_matches_actual_IO5':clipped[1]['F.Cu'].equals_exact(expected,0),'outside_IO5_copper_unchanged':clipped[1]['F.Cu'].difference(io).equals_exact(original[1]['F.Cu'].difference(io),0),
          'clipped_area_mm2':original[1]['F.Cu'].area-clipped[1]['F.Cu'].area,'original_bridge_overlap_with_IO5_mm2':original[1]['F.Cu'].intersection(io).area,'original_bridge_overlap_with_retired_IO1_mm2':original[1]['F.Cu'].intersection(retired).area,
          'own_upstream_copper_unchanged':own[1]['F.Cu'].equals_exact(original[1]['F.Cu'],0),'mask_identity_unchanged':clipped[2] is original[2],'drill_identity_unchanged':clipped[3] is original[3],
          'other_physical_net_geometry_unchanged':all(all(row[1][l].equals_exact(src[1][l],0) for l in src[1]) for src,row in zip(work,down) if src[0]['net']!='PORT_C_RX_EXT'),
          'physical_record_set_unchanged':all(q[0]==p[0] for q,p in zip(work,list(work)))}
        rr=out['actual_pad_regression'];assert all(rr[k] for k in ['foreign_track_clip_matches_actual_IO5','outside_IO5_copper_unchanged','own_upstream_copper_unchanged','mask_identity_unchanged','drill_identity_unchanged','other_physical_net_geometry_unchanged'])
        assert rr['clipped_area_mm2']>0 and rr['original_bridge_overlap_with_retired_IO1_mm2']==0;save()
        def reach(graph,seeds):
            seen=set(seeds);stack=list(seeds)
            while stack:
                for nxt,_,_ in graph['adj'][stack.pop()]:
                    if nxt not in seen:seen.add(nxt);stack.append(nxt)
            return seen
        def anchors(graph,objects,group):
            rows=[];nodes=set()
            for o,cu,_,_ in objects:
                if o['uuid'] not in group['ids']:continue
                coordinates=[o['xy']] if 'xy' in o else [o['start'],o['end']]
                for xy in coordinates:
                    hit=g.gg.terminals(graph,xy,tuple(cu))
                    if hit:rows.append({'uuid':o['uuid'],'key':o.get('key'),'xy':xy,'layers':list(cu),'nodes':sorted(hit)});nodes.update(hit)
                if o['kind']=='pad':
                    for i,(layer,region) in enumerate(graph['nodes']):
                        if layer not in cu:continue
                        usable=cu[layer].buffer(-.0635-g.s.ERROR).intersection(region)
                        for part in g.rt.parts(usable):
                            if part.area<=1e-12:continue
                            p=polylabel(part,tolerance=.000001);rows.append({'uuid':o['uuid'],'key':o.get('key'),'xy':[p.x,p.y],'layers':[layer],'nodes':[i],'full_pad_interior_disk_radius_mm':.0635});nodes.add(i)
            return rows,nodes
        for name,role,targetkey in [('RX_up','upstream','J11.1'),('RX_down','downstream','R34.1')]:
            C._deadline(end);net,peers=view('PORT_C_RX_EXT',role,work);groups=C._physical_groups(g,peers,net)
            sourcegroup=next(z for z in groups if 'U15.5' in z['keys']);targetgroup=next(z for z in groups if targetkey in z['keys'])
            with C._width_state(g,.127):graph=g.gg.build(net,peers,layers=C.ORDINARY)
            aa,ss=anchors(graph,peers,sourcegroup);bb,tt=anchors(graph,peers,targetgroup);rs=reach(graph,ss);rt=reach(graph,tt)
            row={'job':name,'source_component':sourcegroup,'target_component':targetgroup,'actual_source_anchors':aa,'actual_target_anchors':bb,'connected':bool(rs&tt),'source_reachable_nodes':sorted(rs),'target_reachable_nodes':sorted(rt)};out['RX_components'].append(row)
            for side,indices in [('source',rs),('target',rt)]:
                domain=unary_union([graph['nodes'][i][1] for i in indices if graph['nodes'][i][0]=='F.Cu']);eligible=unary_union([graph['eligible'][i] for i in indices if i in graph['eligible'] and graph['nodes'][i][0]=='F.Cu'])
                row[side+'_F']={'area_mm2':domain.area,'bounds':None if domain.is_empty else list(domain.bounds),'wkb_hex':domain.wkb_hex,'eligible_via_area_mm2':eligible.area,'eligible_via_wkb_hex':eligible.wkb_hex}
            if not row['connected']:
                from shapely import from_wkb
                sf=from_wkb(bytes.fromhex(row['source_F']['wkb_hex']));tf=from_wkb(bytes.fromhex(row['target_F']['wkb_hex']))
                if not sf.is_empty and not tf.is_empty:
                    a,b=nearest_points(sf,tf);pts=[[a.x,a.y],[b.x,b.y]];row['nearest_F_frontier']={'gap_mm':a.distance(b),'points':pts,'checks':g.check_track(net,'F.Cu',pts,width=.127,objects=peers)[:12]}
            else:
                for a in aa:
                    if not set(a['nodes'])&rt:continue
                    for b in bb:
                        plan=g.gg.connect(graph,a['xy'],b['xy'],tuple(a['layers']),tuple(b['layers']))
                        if plan['connected']:row['actual_component_witness_plan']=plan;break
                    if 'actual_component_witness_plan' in row:break
            save()
        tx=next(z for z in jobs if z['name']=='TX_MCU');scope=json.loads((HERE/'native7-C-compact-scope-receipt-v4.json').read_text());ids=scope['scopes']['TX_down_complete_tail']['native_ids'];records=[base.by[uid] for uid in ids]
        B=[r['uuid'] for r in records if r['kind']=='track' and 'B.Cu' in r['copper']]
        far=[r['uuid'] for r in records if r['kind']=='via' and Point(r['xy']).distance(Point(g.one_pad('R35.1')['xy']))<4]
        for label,cuts in [('complete_target_B_leaf',B),('target_B_leaf_and_owned_far_barrel',B+far),('complete_original_TX_down_tail',ids)]:
            C._deadline(end);trial=[q for q in work if q[0]['uuid'] not in cuts];plan,_=C._plan(g,view,tx,trial,end)
            row={'scope':label,'removed_native_records':[base.by[uid] for uid in cuts],'TX_MCU_plan':plan,'functional_TX_down_restoration_pending':True,'selected':False};out['TX_diagnostic_scopes'].append(row);save()
            if plan['connected']:break
        out['terminal_reason']='Actual IO5 component access and topology-derived TX replacement scope measured; no new routing or deletion adopted';save()
    except TimeoutError:pass
    except Exception as e:out['terminal_reason']=str(e);out['exception_type']=type(e).__name__;save()
    finally:
        signal.alarm(0);print(json.dumps({'terminal_reason':out.get('terminal_reason'),'seconds':time.monotonic()-start,'receipt_sha256':adapter.digest(output),'RX':[{k:r[k] for k in ('job','connected')} for r in out['RX_components']],'TX_scopes':[(r['scope'],r['TX_MCU_plan']['connected']) for r in out['TX_diagnostic_scopes']]},indent=2),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--contract',type=Path,required=True);main(p.parse_args().contract)
