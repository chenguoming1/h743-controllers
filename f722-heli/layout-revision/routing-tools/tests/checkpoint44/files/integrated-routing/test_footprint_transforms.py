"""Source-bound pose-operation controls; never mutate native source files."""
from pathlib import Path
import copy,json,tempfile,hashlib
from verify_footprint_transforms import ROOT,verify,check_shapes,parse,children,properties
from apply_metadata_copy import child
old=ROOT/'ordinary-routing/candidate41/f722-heli.kicad_pcb';new=ROOT/'ordinary-routing/candidate42/f722-heli.kicad_pcb';declaration=ROOT/'integrated-routing/declared-transforms41-to42.json';plan=json.loads(declaration.read_text());assert verify(old,new,declaration)['exact_unchanged_footprints']==153
controls=[]
def rejected(name,fn):
 try:fn()
 except (AssertionError,KeyError):controls.append({'name':name,'rejected':True})
 else:raise RuntimeError('Accepted defect: '+name)
with tempfile.TemporaryDirectory(prefix='f722-transform-control-') as td:
 path=Path(td)/'plan.json'
 for name in ['wrong_source','wrong_output','missing_flip_axis','wrong_position','nonorthogonal_angle','undeclared_C69']:
  d=copy.deepcopy(plan)
  if name=='wrong_source':d['source_board_sha256']='0'*64
  elif name=='wrong_output':d['board_sha256']='0'*64
  elif name=='missing_flip_axis':d['changes']['R7']['flip_left_right']=None
  elif name=='wrong_position':d['changes']['R8']['after'][0]+=.1
  elif name=='nonorthogonal_angle':d['changes']['R7']['after'][2]=45
  else:del d['changes']['C69']
  path.write_text(json.dumps(d));rejected(name,lambda:verify(old,new,path))
a=parse(old.read_text());b=parse(new.read_text())
def fp(root,ref):return next(f for f in children(root,'footprint') if properties(f)['Reference'].items[2].value==ref)
for name in ['changed_pad_net','changed_land','changed_part_value','unlisted_pose']:
 x=copy.deepcopy(b)
 if name=='changed_pad_net':child(children(fp(x,'R7'),'pad')[0],'net').items[1].value='wrong'
 elif name=='changed_land':child(children(fp(x,'R7'),'pad')[0],'size').items[1].value='99'
 elif name=='changed_part_value':properties(fp(x,'R7'))['Value'].items[2].value='wrong'
 else:child(fp(x,'R1'),'at').items[1].value='99'
 rejected(name,lambda x=x:check_shapes(a,x,b,plan['changes']))
out={'passed':True,'controls':controls,'source_board_sha256':plan['source_board_sha256'],'candidate_board_sha256':plan['board_sha256'],'scope':'Identity-only transform proof; candidate42 is not adopted by this test. No DRC or electrical acceptance.','script_sha256':hashlib.sha256((ROOT/'integrated-routing/verify_footprint_transforms.py').read_bytes()).hexdigest()};(ROOT/'integrated-routing/footprint-transform-controls.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out))
