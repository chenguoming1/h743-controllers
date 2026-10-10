"""Actual-board identity controls; no candidate or canonical mutation."""
import copy,json,hashlib,tempfile
from pathlib import Path
from verify_footprint_translations import check_nodes,verify,parse,children,child,properties,ROOT
old=ROOT/'ordinary-routing/candidate39/f722-heli.kicad_pcb';new=ROOT/'ordinary-routing/candidate40/f722-heli.kicad_pcb'
a=parse(old.read_text());b=parse(new.read_text())
changes={'R38':{'before':[28.775,24.5,0,'B.Cu'],'after':[17.69,23.59,0,'B.Cu']},'R70':{'before':[17.3,22.8,180,'B.Cu'],'after':[17.3,22.72,180,'B.Cu']}}
assert len(check_nodes(a,b,changes))==2
controls=[]
def rejected(name,fun):
 try:fun()
 except (AssertionError,KeyError):controls.append({'name':name,'rejected':True})
 else:raise RuntimeError('Mutation accepted: '+name)
def fp(root,ref):return next(f for f in children(root,'footprint') if properties(f)['Reference'].items[2].value==ref)
c=copy.deepcopy(changes);del c['R70'];rejected('undeclared_second_translation',lambda:check_nodes(a,b,c))
c=copy.deepcopy(changes);c['R38']['after'][0]+=.01;rejected('wrong_declared_position',lambda:check_nodes(a,b,c))
c=copy.deepcopy(changes);c['R38']['after'][3]='F.Cu';rejected('side_flip',lambda:check_nodes(a,b,c))
c=copy.deepcopy(changes);c['R70']['after'][2]=0;rejected('rotation',lambda:check_nodes(a,b,c))
for name,ref,kind in [('target_pad_net','R38','net'),('target_land_size','R38','size')]:
 m=copy.deepcopy(b);pad=children(fp(m,ref),'pad')[0];child(pad,kind).items[1].value='tampered';rejected(name,lambda m=m:check_nodes(a,m,changes))
m=copy.deepcopy(b);properties(fp(m,'R38'))['Value'].items[2].value='different';rejected('target_value',lambda:check_nodes(a,m,changes))
m=copy.deepcopy(b);child(fp(m,'R1'),'at').items[1].value='99';rejected('unlisted_footprint',lambda:check_nodes(a,m,changes))
with tempfile.TemporaryDirectory(prefix='f722-translation-') as td:
 p=Path(td)/'declaration.json';d={'schema':'f722-declared-footprint-translations/v1','source_board_sha256':hashlib.sha256(old.read_bytes()).hexdigest(),'board_sha256':hashlib.sha256(new.read_bytes()).hexdigest(),'changes':changes};p.write_text(json.dumps(d));receipt=verify(old,new,p);assert receipt['exact_unchanged_footprints']==154
 for key in ['source_board_sha256','board_sha256']:
  bad=copy.deepcopy(d);bad[key]='0'*64;p.write_text(json.dumps(bad));rejected(key,lambda:verify(old,new,p))
out={'passed':True,'positive_scope':'Source39 to isolated40 identity only; raw mechanical/DRC failure remains and40 is not adopted.','negative_controls':controls,'negative_control_count':len(controls),'script_sha256':hashlib.sha256((ROOT/'integrated-routing/verify_footprint_translations.py').read_bytes()).hexdigest()};(ROOT/'integrated-routing/footprint-translation-controls.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out))
