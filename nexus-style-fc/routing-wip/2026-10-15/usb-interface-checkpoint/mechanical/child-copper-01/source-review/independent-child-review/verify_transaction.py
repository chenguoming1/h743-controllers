"""Independent read-only analytic geometry check; writes reports only beside itself.

No native KiCad, source writes, regeneration, routing or refill. Two-dimensional
nominal geometry uses Euclidean distances, with exact line/circle/rectangle
primitives and circular Edge.Cuts arcs. Stored zone fills are separately screened
as polygons; no connectivity conclusion depends on those stale fills.
"""
from pathlib import Path
import sys,json,hashlib,math,itertools,collections
sys.dont_write_bytecode=True
ROOT=Path('/workspace/scratch/8a35c1f26232')
HERE=Path(__file__).resolve().parent
PROPOSAL=HERE.parent
sys.path.insert(0,str(ROOT/'nexus-header-redesign-20261015/candidate-02/nexus-style-fc/tools'))
import sexpr as s
P=json.loads((PROPOSAL/'complete-transaction.json').read_text())
I=json.loads((PROPOSAL/'complete-net-inventory.json').read_text())
SOURCE=Path(P['source']['path']); raw=SOURCE.read_bytes(); digest=hashlib.sha256(raw).hexdigest()
assert digest==P['source']['sha256']==I['source_sha256']=='de56d5e4a066ff03a8c16d7e0501f45ca651ebf177c45ba12667488162010f38'
b=s.parse(raw.decode())
EPS=1e-9
def one(n,k): return s.find(n,k)[0]
def xy(n,k): return tuple(map(float,one(n,k)[1:3]))
def uid(n): return s.text(one(n,'uuid')[1])
def net(n): return s.text(one(n,'net')[-1]) if s.find(n,'net') else ''
def ref(n): return next(s.text(p[2]) for p in s.find(n,'property') if s.text(p[1])=='Reference')
def add(a,b):return (a[0]+b[0],a[1]+b[1])
def sub(a,b):return (a[0]-b[0],a[1]-b[1])
def mul(a,k):return (a[0]*k,a[1]*k)
def dot(a,b):return a[0]*b[0]+a[1]*b[1]
def cross(a,b):return a[0]*b[1]-a[1]*b[0]
def norm(a):return math.hypot(*a)
def pointseg(p,a,b):
    d=sub(b,a); den=dot(d,d)
    return norm(sub(p,add(a,mul(d,max(0.,min(1.,dot(sub(p,a),d)/den)))))) if den else norm(sub(p,a))
def segseg(a,b,c,d):
    ab=sub(b,a);cd=sub(d,c);den=cross(ab,cd)
    if abs(den)>EPS:
        t=cross(sub(c,a),cd)/den;u=cross(sub(c,a),ab)/den
        if -EPS<=t<=1+EPS and -EPS<=u<=1+EPS:return 0.
    return min(pointseg(a,c,d),pointseg(b,c,d),pointseg(c,a,b),pointseg(d,a,b))
def polyedges(v):return list(zip(v,v[1:]+v[:1]))
def inpoly(p,v):
    if min(pointseg(p,a,b) for a,b in polyedges(v))<=EPS:return True
    inside=False
    for a,b in polyedges(v):
        if (a[1]>p[1]) != (b[1]>p[1]) and p[0]<(b[0]-a[0])*(p[1]-a[1])/(b[1]-a[1])+a[0]:inside=not inside
    return inside
def segpoly(a,b,v):
    if inpoly(a,v) or inpoly(b,v):return 0.
    return min(segseg(a,b,c,d) for c,d in polyedges(v))
def polypoly(v,w):
    if inpoly(v[0],w) or inpoly(w[0],v):return 0.
    return min(segseg(a,b,c,d) for a,b in polyedges(v) for c,d in polyedges(w))
def distance(a,b):
    # Capsule/point-circle: segment base + radius; rectangle/polygon: vertex list.
    if 'vertices' in a and 'vertices' in b:return polypoly(a['vertices'],b['vertices'])
    if 'vertices' in a:a,b=b,a
    if 'vertices' in b:return segpoly(a['a'],a['b'],b['vertices'])-a['radius']
    return segseg(a['a'],a['b'],b['a'],b['b'])-a['radius']-b['radius']
