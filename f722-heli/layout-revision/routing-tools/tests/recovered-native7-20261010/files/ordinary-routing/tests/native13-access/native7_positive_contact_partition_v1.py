"""Scoped planning topology: positive area, actual drill voids and declared barrels.

This is separate from the historical intersects ledger. It does not establish
full-width contact, annular manufacturing margin or final-native qualification.
"""
from collections import defaultdict
from shapely import unary_union
from shapely.strtree import STRtree


def parts(shape):
    if shape.is_empty:
        return []
    if shape.geom_type == 'Polygon':
        if not shape.is_valid:
            raise ValueError('Invalid copper contour; no repair is permitted')
        return [shape]
    return [p for child in getattr(shape, 'geoms', ()) for p in parts(child)]


def drill_voids(objects, copper_layers):
    holes=defaultdict(list)
    for record, copper, masks, drill in objects:
        if drill is None:
            continue
        layers=list(copper_layers) if record.get('npth') else record.get('barrel_layers', [])
        if not layers:
            raise ValueError('Drilled object lacks declared physical hole layers: '+record['uuid'])
        for layer in layers:
            if layer in copper_layers:
                holes[layer].append(drill)
    return {layer:unary_union(shapes) for layer,shapes in holes.items()}


def partition(objects, net, copper_layers, *, holes=None):
    if holes is None:
        holes=drill_voids(objects,copper_layers)
    fragments=[];bylayer=defaultdict(list);barrels=defaultdict(list)
    for record,copper,masks,drill in objects:
        if record['net']!=net:
            continue
        plated=record.get('plated',False) or record['kind']=='via'
        declared=set(record.get('barrel_layers',()))
        if plated and (drill is None or not declared):
            raise ValueError('Plated object lacks drill/barrel declaration: '+record['uuid'])
        for layer,shape in copper.items():
            material=shape.difference(holes[layer]) if layer in holes else shape
            for polygon in parts(material):
                i=len(fragments);fragments.append((record['uuid'],layer,polygon));bylayer[layer].append(i)
                # Disjoint pad islands do not gain a vertical edge merely because
                # they share one record. Copper must actually meet its hole wall.
                if plated and layer in declared and polygon.boundary.intersection(drill.boundary).length>0:
                    barrels[record['uuid']].append(i)
    parent=list(range(len(fragments)))
    def find(i):
        while parent[i]!=i:
            parent[i]=parent[parent[i]];i=parent[i]
        return i
    def union(a,b):
        a,b=find(a),find(b)
        if a!=b:parent[b]=a
    for ids in bylayer.values():
        tree=STRtree([fragments[i][2] for i in ids])
        for position,i in enumerate(ids):
            for candidate in tree.query(fragments[i][2],predicate='intersects'):
                j=ids[int(candidate)]
                if int(candidate)>position and fragments[i][2].intersection(fragments[j][2]).area>0:
                    union(i,j)
    for ids in barrels.values():
        for i in ids[1:]:union(ids[0],i)
    groups=defaultdict(set);membership=defaultdict(set)
    for i,(uid,layer,polygon) in enumerate(fragments):
        root=find(i);groups[root].add(uid);membership[uid].add(root)
    return list(groups.values()),membership
