"""Apply only the authorized U10.3 net field and exact ten terminal-track removals.

Pure text patch; source bytes never modified. Native topology, refill, ERC and DRC
remain required. The expected input SHA must be supplied explicitly.
"""
from pathlib import Path
import argparse, hashlib, json, re, difflib

def sha(data): return hashlib.sha256(data).hexdigest()
def children(text, start=0, end=None):
    end=len(text) if end is None else end
    depth=0; quoted=False; escape=False; opening=None
    for i in range(start,end):
        c=text[i]
        if quoted:
            if escape: escape=False
            elif c=='\\': escape=True
            elif c=='"': quoted=False
            continue
        if c=='"': quoted=True
        elif c=='(':
            if depth==1: opening=i
            depth+=1
        elif c==')':
            depth-=1
            if depth==1 and opening is not None:
                yield opening,i+1
                opening=None
    assert depth==0 and not quoted

def field(block,name):
    result=re.findall(r'\('+re.escape(name)+r'\s+([^()]*)\)',block)
    assert len(result)==1,(name,len(result))
    return result[0].strip()

def apply(source,target,expected,ledger):
    raw=source.read_bytes(); assert sha(raw)==expected, 'Source hash mismatch'
    text=raw.decode(); ids=set(ledger['authorized_en_delta']['removed_terminal_track_uuids'])
    pid=ledger['authorized_en_delta']['pad_uuid']; nc=ledger['authorized_en_delta']['new_net']
    patches=[]; removed=[]; changed_pad=[]
    for i,j in children(text):
        block=text[i:j]
        tag=re.match(r'\(([^\s()]+)',block).group(1)
        if tag=='segment':
            u=field(block,'uuid').strip('"')
            if u in ids:
                assert field(block,'net')=='"VSYS"'
                assert field(block,'layer')=='"F.Cu"'
                removed.append({'uuid':u,'start':list(map(float,field(block,'start').split())), 'end':list(map(float,field(block,'end').split())), 'width_mm':float(field(block,'width')), 'layer':'F.Cu','net':'VSYS','source_text':block})
                # Remove the block and its indentation/newline only.
                a=i
                while a>0 and text[a-1] in ' \t':a-=1
                z=j+1 if text[j:j+1]=='\n' else j
                patches.append((a,z,''))
        elif tag=='footprint':
            for a,b in children(block):
                pad=block[a:b]
                if not re.match(r'\(pad\s',pad):continue
                if field(pad,'uuid').strip('"')!=pid:continue
                assert re.match(r'\(pad\s+"3"\s',pad)
                matches=list(re.finditer(r'\(net\s+"VSYS"\)',pad));assert len(matches)==1
                m=matches[0]; patches.append((i+a+m.start(),i+a+m.end(),'(net "'+nc+'")'))
                changed_pad.append(pid)
    assert {r['uuid'] for r in removed}==ids and len(removed)==10
    assert changed_pad==[pid]
    out=text
    for i,j,replacement in sorted(patches,reverse=True):out=out[:i]+replacement+out[j:]
    target.parent.mkdir(parents=True,exist_ok=True)
    with target.open('xb') as f:f.write(out.encode())
    assert source.read_bytes()==raw
    receipt={'status':'minimal EN-only text patch; native validation pending','source':str(source),'source_sha256':expected,'candidate':str(target),'candidate_sha256':sha(target.read_bytes()),'approved_pin_delta':{k:ledger['authorized_en_delta'][k] for k in ['reference','pin','pad_uuid','old_net','new_net']},'removed_terminal_tracks':removed,'minimal_patch_count':len(patches),'qualification':'Not a native-verified board. No electrical or fabrication completion claimed.'}
    target.with_suffix('.en-transaction.json').write_text(json.dumps(receipt,indent=2)+'\n')
    target.with_suffix('.en-minimal.patch').write_text(''.join(difflib.unified_diff(text.splitlines(True),out.splitlines(True),fromfile='rollback/'+source.name,tofile='en-only/'+target.name)))
    print(json.dumps({k:receipt[k] for k in ['status','source_sha256','candidate_sha256','minimal_patch_count']},indent=2))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('source',type=Path);p.add_argument('target',type=Path);p.add_argument('expected_sha256');p.add_argument('--ledger',type=Path,default=Path(__file__).with_name('repair-lane-recovery.json'));a=p.parse_args()
    apply(a.source,a.target,a.expected_sha256,json.loads(a.ledger.read_text()))
