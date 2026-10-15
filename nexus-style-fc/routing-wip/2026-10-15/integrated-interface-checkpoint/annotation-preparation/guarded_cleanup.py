#!/usr/bin/env python3
"""Create an isolated successor using eight exact, guarded board-node edits.
No native process, refill, routing, CAM export or Git operation is performed.
The caller must supply the exact incoming board SHA; targets must match the
sealed mechanical baseline, even when unrelated mechanical copper advances.
"""
from __future__ import annotations
import argparse, copy, hashlib, json, pathlib, re, shutil, uuid

HERE = pathlib.Path(__file__).resolve().parent
BOARD = pathlib.Path('hardware/nexus-style-fc.kicad_pcb')
LIB = pathlib.Path('hardware/library/NexusFC.pretty')
TARGET_UIDS = {
 'J4':'a3b8b0d3-051e-475c-9730-f77b531b60d9',
 'J6':'29c15410-5881-4b58-b707-0290eb542fd8',
 'D1':'612706cc-e875-4ee1-bab0-981162669cc8',
 'D2':'ecba98b1-a774-4cdc-be3d-869421137ab6',
 'D3':'cd974035-242a-42c5-956b-70fa06889cf0',
}
ATTR_REFS = ['U3','L2','U14']
NEW_UIDS = {r:str(uuid.uuid5(uuid.NAMESPACE_URL,'nexus-assembly-annotation-20261015/'+r+'/outline-lower')) for r in ['J4','J6']}

class Node:
 def __init__(self,start): self.start=start; self.end=None; self.items=[]
 def value(self): return [x.value() if isinstance(x,Node) else x for x in self.items]
 @property
 def tag(self): return self.items[0]
 def children(self,tag): return [x for x in self.items if isinstance(x,Node) and x.tag==tag]
 def one(self,tag):
  rows=self.children(tag); assert len(rows)==1,(self.tag,tag,len(rows)); return rows[0]
 def val(self,tag): return self.one(tag).items[1]
 def prop(self,key):
  rows=[x.items[2] for x in self.children('property') if x.items[1]==key]; assert len(rows)==1,(self.tag,key);return rows[0]

def parse(text):
 stack=[];root=None
 for m in re.finditer(r'"(?:\\.|[^"\\])*"|[()]|[^\s()]+',text):
  t=m.group()
  if t=='(':
   n=Node(m.start())
   if stack:stack[-1].items.append(n)
   else:assert root is None;root=n
   stack.append(n)
  elif t==')':stack.pop().end=m.end()
  else:stack[-1].items.append(json.loads(t) if t.startswith('"') else t)
 assert root is not None and not stack
 return root

def sha_bytes(b):return hashlib.sha256(b).hexdigest()
def sha(p):return sha_bytes(p.read_bytes())
def csha(value):return sha_bytes(json.dumps(value,sort_keys=True,separators=(',',':')).encode())
def index(n):
 out={}
 def visit(n):
  us=n.children('uuid')
  if us:
   u=us[0].items[1];assert u not in out,('duplicate uuid',u);out[u]=n
  for x in n.items:
   if isinstance(x,Node):visit(x)
 visit(n);return out

def write_json(p,data):p.write_text(json.dumps(data,indent=2)+'\n')
def footprint_map(n):return {f.prop('Reference'):f for f in n.children('footprint')}
def raw(t,n):return t[n.start:n.end]
def replace_once(text,old,new):assert text.count(old)==1,(old,text.count(old));return text.replace(old,new)
def apply_replacements(text,edits):
 old_end=-1
 for s,e,new in sorted(edits):assert s>=old_end;old_end=e
 for s,e,new in sorted(edits,reverse=True):text=text[:s]+new+text[e:]
 return text

def normalized_protected(root):
 n=copy.deepcopy(root.value())
 def walk(n,ref=None):
  if n and n[0]=='footprint':ref=next(x[2] for x in n if isinstance(x,list) and x[0]=='property' and x[1]=='Reference')
  result=[]
  for x in n:
   if not isinstance(x,list):result.append(x);continue
   u=next((z[1] for z in x if isinstance(z,list) and z[0]=='uuid'),None)
   if u in set(TARGET_UIDS.values())|set(NEW_UIDS.values()):continue
   if ref in ATTR_REFS and x[0]=='attr':continue
   result.append(walk(x,ref))
  return result
 return walk(n)

