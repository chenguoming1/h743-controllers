"""Wire repeated nets within each functional drawing unit on the schematic grid.

Pure presentation: symbol and pin identities remain unchanged. Routes are orthogonal,
with explicit junctions at branches and no junction at crossings of different nets.
The exported native netlist must be compared after any layout modification.
"""
import math, heapq, collections, copy
import sexpr as sx

GRID=1.27
DIRS=((1,0),(0,1),(-1,0),(0,-1))

def connect(sch, design, project):
    from gen_schematic import uid, S
    def pt(x,y): return (round(float(x)/GRID),round(float(y)/GRID))
    def mm(p): return [round(p[0]*GRID,4),round(p[1]*GRID,4)]
    defs={sx.text(n[1]):n for n in sx.find(sch,'lib_symbols')[0][1:]}
    parts={p['ref']:p for p in design.PARTS}
    symbols={sx.text(sx.find(n,'property')[0][2]):n for n in sx.find(sch,'symbol')}
    panels=[n for n in sx.find(sch,'polyline') if len(sx.find(sx.find(n,'pts')[0],'xy'))==5]
    # Keep the MCU core's named boundary pins and the separately wired decoupling bank.
    # Every other functional panel gets real local circuits, not islands of net labels.
    target_panels=[]
    for p in panels:
        coords=[pt(*n[1:3]) for n in sx.find(sx.find(p,'pts')[0],'xy')]
        x1,y1=coords[0];x2,y2=coords[2]
        if abs(x1*GRID-286)<2 and (abs(y1*GRID-44)<2 or abs(y1*GRID-291)<2):continue
        target_panels.append((x1,y1,x2,y2))
    remove=set(); added=[]; report=[]
    for panel in target_panels:
        x1,y1,x2,y2=panel
        def inside(p):return x1<p[0]<x2 and y1<p[1]<y2
        refs=[r for r,n in symbols.items() if inside(pt(*sx.find(n,'at')[0][1:3]))]
        if not refs:continue
        block=set(); occupancy=collections.defaultdict(dict); edges=collections.defaultdict(set); endpoints=collections.defaultdict(list); pin_nodes=set(); terminals=collections.defaultdict(set)
        original_labels=collections.defaultdict(list)
        for n in sch:
            if not isinstance(n,list):continue
            if n[0] in ('wire','junction','global_label'):
                points=[pt(*a[1:3]) for a in sx.find(n,'at')]
                if n[0]=='wire':points=[pt(*a[1:3]) for a in sx.find(sx.find(n,'pts')[0],'xy')]
                if points and all(inside(p) for p in points):
                    remove.add(id(n))
                    if n[0]=='global_label':original_labels[sx.text(n[1])].append(n)
        for ref in refs:
            n=symbols[ref];a=sx.find(n,'at')[0];cx,cy=map(float,a[1:3]);angle=float(a[3]);rad=math.radians(angle)
            sym=defs[sx.text(sx.find(n,'lib_id')[0][1])]
            def transform(x,y):return pt(cx+x*math.cos(rad)-y*math.sin(rad),cy-x*math.sin(rad)-y*math.cos(rad))
            # Conservative body box; pin escape corridors are separately protected.
            geometry=[]
            for kind in ('rectangle','polyline','circle','arc','bezier'):
                for shape in sx.walk(sym,kind):
                    for key in ('start','end','xy','center','mid'):
                        for coordinate in sx.walk(shape,key):
                            try: geometry.append((float(coordinate[1]),float(coordinate[2])))
                            except (ValueError,IndexError): pass
            geometry.extend((p[0],p[1]) for p in sx.symbol_pins(sym).values())
            if geometry:
                xa=min(p[0] for p in geometry)-GRID;xb=max(p[0] for p in geometry)+GRID
                ya=min(p[1] for p in geometry)-GRID;yb=max(p[1] for p in geometry)+GRID
            else:
                xa,ya,xb,yb=sx.symbol_bbox(sym)
                xa=min(xa+1.27,-1.27);xb=max(xb-1.27,1.27);ya=min(ya+1.27,-1.27);yb=max(yb-1.27,1.27)
            corners=[transform(x,y) for x in (xa,xb) for y in (ya,yb)]
            for x in range(min(p[0] for p in corners),max(p[0] for p in corners)+1):
                for y in range(min(p[1] for p in corners),max(p[1] for p in corners)+1):block.add((x,y))
            # Keep wires clear of visible reference/value text.
            for prop in sx.find(n,'property'):
                if sx.text(prop[1]) not in ('Reference','Value'):continue
                eff=sx.find(prop,'effects')[0]
                if sx.find(eff,'hide'):continue
                a=sx.find(prop,'at')[0];px,py=pt(*a[1:3]);value=sx.text(prop[2]);w=max(2,math.ceil(len(value)*0.72/GRID));left=bool(sx.find(eff,'justify'))
                for xx in range(px if left else px-w//2,px+w+1 if left else px+(w+1)//2+1):
                    for yy in range(py-1,py+2):block.add((xx,yy))
            for num,(px,py,ang,length,name) in sx.symbol_pins(sym).items():
                net=parts[ref]['pins'][num] if ref in parts else design.PWR_FLAGS[int(ref[-2:])-1]
                if net is None:continue
                p=transform(px,py);a=math.radians(ang+angle+180);direction=(round(math.cos(a)),-round(math.sin(a)));q=(p[0]+direction[0]*3,p[1]+direction[1]*3)
                endpoints[net].append(q);pin_nodes.add(p);pin_nodes.add(q);terminals[net].add(p)
                path=[(p[0]+direction[0]*i,p[1]+direction[1]*i) for i in range(4)]
                for z in path:block.discard(z)
                for aa,bb in zip(path,path[1:]):edges[net].add(tuple(sorted((aa,bb))))
        def refresh():
            occupancy.clear()
            for net,ee in edges.items():
                dirs=collections.defaultdict(set)
                for a,b in ee:dirs[a].add((b[0]-a[0],b[1]-a[1]));dirs[b].add((a[0]-b[0],a[1]-b[1]))
                for p,ds in dirs.items():
                    occupancy[p][net]='H' if ds=={(-1,0),(1,0)} and p not in pin_nodes else 'V' if ds=={(0,-1),(0,1)} and p not in pin_nodes else 'B'
        refresh()
        # Label each unit net once; retain exact global net identities. Selected label
        # rectangles are route obstacles, so newly drawn wires do not run through text.
        chosen=[]
        for net,candidates in original_labels.items():
            if net not in endpoints:continue
            # Prefer horizontal labels for power/analog nets where available.
            candidates=sorted(candidates,key=lambda n:(float(sx.find(n,'at')[0][3])%180!=0,))
            selected=None
            for candidate in candidates:
                a=sx.find(candidate,'at')[0];p=pt(*a[1:3]);angle=int(float(a[3]));w=math.ceil((len(net)*0.8+2)/GRID)
                if angle==0:rect=(p[0]+1,p[1],p[0]+w,p[1])
                elif angle==180:rect=(p[0]-w,p[1],p[0]-1,p[1])
                elif angle==90:rect=(p[0],p[1]-w,p[0],p[1]-1)
                else:rect=(p[0],p[1]+1,p[0],p[1]+w)
                cells={(x,y) for x in range(rect[0],rect[2]+1) for y in range(rect[1],rect[3]+1)}
                if all(inside(z) for z in cells) and not cells.intersection(block) and not any(z in occupancy for z in cells):
                    selected=(copy.deepcopy(candidate),cells);break
            if selected:
                chosen.append(selected[0]);block.update(selected[1]); endpoints[net].append(pt(*sx.find(selected[0],'at')[0][1:3])); pin_nodes.add(endpoints[net][-1]);terminals[net].add(endpoints[net][-1])
            else:
                # Keep the original outward-facing label if no obstacle-free choice exists.
                selected=copy.deepcopy(candidates[0]); chosen.append(selected); endpoints[net].append(pt(*sx.find(selected,'at')[0][1:3])); pin_nodes.add(endpoints[net][-1]);terminals[net].add(endpoints[net][-1])
        def route(start,goals,net):
            bounds=(x1+3,y1+15,x2-3,y2-3)
            def heuristic(p):return min(abs(p[0]-g[0])+abs(p[1]-g[1]) for g in goals)
            queue=[(heuristic(start),0,start,-1)];cost={(start,-1):0};prev={}
            goal_state=None
            while queue:
                _,g,p,di=heapq.heappop(queue);state=(p,di)
                if cost.get(state)!=g:continue
                if p in goals:goal_state=state;break
                mixed_here=any(k!=net for k in occupancy.get(p,{}))
                for ndi,(dx,dy) in enumerate(DIRS):
                    if mixed_here and ndi!=di:continue
                    q=(p[0]+dx,p[1]+dy)
                    if not(bounds[0]<=q[0]<=bounds[2] and bounds[1]<=q[1]<=bounds[3]):continue
                    if q in block:continue
                    others=[v for k,v in occupancy.get(q,{}).items() if k!=net]
                    if others and (len(others)>1 or others[0]=='B' or others[0]==('H' if dx else 'V')):continue
                    if others and di!=-1 and ndi!=di:continue
                    ng=g+1+(3 if di!=-1 and ndi!=di else 0)+(8 if others else 0)
                    ns=(q,ndi)
                    if ng<cost.get(ns,1e20):cost[ns]=ng;prev[ns]=state;heapq.heappush(queue,(ng+heuristic(q),ng,q,ndi))
            if goal_state is None:return None
            path=[];s=goal_state
            while True:
                path.append(s[0])
                if s not in prev:break
                s=prev[s]
            return path[::-1]
        failures=[]
        ordered=sorted(endpoints,key=lambda n:(n in ('GND','3V3','3V3_SENS','5V','VSYS','VX'),len(endpoints[n])))
        for net in ordered:
            points=list(dict.fromkeys(endpoints[net]));tree={points.pop(0)}
            while points:
                start=min(points,key=lambda p:min(abs(p[0]-g[0])+abs(p[1]-g[1]) for g in tree));points.remove(start)
                goals={p for p in tree if len(occupancy.get(p,{}))<=1 and p not in block}
                path=route(start,goals,net)
                if path is None:failures.append((net,start));continue
                for a,b in zip(path,path[1:]):edges[net].add(tuple(sorted((a,b))))
                tree.update(path);refresh()
        if failures:
            raise RuntimeError(f'Cannot complete local wiring in panel {panel}: {failures}')
        for net,ee in edges.items():
            graph=collections.defaultdict(set)
            for a,b in ee:graph[a].add(b);graph[b].add(a)
            # Remove escape-stub tails when a branch joins before the escape endpoint.
            leaves=[p for p,nb in graph.items() if len(nb)==1 and p not in terminals[net]]
            while leaves:
                p=leaves.pop()
                if len(graph[p])!=1 or p in terminals[net]:continue
                q=next(iter(graph[p]));graph[q].remove(p);graph[p].clear()
                if len(graph[q])==1 and q not in terminals[net]:leaves.append(q)
            # Prove all local terminals are joined by wire geometry, not merely net labels.
            reached=set(); pending=[next(iter(terminals[net]))]
            while pending:
                p=pending.pop()
                if p in reached:continue
                reached.add(p);pending.extend(graph[p]-reached)
            if not terminals[net].issubset(reached):
                raise RuntimeError(f'Disconnected local circuit {net} in {panel}')
            vertices={p for p,nb in graph.items() if nb and (p in pin_nodes or len(nb)!=2 or len({a[0] for a in nb})!=1 and len({a[1] for a in nb})!=1)}
            seen=set();segments=[]
            for p in vertices:
                for q in graph[p]:
                    edge=tuple(sorted((p,q)))
                    if edge in seen:continue
                    seen.add(edge);last=p;curr=q
                    while curr not in vertices:
                        nxt=next(z for z in graph[curr] if z!=last);seen.add(tuple(sorted((curr,nxt))));last,curr=curr,nxt
                    segments.append((p,curr))
                    added.append(['wire',['pts',['xy',*mm(p)],['xy',*mm(curr)]],['stroke',['width',0],['type','default']],['uuid',uid(project,'unit-wire',panel,net,p,curr)]])
            for p,nb in graph.items():
                if len(nb)>2:
                    if len(occupancy[p])>1:raise RuntimeError('Junction on crossing')
                    added.append(['junction',['at',*mm(p)],['diameter',0],['color',0,0,0,0],['uuid',uid(project,'unit-junction',panel,net,p)]])
            if not any(sx.text(n[1])==net for n in chosen):
                # Plain local label preserves the net name without a wide flag.
                # A global label is necessary to retain across-unit net names.
                from gen_schematic import glabel
                p=endpoints[net][0]
                chosen.append(glabel(net,*mm(p),0,'left',uid(project,'unit-label',panel,net)))
        added.extend(chosen)
        report.append({'panel':panel,'parts':refs,'nets':len(endpoints),'connected_branches':sum(max(0,len(set(v))-1) for v in endpoints.values())})
    result=[n for n in sch if id(n) not in remove]+added
    print('Connected functional units:',report)
    return result
