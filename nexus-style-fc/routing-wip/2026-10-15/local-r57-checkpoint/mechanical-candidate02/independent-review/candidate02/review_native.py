#!/usr/bin/env python3
"""Read-only Python/text review. Does not invoke KiCad or edit candidate files."""
import os,sys,json,hashlib,math,collections,copy
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path('/workspace/scratch/8a35c1f26232/nexus-header-redesign-20261015')
C=ROOT/'candidate-02/nexus-style-fc';O=ROOT/'rollback-r54-source/nexus-style-fc';T=ROOT/'transaction-r54-03-candidate02'
sys.path.insert(0,str(C/'tools'))
import sexpr as s
import apply_header_interface as apply
import make_footprints as mf
import design_header as dh

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def find(n,k):return s.find(n,k)
def one(n,k):return find(n,k)[0]
def text(v):return s.text(v)
def ref(fp):return next(text(x[2]) for x in find(fp,'property') if text(x[1])=='Reference')
def uuid(n):return text(one(n,'uuid')[1]) if find(n,'uuid') else None
def xy(n,k):return tuple(float(x) for x in one(n,k)[1:3])
def allnodes(n):
    if isinstance(n,list):
        yield n
        for child in n:yield from allnodes(child)
def norm(n):return s.dump(n)
def footprint_map(board):return {ref(fp):fp for fp in find(board,'footprint')}
def edge(n):return n[0] in ('gr_line','gr_arc','fp_line','fp_arc') and find(n,'layer') and text(one(n,'layer')[1])=='Edge.Cuts'
def pad_sig(p):return [text(p[1]),text(p[2]),text(p[3]),xy(p,'at'),tuple(float(x) for x in one(p,'size')[1:3]),tuple(text(x) for x in one(p,'layers')[1:])]
def circle(n):
    p,q,r=[xy(n,k) for k in ('start','mid','end')];(x1,y1),(x2,y2),(x3,y3)=p,q,r
    d=2*(x1*(y2-y3)+x2*(y3-y1)+x3*(y1-y2))
    cx=((x1*x1+y1*y1)*(y2-y3)+(x2*x2+y2*y2)*(y3-y1)+(x3*x3+y3*y3)*(y1-y2))/d
    cy=((x1*x1+y1*y1)*(x3-x2)+(x2*x2+y2*y2)*(x1-x3)+(x3*x3+y3*y3)*(x2-x1))/d
    return [cx,cy,math.hypot(x1-cx,y1-cy)]
def contour_summary(edges):
    ends=collections.defaultdict(list)
    for i,n in enumerate(edges):
        for k in ('start','end'):ends[xy(n,k)].append(i)
    todo=set(range(len(edges)));comps=[]
    while todo:
        stack=[todo.pop()];group=[]
        while stack:
            i=stack.pop();group.append(i)
            for k in ('start','end'):
                for j in ends[xy(edges[i],k)]:
                    if j in todo:todo.remove(j);stack.append(j)
        coords=[xy(edges[i],k) for i in group for k in ('start','end')]
        arcs=[circle(edges[i]) for i in group if edges[i][0].endswith('arc')]
        comps.append({'edge_count':len(group),'bounds_endpoints':[min(x for x,y in coords),min(y for x,y in coords),max(x for x,y in coords),max(y for x,y in coords)],'arcs_center_radius':arcs})
    return {'edge_count':len(edges),'endpoint_degree_failures':{str(k):len(v) for k,v in ends.items() if len(v)!=2},'components':comps}
result={'status':'UNFINISHED candidate: text/geometry review only; no native DRC/ERC/refill/routing/3D validation','files':{},'boards':{}}
for p in sorted(C.rglob('*')):
    if p.is_file() and '__pycache__' not in p.parts:result['files'][str(p.relative_to(C))]=sha(p)