def capsule(kind,n,a,c,r,layers,**kw):return dict(kind=kind,uuid=uid(n),net=net(n),a=a,b=c,radius=r,layers=set(layers),**kw)
def segment(n):return capsule('segment',n,xy(n,'start'),xy(n,'end'),float(one(n,'width')[1])/2,[s.text(one(n,'layer')[1])])
def label(x):return {'kind':x['kind'],'uuid':x['uuid'],'net':x['net'],**({'reference':x['reference'],'number':x['number']} if x['kind']=='pad' else {})}
def layers(n):
    v=[s.text(x) for x in one(n,'layers')[1:]]
    return {'F.Cu','B.Cu'} if '*.Cu' in v else {x for x in v if x.endswith('.Cu')}
original_segments={uid(n):n for n in s.find(b,'segment')};donor_ids=set();replacements=[];guards=[]
all_existing_uuids=set()
def collect_uuids(n):
    for x in n:
        if isinstance(x,list):
            if x and x[0]=='uuid':all_existing_uuids.add(s.text(x[1]))
            collect_uuids(x)
collect_uuids(b)
for route in P['routes']:
    nn=route['net'];expected=.5 if nn in ('GND','VX') else .2
    assert route['original_width_mm']==expected
    for d in route['source_donor_segments']:
        assert d['uuid'] not in donor_ids;donor_ids.add(d['uuid'])
        n=original_segments[d['uuid']]
        assert s.parse(d['native_record'])==n
        assert net(n)==nn and s.text(one(n,'layer')[1])=='B.Cu' and float(one(n,'width')[1])==expected
        assert xy(n,'start')==tuple(d['start']) and xy(n,'end')==tuple(d['end'])
    for v in route['replacement_segments']:
        n=s.parse(v['native_record']);q=segment(n)
        assert q['uuid']==v['uuid'] and q['net']==v['net']==nn and q['layers']=={'B.Cu'}
        assert q['radius']*2==v['width']==expected and q['a']==tuple(v['start']) and q['b']==tuple(v['end'])
        if v['uuid'] not in donor_ids:assert v['uuid'] not in all_existing_uuids
        replacements.append(q)
    guards.append({'net':nn,'exact_donor_native_records':True,'original_width_preserved_mm':expected,'replacement_count':len(route['replacement_segments'])})
assert len(donor_ids)==6 and len(replacements)==9 and len({x['uuid'] for x in replacements})==9
retained=[segment(n) for u,n in original_segments.items() if u not in donor_ids]
segments=retained+replacements
assert len(original_segments)==P['expected_segment_count_before']==70 and len(segments)==P['expected_segment_count_after']==73
pads=[];drills=[];pad_native={}
for f in s.find(b,'footprint'):
    at=one(f,'at');assert len(at)==3 or abs(float(at[3]))<EPS
    for p in s.find(f,'pad'):
        atp=one(p,'at');assert len(atp)==3 or abs(float(atp[3]))<EPS
        center=add(xy(f,'at'),xy(p,'at'));w,h=xy(p,'size');ll=layers(p);shape=s.text(p[3]);r=ref(f)
        if shape=='rect':
            x,y=center;q=dict(kind='pad',uuid=uid(p),net=net(p),layers=ll,vertices=[(x-w/2,y-h/2),(x+w/2,y-h/2),(x+w/2,y+h/2),(x-w/2,y+h/2)],reference=r,number=s.text(p[1]),center=center)
        elif shape=='circle':
            assert abs(w-h)<EPS;q=capsule('pad',p,center,center,w/2,ll,reference=r,number=s.text(p[1]),center=center)
        else:raise AssertionError('Unsupported pad shape '+shape)
        pads.append(q);pad_native[uid(p)]=(p,center,r)
        if s.find(p,'drill'):
            d=one(p,'drill');assert len(d)==2
            drills.append(capsule('drill',p,center,center,float(d[1])/2,['F.Cu','B.Cu'],reference=r,number=s.text(p[1])))
vias=[]
for v in s.find(b,'via'):
    q=capsule('via',v,xy(v,'at'),xy(v,'at'),float(one(v,'size')[1])/2,layers(v));vias.append(q)
    drills.append(capsule('drill',v,xy(v,'at'),xy(v,'at'),float(one(v,'drill')[1])/2,['F.Cu','B.Cu']))