def prepare(source,out,expected,marker_style):
 assert marker_style in ("move-only","filled-0.30")
 bind=json.loads((HERE/'input-bindings.json').read_text());source=source.resolve();out=out.resolve()
 assert not out.exists(),f'Output exists: {out}'
 assert source!=out and source not in out.parents,'Output must not be inside input'
 p=source/BOARD;assert sha(p)==expected,('incoming PCB SHA mismatch',sha(p),expected)
 before=p.read_text();assert before.encode()==p.read_bytes(),'Source PCB encoding/newlines would not round-trip byte-exact';board=parse(before);fps=footprint_map(board);idx=index(board)
 # Full semantic footprint guards include all pads, pin nets, identity, placement and graphics.
 for ref,row in bind['target_footprints'].items():
  assert csha(fps[ref].value())==row['canonical_sha256'],('target footprint changed',ref)
 for u,row in bind['texts'].items():assert idx[u].value()==row['node'],('meaningful text changed',u)
 for rel,expected_hash in bind['guarded_files'].items():assert sha(source/rel)==expected_hash,('authoritative source changed',rel)
 for r in ATTR_REFS:
  assert fps[r].one('attr').value()==['attr','through_hole']
  assert all(pad.items[2]=='smd' and not pad.children('drill') for pad in fps[r].children('pad'))
 # J1 is preserved with its incoming process metadata; neither J1 nor J6 is normalized.
 assert not fps['J1'].prop('LCSC') and len(fps['J1'].children('pad'))==11
 assert {t:sum(p.items[2]==t for p in fps['J6'].children('pad')) for t in ['smd','thru_hole','np_thru_hole']}=={'smd':16,'thru_hole':4,'np_thru_hole':2}
 edits=[];changes=[]
 def change(ref,node,new,label):
  old=raw(before,node);edits.append((node.start,node.end,new))
  changes.append({'ref':ref,'role':label,'before_raw':old,'after_raw':new,'before_node':node.value()})
 for ref in ATTR_REFS:change(ref,fps[ref].one('attr'),'(attr smd)','assembly attribute only')
 for ref in ['J4','J6']:
  n=idx[TARGET_UIDS[ref]];old=raw(before,n)
  assert n.tag=='fp_line' and n.val('layer')=='F.SilkS' and n.one('stroke').val('width')=='0.25'
  x,start,end,cut1,cut2=('-4.57','-1.78','3.43','0.475','2.325') if ref=='J4' else ('4.5','-1.6','1.6','-0.925','0.925')
  assert n.one('start').value()==['start',x,start] and n.one('end').value()==['end',x,end]
  upper=replace_once(old,raw(before,n.one('end')),f'(end {x} {cut1})')
  lower=replace_once(old,raw(before,n.one('start')),f'(start {x} {cut2})')
  lower=replace_once(lower,TARGET_UIDS[ref],NEW_UIDS[ref])
  change(ref,n,upper+'\n\t\t'+lower,'split existing outline around unchanged meaningful text')
 for ref in ['D1','D2','D3']:
  n=idx[TARGET_UIDS[ref]];old=raw(before,n)
  assert n.one('center').value()==['center','-0.8','0.4'] and n.one('end').value()==['end','-0.77','0.4']
  if marker_style=='move-only':
   new=replace_once(old,raw(before,n.one('center')),'(center -0.8 1.05)')
   new=replace_once(new,raw(before,n.one('end')),'(end -0.77 1.05)')
   role='move original cathode circle 0.650 mm south; same UUID/radius/stroke'
  else:
   new=replace_once(old,raw(before,n.one('center')),'(center -0.8 1.15)')
   new=replace_once(new,raw(before,n.one('end')),'(end -0.725 1.15)')
   new=replace_once(new,raw(before,n.one('stroke').one('width')),'(width 0.15)')
   new=replace_once(new,raw(before,n.one('fill')),'(fill solid)')
   role='move original cathode circle 0.750 mm south; retain UUID; filled 0.300 mm outer ink diameter and 0.150 mm stroke'
  change(ref,n,new,role)
 after=apply_replacements(before,edits);ab=parse(after);afps=footprint_map(ab);ai=index(ab)
 assert normalized_protected(board)==normalized_protected(ab),'Unexpected board change outside allowlist'
 assert set(ai)-set(idx)==set(NEW_UIDS.values()) and not set(idx)-set(ai)
 assert raw(before,fps['J1'])==raw(after,afps['J1'])
 for ref in set(fps)-set(ATTR_REFS)-set(TARGET_UIDS):assert raw(before,fps[ref])==raw(after,afps[ref])
 # All component identity/placement/pads are byte-exact, including edited instances.
 for ref in fps:
  for kind in ['property','at','layer','pad','path','model']:
   assert [raw(before,n) for n in fps[ref].children(kind)]==[raw(after,n) for n in afps[ref].children(kind)],(ref,kind)
 # Copy only source directories. Earlier validation, seals, CAM and evidence are not successor claims.
 out.mkdir(parents=True)
 for directory in ['hardware','tools']:shutil.copytree(source/directory,out/directory,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
 (out/BOARD).write_text(after)
 library_changes=[]
 for ref in ATTR_REFS:
  rel=LIB/(fps[ref].items[1].split(':')[1]+'.kicad_mod');old=(source/rel).read_text();root=parse(old)
  assert root.one('attr').value()==['attr','through_hole']
  new=replace_once(old,raw(old,root.one('attr')),'(attr smd)')
  old_protected=[x.value() if isinstance(x,Node) else x for x in root.items if not isinstance(x,Node) or x.tag!='attr']
  nr=parse(new);new_protected=[x.value() if isinstance(x,Node) else x for x in nr.items if not isinstance(x,Node) or x.tag!='attr'];assert old_protected==new_protected
  (out/rel).write_text(new);library_changes.append({'ref':ref,'path':str(rel),'before_sha256':sha(source/rel),'after_sha256':sha(out/rel),'before_node':['attr','through_hole'],'after_node':['attr','smd'],'all_other_bytes_unchanged':True})
 old=(source/'tools/pcbutil.py').read_text()
 new=replace_once(old,'import pcbnew\n','import pcbnew\nfrom assembly_annotations import apply_main_assembly_annotations\n')
 new=replace_once(new,'        clear_main_u10_donor_metadata(fp, part, project)\n','        clear_main_u10_donor_metadata(fp, part, project)\n        apply_main_assembly_annotations(fp, part, project)\n')
 (out/'tools/pcbutil.py').write_text(new);helper=(HERE/'assembly_annotations.py').read_text()
 if marker_style=='filled-0.30':helper=replace_once(helper,'MARKER_STYLE = "move-only"','MARKER_STYLE = "filled-0.30"')
 (out/'tools/assembly_annotations.py').write_text(helper)
 changed={str(BOARD),str(pathlib.Path('tools/pcbutil.py'))}|{r['path'] for r in library_changes}
 copied=[]
 for directory in ['hardware','tools']:
  for src in sorted((source/directory).rglob('*')):
   if not src.is_file() or '__pycache__' in src.parts or src.suffix=='.pyc':continue
   rel=src.relative_to(source);dst=out/rel
   if str(rel) not in changed:assert sha(src)==sha(dst),('unexpected source-file mutation',str(rel))
   copied.append({'path':str(rel),'source_sha256':sha(src),'candidate_sha256':sha(dst),'changed':str(rel) in changed})
 for row in changes:
  row['after_nodes']=[ai[u].value() for u in [TARGET_UIDS[row['ref']],NEW_UIDS[row['ref']]] if u in ai] if row['ref'] in NEW_UIDS else ([afps[row['ref']].one('attr').value()] if row['ref'] in ATTR_REFS else [ai[TARGET_UIDS[row['ref']]].value()])
 assert sha(p)==expected,'Source board changed during transaction'
 for rel,h in bind['guarded_files'].items():assert sha(source/rel)==h,('Guarded source changed during transaction',rel)
 result={'marker_style':marker_style,'status':'SOURCE-ONLY PREPARED; native, actual BOM/CPL and visual checks pending','source_project':str(source),'source_board_sha256':sha(p),'candidate_board_sha256':sha(out/BOARD),'baseline_target_binding_sha256':sha(HERE/'input-bindings.json'),'board_changes':changes,'library_changes':library_changes,'new_graphic_uuids':NEW_UIDS,'protected_board_canonical_sha256':csha(normalized_protected(board)),'all_nonallowed_source_nodes_byte_exact':True,'all_part_identity_pin_net_pad_placement_model_nodes_byte_exact':True,'J1_byte_exact_manual_joint':True,'J6_mixed_technology_unchanged':{'smd_contacts':16,'pth_shell_lugs':4,'npth_locator_holes':2},'copied_source_files':copied,'generator_helper_sha256':sha(out/'tools/assembly_annotations.py'),'generator_pcbutil_sha256':sha(out/'tools/pcbutil.py')}
 write_json(out/'annotation-transaction.json',result)
 return result

if __name__=='__main__':
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--source-project',required=True,type=pathlib.Path);ap.add_argument('--output-project',required=True,type=pathlib.Path);ap.add_argument('--expected-board-sha256',required=True);ap.add_argument('--marker-style',required=True,choices=['move-only','filled-0.30']);args=ap.parse_args();r=prepare(args.source_project,args.output_project,args.expected_board_sha256,args.marker_style);print(json.dumps({k:r[k] for k in ['status','source_board_sha256','candidate_board_sha256','new_graphic_uuids']},indent=2))