for which,rel in [('main','hardware/nexus-style-fc.kicad_pcb'),('child','hardware/header-board/nexus-header-board.kicad_pcb')]:
    op=O/rel;cp=C/rel;old=s.parse(op.read_text());new=s.parse(cp.read_text());ofs=footprint_map(old);nfs=footprint_map(new)
    b={'source_sha256':sha(op),'candidate_sha256':sha(cp),'top_level_counts':{k:len(find(new,k)) for k in ('footprint','segment','via','zone','gr_line','gr_arc','net')},'exact_unchanged':{},'changed_footprints':[]}
    for k in set(n[0] for n in old[1:] if isinstance(n,list))|set(n[0] for n in new[1:] if isinstance(n,list)):
        if k not in ('footprint','zone','gr_line','gr_arc'):b['exact_unchanged'][k]=find(old,k)==find(new,k)
    b['connected_pad_identity_exact']=apply.immutable_signature(old)==apply.immutable_signature(new)
    b['footprint_refs_exact']=set(ofs)==set(nfs)
    b['changed_footprints']=[r for r in ofs if ofs[r]!=nfs[r]]
    b['board_outer_contours']=contour_summary([n for n in new if isinstance(n,list) and edge(n)])
    ids=[uuid(n) for n in allnodes(new) if find(n,'uuid')]
    b['duplicate_uuids']=[u for u,count in collections.Counter(ids).items() if count>1]
    zones_old=copy.deepcopy(find(old,'zone'));zones_new=copy.deepcopy(find(new,'zone'))
    for z in zones_old:z[:]=[v for v in z if not(isinstance(v,list) and v[0] in ('filled_polygon','fill_segments'))]
    b['zones_only_cached_fill_removed']=zones_old==zones_new
    b['remaining_fill_polygons']=sum(len(find(z,'filled_polygon'))+len(find(z,'fill_segments')) for z in zones_new)
    guarded=apply.guard(op.read_text(),which,json.loads((C/'tools/header_interface_r54_anchors.json').read_text()))
    replay,rr=apply.patch(op.read_text(),which)
    b['in_memory_replay_equals_candidate']=replay.encode()==cp.read_bytes()
    tp=T/('nexus-style-fc.kicad_pcb' if which=='main' else 'header-board/nexus-header-board.kicad_pcb')
    b['candidate_equals_transaction']=cp.read_bytes()==tp.read_bytes()
    contacts={}
    for r,fp in nfs.items():
        if (which=='main' and r!='J1') or (which=='child' and r=='J1'):continue
        name=text(fp[1]).split(':')[-1];lib=s.parse((C/'hardware/library/NexusFC.pretty'/f'{name}.kicad_mod').read_text())
        ps=sorted([pad_sig(p) for p in find(fp,'pad')],key=str);pls=sorted([pad_sig(p) for p in find(lib,'pad')],key=str)
        es=[n for n in fp if isinstance(n,list) and edge(n)];els=[n for n in lib if isinstance(n,list) and edge(n)]
        def e_sig(n):return [n[0],xy(n,'start'),xy(n,'end')]+([xy(n,'mid')] if n[0].endswith('arc') else [])
        contacts[r]={'at':one(fp,'at')[1:],'library':name,'pads_match_library':ps==pls,'pads':ps,'edges_match_library':[e_sig(n) for n in es]==[e_sig(n) for n in els]}
        if which=='main':b['joint_cutouts']=contour_summary(es)
    b['contacts']=contacts
    if which=='main':b['outer_edges_exact']=find(old,'gr_line')==find(new,'gr_line') and find(old,'gr_arc')==find(new,'gr_arc')
    else:
        b['connector_unchanged_exact']=ofs['J1']==nfs['J1']
        b['design_header_placement_match']={p['ref']:xy(nfs[p['ref']],'at')==(round(100+p['place'][1],6),round(108.4+p['place'][2],6)) for p in dh.PARTS}
    result['boards'][which]=b
# Deterministic footprint library generation, entirely in memory.
libchecks={}
for name,fn in [('Header_3x07_P2.54_Vertical_Servo',mf.fp_header),('HeaderBoard_Joint',mf.fp_joint)]:
    lines=[];fn(lines);libchecks[name]=(C/'hardware/library/NexusFC.pretty'/f'{name}.kicad_mod').read_text()=='\n'.join(lines)+'\n'
for name,w in [('ChildBoard_TabPad_Sig',mf.SIG_W),('ChildBoard_TabPad_Pwr',mf.PWR_W)]:
    lines=[];mf.fp_tabpad(lines,name,w);libchecks[name]=(C/'hardware/library/NexusFC.pretty'/f'{name}.kicad_mod').read_text()=='\n'.join(lines)+'\n'
name='ChildBoard_TabStrip_W7.892';lines=[];mf.fp_tabstrip(lines,name,7.892);libchecks[name]=(C/'hardware/library/NexusFC.pretty'/f'{name}.kicad_mod').read_text()=='\n'.join(lines)+'\n'
result['library_generation_exact']=libchecks
# Electrical schematic exactness: only the two intended footprint identifier edits.
schrel='hardware/header-board/nexus-header-board.kicad_sch';old=(O/schrel).read_text();new=(C/schrel).read_text()
result['child_schematic_only_two_footprint_id_replacements']=old.count('NexusFC:ChildBoard_TabStrip_W9.8')==2 and old.replace('NexusFC:ChildBoard_TabStrip_W9.8','NexusFC:ChildBoard_TabStrip_W7.892')==new
result['main_schematic_byte_identical']=(O/'hardware/nexus-style-fc.kicad_sch').read_bytes()==(C/'hardware/nexus-style-fc.kicad_sch').read_bytes()
result['rules_project_files_identical']={str(p.relative_to(O)):p.read_bytes()==(C/p.relative_to(O)).read_bytes() for p in O.rglob('*') if p.suffix in ('.kicad_dru','.kicad_pro')}
result['candidate_new_model_exists']=(C/'hardware/library/NexusFC.3dshapes'/mf.hig.MODEL_FILE).exists()
print(json.dumps(result,indent=2))
