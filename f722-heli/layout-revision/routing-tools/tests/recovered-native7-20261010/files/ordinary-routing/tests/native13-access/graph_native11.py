"""Exact four-layer component graph with actual own-via reuse."""
import heapq
import math
import native11_context as g
import route_native11 as r
from shapely.geometry import Point
from shapely.strtree import STRtree
from shapely.ops import polylabel
s=g.s


def build(net,objects,layers=('B.Cu','In3.Cu','In2.Cu','F.Cu')):
    s.OBJECTS=objects;s.HALF=.0635
    nodes=[];bylayer={};obstacles={};adj={}
    for layer in layers:
        free,obs,vo=r.domain(net,layer,objects=objects)
        obstacles[layer]=obs;bylayer[layer]=[]
        for p in r.parts(free):
            i=len(nodes);nodes.append((layer,p));bylayer[layer].append(i);adj[i]=[]
    legal=s.OUTLINE.buffer(-.479-s.ERROR-.0001).difference(r.expanded(vo))
    eligible={i:p.intersection(legal)for i,(l,p)in enumerate(nodes)}
    eligible={i:p for i,p in eligible.items()if not p.is_empty and p.area>1e-9}
    for o,c,m,d in objects:
        if o['kind']!='via'or o['net']!=net:continue
        hit=[i for i,(l,p)in enumerate(nodes)if l in c and p.covers(Point(o['xy']))]
        for ai,a in enumerate(hit):
            for b in hit[ai+1:]:
                e=dict(kind='existing_own_via',xy=o['xy'],uuid=o['uuid'])
                adj[a].append((b,0,e));adj[b].append((a,0,e))
    for ai,la in enumerate(layers):
        for lb in layers[ai+1:]:
            ids=[i for i in bylayer[lb]if i in eligible]
            if not ids:continue
            tree=STRtree([eligible[i]for i in ids])
            for a in bylayer[la]:
                if a not in eligible:continue
                for j in tree.query(eligible[a],predicate='intersects'):
                    b=ids[int(j)];pp=r.parts(eligible[a].intersection(eligible[b]))
                    if not pp:continue
                    p=max(pp,key=lambda p:p.area)
                    if p.area<=1e-9:continue
                    e=dict(kind='new_via_region',geometry=p)
                    adj[a].append((b,1,e));adj[b].append((a,1,e))
    return dict(nodes=nodes,bylayer=bylayer,obstacles=obstacles,via_obstacles=vo,adj=adj,eligible=eligible)


def terminals(graph,xy,layers):
    return {i for i,(l,p)in enumerate(graph['nodes'])if l in layers and p.covers(Point(xy))}


def connect(graph,a,b,start_layers=('B.Cu',),end_layers=('B.Cu',)):
    starts=terminals(graph,a,start_layers);ends=terminals(graph,b,end_layers)
    queue=[(0,i)for i in starts];heapq.heapify(queue)
    dist={i:0 for i in starts};prev={};goal=None
    while queue:
        cost,i=heapq.heappop(queue)
        if cost!=dist[i]:continue
        if i in ends:goal=i;break
        for j,w,e in graph['adj'][i]:
            nc=cost+w
            if nc<dist.get(j,math.inf):dist[j]=nc;prev[j]=(i,e);heapq.heappush(queue,(nc,j))
    row=dict(start=a,end=b,start_nodes=sorted(starts),end_nodes=sorted(ends),
             connected=goal is not None,additional_transition_count=None if goal is None else dist[goal],
             legs=[],new_vias=[])
    if goal is None:return row
    seq=[];cur=goal
    while cur not in starts:
        before,e=prev[cur];seq.append((before,cur,e));cur=before
    seq.reverse();cursor=a;current=cur
    for aa,bb,e in seq:
        if e['kind']=='existing_own_via':xy=e['xy'];transition=e
        else:
            p=polylabel(e['geometry'],tolerance=.0001);xy=[round(p.x,6),round(p.y,6)]
            ch=s.check(Point(xy),graph['via_obstacles'],True)
            transition=dict(kind=e['kind'],xy=xy,region_area_mm2=e['geometry'].area,
                            region_bounds=list(e['geometry'].bounds),passed=ch[0]['pass_with_polygon_error'],nearest=ch[:4])
            row['new_vias'].append(transition)
        row['legs'].append(dict(node=current,layer=graph['nodes'][current][0],start=cursor,end=xy,transition=transition))
        cursor=xy;current=bb
    row['legs'].append(dict(node=goal,layer=graph['nodes'][goal][0],start=cursor,end=b))
    return row
