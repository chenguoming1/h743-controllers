#!/usr/bin/env python3
"""Patch a copied F722 schematic/parts set. Never changes a PCB or published source.

Usage: python patch_recovered_metadata.py --hardware COPY/hardware --report REPORT.json [--apply]
Without --apply this only writes the proposed change report. Run before KiCad saves
or netlist export. The placement builder separately applies the documented U13 pad-net cycle.
"""
import argparse, copy, hashlib, json, re
from pathlib import Path

SOURCE = (Path(__file__).resolve().parents[2] / 'hardware').resolve()
SOURCE_HASHES = {
    'sensors.kicad_sch': None,
    'io-ports.kicad_sch': None,
    'parts.json': None,
}
TOKEN = re.compile(r'\(|\)|"(?:\\.|[^"\\])*"|[^\s()]+')
class Atom:
    def __init__(self,value,start,end): self.value,self.start,self.end=value,start,end
class Node:
    def __init__(self,start): self.items,self.start,self.end=[],start,None

def parse(text):
    stack=[]; root=None
    for m in TOKEN.finditer(text):
        t=m.group()
        if t=='(':
            node=Node(m.start())
            if stack: stack[-1].items.append(node)
            stack.append(node)
        elif t==')':
            node=stack.pop();node.end=m.end()
            if not stack: root=node
        else:
            stack[-1].items.append(Atom(json.loads(t) if t.startswith('"') else t,m.start(),m.end()))
    assert root and not stack
    return root

def children(node,key):
    return [c for c in node.items if isinstance(c,Node) and c.items and c.items[0].value==key]
def child(node,key):
    rows=children(node,key);assert len(rows)==1,(key,len(rows));return rows[0]
def val(node,index=1):return node.items[index].value
def shape(node):return [shape(x) if isinstance(x,Node) else x.value for x in node.items]
def props(node):return {val(p):val(p,2) for p in children(node,'property')}
def sha(data):return hashlib.sha256(data).hexdigest()
def replace(text,changes):
    for a,b,new in sorted(changes,reverse=True):text=text[:a]+new+text[b:]
    return text

def symbol_snapshot(tree,ref):
    result=[n for n in children(tree,'symbol') if props(n).get('Reference')==ref]
    assert len(result)==1,(ref,len(result));n=result[0]
    return n,dict(uuid=val(child(n,'uuid')),at=[x.value for x in child(n,'at').items[1:]],properties=props(n))

def patch_sensors(text):
    tree=parse(text);changes=[];before={};after={}
    expected={'Value':('4.7k / 1%','2.2k / 1%'),
              'MPN':('0402WGF4701TCE','0402WGF2201TCE'),
              'LCSC':('C25900','C25879'),
              'Supplier':('https://jlcpcb.com/partdetail/26643-0402WGF4701TCE/C25900','https://jlcpcb.com/partdetail/26622-0402WGF2201TCE/C25879')}
    uuids={'R7':'27bf5a19-5505-554a-a131-7cf399729b04','R8':'b7bb467b-6f3e-5565-a07c-41d67feae6d3'}
    for ref in ['R7','R8']:
        node,before[ref]=symbol_snapshot(tree,ref)
        assert before[ref]['uuid']==uuids[ref]
        assert before[ref]['properties']['Footprint']=='F722_Heli:R_0402_1005Metric'
        assert before[ref]['properties']['Manufacturer']=='UNI-ROYAL (Uniroyal Elec)'
        for p in children(node,'property'):
            name=val(p)
            if name in expected:
                old,new=expected[name];a=p.items[2];assert a.value==old,(ref,name,a.value)
                changes.append((a.start,a.end,json.dumps(new)));a.value=new
    newtext=replace(text,changes);newtree=parse(newtext)
    assert shape(tree)==shape(newtree),'Unexpected schematic change'
    for ref in ['R7','R8']:after[ref]=symbol_snapshot(newtree,ref)[1]
    return newtext,dict(before=before,after=after,changed_atoms=len(changes))

U13_LABELS=[
 ('b6dd0996-904d-5f2e-b75a-12068a7c090f',['170.18','142.24','180.0'],'1','ESC_MCU','SBUS_MCU'),
 ('81e9b770-d594-53f3-ab6f-d0a4ed872afa',['170.18','144.78','180.0'],'3','RPM_MCU','ESC_MCU'),
 ('de792af0-c48e-5c6d-b884-1808f6fcab4a',['170.18','149.86','180.0'],'6','SBUS_MCU','RPM_MCU'),
]

