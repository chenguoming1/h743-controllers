#!/usr/bin/env python3
"""Hash-bound native contact/loop geometry audit. Never assembles an FEM mesh."""
import argparse
import hashlib
import json
from pathlib import Path
import shapely as s
from copper_fem import Refused, native_geometry, contact_keys, contact_spec_geometry, polygon_set, parts
from validate_static import read_json, sha256, stackup_centers


def ideal_land_contact_groups(domains,contacts,barrels):
    """Find same-layer terminal mergers through ideal lands before triangulation.

    Barrel spans have finite resistance and never join layer components here.
    The 0.02 nm (2e-8 mm) per-region buffer matches the FEM's contact roundoff membership.
    It is used only for a conservative refusal screen, not to alter copper.
    """
    collisions=[];region_count=0
    for layer,domain in domains.items():
        entries=[('contact',name,geom.intersection(domain))for name,(l,geom)in contacts.items()if l==layer]
        entries += [('barrel',obj['uuid'],polygon_set(obj['copper'][layer]).intersection(domain))
                    for obj in barrels if layer in obj['copper']]
        if not entries:continue
        for kind,name,geom in entries:
            if geom.is_empty or not geom.is_valid or geom.geom_type!='Polygon':
                raise Refused('Disconnected/empty ideal '+kind+' land: '+name+'/'+layer)
        regions=[e[2].buffer(2e-8)for e in entries];tree=s.STRtree(regions)
        parent=list(range(len(entries)))
        def root(i):
            while parent[i]!=i:
                parent[i]=parent[parent[i]];i=parent[i]
            return i
        for i,j in tree.query(regions,predicate='intersects').T:
            parent[root(int(i))]=root(int(j))
        groups={}
        for i,entry in enumerate(entries):groups.setdefault(root(i),[]).append(entry)
        region_count+=len(entries)
        for group in groups.values():
            names=sorted(name for kind,name,_ in group if kind=='contact')
            if len(names)>1:
                union=s.union_all([geom for _,_,geom in group])
                collisions.append({'layer':layer,'contacts':names,
                  'barrel_uuids':sorted(name for kind,name,_ in group if kind=='barrel'),
                  'native_union_area_mm2':union.area,'native_union_bounds_mm':list(union.bounds),
                  'membership_roundoff_buffer_mm':2e-8,
                  'meaning':'These distinct contacts collapse through same-layer ideal via/land regions; explicit reviewed union/aliases are required'})
    return {'ideal_region_count':region_count,'terminal_collisions':collisions,
            'finite_interlayer_barrel_resistance_preserved':True}


