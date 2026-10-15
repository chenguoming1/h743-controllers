#!/usr/bin/env python3
"""Guarded, source-bound mechanical transaction; no native runtime or routing.
Writes only a new output directory and exact rollback there. Never edits inputs.
Preserves every track/via, connected-pad UUID/net, other footprint and board rule.
Cached zone fill is invalidated. Copper reconnection/refill and native checks are REQUIRED.
"""
import argparse,copy,hashlib,json,shutil,uuid
# All assertion guards remain active; optimized Python is explicitly unsupported.
if not __debug__:
    raise SystemExit("Refusing optimized Python: run this guarded transaction without -O/-OO.")
from pathlib import Path
import sexpr as s
import header_interface_geometry as g
HERE=Path(__file__).parent
NS=uuid.UUID('76fc26ee-25f2-483d-9fd7-5600b86b9fd9')
Q=lambda x:('s',str(x))
F=lambda x:f'{x:.6f}'.rstrip('0').rstrip('.') or '0'

def sha(data):return hashlib.sha256(data).hexdigest()
def first(n,k):return s.find(n,k)[0]
def ref(n):return next(s.text(p[2]) for p in s.find(n,'property') if s.text(p[1])=='Reference')
def norm(n):return s.dump(n)
def uid(n):return s.text(first(n,'uuid')[1])
def at(n):return [float(x) for x in first(n,'at')[1:3]]
def spans(raw):
    depth=0;start=None;quoted=False;escape=False
    for i,c in enumerate(raw):
        if quoted:
            if escape:escape=False
            elif c=='\\':escape=True
            elif c=='"':quoted=False
            continue
        if c=='"':quoted=True
        elif c=='(':
            depth+=1
            if depth==2:start=i
        elif c==')':
            if depth==2:yield start,i+1
            depth-=1
    assert depth==0 and not quoted

def body(raw):return [(a,b,s.parse(raw[a:b])) for a,b in spans(raw)]
def immutable_signature(board):
    # Empty NPTH mechanical pads are intentionally removed; all connected pad identities are fixed.
    return sorted((ref(fp),uid(p),s.text(p[1]),norm(first(p,'net'))) for fp in s.find(board,'footprint') for p in s.find(fp,'pad') if s.find(p,'net'))
def edge(n):return n[0] in ('gr_line','gr_arc') and s.text(first(n,'layer')[1])=='Edge.Cuts'
def bottom(n):
    return edge(n) and all(float(first(n,k)[2])>=108.4-1e-8 for k in ('start','end')) and n[0]=='gr_line'

def guard(raw,which,anchors):
    b=s.parse(raw)
    if which=='main':
        fp=next(f for f in s.find(b,'footprint') if ref(f)=='J1')
        assert sha(norm(fp).encode())==anchors['main_J1'], 'Main J1 differs from reviewed r54 anchor'
        edges=[norm(n) for n in b if isinstance(n,list) and edge(n)]
        assert sha(json.dumps(edges).encode())==anchors['main_outline'], 'Main outline changed'
        for z in s.find(b,'zone'):
            if s.find(z,'keepout'):
                assert anchors['main_slot_keepouts'].get(uid(z))==sha(norm(z).encode()), 'Main slot keepout differs from reviewed anchor'
        assert {uid(z) for z in s.find(b,'zone') if s.find(z,'keepout')}==set(anchors['main_slot_keepouts'])
    else:
        assert {ref(f):sha(norm(f).encode()) for f in s.find(b,'footprint')}==anchors['child_footprints'], 'Child footprint/contact baseline changed'
        edges=[norm(n) for n in b if isinstance(n,list) and edge(n)]
        assert sha(json.dumps(edges).encode())==anchors['child_outline'], 'Child outline changed'
    return b