def patch_io(text):
    tree=parse(text);changes=[];result=[]
    _,snap=symbol_snapshot(tree,'U13');assert snap['uuid']=='eebbc0c0-c55e-5be5-ae0b-2b8a00b98eaf'
    assert snap['at']==['182.88','144.78','0']
    for uid,at,pin,old,new in U13_LABELS:
        matches=[n for n in children(tree,'global_label') if val(child(n,'uuid'))==uid]
        assert len(matches)==1;node=matches[0]
        assert [x.value for x in child(node,'at').items[1:]]==at
        a=node.items[1];assert a.value==old
        changes.append((a.start,a.end,json.dumps(new)));a.value=new
        result.append(dict(label_uuid=uid,at=at,U13_pin=pin,before=old,after=new))
    newtext=replace(text,changes)
    assert shape(tree)==shape(parse(newtext)),'Unexpected U13 or unrelated schematic change'
    return newtext,dict(symbol=snap,label_changes=result,changed_atoms=len(changes),unchanged_pads={'2':'GND','4':'unconnected-(U13-I{slash}O3-Pad4)','5':'+3V3_CORE'})

def patch_parts(text):
    data=json.loads(text);newdata=copy.deepcopy(data);facts={}
    for ref in ['R7','R8']:
        p=newdata[ref]
        assert p['mpn']=='0402WGF4701TCE' and p['jlcpcb_lcsc_code']=='C25900'
        assert p['proposed_footprint']=='F722_Heli:R_0402_1005Metric'
        p.update(mpn='0402WGF2201TCE',jlcpcb_lcsc_code='C25879',supplier_url='https://jlcpcb.com/partdetail/26622-0402WGF2201TCE/C25879')
        facts[ref]=dict(before=data[ref],after=p)
    assert {k:v for k,v in data.items()if k not in facts}=={k:v for k,v in newdata.items()if k not in facts}
    return json.dumps(newdata,indent=2)+'\n',facts

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--hardware',type=Path,required=True);ap.add_argument('--report',type=Path,required=True);ap.add_argument('--apply',action='store_true');args=ap.parse_args()
    target=args.hardware.resolve()
    assert target!=SOURCE and SOURCE not in target.parents,'Refuse to edit published hardware source'
    originals={};proposed={};facts={}
    for filename,fn in [('sensors.kicad_sch',patch_sensors),('io-ports.kicad_sch',patch_io),('parts.json',patch_parts)]:
        path=target/filename;assert path.is_file() and not path.is_symlink()
        assert path.resolve()!=SOURCE/filename
        originals[filename]=path.read_bytes();newtext,facts[filename]=fn(originals[filename].decode());proposed[filename]=newtext.encode()
    pcb=target/'f722-heli.kicad_pcb';pcb_before=sha(pcb.read_bytes()) if pcb.exists() else None
    report=dict(mode='applied' if args.apply else 'dry-run',hardware=target.name,files={n:dict(before_sha256=sha(originals[n]),after_sha256=sha(proposed[n]),facts=facts[n])for n in originals},native_PCB_untouched=pcb_before,native_edits_required=dict(values={'R7':'2.2k / 1%','R8':'2.2k / 1%'},U13_pad_nets={'1':'SBUS_MCU','3':'ESC_MCU','6':'RPM_MCU'}),verification_plan=['Export a fresh netlist from copied f722-heli.kicad_sch with KiCad 10; compare every ref/pin/net against published board except U13.1/.3/.6 above.','Confirm U13.2 GND, .4 NC, .5 +3V3_CORE and all U12/U14 assignments unchanged.','Run native ERC on copied f722-heli.kicad_sch; inspect unsuppressed diagnostics.','Verify PCB values, footprints, all 511 assigned pad identities, and 151 part metadata records after native edits.','Regenerate current BOM/CPL/export and evidence files from the checked new source; label old published results as historical.'],warning='Historical R7/R8 evidence_file strings are retained as provenance only. No earlier electrical/DRC result validates the new board.')
    if args.apply:
        for n in originals:assert (target/n).read_bytes()==originals[n],'Input changed during patch preparation'
        for n in proposed:(target/n).write_bytes(proposed[n])
        for n in proposed:assert (target/n).read_bytes()==proposed[n]
    if pcb.exists():assert sha(pcb.read_bytes())==pcb_before
    args.report.parent.mkdir(parents=True,exist_ok=True);args.report.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(mode=report['mode'],report=str(args.report),changed_schematic_atoms=sum(facts[n]['changed_atoms']for n in ['sensors.kicad_sch','io-ports.kicad_sch']),PCB_unchanged=pcb_before)))
if __name__=='__main__':main()