inventory_checks=[]
for nn,d in I['nets'].items():
    pp=[p for p in pads if p['net']==nn]
    assert {x['uuid'] for x in pp}=={x['uuid'] for x in d['pads']}
    for rec in d['pads']:
        native,center,r=pad_native[rec['uuid']]
        assert s.parse(rec['native_record'])==native and rec['ref']==r and norm(sub(center,rec['center']))<EPS
    for kind,native in [('segments',s.find(b,'segment')),('vias',s.find(b,'via'))]:
        actual={uid(n):n for n in native if net(n)==nn};assert set(actual)=={x['uuid'] for x in d[kind]}
        for rec in d[kind]:assert s.parse(rec['native_record'])==actual[rec['uuid']]
    inventory_checks.append({'net':nn,'pad_count':len(pp),'complete_pad_segment_via_uuid_and_native_records':True})
assert sum(x['pad_count'] for x in inventory_checks)==22
items=segments+pads+vias
connectivity=[]
for nn in I['nets']:
    objects=[x for x in items if x['net']==nn];parent=list(range(len(objects)))
    def root(i):
        while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
        return i
    for i,a in enumerate(objects):
        for j in range(i):
            o=objects[j]
            if a['layers']&o['layers'] and distance(a,o)<=EPS:parent[root(i)]=root(j)
    comp=collections.defaultdict(list)
    for i,a in enumerate(objects):comp[root(i)].append(a)
    padcomps=[[label(x) for x in c if x['kind']=='pad'] for c in comp.values() if any(x['kind']=='pad' for x in c)]
    connectivity.append({'net':nn,'all_physical_pads_connected':len(padcomps)==1,'pad_count':sum(len(x) for x in padcomps),'pad_components':padcomps,'all_copper_component_count_excluding_zones':len(comp),'zone_fill_needed_for_proof':False})
ports=[];terminals=[]
for route in P['routes']:
    nn=route['net'];donors=[segment(original_segments[x['uuid']]) for x in route['source_donor_segments']]
    new=[x for x in replacements if x['net']==nn];contacts=[]
    for o in retained+pads+vias:
        hits=[d for d in donors if d['layers']&o['layers'] and distance(d,o)<=EPS]
        if hits:
            newhits=[n for n in new if n['layers']&o['layers'] and distance(n,o)<=EPS]
            contacts.append({'external_object':label(o),'original_donor_contacts':[d['uuid'] for d in hits],'replacement_contacts':[n['uuid'] for n in newhits],'same_net':o['net']==nn,'preserved_direct_contact':bool(newhits)})
    endpoints=[]
    for d in donors:
        for name,p in [('start',d['a']),('end',d['b'])]:
            cap=dict(d,a=p,b=p)
            endpoints.append({'donor_uuid':d['uuid'],'endpoint':name,'point':p,'external_contacts':[label(o) for o in retained+pads+vias if cap['layers']&o['layers'] and distance(cap,o)<=EPS]})
    ports.append({'net':nn,'all_original_external_contacts':contacts,'all_same_net_external_contacts_preserved':all(x['preserved_direct_contact'] for x in contacts if x['same_net']),'foreign_nonzone_original_contacts':[x for x in contacts if not x['same_net']],'original_endpoint_contacts':endpoints})
    t=route['terminal_port'];pad=next(x for x in pads if x['uuid']==t['pad_uuid']);endpoint=new[-1]['b'];radius=new[-1]['radius']
    assert pad['reference']==t['reference'] and pad['number']==t['pad_number'] and norm(sub(endpoint,pad['center']))<EPS
    x,y=endpoint;v=pad['vertices'];min_side=min(x-v[0][0],v[1][0]-x,y-v[0][1],v[2][1]-y)
    terminals.append({'net':nn,'pad':label(pad),'endpoint':endpoint,'center_matches':True,'trace_width_mm':2*radius,'endpoint_disk_inside_pad':min_side-radius>=-EPS,'minimum_endpoint_disk_to_pad_boundary_mm':min_side-radius})
# Exact circular-arc edge distance, including limited sweep and segment-circle intersection.
def arc(n):
    a,m,c=xy(n,'start'),xy(n,'mid'),xy(n,'end');v=sub(m,a);w=sub(c,a);den=2*cross(v,w)
    ox=(dot(v,v)*w[1]-dot(w,w)*v[1])/den;oy=(v[0]*dot(w,w)-w[0]*dot(v,v))/den;o=add(a,(ox,oy));r=norm(sub(a,o))
    angle=lambda p:math.atan2(p[1]-o[1],p[0]-o[0]);start=angle(a);sweep=(angle(c)-start)%(2*math.pi)
    if (angle(m)-start)%(2*math.pi)>sweep:start=angle(c);sweep=(angle(a)-start)%(2*math.pi)
    return dict(a=a,b=c,o=o,r=r,start=start,sweep=sweep,uuid=uid(n))