def patch(raw,which):
    replacement=[];changed=[];fill_count=0;bottom_count=0
    inner={num:(net,x,w) for num,net,x,w in g.inner_pads_main()}
    old_contacts=[];new_contacts=[]
    for a,b,n in body(raw):
        original=copy.deepcopy(n);reason=None
        if n[0]=='footprint' and ((which=='main' and ref(n)=='J1') or (which=='child' and ref(n)!='J1')):
            r=ref(n)
            for p in s.find(n,'pad'):
                if s.find(p,'net'):old_contacts.append({'ref':r,'pad_uuid':uid(p),'net':s.text(first(p,'net')[-1]),'footprint_at':at(n),'pad_at':at(p),'size':[float(v) for v in first(p,'size')[1:3]],'layers':[s.text(v) for v in first(p,'layers')[1:]]})
            if which=='main':
                n[:]=[e for e in n if not(isinstance(e,list) and e[0]=='pad' and s.text(e[2])=='np_thru_hole')]
                for p in s.find(n,'pad'):
                    num=s.text(p[1]);strip=at(p)[1]<2.4
                    if strip:x=5.6 if num=='1' else 16.8;y=.675;w=9.8;h=.65
                    else:net,x,w=inner[num];y=4.225;h=.85;assert s.text(first(p,'net')[-1])==net
                    first(p,'at')[1:3]=[F(x),F(y)];first(p,'size')[1:3]=[F(w),F(h)]
                for si,(cx,cy) in enumerate(g.SLOT_CENTERS):
                    for gi,shape in enumerate(g.rounded_slot(cx,cy)):
                        n.append(s.parse(g.kicad_shape(shape,uid=str(uuid.uuid5(NS,f'main-slot-{si}-{gi}')))))
                first(n,'attr')[1:]=['smd']
                first(n,'descr')[1]=Q('UNFINISHED root-aware joint: two routed 10.0 x 2.1 mm R0.5 cutouts; moved full-width contacts; fixture and qualification required')
                first(n,'model')[1]=Q('${KIPRJMOD}/library/NexusFC.3dshapes/'+g.MODEL_FILE)
            else:
                p=first(n,'pad');net=s.text(first(p,'net')[-1]);strip=r.startswith('K')
                if strip:
                    x=5.6 if net=='GND' else 16.8;w=g.CHILD_STRIP_WIDTH
                    n[1]=Q('NexusFC:ChildBoard_TabStrip_W7.892')
                    first(n,'descr')[1]=Q('UNFINISHED root-aware child outer-face strip, 7.892 mm wide, 2.346 mm tall')
                else:
                    _,xm,w=next(v for v in inner.values() if v[0]==net);x=round(g.WIDTH-xm,6)
                first(n,'at')[1:3]=[F(100+x),'108.4']
                first(p,'at')[1:3]=['0','1.173'];first(p,'size')[1:3]=[F(w),'2.346']
            for p in s.find(n,'pad'):
                if s.find(p,'net'):new_contacts.append({'ref':r,'pad_uuid':uid(p),'net':s.text(first(p,'net')[-1]),'footprint_at':at(n),'pad_at':at(p),'size':[float(v) for v in first(p,'size')[1:3]],'layers':[s.text(v) for v in first(p,'layers')[1:]]})
            reason='mating contacts and routed cutouts' if which=='main' else 'tab contact position/size'
        elif which=='child' and bottom(n):
            bottom_count+=1
            if bottom_count==1:
                replacement.append((a,b,'\n\t'.join(g.kicad_shape(shape,'gr',(100,108.4),str(uuid.uuid5(NS,f'child-bottom-{i}'))) for i,shape in enumerate(g.tab_outline()))))
            else:replacement.append((a,b,''))
            changed.append({'uuid':uid(n),'reason':'replace sharp-root tab contour with R0.5 relief contour'});continue
        elif which=='main' and n[0]=='zone' and s.find(n,'keepout'):
            pts=first(first(n,'polygon'),'pts')
            coords=[tuple(map(float,p[1:3])) for p in s.find(pts,'xy')]
            cx=(min(p[0] for p in coords)+max(p[0] for p in coords))/2
            x0=cx-g.SLOT_LENGTH/2-g.SLOT_ROUTE_KEEPOUT_X;x1=cx+g.SLOT_LENGTH/2+g.SLOT_ROUTE_KEEPOUT_X
            y0=100+2.4-g.SLOT_WIDTH/2-g.SLOT_ROUTE_KEEPOUT_Y;y1=100+2.4+g.SLOT_WIDTH/2+g.SLOT_ROUTE_KEEPOUT_Y
            pts[1:]=[['xy',F(x),F(y)] for x,y in ((x0,y0),(x1,y0),(x1,y1),(x0,y1))]
            reason='expand slot keepout vertically; preserve stricter original lateral bounds and all rule permissions'
        elif n[0]=='zone':
            cached=[x for x in n if isinstance(x,list) and x[0] in ('filled_polygon','fill_segments')]
            if cached:
                fill_count+=len(cached);n[:]=[x for x in n if x not in cached];reason='invalidate stale zone-fill cache; refill required'
        if reason:
            replacement.append((a,b,s.dump(n,1)));changed.append({'uuid':uid(n),'reason':reason})
    if which=='child':assert bottom_count==9, bottom_count
    out=raw
    for a,b,v in reversed(replacement):out=out[:a]+v+out[b:]
    old=s.parse(raw);new=s.parse(out)
    assert immutable_signature(old)==immutable_signature(new),'Pad UUID/net/pin identity changed'
    for typ in ('segment','via','setup','general','net'):
        assert s.find(old,typ)==s.find(new,typ),f'{typ} changed'
    for fp in s.find(old,'footprint'):
        if (which=='main' and ref(fp)!='J1') or (which=='child' and ref(fp)=='J1'):
            assert fp==next(f for f in s.find(new,'footprint') if ref(f)==ref(fp))
    if which=='main':assert [n for n in old if isinstance(n,list) and edge(n)]==[n for n in new if isinstance(n,list) and edge(n)]
    return out,{'changed_nodes':changed,'invalidated_cached_fill_polygons':fill_count,'old_contacts':old_contacts,'new_contacts':new_contacts,'tracks_vias_rules_other_footprints_unchanged':True}

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    for a in ('main','child','child-schematic','expect-main','expect-child','expect-child-schematic','out'):ap.add_argument('--'+a,required=True)
    args=ap.parse_args();out=Path(args.out).resolve();assert not out.exists(),'Output must not exist; use a new experiment directory'
    paths={'main':Path(args.main),'child':Path(args.child),'child-schematic':Path(args.child_schematic)}
    data={k:p.read_bytes() for k,p in paths.items()};expected={'main':args.expect_main,'child':args.expect_child,'child-schematic':args.expect_child_schematic}
    for k in data:assert sha(data[k])==expected[k],f'{k} source hash mismatch'
    anchors=json.loads((HERE/'header_interface_r54_anchors.json').read_text())
    for which in ('main','child'):guard(data[which].decode(),which,anchors)
    sch=data['child-schematic'].decode();old='NexusFC:ChildBoard_TabStrip_W9.8';new='NexusFC:ChildBoard_TabStrip_W7.892';assert sch.count(old)==2
    out.mkdir(parents=True);rollback=out/'rollback';rollback.mkdir()
    for k,p in paths.items():(rollback/p.name).write_bytes(data[k])
    package = HERE.parent
    bound_files = [HERE/name for name in ('apply_header_interface.py','header_interface_geometry.py','header_interface_r54_anchors.json','sexpr.py','make_footprints.py','build_header_board.py','design_header.py','pcbutil.py','route_board.py')]
    bound_files += sorted((package/'hardware/library/NexusFC.pretty').glob('ChildBoard_*.kicad_mod'))
    bound_files += [package/'hardware/library/NexusFC.pretty/HeaderBoard_Joint.kicad_mod', package/'hardware/library/NexusFC.pretty/Header_3x07_P2.54_Vertical_Servo.kicad_mod']
    package_binding = {str(p.relative_to(package)):sha(p.read_bytes()) for p in bound_files}
    (out/'source-manifest.json').write_text(json.dumps({'implementation_sha256':package_binding,'status':'UNFINISHED mechanical-only transaction; routing/refill/native/3D checks required','sources':{k:{'path':str(p.resolve()),'sha256':sha(data[k])} for k,p in paths.items()}},indent=2)+'\n')
    report={};dest={'main':out/'nexus-style-fc.kicad_pcb','child':out/'header-board/nexus-header-board.kicad_pcb'}
    for which in ('main','child'):
        text,r=patch(data[which].decode(),which);dest[which].parent.mkdir(parents=True,exist_ok=True);dest[which].write_text(text);report[which]=dict(r,output_sha256=sha(text.encode()))
    (out/'header-board/nexus-header-board.kicad_sch').write_text(sch.replace(old,new))
    report['child_schematic']='Only two footprint identifier properties updated; all other bytes, wires and pin assignments identical'
    (out/'transaction-report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'out':str(out),'main':report['main']['output_sha256'],'child':report['child']['output_sha256']}))
if __name__=='__main__':main()