def audit_ports(board, geometry_path, ledger_path, connectivity_path, critical_path=None):
    paths={'board':Path(board),'geometry':Path(geometry_path),'ledger':Path(ledger_path),
           'connectivity':Path(connectivity_path)}
    if critical_path:paths['critical']=Path(critical_path)
    hashes={name:sha256(path)for name,path in paths.items()}
    g=read_json(paths['geometry']);l=read_json(paths['ledger']);c=read_json(paths['connectivity'])
    critical=read_json(paths['critical'])if critical_path else {}
    for name,report in [('geometry',g),('connectivity',c)]+([('critical',critical)]if critical_path else []):
        if report.get('board_sha256')!=hashes['board']:
            raise Refused(name+' does not belong to this board')
    if g.get('schema')!='kicad-native-copper/v1' or g.get('source_unchanged')is not True or g.get('units')!='mm':
        raise Refused('Expected unchanged native millimetre geometry')
    networks=l.get('networks',[])
    if not networks or len({n['net']for n in networks})!=len(networks):
        raise Refused('Missing or duplicate networks')
    names=[name for n in networks for name in n['contacts']]
    if len(set(names))!=len(names):raise Refused('Duplicate contact names')
    rows=[];all_contacts={};faults=[]
    legacy={x['net']:x for x in critical.get('fullnet_connectivity',[])}
    for network in networks:
        net=network['net'];domain,pads,barrels=native_geometry(g,net)
        expected={o['uuid']for o in g['objects']if o['kind']=='pad'and o.get('net')==net and o.get('number')}
        proof=c.get('nets',{}).get(net)
        if proof is not None:
            actual={u for group in proof.get('groups',[])for u in group.get('pad_uuids',[])}
            complete=bool(expected)and proof.get('pad_group_count')==1 and actual==expected
            proof_kind='Native pad UUID groups'
        else:
            proof=legacy.get(net,{})
            expected_keys={o['key']for o in g['objects']if o['kind']=='pad'and o.get('net')==net and o.get('number')}
            complete=bool(expected_keys)and proof.get('complete')is True and not proof.get('unreached')and set(proof.get('pads',[]))==expected_keys
            proof_kind='Hash-bound critical checker complete pad-key set'
        if not complete:faults.append({'net':net,'reason':'Missing/incomplete native all-pad connectivity evidence'})
        contacts=[];contact_regions=[];regions_by_name={}
        for name,spec in network['contacts'].items():
            raw=contact_spec_geometry(pads,spec)
            if spec['layer']not in domain:raise Refused('Contact layer absent from native domain')
            physical=raw.intersection(domain[spec['layer']])
            if physical.is_empty or not physical.is_valid or physical.geom_type!='Polygon' or physical.area<=0:
                raise Refused(name+' is empty/disconnected after actual drill and outline clipping')
            for previous,layer,shape in contact_regions:
                if layer==spec['layer'] and physical.intersects(shape):
                    raise Refused(name+' touches/overlaps contact '+previous+'; define one grouped contact instead')
            contact_regions.append((name,spec['layer'],physical))
            regions_by_name[name]=(spec['layer'],physical)
            row={'name':name,'pads':contact_keys(spec),'layer':spec['layer'],
                 'native_pad_uuids':sorted(o['uuid']for key in contact_keys(spec)for o in pads[key]),
                 'raw_land_area_mm2':raw.area,'physical_contact_area_mm2':physical.area,
                 'area_removed_by_actual_drills_or_outline_mm2':raw.area-physical.area,
                 'physical_holes':len(physical.interiors),'physical_bounds_mm':list(physical.bounds),
                 'physical_geometry_sha256':hashlib.sha256(physical.wkb).hexdigest(),
                 'finite_connected_contact':True}
            contacts.append(row);all_contacts[name]=(net,spec['layer'])
        ideal=ideal_land_contact_groups(domain,regions_by_name,barrels)
        for collision in ideal['terminal_collisions']:
            faults.append({'net':net,'reason':'Distinct contacts merge through ideal via/land regions',**collision})
        rows.append({'net':net,'native_all_pad_connectivity_complete':complete,'connectivity_proof':proof_kind,
                     'native_pad_count':len(expected),'plated_barrel_count':len(barrels),
                     'actual_copper_area_mm2_by_layer':{layer:shape.area for layer,shape in domain.items()},'contacts':contacts,
                     'boundary_vertices_by_layer':{layer:sum(len(p.exterior.coords)-1+sum(len(h.coords)-1 for h in p.interiors)for p in parts(shape))for layer,shape in domain.items()},
                     'ideal_land_equivalence':ideal})
    loops=[]
    for loop in l.get('loops',[]):
        if not loop.get('legs'):raise Refused('Empty loop')
        for leg in loop['legs']:
            if leg['source']==leg['sink']or any(all_contacts.get(leg[k],(None,))[0]!=leg['net']for k in ['source','sink']):
                raise Refused('Loop uses missing, wrong-net or equivalent endpoint names')
        loops.append({'name':loop['name'],'legs':loop['legs'],'endpoint_bindings_valid':True,
                      'maximum_ohm':loop.get('maximum_ohm'),'resistance_solved':False})
    if hashes!={name:sha256(path)for name,path in paths.items()}:
        raise Refused('An input changed during the audit')
    return {'status':'GEOMETRY AND NATIVE CONNECTIVITY AUDIT ONLY; NO MESH OR CIRCUIT RUN',
      'board_sha256':hashes['board'],'input_sha256':hashes,'native_version':g.get('native_version'),
      'passed':not faults,'source_acceptance_or_final_board_qualification':False,'faults':faults,
      'all_net_drills_included':True,'physical_drill_objects':sum(bool(o.get('drill'))for o in g['objects']),
      'saved_fills_used_without_repair':True,'stackup':stackup_centers(paths['board'],g['copper_layers']),
      'networks':rows,'contact_count':len(all_contacts),'loops':loops,
      'limitations':['Physical/DRC/source-acceptance gates remain separate and must all pass before numerical activation.',
                    'This audit does not establish copper resistance, current sharing, voltage margins, ampacity or temperature.',
                    'Any later route, via, drill, pad or fill change invalidates this source binding. Re-audit the final routed board.']}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ['board','geometry','ledger','connectivity','out']:p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--critical',type=Path)
    a=p.parse_args()
    protected=[a.board,a.geometry,a.ledger,a.connectivity]+([a.critical]if a.critical else [])+list(Path(__file__).parent.glob('*.py'))
    if a.out.suffix!='.json' or any(a.out.resolve()==x.resolve()or(a.out.exists()and a.out.samefile(x))for x in protected):
        raise Refused('Output must be a separate JSON receipt')
    result=audit_ports(a.board,a.geometry,a.ledger,a.connectivity,a.critical)
    a.out.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'passed':result['passed'],'board_sha256':result['board_sha256'],
                      'contacts':result['contact_count'],'loops':len(result['loops']),'mesh_run':False}))
    return 0 if result['passed']else 1


if __name__=='__main__':raise SystemExit(main())
