"""Source-only exact KiCad record checks; no native or geometry imports."""
import copy
from decimal import Decimal
import json
from pathlib import Path
import re, gzip, lzma


def require(ok, message):
    if not ok: raise ValueError(message)


def parse(path):
    stack=[]; root=None
    for match in re.finditer(r'\(|\)|"(?:\\.|[^"\\])*"|[^\s()]+', (lzma.open(path,'rt').read() if str(path).endswith('.xz') else gzip.open(path,'rt').read() if str(path).endswith('.gz') else Path(path).read_text())):
        token=match.group()
        if token=='(':
            node=[]
            if stack: stack[-1].append(node)
            stack.append(node)
        elif token==')':
            require(bool(stack),'Unbalanced source'); root=stack.pop()
        else:
            require(bool(stack),'Atom outside source root'); stack[-1].append(token)
    require(not stack and root and root[0]=='kicad_pcb','Invalid board source')
    return root


def children(node, kind): return [v for v in node if isinstance(v,list) and v and v[0]==kind]
def child(node,kind):
    rows=children(node,kind);require(len(rows)==1,'Expected one '+kind);return rows[0]
def uid(node): return json.loads(child(node,'uuid')[1])
def ref(node): return json.loads(next(v[2] for v in children(node,'property') if v[1]=='"Reference"'))
def canonical(node):
    if isinstance(node,list): return [canonical(x) for x in node]
    if node.startswith('"'): return ('s',json.loads(node))
    try: return ('n',str(Decimal(node).normalize()))
    except Exception: return ('a',node)
def equal(a,b):return canonical(a)==canonical(b)
def unordered(node):return sorted((json.dumps(canonical(x),sort_keys=True) for x in node))
def pose(node):
    a=child(node,'at');return [float(a[1]),float(a[2]),float(a[3])%360 if len(a)>3 else 0,json.loads(child(node,'layer')[1])]


def shifted_angle(record,delta):
    record=copy.deepcopy(record);rows=children(record,'at')
    require(len(rows)<=1,'Ambiguous local position')
    if rows:
        a=rows[0];angle=(Decimal(a[3]) if len(a)>3 else Decimal(0))+Decimal(str(delta));angle%=360
        if angle<0:angle+=360
        # Explicit zero and omitted zero are equivalent for native positions.
        a[:]=['at',a[1],a[2],str(angle)]
    return record


def normal_at(record):return shifted_angle(record,0)


def verify_raw_board(source_path,after_path,poses,cuts,adds,text_angle_normalizations=None):
    before=parse(source_path);after=parse(after_path)
    records=lambda root:{uid(n):n for n in root if isinstance(n,list) and children(n,'uuid')}
    a=records(before);b=records(after)
    text_ledger=[]
    if text_angle_normalizations:
        for fp_uuid, expected in text_angle_normalizations.items():
            require(fp_uuid in a and fp_uuid in b and a[fp_uuid][0]=='footprint' and ref(a[fp_uuid])=='R6','Text normalization must bind source R6')
            olditems={uid(n):n for n in a[fp_uuid] if isinstance(n,list) and children(n,'uuid')}
            newitems={uid(n):n for n in b[fp_uuid] if isinstance(n,list) and children(n,'uuid')}
            for text_uuid, angles in expected.items():
                require(text_uuid in olditems and text_uuid in newitems,'Expected text UUID missing')
                old=olditems[text_uuid];new=newitems[text_uuid]
                require(old[0] in ['property','fp_text'] and new[0]==old[0],'Only text angle normalization permitted')
                oa=child(old,'at');na=child(new,'at')
                require(len(oa)==len(na)==4 and Decimal(oa[3])==Decimal(str(angles[0])) and Decimal(na[3])==Decimal(str(angles[1])),'Unexpected text angle normalization')
                restored=copy.deepcopy(new);child(restored,'at')[3]=oa[3]
                require(equal(old,restored),'Text fields other than exact declared angle changed')
                text_ledger.append({'footprint_uuid':fp_uuid,'text_uuid':text_uuid,'source_angle':angles[0],'inverse_control_angle':angles[1],'all_other_text_fields_exact':True})
                # Comparison-only canonicalization, never written to either board.
                na[3]=oa[3]
    require(set(a)-set(b)==set(cuts),'Raw source removed UUID set differs')
    require(set(b)-set(a)=={r['uuid'] for r in adds},'Raw source added UUID set differs')
    # Header, stackup, netlist, settings and any UUID-less metadata must be exact.
    other=lambda root:[n for n in root if not(isinstance(n,list) and children(n,'uuid'))]
    require(unordered(other(before))==unordered(other(after)),'Board stackup/settings/netlist or metadata changed')
    ledger=[];fixed=0
    for key,old in a.items():
        if key in cuts:
            require(old[0] in ['segment','via','arc'],'Removal is not a whole route record');continue
        new=b[key]
        if old[0]=='zone':
            import island_guard
            new=island_guard.restore_raw_policy(old,new)
            strip=lambda n:[x for x in n if not(isinstance(x,list) and x[0] in ['filled_polygon','fill_segments'])]
            require(equal(strip(old),strip(new)),'Zone definition changed: '+key);continue
        if old[0]!='footprint' or ref(old) not in poses:
            # Direct footprint child ordering may change on SaveBoard, never child content.
            require(unordered(old)==unordered(new) if old[0]=='footprint' else equal(old,new),'Fixed raw object changed: '+key)
            fixed+=1;continue
        name=ref(old);target=poses[name];prior=pose(old)
        require(pose(new)==target,'Raw moved footprint pose differs: '+name)
        olditems={uid(n):n for n in old if isinstance(n,list) and children(n,'uuid')}
        newitems={uid(n):n for n in new if isinstance(n,list) and children(n,'uuid')}
        require(set(olditems)==set(newitems),'Moved footprint child UUID inventory changed')
        head=lambda n:[v for v in n if not(isinstance(v,list) and (v[0]=='at' or children(v,'uuid')))]
        require(unordered(head(old))==unordered(head(new)),'Footprint package/attributes changed')
        entries=[]
        for i,row in olditems.items():
            actual=newitems[i]
            if row[0] in ['pad','property','fp_text']:
                require(equal(shifted_angle(row,target[2]-prior[2]),normal_at(actual)),'Local pad/aperture/text settings changed: '+i)
            else:require(equal(row,actual),'Local footprint primitive changed: '+i)
            entries.append({'uuid':i,'kind':row[0],'all_local_settings_preserved':True})
        ledger.append({'reference':name,'uuid':key,'before_pose':prior,'after_pose':target,'children':entries})
    return {'raw_source_check':'PASSED','exact_text_angle_normalizations':text_ledger,'moved_footprints':ledger,'fixed_top_level_records':fixed,'all_pad_aperture_settings_and_local_shapes_preserved':True,'all_other_text_fields_preserved':True,'zone_fills_and_exact_two_island_removal_policy_fields_only':True,'board_stackup_netlist_settings_unchanged':True}