def onarc(p,e):return (math.atan2(p[1]-e['o'][1],p[0]-e['o'][0])-e['start'])%(2*math.pi)<=e['sweep']+1e-8
def pointarc(p,e):
    ans=min(norm(sub(p,e['a'])),norm(sub(p,e['b'])))
    if onarc(p,e):ans=min(ans,abs(norm(sub(p,e['o']))-e['r']))
    return ans
def segarc(a,b,e):
    ans=min(pointarc(a,e),pointarc(b,e),pointseg(e['a'],a,b),pointseg(e['b'],a,b))
    d=sub(b,a);dd=dot(d,d)
    if dd:
        t=dot(sub(e['o'],a),d)/dd
        if 0<=t<=1:
            p=add(a,mul(d,t));v=sub(p,e['o']);vn=norm(v)
            if vn>EPS:
                for sign in (1,-1):
                    candidate=add(e['o'],mul(v,sign*e['r']/vn))
                    if onarc(candidate,e):ans=min(ans,norm(sub(p,candidate)))
        z=sub(a,e['o']);bb=2*dot(z,d);cc=dot(z,z)-e['r']**2;disc=bb*bb-4*dd*cc
        if disc>=-EPS:
            for t in ((-bb-math.sqrt(max(0.,disc)))/(2*dd),(-bb+math.sqrt(max(0.,disc)))/(2*dd)):
                if -EPS<=t<=1+EPS and onarc(add(a,mul(d,t)),e):return 0.
    return ans
edges=[]
for n in b:
    if isinstance(n,list) and n[0] in ('gr_line','gr_arc') and s.text(one(n,'layer')[1])=='Edge.Cuts':edges.append(dict(kind=n[0],**(arc(n) if n[0]=='gr_arc' else dict(a=xy(n,'start'),b=xy(n,'end'),uuid=uid(n)))))
def insideboard(p):
    x,y=p
    if 100-EPS<=x<=122.4+EPS and 100-EPS<=y<=108.4+EPS:
        for cx in (100.5,121.9):
            if y<100.5 and ((cx==100.5 and x<cx) or (cx==121.9 and x>cx)) and math.hypot(x-cx,y-100.5)>.500002:return False
        for cx in (100.9,110.3,112.1,121.5):
            if math.hypot(x-cx,y-108.4)<.5-EPS:return False
        return True
    return 108.4-EPS<=y<=111+EPS and (101.4-EPS<=x<=109.8+EPS or 112.6-EPS<=x<=121+EPS)
def edge_clearance(o):
    base=polyedges(o['vertices']) if 'vertices' in o else [(o['a'],o['b'])];rr=o.get('radius',0.)
    pairs=[((segarc(a,c,e) if e['kind']=='gr_arc' else segseg(a,c,e['a'],e['b']))-rr,e['uuid']) for a,c in base for e in edges]
    value,eid=min(pairs)
    inside=all(insideboard(p) for a,c in base for p in (a,c))
    return value if inside else -abs(value),eid,inside
def min_clearance(objects,others,mode='foreign'):
    out=[]
    for a in objects:
        candidates=[(distance(a,o),o) for o in others if a['uuid']!=o['uuid'] and a['layers']&o['layers'] and (mode!='foreign' or a['net']!=o['net'])]
        if not candidates:continue
        val,obj=min(candidates,key=lambda z:z[0]);out.append({'object':label(a),'clearance_mm':val,'nearest':label(obj)})
    return sorted(out,key=lambda z:z['clearance_mm'])
all_edges=[]
for o in items:
    val,edgeid,inside=edge_clearance(o);all_edges.append({'object':label(o),'clearance_mm':val,'nearest_edge_uuid':edgeid,'base_points_inside_outline':inside})
all_edges.sort(key=lambda x:x['clearance_mm']);new_ids={x['uuid'] for x in replacements}
new_copper=min_clearance(replacements,items);new_drill=min_clearance(replacements,drills)
full_copper=min_clearance(items,items);full_drill=min_clearance(items,drills)
fills=[]
for z in s.find(b,'zone'):
    for i,f in enumerate(s.find(z,'filled_polygon')):
        vertices=[tuple(map(float,x[1:3])) for x in s.find(one(f,'pts'),'xy')]
        fills.append(dict(kind='stored_zone_fill',uuid=uid(z)+':'+str(i),net=net(z),layers={s.text(one(f,'layer')[1])},vertices=vertices))
