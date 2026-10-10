"""Bounded exact-domain routing helpers; importing performs no route search."""
import heapq
import math
import time
import shapely
from shapely import unary_union
from shapely.geometry import Point, LineString
import native11_context as g
s=g.s


def parts(q):
    return [p for p in (q.geoms if hasattr(q,'geoms')else[q]) if p.geom_type=='Polygon' and not p.is_empty]


def expanded(obs,reserve=.0001):
    return unary_union([o['geometry'].buffer((o['required_center_distance_mm']+s.ERROR+reserve)/math.cos(math.pi/128),quad_segs=32)
                        for o in obs if o['category']!='edge_npth_copper'])


def domain(net,layer,width=.127,objects=None,reserve=.0001):
    if objects is not None:s.OBJECTS=objects
    s.HALF=width/2
    obs,vo,_=s.obstacles(net,layer)
    return s.OUTLINE.buffer(-.254-width/2-s.ERROR-reserve).difference(expanded(obs,reserve)),obs,vo


def component(f,xy):
    return next((p for p in parts(f)if p.covers(Point(xy))),None)


def route(comp,a,b,deadline):
    if comp is None or not comp.covers(Point(a))or not comp.covers(Point(b)):return None
    shapely.prepare(comp)
    for pts in s.paths2(a,b):
        if comp.covers(LineString(pts)):return pts
    tris=list(shapely.constrained_delaunay_triangles(comp).geoms)
    centers=[tuple(t.centroid.coords[0])for t in tris]
    adj=[{}for t in tris];edges={}
    for k,t in enumerate(tris):
        if time.monotonic()>deadline:return None
        vs=list(t.exterior.coords)
        for p,q in zip(vs,vs[1:]):
            key=tuple(sorted((p,q)))
            if key in edges:
                i=edges[key];m=((p[0]+q[0])/2,(p[1]+q[1])/2)
                w=math.dist(centers[i],m)+math.dist(centers[k],m)
                adj[i][k]=(w,m);adj[k][i]=(w,m)
            else:edges[key]=k
    ai=next(i for i,p in enumerate(tris)if p.covers(Point(a)))
    bi=next(i for i,p in enumerate(tris)if p.covers(Point(b)))
    queue=[(0,ai)];costs={ai:0};prev={}
    while queue:
        cost,i=heapq.heappop(queue)
        if cost!=costs[i]:continue
        if i==bi:break
        if time.monotonic()>deadline:return None
        for k,(w,m)in adj[i].items():
            nc=cost+w
            if nc<costs.get(k,math.inf):costs[k]=nc;prev[k]=i;heapq.heappush(queue,(nc,k))
    if bi not in costs:return None
    seq=[bi]
    while seq[-1]!=ai:seq.append(prev[seq[-1]])
    seq.reverse();raw=[a]
    for i,k in zip(seq,seq[1:]):raw.extend([centers[i],adj[i][k][1]])
    raw.extend([centers[bi],b]);pts=[raw[0]];i=0
    while i<len(raw)-1:
        if time.monotonic()>deadline:return None
        k=len(raw)-1
        while k>i+1 and not comp.covers(LineString([raw[i],raw[k]])):k-=1
        pts.append(raw[k]);i=k
    return [[round(x,6),round(y,6)]for x,y in pts]