fill_screen=min_clearance(replacements,fills)
ground_fill_contacts=[]
for route in P['routes']:
    nn=route['net'];donors=[segment(original_segments[x['uuid']]) for x in route['source_donor_segments']];new=[x for x in replacements if x['net']==nn]
    for f in fills:
        if f['net']==nn and any(d['layers']&f['layers'] and distance(d,f)<=EPS for d in donors):
            ground_fill_contacts.append({'net':nn,'fill':label(f),'old_donor_touch':True,'replacement_still_touches_stored_fill':any(n['layers']&f['layers'] and distance(n,f)<=EPS for n in new)})
project=json.loads(SOURCE.with_suffix('.kicad_pro').read_text());rules=project['board']['design_settings']['rules'];floors={k:rules[k] for k in ('min_clearance','min_copper_edge_clearance','min_hole_clearance')}
report={
 'status':'PASS for independent nominal retained-copper geometry and connectivity; NOT native DRC sign-off. Stored zone fill collisions make native refill mandatory.',
 'method':__doc__, 'source':{'path':str(SOURCE),'sha256_before':digest},'proposal_sha256':hashlib.sha256((PROPOSAL/'complete-transaction.json').read_bytes()).hexdigest(),
 'guards':guards,'scope_counts':{'donors_removed':6,'replacement_segments':9,'segments_before':70,'segments_after':73,'vias_before_and_after':len(vias),'affected_net_physical_pads':22},
 'inventory':inventory_checks,'connectivity_without_zones':connectivity,'original_external_contacts':ports,'terminal_contact':terminals,
 'project_floors_mm':floors,
 'replacement_edge_clearances':sorted([x for x in all_edges if x['object']['uuid'] in new_ids],key=lambda x:x['clearance_mm']),
 'replacement_foreign_nonzone_copper_clearances':new_copper,'replacement_foreign_drill_clearances':new_drill,
 'whole_board_nonzone_minimums':{'edge':all_edges[0],'foreign_copper':full_copper[0],'foreign_drill':full_drill[0]},
 'whole_board_nonzone_violations':{'edge':[x for x in all_edges if x['clearance_mm']<.254-1e-7],'foreign_copper':[x for x in full_copper if x['clearance_mm']<.15-1e-7],'foreign_drill':[x for x in full_drill if x['clearance_mm']<.25-1e-7]},
 'stored_zone_fill_screen':{'status':'Stale pre-edit fills cannot be retained for final validation; refill required. No connectivity proof relies on zones.','replacement_to_foreign_fill':fill_screen,'same_net_original_fill_contacts':ground_fill_contacts},
 'limitations':['Native zone refill, all-visible native DRC/ERC/parity and manufactured tolerances are not evaluated.','Copper shapes are nominal and finite-precision; comparisons allow 0.0000001 mm numerical tolerance.','Stored fill polygons are screened literally; no refill is attempted.'],
}
report['source']['sha256_after']=hashlib.sha256(SOURCE.read_bytes()).hexdigest();assert digest==report['source']['sha256_after']
assert all(x['all_physical_pads_connected'] for x in connectivity)
assert all(x['all_same_net_external_contacts_preserved'] and not x['foreign_nonzone_original_contacts'] for x in ports)
assert all(x['endpoint_disk_inside_pad'] for x in terminals)
assert all(x['clearance_mm']>=.254-1e-7 for x in report['replacement_edge_clearances'])
assert all(x['clearance_mm']>=.15-1e-7 for x in new_copper)
assert all(x['clearance_mm']>=.25-1e-7 for x in new_drill)
assert all(not v for v in report['whole_board_nonzone_violations'].values())
(HERE/'independent-review.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'status':report['status'],'pad_connectivity':[(x['net'],x['pad_count'],x['all_physical_pads_connected']) for x in connectivity],'minimum_replacement_edge_mm':report['replacement_edge_clearances'][0]['clearance_mm'],'minimum_replacement_foreign_copper_mm':new_copper[0]['clearance_mm'],'minimum_replacement_foreign_drill_mm':new_drill[0]['clearance_mm'],'whole_board_nonzone_violations':{k:len(v) for k,v in report['whole_board_nonzone_violations'].items()},'report':str(HERE/'independent-review.json')},indent=2))
